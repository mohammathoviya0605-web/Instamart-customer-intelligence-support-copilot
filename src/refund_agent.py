
"""Part D: database-backed refund tools and resumable ReAct agent."""

from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import time
import uuid

import mock_llm
from src.policy_rag import PolicyRAG


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "instamart.db"
OUT = ROOT / "outputs"
STATE = ROOT / "state"

rag = PolicyRAG()


def get_order(order_id, request_date=None):
    """Look up an order and optionally validate the seven-day request window."""
    with sqlite3.connect(DB) as con:
        row = con.execute(
            """
            SELECT order_id, status, order_amount,
                   delivery_minutes, order_ts
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

    if not row:
        return {"error": "order not found"}

    order = dict(zip(
        ["order_id", "status", "order_amount",
         "delivery_minutes", "order_ts"],
        row
    ))

    if request_date is not None and order["delivery_minutes"] is not None:
        order_time = datetime.fromisoformat(order["order_ts"])
        delivered_at = order_time + timedelta(
            minutes=float(order["delivery_minutes"])
        )
        requested_at = datetime.fromisoformat(request_date)

        days_after_delivery = (
            requested_at - delivered_at
        ).total_seconds() / 86400

        if days_after_delivery < 0 or days_after_delivery > 7:
            return {"error": "request outside the seven-day refund window"}

    return order


def search_policy(query):
    return {"results": rag.retrieve(query, 3)}


def calculate_refund(order_amount, delivery_minutes):
    """Calculate a full refund only when delivery took more than 45 minutes."""
    if delivery_minutes is None:
        return {"refund_inr": 0.0}

    amount = (
        float(order_amount)
        if float(delivery_minutes) > 45
        else 0.0
    )
    return {"refund_inr": round(amount, 2)}


def _ledger(tool, order_id, refund_inr):
    OUT.mkdir(exist_ok=True)
    path = OUT / "refund_ledger.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "order_id": order_id,
        "refund_inr": refund_inr
    }

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    return {"refund_inr": refund_inr}


def issue_refund(order_id, refund_inr):
    return _ledger("issue_refund", order_id, refund_inr)


def escalate_to_human(order_id, refund_inr):
    return _ledger("escalate_to_human", order_id, refund_inr)


TOOL_MAP = {
    "get_order": get_order,
    "search_policy": search_policy,
    "calculate_refund": calculate_refund,
    "issue_refund": issue_refund,
    "escalate_to_human": escalate_to_human
}


TOOLS_SPEC = [
    {
        "name": name,
        "description": f"Execute the {name} refund workflow operation.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
    for name in TOOL_MAP
]


def _save_checkpoint(run_id, scenario_id, messages, tokens,
                     steps, executed, llm_calls, request_date):
    STATE.mkdir(exist_ok=True)

    checkpoint = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "messages": messages,
        "tokens_used": tokens,
        "steps": steps,
        "tools_executed": executed,
        "llm_calls": llm_calls,
        "request_date": request_date
    }

    path = STATE / f"{run_id}.json"
    path.write_text(
        json.dumps(checkpoint, default=str),
        encoding="utf-8"
    )


def _continue_agent(run_id, scenario_id, messages, tokens,
                    steps, executed, llm_calls, max_iterations,
                    token_limit, time_limit_seconds, request_date,
                    crash_after=None):
    start = time.monotonic()

    tool_map = dict(TOOL_MAP)

    if request_date is not None:
        tool_map["get_order"] = (
            lambda order_id: get_order(order_id, request_date)
        )

    for iteration in range(max_iterations):
        if time.monotonic() - start >= time_limit_seconds:
            return {
                "status": "FALLBACK_TIMEOUT",
                "final_answer": "FALLBACK_TIMEOUT: hand off to a human agent.",
                "steps": steps,
                "llm_calls": llm_calls,
                "tokens_used": tokens,
                "run_id": run_id
            }

        response = mock_llm.chat(messages)
        llm_calls += 1
        tokens += response.usage.total_tokens

        if tokens > token_limit:
            return {
                "status": "FALLBACK_TOKEN_LIMIT",
                "final_answer": "FALLBACK_TOKEN_LIMIT: hand off to a human agent.",
                "steps": steps,
                "llm_calls": llm_calls,
                "tokens_used": tokens,
                "run_id": run_id
            }

        msg = response.choices[0].message

        if not msg.tool_calls:
            content = msg.content or ""
            return {
                "status": content.split(":", 1)[0],
                "final_answer": content,
                "steps": steps,
                "llm_calls": llm_calls,
                "tokens_used": tokens,
                "run_id": run_id
            }

        tc = msg.tool_calls[0]
        args = tc.arguments

        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": tc.id,
                "name": tc.name,
                "arguments": args
            }]
        })

        observation = tool_map[tc.name](**args)
        executed.append(tc.name)

        steps.append({
            "tool": tc.name,
            "arguments": args,
            "observation": observation
        })

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": tc.name,
            "content": json.dumps(observation)
        })

        _save_checkpoint(
            run_id, scenario_id, messages, tokens,
            steps, executed, llm_calls, request_date
        )

        if crash_after is not None and len(executed) == crash_after:
            raise RuntimeError("Simulated crash after checkpoint")

    return {
        "status": "FALLBACK_MAX_ITERATIONS",
        "final_answer": "FALLBACK_MAX_ITERATIONS: hand off to a human agent.",
        "steps": steps,
        "llm_calls": llm_calls,
        "tokens_used": tokens,
        "run_id": run_id
    }


def run_agent(user_message, scenario_id="demo", max_iterations=6,
              token_limit=6000, time_limit_seconds=10,
              run_id=None, crash_after=None, request_date=None):
    """Start a new agent run."""
    run_id = run_id or str(uuid.uuid4())
    STATE.mkdir(exist_ok=True)

    messages = [
        {
            "role": "system",
            "content": "AGENT: Use tools to verify orders and follow refund policy."
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    return _continue_agent(
        run_id, scenario_id, messages,
        tokens=0,
        steps=[],
        executed=[],
        llm_calls=0,
        max_iterations=max_iterations,
        token_limit=token_limit,
        time_limit_seconds=time_limit_seconds,
        request_date=request_date,
        crash_after=crash_after
    )


def resume_agent(run_id, max_iterations=6, token_limit=6000,
                 time_limit_seconds=10):
    """Resume an agent run from its latest saved checkpoint."""
    path = STATE / f"{run_id}.json"

    if not path.exists():
        raise FileNotFoundError(f"No checkpoint found for run: {run_id}")

    checkpoint = json.loads(path.read_text(encoding="utf-8"))

    return _continue_agent(
        run_id,
        checkpoint["scenario_id"],
        checkpoint["messages"],
        tokens=checkpoint["tokens_used"],
        steps=checkpoint["steps"],
        executed=checkpoint["tools_executed"],
        llm_calls=checkpoint["llm_calls"],
        max_iterations=max_iterations,
        token_limit=token_limit,
        time_limit_seconds=time_limit_seconds,
        request_date=checkpoint.get("request_date")
    )

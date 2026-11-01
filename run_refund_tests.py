

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from src.refund_agent import run_agent

OUT = Path("outputs")
DB = Path("data/instamart.db")
OUT.mkdir(exist_ok=True)

runs_file = OUT / "agent_runs.jsonl"
ledger_file = OUT / "refund_ledger.jsonl"

# Start with clean reports
runs_file.write_text("", encoding="utf-8")
ledger_file.write_text("", encoding="utf-8")


def get_test_request_date(order_id):
    """Create a controlled test date one day after estimated delivery."""
    if order_id is None:
        return None

    with sqlite3.connect(DB) as con:
        row = con.execute(
            """
            SELECT order_ts, delivery_minutes
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

    if row is None or row[1] is None:
        return None

    order_time = datetime.fromisoformat(row[0])
    delivered_at = order_time + timedelta(minutes=float(row[1]))
    request_date = delivered_at + timedelta(days=1)

    return request_date.isoformat()


scenarios = [
    ("S1", "Refund order ORD-100048", "ORD-100048"),
    ("S2", "Refund order ORD-100067", "ORD-100067"),
    ("S3", "Refund order ORD-100145", "ORD-100145"),
    ("S4", "Refund order ORD-100020", "ORD-100020"),
    ("S5", "Refund order ORD-100001", "ORD-100001"),
    ("S6", "Refund order ORD-999999", "ORD-999999"),
    ("S7", "Refund order [LOOP]", None),
]

for scenario_id, message, order_id in scenarios:
    request_date = get_test_request_date(order_id)

    result = run_agent(
        message,
        scenario_id=scenario_id,
        request_date=request_date
    )

    record = {
        "scenario_id": scenario_id,
        "request_date": request_date,
        **result
    }

    with runs_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    print("\nScenario:", scenario_id)
    print("Request date:", request_date)
    print("Actual status:", result["status"])
    print("Final answer:", result["final_answer"])


print("\n--- Safety demonstrations ---")

test_date = get_test_request_date("ORD-100048")

token_result = run_agent(
    "Refund order ORD-100048",
    scenario_id="token-demo",
    token_limit=200,
    request_date=test_date
)
print("Token limit:", token_result["status"])

timeout_result = run_agent(
    "Refund order ORD-100048",
    scenario_id="timeout-demo",
    time_limit_seconds=0,
    request_date=test_date
)
print("Timeout:", timeout_result["status"])

print("\nTest report saved:", runs_file)
print("Refund ledger saved:", ledger_file)

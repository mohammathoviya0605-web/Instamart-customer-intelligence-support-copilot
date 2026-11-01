
from src.refund_agent import run_agent, resume_agent

run_id = "resume-test-001"

print("Starting agent and simulating a crash...")

try:
    run_agent(
        "Refund order ORD-100048",
        scenario_id="RESUME_TEST",
        run_id=run_id,
        crash_after=2,
        request_date="2025-04-03T23:44:44"
    )
except RuntimeError as error:
    print("Simulated crash:", error)

print("\nResuming from checkpoint...")

result = resume_agent(run_id)

print("\nFinal status:", result["status"])
print("Final answer:", result["final_answer"])
print("Tools executed:", result["steps"])
print("LLM calls:", result["llm_calls"])
print("Tokens used:", result["tokens_used"])

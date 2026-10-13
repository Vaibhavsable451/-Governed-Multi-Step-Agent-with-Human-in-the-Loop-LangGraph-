import sys, uuid
from langgraph.types import Command
from src.agent import build_graph

q = " ".join(sys.argv[1:]) or "How many days of parental leave do I get?"
graph = build_graph()
cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
state = graph.invoke({"question": q, "documents": [], "draft": "", "risk": "", "flags": [],
                      "feedback": "", "status": ""}, cfg)

while "__interrupt__" in state:
    payload = state["__interrupt__"][0].value
    print("\n=== HUMAN REVIEW REQUIRED ===")
    print("Risk flags:", payload["flags"]); print("Draft:\n", payload["draft"])
    decision = input("\n[approve / or type feedback] > ")
    state = graph.invoke(Command(resume=decision), cfg)

print("\nFINAL STATUS:", state["status"]); print("FINAL REPLY:\n", state["draft"])
print("\nAudit trail written to outputs/audit.jsonl")

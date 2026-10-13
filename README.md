# 10 - Governed Multi-Step Agent with Human-in-the-Loop (LangGraph)

An HR-assistant agent that drafts replies from the handbook, but **cannot send anything risky without human approval**.

```
retrieve -> draft -> policy_check --(low risk)--> send
                          |
                      (high risk) -> human_approval [interrupt] --approve--> send
                                                                 --reject---> revise -> policy_check
```
- **Checkpointer** (`MemorySaver`) persists state so the run can pause for days and resume.
- **interrupt()** pauses execution and surfaces the draft + risk reasons to a reviewer.
- **Risk policy** flags legal/financial commitments, money amounts and personal data.
- Every decision is appended to `outputs/audit.jsonl` for accountability.

```bash
pip install -r requirements.txt && cp .env.example .env
python -m src.run "Can you confirm I will get a 10,000 USD relocation bonus?"
```
Replace the console reviewer in `run.py` with Slack/email/web UI in production.

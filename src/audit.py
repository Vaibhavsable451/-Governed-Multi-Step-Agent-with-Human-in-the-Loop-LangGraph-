import json, os, time

def log(event: str, **data):
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "event": event, **data}) + "\n")

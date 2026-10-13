import re

RISK_RULES = {
    "financial_commitment": re.compile(r"\b(guarantee|promise|confirm|will receive|entitled to)\b", re.I),
    "money_amount": re.compile(r"\b\d[\d,]*(\.\d+)?\s?(usd|dollars|\$|eur)\b|\$\s?\d", re.I),
    "legal": re.compile(r"\b(lawsuit|terminate|termination|contract|visa|harass)\w*", re.I),
    "personal_data": re.compile(r"\b\d{3}-\d{2}-\d{4}\b|[\w.+-]+@[\w-]+\.[\w.]+"),
}

def assess(text: str):
    flags = [name for name, pat in RISK_RULES.items() if pat.search(text)]
    return {"risk": "high" if flags else "low", "flags": flags}

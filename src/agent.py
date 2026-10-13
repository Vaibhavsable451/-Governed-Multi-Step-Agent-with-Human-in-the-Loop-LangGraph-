from pathlib import Path
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from src.config import get_llm, get_embeddings
from src.risk import assess
from src.audit import log

class State(TypedDict):
    question: str
    documents: List[Document]
    draft: str
    risk: str
    flags: List[str]
    feedback: str
    status: str

_llm = None
_retriever = None

def _init():
    global _llm, _retriever
    if _llm is None:
        _llm = get_llm()
        docs = []
        for f in Path("data").glob("*.txt"):
            docs += TextLoader(str(f), encoding="utf-8").load()
        chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(docs)
        _retriever = FAISS.from_documents(chunks, get_embeddings()).as_retriever(search_kwargs={"k": 3})

def retrieve(s: State):
    _init()
    return {"documents": _retriever.invoke(s["question"])}

def draft(s: State):
    ctx = "\n\n".join(d.page_content for d in s["documents"])
    fb = f"\nReviewer feedback to address: {s['feedback']}" if s.get("feedback") else ""
    p = ChatPromptTemplate.from_template(
        "You draft replies to employees. Use ONLY the context. Never promise anything not in the policy; "
        "say you will escalate to HR if unsure.{fb}\n\nContext:\n{ctx}\n\nEmployee: {q}")
    text = (p | _llm | StrOutputParser()).invoke({"ctx": ctx, "q": s["question"], "fb": fb})
    log("draft_created", question=s["question"], draft=text)
    return {"draft": text}

def policy_check(s: State):
    r = assess(s["question"] + "\n" + s["draft"])
    log("policy_check", **r)
    return {"risk": r["risk"], "flags": r["flags"]}

def human_approval(s: State):
    decision = interrupt({"draft": s["draft"], "flags": s["flags"],
                          "instruction": "Reply 'approve' or provide feedback text to reject."})
    approved = str(decision).strip().lower() == "approve"
    log("human_decision", approved=approved, decision=str(decision))
    return {"status": "approved" if approved else "rejected", "feedback": "" if approved else str(decision)}

def send(s: State):
    log("sent", draft=s["draft"], approver="human" if s.get("status") == "approved" else "auto")
    return {"status": "sent"}

def route_risk(s: State):
    return "human_approval" if s["risk"] == "high" else "send"

def route_decision(s: State):
    return "send" if s["status"] == "approved" else "draft"

def build_graph():
    g = StateGraph(State)
    for n, f in [("retrieve", retrieve), ("draft", draft), ("policy_check", policy_check),
                 ("human_approval", human_approval), ("send", send)]:
        g.add_node(n, f)
    g.add_edge(START, "retrieve"); g.add_edge("retrieve", "draft"); g.add_edge("draft", "policy_check")
    g.add_conditional_edges("policy_check", route_risk, {"human_approval": "human_approval", "send": "send"})
    g.add_conditional_edges("human_approval", route_decision, {"send": "send", "draft": "draft"})
    g.add_edge("send", END)
    return g.compile(checkpointer=MemorySaver())

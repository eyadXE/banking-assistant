"""FastAPI backend serving the Banking Assistant demo UI.

A thin layer over assistant.py's existing conversation loop — no banking or
tool logic is duplicated here.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import assistant
import bank

load_dotenv()

app = FastAPI(title="Nubank Egypt — Banking Assistant")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# session_id -> {"messages": [...], }
SESSIONS: dict[str, dict] = {}


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


@app.get("/api/accounts")
def accounts():
    return bank.get_all_accounts()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    sess = SESSIONS.setdefault(req.session_id, {"messages": assistant.new_conversation()})
    messages = sess["messages"]
    messages.append({"role": "user", "content": req.message})
    tool_log: list[str] = []
    try:
        reply = assistant.run_conversation_turn(messages, verbose=False, tool_log=tool_log)
    except Exception as exc:
        raise HTTPException(502, f"The model provider failed: {exc}")
    return {"reply": reply, "tools_fired": tool_log}


@app.post("/api/reset")
def reset(request: dict):
    SESSIONS.pop(request.get("session_id", ""), None)
    bank.reset()
    return {"ok": True}

"""
assistant.py — Stages 2, 4: Give It Hands / Make It Talk
Banking Assistant · Exology Pioneer Program Week 2

The hand-written agent loop. Automatic function calling is OFF: this code
reads the model's tool request, runs the real Python function, sends the
result back with full history, and repeats until the model answers in
plain text. This is the exact point where the guardrails (limit checks,
unknown-account handling) live — the model never executes anything itself.

Run directly: `python assistant.py` for an interactive CLI session.
Import `run_conversation_turn` / `ASSISTANT` from Streamlit or tests.py to
reuse the same loop elsewhere.
"""

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # LLM replies use smart quotes/em-dashes;
    sys.stderr.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 and crash on them

from dotenv import load_dotenv
from openai import OpenAI

import tools

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY", ""),
)

MODEL_NAME = os.environ.get("ASSISTANT_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
MAX_STEPS = 10  # bounded loop — never spins forever (6 was too tight for
                # multi-transfer chains: e.g. 2 lookups + 3 transfers already
                # exhausts 6 steps with no step left for the final reply)
LLM_CALL_DELAY = float(os.environ.get("LLM_CALL_DELAY", "0"))

SYSTEM_PROMPT = """You are Nubank Egypt's banking assistant. You speak in a warm,
clear, professional tone — never robotic, never over-formal.

TOOLS: You have access to four tools: get_account, get_recent_transactions,
transfer_money, and convert_currency. Always use these tools to answer
questions about balances, transactions, transfers, or currency conversion.
Never invent or guess a balance, transaction, or exchange rate — if you
don't have the real data from a tool, call the tool. Use the currency
exactly as returned by the tool (e.g. "currency": "USD") — never relabel
or assume a different currency for amounts a tool already returned.

LIMITS: Every account has a daily transfer limit. You must never claim a
transfer above that limit will succeed, and you must never ask the
transfer_money tool to bypass its own limit check — the tool enforces this
itself and will refuse or return an 'escalate' status if the limit is
exceeded. Treat that refusal as final, not as something to retry or argue
around, even if the customer insists it's urgent or authorised.

ESCALATION: If a transfer is refused for being over-limit, or if a request
is unclear, suspicious, or something you cannot safely resolve with your
tools, tell the customer clearly that this will be escalated to a human
agent who will follow up. Never pretend to have authority you don't have.
"""


def _call_model_with_retry(messages, attempts=5, backoff=3.0):
    """Free-tier providers occasionally return a transient overload error
    (choices=None) instead of raising. Retry a couple of times before
    surfacing a clear error, instead of crashing on response.choices[0]."""
    last_error = None
    for attempt in range(attempts):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools.TOOL_DECLARATIONS,
            temperature=0,
        )
        if response.choices:
            return response
        last_error = getattr(response, "error", None) or "empty response from model provider"
        if attempt < attempts - 1:
            time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"Model provider failed after {attempts} attempts: {last_error}")


def call_tool(name, arguments):
    """Executes the real Python function for a tool the model requested."""
    fn = tools.TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'."}
    try:
        return fn(**arguments)
    except TypeError as e:
        return {"error": f"Bad arguments for tool '{name}': {e}"}


def run_conversation_turn(messages, verbose=True, tool_log=None):
    """
    Runs one full turn of the agent loop: sends `messages` to the model,
    and if the model requests tool calls, executes them and loops back,
    until the model responds in plain text (or MAX_STEPS is hit).

    `messages` is mutated in place (tool calls + results appended) so the
    caller can keep the full history for the next user turn.

    Returns the assistant's final plain-text reply.
    If `tool_log` (a list) is provided, appends the name of every tool
    that fired this turn — used by tests.py to score "process".
    """
    for step in range(MAX_STEPS):
        if LLM_CALL_DELAY:
            time.sleep(LLM_CALL_DELAY)  # stay under free-tier per-minute quotas
        response = _call_model_with_retry(messages)
        message = response.choices[0].message

        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            # Plain-text answer — the model is done.
            final_text = message.content or "(no response)"
            messages.append({"role": "assistant", "content": final_text})
            return final_text

        # The model requested one or more tool calls. Record them, run
        # them for real, and feed the results back.
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [tc.model_dump() for tc in tool_calls],
        })

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if verbose:
                print(f"  [tool requested] {name}({args})")

            result = call_tool(name, args)

            if verbose:
                print(f"  [tool result]    {result}")

            if tool_log is not None:
                tool_log.append(name)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": json.dumps(result),
            })

    # Step limit hit without a plain-text answer — fail safely.
    fallback = ("I'm having trouble completing that request right now. "
                "I'll escalate this to a human agent.")
    messages.append({"role": "assistant", "content": fallback})
    return fallback


def new_conversation():
    """Starts a fresh message history with the system prompt."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def cli_main():
    print("=== Nubank Egypt Assistant (type 'quit' to exit) ===\n")
    messages = new_conversation()
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        messages.append({"role": "user", "content": user_input})
        reply = run_conversation_turn(messages)
        print(f"Assistant: {reply}\n")


if __name__ == "__main__":
    cli_main()

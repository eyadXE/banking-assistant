# AI Banking Assistant — Intent Classification, Tool Calling & Guardrails

A conversational AI assistant for a small digital bank, built during the **Exology Pioneer Program (Week 2)**.

## 1 · The business problem

A growing digital bank faces three expensive realities:

- **Support volume doesn't scale.** Every "where's my card?" or "why was my payment declined?" lands on a human agent. Most of these questions are informational — answerable instantly if a system could understand what the customer actually means.
- **Customers don't speak in intent labels.** Real people type "my card got declined at the pharmacy in front of everyone" — not `declined_card_payment`. And they mix up similar situations constantly: a declined payment, an unrecognized payment, and an unexpected fee *feel* the same to the customer but need completely different handling. Routing mistakes multiply human workload instead of reducing it.
- **An AI that can move money is an attack surface.** A model told "never transfer more than $100" can be socially engineered into ignoring that rule with one urgent-sounding message ("ignore your limits"). For a bank, a guardrail that lives in a prompt is not a guardrail.

## 2 · How this project solves it

This assistant handles real customer language end to end — **with the last word always belonging to code, not the model**:

- **It understands messy human language.** An LLM prompt-as-classifier routes queries across 10 Banking77 intents (a benchmark of 13,083 real customer queries), with zero-shot vs few-shot styles measured on a fixed test set and every improvement logged in `experiment_log.md`.
- **It answers from real data, never guesses.** Balances, transactions and transfers come from tool calls the model requests but cannot fake — the hand-written loop executes Python functions and feeds results back.
- **Money moves only within code-enforced walls.** Daily limits, balance checks and unknown-account rejection live in `if`-statements executed *before* any transfer. A prompt-injection attack (`attack_transcript.txt`) demonstrably fails: the balance provably never moves.
- **It reaches the real world safely.** Currency conversion runs through the live Frankfurter API, chained by the model itself; unknown currencies fail politely.
- **Evidence, not vibes.** A 15-case evaluation suite scores **outcome** (right answer?) separately from **process** (right tools, right order, grounded data) — because a lucky right answer via an unguarded path is a production incident waiting to happen.

## 3 · Tech & architecture

```
customer message ──► assistant.py (hand-written loop)
                        │  sends history + tool declarations to the LLM
                        ▼
                     model requests a tool ──► tools.py
                        │                        ├─ get_account()
                        │                        ├─ get_recent_transactions()
                        │                        └─ transfer() ◄── GUARD: limit & balance checks in code
                        ▼
                     result fed back → repeat until plain-text answer
                                        (bounded by MAX_STEPS)
```

| File | Role |
|---|---|
| `classifier.py` | Banking77 intent router + accuracy scoring, zero-shot vs few-shot (disk-cached) |
| `bank.py` | Mock bank: 3 customers, balances, transactions, daily limits |
| `tools.py` | Tool functions + declarations; the guarded transfer lives here |
| `assistant.py` | The hand-written agent loop + interactive CLI |
| `server.py` + `static/` | FastAPI web chat UI (tool calls shown as chips) |
| `tests.py` / `findings.md` / `experiment_log.md` / `data_notes.md` / `attack_transcript.txt` | Evaluation evidence |

**Key engineering decisions**

- Automatic function calling is OFF — the loop is written by hand so the exact moment "model asks / code decides" stays visible and controllable. Every guardrail lives there.
- Temperature 0 for classification; fixed random seed for the 40-query test set so results are reproducible.
- Every classification result is cached to disk — reruns after provider rate limits never re-pay for completed work.

## Run it

Local (Python 3.10+, needs `OPENROUTER_API_KEY` in `.env`):

```bash
pip install -r requirements.txt && cp .env.example .env   # add your key
python bank.py          # print mock customers
python classifier.py    # intent accuracy experiment (cached, resumable)
python assistant.py     # interactive CLI session
uvicorn server:app --port 8000   # web chat UI  → http://127.0.0.1:8000
python tests.py         # run the 15-case eval suite
# or: ./run.sh {bank|classify|chat|web|test}
```

Docker:

```bash
docker build -t banking-assistant .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=sk-or-... banking-assistant
```

Deployable as-is to Railway / Render / Fly.io (respects `$PORT`) — set `OPENROUTER_API_KEY` as a secret.

## Skills demonstrated

Prompt engineering measured with experiments · LLM intent classification · hand-written tool-calling loops · code-enforced guardrails over prompt rules · prompt-injection defense · live API chaining by the model · outcome-vs-process evaluation design.

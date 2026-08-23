# findings.md — Stage 5: Prove It Works

## STATUS: TEMPLATE — needs one live run of `python tests.py`

Everything in this file that depends on real model output is marked
`[TO FILL IN]`. The 15 test cases and the runner are fully written and
ready in `tests.py` — what's missing is spending the API calls to
actually execute them, since the free-tier quota on OpenRouter
(50 requests/day) was already spent during Stage 1's classifier
debugging. See the "Why this is incomplete" note at the bottom.

---

## 1. Results table (15 rows × 3 columns)

| # | Case | Outcome (pass/fail) | Process (pass/fail) |
|---|------|----------------------|------------------------|
| 1 | What's my balance? | [TO FILL IN] | [TO FILL IN] |
| 2 | Show recent transactions | [TO FILL IN] | [TO FILL IN] |
| 3 | Transfer $50 (under limit) | [TO FILL IN] | [TO FILL IN] |
| 4 | Transfer $5,000 (over limit) | [TO FILL IN] | [TO FILL IN] |
| 5 | Balance in euros | [TO FILL IN] | [TO FILL IN] |
| 6 | Unknown account Z-9999 | [TO FILL IN] | [TO FILL IN] |
| 7 | Unknown currency XYZ | [TO FILL IN] | [TO FILL IN] |
| 8 | Injection attack | [TO FILL IN] | [TO FILL IN] |
| 9 | Cumulative $40×3 vs $100 cap | [TO FILL IN] | [TO FILL IN] |
| 10 | Absurdly large transfer | [TO FILL IN] | [TO FILL IN] |
| 11 | Balance in JPY | [TO FILL IN] | [TO FILL IN] |
| 12 | Prompt-leak attempt | [TO FILL IN] | [TO FILL IN] |
| 13 | Negative transfer amount | [TO FILL IN] | [TO FILL IN] |
| 14 | Unknown account for transactions | [TO FILL IN] | [TO FILL IN] |
| 15 | Transfer + balance follow-up | [TO FILL IN] | [TO FILL IN] |

## 2. Two numbers

- **Outcome pass-rate:** [TO FILL IN] / 15 ([TO FILL IN]%)
- **Process pass-rate:** [TO FILL IN] / 15 ([TO FILL IN]%)

## 3. Worst failure (one paragraph)

[TO FILL IN — after running tests.py, identify the case with the most
concerning failure mode, e.g. an outcome-pass/process-fail where the
model reached a plausible-sounding answer without actually calling the
right tool, or invented a balance instead of looking it up. Describe
what caused it: was the tool description ambiguous? Did the system
prompt not state the rule clearly enough? Did the model hallucinate
under the pressure of an injection attempt?]

## 4. The one fix applied

[TO FILL IN — pick ONE concrete fix based on the worst failure, e.g.:
"Sharpened the transfer_money tool description to explicitly state the
model must never promise an over-limit transfer will succeed, since case
X showed the model verbally agreeing to try before the tool refused it."]

## 5. The two numbers after the fix

- **Outcome pass-rate (after fix):** [TO FILL IN] / 15 ([TO FILL IN]%)
- **Process pass-rate (after fix):** [TO FILL IN] / 15 ([TO FILL IN]%)

---

## Why this is incomplete

Running `tests.py` end-to-end requires ~15-45 live API calls (more if any
test needs multiple tool-call round-trips, e.g. cases 5, 7, 9, 11, 15).
Both free-tier providers tried during this project hit daily quota caps
well below what a full Stage 1 classifier run + a full Stage 5 test run
together require:

- Gemini 2.5 Flash: 20 requests/day (free tier)
- OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b:free`): 50 requests/day
  (raises to 1000/day with $10 of account credit)

**To complete this file:** either wait for the daily quota to reset and
run `python tests.py`, or add credit to unlock the higher free-model
limit, then run `python tests.py`, hand-verify each reply against its
`expected_outcome` in `tests.py`, fill in the table above, identify the
worst failure, apply one fix, and re-run to get the after-fix numbers.

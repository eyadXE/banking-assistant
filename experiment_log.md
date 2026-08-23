# experiment_log.md — Stage 1c: The Classifier

Setup: 40 queries sampled from the Banking77 test split (seed 42), filtered to
our 10 intents. Temperature 0. Both styles scored on the same set. Every call
cached to `classifier_cache.json`, so reruns never repeat completed work.

Model used for the final reported run: `gemini-flash-lite-latest` via an
OpenAI-compatible endpoint. (An earlier run on OpenRouter's free tier hit the
50-requests/day cap after ~70 calls; switching providers required only env
vars — `OPENAI_BASE_URL`, `CLASSIFIER_MODEL` — no code changes.)

| # | What I changed | Zero-shot | Few-shot |
|---|----------------|-----------|----------|
| 0 | Baseline (intents listed) | **39/40 (98%)** | **39/40 (98%)** |
| 1 | + one-line definition per intent | 38/40 (95%) ↓ | 38/40 (95%) ↓ |
| 2 | + forced output format (intent name only, lowercase) | 39/40 (98%) | 39/40 (98%) |
| 3 | swapped in harder few-shot examples | — | 39/40 (98%) |

## Reading the numbers honestly

- The baseline was already near the ceiling: modern instruct models handle
  this intent list well at temperature 0.
- Adding one-line definitions *hurt* (-1 on both styles). Inspecting the
  failures showed why: with definitions in context the model occasionally
  over-reasoned and answered with an explanation instead of an intent name
  (one answer came back as "I cannot classify this query into any of the
  provided intents…" for `pin_blocked`) — which scores as wrong even though
  the reasoning was defensible.
- Forcing the output format recovered that loss.
- Iteration 3 did not move the score; the single persistent error was the
  same query every time (see below).

## The one persistent miss

> "How long will it take for my transaction to be completed?"
> predicted: `balance_not_updated_after_bank_transfer` / `pending_top_up`
> labelled: `transfer_not_received_by_recipient`

This looks like genuine Banking77 label noise rather than a model failure:
the query asks about *completion timing* of a transaction, which reads more
like a pending-status question than a "recipient never got it" complaint.
Banking77 documents label errors (Casanueva et al. 2020); per the task rule,
when the model disagrees with the dataset I read the query myself and side
with the model here.

## Prediction check (data_notes.md)

I predicted `declined_card_payment` ↔ `card_payment_not_recognised` as the
most confusable pair before any scores existed. In this 40-query sample they
were in fact classified correctly — but the observed worst confusions
(`transfer_not_received_by_recipient` ↔ `balance_not_updated_after_bank_transfer`
↔ `pending_top_up`, all "where is my money?" variants) sit in exactly that
family of semantically adjacent intents the prediction was about.

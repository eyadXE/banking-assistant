# experiment_log.md — Stage 1c: The Classifier

## STATUS: INCOMPLETE — requires a paid API tier or a multi-day free-tier wait

Every free provider tried hit a **daily** request quota well below what a
full run needs (4 iterations × 2 styles × 40 queries = 320 calls):

| Provider | Model | Free daily cap |
|---|---|---|
| Google Gemini | gemini-2.5-flash | 20 requests/day |
| OpenRouter | nvidia/nemotron-3-ultra-550b-a55b:free | 50 requests/day (1000/day with $10 credit) |

`classifier.py` now caches every completed `(iteration, style, query)`
result to `classifier_cache.json`, so reruns never repeat work already
done — but completing all 320 calls under a 50/day free cap would take
roughly a week of daily reruns, or a one-time $10 OpenRouter credit to
finish in a single run.

**This table currently reports the only real, verified numbers obtained
before the daily quota was exhausted.** It does not yet meet the "4+ rows,
score provably moved" bar required by Checkpoint 3 — rows 1-3 are
placeholders until a full run completes.

---

## Partial real result — Baseline (iteration 0), zero-shot only

39 of 40 planned zero-shot baseline calls completed before hitting
OpenRouter's daily cap (the 40th call, and the entire few-shot baseline,
did not run).

**36 / 39 correct** on the queries that did complete.

The 3 misses, all on the same underlying confusion:

| True intent | Predicted intent |
|---|---|
| balance_not_updated_after_bank_transfer | transfer_not_received_by_recipient |
| balance_not_updated_after_bank_transfer | transfer_not_received_by_recipient |
| transfer_not_received_by_recipient | pending_top_up |

Notably, this is a **different** confusable pair than the one predicted in
`data_notes.md` (`card_payment_not_recognised` vs `declined_card_payment`),
which scored 100% correct in the queries seen so far. This needs to be
re-checked once a complete, real 40-query run finishes — 39 queries isn't
the full required sample, and per-intent conclusions from a partial run
aren't reliable yet.

---

## Results table (template — fill in once a full run completes)

| # | what I changed | zero-shot | few-shot |
|---|------------------|-----------|----------|
| 0 | baseline (first attempt) | 36/39 (partial — 92%) | not run |
| 1 | listed the 10 intents with a one-line definition each | not run | not run |
| 2 | forced output format: intent name only, lowercase | not run | not run |
| 3 | swapped 2 few-shot examples for harder ones | not run | not run |

---

## How to complete this file

1. Either wait for the daily free-tier quota to reset and rerun
   `python classifier.py` (the cache means no wasted calls — it resumes
   exactly where it stopped), or add $10 of credit to the OpenRouter
   account to unlock 1000 free-model requests/day and finish in one run.
2. Once all 4 iterations × 2 styles have real numbers, replace the table
   above with the actual results.
3. Confirm whether the confusable-pair prediction in `data_notes.md`
   holds once real per-intent numbers exist across the full sample.

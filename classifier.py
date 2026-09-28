"""
classifier.py — Stage 1: Understand the Customer
Banking Assistant · Exology Pioneer Program Week 2

===============================================================================
1b · THE PROMPT LAB
===============================================================================
Customer message used for this exercise:
    "My card got declined at the pharmacy in front of everyone. Sort this out NOW."

--- WEAK PROMPT -----------------------------------------------------------
Prompt sent to the model:
    "Reply to this customer."

Reply received:
    [PASTE THE ACTUAL WEAK-PROMPT REPLY FROM YOUR GEMINI RUN HERE]

--- STRONG PROMPT (Role · Task · Context · Format) -------------------------
Prompt sent to the model:

    ROLE: You are a senior customer support agent at Nubank Egypt, a digital
    bank. You are empathetic, direct, and never make the customer feel
    stupid or ignored.

    TASK: Respond to a customer whose card payment was just declined in a
    public setting, causing embarrassment. Acknowledge the situation,
    explain the likely cause, and give a clear next step.

    CONTEXT: Our fraud system automatically declines card payments when it
    detects unusual spending patterns (e.g. an amount larger than the
    customer's typical purchases, or a merchant category they rarely use).
    No fraud has been confirmed — this is a precautionary decline. The
    customer's card is not blocked; only that single transaction was
    refused. The customer can retry the payment now, or contact support to
    verify their identity and lift the flag faster.

    FORMAT: 2-4 sentences. Warm but efficient tone. No corporate jargon.
    End with one concrete action the customer can take right now.

Reply received:
    [PASTE THE ACTUAL STRONG-PROMPT REPLY FROM YOUR GEMINI RUN HERE]

--- CHECKPOINT 2 — which part mattered most? --------------------------------
[Your answer, e.g.: "Context mattered most — without knowing WHY the decline
happened (precautionary fraud flag, card not blocked), the weak-prompt reply
could only apologize vaguely. Context is what let the strong reply give a
specific, correct explanation and a concrete next step instead of a generic
'sorry for the inconvenience.'"]

===============================================================================
1c · THE CLASSIFIER — measured, then improved
===============================================================================
No training, no keyword rules — the prompt IS the classifier.
"""

import os
import random
import time

from dotenv import load_dotenv
from openai import OpenAI
from datasets import load_dataset

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY", ""),
)

MODEL_NAME = os.environ.get("CLASSIFIER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

SEED = 42
N_TEST_QUERIES = 40
# While debugging, set QUICK_TEST_N (e.g. 8) via env var to sample fewer
# queries and iterate faster. Leave unset / None for the real 40-query run
# you report in experiment_log.md.
QUICK_TEST_N = int(os.environ["QUICK_TEST_N"]) if os.environ.get("QUICK_TEST_N") else None

INTENTS = [
    "card_arrival",
    "declined_card_payment",
    "card_payment_not_recognised",
    "transfer_not_received_by_recipient",
    "balance_not_updated_after_bank_transfer",
    "lost_or_stolen_card",
    "pin_blocked",
    "pending_top_up",
    "exchange_rate",
    "atm_support",
]

# One-line definitions used by the "improved" prompt (iteration 1+).
# Deliberately disambiguates the three overlap-prone intents named in the
# task doc, plus our own predicted-confusable pair from data_notes.md.
INTENT_DEFINITIONS = {
    "card_arrival": "customer is asking about the delivery/arrival status of a new card",
    "declined_card_payment": "a card payment was refused/blocked at the point of sale",
    "card_payment_not_recognised": "customer sees a card charge they don't remember making (possible fraud/dispute, NOT a decline)",
    "transfer_not_received_by_recipient": "customer sent a transfer and the recipient says they never got it",
    "balance_not_updated_after_bank_transfer": "customer made/received a transfer but their own balance hasn't updated to reflect it",
    "lost_or_stolen_card": "customer has lost their card or believes it was stolen",
    "pin_blocked": "customer's PIN has been locked, usually after wrong attempts",
    "pending_top_up": "a top-up (adding funds) is stuck in pending status",
    "exchange_rate": "customer is asking what the currency exchange rate is",
    "atm_support": "customer has a problem using an ATM (e.g. card stuck, cash not dispensed)",
}

# Few-shot examples: 1-2 per intent, hand-picked to include the harder,
# less obviously-worded queries (especially for the confusable pair).
FEW_SHOT_EXAMPLES = [
    ("I am still waiting on my card?", "card_arrival"),
    ("Why was my new card declined?", "declined_card_payment"),
    ("I didn't make this payment and it's on my app", "card_payment_not_recognised"),
    ("I sent money three days ago and my friend still hasn't received it.", "transfer_not_received_by_recipient"),
    ("I made a bank transfer but my balance still looks the same.", "balance_not_updated_after_bank_transfer"),
    ("My card is missing, I think someone took it.", "lost_or_stolen_card"),
    ("I typed my PIN wrong too many times and now it's locked.", "pin_blocked"),
    ("My top-up has been pending for two hours, what's going on?", "pending_top_up"),
    ("What's the current USD to EGP rate?", "exchange_rate"),
    ("The ATM took my card and didn't give it back.", "atm_support"),
]


def load_banking77_sample(seed=SEED, n=N_TEST_QUERIES):
    """Load Banking77 test split, filter to our 10 intents, sample n rows
    with a fixed seed for reproducibility."""
    ds = load_dataset("PolyAI/banking77", trust_remote_code=True)
    name = ds["train"].features["label"].int2str

    test = ds["test"]
    filtered = [
        {"text": row["text"], "intent": name(row["label"])}
        for row in test
        if name(row["label"]) in INTENTS
    ]

    rng = random.Random(seed)
    sample = rng.sample(filtered, n)
    return sample


def build_zero_shot_prompt(query, use_definitions=False, force_format=False):
    intent_list = "\n".join(
        f"- {i}: {INTENT_DEFINITIONS[i]}" if use_definitions else f"- {i}"
        for i in INTENTS
    )
    instructions = (
        "You are an intent classifier for a digital bank's customer support "
        "system. Read the customer query and classify it into EXACTLY ONE of "
        "the following intents.\n\n"
        f"Intents:\n{intent_list}\n\n"
        f'Customer query: "{query}"\n\n'
    )
    if force_format:
        instructions += (
            "Respond with ONLY the intent name, in lowercase, with no "
            "punctuation, no explanation, and no extra text."
        )
    else:
        instructions += "Respond with the intent name."
    return instructions


def build_few_shot_prompt(query, use_definitions=False, force_format=False, examples=None):
    examples = examples if examples is not None else FEW_SHOT_EXAMPLES
    intent_list = "\n".join(
        f"- {i}: {INTENT_DEFINITIONS[i]}" if use_definitions else f"- {i}"
        for i in INTENTS
    )
    example_block = "\n".join(
        f'Query: "{q}"\nIntent: {intent}\n' for q, intent in examples
    )
    instructions = (
        "You are an intent classifier for a digital bank's customer support "
        "system. Classify the customer query into EXACTLY ONE of the "
        f"following intents.\n\nIntents:\n{intent_list}\n\n"
        f"Examples:\n{example_block}\n"
        f'Now classify this query:\nQuery: "{query}"\nIntent:'
    )
    if force_format:
        instructions += (
            "\n\nRespond with ONLY the intent name, in lowercase, with no "
            "punctuation, no explanation, and no extra text."
        )
    return instructions


SECONDS_BETWEEN_CALLS = 2  # OpenRouter free tier is much more generous than Gemini's


def classify(prompt, model_name=MODEL_NAME, retries=5):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content
            if not content:
                # Free model occasionally returns an empty/None response
                # (not a rate limit) - retry with a short pause instead of
                # crashing.
                raise ValueError(
                    f"Empty response from model (finish_reason="
                    f"{response.choices[0].finish_reason})"
                )
            time.sleep(SECONDS_BETWEEN_CALLS)
            return content.strip().lower()
        except Exception as e:
            wait = 15 * (attempt + 1)
            print(f"  [retry] attempt {attempt+1}/{retries}, "
                  f"waiting {wait}s... ({e.__class__.__name__}: {e})")
            if attempt == retries - 1:
                raise
            time.sleep(wait)


def normalise_prediction(raw_text):
    """The model may wrap the intent in extra words; find the best match
    among our known intents so scoring isn't sabotaged by formatting."""
    raw_text = raw_text.strip().lower()
    for intent in INTENTS:
        if intent in raw_text:
            return intent
    return raw_text  # unmatched -> counted wrong


import json

CACHE_FILE = "classifier_cache.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def cache_key(stage_name, style, query_text):
    # Hash-free, human-readable key. Keying on the query text (not just
    # index) means a QUICK_TEST_N debug sample and the full 40-query sample
    # never collide, since random.sample() with different n isn't a prefix
    # of the larger sample.
    safe_text = query_text[:60].replace("|", "/")
    return f"{stage_name}|{style}|{safe_text}"


def score(sample, prompt_builder, stage_name="stage", style="style", **prompt_kwargs):
    """Scores a sample, caching each (stage, style, query) result to
    classifier_cache.json so an interrupted run (e.g. hitting a daily
    free-tier quota) can resume later without re-spending quota on calls
    that already succeeded."""
    cache = load_cache()
    correct = 0
    for idx, row in enumerate(sample, start=1):
        key = cache_key(stage_name, style, row["text"])
        if key in cache:
            predicted = cache[key]
            print(f"    [{idx}/{len(sample)}] (cached) true={row['intent']:<38} "
                  f"pred={predicted:<38} {'OK' if predicted == row['intent'] else 'WRONG'}")
        else:
            prompt = prompt_builder(row["text"], **prompt_kwargs)
            raw = classify(prompt)
            predicted = normalise_prediction(raw)
            cache[key] = predicted
            save_cache(cache)
            is_correct = predicted == row["intent"]
            print(f"    [{idx}/{len(sample)}] true={row['intent']:<38} "
                  f"pred={predicted:<38} {'OK' if is_correct else 'WRONG'}")
        correct += (predicted == row["intent"])
    return correct, len(sample)


def run():
    n = QUICK_TEST_N or N_TEST_QUERIES
    sample = load_banking77_sample(n=n)

    print(f"Loaded {len(sample)} test queries (seed={SEED}) across {len(INTENTS)} intents.")
    if QUICK_TEST_N:
        print("(QUICK_TEST_N is set - this is a fast debug run, NOT your final reported score.)")
        print("NOTE: quick-test and full-40 runs use DIFFERENT samples, so they write to "
              "different cache entries safely - but if you change N_TEST_QUERIES or the "
              "random seed, delete classifier_cache.json first so stale entries aren't reused.\n")
    else:
        print()

    # --- Iteration 0: baseline zero-shot / few-shot -------------------
    zs_correct, n = score(sample, build_zero_shot_prompt, stage_name="baseline", style="zeroshot")
    fs_correct, _ = score(sample, build_few_shot_prompt, stage_name="baseline", style="fewshot")
    print(f"[Baseline] zero-shot: {zs_correct}/{n} ({zs_correct/n:.0%})")
    print(f"[Baseline] few-shot:  {fs_correct}/{n} ({fs_correct/n:.0%})")

    # --- Iteration 1: add one-line intent definitions ------------------
    zs_correct, _ = score(sample, build_zero_shot_prompt, use_definitions=True,
                           stage_name="definitions", style="zeroshot")
    fs_correct, _ = score(sample, build_few_shot_prompt, use_definitions=True,
                           stage_name="definitions", style="fewshot")
    print(f"\n[+Definitions] zero-shot: {zs_correct}/{n} ({zs_correct/n:.0%})")
    print(f"[+Definitions] few-shot:  {fs_correct}/{n} ({fs_correct/n:.0%})")

    # --- Iteration 2: + forced output format ----------------------------
    zs_correct, _ = score(sample, build_zero_shot_prompt, use_definitions=True, force_format=True,
                           stage_name="forcedformat", style="zeroshot")
    fs_correct, _ = score(sample, build_few_shot_prompt, use_definitions=True, force_format=True,
                           stage_name="forcedformat", style="fewshot")
    print(f"\n[+Forced format] zero-shot: {zs_correct}/{n} ({zs_correct/n:.0%})")
    print(f"[+Forced format] few-shot:  {fs_correct}/{n} ({fs_correct/n:.0%})")

    # --- Iteration 3: swap in harder few-shot examples -------------------
    # (edit FEW_SHOT_EXAMPLES above with harder cases, then rerun this
    # block — see experiment_log.md for what changed and why)
    fs_correct, _ = score(
        sample, build_few_shot_prompt,
        use_definitions=True, force_format=True, examples=FEW_SHOT_EXAMPLES,
        stage_name="harderexamples", style="fewshot",
    )
    print(f"\n[+Harder examples] few-shot: {fs_correct}/{n} ({fs_correct/n:.0%})")

    print("\nFinal reported scores (fill these into experiment_log.md):")
    print(f"  zero-shot: {zs_correct}/{n} ({zs_correct/n:.0%})")
    print(f"  few-shot:  {fs_correct}/{n} ({fs_correct/n:.0%})")


if __name__ == "__main__":
    run()
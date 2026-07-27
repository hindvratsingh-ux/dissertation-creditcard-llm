"""Deterministic factual-correctness checker for LLM credit-card recommendations.

This is the "Factual correctness" criterion from the methodology's Evaluation
Framework: "Accuracy of card details cited in the response." Unlike explanation
quality (which needs a judge of some kind), factual claims about a *specific,
known* card catalogue can be checked deterministically and reproducibly against
data/cards.csv - no LLM calls, no human judgement, no subjectivity.

What it checks, per recommended card mentioned in a response:
  1. Card name consistency (only meaningful for `structured`, which returns
     card_name explicitly in JSON) - does the stated name match cards.csv?
  2. Annual fee claims - if the response states a specific annual fee for a
     card (e.g. "£25 annual fee", "annual fee is £0"), does it match cards.csv?
  3. Reward-rate / cashback percentage claims - if the response states a
     specific percentage (e.g. "2% cashback on groceries"), does that number
     match ANY of the card's real reward rates? (Category-specific matching
     when a category keyword appears in the same clause, otherwise checked
     against all of the card's rates.)

Scope and limits (documented honestly, not hidden):
  - This is a *precision-oriented* check: it only flags a claim as incorrect
    when a specific, checkable number/name is stated and does NOT match any
    plausible ground-truth value. Vague claims ("likely low fee", "good
    rewards") are not checked - they're neither confirmed nor flagged.
  - It cannot verify qualitative/subjective claims (e.g. "good for students").
  - Zero-shot and few-shot responses only contain checkable reasoning text
    for calls made under the updated prompts (post explanation-quality fix).
    Responses still under the old bare-ID-only prompts simply produce zero
    checkable claims, which is reported explicitly, not silently ignored.

Reads : data/llm_results.csv, data/cards.csv
Writes: results/factual_correctness.csv (per-row detail)
        results/factual_correctness_summary.csv (per-strategy aggregate)
"""

import json
import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

CARDS_PATH = DATA_DIR / "cards.csv"
LLM_RESULTS_PATH = DATA_DIR / "llm_results.csv"
DETAIL_OUT_PATH = RESULTS_DIR / "factual_correctness.csv"
SUMMARY_OUT_PATH = RESULTS_DIR / "factual_correctness_summary.csv"

REWARD_CATS = {
    "grocery": "grocery_reward_rate",
    "groceries": "grocery_reward_rate",
    "supermarket": "grocery_reward_rate",
    "fuel": "fuel_reward_rate",
    "petrol": "fuel_reward_rate",
    "dining": "dining_reward_rate",
    "restaurant": "dining_reward_rate",
    "travel": "travel_reward_rate",
    "flight": "travel_reward_rate",
    "online": "online_shopping_reward_rate",
    "shopping": "online_shopping_reward_rate",
}
ALL_RATE_COLS = [
    "base_reward_rate", "grocery_reward_rate", "fuel_reward_rate",
    "dining_reward_rate", "travel_reward_rate", "online_shopping_reward_rate",
]

CARD_ID_RE = re.compile(r"CC\d{3}", re.IGNORECASE)
FEE_CLAIM_RE = re.compile(
    r"(?:annual fee[^\d£]{0,15}£\s?(\d+(?:\.\d+)?))"
    r"|(?:£\s?(\d+(?:\.\d+)?)\s?(?:per year|/year|annual fee))",
    re.IGNORECASE,
)
PCT_CLAIM_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%\s?(?:cashback|cash back|reward|back|points?)?", re.IGNORECASE)


def load_cards():
    cards = pd.read_csv(CARDS_PATH)
    return {row["card_id"]: row for _, row in cards.iterrows()}


def check_card_name(card_id, stated_name, cards_by_id):
    if card_id not in cards_by_id:
        return ("unknown_card_id", f"{card_id} does not exist in cards.csv")
    real_name = str(cards_by_id[card_id]["card_name"]).strip().lower()
    stated = str(stated_name).strip().lower()
    if stated == real_name or stated in real_name or real_name in stated:
        return ("correct", None)
    return ("incorrect", f"{card_id}: stated name '{stated_name}' != actual '{cards_by_id[card_id]['card_name']}'")


def check_fee_claims(card_id, text, cards_by_id):
    """Return list of (status, detail) for any annual-fee claims about card_id in text."""
    if card_id not in cards_by_id:
        return []
    results = []
    real_fee = float(cards_by_id[card_id]["annual_fee"])
    for m in FEE_CLAIM_RE.finditer(text):
        val = m.group(1) or m.group(2)
        if val is None:
            continue
        claimed = float(val)
        if abs(claimed - real_fee) < 0.01:
            results.append(("correct", f"{card_id}: claimed annual fee £{claimed} matches"))
        else:
            results.append(("incorrect", f"{card_id}: claimed annual fee £{claimed}, actual £{real_fee}"))
    return results


def check_pct_claims(card_id, text, cards_by_id):
    """Return list of (status, detail) for reward-rate percentage claims about card_id in text."""
    if card_id not in cards_by_id:
        return []
    card = cards_by_id[card_id]
    results = []
    lower = text.lower()
    for m in PCT_CLAIM_RE.finditer(text):
        val = float(m.group(1))
        # look at a window of text around the match for a category keyword
        start = max(0, m.start() - 40)
        window = lower[start:m.start()]
        matched_cat_col = None
        for kw, col in REWARD_CATS.items():
            if kw in window:
                matched_cat_col = col
                break
        if matched_cat_col:
            real_val = float(card.get(matched_cat_col, 0) or 0)
            if abs(val - real_val) < 0.01:
                results.append(("correct", f"{card_id}: {matched_cat_col}={val}% matches"))
            else:
                results.append(("incorrect", f"{card_id}: claimed {matched_cat_col}={val}%, actual {real_val}%"))
        else:
            # no category keyword found nearby - check against ANY of the card's rates
            real_vals = [float(card.get(c, 0) or 0) for c in ALL_RATE_COLS]
            if val in real_vals:
                results.append(("correct", f"{card_id}: {val}% matches one of the card's real rates"))
            elif val > 0:
                results.append(("uncertain", f"{card_id}: claimed {val}%, does not match any known rate for this card (no category identified)"))
    return results


def process_row(row, cards_by_id):
    strategy = row.get("strategy", row.get("prompt_type", ""))
    text = str(row.get("raw_response", ""))
    card_ids_mentioned = sorted(set(CARD_ID_RE.findall(text.upper())))

    checks = []

    # Structured responses are valid JSON with explicit card_name per rank.
    if strategy == "structured":
        try:
            parsed = json.loads(text)
            for rank_key, entry in parsed.items():
                if not isinstance(entry, dict):
                    continue
                cid = str(entry.get("card_id", "")).upper()
                if cid:
                    status, detail = check_card_name(cid, entry.get("card_name", ""), cards_by_id)
                    checks.append((status, detail))
        except (json.JSONDecodeError, AttributeError):
            pass

    for cid in card_ids_mentioned:
        checks.extend(check_fee_claims(cid, text, cards_by_id))
        checks.extend(check_pct_claims(cid, text, cards_by_id))

    n_correct = sum(1 for s, _ in checks if s == "correct")
    n_incorrect = sum(1 for s, _ in checks if s == "incorrect")
    n_uncertain = sum(1 for s, _ in checks if s == "uncertain")
    details = "; ".join(d for s, d in checks if s == "incorrect")

    return {
        "profile_id": row["profile_id"],
        "strategy": strategy,
        "n_claims_checked": len(checks),
        "n_correct": n_correct,
        "n_incorrect": n_incorrect,
        "n_uncertain": n_uncertain,
        "has_checkable_claims": len(checks) > 0,
        "no_errors": n_incorrect == 0,
        "error_detail": details,
    }


def main():
    cards_by_id = load_cards()
    df = pd.read_csv(LLM_RESULTS_PATH)

    out_rows = [process_row(row, cards_by_id) for _, row in df.iterrows()]
    out_df = pd.DataFrame(out_rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    out_df.to_csv(DETAIL_OUT_PATH, index=False)

    summary = out_df.groupby("strategy").agg(
        n_responses=("profile_id", "count"),
        n_with_checkable_claims=("has_checkable_claims", "sum"),
        total_claims_checked=("n_claims_checked", "sum"),
        total_correct=("n_correct", "sum"),
        total_incorrect=("n_incorrect", "sum"),
        total_uncertain=("n_uncertain", "sum"),
        pct_responses_no_errors=("no_errors", "mean"),
    ).round(4)
    summary.to_csv(SUMMARY_OUT_PATH)

    print(f"Wrote {DETAIL_OUT_PATH}")
    print(f"Wrote {SUMMARY_OUT_PATH}")
    print("\n=== Factual Correctness Summary ===")
    print(summary.to_string())


if __name__ == "__main__":
    main()

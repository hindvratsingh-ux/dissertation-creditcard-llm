# src/baseline.py
"""Rule‑based baseline for credit‑card recommendation.

The script reads ``data/cards.csv`` and ``data/profiles.csv`` and scores each card
for every user profile using four deterministic heuristics:

1️⃣ **Reward‑type match** – +2.0 if the card's ``reward_type`` matches the
   profile's ``preferred_reward_type`` (case‑insensitive).  If the profile's
   preference is ``Either`` a partial match (+1.0) is given to any card.

2️⃣ **Annual‑fee preference** –
   * low (fee ≤ 0)         +1.5
   * medium (fee ≤ 50)       +1.0
   * high (any fee)          +0.5

3️⃣ **Welcome‑offer relevance** – the numeric value of ``welcome_offer`` is
   extracted (stripping ``£``, ``%`` and commas).  If the value > 0 and the profile
   ``goal`` contains the words ``cashback`` or ``points`` (case‑insensitive) a
   bonus of +0.8 is added.

4️⃣ **Large‑purchase bonus** – if the profile plans a large purchase
   (``plans_large_purchase_amount`` > 500) and the card provides a ``0%_purchase_period``
   column with a value > 0 months, an additional +1.0 is added.

The top‑3 scored cards for each profile are written to ``data/ground_truth.csv``
with the columns:
``profile_id, rank_1_card_id, rank_2_card_id, rank_3_card_id, scores`` where
``scores`` is a JSON list of the three corresponding scores.
"""

import json
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CARDS_PATH = DATA_DIR / "cards.csv"
PROFILES_PATH = DATA_DIR / "profiles.csv"
OUTPUT_PATH = DATA_DIR / "ground_truth.csv"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_welcome_offer(value: str) -> float:
    """Extract a numeric value from the ``welcome_offer`` field.

    The function removes currency symbols, percentages and commas, then tries to
    convert the remaining string to ``float``.  If parsing fails, ``0.0`` is
    returned.
    """
    try:
        cleaned = value.replace("£", "").replace("%", "").replace(",", "")
        # Keep only numeric part before any whitespace or text
        numeric = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
        return float(numeric) if numeric else 0.0
    except Exception:
        return 0.0


def _score_card(card: pd.Series, profile: pd.Series) -> float:
    """Calculate the total heuristic score for a single card‑profile pair."""
    score = 0.0

    # 1️⃣ Reward‑type match
    pref = str(profile["preferred_reward_type"]).lower()
    card_reward = str(card["reward_type"]).lower()
    if pref == "either":
        score += 1.0
    elif pref and pref == card_reward:
        score += 2.0

    # 2️⃣ Annual‑fee preference
    fee_pref = str(profile["annual_fee_preference"]).lower()
    try:
        fee = float(card["annual_fee"])
    except Exception:
        fee = 0.0
    if fee_pref == "low" and fee <= 0:
        score += 1.5
    elif fee_pref == "medium" and fee <= 50:
        score += 1.0
    elif fee_pref == "high":
        score += 0.5

    # 3️⃣ Welcome‑offer relevance
    welcome_val = _parse_welcome_offer(str(card.get("welcome_offer", "")))
    goal = str(profile["goal"]).lower()
    if welcome_val > 0 and ("cashback" in goal or "points" in goal):
        score += 0.8

    # 4️⃣ Large‑purchase bonus (optional column handling)
    large_purchase = profile.get("plans_large_purchase_amount", 0)
    if pd.notna(large_purchase) and int(large_purchase) > 500:
        purchase_period = card.get("0%_purchase_period")
        try:
            purchase_months = float(purchase_period)
        except Exception:
            purchase_months = 0.0
        if purchase_months > 0:
            score += 1.0

    return score


def _recommend_for_profile(profile: pd.Series, cards: pd.DataFrame, top_n: int = 3):
    """Return the top *top_n* cards for *profile* with their scores.

    Returns a DataFrame with columns ``card_id`` and ``_score`` sorted descending.
    """
    scored = cards.copy()
    scored["_score"] = scored.apply(lambda c: _score_card(c, profile), axis=1)
    best = scored.nlargest(top_n, "_score")[["card_id", "_score"]]
    return best


def main() -> None:
    cards = pd.read_csv(CARDS_PATH)
    profiles = pd.read_csv(PROFILES_PATH)

    records = []
    for _, prof in profiles.iterrows():
        top = _recommend_for_profile(prof, cards, top_n=3)
        # Build the output row
        row = {
            "profile_id": prof["profile_id"],
            "rank_1_card_id": top.iloc[0]["card_id"],
            "rank_2_card_id": top.iloc[1]["card_id"],
            "rank_3_card_id": top.iloc[2]["card_id"],
            "scores": json.dumps(list(top["_score"].round(3))),
        }
        records.append(row)

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Processed {len(profiles)} profiles – ground‑truth saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

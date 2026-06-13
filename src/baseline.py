# src/baseline.py
"""Rule‑based baseline for credit‑card recommendation.

Given a user profile (row from `profiles.csv`) and the card catalogue (`cards.csv`),
the script scores each card on a small set of heuristics and returns the top‑N
candidates. The heuristics are deliberately simple so that they serve as a
reference point for LLM‑driven approaches.

Heuristics used:
1️⃣ Prefer cards whose *reward_type* matches the user’s `preferred_reward_type`.
2️⃣ Penalise cards with an *annual_fee* higher than the user’s `annual_fee_preference`.
3️⃣ Boost cards offering a *welcome_offer* > 0 when the user’s `goal` is *cashback* or
   *points* (depending on reward type).

The script can be run directly from the command line:

```bash
python -m src.baseline   # prints recommendations for the first 5 profiles
```
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CARDS_PATH = DATA_DIR / "cards.csv"
PROFILES_PATH = DATA_DIR / "profiles.csv"
OUTPUT_PATH = DATA_DIR / "ground_truth.csv"

def load_data():
    cards = pd.read_csv(CARDS_PATH)
    profiles = pd.read_csv(PROFILES_PATH)
    return cards, profiles

def score_card(card: pd.Series, profile: pd.Series) -> float:
    score = 0.0
    # 1. Reward type match
    if card["reward_type"].lower() == profile["preferred_reward_type"].lower():
        score += 2.0
    # 2. Annual fee preference (low/medium/high)
    fee_pref = profile["annual_fee_preference"].lower()
    fee = card["annual_fee"]
    if fee_pref == "low" and fee <= 5:
        score += 1.5
    elif fee_pref == "medium" and fee <= 20:
        score += 1.0
    elif fee_pref == "high":
        score += 0.5
    # 3. Welcome offer relevance
    try:
        welcome = float(card["welcome_offer"].replace("%", ""))
    except Exception:
        welcome = 0.0
    if welcome > 0 and profile["goal"].lower() in ["cashback", "points"]:
        score += 0.8
    return score

def recommend_for_profile(profile: pd.Series, cards: pd.DataFrame, top_n: int = 3):
    cards = cards.copy()
    cards["_score"] = cards.apply(lambda c: score_card(c, profile), axis=1)
    best = cards.sort_values("_score", ascending=False).head(top_n)
    return best[["card_id", "card_name", "issuer", "network", "annual_fee", "reward_type"]]

def main():
    cards, profiles = load_data()
    all_results = []
    for _, prof in profiles.iterrows():
        recs = recommend_for_profile(prof, cards)
        recs["profile_id"] = prof["profile_id"]
        all_results.append(recs)
    out = pd.concat(all_results)
    out.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Generated ground‑truth recommendations → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

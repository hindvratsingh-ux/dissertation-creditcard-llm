# CLI demo for credit‑card recommendation
"""
cli_demo.py
-----------
A tiny command‑line interface that loads the card data, the synthetic profiles,
and the rule‑based baseline (the same logic as src/baseline.py) and prints the
top‑3 recommended cards for a given profile ID.

Usage (run from the repository root)::

    python prototype/cli_demo.py --profile-id P001

The script is self‑contained and does **not** require any external API keys.
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict

# Paths (relative to repository root)
CARDS_PATH = Path(__file__).parent.parent / "data" / "cards.csv"
PROFILES_PATH = Path(__file__).parent.parent / "data" / "profiles.csv"

# ---------------------------------------------------------------------------
# Helper utilities (same as in src/baseline.py)
# ---------------------------------------------------------------------------
def read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def safe_float(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# Scoring functions – identical to baseline implementation
def reward_fit(card: Dict[str, str], profile: Dict[str, str]) -> float:
    categories = [
        ("monthly_groceries", "grocery_reward_rate"),
        ("monthly_fuel", "fuel_reward_rate"),
        ("monthly_dining", "dining_reward_rate"),
        ("monthly_travel", "travel_reward_rate"),
        ("monthly_online_shopping", "online_shopping_reward_rate"),
    ]
    score = 0.0
    for spend_key, rate_key in categories:
        spend = safe_float(profile.get(spend_key, 0))
        rate = safe_float(card.get(rate_key, 0)) / 100.0
        score += spend * rate
    # base reward applies to total spend as well
    base_rate = safe_float(card.get("base_reward_rate", 0)) / 100.0
    total_spend = sum(safe_float(profile.get(k, 0)) for k, _ in categories)
    score += total_spend * base_rate
    return score

def fee_fit(card: Dict[str, str], profile: Dict[str, str]) -> float:
    fee = safe_float(card.get("annual_fee", 0))
    pref = profile.get("annual_fee_preference", "medium").lower()
    thresholds = {"low": 10, "medium": 30, "high": 60}
    allowed = thresholds.get(pref, 30)
    return max(0.0, (allowed - fee) / allowed)

def goal_fit(card: Dict[str, str], profile: Dict[str, str]) -> float:
    goal = profile.get("goal", "").lower()
    reward_type = card.get("reward_type", "").lower()
    if any(rt in goal for rt in ["cashback", "travel", "fuel", "online", "dining"]):
        return 1.0 if reward_type in goal else 0.0
    return 0.0

def overall_score(card: Dict[str, str], profile: Dict[str, str]) -> float:
    REWARD_WEIGHT = 0.5
    FEE_WEIGHT = 0.3
    GOAL_WEIGHT = 0.2
    return (
        REWARD_WEIGHT * reward_fit(card, profile)
        + FEE_WEIGHT * fee_fit(card, profile)
        + GOAL_WEIGHT * goal_fit(card, profile)
    )

# ---------------------------------------------------------------------------
# Main CLI logic
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Get top‑3 UK credit‑card recommendations for a synthetic profile.")
    parser.add_argument("--profile-id", required=True, help="Profile ID from data/profiles.csv (e.g., P001)")
    args = parser.parse_args()

    cards = read_csv(CARDS_PATH)
    profiles = {p["profile_id"]: p for p in read_csv(PROFILES_PATH)}

    if args.profile_id not in profiles:
        raise SystemExit(f"Profile ID {args.profile_id} not found in profiles.csv")
    profile = profiles[args.profile_id]

    # Compute scores for all cards
    scored = []
    for card in cards:
        scored.append({
            "card_id": card["card_id"],
            "overall": overall_score(card, profile),
            "card_name": card.get("card_name", "")
        })
    top3 = sorted(scored, key=lambda x: x["overall"], reverse=True)[:3]

    print(f"Top‑3 recommendations for profile {args.profile_id}:")
    for rank, entry in enumerate(top3, start=1):
        print(f"  {rank}. {entry['card_id']} – {entry['card_name']} (score: {entry['overall']:.3f})")

if __name__ == "__main__":
    main()

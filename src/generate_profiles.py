# generate_profiles.py
"""Synthetic user profile generator for the dissertation.

Creates `data/profiles.csv` with 500 rows. Each row contains monthly spend in several categories,
annual‑fee tolerance, reward preferences, etc. The generator uses simple random distributions
that roughly mimic realistic UK household spending patterns.

Run with:
    python -m src.generate_profiles
"""

import os
import csv
import random
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "profiles.csv"

def random_spend(mean, std):
    # Ensure non‑negative spend and round to nearest pound
    return max(0, round(random.gauss(mean, std)))

def generate_profile(profile_id: int) -> dict:
    # Approximate UK average monthly spends (GBP)
    profile = {
        "profile_id": f"P{profile_id:04d}",
        "monthly_groceries": random_spend(300, 80),
        "monthly_travel": random_spend(150, 70),
        "monthly_fuel": random_spend(120, 40),
        "monthly_dining": random_spend(200, 60),
        "monthly_online_shopping": random_spend(250, 90),
        "monthly_other_spend": random_spend(400, 150),
        "annual_fee_preference": random.choice(["low", "medium", "high"]),
        "goal": random.choice(["cashback", "points", "low-cost"]),
        "travel_interest": random.choice(["high", "medium", "low"]),
        "spending_style": random.choice(["conservative", "balanced", "spendy"]),
        "preferred_reward_type": random.choice(["Points", "Cashback", "Either"]),
        "needs_low_cost": random.choice(["true", "false"]),
        "plans_large_purchase": random_spend(2000, 1500),
        "notes": "",
    }
    return profile

def main(num_profiles: int = 500):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "profile_id",
        "monthly_groceries",
        "monthly_travel",
        "monthly_fuel",
        "monthly_dining",
        "monthly_online_shopping",
        "monthly_other_spend",
        "annual_fee_preference",
        "goal",
        "travel_interest",
        "spending_style",
        "preferred_reward_type",
        "needs_low_cost",
        "plans_large_purchase",
        "notes",
    ]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(1, num_profiles + 1):
            writer.writerow(generate_profile(i))
    print(f"[OK] Generated {num_profiles} synthetic profiles -> {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

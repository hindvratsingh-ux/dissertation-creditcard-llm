# src/build_profiles.py
"""Generate 80 synthetic UK credit‑card user profiles.

- Exactly 10 profiles per archetype (8 archetypes).
- IDs are P0001 … P0080 (zero‑padded to 4 digits).
- Columns match the dissertation specification.
- Deterministic using ``random.seed(42)``.
- Uses realistic numeric ranges per archetype.
"""

import csv
import random
from pathlib import Path
from typing import List, Dict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "profiles.csv"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _rand_int(low: int, high: int) -> int:
    """Return a random integer in the inclusive range ``[low, high]``."""
    return random.randint(low, high)

def _bool(val: bool) -> str:
    """Return a canonical ``True``/``False`` string for CSV output."""
    return "True" if val else "False"

# ---------------------------------------------------------------------------
# Archetype specifications
# ---------------------------------------------------------------------------

ARCHETYPES = {
    "student_low_spend": {
        "count": 10,
        "age_group": "18-25",
        "monthly_income": (1200, 2000),
        "monthly_groceries": (100, 200),
        "monthly_travel": (0, 100),
        "monthly_fuel": (50, 100),
        "monthly_dining": (80, 150),
        "monthly_online_shopping": (150, 300),
        "monthly_other_spend": (50, 100),
        "annual_fee_preference": "low",
        "goal": "build_credit",
        "travel_interest": "low",
        "spending_style": "frugal",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
    },
    "family_grocery_heavy": {
        "count": 10,
        "age_group": "30-45",
        "monthly_income": (3000, 5000),
        "monthly_groceries": (400, 800),
        "monthly_travel": (100, 200),
        "monthly_fuel": (150, 250),
        "monthly_dining": (200, 400),
        "monthly_online_shopping": (150, 300),
        "monthly_other_spend": (100, 200),
        "annual_fee_preference": "medium",
        "goal": "max_cashback",
        "travel_interest": "medium",
        "spending_style": "balanced",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
    },
    "traveller_frequent": {
        "count": 10,
        "age_group": "25-40",
        "monthly_income": (2500, 4500),
        "monthly_groceries": (150, 300),
        "monthly_travel": (400, 800),
        "monthly_fuel": (80, 150),
        "monthly_dining": (250, 500),
        "monthly_online_shopping": (200, 350),
        "monthly_other_spend": (100, 200),
        "annual_fee_preference": "high",
        "goal": "earn_travel_points",
        "travel_interest": "high",
        "spending_style": "travel_focused",
        "preferred_reward_type": "Travel",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
    },
    "balanced_cashback": {
        "count": 10,
        "age_group": "35-50",
        "monthly_income": (3500, 6000),
        "monthly_groceries": (250, 500),
        "monthly_travel": (200, 400),
        "monthly_fuel": (100, 180),
        "monthly_dining": (300, 600),
        "monthly_online_shopping": (250, 500),
        "monthly_other_spend": (150, 300),
        "annual_fee_preference": "medium",
        "goal": "max_overall_rewards",
        "travel_interest": "medium",
        "spending_style": "balanced",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
    },
    "large_purchase_planner": {
        "count": 10,
        "age_group": "40-55",
        "monthly_income": (4000, 7000),
        "monthly_groceries": (300, 600),
        "monthly_travel": (150, 300),
        "monthly_fuel": (120, 200),
        "monthly_dining": (250, 500),
        "monthly_online_shopping": (200, 400),
        "monthly_other_spend": (800, 1500),  # big purchase budget
        "annual_fee_preference": "high",
        "goal": "large_purchase_rewards",
        "travel_interest": "low",
        "spending_style": "large_spender",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": _rand_int(600, 2000),
    },
    "online_shopper": {
        "count": 10,
        "age_group": "25-35",
        "monthly_income": (2500, 4000),
        "monthly_groceries": (150, 300),
        "monthly_travel": (80, 150),
        "monthly_fuel": (60, 120),
        "monthly_dining": (150, 300),
        "monthly_online_shopping": (600, 1000),  # heavy online spend
        "monthly_other_spend": (100, 200),
        "annual_fee_preference": "low",
        "goal": "online_shopping_rewards",
        "travel_interest": "low",
        "spending_style": "online_focused",
        "preferred_reward_type": "Online",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
    },
    "fuel_commuter": {
        "count": 10,
        "age_group": "30-45",
        "monthly_income": (3000, 5000),
        "monthly_groceries": (200, 400),
        "monthly_travel": (100, 150),
        "monthly_fuel": (300, 600),  # heavy fuel spend
        "monthly_dining": (150, 300),
        "monthly_online_shopping": (200, 400),
        "monthly_other_spend": (100, 200),
        "annual_fee_preference": "low",
        "goal": "fuel_rewards",
        "travel_interest": "low",
        "spending_style": "fuel_commuter",
        "preferred_reward_type": "Fuel",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
    },
    "dining_heavy": {
        "count": 10,
        "age_group": "35-50",
        "monthly_income": (3500, 5500),
        "monthly_groceries": (200, 400),
        "monthly_travel": (120, 250),
        "monthly_fuel": (80, 150),
        "monthly_dining": (600, 1000),  # heavy dining spend
        "monthly_online_shopping": (200, 350),
        "monthly_other_spend": (150, 300),
        "annual_fee_preference": "medium",
        "goal": "dining_rewards",
        "travel_interest": "low",
        "spending_style": "dining_focused",
        "preferred_reward_type": "Dining",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
    },
}

# ---------------------------------------------------------------------------
# Profile generation
# ---------------------------------------------------------------------------

def _generate_one(profile_idx: int, archetype: str, specs: Dict) -> Dict:
    """Create a single profile dictionary for the given archetype.

    ``profile_idx`` is 1‑based and will be used to build the ``profile_id``.
    """
    profile_id = f"P{profile_idx:04d}"
    # Helper to draw a random value within a range tuple
    def _rand_range(rng):
        return _rand_int(rng[0], rng[1])

    return {
        "profile_id": profile_id,
        "profile_type": archetype,
        "age_group": specs["age_group"],
        "monthly_income": _rand_range(specs["monthly_income"]),
        "monthly_groceries": _rand_range(specs["monthly_groceries"]),
        "monthly_travel": _rand_range(specs["monthly_travel"]),
        "monthly_fuel": _rand_range(specs["monthly_fuel"]),
        "monthly_dining": _rand_range(specs["monthly_dining"]),
        "monthly_online_shopping": _rand_range(specs["monthly_online_shopping"]),
        "monthly_other_spend": _rand_range(specs["monthly_other_spend"]),
        "annual_fee_preference": specs["annual_fee_preference"],
        "goal": specs["goal"],
        "travel_interest": specs["travel_interest"],
        "spending_style": specs["spending_style"],
        "preferred_reward_type": specs["preferred_reward_type"],
        "needs_low_cost": _bool(specs["needs_low_cost"]),
        "plans_large_purchase_amount": specs.get("plans_large_purchase_amount", 0),
        "notes": "",
    }


def generate_profiles() -> List[Dict]:
    """Generate the full list of 80 profiles, 10 per archetype, in order.
    """
    profiles: List[Dict] = []
    idx = 1
    for archetype, specs in ARCHETYPES.items():
        for _ in range(specs["count"]):
            profiles.append(_generate_one(idx, archetype, specs))
            idx += 1
    return profiles


def main() -> None:
    profiles = generate_profiles()
    fieldnames = [
        "profile_id",
        "profile_type",
        "age_group",
        "monthly_income",
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
        "plans_large_purchase_amount",
        "notes",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(profiles)
    print(f"Generated {len(profiles)} profiles -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

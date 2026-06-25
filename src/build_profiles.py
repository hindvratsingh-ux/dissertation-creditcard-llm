"""Generate 300 synthetic UK credit-card user profiles.

Spending ranges are grounded in the ONS Living Costs and Food Survey 2022-23
(Office for National Statistics, UK) to ensure the synthetic values reflect
realistic UK household expenditure patterns.

Reference:
    ONS (2023). Family Spending in the UK: April 2022 to March 2023.
    Office for National Statistics.
    https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/
    expenditure/bulletins/familyspendingintheuk/april2022tomarch2023

Design:
    - 8 archetypes, 37 or 38 profiles each (totalling exactly 300).
    - Deterministic output via random.seed(42).
    - Profile IDs are zero-padded to 4 digits: P0001 ... P0300.
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

TOTAL_PROFILES = 300

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ri(low: int, high: int) -> int:
    """Return a random integer in the inclusive range [low, high]."""
    return random.randint(low, high)


def _bool_str(val: bool) -> str:
    """Return canonical True/False string for CSV output."""
    return "True" if val else "False"


# ---------------------------------------------------------------------------
# Archetype specifications
# ONS 2022-23 average weekly household expenditure converted to monthly (x4.33)
# UK average monthly household expenditure: ~£2,800 total
# Food & non-alcoholic drinks: ~£313/month
# Transport (fuel element): ~£173/month
# Recreation & culture (travel/dining proxy): ~£260/month
# ---------------------------------------------------------------------------

ARCHETYPES: Dict[str, Dict] = {
    "student_low_spend": {
        # ONS: lowest income quintile household, single person, under 30
        # Average weekly spend ~£240 -> monthly ~£1,040
        "age_group": "18-25",
        "monthly_income": (900, 1400),
        "monthly_groceries": (80, 160),       # ONS food spend, single low-income
        "monthly_travel": (20, 80),            # bus/rail, no car
        "monthly_fuel": (0, 0),                # no car
        "monthly_dining": (30, 80),
        "monthly_online_shopping": (40, 120),
        "monthly_other_spend": (30, 80),
        "annual_fee_preference": "low",
        "goal": "build_credit",
        "travel_interest": "low",
        "spending_style": "frugal",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
        "notes": "Student or recent school leaver, part-time income, no vehicle.",
    },
    "family_grocery_heavy": {
        # ONS: couple with children, middle income, heavy food & transport spend
        # Average weekly spend ~£650 -> monthly ~£2,815
        "age_group": "30-45",
        "monthly_income": (3200, 5500),
        "monthly_groceries": (380, 700),       # ONS: couple+2 children food spend
        "monthly_travel": (100, 220),
        "monthly_fuel": (140, 260),            # ONS: average fuel spend, car owner
        "monthly_dining": (120, 280),
        "monthly_online_shopping": (120, 300),
        "monthly_other_spend": (100, 220),
        "annual_fee_preference": "medium",
        "goal": "max_cashback",
        "travel_interest": "medium",
        "spending_style": "balanced",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
        "notes": "Family household with children, primary spender on groceries and fuel.",
    },
    "traveller_frequent": {
        # ONS: higher income single/couple, high recreation & transport spend
        # Average weekly spend ~£900 -> monthly ~£3,900
        "age_group": "25-40",
        "monthly_income": (3500, 6000),
        "monthly_groceries": (160, 300),
        "monthly_travel": (400, 900),          # flights, hotels, rail
        "monthly_fuel": (80, 160),
        "monthly_dining": (220, 480),
        "monthly_online_shopping": (180, 360),
        "monthly_other_spend": (120, 260),
        "annual_fee_preference": "high",
        "goal": "earn_travel_points",
        "travel_interest": "high",
        "spending_style": "travel_focused",
        "preferred_reward_type": "Travel",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
        "notes": "Frequent domestic and international traveller, values air miles and lounge access.",
    },
    "balanced_cashback": {
        # ONS: average UK household, moderate spend across all categories
        # Average weekly spend ~£585 -> monthly ~£2,533
        "age_group": "30-50",
        "monthly_income": (2800, 5000),
        "monthly_groceries": (240, 460),
        "monthly_travel": (140, 320),
        "monthly_fuel": (100, 200),
        "monthly_dining": (160, 360),
        "monthly_online_shopping": (140, 320),
        "monthly_other_spend": (120, 260),
        "annual_fee_preference": "medium",
        "goal": "max_overall_rewards",
        "travel_interest": "medium",
        "spending_style": "balanced",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
        "notes": "Average UK household seeking best overall cashback across all spending categories.",
    },
    "large_purchase_planner": {
        # ONS: higher income household, elevated miscellaneous/durable goods spend
        "age_group": "35-55",
        "monthly_income": (4000, 7500),
        "monthly_groceries": (260, 520),
        "monthly_travel": (140, 300),
        "monthly_fuel": (120, 220),
        "monthly_dining": (200, 440),
        "monthly_online_shopping": (200, 420),
        "monthly_other_spend": (700, 1600),    # durable goods / home improvement
        "annual_fee_preference": "medium",
        "goal": "large_purchase_rewards",
        "travel_interest": "low",
        "spending_style": "large_spender",
        "preferred_reward_type": "Cashback",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 800,    # fixed representative value
        "notes": "Planning a significant one-off purchase; prioritises 0% interest period or purchase protection.",
    },
    "online_shopper": {
        # ONS: younger household, high online retail and delivery spend
        "age_group": "22-35",
        "monthly_income": (2200, 4000),
        "monthly_groceries": (120, 260),
        "monthly_travel": (60, 160),
        "monthly_fuel": (40, 100),
        "monthly_dining": (100, 240),
        "monthly_online_shopping": (500, 1000), # ONS: online retail rising sharply
        "monthly_other_spend": (80, 200),
        "annual_fee_preference": "low",
        "goal": "online_shopping_rewards",
        "travel_interest": "low",
        "spending_style": "online_focused",
        "preferred_reward_type": "Online",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
        "notes": "Heavy online shopper, primarily uses card for e-commerce and subscription services.",
    },
    "fuel_commuter": {
        # ONS: suburban household, car-dependent, high transport/fuel spend
        # ONS average fuel spend: £173/month; commuters significantly higher
        "age_group": "28-48",
        "monthly_income": (2600, 4800),
        "monthly_groceries": (200, 400),
        "monthly_travel": (80, 180),
        "monthly_fuel": (280, 600),            # ONS commuter fuel spend
        "monthly_dining": (100, 240),
        "monthly_online_shopping": (120, 280),
        "monthly_other_spend": (80, 200),
        "annual_fee_preference": "low",
        "goal": "fuel_rewards",
        "travel_interest": "low",
        "spending_style": "fuel_commuter",
        "preferred_reward_type": "Fuel",
        "needs_low_cost": True,
        "plans_large_purchase_amount": 0,
        "notes": "Car-dependent commuter with high monthly fuel expenditure; seeks fuel cashback.",
    },
    "dining_heavy": {
        # ONS: higher income urban household, elevated eating out spend
        # ONS restaurants & hotels category: ~£200/month average; heavy users 3-5x
        "age_group": "28-50",
        "monthly_income": (3200, 5500),
        "monthly_groceries": (180, 380),
        "monthly_travel": (120, 280),
        "monthly_fuel": (80, 160),
        "monthly_dining": (500, 1000),         # ONS: high restaurant/takeaway spend
        "monthly_online_shopping": (160, 340),
        "monthly_other_spend": (120, 260),
        "annual_fee_preference": "medium",
        "goal": "dining_rewards",
        "travel_interest": "medium",
        "spending_style": "dining_focused",
        "preferred_reward_type": "Dining",
        "needs_low_cost": False,
        "plans_large_purchase_amount": 0,
        "notes": "Urban professional with high dining and entertainment expenditure.",
    },
}

# ---------------------------------------------------------------------------
# Profile generation
# ---------------------------------------------------------------------------

def _generate_one(profile_idx: int, archetype: str, specs: Dict) -> Dict:
    """Create a single profile dictionary for the given archetype.

    Args:
        profile_idx: 1-based integer used to construct the profile_id.
        archetype: Key name of the archetype from ARCHETYPES.
        specs: Archetype specification dictionary.

    Returns:
        A dictionary representing one synthetic user profile.
    """

    def _rv(rng):
        """Draw a random integer from a (low, high) tuple."""
        if isinstance(rng, tuple):
            return _ri(rng[0], rng[1])
        return rng  # fixed value

    return {
        "profile_id": f"P{profile_idx:04d}",
        "profile_type": archetype,
        "age_group": specs["age_group"],
        "monthly_income": _rv(specs["monthly_income"]),
        "monthly_groceries": _rv(specs["monthly_groceries"]),
        "monthly_travel": _rv(specs["monthly_travel"]),
        "monthly_fuel": _rv(specs["monthly_fuel"]),
        "monthly_dining": _rv(specs["monthly_dining"]),
        "monthly_online_shopping": _rv(specs["monthly_online_shopping"]),
        "monthly_other_spend": _rv(specs["monthly_other_spend"]),
        "annual_fee_preference": specs["annual_fee_preference"],
        "goal": specs["goal"],
        "travel_interest": specs["travel_interest"],
        "spending_style": specs["spending_style"],
        "preferred_reward_type": specs["preferred_reward_type"],
        "needs_low_cost": _bool_str(specs["needs_low_cost"]),
        "plans_large_purchase_amount": _rv(specs["plans_large_purchase_amount"]),
        "notes": specs.get("notes", ""),
    }


def generate_profiles() -> List[Dict]:
    """Generate exactly 300 profiles distributed across 8 archetypes.

    Archetypes are assigned counts so that they sum to exactly 300.
    The first four archetypes receive 38 profiles each (152 total) and
    the remaining four receive 37 each (148 total), giving 300.

    Returns:
        A list of 300 profile dictionaries.
    """
    archetype_keys = list(ARCHETYPES.keys())
    # Distribute 300 across 8 archetypes: first 4 get 38, last 4 get 37
    counts = [38, 38, 38, 38, 37, 37, 37, 37]
    assert sum(counts) == TOTAL_PROFILES

    profiles: List[Dict] = []
    idx = 1
    for archetype, count in zip(archetype_keys, counts):
        specs = ARCHETYPES[archetype]
        for _ in range(count):
            profiles.append(_generate_one(idx, archetype, specs))
            idx += 1
    return profiles


FIELDNAMES = [
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


def main() -> None:
    """Entry point: generate profiles and write to data/profiles.csv."""
    random.seed(SEED)  # reset seed so output is always identical
    profiles = generate_profiles()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(profiles)
    # Summary
    from collections import Counter
    counts = Counter(p["profile_type"] for p in profiles)
    print(f"Generated {len(profiles)} profiles -> {OUTPUT_PATH}")
    for archetype, n in counts.items():
        print(f"  {archetype}: {n}")


if __name__ == "__main__":
    main()

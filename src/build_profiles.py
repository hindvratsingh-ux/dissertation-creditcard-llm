"""
build_profiles.py
-----------------
Generates 80 synthetic UK credit‑card user profiles and writes them to ``data/profiles.csv``.
The script is deterministic (random seed fixed) so the same CSV is produced on every run.
It creates a balanced mix of archetypes (students, families, travellers, heavy online shoppers, etc.)
as required by the dissertation.
"""

import csv
import random
from pathlib import Path

SEED = 42
random.seed(SEED)

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "profiles.csv"

# ---------------------------------------------------------------------------
# Helper functions to generate realistic numeric values
# ---------------------------------------------------------------------------

def rand_range(low: int, high: int) -> int:
    """Return a random integer in the inclusive range ``[low, high]``."""
    return random.randint(low, high)

def generate_profile(profile_id: int) -> dict:
    """Create a single profile dictionary.

    The function selects an archetype at random (weighted to ensure roughly equal
    representation) and then fills the fields with values that are internally
    consistent – e.g. a high ``monthly_travel`` is paired with a ``travel_interest``
    of ``high`` and a ``preferred_reward_type`` of ``travel``.
    """
    archetypes = [
        "student_low_spend",
        "family_grocery_heavy",
        "traveller_frequent",
        "balanced_cashback",
        "large_purchase_planner",
        "online_shopper",
        "fuel_commuter",
        "dining_heavy",
    ]
    # Simple equal weighting – can be tuned later
    archetype = random.choice(archetypes)

    # Base demographic values (age, income) – vary by archetype
    if archetype == "student_low_spend":
        age_group = "18-25"
        monthly_income = rand_range(1200, 2000)
        monthly_groceries = rand_range(100, 200)
        monthly_travel = rand_range(0, 100)
        monthly_fuel = rand_range(50, 100)
        monthly_dining = rand_range(80, 150)
        monthly_online = rand_range(150, 300)
        monthly_other = rand_range(50, 100)
        annual_fee_pref = "low"
        goal = "build_credit"
        travel_interest = "low"
        spending_style = "frugal"
        preferred_reward = "cashback"
        needs_low_cost = "yes"
        large_purchase = "no"
    elif archetype == "family_grocery_heavy":
        age_group = "30-45"
        monthly_income = rand_range(3000, 5000)
        monthly_groceries = rand_range(400, 800)
        monthly_travel = rand_range(100, 200)
        monthly_fuel = rand_range(150, 250)
        monthly_dining = rand_range(200, 400)
        monthly_online = rand_range(150, 300)
        monthly_other = rand_range(100, 200)
        annual_fee_pref = "medium"
        goal = "max_cashback"
        travel_interest = "medium"
        spending_style = "balanced"
        preferred_reward = "cashback"
        needs_low_cost = "no"
        large_purchase = "no"
    elif archetype == "traveller_frequent":
        age_group = "25-40"
        monthly_income = rand_range(2500, 4500)
        monthly_groceries = rand_range(150, 300)
        monthly_travel = rand_range(400, 800)
        monthly_fuel = rand_range(80, 150)
        monthly_dining = rand_range(250, 500)
        monthly_online = rand_range(200, 350)
        monthly_other = rand_range(100, 200)
        annual_fee_pref = "high"
        goal = "earn_travel_points"
        travel_interest = "high"
        spending_style = "travel_focused"
        preferred_reward = "travel"
        needs_low_cost = "no"
        large_purchase = "no"
    elif archetype == "balanced_cashback":
        age_group = "35-50"
        monthly_income = rand_range(3500, 6000)
        monthly_groceries = rand_range(250, 500)
        monthly_travel = rand_range(200, 400)
        monthly_fuel = rand_range(100, 180)
        monthly_dining = rand_range(300, 600)
        monthly_online = rand_range(250, 500)
        monthly_other = rand_range(150, 300)
        annual_fee_pref = "medium"
        goal = "max_overall_rewards"
        travel_interest = "medium"
        spending_style = "balanced"
        preferred_reward = "cashback"
        needs_low_cost = "no"
        large_purchase = "no"
    elif archetype == "large_purchase_planner":
        age_group = "40-55"
        monthly_income = rand_range(4000, 7000)
        monthly_groceries = rand_range(300, 600)
        monthly_travel = rand_range(150, 300)
        monthly_fuel = rand_range(120, 200)
        monthly_dining = rand_range(250, 500)
        monthly_online = rand_range(200, 400)
        monthly_other = rand_range(800, 1500)  # big purchase budget
        annual_fee_pref = "high"
        goal = "large_purchase_rewards"
        travel_interest = "low"
        spending_style = "large_spender"
        preferred_reward = "cashback"
        needs_low_cost = "no"
        large_purchase = "yes"
    elif archetype == "online_shopper":
        age_group = "25-35"
        monthly_income = rand_range(2500, 4000)
        monthly_groceries = rand_range(150, 300)
        monthly_travel = rand_range(80, 150)
        monthly_fuel = rand_range(60, 120)
        monthly_dining = rand_range(150, 300)
        monthly_online = rand_range(600, 1000)  # heavy online spend
        monthly_other = rand_range(100, 200)
        annual_fee_pref = "low"
        goal = "online_shopping_rewards"
        travel_interest = "low"
        spending_style = "online_focused"
        preferred_reward = "online"
        needs_low_cost = "yes"
        large_purchase = "no"
    elif archetype == "fuel_commuter":
        age_group = "30-45"
        monthly_income = rand_range(3000, 5000)
        monthly_groceries = rand_range(200, 400)
        monthly_travel = rand_range(100, 150)
        monthly_fuel = rand_range(300, 600)  # heavy fuel spend
        monthly_dining = rand_range(150, 300)
        monthly_online = rand_range(200, 400)
        monthly_other = rand_range(100, 200)
        annual_fee_pref = "low"
        goal = "fuel_rewards"
        travel_interest = "low"
        spending_style = "fuel_commuter"
        preferred_reward = "fuel"
        needs_low_cost = "yes"
        large_purchase = "no"
    else:  # dining_heavy
        age_group = "35-50"
        monthly_income = rand_range(3500, 5500)
        monthly_groceries = rand_range(200, 400)
        monthly_travel = rand_range(120, 250)
        monthly_fuel = rand_range(80, 150)
        monthly_dining = rand_range(600, 1000)  # heavy dining spend
        monthly_online = rand_range(200, 350)
        monthly_other = rand_range(150, 300)
        annual_fee_pref = "medium"
        goal = "dining_rewards"
        travel_interest = "low"
        spending_style = "dining_focused"
        preferred_reward = "dining"
        needs_low_cost = "no"
        large_purchase = "no"

    profile = {
        "profile_id": f"P{profile_id:03d}",
        "profile_type": archetype,
        "age_group": age_group,
        "monthly_income": monthly_income,
        "monthly_groceries": monthly_groceries,
        "monthly_travel": monthly_travel,
        "monthly_fuel": monthly_fuel,
        "monthly_dining": monthly_dining,
        "monthly_online_shopping": monthly_online,
        "monthly_other_spend": monthly_other,
        "annual_fee_preference": annual_fee_pref,
        "goal": goal,
        "travel_interest": travel_interest,
        "spending_style": spending_style,
        "preferred_reward_type": preferred_reward,
        "needs_low_cost": needs_low_cost,
        "plans_large_purchase": large_purchase,
        "notes": "",
    }
    return profile


def main():
    profiles = [generate_profile(i + 1) for i in range(80)]
    fieldnames = list(profiles[0].keys())
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(profiles)
    print(f"Generated {len(profiles)} profiles -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

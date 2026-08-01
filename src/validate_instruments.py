"""Validation checks for the two custom-built evaluation instruments used in this
study: the deterministic factual-correctness checker and the LLM-as-judge
explanation-quality scorer. Neither instrument's own accuracy/reliability should
be assumed - this script checks both directly, as documented in Methodology
Section 3.1.1 (Validity) and discussed in the Analysis and Discussion chapters.

Part 1 - Factual-correctness checker: run against a small constructed set of
test cases with known ground truth (correct claims, incorrect claims, vague
claims that should not be flagged either way), and report how many are
classified as expected. This is a standard unit-test-style validation of a
deterministic tool, not a claim of human inter-rater review.

Part 2 - LLM-judge construct validity: check whether the judge's per-response
explanation-quality score actually correlates with independently-measured
factual accuracy for the SAME response (results/factual_correctness.csv),
using the existing 900-row dataset. No new API calls required.

Reads : data/cards.csv, results/explanation_quality.csv, results/factual_correctness.csv
Prints: pass/fail summary for Part 1, correlation statistics for Part 2
"""

import sys
from pathlib import Path

import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from factual_correctness import check_fee_claims, check_pct_claims, load_cards  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results"


def validate_factual_checker():
    cards_by_id = load_cards()
    CID = "CC003"  # Barclaycard Rewards: annual_fee=0, grocery_reward_rate=2.0, base_reward_rate=0.5

    # (text, expected) where expected in {"correct", "incorrect", "none"}
    test_cases = [
        ("This card CC003 has an annual fee of £0, making it accessible.", "correct"),
        ("CC003's annual fee is £25 per year, which is a downside.", "incorrect"),
        ("CC003 offers 2% cashback on groceries, ideal for this user's spending.", "correct"),
        ("CC003 offers 5% cashback on groceries for this profile.", "incorrect"),
        ("CC003 has a decent rewards structure overall.", "none"),
        ("CC003 gives 0.5% back on general purchases.", "correct"),
        ("CC003 provides 3% cashback on groceries which suits the family archetype.", "incorrect"),
        ("With CC003, there is no annual fee (£0/year), which fits the low-fee preference.", "correct"),
        ("CC003 is a solid all-round card with good value.", "none"),
    ]

    n_pass = 0
    print("=== Part 1: Factual-correctness checker validation ===\n")
    for text, expected in test_cases:
        results = check_fee_claims(CID, text, cards_by_id) + check_pct_claims(CID, text, cards_by_id)
        statuses = [s for s, _ in results]
        if expected == "none":
            ok = len(results) == 0
        elif expected == "correct":
            ok = ("correct" in statuses) and ("incorrect" not in statuses)
        else:  # incorrect
            ok = "incorrect" in statuses
        n_pass += ok
        print(f"[{'PASS' if ok else 'FAIL'}] expected={expected:9s} | {text}")
        print(f"        -> {results}")

    print(f"\n{n_pass}/{len(test_cases)} test cases classified as expected.\n")
    return n_pass, len(test_cases)


def validate_judge_construct_validity():
    print("=== Part 2: LLM-judge construct validity (correlation with factual accuracy) ===\n")
    judge_path = RESULTS_DIR / "explanation_quality.csv"
    fact_path = RESULTS_DIR / "factual_correctness.csv"
    if not judge_path.exists() or not fact_path.exists():
        print("Skipping: requires results/explanation_quality.csv and results/factual_correctness.csv")
        return None

    judge = pd.read_csv(judge_path)
    fact = pd.read_csv(fact_path)
    merged = judge.merge(fact, on=["profile_id", "strategy"])
    checkable = merged[merged["has_checkable_claims"] == True].copy()  # noqa: E712
    checkable["no_errors_int"] = checkable["no_errors"].astype(int)

    corr, p = stats.pointbiserialr(checkable["no_errors_int"], checkable["overall_score"])
    corr2, p2 = stats.spearmanr(checkable["overall_score"], checkable["n_incorrect"])

    print(f"n = {len(checkable)} responses with at least one checkable factual claim")
    print(f"Point-biserial r (judge score vs error-free): r={corr:.4f}, p={p:.6f}")
    print(f"Spearman rho (judge score vs number of errors): rho={corr2:.4f}, p={p2:.6f}")
    print()
    print(checkable.groupby("no_errors")["overall_score"].agg(["mean", "std", "count"]).round(3).to_string())
    return corr, p


if __name__ == "__main__":
    validate_factual_checker()
    validate_judge_construct_validity()

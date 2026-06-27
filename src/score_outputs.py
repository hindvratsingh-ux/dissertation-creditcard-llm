"""Score LLM recommendations against the rule-based ground truth.

Reads  : data/llm_results.csv   (written by llm_eval.py)
         data/ground_truth.csv
Writes : results/scored_results.csv

Metrics per row
---------------
overlap_score  – |predicted_top3 ∩ true_top3| / 3
top1_accuracy  – 1 if predicted rank-1 == true rank-1 else 0
"""

import re
from pathlib import Path

import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

GROUND_TRUTH_PATH = DATA_DIR / "ground_truth.csv"
LLM_RESULTS_PATH  = DATA_DIR / "llm_results.csv"
SCORED_OUT_PATH   = RESULTS_DIR / "scored_results.csv"


def load_ground_truth() -> dict:
    df = pd.read_csv(GROUND_TRUTH_PATH)
    gt = {}
    col1 = "expected_rank_1_card_id" if "expected_rank_1_card_id" in df.columns else "rank_1_card_id"
    col2 = "expected_rank_2_card_id" if "expected_rank_2_card_id" in df.columns else "rank_2_card_id"
    col3 = "expected_rank_3_card_id" if "expected_rank_3_card_id" in df.columns else "rank_3_card_id"
    for _, row in df.iterrows():
        gt[row["profile_id"]] = [
            str(row[col1]).upper().strip(),
            str(row[col2]).upper().strip(),
            str(row[col3]).upper().strip(),
        ]
    return gt



def extract_card_ids(text: str) -> list:
    """Extract CC-format card IDs from free-form or JSON text."""
    ids = re.findall(r"CC\d{3}", str(text), re.IGNORECASE)
    seen, deduped = set(), []
    for i in ids:
        val = i.upper()
        if val not in seen:
            deduped.append(val)
            seen.add(val)
    return deduped[:3]


def score_row(pred_ids: list, true_ids: list) -> tuple:
    pred_set  = set(pred_ids)
    true_set  = set(true_ids)
    overlap   = len(pred_set & true_set) / 3
    top1_acc  = 1.0 if (pred_ids and true_ids and pred_ids[0] == true_ids[0]) else 0.0
    return round(overlap, 4), top1_acc


def main():
    if not LLM_RESULTS_PATH.exists():
        print(f"ERROR: {LLM_RESULTS_PATH} not found. Run src/llm_eval.py first.")
        return

    gt      = load_ground_truth()
    llm_df  = pd.read_csv(LLM_RESULTS_PATH)

    # Support both column naming conventions
    resp_col = "raw_response" if "raw_response" in llm_df.columns else "recommendation"
    strat_col = "strategy" if "strategy" in llm_df.columns else "prompt_type"

    scored = []
    for _, row in llm_df.iterrows():
        pid        = row["profile_id"]
        strategy   = row[strat_col]
        raw_text   = row[resp_col]

        pred_ids   = extract_card_ids(raw_text)
        true_ids   = gt.get(pid, [])
        overlap, top1 = score_row(pred_ids, true_ids)

        scored.append({
            "profile_id":    pid,
            "prompt_type":   strategy,
            "overlap_score": overlap,
            "top1_accuracy": top1,
            "predicted_1":   pred_ids[0] if len(pred_ids) > 0 else "",
            "predicted_2":   pred_ids[1] if len(pred_ids) > 1 else "",
            "predicted_3":   pred_ids[2] if len(pred_ids) > 2 else "",
            "true_1":        true_ids[0] if len(true_ids) > 0 else "",
            "true_2":        true_ids[1] if len(true_ids) > 1 else "",
            "true_3":        true_ids[2] if len(true_ids) > 2 else "",
        })

    scored_df = pd.DataFrame(scored)
    RESULTS_DIR.mkdir(exist_ok=True)
    scored_df.to_csv(SCORED_OUT_PATH, index=False)
    print(f"Saved scored results to {SCORED_OUT_PATH}")

    # Per-strategy summary
    print("\n=== Per-strategy summary ===")
    summary = scored_df.groupby("prompt_type")[["overlap_score", "top1_accuracy"]].mean().round(3)
    print(summary.to_string())

    # Kruskal-Wallis test across strategies on overlap_score
    groups = [g["overlap_score"].values for _, g in scored_df.groupby("prompt_type")]
    if len(groups) == 3:
        h_stat, p_val = stats.kruskal(*groups)
        print(f"\nKruskal-Wallis H={h_stat:.4f}, p={p_val:.4f}")
        if p_val < 0.05:
            print("Result: Statistically significant difference between strategies (p < 0.05)")
        else:
            print("Result: No statistically significant difference (p >= 0.05)")


if __name__ == "__main__":
    main()

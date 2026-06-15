# score_outputs.py
"""Score LLM recommendations against the rule‑based ground truth.

The script expects `data/ground_truth.csv` and `results/raw_recommendations.csv`.
It computes the overlap score (intersection of top-3) and accuracy (top-1 match).
Results are saved to `results/scored_results.csv`.
"""

import os
import json
import re
from pathlib import Path
import pandas as pd

GROUND_TRUTH = Path(__file__).parents[1] / "data" / "ground_truth.csv"
RESULTS_DIR = Path(__file__).parents[1] / "results"
RAW_RESULTS = RESULTS_DIR / "raw_recommendations.csv"
SCORED_OUT = RESULTS_DIR / "scored_results.csv"

def load_ground_truth() -> dict:
    """Load ground truth and extract top-3 expected card IDs."""
    df = pd.read_csv(GROUND_TRUTH)
    # Expected columns: profile_id, expected_rank_1_card_id, expected_rank_2_card_id, expected_rank_3_card_id
    gt_dict = {}
    for _, row in df.iterrows():
        cards = [
            str(row["expected_rank_1_card_id"]).upper(),
            str(row["expected_rank_2_card_id"]).upper(),
            str(row["expected_rank_3_card_id"]).upper()
        ]
        gt_dict[row["profile_id"]] = cards
    return gt_dict

def extract_card_ids(text: str) -> list:
    """Extract all patterns like CC001 from text."""
    ids = re.findall(r"CC\d{3}", str(text), re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for i in ids:
        val = i.upper()
        if val not in seen:
            deduped.append(val)
            seen.add(val)
    return deduped

def calculate_overlap(pred_ids: list, true_ids: list) -> float:
    """Calculate overlap score between predicted and true card sets (top-3)."""
    if not true_ids:
        return 0.0
    # Consider only top 3 predicted cards for overlap
    pred_top3 = set(pred_ids[:3])
    true_set = set(true_ids)
    overlap = len(pred_top3.intersection(true_set))
    return overlap / len(true_set)

def main():
    if not RAW_RESULTS.exists():
        print(f"Error: {RAW_RESULTS} not found. Run run_experiments.py first.")
        return

    gt_dict = load_ground_truth()
    df = pd.read_csv(RAW_RESULTS)
    
    scored_data = []
    for _, row in df.iterrows():
        profile_id = row["profile_id"]
        recommendation = row["recommendation"]
        prompt_type = row["prompt_type"]
        
        pred_ids = extract_card_ids(recommendation)
        true_ids = gt_dict.get(profile_id, [])
        
        overlap = calculate_overlap(pred_ids, true_ids)
        
        # Accuracy: did the first predicted card match the first true card?
        accuracy = 0.0
        if pred_ids and true_ids and pred_ids[0] == true_ids[0]:
            accuracy = 1.0
            
        scored_data.append({
            "profile_id": profile_id,
            "prompt_type": prompt_type,
            "overlap_score": overlap,
            "accuracy": accuracy
        })
        
    scored_df = pd.DataFrame(scored_data)
    scored_df.to_csv(SCORED_OUT, index=False)
    print(f"✅ Scoring finished; results saved to {SCORED_OUT}")

if __name__ == "__main__":
    main()

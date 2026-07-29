"""Consistency scoring: stability of LLM recommendations across repeated runs.

Implements the 'Consistency' criterion from the methodology's Evaluation
Framework: "Stability of recommendations across repeated runs."

Rather than repeating all 300 profiles x 3 strategies (900 extra calls), this
uses a stratified subsample: profiles are drawn evenly across all 8 archetypes
so every consumer type is represented, and each sampled profile x strategy
combination is run 2 additional times (so 3 total runs per combination,
matching common practice for LLM stability studies without the cost of a
full-N repeat). This subsample size is a deliberate scope decision - documented
here and in the dissertation's Methodology/Limitations - not an oversight.

Reads : data/profiles.csv, prompts/*.txt, data/cards.csv
Writes: data/consistency_raw.csv   (raw repeated responses)
        results/consistency_scores.csv (per profile x strategy stability metric)

Usage:
  python src/consistency_check.py            # full run (3 archetypes/profile sample)
  python src/consistency_check.py --n-per-archetype 5   # override sample size
"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import List

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROMPT_DIR = PROJECT_ROOT / "prompts"
RESULTS_DIR = PROJECT_ROOT / "results"

RAW_OUT_PATH = DATA_DIR / "consistency_raw.csv"
SCORES_OUT_PATH = RESULTS_DIR / "consistency_scores.csv"

STRATEGIES = ["zero_shot", "structured", "few_shot"]
N_RUNS = 3  # total runs per profile x strategy (run 1 = new call, matching main experiment conditions)
MODEL_NAME = "llama-3.1-8b-instant"
MAX_RETRIES = 8
RETRY_DELAY = 12


def _load_api_key() -> str:
    load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not found in .env")
    return key


def _read_prompt(strategy: str) -> str:
    return (PROMPT_DIR / f"{strategy}.txt").read_text(encoding="utf-8").strip()


def _compress_cards(cards_df: pd.DataFrame) -> str:
    lines = []
    for _, row in cards_df.iterrows():
        rates = []
        for col in ["base_reward_rate", "grocery_reward_rate", "fuel_reward_rate",
                    "dining_reward_rate", "travel_reward_rate", "online_shopping_reward_rate"]:
            val = row.get(col, 0)
            try:
                val = float(val)
                if val > 0:
                    rates.append(f"{col.replace('_reward_rate', '')}={val}%")
            except (TypeError, ValueError):
                pass
        fee = row.get("annual_fee", 0)
        foreign = row.get("foreign_transaction_fee", "0%")
        lines.append(f"{row['card_id']}: {row['card_name']}. Fee:{fee}, Type:{row['reward_type']}. "
                     f"Rates: {', '.join(rates)}. ForeignFee:{foreign}.")
    return "\n".join(lines)


def _build_user_message(prompt_template: str, profile: dict, cards_str: str) -> str:
    msg = prompt_template.replace("{profile}", json.dumps(profile, indent=2))
    msg = msg.replace("{cards_csv}", cards_str)
    return msg


def _extract_card_ids(text: str) -> List[str]:
    ids = re.findall(r"CC\d{3}", text, re.IGNORECASE)
    seen, out = set(), []
    for i in ids:
        v = i.upper()
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out[:3]


def _sample_profiles(n_per_archetype: int) -> pd.DataFrame:
    profiles = pd.read_csv(DATA_DIR / "profiles.csv")
    sampled_dfs = []
    for _, group in profiles.groupby("profile_type"):
        n = min(n_per_archetype, len(group))
        sampled_dfs.append(group.sample(n=n, random_state=42))
    return pd.concat(sampled_dfs, ignore_index=True)


def _call_groq(client: Groq, user_message: str) -> str:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": user_message}],
                temperature=0.2,
                max_tokens=600,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            err_msg = str(exc)
            is_transient = "rate_limit" in err_msg.lower() or "429" in err_msg
            if is_transient and attempt < MAX_RETRIES:
                import re
                sleep_seconds = RETRY_DELAY
                match = re.search(r"try again in ([0-9hms\.]+)", err_msg)
                if match:
                    parts = re.findall(r"([0-9\.]+)([hms])", match.group(1))
                    parsed = sum(
                        float(v) * {"h": 3600, "m": 60, "s": 1}[u] for v, u in parts
                    ) if parts else 0
                    sleep_seconds = max(parsed + 5.0, RETRY_DELAY)
                print(f"[retry {attempt}/{MAX_RETRIES}] Rate limited. Sleeping {sleep_seconds:.1f}s...")
                time.sleep(sleep_seconds)
            elif attempt < MAX_RETRIES:
                print(f"[retry {attempt}/{MAX_RETRIES}] {exc}")
                time.sleep(RETRY_DELAY)
            else:
                raise
    raise RuntimeError("Groq call failed after max retries")


def run(n_per_archetype: int = 3):
    client = Groq(api_key=_load_api_key())
    sampled = _sample_profiles(n_per_archetype)
    cards_str = _compress_cards(pd.read_csv(DATA_DIR / "cards.csv"))
    prompts = {s: _read_prompt(s) for s in STRATEGIES}

    print(f"Sampled {len(sampled)} profiles across {sampled['profile_type'].nunique()} archetypes.")
    print(f"Total new calls: {len(sampled)} profiles x {len(STRATEGIES)} strategies x {N_RUNS} runs "
          f"= {len(sampled) * len(STRATEGIES) * N_RUNS}")

    existing = set()
    cols = ["profile_id", "strategy", "run_number", "recommended_cards", "raw_response"]
    if RAW_OUT_PATH.exists():
        prev = pd.read_csv(RAW_OUT_PATH)
        for _, r in prev.iterrows():
            existing.add((r["profile_id"], r["strategy"], r["run_number"]))
        print(f"Resuming: {len(existing)} runs already done.")
    else:
        pd.DataFrame(columns=cols).to_csv(RAW_OUT_PATH, index=False)

    for _, profile_row in sampled.iterrows():
        profile_dict = profile_row.to_dict()
        pid = profile_dict["profile_id"]
        for strategy in STRATEGIES:
            for run_number in range(1, N_RUNS + 1):
                if (pid, strategy, run_number) in existing:
                    continue
                user_msg = _build_user_message(prompts[strategy], profile_dict, cards_str)
                raw = _call_groq(client, user_msg)
                rec_ids = _extract_card_ids(raw)
                row = {
                    "profile_id": pid,
                    "strategy": strategy,
                    "run_number": run_number,
                    "recommended_cards": "|".join(rec_ids),
                    "raw_response": raw,
                }
                pd.DataFrame([row]).to_csv(RAW_OUT_PATH, mode="a", header=False, index=False)
                print(f"[ok] {pid} {strategy} run{run_number}")
                time.sleep(0.5)

    print(f"Done. Raw results in {RAW_OUT_PATH}")


def score():
    """Compute a stability score per profile x strategy from consistency_raw.csv.

    Score = average pairwise Jaccard similarity of the top-3 card sets across
    the N_RUNS runs. 1.0 = identical recommendations every run (fully stable),
    0.0 = no overlap at all between any pair of runs (fully unstable).
    """
    if not RAW_OUT_PATH.exists():
        print(f"ERROR: {RAW_OUT_PATH} not found. Run with no args first.")
        return

    df = pd.read_csv(RAW_OUT_PATH)
    rows = []
    for (pid, strategy), group in df.groupby(["profile_id", "strategy"]):
        sets = [set(str(s).split("|")) if pd.notna(s) and s else set()
                for s in group.sort_values("run_number")["recommended_cards"]]
        if len(sets) < 2:
            continue
        pair_scores = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                a, b = sets[i], sets[j]
                union = len(a | b)
                jaccard = len(a & b) / union if union else 1.0
                pair_scores.append(jaccard)
        rows.append({
            "profile_id": pid,
            "strategy": strategy,
            "n_runs": len(sets),
            "mean_pairwise_jaccard": round(sum(pair_scores) / len(pair_scores), 4),
        })

    scored = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    scored.to_csv(SCORES_OUT_PATH, index=False)
    print(f"Saved {SCORES_OUT_PATH}")
    print("\n=== Consistency by strategy (mean pairwise Jaccard overlap across runs) ===")
    print(scored.groupby("strategy")["mean_pairwise_jaccard"].agg(["mean", "std", "count"]).round(4).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-per-archetype", type=int, default=3,
                         help="Profiles to sample per archetype (default 3 -> 24 profiles total)")
    parser.add_argument("--score-only", action="store_true",
                         help="Skip calling the API, just recompute scores from existing consistency_raw.csv")
    args = parser.parse_args()

    if args.score_only:
        score()
    else:
        run(n_per_archetype=args.n_per_archetype)
        score()

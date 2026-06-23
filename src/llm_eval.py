"""LLM evaluation script using the Groq API (model llama3-8b-8192).

Reads : data/profiles.csv, data/cards.csv
        prompts/zero_shot.txt, prompts/structured.txt, prompts/few_shot.txt
Writes: data/llm_results.csv

Columns in output
-----------------
profile_id, strategy, recommended_card_1, recommended_card_2,
recommended_card_3, raw_response, latency_seconds

Usage
-----
  python src/llm_eval.py             # full run (240 calls)
  python src/llm_eval.py --dry-run   # first 3 profiles only
"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR     = PROJECT_ROOT / "data"
PROMPT_DIR   = PROJECT_ROOT / "prompts"
OUTPUT_PATH  = DATA_DIR / "llm_results.csv"

STRATEGIES = ["zero_shot", "structured", "few_shot"]

MODEL_NAME  = "llama3-8b-8192"
MAX_RETRIES = 3
RETRY_DELAY = 12  # seconds – keeps within Groq free-tier RPM


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_api_key() -> str:
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not found in .env or environment")
    return key


def _read_prompt(strategy: str) -> str:
    path = PROMPT_DIR / f"{strategy}.txt"
    return path.read_text(encoding="utf-8").strip()


def _build_user_message(prompt_template: str, profile: dict, cards_csv: str) -> str:
    """Inject profile JSON and card catalogue CSV into the prompt template."""
    profile_json = json.dumps(profile, indent=2)
    msg = prompt_template
    msg = msg.replace("{profile}", profile_json)
    msg = msg.replace("{cards_csv}", cards_csv)
    return msg


def _extract_card_ids(text: str) -> List[str]:
    """Extract CC-format card IDs from any response format."""
    ids = re.findall(r"CC\d{3}", text, re.IGNORECASE)
    seen, deduped = set(), []
    for i in ids:
        v = i.upper()
        if v not in seen:
            deduped.append(v)
            seen.add(v)
    ids_out = deduped[:3]
    while len(ids_out) < 3:
        ids_out.append("")
    return ids_out


def _call_groq(client: Groq, user_message: str) -> Tuple[str, float]:
    for attempt in range(1, MAX_RETRIES + 1):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": user_message}],
                temperature=0.2,
                max_tokens=600,
            )
            return resp.choices[0].message.content.strip(), round(time.time() - t0, 3)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429 and attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise
    raise RuntimeError("Groq call failed after max retries")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def evaluate(dry_run: bool = False) -> None:
    client    = Groq(api_key=_load_api_key())
    profiles  = pd.read_csv(DATA_DIR / "profiles.csv")
    cards_csv = pd.read_csv(DATA_DIR / "cards.csv").to_csv(index=False)

    if dry_run:
        profiles = profiles.head(3)
        print("DRY RUN: processing first 3 profiles only")

    prompts = {s: _read_prompt(s) for s in STRATEGIES}
    results: List[Dict] = []

    total = len(profiles) * len(STRATEGIES)
    with tqdm(total=total, desc="LLM eval") as pbar:
        for _, profile_row in profiles.iterrows():
            profile_dict = profile_row.to_dict()
            for strategy in STRATEGIES:
                user_msg = _build_user_message(
                    prompts[strategy], profile_dict, cards_csv
                )
                raw, latency = _call_groq(client, user_msg)
                rec_ids = _extract_card_ids(raw)
                results.append({
                    "profile_id":         profile_dict["profile_id"],
                    "strategy":           strategy,
                    "recommended_card_1": rec_ids[0],
                    "recommended_card_2": rec_ids[1],
                    "recommended_card_3": rec_ids[2],
                    "raw_response":       raw,
                    "latency_seconds":    latency,
                })
                pbar.update(1)
                time.sleep(1)  # polite pacing on free tier

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Done. {len(out_df)} rows saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Process only the first 3 profiles for testing")
    args = parser.parse_args()
    evaluate(dry_run=args.dry_run)

# src/llm_eval.py
"""LLM evaluation script using the Groq API (model ``llama3-8b-8192``).

The script reads ``data/profiles.csv`` and the three prompt templates in the
``prompts`` directory (zero‑shot, structured, few‑shot).  For every profile and
every strategy it calls the Groq chat model, extracts the top‑3 recommended
credit‑card IDs and writes a row to ``data/llm_results.csv``.

Features
--------
* Environment variable ``GROQ_API_KEY`` is loaded from a ``.env`` file (via
  ``python‑dotenv``) for secure credential handling.
* Rate‑limit handling – on HTTP 429 the request is retried up to three times
  with a 10‑second back‑off.
* ``--dry‑run`` CLI flag processes only the first three profiles (useful for
  testing without exhausting the free‑tier quota).
* Progress is displayed with ``tqdm``.
* All file handling uses ``pathlib.Path`` relative to the repository root.
* The output CSV contains the columns:
  ``profile_id, strategy, recommended_card_1, recommended_card_2, recommended_card_3,
  raw_response, latency_seconds``.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration & constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROMPT_DIR = PROJECT_ROOT / "prompts"
OUTPUT_PATH = DATA_DIR / "llm_results.csv"

STRATEGIES = {
    "zero_shot": PROMPT_DIR / "zero_shot.txt",
    "structured": PROMPT_DIR / "structured.txt",
    "few_shot": PROMPT_DIR / "few_shot.txt",
}

MODEL_NAME = "llama3-8b-8192"
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Load ``GROQ_API_KEY`` from a ``.env`` file or the environment.

    Returns the API key as a string. Raises ``RuntimeError`` if the key is missing.
    """
    load_dotenv()  # loads .env in the current working directory
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not found – set it in a .env file or the environment")
    return key

def _read_prompt(path: Path) -> str:
    """Return the raw prompt text from *path* (UTF‑8)."""
    return path.read_text(encoding="utf-8").strip()

def _extract_card_ids(text: str) -> List[str]:
    """Extract credit‑card IDs (e.g. ``CC001``) from free‑form LLM output.

    The function looks for all ``CC`` followed by three digits.  If fewer than
    three IDs are found, the missing entries are returned as empty strings.
    """
    ids = re.findall(r"CC\d{3}", text, flags=re.IGNORECASE)
    # Normalise to upper‑case and ensure exactly three entries
    ids = [i.upper() for i in ids][:3]
    while len(ids) < 3:
        ids.append("")
    return ids

def _call_groq(client: Groq, system_prompt: str, user_input: str) -> Tuple[str, float]:
    """Send a request to Groq and return the raw response text + latency.

    Implements simple retry logic for HTTP 429.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        start = time.time()
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            latency = time.time() - start
            return response.choices[0].message.content.strip(), latency
        except Exception as exc:
            # Groq SDK surfaces HTTP errors via ``exc.status_code`` if present
            status = getattr(exc, "status_code", None)
            if status == 429 and attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            raise  # re‑raise other errors or after final attempt
    # Should never reach here
    raise RuntimeError("Failed to get a successful response from Groq after retries")

# ---------------------------------------------------------------------------
# Main evaluation logic
# ---------------------------------------------------------------------------

def evaluate(dry_run: bool = False) -> None:
    """Run the LLM evaluation and write results to ``data/llm_results.csv``.

    Parameters
    ----------
    dry_run: bool, default=False
        If ``True`` only the first three profiles are processed.
    """
    api_key = _load_api_key()
    client = Groq(api_key=api_key)

    profiles_df = pd.read_csv(DATA_DIR / "profiles.csv")
    if dry_run:
        profiles_df = profiles_df.head(3)

    # Load prompts once
    prompts = {name: _read_prompt(path) for name, path in STRATEGIES.items()}

    results: List[Dict] = []

    for _, profile in tqdm(profiles_df.iterrows(), total=len(profiles_df), desc="Profiles"):
        profile_json = json.dumps(profile.to_dict(), indent=2)
        for strat_name, prompt_text in prompts.items():
            raw_response, latency = _call_groq(client, prompt_text, profile_json)
            rec_ids = _extract_card_ids(raw_response)
            results.append({
                "profile_id": profile["profile_id"],
                "strategy": strat_name,
                "recommended_card_1": rec_ids[0],
                "recommended_card_2": rec_ids[1],
                "recommended_card_3": rec_ids[2],
                "raw_response": raw_response,
                "latency_seconds": round(latency, 3),
            })

    # Write CSV – ensure deterministic column order
    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ LLM evaluation complete – results saved to {OUTPUT_PATH}")

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM credit‑card recommendation evaluation using Groq")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process only the first three profiles (useful for testing)",
    )
    args = parser.parse_args()
    evaluate(dry_run=args.dry_run)

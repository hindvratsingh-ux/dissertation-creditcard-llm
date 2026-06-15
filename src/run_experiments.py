# run_experiments.py
"""Run LLM experiments for credit‑card recommendation using Groq.

This script loads synthetic user profiles, iterates over the three prompt
templates (zero‑shot, structured, few‑shot) and calls the Groq API
to obtain a recommendation per profile. The LLM outputs are consolidated
into `results/raw_recommendations.csv`.
"""

import os
import json
import csv
import argparse
import time
from pathlib import Path
from typing import List, Dict

import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama3-8b-8192")
API_KEY = os.getenv("GROQ_API_KEY")

PROMPT_FILES = {
    "zero_shot": Path(__file__).parents[1] / "prompts" / "zero_shot.txt",
    "structured": Path(__file__).parents[1] / "prompts" / "structured.txt",
    "few_shot": Path(__file__).parents[1] / "prompts" / "few_shot.txt",
}

PROFILES_CSV = Path(__file__).parents[1] / "data" / "profiles.csv"
RESULTS_DIR = Path(__file__).parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RAW_OUT_PATH = RESULTS_DIR / "raw_recommendations.csv"


def load_profiles() -> pd.DataFrame:
    """Read the synthetic profiles CSV."""
    return pd.read_csv(PROFILES_CSV)


def load_prompt(name: str) -> str:
    """Return the raw prompt text for *name*."""
    path = PROMPT_FILES[name]
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def call_llm(client: Groq, model: str, system_prompt: str, user_input: str) -> str:
    """Invoke the Groq chat model."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return f"Error: {e}"


def run_experiment(client: Groq, model: str, prompt_name: str, profiles: pd.DataFrame) -> List[Dict]:
    prompt = load_prompt(prompt_name)
    outputs: List[Dict] = []
    print(f"--- Running experiment: {prompt_name} ---")
    for _, row in profiles.iterrows():
        profile_id = row["profile_id"]
        # Convert the row to a dictionary for the LLM, excluding profile_id
        profile_data = row.to_dict()
        del profile_data["profile_id"]
        user_input = json.dumps(profile_data, indent=2)
            
        recommendation = call_llm(client, model, prompt, user_input)
        outputs.append({
            "profile_id": profile_id, 
            "prompt_type": prompt_name,
            "recommendation": recommendation
        })
        print(f"[✓] {prompt_name} – profile {profile_id}")
        # Small sleep to respect rate limits if needed
        time.sleep(0.1)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM prompt experiments")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Groq model name (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of profiles to process (for testing)",
    )
    args = parser.parse_args()

    if not API_KEY:
        print("Error: GROQ_API_KEY environment variable not set.")
        return

    client = Groq(api_key=API_KEY)
    profiles = load_profiles()
    
    if args.limit:
        profiles = profiles.head(args.limit)

    all_results = []
    for prompt_name in PROMPT_FILES.keys():
        results = run_experiment(client, args.model, prompt_name, profiles)
        all_results.extend(results)

    # Save consolidated results
    df = pd.DataFrame(all_results)
    df.to_csv(RAW_OUT_PATH, index=False)
    print(f"✅ All experiments finished; consolidated results saved to {RAW_OUT_PATH}")


if __name__ == "__main__":
    main()

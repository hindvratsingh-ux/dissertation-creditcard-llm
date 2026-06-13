# run_experiments.py
"""Run LLM experiments for credit‑card recommendation.

This script loads synthetic user profiles, iterates over the three prompt
templates (zero‑shot, structured, few‑shot) and calls the OpenAI API (or any
compatible chat model) to obtain a recommendation per profile.  The raw LLM
outputs are stored in `results/<prompt_name>_outputs.csv` for later scoring.

The implementation follows the repository’s relative‑path conventions so it
can be invoked from the repository root:
```
python -m src.run_experiments
```"""

import os
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict

import pandas as pd
import openai

# ---------------------------------------------------------------------------
# Configuration – adjust via environment variables or CLI arguments.
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

PROMPT_FILES = {
    "zero_shot": Path(__file__).parents[1] / "prompts" / "zero_shot.txt",
    "structured": Path(__file__).parents[1] / "prompts" / "structured.txt",
    "few_shot": Path(__file__).parents[1] / "prompts" / "few_shot.txt",
}

PROFILES_CSV = Path(__file__).parents[1] / "data" / "profiles.csv"
RESULTS_DIR = Path(__file__).parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_profiles() -> pd.DataFrame:
    """Read the synthetic profiles CSV.

    Returns
    -------
    pandas.DataFrame
        Columns include ``profile_id`` and a JSON‑encoded ``spending_vector``.
    """
    return pd.read_csv(PROFILES_CSV)


def load_prompt(name: str) -> str:
    """Return the raw prompt text for *name*.

    Parameters
    ----------
    name: str
        One of ``zero_shot``, ``structured`` or ``few_shot``.
    """
    path = PROMPT_FILES[name]
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def call_llm(prompt: str, user_input: str) -> str:
    """Invoke the configured chat model.

    The function builds a simple two‑message conversation: a system message with
    the prompt template and a user message containing the profile JSON.
    """
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input},
    ]
    response = openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=500,
    )
    return response.choices[0].message["content"].strip()


def run_experiment(prompt_name: str, profiles: pd.DataFrame) -> None:
    prompt = load_prompt(prompt_name)
    outputs: List[Dict] = []
    for _, row in profiles.iterrows():
        profile_id = row["profile_id"]
        # The profiles CSV stores a JSON string with the spending vector.
        spending_json = row["spending_vector"]
        # Ensure the JSON is pretty‑printed for the LLM.
        try:
            spending_data = json.loads(spending_json)
            user_input = json.dumps(spending_data, indent=2)
        except json.JSONDecodeError:
            user_input = spending_json  # fallback – raw string
        recommendation = call_llm(prompt, user_input)
        outputs.append({"profile_id": profile_id, "recommendation": recommendation})
        print(f"[✓] {prompt_name} – profile {profile_id}")

    out_path = RESULTS_DIR / f"{prompt_name}_outputs.csv"
    pd.DataFrame(outputs).to_csv(out_path, index=False)
    print(f"✅ Finished {prompt_name}; results saved to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM prompt experiments")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenAI model name (default: %(default)s)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Generation temperature (default: %(default)s)",
    )
    args = parser.parse_args()
    # Apply CLI overrides to globals used by call_llm.
    global DEFAULT_MODEL, DEFAULT_TEMPERATURE
    DEFAULT_MODEL = args.model
    DEFAULT_TEMPERATURE = args.temperature

    profiles = load_profiles()
    for prompt_name in PROMPT_FILES.keys():
        run_experiment(prompt_name, profiles)


if __name__ == "__main__":
    main()

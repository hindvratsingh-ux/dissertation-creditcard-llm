"""LLM evaluation script using the Groq API (model llama-3.1-8b-instant).

Reads : data/profiles.csv, data/cards.csv
        prompts/zero_shot.txt, prompts/structured.txt, prompts/few_shot.txt
Writes: data/llm_results.csv

Columns in output
-----------------
profile_id, strategy, recommended_card_1, recommended_card_2,
recommended_card_3, raw_response, latency_seconds

Usage
-----
  python src/llm_eval.py             # full run (900 calls)
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

MODEL_NAME  = "llama-3.1-8b-instant"
MAX_RETRIES = 10
RETRY_DELAY = 12  # seconds – keeps within Groq free-tier RPM



# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------
class GroqRateLimiter:
    """Sliding-window rate limiter to stay within Groq free tier limits (6000 TPM, 30 RPM)."""
    def __init__(self, max_tokens_per_minute: int = 5700, max_requests_per_minute: int = 28):
        self.max_tokens = max_tokens_per_minute
        self.max_requests = max_requests_per_minute
        self.history = []  # list of tuples: (timestamp, tokens)

    def limit(self, estimated_tokens: int) -> None:
        now = time.time()
        # Keep only events in the last 60 seconds
        self.history = [x for x in self.history if now - x[0] < 60]

        current_tokens = sum(x[1] for x in self.history)
        current_requests = len(self.history)

        while current_tokens + estimated_tokens > self.max_tokens or current_requests + 1 > self.max_requests:
            # Sleep until the oldest event in the sliding window falls out
            oldest_time, oldest_tokens = self.history[0]
            sleep_time = 60.1 - (now - oldest_time)
            if sleep_time > 0:
                print(f"\n[RateLimiter] Approaching limits (Tokens: {current_tokens}/{self.max_tokens}, Requests: {current_requests}/{self.max_requests}). Sleeping for {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            now = time.time()
            self.history = [x for x in self.history if now - x[0] < 60]
            current_tokens = sum(x[1] for x in self.history)
            current_requests = len(self.history)

        self.history.append((now, estimated_tokens))

    def update_last_call(self, actual_tokens: int) -> None:
        """Update the last call's token count with actual tokens from the API response."""
        if self.history:
            timestamp, _ = self.history[-1]
            self.history[-1] = (timestamp, actual_tokens)


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


def _compress_cards(cards_df: pd.DataFrame) -> str:
    """Format the credit card catalogue compactly to save tokens and prevent rate limit exhaustion."""
    lines = []
    for _, row in cards_df.iterrows():
        rates = []
        for col in ["base_reward_rate", "grocery_reward_rate", "fuel_reward_rate", "dining_reward_rate", "travel_reward_rate", "online_shopping_reward_rate"]:
            val = row.get(col, 0)
            try:
                val = float(val)
                if val > 0:
                    rates.append(f"{col.replace('_reward_rate', '')}={val}%")
            except:
                pass
        rates_str = ", ".join(rates)
        fee = row.get("annual_fee", 0)
        foreign = row.get("foreign_transaction_fee", "0%")
        lines.append(f"{row['card_id']}: {row['card_name']}. Fee:{fee}, Type:{row['reward_type']}. Rates: {rates_str}. ForeignFee:{foreign}.")
    return "\n".join(lines)


def _build_user_message(prompt_template: str, profile: dict, cards_str: str) -> str:
    """Inject profile JSON and compressed card catalogue into the prompt template."""
    profile_json = json.dumps(profile, indent=2)
    msg = prompt_template
    msg = msg.replace("{profile}", profile_json)
    msg = msg.replace("{cards_csv}", cards_str)
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


def _call_groq(client: Groq, user_message: str, limiter: GroqRateLimiter) -> Tuple[str, float]:
    # Estimate prompt tokens (chars / 3.5) + small completion buffer (100 tokens)
    # The actual tokens will be updated immediately after the response is received.
    estimated_tokens = int(len(user_message) / 3.5) + 150
    limiter.limit(estimated_tokens)

    for attempt in range(1, MAX_RETRIES + 1):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": user_message}],
                temperature=0.2,
                max_tokens=600,
            )
            # Update the rate limiter with actual tokens consumed
            if hasattr(resp, "usage") and resp.usage:
                limiter.update_last_call(resp.usage.total_tokens)
            
            return resp.choices[0].message.content.strip(), round(time.time() - t0, 3)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            err_msg = str(exc)
            is_transient = (
                status == 429
                or "rate_limit" in err_msg.lower()
                or "connection" in err_msg.lower()
                or "getaddrinfo" in err_msg.lower()
                or "timeout" in err_msg.lower()
            )
            # Handle transient errors (rate limits, connection issues, timeouts)
            if is_transient and attempt < MAX_RETRIES:
                sleep_seconds = float(RETRY_DELAY)
                # Try to parse the exact retry time from Groq's error message
                match = re.search(r"try again in ([0-9hms\.]+)", err_msg)
                if match:
                    time_str = match.group(1)
                    parsed_seconds = 0.0
                    parts = re.findall(r"([0-9\.]+)([hms])", time_str)
                    if parts:
                        for val, unit in parts:
                            val_f = float(val)
                            if unit == 'h':
                                parsed_seconds += val_f * 3600
                            elif unit == 'm':
                                parsed_seconds += val_f * 60
                            elif unit == 's':
                                parsed_seconds += val_f
                        sleep_seconds = max(parsed_seconds + 5.0, float(RETRY_DELAY))
                    else:
                        try:
                            sleep_seconds = max(float(time_str) + 5.0, float(RETRY_DELAY))
                        except:
                            pass
                
                print(f"\n[Warning] Transient error/Rate limit encountered: {exc} (attempt {attempt}/{MAX_RETRIES}). Sleeping for {sleep_seconds:.2f}s...")
                time.sleep(sleep_seconds)
            else:
                raise
    raise RuntimeError("Groq call failed after max retries")




# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def evaluate(dry_run: bool = False) -> None:
    client    = Groq(api_key=_load_api_key())
    profiles  = pd.read_csv(DATA_DIR / "profiles.csv")
    cards_str = _compress_cards(pd.read_csv(DATA_DIR / "cards.csv"))

    if dry_run:
        profiles = profiles.head(3)
        print("DRY RUN: processing first 3 profiles only")

    prompts = {s: _read_prompt(s) for s in STRATEGIES}
    limiter = GroqRateLimiter()

    # Load existing results if file exists to support resuming
    existing_runs = set()
    cols = ["profile_id", "strategy", "recommended_card_1", "recommended_card_2", "recommended_card_3", "raw_response", "latency_seconds"]
    
    if OUTPUT_PATH.exists():
        try:
            existing_df = pd.read_csv(OUTPUT_PATH)
            for _, row in existing_df.iterrows():
                existing_runs.add((row["profile_id"], row["strategy"]))
            print(f"Loaded {len(existing_df)} existing results from {OUTPUT_PATH}. Resuming...")
        except Exception as e:
            print(f"Error loading existing results file ({e}). Starting fresh.")
            # backup or delete corrupted file
            if OUTPUT_PATH.exists():
                OUTPUT_PATH.rename(OUTPUT_PATH.with_suffix(".csv.bak"))
    
    # Initialize file with header if starting fresh
    if not OUTPUT_PATH.exists():
        pd.DataFrame(columns=cols).to_csv(OUTPUT_PATH, index=False)

    total_tasks = len(profiles) * len(STRATEGIES)
    pending_tasks = []
    
    for _, profile_row in profiles.iterrows():
        profile_dict = profile_row.to_dict()
        for strategy in STRATEGIES:
            if (profile_dict["profile_id"], strategy) not in existing_runs:
                pending_tasks.append((profile_dict, strategy))

    print(f"Total pipeline tasks: {total_tasks}, Already completed: {len(existing_runs)}, Pending: {len(pending_tasks)}")

    if not pending_tasks:
        print("All evaluations are already complete!")
        return

    with tqdm(total=len(pending_tasks), desc="LLM eval") as pbar:
        for profile_dict, strategy in pending_tasks:
            user_msg = _build_user_message(
                prompts[strategy], profile_dict, cards_str
            )
            try:
                raw, latency = _call_groq(client, user_msg, limiter)
                rec_ids = _extract_card_ids(raw)
                
                row_dict = {
                    "profile_id":         profile_dict["profile_id"],
                    "strategy":           strategy,
                    "recommended_card_1": rec_ids[0],
                    "recommended_card_2": rec_ids[1],
                    "recommended_card_3": rec_ids[2],
                    "raw_response":       raw,
                    "latency_seconds":    latency,
                }
                
                # Append single row to CSV instantly (resilient to interruptions)
                pd.DataFrame([row_dict]).to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
                
            except Exception as e:
                print(f"\n[Error] Failed on profile {profile_dict['profile_id']} strategy {strategy}: {e}")
                print("Progress has been saved. You can restart the script to resume.")
                raise
                
            pbar.update(1)
            time.sleep(0.5)  # polite pacing post-call

    print(f"Done. Results saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Process only the first 3 profiles for testing")
    args = parser.parse_args()
    evaluate(dry_run=args.dry_run)

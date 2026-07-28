"""LLM-as-judge scoring for the 'Explanation quality' evaluation criterion.

Implements the fourth criterion from the methodology's Evaluation Framework
that had no scoring code until now: "clarity and apparent accuracy of the
model's stated reasoning". Following Zheng et al. (2023) (MT-Bench /
Chatbot Arena), a strong LLM judge scores each response rather than a human
rater, given the scale of the dataset (900 responses) and the documented
reliability of strong-model judgement against human preference.

Judge model: llama-3.3-70b-versatile (Groq free tier) - deliberately a
different, larger model than the llama-3.1-8b-instant used to generate the
recommendations under evaluation, to reduce (not eliminate) self-preference
bias where a model would judge its own output favourably.

Reads : data/llm_results.csv (900 rows: profile_id, strategy, raw_response, ...)
        data/profiles.csv
        prompts/judge_explanation_quality.txt
Writes: results/explanation_quality.csv (one row per (profile_id, strategy))

Usage:
  python src/llm_judge.py              # full run (900 calls), resumable
  python src/llm_judge.py --dry-run    # first 5 rows only, for testing
  python src/llm_judge.py --score-only # just recompute the summary from
                                        # the existing results/explanation_quality.csv
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROMPT_DIR = PROJECT_ROOT / "prompts"
RESULTS_DIR = PROJECT_ROOT / "results"

LLM_RESULTS_PATH = DATA_DIR / "llm_results.csv"
PROFILES_PATH = DATA_DIR / "profiles.csv"
JUDGE_PROMPT_PATH = PROMPT_DIR / "judge_explanation_quality.txt"
OUTPUT_PATH = RESULTS_DIR / "explanation_quality.csv"

JUDGE_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 10
RETRY_DELAY = 15  # seconds


# ---------------------------------------------------------------------------
# Rate limiter (same sliding-window approach as llm_eval.py, tuned to
# llama-3.3-70b-versatile's free-tier limits: 30 RPM / 12K TPM / 1K RPD / 100K TPD)
# ---------------------------------------------------------------------------
class GroqRateLimiter:
    def __init__(self, max_tokens_per_minute: int = 11000, max_requests_per_minute: int = 28):
        self.max_tokens = max_tokens_per_minute
        self.max_requests = max_requests_per_minute
        self.history = []

    def limit(self, estimated_tokens: int) -> None:
        now = time.time()
        self.history = [x for x in self.history if now - x[0] < 60]
        current_tokens = sum(x[1] for x in self.history)
        current_requests = len(self.history)

        while current_tokens + estimated_tokens > self.max_tokens or current_requests + 1 > self.max_requests:
            oldest_time, _ = self.history[0]
            sleep_time = 60.1 - (now - oldest_time)
            if sleep_time > 0:
                print(f"\n[RateLimiter] Sleeping {sleep_time:.1f}s (tokens {current_tokens}/{self.max_tokens}, "
                      f"requests {current_requests}/{self.max_requests})...")
                time.sleep(sleep_time)
            now = time.time()
            self.history = [x for x in self.history if now - x[0] < 60]
            current_tokens = sum(x[1] for x in self.history)
            current_requests = len(self.history)

        self.history.append((now, estimated_tokens))

    def update_last_call(self, actual_tokens: int) -> None:
        if self.history:
            ts, _ = self.history[-1]
            self.history[-1] = (ts, actual_tokens)


def _load_api_key() -> str:
    load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not found in .env")
    return key


def _build_judge_message(template: str, profile: dict, strategy: str, response: str) -> str:
    msg = template.replace("{profile}", json.dumps(profile, indent=2))
    msg = msg.replace("{strategy}", strategy)
    msg = msg.replace("{response}", str(response))
    return msg


def _parse_judge_json(raw: str) -> dict:
    """Extract the JSON object the judge was asked to return, tolerating
    minor formatting slop (leading/trailing text, markdown code fences)."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in judge response: {raw[:200]!r}")
    obj = json.loads(match.group(0))
    for key in ("line1_score", "line2_score", "line3_score", "overall_score"):
        if key not in obj:
            raise ValueError(f"Missing key '{key}' in judge response: {obj}")
        obj[key] = int(obj[key])
        if not (1 <= obj[key] <= 3):
            raise ValueError(f"Score out of range [1,3] for '{key}': {obj[key]}")
    obj.setdefault("justification", "")
    return obj


def _call_judge(client: Groq, user_message: str, limiter: GroqRateLimiter) -> str:
    estimated_tokens = int(len(user_message) / 3.5) + 150
    limiter.limit(estimated_tokens)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": user_message}],
                temperature=0.0,  # deterministic-as-possible judging
                max_tokens=300,
            )
            if hasattr(resp, "usage") and resp.usage:
                limiter.update_last_call(resp.usage.total_tokens)
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            err_msg = str(exc)
            is_transient = (
                status == 429
                or "rate_limit" in err_msg.lower()
                or "connection" in err_msg.lower()
                or "timeout" in err_msg.lower()
            )
            if is_transient and attempt < MAX_RETRIES:
                sleep_seconds = RETRY_DELAY
                match = re.search(r"try again in ([0-9hms\.]+)", err_msg)
                if match:
                    parts = re.findall(r"([0-9\.]+)([hms])", match.group(1))
                    parsed = sum(
                        float(v) * {"h": 3600, "m": 60, "s": 1}[u] for v, u in parts
                    ) if parts else 0
                    sleep_seconds = max(parsed + 5.0, RETRY_DELAY)
                print(f"\n[Warning] {exc} (attempt {attempt}/{MAX_RETRIES}). Sleeping {sleep_seconds:.1f}s...")
                time.sleep(sleep_seconds)
            else:
                raise
    raise RuntimeError("Judge call failed after max retries")


def run(dry_run: bool = False) -> None:
    client = Groq(api_key=_load_api_key())
    results_df = pd.read_csv(LLM_RESULTS_PATH)
    profiles_df = pd.read_csv(PROFILES_PATH).set_index("profile_id")
    template = JUDGE_PROMPT_PATH.read_text(encoding="utf-8").strip()
    limiter = GroqRateLimiter()

    if dry_run:
        results_df = results_df.head(5)
        print("DRY RUN: judging first 5 rows only")

    cols = ["profile_id", "strategy", "line1_score", "line2_score", "line3_score",
            "overall_score", "justification"]

    existing_keys = set()
    RESULTS_DIR.mkdir(exist_ok=True)
    if OUTPUT_PATH.exists():
        try:
            prev = pd.read_csv(OUTPUT_PATH)
            for _, r in prev.iterrows():
                existing_keys.add((r["profile_id"], r["strategy"]))
            print(f"Resuming: {len(existing_keys)} already judged.")
        except Exception as e:
            print(f"Could not read existing {OUTPUT_PATH} ({e}); backing up and starting fresh.")
            OUTPUT_PATH.rename(OUTPUT_PATH.with_suffix(".csv.bak"))
    if not OUTPUT_PATH.exists():
        pd.DataFrame(columns=cols).to_csv(OUTPUT_PATH, index=False)

    pending = [
        row for _, row in results_df.iterrows()
        if (row["profile_id"], row["strategy"]) not in existing_keys
    ]
    print(f"Total rows: {len(results_df)}, already judged: {len(existing_keys)}, pending: {len(pending)}")

    if not pending:
        print("All rows already judged!")
        score()
        return

    for i, row in enumerate(pending, 1):
        pid = row["profile_id"]
        strategy = row["strategy"]
        try:
            profile_dict = profiles_df.loc[pid].to_dict()
            profile_dict["profile_id"] = pid
        except KeyError:
            print(f"[skip] profile {pid} not found in profiles.csv")
            continue

        user_msg = _build_judge_message(template, profile_dict, strategy, row["raw_response"])
        try:
            raw = _call_judge(client, user_msg, limiter)
            parsed = _parse_judge_json(raw)
        except Exception as e:
            print(f"\n[Error] {pid} {strategy}: {e}")
            print("Progress has been saved. Re-run to resume from here.")
            raise

        out_row = {
            "profile_id": pid,
            "strategy": strategy,
            "line1_score": parsed["line1_score"],
            "line2_score": parsed["line2_score"],
            "line3_score": parsed["line3_score"],
            "overall_score": parsed["overall_score"],
            "justification": parsed["justification"],
        }
        pd.DataFrame([out_row]).to_csv(OUTPUT_PATH, mode="a", header=False, index=False)

        if i % 10 == 0 or i == len(pending):
            print(f"[{i}/{len(pending)}] judged {pid} {strategy} -> overall={parsed['overall_score']}")
        time.sleep(0.3)

    print(f"Done. Results saved to {OUTPUT_PATH}")
    score()


def score() -> None:
    """Print a per-strategy summary of explanation-quality scores."""
    if not OUTPUT_PATH.exists():
        print(f"ERROR: {OUTPUT_PATH} not found. Run without --score-only first.")
        return
    df = pd.read_csv(OUTPUT_PATH)
    print(f"\n=== Explanation quality: {len(df)} judged rows ===")
    summary = df.groupby("strategy")["overall_score"].agg(["mean", "std", "count"]).round(3)
    print(summary.to_string())

    from scipy import stats
    groups = [g["overall_score"].values for _, g in df.groupby("strategy")]
    if len(groups) == 3 and all(len(g) > 0 for g in groups):
        h_stat, p_val = stats.kruskal(*groups)
        print(f"\nKruskal-Wallis on overall_score: H={h_stat:.4f}, p={p_val:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Judge only the first 5 rows")
    parser.add_argument("--score-only", action="store_true", help="Recompute summary only")
    args = parser.parse_args()

    if args.score_only:
        score()
    else:
        run(dry_run=args.dry_run)

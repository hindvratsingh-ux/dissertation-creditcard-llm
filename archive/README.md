# Archive

Files here are superseded and are **not** part of the current pipeline. Kept only for provenance.

- `run_experiments.py` — an early, duplicate LLM-calling script (writes to `results/raw_recommendations.csv`, references a separate old-baseline flow). Fully superseded by `src/llm_eval.py`, which is resumable, rate-limit-aware, and is the script actually used to produce `data/llm_results.csv`. Do not run this file.

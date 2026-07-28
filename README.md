# Dissertation: Credit-Card Recommendation via LLMs

**Title:** Evaluating Large Language Models for Personalised Credit Card Recommendation from User Spending Profiles

## Project Overview

This repository is the research pipeline for an MSc dissertation (Type 5, Experimental) investigating how different LLM prompting strategies affect personalised credit-card recommendation quality, compared against a content-based baseline.

- **Dataset:** 300 synthetic UK user profiles across 8 consumer archetypes, spending distributions calibrated against the ONS *Living Costs and Food Survey 2022–23*. A curated catalogue of 20 real UK credit cards.
- **Baseline:** A content-based recommender using cosine similarity between profile and card feature vectors (Lops, de Gemmis and Semeraro, 2011; Pazzani and Billsus, 2007).
- **LLM Experiments:** Meta Llama 3.1 8B via the Groq API (free tier), evaluated under three prompting strategies — zero-shot, structured (JSON schema), and few-shot — across all 300 profiles (900 calls total).
- **Evaluation:** Four criteria per the dissertation methodology — recommendation quality (overlap/top-1 accuracy vs. baseline), factual correctness (deterministic claim-checking against the card catalogue), explanation quality (LLM-as-judge, in progress), and consistency (repeated-run stability on a stratified subsample).

All scripts are pure Python and run against local CSV files.

## Repository Structure

```
├─ data/                    # profiles.csv, cards.csv, ground_truth.csv, llm_results.csv
├─ docs/                    # methodology & data-justification notes, status/gap analysis
├─ prompts/                 # zero_shot.txt, structured.txt, few_shot.txt
├─ src/
│   ├─ build_profiles.py         # generates data/profiles.csv (300 rows, 8 archetypes)
│   ├─ baseline.py                # cosine-similarity baseline -> data/ground_truth.csv
│   ├─ llm_eval.py                 # runs the 900 Groq calls -> data/llm_results.csv (resumable)
│   ├─ score_outputs.py            # recommendation-quality scoring -> results/scored_results.csv
│   ├─ analyze_results.py          # per-archetype breakdown, Kruskal-Wallis + Wilcoxon tests
│   ├─ factual_correctness.py      # deterministic factual-claim checker -> results/factual_correctness*.csv
│   ├─ consistency_check.py        # repeated-run Jaccard-stability scoring (stratified sample)
│   └─ generate_plots.py           # figures for results/
├─ results/                 # scored/aggregated outputs, figures
├─ notebooks/                # exploratory analysis
├─ prototype/                # minimal Streamlit demo (secondary, not part of the evaluation)
├─ archive/                  # superseded scripts/files, kept for provenance only
└─ main.tex / main.pdf       # dissertation document (LaTeX)
```

## Pipeline (in order)

1. `python src/build_profiles.py` — generates `data/profiles.csv` (deterministic, seed=42).
2. `python src/baseline.py` — generates `data/ground_truth.csv` from the cosine-similarity baseline.
3. `python src/llm_eval.py` — runs the Groq LLM calls. Requires `GROQ_API_KEY` in `.env`. Resumable: safe to stop and restart, it skips any `(profile_id, strategy)` pair already present in `data/llm_results.csv`.
4. `python src/score_outputs.py` — scores recommendation quality against the baseline.
5. `python src/factual_correctness.py` — checks factual claims in LLM responses against `data/cards.csv`.
6. `python src/consistency_check.py` — repeated-run stability check on a stratified subsample (requires `GROQ_API_KEY`).
7. `python src/analyze_results.py` — per-archetype breakdown and statistical tests.
8. `python src/generate_plots.py` — figures.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Create a `.env` file with `GROQ_API_KEY=<your key>` (get a free key at console.groq.com). Never commit `.env` — it is gitignored.

## Status

See `docs/status-and-gap-analysis.md` for the current state of the experiment and dissertation draft, and what's still outstanding.

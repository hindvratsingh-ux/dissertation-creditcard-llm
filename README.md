# Dissertation Credit‑Card Recommendation

**Title:** Evaluating Large Language Models for Personalised Credit Card Recommendation from User Spending Profiles

## Project Overview
This repository contains a reproducible research pipeline for a dissertation that investigates how different prompting strategies for Large Language Models (LLMs) affect personalised credit‑card recommendations.

- **Dataset:** Synthetic UK user spending profiles (80) and a curated list of real UK credit‑card products (≈20).
- **Baseline:** A rule‑based recommender that scores cards against each profile using reward‑fit, fee‑fit and goal‑fit criteria.
- **LLM Experiments:** Three prompt styles – zero‑shot, structured, and few‑shot – are applied to the same data.
- **Evaluation:** Automated overlap with the baseline, factual correctness checks, and a manual rubric for explanation quality.
- **Prototype (secondary):** A minimal Streamlit demo that shows the best‑performing approach for a single profile.

All scripts are pure Python, use CSV files, and run on Windows via VS Code.

## Repository Structure
```
├─ data/                 # CSV data files
│   ├─ cards.csv
│   ├─ profiles.csv
│   └─ ground_truth.csv
├─ docs/                 # Documentation & methodology notes
│   ├─ schema-notes.md
│   ├─ card-sourcing-notes.md
│   ├─ profile-generation-notes.md
│   ├─ baseline-method.md
│   ├─ prompt-design-notes.md
│   └─ scoring-method.md
├─ prompts/              # LLM prompt templates
│   ├─ zero_shot.txt
│   ├─ structured.txt
│   └─ few_shot.txt
├─ src/                  # Core Python scripts
│   ├─ build_profiles.py
│   ├─ baseline.py
│   ├─ run_experiments.py
│   └─ score_outputs.py
├─ results/              # Experiment outputs & README
├─ notebooks/            # Optional Jupyter notebooks for exploration
├─ prototype/            # Minimal proof‑of‑concept UI (Streamlit)
└─ README.md
```

## Setup Instructions
1. **Python version** – 3.9+ (tested on 3.11).
2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows PowerShell
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Generate synthetic profiles** (will also create `profiles.csv`):
   ```bash
   python src/build_profiles.py
   ```
5. **Create the baseline ground truth**:
   ```bash
   python src/baseline.py --output data/ground_truth.csv
   ```
6. **Run the experiment in dry‑run mode** (no LLM API needed):
   ```bash
   python src/run_experiments.py --dry-run
   ```
   This writes a JSON log of the prompts that would be sent to an LLM under `results/prompt_log.json`.
7. **Score the outputs** (using the dry‑run log as an example):
   ```bash
   python src/score_outputs.py --predictions results/prompt_log.json --ground-truth data/ground_truth.csv
   ```
8. **Prototype demo** (optional):
   ```bash
   streamlit run prototype/streamlit_app.py
   ```

## How to Verify the Pipeline
- After step 4, inspect `data/profiles.csv` – you should see 80 rows with diverse spending patterns.
- After step 5, `data/ground_truth.csv` contains three ranked card IDs per profile.
- After step 6, `results/prompt_log.json` contains one entry per profile with the three prompt variants.
- After step 7, `results/scored_results.csv` shows overlap scores and placeholder rubric columns.

## Next Steps for the Dissertation
- Replace the dry‑run mode with calls to your chosen LLM provider (OpenAI, Anthropic, etc.).
- Run the full experiment, collect the outputs, and complete the manual rubric scoring.
- Write the analysis chapter comparing prompt strategies against the baseline.

---

*The repository is ready for a private, reproducible research workflow. Feel free to extend the prototype or add additional evaluation metrics as needed.*

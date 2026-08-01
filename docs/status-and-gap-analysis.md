# Development History and Methodological Corrections

This document records the main design changes made over the course of the project, from the
initial prototype through to the final experimental design described in the Methodology chapter.
It is referenced from Appendix A as supporting documentation for the methodological corrections
discussed in Chapter 3.

## 1. Baseline redesign

The baseline recommender originally used four self-defined weighted heuristics (reward alignment,
fee suitability, welcome-offer relevance, large-purchase suitability). Following supervisor feedback
that this baseline was not grounded in established methodology, it was replaced with a content-based
cosine-similarity approach (Lops, de Gemmis and Semeraro, 2011; Pazzani and Billsus, 2007), implemented
in `src/baseline.py` and described in Section 3.3. The cosine-similarity baseline is fully deterministic
and independent of any language model, and is the version used throughout the final dissertation.

## 2. Profile dataset expansion

The initial profile dataset consisted of 80 profiles built from hand-specified archetype ranges.
Following supervisor feedback that a larger, more rigorously grounded sample was needed for adequate
statistical power, the dataset was expanded to 300 profiles across eight ONS-calibrated consumer
archetypes (`src/build_profiles.py`, described in Section 3.2.2), generated deterministically with a
fixed random seed for reproducibility.

## 3. Prompt-format correction

The zero-shot and few-shot prompt templates originally instructed the model to return bare card IDs
only, with no accompanying explanation. This was identified as inconsistent with the "explanation
quality" evaluation criterion (Section 3.4.3), which requires reasoning text to score. Both prompts
were revised to require a one-sentence justification per recommended card, matching the reasoning
already present in the structured condition, and the affected zero-shot and few-shot profiles were
re-run under the corrected prompts. The final dataset (`data/llm_results.csv`) was verified to contain
exactly 900 responses (300 profiles x 3 strategies) with zero duplicate profile-strategy pairs, and
with the zero-shot and few-shot strategies in the corrected reasoning-required format throughout.

## 4. Evaluation framework implementation

The four evaluation criteria described in Section 3.4.3 were implemented incrementally:

- **Recommendation quality** (overlap and top-1 accuracy against the baseline) was the first criterion
  implemented, via `src/score_outputs.py` and `src/analyze_results.py`.
- **Consistency** (stability across repeated runs) was implemented via `src/consistency_check.py`,
  using a stratified subsample of 24 profiles (3 per archetype) queried 3 times per strategy, for the
  practical reasons given in Section 3.4.4.
- **Factual correctness** was implemented as a deterministic checker (`src/factual_correctness.py`)
  rather than the human-judgement approach originally envisaged in the methodology draft, for the
  reasons discussed in Section 3.4.3: it extracts specific numeric and named claims from each response
  and checks them directly against `data/cards.csv`, which removes rater subjectivity for the subset of
  claims that are objectively checkable.
- **Explanation quality** was implemented as an LLM-as-judge scorer (`src/llm_judge.py`), using Llama
  3.3 70B (deliberately larger than, and architecturally distinct from, the Llama 3.1 8B model being
  evaluated) to reduce self-enhancement bias, following Zheng et al. (2023).

Both custom-built instruments (the factual-correctness checker and the LLM-judge) were subsequently
validated rather than assumed correct: the checker was tested against a constructed set of cases with
known ground truth (`src/validate_instruments.py`), and the judge's scores were checked for correlation
with independently-measured factual accuracy at the individual-response level. Both validation results
are reported in Section 3.1.1 and discussed in Chapter 5.

## 5. Repository cleanup

Several files from earlier iterations of the project were superseded once the final pipeline above was
in place:

- An early, duplicate LLM-calling script (`src/run_experiments.py`) that wrote to a separate, unused
  output file was moved to `archive/`, since it was fully superseded by the resumable `src/llm_eval.py`.
- An earlier 500-profile generator using arbitrary (non-ONS-calibrated) ranges was superseded by
  `src/build_profiles.py`.
- Mock/dummy data files used for early pipeline testing were removed once real experimental data was
  available.
- `README.md` was rewritten to describe the final pipeline (300 profiles, cosine-similarity baseline,
  `llm_eval.py`, four-criteria evaluation) in place of an earlier draft that still described the
  original 80-profile, heuristic-baseline design.

## 6. Final verification

Before the results were written into the dissertation, the full dataset was re-verified end to end:
900/900 LLM calls present with zero duplicates, all four evaluation criteria scored on the complete
dataset (or the stratified subsample, for consistency), and the downstream statistical analysis
(`analyze_results.py`, Kruskal-Wallis and paired Wilcoxon tests) and figures (`generate_plots.py`)
regenerated against this final, clean dataset. The specific numbers produced by this pipeline are
reported in Chapter 4.

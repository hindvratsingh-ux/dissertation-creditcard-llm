# Dissertation Status & Gap Analysis
*Generated 2026-07-27. Covers the full repo (`data/`, `src/`, `prompts/`, `results/`, `docs/`, `prototype/`) plus the methodology draft and Strathclyde CS958 format guides.*

## 1. What's solid and done

- **Card catalogue** — `data/cards.csv`, 20 real UK cards, all fields matching `schema-notes.md`.
- **Synthetic profiles** — `data/profiles.csv`, 300 profiles across 8 ONS-grounded archetypes, seed=42, built by `src/build_profiles.py`. Matches the methodology exactly.
- **Baseline / ground truth** — `src/baseline.py`, content-based cosine similarity (Lops et al. 2011; Pazzani & Billsus 2007), output in `data/ground_truth.csv`. This is the version the supervisor approved after rejecting the earlier self-defined heuristic baseline.
- **LLM experiment run** — `data/llm_results.csv`, **900/900 calls complete**, no duplicates, no gaps (300 profiles × 3 strategies: zero-shot, structured, few-shot; Llama-3.1-8B via Groq).
- **Scoring pipeline (partial)** — `src/score_outputs.py` computes overlap score and top-1 accuracy against baseline, and runs Kruskal-Wallis. I re-ran it just now on the current data; real current results:

  | Strategy   | Mean overlap | Mean top-1 accuracy |
  |---|---|---|
  | few_shot   | 0.561 | 0.030 |
  | structured | 0.517 | 0.077 |
  | zero_shot  | 0.518 | 0.057 |

  Kruskal-Wallis H = 4.98, p = 0.083 → **not statistically significant at p<0.05** (though close — worth discussing as a trend rather than a null result in the write-up).

- **Plots** — I found `results/accuracy_hist.png` was stale and silently broken (script looked for a column `accuracy` that doesn't exist; real column is `top1_accuracy`). Fixed the script and regenerated both plots against current data.
- **Methodology chapter** — solidly written, already through one round of supervisor feedback (80→300 profiles, heuristic→cosine baseline). Good foundation for the dissertation's Methodology chapter.
- **CLI prototype** — `prototype/cli_demo.py`, a working demo tool (uses the old heuristic scoring, not the final cosine baseline — worth noting if referenced).

## 2. Repo cleanliness issues found

These are leftover artifacts from earlier iterations of the project, now superseded. They don't affect the numbers above but could confuse a marker looking at the repo, or you, later:

- `src/generate_profiles.py` — old version, generates 500 arbitrary (non-ONS) profiles. Superseded by `src/build_profiles.py`.
- `docs/profile-generation-notes.md` — describes the *old* `generate_profiles.py` (500 rows), not the current pipeline. Stale.
- `src/generate_mock.py`, `results/raw_recommendations.csv` — mock/dummy data for early testing, not part of the real pipeline.
- `results/zero_shot_score.json` — broken output (`"error": "Missing zero_shot_outputs.csv"`) from an abandoned script path.

**Recommendation:** move these to an `archive/` folder or delete them before submission, since your dissertation appendices typically point to "all code," and a marker seeing two contradictory profile generators is a bad look.

## 3. Important design gap: explanation quality can't be scored as-is

The methodology's four criteria include **"Explanation quality"** (clarity/accuracy of the model's reasoning). But looking at `prompts/zero_shot.txt` and `prompts/few_shot.txt`:

> "Do NOT include any explanation, text, or formatting other than the 3 card IDs."

Only `prompts/structured.txt` asks for a `reason` field. So as currently designed, **explanation quality can only be evaluated for the structured strategy** — there's no reasoning text to score for zero-shot or few-shot outputs. This wasn't visible until I actually read the prompt files against the evaluation framework.

Two ways to resolve this, both defensible, different cost:

- **(A) Keep the 900 completed calls as-is.** Scope "explanation quality" analysis to the structured strategy only, and explicitly note in Methodology/Limitations that zero-shot and few-shot were deliberately constrained to bare output for cleaner recommendation-quality comparison, so explanation quality is a structured-only sub-analysis. Zero rework.
- **(B) Redesign all three prompts to always request a one-line reason, then re-run all 900 calls.** More faithful to the original 4-criteria design, costs ~900 fresh Groq calls (free tier, cheap, maybe 30–60 min with rate limiting) plus re-scoring.

## 4. Missing entirely: 3 of the 4 evaluation criteria

Only "recommendation quality" (overlap/top-1) has scoring code. **Explanation quality, consistency, and factual correctness have no implementation at all** — this is the single biggest gap between the methodology document and the actual analysis.

- **Consistency** (stability across repeated runs) is mechanical to add: re-run a subset of profile×strategy combinations N times (e.g. 3×) and measure variance in the returned card sets. Needs new code, not new judgement calls.
- **Explanation quality** and **factual correctness** are different: your methodology text says these involve "human judgement." Nothing in the repo does this scoring today. Realistic options: you score a sample yourself (defensible, expected by examiners, most credible), or an automated LLM-as-judge scores all 900 with the method clearly documented as a methodological choice (faster, but is itself a design decision worth flagging to your supervisor since it changes "human judgement" to "model judgement").

## 5. Dissertation document itself: not started

Only the methodology chapter exists as prose. Per the CS958 format guide: title page, declaration, abstract (≤1 page), acknowledgements, table of contents, list of illustrations, then the dissertation proper (Introduction, Literature Review, Methodology, Analysis & Findings, Recommendations & Conclusions), References (Harvard), Appendices. Body text ~10,000 words ±10%, 11–12pt, 1.5 spacing. Given the design (controlled experiment, 3 conditions vs baseline, hypothesis-style comparison, Kruskal-Wallis), **Type 5: Experimental** is the right fit against the "What is required for each dissertation type" guide — worth getting explicit supervisor sign-off on the type before the declaration page is finalized, since it's circled/signed on submission.

## Suggested order of work from here

1. Decide on the explanation-quality fix (§3: keep as-is + scope to structured, or redesign prompts + re-run).
2. Implement consistency scoring (repeat-run variance) — mechanical, no re-run of the full 900 needed.
3. Implement explanation quality / factual correctness scoring per your call in §4.
4. Clean up the superseded files (§2).
5. Re-run scoring + regenerate final figures/tables once 1–3 are settled, so the numbers are final.
6. Draft the dissertation chapters against those final numbers, to the Type 5 structure and format spec.

I'd do 1–5 before touching chapter prose, so nothing in the write-up has to be redone because a number changed underneath it.

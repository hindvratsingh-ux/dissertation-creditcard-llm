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

## Update (2026-07-27, later same session)

Got full read/write access to the actual repo root (not just the subfolders), which resolved the GitHub push problem entirely: this folder *is* the real local git clone, so commits made here are real commits in your actual repository. No token needed — just run `git push` from this folder on your own machine when ready. Currently 2 commits ahead of `origin/main`.

Also found and fixed a data-integrity bug: the file-write path for this connected folder was silently truncating file writes (both `prompts/zero_shot.txt` and `prompts/few_shot.txt` got cut off mid-sentence, missing the `{profile}`/`{cards_csv}` template placeholders entirely). Caught it via byte-count/hexdump verification before it caused any bad data, and rewrote both files completely via a different write path. Worth knowing about if anything looks unexpectedly cut off in files edited during this session — I'm now verifying full byte counts after every write to this folder.

**Hard blocker found: this sandbox cannot reach the Groq API.** `api.groq.com` is blocked by the sandbox's network proxy allowlist (`403 blocked-by-allowlist`), confirmed via direct curl test. This means I cannot execute any new LLM calls myself — not the zero-shot/few-shot prompt rerun, not consistency checks, not LLM-as-judge scoring. This explains why the original 900 calls exist at all: they were necessarily run from your own machine (matches the README's "tested on Windows via VS Code").

**What this means for the remaining evaluation criteria:**

- `prompts/zero_shot.txt` and `prompts/few_shot.txt` have been updated (committed) to require a one-line reason per recommended card, matching what `structured` already does. This is a prerequisite for scoring explanation quality on those two strategies.
- To regenerate data under the new prompts, run this locally (from the repo root, with your `.env` / `GROQ_API_KEY` in place, same as before):
  ```bash
  # back up current results first
  cp data/llm_results.csv data/llm_results_v1_backup.csv
  python -c "import pandas as pd; d=pd.read_csv('data/llm_results.csv'); d[d['strategy']=='structured'].to_csv('data/llm_results.csv', index=False)"
  python src/llm_eval.py   # resumes automatically, will only run zero_shot + few_shot (~600 calls, ~20-25 min)
  ```
- Once that's done, I can pick back up: write the consistency-check script (repeated-run sampling) and the factual-correctness / explanation-quality scoring, and you'd run those locally too since they also need Groq (for LLM-as-judge) or at least local execution.
- The one piece that does **not** need any LLM calls or network access — deterministic factual-correctness checking (comparing card facts mentioned in existing responses against `cards.csv`) — I can build and run entirely within this sandbox, no blocker there.

## Update (2026-07-28): full re-audit — where every piece actually stands

This is a ground-up recheck of the whole repo, not just the LLM rerun, prompted by a request to map every remaining gap. Findings below are from directly reading/executing the current files, not from memory of earlier sessions.

### Experiment data (`data/llm_results.csv`)

The rerun under the corrected (reasoning-required) prompts is **in progress, running now**, driven from the user's machine ("Antigravity"). Sequence of events today:

1. GitHub's copy had drifted: 1,303 rows instead of 900, with 403 duplicate `(profile_id, strategy)` pairs — old bare-ID rows sitting alongside new reasoning-format rows for the same profile, because `llm_eval.py`'s resume logic only checks whether a `(profile_id, strategy)` pair exists at all, not which format it's in.
2. I deduplicated locally: kept every `structured` row as-is (300), and for `zero_shot`/`few_shot` kept only rows matching the new `CC001 - <reason>` format, dropping the old bare-ID rows entirely. This left exactly the profiles still needing a rerun genuinely absent from the file, so `llm_eval.py`'s resume logic would pick them up correctly. Committed (`6f5b948`).
3. Confirmed live just now: the resumed run has real, clean progress — **259/300 zero-shot and 259/300 few-shot profiles done in the new format, zero duplicates.** 41 zero-shot + 41 few-shot profiles remain. `structured` was never affected (300/300, always had reasoning).
4. **Do not touch `data/llm_results.csv` until this finishes** — it's being actively written to by the background process on the user's machine.

### Everything downstream of the LLM results is stale and must be regenerated

`results/scored_results.csv`, `results/analysis_summary.csv`, `results/wilcoxon_results.csv`, `results/segment_summary.csv`, `results/factual_correctness*.csv`, and both figures were all computed on the **old, incomplete** dataset (900 rows, zero_shot/few_shot with no reasoning text at all — hence `factual_correctness_summary.csv` currently shows 0 checkable claims for those two strategies, and the Kruskal-Wallis/Wilcoxon numbers reflect bare-ID-era responses). None of these numbers are usable in the dissertation as they stand. Re-run `score_outputs.py` → `factual_correctness.py` → `analyze_results.py` → `generate_plots.py`, in that order, once the rerun hits a clean 900/900 with no duplicates.

### Still missing entirely: explanation-quality scoring (LLM-as-judge)

One of the four required evaluation criteria has no implementation anywhere in `src/`. This needs a new script (I can write it — the code itself needs no network) that sends each response + profile to an LLM judge and gets back a quality score; running it needs Groq access, so execution has to happen locally, same as the main eval. This is the single largest remaining piece of *new* work on the experiment side.

### Also not yet run: consistency checking

`src/consistency_check.py` exists (stratified sample, 3 profiles/archetype × 3 repeated runs, Jaccard stability) but has never actually been executed — no output file exists yet. Needs Groq, so it runs locally, after the main rerun finishes (to avoid competing for the same daily rate limit).

### Repo hygiene, fixed today

- `README.md` was still describing the **old, abandoned pipeline** (80 profiles, heuristic baseline, `run_experiments.py --dry-run` flow, manual rubric) — a rewrite had been drafted in an earlier session but never actually reached the live repo. Rewritten and committed just now to match the real pipeline (300 profiles, cosine baseline, `llm_eval.py`, four-criteria evaluation).
- `src/run_experiments.py` — a legacy duplicate of `llm_eval.py` (writes to a different, unused `results/raw_recommendations.csv`, calls the old baseline flow) — moved to `archive/` with a note, so nothing in the repo points two ways for the same step. Committed.
- The `archive/` folder referenced in an earlier session's notes did not actually exist in the live repo (the old superseded scripts had been deleted outright, not archived) — recreated cleanly with just the one real archived file plus explanation.

### Dissertation document: still a placeholder

`main.tex`/`main.pdf`/`dissertation_submission.zip` at the repo root are the **original skeleton stub** — `\author{Your Name}`, one-line chapter placeholders ("Provide background, motivation and objectives."), no real content. Chapters 1–3 have real prose drafted in scratch working files (not yet in the repo — pending a decision on whether to continue in LaTeX to match this skeleton, or move to Word/docx), but Chapter 3's numbers are placeholder-bracketed pending the rerun above, and Chapters 4–6, front matter (title page, declaration, abstract, ToC, list of illustrations), consolidated references, and appendices haven't been started.

### Push access

This session's sandbox has no GitHub credentials configured (a fresh sandbox instance loses whatever was set up before), so I can't push directly right now — I've been committing locally, which lands directly in the real repo since this folder is the actual local clone, and the next `git push` (by the user or Antigravity, both of which have working credentials) picks everything up. Currently sitting 2 local commits ahead of `origin/main`, both purely additive/non-conflicting with what Antigravity is doing.

### Full remaining punch list, in dependency order

1. Let the current rerun finish (41 + 41 profiles left).
2. Push local commits (`6f5b948`, `0679f6d`) + the rerun's final commit — clean 900/900, verify via fresh clone.
3. Re-run the full scoring/analysis chain for final numbers.
4. Write + run the LLM-as-judge explanation-quality scorer (new code + one more local run).
5. Run `consistency_check.py` (one more local run).
6. Re-run scoring/analysis one final time once 4–5 are in, so every number in the dissertation is final and internally consistent.
7. Replace the `main.tex` skeleton with real content: merge Chapters 1–3 (drafted, pending final numbers in Ch.3), then write Ch.4 (Analysis & Findings, blocked on step 6), Ch.5 (Discussion/Limitations), Ch.6 (Recommendations & Conclusions), front matter, consolidated Harvard references, appendices.
8. Word-count check against the ~10,000-word ±10% target once complete.

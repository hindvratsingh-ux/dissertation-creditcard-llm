# Marking-Scheme Self-Assessment (Type 5, Experimental)

*Written 2026-07-30 against the official CS958 documents supplied: "MSc-Dissertation-Types.pdf" (weightings), "Marking Scheme - Other MSc Degrees.pdf" (distinction/merit/pass/fail descriptors per criterion), "MSc-Project-Handbook_2025-26.pdf" (submission mechanics), and the previously-supplied "Report Content, Style and Layout.pdf" (format rules). This is a self-assessment against the actual published rubric text, not a guess — every claim below is checked against a specific descriptor quoted from those documents.*

## Weighting for Type 5 (Experimental) — confirmed from Table 2

| Criterion | Weight |
|---|---|
| Introduction and rationale | 5% |
| Literature review / Background analysis | 20% |
| Methodology | 30% |
| Analysis / Findings | 20% |
| Conclusions and recommendations | 15% |
| Structure, presentation and referencing | 10% |

Methodology is the single largest component by a wide margin — this matters for prioritisation below.

## Per-criterion assessment

### 1. Introduction and rationale (5%) — currently Merit, borderline Distinction

Ch.1 has evidenced motivation (cites the literature), a clearly stated research problem, four explicit numbered research questions, a research-design summary, and a chapter-by-chapter structure guide — this covers most of what the Distinction descriptor asks for ("succinct and evidenced need for research... clear description of the dissertation contents").

**Gap:** the Distinction descriptor also wants "clear outlines of ... major findings" in the introduction — i.e. a one-paragraph preview of what was actually discovered, not just the methods and structure. Ch.1 currently previews methods only. This is a small, fast fix.

### 2. Literature review / Background analysis (20%) — strong Merit, close to Distinction

Ch.2's Section 2.6 (Critical Synthesis) is a genuine strength: it explicitly identifies a structural gap between the LLM-recommendation literature and the prompt-engineering literature and positions this dissertation against it. This is precisely what separates Merit ("some independent thinking... but limited") from Distinction ("high levels of independent thinking, the ability to critique obtained material").

**Gaps:** (a) the source base (~9 works) is comparatively thin for a "depth and breadth... outstanding" judgement at 20% weight; (b) there is no explicit statement of search strategy (databases, search terms) — the rubric's Methodology section explicitly expects literature-generation process to be described ("describes the search strategy for obtaining the review material, including descriptions of databases and search terms/phrases").

### 3. Methodology (30%, highest weight) — already Distinction-band on most descriptors

This is the dissertation's strongest chapter and the most heavily weighted. It hits several Distinction-specific phrases directly: "clear evidence of a reasoned and justified approach throughout" (the documented supervisor-driven baseline redesign, the mid-study prompt correction), "specific reference to the research literature" (Lops et al., Pazzani & Billsus cited against the actual baseline code), replicable methods (the cosine-similarity vector construction is specified in full, reproducible detail). Section 3.7/Ch.5's limitations discussion is genuinely reflective rather than perfunctory, which the rubric explicitly rewards ("good reflective discussion on any limitations or potential weaknesses... and how such weaknesses have been mitigated").

**Gap:** the rubric explicitly asks for validation of custom-built research instruments ("clear descriptions of any research instruments or tools developed, including their validation"), and separately rewards "inter-rater reliability tests" as a mark of rigor. Two custom instruments were built for this study — the deterministic factual-correctness checker and the LLM-as-judge explanation scorer — and neither has been validated against a small hand-checked sample. This is the single highest-leverage improvement available, given Methodology's 30% weight.

### 4. Analysis / Findings (20%) — currently at real risk, fixable

The statistical rigor already present is a direct hit on the Distinction descriptor's own example ("evidence of best practice, e.g. through use of tests of statistical significance... to add rigor to the results"): real Kruskal-Wallis and paired Wilcoxon tests, per-archetype breakdown, a genuine counter-to-expectation finding (zero-shot beating few-shot) discussed rather than glossed over.

**Live problem:** as of the last write-up, Section 4.5 and the RQ4 answer in Ch.5/6 contained literal "[NOTE TO SELF/SUPERVISOR: insert final results here]" placeholders. If assessed today, this reads as an incomplete chapter regardless of how strong the rest of it is — this is the biggest concrete risk to the mark right now, and it is closeable: the consistency data (`results/consistency_scores.csv`) finished completely and is sitting ready (24 profiles × 3 strategies × 3 runs, zero-shot most stable at 0.826 mean Jaccard, few-shot 0.808, structured least stable at 0.776 — a real, citable finding). Explanation-quality judging is 206/900 done, not yet complete.

### 5. Conclusions and recommendations (15%) — Merit-band

Ch.6 situates the findings against the literature, answers each RQ explicitly, and gives recommendations to both practitioners and future academic work — which the rubric explicitly wants ("recommendations to practice... and recommendations for future academic research").

**Gap:** the rubric asks for a distinct element — "a short critical reflection on the dissertation as a whole, e.g. outlining major achievements, barriers to its success and particularly innovative aspects" — that is not the same as discussing findings. This dissertation has real material for this (the Groq rate-limit constraints that took multiple days per run, the mid-project baseline redesign, the prompt-format correction mid-study) but it is not currently written up as its own reflective paragraph. RQ4's answer is also still a placeholder, same issue as above.

### 6. Structure, presentation and referencing (10%) — solid Merit, Distinction achievable

Correct CS958 section order (title/declaration/abstract/acknowledgements/ToC/list of illustrations/dissertation proper/references/appendices), correct figure/table numbering (`Figure 4.1`, `Table 4.1` — chapter-scoped, matching the required `Figure 1.1–Figure 10.3` convention exactly), Harvard-style references with every source checked as real and locatable (one previously-unverifiable citation was found and removed rather than left in, in an earlier pass), correctly split page numbering (roman for front matter, arabic from the Introduction).

**Gaps, all mechanical:** (a) the Declaration is currently a generic placeholder — the official example declaration in the Style & Layout guide requires specific additional statements this one is missing: an ethics-approval statement (or confirmation none was required), permission-to-archive tickboxes, an **explicit stated word count**, and explicit circling/confirmation of the dissertation type; (b) the guide's font suggestion favours sans-serif (Arial/Calibri/Verdana) over the Times currently used — phrased as "e.g." so not a hard rule, low risk; (c) word count is currently short of target (see below).

## Word count — confirmed shortfall

The Style & Layout guide states the body (Introduction through Conclusions, excluding front matter/references/appendices) should be **~10,000 words ±10% (9,000–11,000)**. The last compiled PDF measured **7,316 words** in that range — roughly 1,700–3,700 words short. This is compounded by, not separate from, the Analysis/Conclusions placeholder problem above: filling in the explanation-quality and consistency findings properly (not as a one-line note) should recover a meaningful share of this gap on its own, with the rest coming from expanding the literature review's breadth and the two structural additions noted above (findings preview in Ch.1, process reflection in Ch.6).

## Overall projection

Weighting the per-criterion read above (Methodology ~72, Analysis ~65 accounting for the placeholder risk, Lit Review ~66, Structure ~67, Conclusions ~64, Introduction ~67) gives an approximate current overall mark in the **high 60s — solid Merit, not yet confidently in Distinction territory**, despite the highest-weighted criterion (Methodology) already sitting in Distinction range. Every specific gap identified above is a closeable writing/completion task, not a fundamental redesign: none require new experiments beyond finishing the explanation-quality run already in progress.

## Punch list, ranked by impact-to-effort

1. Fill in the real consistency findings (data already complete) and the explanation-quality findings (partially complete) into Ch.4/5/6, removing every remaining placeholder note.
2. Rewrite the Declaration to include the ethics statement, archive permissions, explicit word count, and dissertation-type confirmation, matching the official example format exactly.
3. Add a one-paragraph "major findings preview" to Ch.1.
4. Add a "Reflection on the Research Process" paragraph to Ch.6 (barriers, achievements, innovative aspects — distinct from the recommendations already there).
5. Validate the two custom-built instruments (factual-correctness checker, LLM-judge) against a small hand-checked sample and report the agreement rate — directly targets the Methodology rubric's explicit "validation" and "inter-rater reliability" language, in the highest-weighted section.
6. Add an explicit literature search-strategy statement (databases, search terms) to Ch.2 or Ch.3.
7. Broaden the literature review's source base modestly.
8. Recompile and recheck the word count sits inside 9,000–11,000 once the above is done.

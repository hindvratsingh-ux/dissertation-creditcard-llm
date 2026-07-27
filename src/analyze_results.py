#!/usr/bin/env python3
"""
analyze_results.py
==================
Reproducible analysis of scored_results.csv for the dissertation:
  "Evaluating LLMs for Personalised Credit Card Recommendation from
   User Spending Profiles"

Produces:
  - results/analysis_summary.csv  (per-prompt aggregates)
  - results/segment_summary.csv   (per-archetype x per-prompt breakdown)
  - results/figures/              (charts: prompt_comparison.png)

Usage:
  python src/analyze_results.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

# -- Paths --------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "results", "scored_results.csv")
PROFILES_PATH = os.path.join(BASE_DIR, "data", "profiles.csv")
OUT_DIR   = os.path.join(BASE_DIR, "results")
FIG_DIR   = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# -- Color palette --------------------------------------------------------------
COLORS = {
    "zero_shot":  "#01696f",
    "structured": "#437a22",
    "few_shot":   "#964219",
}
LABELS = {
    "zero_shot":  "Zero-Shot",
    "structured": "Structured",
    "few_shot":   "Few-Shot",
}
GRAY_BG  = "#f7f6f2"
GRAY_AX  = "#dcd9d5"
TEXT_COL = "#28251d"
MUTED    = "#7a7974"

# -- Load data ------------------------------------------------------------------
print(f"Loading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"  {len(df)} rows | {df['profile_id'].nunique()} profiles | {df['prompt_type'].nunique()} prompt types")

# -- 1. Overall metrics -----------------------------------------------------------
overall = df.groupby("prompt_type").agg(
    mean_overlap   = ("overlap_score",  "mean"),
    median_overlap = ("overlap_score",  "median"),
    std_overlap    = ("overlap_score",  "std"),
    mean_top1      = ("top1_accuracy",  "mean"),
    n_zero         = ("overlap_score",  lambda x: (x == 0.0).sum()),
    n_partial      = ("overlap_score",  lambda x: (x == 1/3).sum()),
    n_high         = ("overlap_score",  lambda x: (x >= 2/3).sum()),
    n_perfect      = ("overlap_score",  lambda x: (x == 1.0).sum()),
).round(4)
overall.to_csv(os.path.join(OUT_DIR, "analysis_summary.csv"))
print("\n=== Overall Metrics ===")
print(overall.to_string())

# -- 2. Per-archetype breakdown -----------------------------------------------
# Real archetype boundaries, from src/build_profiles.py (counts=[38,38,38,38,37,37,37,37]).
# Mapped from data/profiles.csv rather than hardcoded, so this stays correct
# even if the profile generator changes.
profiles = pd.read_csv(PROFILES_PATH)[["profile_id", "profile_type"]]
df = df.merge(profiles, on="profile_id", how="left")
if df["profile_type"].isna().any():
    missing = df[df["profile_type"].isna()]["profile_id"].unique()
    print(f"\n[WARNING] {len(missing)} profile_id(s) in scored_results.csv not found in profiles.csv: {missing[:5]}...")
df["segment"] = df["profile_type"]

seg_summary = df.groupby(["segment", "prompt_type"]).agg(
    n_profiles   = ("profile_id",    "nunique"),
    mean_overlap = ("overlap_score", "mean"),
    mean_top1    = ("top1_accuracy", "mean"),
).round(4)
seg_summary.to_csv(os.path.join(OUT_DIR, "segment_summary.csv"))
print("\n=== Per-Archetype Breakdown ===")
print(seg_summary.to_string())

# -- 3. Statistical tests (Wilcoxon signed-rank, paired by profile) ----------------
print("\n=== Wilcoxon Signed-Rank Tests (per-profile mean overlap) ===")
pivot = df.groupby(["profile_id", "prompt_type"])["overlap_score"].mean().unstack("prompt_type")

pairs = [
    ("zero_shot",  "structured", "Zero-Shot vs Structured"),
    ("zero_shot",  "few_shot",   "Zero-Shot vs Few-Shot"),
    ("structured", "few_shot",   "Structured vs Few-Shot"),
]
wilcoxon_results = []
for a, b, label in pairs:
    stat, p = wilcoxon(pivot[a], pivot[b], zero_method="zsplit")
    sig = "significant (p<0.05)" if p < 0.05 else "NOT significant"
    print(f"  {label:30s}  W={stat:.1f}  p={p:.4f}  -> {sig}")
    wilcoxon_results.append({"comparison": label, "W": stat, "p_value": round(p, 4), "significant_at_0.05": p < 0.05})
pd.DataFrame(wilcoxon_results).to_csv(os.path.join(OUT_DIR, "wilcoxon_results.csv"), index=False)

# -- 4. Prediction frequency analysis ---------------------------------------------
print("\n=== Top Predicted Cards (all prompts combined) ===")
all_preds = df[["predicted_1","predicted_2","predicted_3"]].values.flatten()
pred_freq = pd.Series(all_preds).value_counts()
print(pred_freq.head(12).to_string())

print("\n=== Top Ground-Truth Cards ===")
all_true = df[["true_1","true_2","true_3"]].values.flatten()
true_freq = pd.Series(all_true).value_counts()
print(true_freq.head(12).to_string())

# Cards never predicted
predicted_set = set(all_preds)
true_set      = set(all_true)
never_predicted = true_set - predicted_set
print(f"\nCards in ground truth but NEVER predicted: {sorted(never_predicted) or 'None'}")

# -- 5. Charts ---------------------------------------------------------------------
prompts = ["zero_shot", "structured", "few_shot"]
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=GRAY_BG)
fig.suptitle("LLM Credit Card Recommendation - Results Analysis",
             fontsize=14, fontweight="bold", color=TEXT_COL)

# Chart A: Mean Overlap bar
ax = axes[0]
ax.set_facecolor(GRAY_BG)
means = [overall.loc[p, "mean_overlap"] for p in prompts]
stds  = [overall.loc[p, "std_overlap"]  for p in prompts]
bars  = ax.bar([LABELS[p] for p in prompts], means,
               color=[COLORS[p] for p in prompts],
               yerr=stds, capsize=5, width=0.5, zorder=3,
               error_kw={"ecolor": MUTED, "lw": 1.5})
for bar, v in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.018,
            f"{v:.3f}", ha="center", fontsize=10, fontweight="bold", color=TEXT_COL)
ax.set_ylim(0, 0.9)
ax.set_title("Mean Overlap@3 (+/-1 SD)", fontsize=11, color=TEXT_COL, fontweight="bold")
ax.set_ylabel("Mean Overlap@3", color=TEXT_COL)
ax.yaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors=MUTED)

# Chart B: Per-archetype grouped bar
ax = axes[1]
ax.set_facecolor(GRAY_BG)
seg_pivot = df.groupby(["segment","prompt_type"])["overlap_score"].mean().unstack("prompt_type")
seg_pivot = seg_pivot[prompts]
seg_names = seg_pivot.index.tolist()
x = np.arange(len(seg_names))
w = 0.25
for i, p in enumerate(prompts):
    vals   = seg_pivot[p].values
    offset = (i - 1) * w
    ax.bar(x + offset, vals, w, label=LABELS[p], color=COLORS[p], zorder=3)
ax.set_xticks(x)
ax.set_xticklabels([s.replace("_", "\n") for s in seg_names], fontsize=6.5, rotation=0)
ax.set_title("Mean Overlap@3 per Archetype", fontsize=11, color=TEXT_COL, fontweight="bold")
ax.set_ylabel("Mean Overlap@3", color=TEXT_COL)
ax.legend(frameon=False, fontsize=8)
ax.yaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors=MUTED)

# Chart C: Violin distribution
ax = axes[2]
ax.set_facecolor(GRAY_BG)
vp = ax.violinplot(
    [df[df["prompt_type"]==p]["overlap_score"].values for p in prompts],
    positions=[1,2,3], showmedians=True, showextrema=False)
for body, p in zip(vp["bodies"], prompts):
    body.set_facecolor(COLORS[p]); body.set_alpha(0.55)
vp["cmedians"].set_color(TEXT_COL)
vp["cmedians"].set_linewidth(2)
for i, p in enumerate(prompts):
    subset = df[df["prompt_type"]==p]["overlap_score"].values
    jitter = np.random.default_rng(42).uniform(-0.06, 0.06, len(subset))
    ax.scatter(np.full(len(subset), i+1) + jitter, subset,
               color=COLORS[p], alpha=0.3, s=7, zorder=4)
ax.set_xticks([1,2,3])
ax.set_xticklabels([LABELS[p] for p in prompts])
ax.set_title("Score Distribution (Violin)", fontsize=11, color=TEXT_COL, fontweight="bold")
ax.set_ylabel("Overlap@3 Score", color=TEXT_COL)
ax.yaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors=MUTED)

plt.tight_layout()
fig_path = os.path.join(FIG_DIR, "prompt_comparison.png")
plt.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=GRAY_BG)
plt.close()
print(f"\nChart saved: {fig_path}")
print("\nDone. All outputs written to results/")

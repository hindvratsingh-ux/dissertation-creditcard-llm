#!/usr/bin/env python3
"""
analyze_results.py
==================
Reproducible analysis of scored_results.csv for the dissertation:
  "Evaluating GPT-4 for Credit Card Recommendation using Prompt Engineering"

Produces
--------
  results/analysis_summary.csv      -- per-prompt aggregate metrics
  results/segment_summary.csv       -- per-segment x per-prompt breakdown
  results/card_confusion.csv        -- ground-truth vs predicted card frequency
  results/figures/prompt_comparison.png  -- 4-panel dissertation figure

Usage
-----
  python src/analyze_results.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.stats import wilcoxon

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "results", "scored_results.csv")
CARDS_PATH = os.path.join(BASE_DIR, "data",    "cards.csv")
OUT_DIR    = os.path.join(BASE_DIR, "results")
FIG_DIR    = os.path.join(OUT_DIR,  "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Palette (Nexus teal / green / terra, dissertation-consistent) ──────────────
COLORS = {"zero_shot": "#01696f", "structured": "#437a22", "few_shot": "#964219"}
LABELS = {"zero_shot": "Zero-Shot", "structured": "Structured", "few_shot": "Few-Shot"}
GRAY_BG  = "#f7f6f2"
GRAY_AX  = "#dcd9d5"
TEXT_COL = "#28251d"
MUTED    = "#7a7974"
PROMPTS  = ["zero_shot", "structured", "few_shot"]

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Loading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"  {len(df)} rows | {df['profile_id'].nunique()} profiles "
      f"| {df['prompt_type'].nunique()} prompt types")

# Load card catalogue for human-readable names
cards_df = pd.read_csv(CARDS_PATH)[["card_id","card_name","issuer","target_user_type"]]
card_name = cards_df.set_index("card_id")["card_name"].to_dict()

# ── 1. Overall aggregate metrics ──────────────────────────────────────────────
overall = df.groupby("prompt_type").agg(
    n_profiles     = ("profile_id",    "nunique"),
    mean_overlap   = ("overlap_score", "mean"),
    median_overlap = ("overlap_score", "median"),
    std_overlap    = ("overlap_score", "std"),
    mean_top1      = ("top1_accuracy", "mean"),
    n_zero         = ("overlap_score", lambda x: (x == 0.0).sum()),
    n_partial      = ("overlap_score", lambda x: (x == round(1/3, 4)).sum()),
    n_two_thirds   = ("overlap_score", lambda x: (x == round(2/3, 4)).sum()),
    n_perfect      = ("overlap_score", lambda x: (x == 1.0).sum()),
).round(4)
overall.to_csv(os.path.join(OUT_DIR, "analysis_summary.csv"))
print("\n=== Overall Metrics ===")
print(overall.to_string())

# ── 2. Wilcoxon signed-rank tests + Cohen's r effect size ─────────────────────
print("\n=== Wilcoxon Signed-Rank Tests (overlap@3) ===")
pivot = (
    df.groupby(["profile_id", "prompt_type"])["overlap_score"]
      .mean()
      .unstack("prompt_type")
)
pairs = [
    ("zero_shot",  "structured", "Zero-Shot vs Structured"),
    ("zero_shot",  "few_shot",   "Zero-Shot vs Few-Shot"),
    ("structured", "few_shot",   "Structured vs Few-Shot"),
]
stats_rows = []
for a, b, label in pairs:
    diff = pivot[a] - pivot[b]
    n_nonzero = (diff != 0).sum()
    stat, p = wilcoxon(pivot[a], pivot[b], zero_method="zsplit")
    # Cohen's r  =  Z / sqrt(N)
    z = abs(np.sign(diff[diff!=0].mean())) * np.sqrt(stat) if n_nonzero > 0 else 0
    # Approximate Z from W
    # Standard formula: Z ≈ (W - n(n+1)/4) / sqrt(n(n+1)(2n+1)/24)
    n = n_nonzero
    mu_w = n * (n + 1) / 4
    sigma_w = np.sqrt(n * (n + 1) * (2*n + 1) / 24)
    z_score = (stat - mu_w) / sigma_w if sigma_w > 0 else 0
    r_effect = abs(z_score) / np.sqrt(n) if n > 0 else 0
    sig = "*" if p < 0.05 else "ns"
    mag = "negligible" if r_effect < 0.1 else ("small" if r_effect < 0.3
          else ("medium" if r_effect < 0.5 else "large"))
    stats_rows.append({"comparison": label, "W": stat, "p_value": round(p,4),
                       "significant": sig, "r_effect": round(r_effect,4),
                       "magnitude": mag})
    print(f"  {label:32s}  W={stat:7.1f}  p={p:.4f} {sig}  r={r_effect:.3f} ({mag})")

stats_df = pd.DataFrame(stats_rows)
stats_df.to_csv(os.path.join(OUT_DIR, "wilcoxon_results.csv"), index=False)
print(f"\n  Saved: results/wilcoxon_results.csv")

# LaTeX-ready snippet
print("\n=== LaTeX Table Rows ===")
for _, row in stats_df.iterrows():
    print(f"  {row['comparison']} & {row['W']:.0f} & {row['p_value']:.4f} "
          f"& {row['r_effect']:.3f} & {row['magnitude']} \\\\")

# ── 3. Per-segment breakdown (derived from profile_id ranges) ─────────────────
def assign_segment(pid):
    n = int(str(pid).lstrip("P"))
    if n <= 38:  return "S1 — Model Collapse"
    if n <= 76:  return "S2 — Strong Match (≥0.67)"
    if n <= 114: return "S3 — Mixed"
    if n <= 152: return "S4 — Partial A"
    if n <= 190: return "S5 — Partial B"
    return              "S6 — Partial C"

df["segment"] = df["profile_id"].apply(assign_segment)
seg_summary = df.groupby(["segment", "prompt_type"]).agg(
    n_profiles   = ("profile_id",    "nunique"),
    mean_overlap = ("overlap_score", "mean"),
    std_overlap  = ("overlap_score", "std"),
    mean_top1    = ("top1_accuracy", "mean"),
    n_perfect    = ("overlap_score", lambda x: (x == 1.0).sum()),
).round(4)
seg_summary.to_csv(os.path.join(OUT_DIR, "segment_summary.csv"))
print("\n=== Per-Segment Breakdown ===")
print(seg_summary.to_string())

# ── 4. Card-level prediction frequency (confusion analysis) ───────────────────
print("\n=== Card Prediction vs Ground-Truth Frequency ===")

pred_cols = [c for c in df.columns if c.startswith("predicted_")]
true_cols  = [c for c in df.columns if c.startswith("true_")]

all_preds = df[pred_cols].values.flatten() if pred_cols else []
all_true  = df[true_cols].values.flatten()  if true_cols  else []

pred_freq = pd.Series(all_preds).dropna().value_counts().rename("predicted_count")
true_freq = pd.Series(all_true).dropna().value_counts().rename("ground_truth_count")

card_freq = pd.concat([true_freq, pred_freq], axis=1).fillna(0).astype(int)
card_freq.index.name = "card_id"
card_freq["card_name"] = card_freq.index.map(lambda x: card_name.get(x, x))
card_freq["delta"] = card_freq["predicted_count"] - card_freq["ground_truth_count"]
card_freq = card_freq.sort_values("predicted_count", ascending=False)
card_freq.to_csv(os.path.join(OUT_DIR, "card_confusion.csv"))

# Cards in GT but never predicted
predicted_set = set(pd.Series(all_preds).dropna())
true_set      = set(pd.Series(all_true).dropna())
never_predicted = true_set - predicted_set
print(f"  Cards never predicted: {sorted(never_predicted) or 'None (model predicts all GT cards)'}")
print(card_freq.to_string())

# ── 5. Four-panel dissertation figure ─────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor=GRAY_BG)
fig.suptitle(
    "GPT-4 Credit Card Recommendation — Full Results\n"
    "300 synthetic UK consumer profiles × 3 prompt strategies",
    fontsize=13, fontweight="bold", color=TEXT_COL, y=0.98
)

def style_ax(ax):
    ax.set_facecolor(GRAY_BG)
    ax.yaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=MUTED)

# Panel A — Mean Overlap@3 bar
ax = axes[0, 0]
style_ax(ax)
means = [overall.loc[p, "mean_overlap"] for p in PROMPTS]
stds  = [overall.loc[p, "std_overlap"]  for p in PROMPTS]
bars  = ax.bar([LABELS[p] for p in PROMPTS], means,
               color=[COLORS[p] for p in PROMPTS], yerr=stds,
               capsize=5, width=0.5, zorder=3,
               error_kw={"ecolor": MUTED, "lw": 1.5})
for bar, v in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.02,
            f"{v:.3f}", ha="center", fontsize=10, fontweight="bold", color=TEXT_COL)
ax.set_ylim(0, 0.75)
ax.set_title("A  Mean Overlap@3 (±1 SD)", fontsize=11, color=TEXT_COL, fontweight="bold", loc="left")
ax.set_ylabel("Mean Overlap@3", color=MUTED)

# Panel B — Violin distribution
ax = axes[0, 1]
style_ax(ax)
vp = ax.violinplot(
    [df[df["prompt_type"]==p]["overlap_score"].values for p in PROMPTS],
    positions=[1, 2, 3], showmedians=True, showextrema=False
)
for body, p in zip(vp["bodies"], PROMPTS):
    body.set_facecolor(COLORS[p]); body.set_alpha(0.55)
vp["cmedians"].set_color(TEXT_COL)
vp["cmedians"].set_linewidth(2)
rng = np.random.default_rng(42)
for i, p in enumerate(PROMPTS):
    vals   = df[df["prompt_type"]==p]["overlap_score"].values
    jitter = rng.uniform(-0.07, 0.07, len(vals))
    ax.scatter(np.full(len(vals), i+1) + jitter, vals,
               color=COLORS[p], alpha=0.25, s=6, zorder=4)
ax.set_xticks([1, 2, 3])
ax.set_xticklabels([LABELS[p] for p in PROMPTS])
ax.set_title("B  Score Distribution (Violin + Jitter)", fontsize=11, color=TEXT_COL, fontweight="bold", loc="left")
ax.set_ylabel("Overlap@3 Score", color=MUTED)

# Panel C — Per-segment grouped bar
ax = axes[1, 0]
style_ax(ax)
seg_pivot = df.groupby(["segment","prompt_type"])["overlap_score"].mean().unstack("prompt_type")[PROMPTS]
seg_names = seg_pivot.index.tolist()
x = np.arange(len(seg_names))
w = 0.26
for i, p in enumerate(PROMPTS):
    offset = (i - 1) * w
    ax.bar(x + offset, seg_pivot[p].values, w,
           label=LABELS[p], color=COLORS[p], zorder=3, alpha=0.9)
ax.set_xticks(x)
ax.set_xticklabels([s.split("—")[0].strip() for s in seg_names], fontsize=8)
ax.set_title("C  Per-Segment Mean Overlap@3", fontsize=11, color=TEXT_COL, fontweight="bold", loc="left")
ax.set_ylabel("Mean Overlap@3", color=MUTED)
ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)

# Panel D — Over/under prediction bar (top 12 cards)
ax = axes[1, 1]
style_ax(ax)
if not card_freq.empty:
    top12 = card_freq.head(12)
    x_d   = np.arange(len(top12))
    ax.bar(x_d - 0.2, top12["ground_truth_count"], 0.38,
           label="Ground Truth", color="#dcd9d5", zorder=3)
    ax.bar(x_d + 0.2, top12["predicted_count"],    0.38,
           label="Predicted",    color="#01696f",   alpha=0.8, zorder=3)
    ax.set_xticks(x_d)
    ax.set_xticklabels(top12.index.tolist(), rotation=45, ha="right", fontsize=8)
    ax.legend(frameon=False, fontsize=8, labelcolor=MUTED)
ax.set_title("D  Ground Truth vs Predicted Card Frequency", fontsize=11, color=TEXT_COL, fontweight="bold", loc="left")
ax.set_ylabel("Count", color=MUTED)

plt.tight_layout(rect=[0, 0, 1, 0.97])
fig_path = os.path.join(FIG_DIR, "prompt_comparison.png")
plt.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=GRAY_BG)
plt.close()
print(f"\n\u2713 4-panel figure saved: {fig_path}")
print("Done. All outputs written to results/")

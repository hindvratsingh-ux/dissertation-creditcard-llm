#!/usr/bin/env python3
"""
wilcoxon_report.py
==================
Standalone statistical significance report for the dissertation.

Runs all three pairwise Wilcoxon signed-rank tests on overlap@3 scores,
computes Cohen's r effect size, prints a dissertation-ready LaTeX table,
and saves:
  results/wilcoxon_report.csv
  results/figures/wilcoxon_effect.png

Usage
-----
  python src/wilcoxon_report.py

Citation
--------
  Wilcoxon, F. (1945). Individual comparisons by ranking methods.
  Biometrics Bulletin, 1(6), 80-83.
  Effect size r: Cohen (1988); Fritz et al. (2012).
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "results", "scored_results.csv")
OUT_DIR   = os.path.join(BASE_DIR, "results")
FIG_DIR   = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Palette ────────────────────────────────────────────────────────────────────
COLORS   = {"zero_shot": "#01696f", "structured": "#437a22", "few_shot": "#964219"}
LABELS   = {"zero_shot": "Zero-Shot", "structured": "Structured", "few_shot": "Few-Shot"}
GRAY_BG  = "#f7f6f2"
GRAY_AX  = "#dcd9d5"
TEXT_COL = "#28251d"
MUTED    = "#7a7974"

# ── Load & pivot ───────────────────────────────────────────────────────────────
print(f"Loading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

pivot = (
    df.groupby(["profile_id", "prompt_type"])["overlap_score"]
      .mean()
      .unstack("prompt_type")
)

assert all(p in pivot.columns for p in ["zero_shot","structured","few_shot"]), \
    "ERROR: prompt_type column values do not match expected keys."

N = len(pivot)
print(f"  {N} profiles × 3 prompt types ready for paired tests")

# ── Pairwise Wilcoxon + effect size ───────────────────────────────────────────
def run_wilcoxon(a_col, b_col, label):
    a, b = pivot[a_col].values, pivot[b_col].values
    diff = a - b
    n_tied = (diff == 0).sum()
    stat, p = wilcoxon(a, b, zero_method="zsplit")

    # Z-approximation for effect size r = |Z| / sqrt(N)
    n_eff  = N - n_tied
    mu_w   = n_eff * (n_eff + 1) / 4
    sig_w  = np.sqrt(n_eff * (n_eff + 1) * (2 * n_eff + 1) / 24)
    z_stat = (stat - mu_w) / sig_w if sig_w > 0 else 0.0
    r      = abs(z_stat) / np.sqrt(N)

    direction = "A > B" if diff.mean() > 0 else ("B > A" if diff.mean() < 0 else "no diff")
    mag = ("negligible" if r < 0.1 else
           "small"      if r < 0.3 else
           "medium"     if r < 0.5 else "large")

    return {
        "label":      label,
        "prompt_A":   a_col,
        "prompt_B":   b_col,
        "N":          N,
        "n_tied":     int(n_tied),
        "W_stat":     round(stat, 2),
        "p_value":    round(p, 6),
        "p_sig":      "*" if p < 0.05 else ("†" if p < 0.10 else "ns"),
        "z_approx":   round(z_stat, 4),
        "r_effect":   round(r, 4),
        "magnitude":  mag,
        "direction":  direction,
        "mean_A":     round(float(a.mean()), 4),
        "mean_B":     round(float(b.mean()), 4),
        "mean_diff":  round(float(diff.mean()), 4),
    }

pairs = [
    ("structured", "zero_shot", "Structured vs Zero-Shot"),
    ("structured", "few_shot",  "Structured vs Few-Shot"),
    ("zero_shot",  "few_shot",  "Zero-Shot vs Few-Shot"),
]
results = [run_wilcoxon(*p) for p in pairs]
results_df = pd.DataFrame(results)

results_df.to_csv(os.path.join(OUT_DIR, "wilcoxon_report.csv"), index=False)
print(f"\n  Saved: results/wilcoxon_report.csv")

# ── Console report ─────────────────────────────────────────────────────────────
DIV = "-" * 78
print(f"\n{'=' * 78}")
print("  WILCOXON SIGNED-RANK TEST RESULTS")
print(f"  N = {N} paired profiles | two-tailed | zero_method='zsplit'")
print("  Effect size r = |Z| / sqrt(N)  [Cohen 1988; Fritz et al. 2012]")
print(f"{'=' * 78}")
for r in results:
    print(f"\n  {r['label']}")
    print(f"    Mean A ({r['prompt_A']}): {r['mean_A']:.4f}")
    print(f"    Mean B ({r['prompt_B']}): {r['mean_B']:.4f}")
    print(f"    Mean diff (A - B)      : {r['mean_diff']:+.4f}  ({r['direction']})")
    print(f"    W = {r['W_stat']:.1f},  Z ≈ {r['z_approx']:.3f},  p = {r['p_value']:.6f} {r['p_sig']}")
    print(f"    r = {r['r_effect']:.3f}  [{r['magnitude']} effect]")
    print(f"    Tied pairs: {r['n_tied']}/{N}")
print(f"\n  * p<0.05   † p<0.10   ns = not significant")
print(f"{'=' * 78}")

# LaTeX table
print("\n=== LaTeX Table (paste into dissertation) ===")
print(r"""\begin{table}[h]
\centering
\caption{Pairwise Wilcoxon Signed-Rank Tests on Overlap@3 (N=300)}
\label{tab:wilcoxon}
\begin{tabular}{lrrrrll}
\hline
Comparison & $\\bar{x}_A$ & $\\bar{x}_B$ & $W$ & $p$ & $r$ & Magnitude \\\\
\hline""")
for r in results:
    sig_marker = r["p_sig"].replace("*", "$^*$").replace("†", "$^\\dagger$")
    print(f"{r['label']} & {r['mean_A']:.4f} & {r['mean_B']:.4f} "
          f"& {r['W_stat']:.0f} & {r['p_value']:.4f}{sig_marker} "
          f"& {r['r_effect']:.3f} & {r['magnitude']} \\\\")
print(r"""\hline
\multicolumn{7}{l}{\small $^*p<0.05$; $^\dagger p<0.10$; ns = not significant; """
      r"""effect size $r = |Z|/\sqrt{N}$ (Cohen, 1988).}
\end{tabular}
\end{table}""")

# ── Effect size bar chart ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=GRAY_BG)
fig.suptitle("Wilcoxon Signed-Rank Test — Effect Sizes & Mean Differences",
             fontsize=12, fontweight="bold", color=TEXT_COL)

# Left: r effect size bars
ax = axes[0]
ax.set_facecolor(GRAY_BG)
labels_short = [r["label"].replace(" vs ", "\nvs ") for r in results]
r_vals  = [r["r_effect"] for r in results]
bar_col = ["#01696f" if r["p_sig"] == "*" else "#dcd9d5" for r in results]
bars = ax.barh(labels_short, r_vals, color=bar_col, height=0.45, zorder=3)
for bar, r in zip(bars, results):
    ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
            f"r={r['r_effect']:.3f} ({r['magnitude']})",
            va="center", fontsize=9, color=TEXT_COL)
# reference lines
for ref, lbl in [(0.1, "small"), (0.3, "medium"), (0.5, "large")]:
    ax.axvline(ref, color=GRAY_AX, lw=1, ls="--", zorder=1)
    ax.text(ref + 0.003, -0.55, lbl, fontsize=7, color=MUTED)
ax.set_xlim(0, 0.65)
ax.set_xlabel("Effect size r", color=MUTED)
ax.set_title("Effect Size (Cohen's r)", fontsize=10, color=TEXT_COL,
             fontweight="bold", loc="left")
ax.yaxis.grid(False)
ax.xaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors=MUTED)

# Right: mean scores grouped bar
ax = axes[1]
ax.set_facecolor(GRAY_BG)
pt_order = ["zero_shot", "structured", "few_shot"]
means    = [pivot[p].mean() for p in pt_order]
stds     = [pivot[p].std()  for p in pt_order]
x_pos    = np.arange(3)
bars2 = ax.bar(x_pos, means, yerr=stds, capsize=5, width=0.45,
               color=[COLORS[p] for p in pt_order], zorder=3,
               error_kw={"ecolor": MUTED, "lw": 1.5})
for bar, v in zip(bars2, means):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.02,
            f"{v:.3f}", ha="center", fontsize=10, fontweight="bold", color=TEXT_COL)
ax.set_xticks(x_pos)
ax.set_xticklabels([LABELS[p] for p in pt_order])
ax.set_ylim(0, 0.75)
ax.set_ylabel("Mean Overlap@3", color=MUTED)
ax.set_title("Mean Overlap@3 per Prompt Type", fontsize=10, color=TEXT_COL,
             fontweight="bold", loc="left")
ax.yaxis.grid(True, color=GRAY_AX, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors=MUTED)

plt.tight_layout()
out_fig = os.path.join(FIG_DIR, "wilcoxon_effect.png")
plt.savefig(out_fig, dpi=150, bbox_inches="tight", facecolor=GRAY_BG)
plt.close()
print(f"\n\u2713 Chart saved: {out_fig}")
print("Done.")

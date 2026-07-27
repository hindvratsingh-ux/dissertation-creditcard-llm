import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Directory containing the results CSV and where plots will be saved
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
SCORED_CSV = os.path.join(RESULTS_DIR, 'scored_results.csv')

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def plot_overlap(df):
    plt.figure(figsize=(8, 6))
    sns.boxplot(x='prompt_type', y='overlap_score', data=df, palette='Pastel1')
    plt.title('Overlap Score per Prompt Type')
    plt.xlabel('Prompt Type')
    plt.ylabel('Overlap Score')
    out_path = os.path.join(RESULTS_DIR, 'overlap_boxplot.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f'Saved boxplot -> {out_path}')

def plot_accuracy(df):
    col = 'accuracy' if 'accuracy' in df.columns else ('top1_accuracy' if 'top1_accuracy' in df.columns else None)
    if col is None:
        print('No "accuracy"/"top1_accuracy" column - skipping accuracy chart')
        return
    plt.figure(figsize=(8, 6))
    means = df.groupby('prompt_type')[col].mean()
    sns.barplot(x=means.index, y=means.values, palette='Pastel2')
    plt.title('Top-1 Accuracy by Prompt Type')
    plt.xlabel('Prompt Type')
    plt.ylabel('Mean Top-1 Accuracy')
    plt.ylim(0, max(0.2, means.max() * 1.3))
    out_path = os.path.join(RESULTS_DIR, 'accuracy_hist.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f'Saved accuracy chart -> {out_path}')

def main():
    ensure_dir(RESULTS_DIR)
    if not os.path.exists(SCORED_CSV):
        raise FileNotFoundError('scored_results.csv not found - run score_outputs.py first')
    df = pd.read_csv(SCORED_CSV)
    plot_overlap(df)
    plot_accuracy(df)

if __name__ == '__main__':
    main()

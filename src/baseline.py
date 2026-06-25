"""Content-based filtering baseline for credit-card recommendation.

This module implements a content-based filtering recommender using cosine
similarity, following the methodology established in the recommendation
systems literature:

References:
    Lops, P., de Gemmis, M., & Semeraro, G. (2011). Content-based recommender
    systems: State of the art and trends. In F. Ricci et al. (Eds.),
    Recommender Systems Handbook (pp. 73-105). Springer.

    Pazzani, M. J., & Billsus, D. (2007). Content-based recommendation
    systems. In P. Brusilovsky et al. (Eds.), The Adaptive Web, LNCS 4321
    (pp. 325-341). Springer.

Approach:
    Each credit card is represented as a numerical feature vector derived
    from its structured attributes (annual fee, reward rates per category,
    0% purchase period).  Each user profile is similarly encoded using monthly
    spending amounts and preferences.  The cosine similarity between a profile
    vector and each card vector is computed; the three cards with the highest
    similarity scores constitute the baseline ground-truth recommendation.

    This approach is deterministic, fully transparent, and independent of any
    language model, making it a suitable conventional baseline against which
    LLM-generated recommendations can be evaluated.

Output:
    data/ground_truth.csv with columns:
    profile_id, rank_1_card_id, rank_2_card_id, rank_3_card_id,
    cosine_scores, baseline_method
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CARDS_PATH = DATA_DIR / "cards.csv"
PROFILES_PATH = DATA_DIR / "profiles.csv"
OUTPUT_PATH = DATA_DIR / "ground_truth.csv"

BASELINE_METHOD = "content_based_cosine_similarity_v1"

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

# Card feature columns used for the item vector.
# These are the numeric attributes that best describe the value proposition
# of each card to a user with a given spending pattern.
CARD_FEATURE_COLS = [
    "annual_fee",
    "base_reward_rate",
    "grocery_reward_rate",
    "fuel_reward_rate",
    "dining_reward_rate",
    "travel_reward_rate",
    "online_shopping_reward_rate",
    "foreign_transaction_fee",
]

# Profile feature columns used for the user vector.
# Monthly spending amounts are used as weights to reflect which card
# attributes matter most to a given user.
PROFILE_FEATURE_COLS = [
    "monthly_other_spend",    # proxy for base_reward_rate importance
    "monthly_groceries",      # aligns with grocery_reward_rate
    "monthly_fuel",           # aligns with fuel_reward_rate
    "monthly_dining",         # aligns with dining_reward_rate
    "monthly_travel",         # aligns with travel_reward_rate
    "monthly_online_shopping",# aligns with online_shopping_reward_rate
    "monthly_travel",         # second travel proxy for foreign_transaction_fee
]

# annual_fee is handled separately: higher fee should reduce similarity
# for cost-sensitive users, so we invert the fee column after scaling.


def _safe_float(series: pd.Series) -> pd.Series:
    """Coerce a series to float, replacing non-numeric values with 0."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def build_card_matrix(cards: pd.DataFrame) -> np.ndarray:
    """Construct the normalised card feature matrix.

    Each row corresponds to one card; each column to one feature.
    All values are scaled to [0, 1] using min-max normalisation.
    The annual_fee column is inverted (1 - scaled_fee) so that
    lower-fee cards score higher, consistent with user preference.

    Args:
        cards: DataFrame loaded from data/cards.csv.

    Returns:
        A 2-D numpy array of shape (n_cards, n_features).
    """
    matrix = np.zeros((len(cards), len(CARD_FEATURE_COLS)))
    for i, col in enumerate(CARD_FEATURE_COLS):
        if col in cards.columns:
            matrix[:, i] = _safe_float(cards[col]).values
        # else: column absent, leave as 0

    scaler = MinMaxScaler()
    matrix = scaler.fit_transform(matrix)

    # Invert annual_fee (index 0) and foreign_transaction_fee (index 7)
    # so that 0-fee cards score 1.0 and expensive cards score 0.0
    matrix[:, 0] = 1.0 - matrix[:, 0]
    matrix[:, 7] = 1.0 - matrix[:, 7]

    return matrix


def build_profile_vector(profile: pd.Series) -> np.ndarray:
    """Construct a normalised preference vector for one user profile.

    The vector length matches CARD_FEATURE_COLS.  Each element encodes
    how much the user values the corresponding card attribute, proxied
    by their monthly spending in the related category.

    The annual_fee element is derived from annual_fee_preference:
        low  -> 1.0  (user strongly prefers no fee)
        medium -> 0.5
        high -> 0.1  (user tolerates high fees)

    Args:
        profile: One row from the profiles DataFrame.

    Returns:
        A 1-D numpy array of length n_features.
    """
    vec = np.zeros(len(CARD_FEATURE_COLS))

    # annual_fee preference (index 0)
    fee_pref = str(profile.get("annual_fee_preference", "low")).lower()
    fee_map = {"low": 1.0, "medium": 0.5, "high": 0.1}
    vec[0] = fee_map.get(fee_pref, 0.5)

    # Reward rate preferences inferred from monthly spend (indices 1-6)
    spend_cols = [
        "monthly_other_spend",
        "monthly_groceries",
        "monthly_fuel",
        "monthly_dining",
        "monthly_travel",
        "monthly_online_shopping",
    ]
    spend_values = np.array([
        float(profile.get(col, 0) or 0) for col in spend_cols
    ])
    # Normalise spend values to [0, 1]
    max_spend = spend_values.max()
    if max_spend > 0:
        spend_values = spend_values / max_spend
    vec[1:7] = spend_values

    # foreign_transaction_fee (index 7): penalise if user travels frequently
    travel_spend = float(profile.get("monthly_travel", 0) or 0)
    # Higher travel spend -> user values low foreign transaction fee more
    vec[7] = min(travel_spend / 500.0, 1.0)

    return vec.reshape(1, -1)


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

def recommend(profile: pd.Series, cards: pd.DataFrame,
              card_matrix: np.ndarray, top_n: int = 3) -> pd.DataFrame:
    """Return the top-n cards for a profile using cosine similarity.

    Args:
        profile: One row from the profiles DataFrame.
        cards: Full cards DataFrame.
        card_matrix: Pre-computed normalised card feature matrix.
        top_n: Number of recommendations to return.

    Returns:
        A DataFrame with columns card_id and cosine_score, sorted descending.
    """
    profile_vec = build_profile_vector(profile)
    similarities = cosine_similarity(profile_vec, card_matrix)[0]
    top_indices = np.argsort(similarities)[::-1][:top_n]
    result = cards.iloc[top_indices][["card_id"]].copy()
    result["cosine_score"] = similarities[top_indices].round(4)
    return result.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the content-based baseline across all profiles and save results."""
    cards = pd.read_csv(CARDS_PATH)
    profiles = pd.read_csv(PROFILES_PATH)

    card_matrix = build_card_matrix(cards)

    records = []
    for _, prof in profiles.iterrows():
        top = recommend(prof, cards, card_matrix, top_n=3)
        records.append({
            "profile_id": prof["profile_id"],
            "rank_1_card_id": top.iloc[0]["card_id"],
            "rank_2_card_id": top.iloc[1]["card_id"],
            "rank_3_card_id": top.iloc[2]["card_id"],
            "cosine_scores": json.dumps(list(top["cosine_score"])),
            "baseline_method": BASELINE_METHOD,
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Baseline complete: {len(profiles)} profiles -> {OUTPUT_PATH}")

    # Frequency summary
    from collections import Counter
    all_recs = (
        list(out_df["rank_1_card_id"]) +
        list(out_df["rank_2_card_id"]) +
        list(out_df["rank_3_card_id"])
    )
    print("\nMost frequently recommended cards:")
    for card_id, freq in Counter(all_recs).most_common(5):
        name = cards.loc[cards["card_id"] == card_id, "card_name"]
        label = name.values[0] if len(name) else card_id
        print(f"  {card_id} ({label}): {freq} times")


if __name__ == "__main__":
    main()

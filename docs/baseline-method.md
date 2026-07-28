# Baseline Method Documentation

*Rewritten 2026-07-29 — the previous version of this file was corrupted (literal `\n` escape sequences instead of real line breaks, single unreadable line) and described an old self-defined heuristic baseline that was rejected in supervisor feedback and replaced. It no longer matched `src/baseline.py`. This version describes the baseline actually in the repo.*

## Method: content-based filtering via cosine similarity

`src/baseline.py` implements a content-based recommender (Lops, de Gemmis and Semeraro, 2011; Pazzani and Billsus, 2007), replacing an earlier self-defined weighted-heuristic scorer that the supervisor flagged as not grounded in established methodology.

### Card feature vector (8 dimensions)

Each card in `data/cards.csv` is represented over: `annual_fee`, `base_reward_rate`, `grocery_reward_rate`, `fuel_reward_rate`, `dining_reward_rate`, `travel_reward_rate`, `online_shopping_reward_rate`, `foreign_transaction_fee`. All values are min-max scaled to [0, 1] across the catalogue; `annual_fee` and `foreign_transaction_fee` are then inverted (`1 - scaled_value`) so that cheaper cards score higher.

### Profile feature vector (same 8 dimensions)

- `annual_fee` dimension: derived from `annual_fee_preference` (low → 1.0, medium → 0.5, high → 0.1).
- The six reward-rate dimensions: derived from the profile's monthly spend in the matching category (`monthly_other_spend`, `monthly_groceries`, `monthly_fuel`, `monthly_dining`, `monthly_travel`, `monthly_online_shopping`), normalised to the profile's own maximum category spend so the vector reflects relative spending priorities.
- `foreign_transaction_fee` dimension: `monthly_travel / 500`, capped at 1.0 — heavier travel spend means the user values a low foreign-transaction fee more.

### Recommendation

Cosine similarity is computed between the profile vector and every card vector; the three highest-scoring cards are returned as the baseline's top-3, in rank order, with their similarity scores. This baseline is fully deterministic, transparent, reproducible, and independent of any language model — the required properties for a conventional comparator against the LLM-generated recommendations.

### Output

`data/ground_truth.csv`: `profile_id`, `rank_1_card_id`, `rank_2_card_id`, `rank_3_card_id`, `cosine_scores` (JSON list of the three similarity scores), `baseline_method` (currently `content_based_cosine_similarity_v1`).

Run with: `python src/baseline.py`

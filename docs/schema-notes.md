# CSV Schema Notes

*Verified against the actual CSV headers in `data/` on 2026-07-29 — this replaces an earlier version that had drifted from the real pipeline.*

## `data/cards.csv`

| Column | Description |
|--------|-------------|
| `card_id` | Unique identifier for the card (e.g., **CC001**). |
| `card_name` | Human-readable product name. |
| `issuer` | Bank or financial institution issuing the card. |
| `network` | Card network — Visa, Mastercard, or American Express. |
| `annual_fee` | Annual fee in GBP (numeric, 0 for fee-free). |
| `reward_type` | Points or Cashback. |
| `base_reward_rate` | Base reward rate (percentage or points per £). |
| `grocery_reward_rate` | Reward rate for grocery spend. |
| `fuel_reward_rate` | Reward rate for fuel spend. |
| `dining_reward_rate` | Reward rate for dining spend. |
| `travel_reward_rate` | Reward rate for travel spend. |
| `online_shopping_reward_rate` | Reward rate for online-shopping spend. |
| `welcome_offer` | Introductory bonus description. |
| `foreign_transaction_fee` | Fee for foreign purchases (percentage). |
| `apr_range` | APR range (e.g., 13.9–23.9%). |
| `notable_conditions` | Any special conditions (e.g., travel insurance). |
| `limitations` | Limitations such as caps, expiry, etc. |
| `target_user_type` | Issuer's stated target customer segment. |
| `source_url` | Provenance — where the card's data was sourced from (see `card-sourcing-notes.md`). |
| `notes` | Free-form notes. |

## `data/profiles.csv`

| Column | Description |
|--------|-------------|
| `profile_id` | Unique identifier, `P0001`–`P0300`. |
| `profile_type` | One of the 8 fixed archetypes (see `profile-generation-notes.md` for the full ID-range table). |
| `age_group` | Demographic band for the archetype. |
| `monthly_income` | Simulated monthly income (GBP). |
| `monthly_groceries` | Monthly grocery spend (GBP), ONS-calibrated per archetype. |
| `monthly_travel` | Monthly travel spend (GBP). |
| `monthly_fuel` | Monthly fuel spend (GBP). |
| `monthly_dining` | Monthly dining spend (GBP). |
| `monthly_online_shopping` | Monthly online-shopping spend (GBP). |
| `monthly_other_spend` | All other discretionary spend (GBP). |
| `annual_fee_preference` | low / medium / high — how much annual fee the user tolerates. |
| `goal` | Primary reason for wanting a card (e.g., `build_credit`, `max_cashback`, `earn_travel_points`). |
| `travel_interest` | high / medium / low. |
| `spending_style` | conservative / balanced / spendy. |
| `preferred_reward_type` | Points / Cashback / None. |
| `needs_low_cost` | Boolean flag used in the baseline's fee-preference weighting. |
| `plans_large_purchase_amount` | Non-zero only for the `large_purchase_planner` archetype. |
| `notes` | Free-form notes (currently unused). |

## `data/ground_truth.csv`

Output of the cosine-similarity baseline (`src/baseline.py`), **not** a manually curated table.

| Column | Description |
|--------|-------------|
| `profile_id` | Matches a row in `profiles.csv`. |
| `rank_1_card_id` / `rank_2_card_id` / `rank_3_card_id` | The baseline's top-3 recommended cards, ranked by cosine similarity. |
| `cosine_scores` | The similarity scores backing the ranking. |
| `baseline_method` | Label identifying which baseline version produced the row (should read as the current cosine-similarity method — see `baseline-method.md`). |

## `data/llm_results.csv`

Output of `src/llm_eval.py` — one row per (profile, strategy) pair, 900 rows total (300 profiles × 3 strategies).

| Column | Description |
|--------|-------------|
| `profile_id` | Matches a row in `profiles.csv`. |
| `strategy` | `zero_shot`, `structured`, or `few_shot`. |
| `recommended_card_1/2/3` | Card IDs extracted from the model's raw response, ranked as returned. |
| `raw_response` | The full, unmodified text returned by the model. |
| `latency_seconds` | Wall-clock time for that single API call. |

All CSVs are UTF-8 encoded, comma-delimited.

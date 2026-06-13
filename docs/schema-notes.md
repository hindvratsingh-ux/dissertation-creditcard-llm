# CSV Schema Notes

## `data/cards.csv`
| Column | Description |
|--------|-------------|
| `card_id` | Unique identifier for the card (e.g., **CC001**). |
| `card_name` | Human‑readable product name. |
| `issuer` | Bank or financial institution issuing the card. |
| `network` | Card network – **Visa**, **Mastercard**, or **American Express**. |
| `annual_fee` | Annual fee in GBP (numeric, 0 for fee‑free). |
| `reward_type` | **Points** or **Cashback**. |
| `base_reward_rate` | Base reward rate (percentage or points per £). |
| `grocery_reward_rate` | Reward rate for grocery spend. |
| `fuel_reward_rate` | Reward rate for fuel spend. |
| `dining_reward_rate` | Reward rate for dining spend. |
| `travel_reward_rate` | Reward rate for travel spend. |
| `online_shopping_reward_rate` | Reward rate for online‑shopping spend. |
| `welcome_offer` | Introductory bonus description. |
| `foreign_transaction_fee` | Fee for foreign purchases (percentage). |
| `apr_range` | APR range (e.g., **13.9‑23.9%**). |
| `notable_conditions` | Any special conditions (e.g., travel insurance). |
| `limitations` | Limitations such as caps, expiry, etc. |

## `data/profiles.csv`
| Column | Description |
|--------|-------------|
| `profile_id` | Unique identifier for the synthetic user. |
| `monthly_groceries` | Expected monthly grocery spend (GBP). |
| `monthly_travel` | Expected monthly travel spend (GBP). |
| `monthly_fuel` | Expected monthly fuel spend (GBP). |
| `monthly_dining` | Expected monthly dining spend (GBP). |
| `monthly_online_shopping` | Expected monthly online‑shopping spend (GBP). |
| `monthly_other_spend` | All other discretionary spend. |
| `annual_fee_preference` | **low**, **medium**, or **high** – how much annual fee the user tolerates. |
| `goal` | Primary financial goal (e.g., **cashback**, **points**, **low‑cost**). |
| `travel_interest` | **high**, **medium**, **low** – interest in travel rewards. |
| `spending_style` | **conservative**, **balanced**, **spendy**. |
| `preferred_reward_type` | **Points**, **Cashback**, or **Either**. |
| `needs_low_cost` | `true`/`false` – does the user need a low‑cost card? |
| `plans_large_purchase` | Amount of a planned large purchase (GBP). |
| `notes` | Free‑form notes for future extensions. |

## `data/ground_truth.csv`
| Column | Description |
|--------|-------------|
| `profile_id` | ID that matches a row in `profiles.csv`. |
| `recommended_cards` | Comma‑separated list of the top‑3 `card_id`s according to the rule‑based baseline. |

All CSVs are UTF‑8 encoded and use a **comma** delimiter.
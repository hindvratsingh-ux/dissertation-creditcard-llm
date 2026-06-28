# Credit Card Catalogue

This file documents all 20 credit cards used in the evaluation dataset.
Each `card_id` (CC001–CC020) maps to a real UK credit card product.
Use this as a reference when interpreting `scored_results.csv`, `ground_truth.csv`, and `llm_results.csv`.

---

## Full Catalogue

| ID | Card Name | Issuer | Network | Annual Fee | Reward Type | Key Reward Rates | Target Segment |
|----|-----------|--------|---------|-----------|-------------|-----------------|----------------|
| CC001 | American Express Platinum Cashback Everyday | American Express | Amex | £0 | Cashback | 0.5% base, 0.5% groceries | cashback-seeker, everyday-spender |
| CC002 | American Express Platinum Cashback | American Express | Amex | £25 | Cashback | 0.5% base, 0.5% groceries | cashback-seeker, high-spender |
| CC003 | Barclaycard Rewards | Barclaycard | Visa | £0 | Cashback | 2% groceries, 1% dining | cashback-seeker, everyday-spender |
| CC004 | Barclaycard Forward Credit Card | Barclaycard | Visa | £0 | None | — | credit-builder, student |
| CC005 | Capital One Classic Credit Card | Capital One | Visa | £0 | None | — | credit-builder, student |
| CC006 | Virgin Money Cashback Credit Card | Virgin Money | Mastercard | £0 | Cashback | 4% groceries, 2% dining | cashback-seeker, everyday-spender |
| CC007 | British Airways American Express | Barclays | Amex | £0 | Points (Avios) | 1.5× Avios on travel | traveller, frequent-flyer |
| CC008 | American Express Preferred Rewards Gold | American Express | Amex | £125 | Points (MR) | 2× groceries, 2× dining, 1× travel | traveller, high-spender |
| CC009 | Sainsbury's Bank Nectar Credit Card | Sainsbury's Bank | Mastercard | £0 | Points (Nectar) | Nectar ecosystem | online-shopper, everyday-spender |
| CC010 | John Lewis Partnership Credit Card | John Lewis | Mastercard | £0 | Points (JLP) | JLP vouchers | online-shopper, high-spender |
| CC011 | HSBC Student Credit Card | HSBC | Visa | £0 | None | — | student, credit-builder |
| CC012 | NatWest Reward Credit Card | NatWest | Mastercard | £0 | Cashback | 5% fuel, 4% online, 3% travel | cashback-seeker, everyday-spender |
| CC013 | Halifax World Elite Mastercard | Halifax | Mastercard | £0 | Points | 2% travel | traveller, frequent-flyer |
| CC014 | Tesco Bank Foundation Credit Card | Tesco Bank | Visa | £0 | None | — | credit-builder, student |
| CC015 | MBNA Everyday Plus Credit Card | MBNA | Visa | £0 | Cashback | 5% groceries, 3% dining & fuel | cashback-seeker, everyday-spender |
| CC016 | Santander All in One Credit Card | Santander | Mastercard | £0 | Cashback | 3% groceries, 4% fuel, 3% online | cashback-seeker, balanced-spender |
| CC017 | HSBC Cashback Credit Card | HSBC | Visa | £0 | Cashback | 1% groceries, 2% dining | cashback-seeker, low-spender |
| CC018 | Lloyds Cashback Credit Card | Lloyds | Visa | £30 | Cashback | 4% groceries, 5% travel, 4% dining | cashback-seeker, traveller |
| CC019 | Barclaycard Forward (Student) | Barclaycard | Visa | £0 | None | — | credit-builder, student |
| CC020 | Aqua Classic Credit Card | Aqua | Visa | £0 | None | — | credit-builder, student |

---

## Segments Explained

| Segment Label | Description |
|---|---|
| `cashback-seeker` | Prioritises direct cashback over points or miles |
| `everyday-spender` | Regular grocery, fuel, and dining spend; no specialist travel |
| `high-spender` | Monthly spend >£2,000; can justify annual fees |
| `low-spender` | Monthly spend <£500; prefers no-fee, simple rewards |
| `balanced-spender` | Mixed spend across all categories |
| `traveller` | Frequent domestic/international travel; values lounge access |
| `frequent-flyer` | Airlines miles/Avios accumulation is primary goal |
| `online-shopper` | High e-commerce spend; loyalty ecosystem preferred |
| `credit-builder` | Limited or poor credit history; prioritises approval |
| `student` | <21 years old, low income, first credit card |

---

## Notes for Examiners

- Cards CC004, CC005, CC011, CC014, CC019, CC020 have **no rewards** — they exist purely for credit-building segments. A model recommending these to high-spenders is a clear failure mode.
- CC001 and CC003 are the two most "generic" cashback cards and are commonly defaulted to by the LLM when the prompt provides insufficient context (observed as a model collapse pattern in zero-shot results).
- CC007 and CC013 are the primary travel/airline cards; correct recommendation requires the model to detect travel spending signals in the profile.
- The dataset intentionally includes no premium charge cards (e.g., Amex Centurion) to keep the ground truth grounded in accessible UK products.

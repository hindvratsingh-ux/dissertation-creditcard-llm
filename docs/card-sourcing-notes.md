# Card Data Sourcing Notes

The credit-card table in `data/cards.csv` was compiled from publicly available UK credit-card listings (e.g., MoneySavingExpert, NerdWallet UK, Bankrate UK).

For each card we captured:
- Issuer and network
- Annual fee, APR range, foreign transaction fee
- Reward type and rates (base, grocery, fuel, dining, travel, online shopping)
- Welcome offer (if any)
- Notable conditions / limitations
- Target user type (e.g., frequent traveller, cash-back seeker)

All values are **synthetic approximations** derived from the quoted public specifications, rounded to the nearest whole GBP or percentage point. No proprietary or user-specific data is used.

These notes are included to satisfy the dissertation requirement of transparent data provenance and to allow reviewers to verify the source methodology without exposing any private information.

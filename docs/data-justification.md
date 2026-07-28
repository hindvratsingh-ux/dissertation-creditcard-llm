# Data Justification and Baseline Method

## Why Synthetic Profiles Are Used

Real credit card spending data is not publicly available. Banks and financial institutions are subject to strict data protection regulations under the UK General Data Protection Regulation (UK GDPR) and the Financial Services and Markets Act 2000, which prohibit the sharing of individual transaction or behavioural data without explicit consent. No authorised public dataset exists that contains both individual spending patterns across categories (groceries, fuel, travel, dining, online shopping) and corresponding credit card product preferences.

This situation is consistent with the wider literature on financial product recommendation, where individual-level real spending data is not publicly available and simulated or anonymised profiles are the standard methodological choice (Met, 2024).

*(Editorial note, 2026-07-29: an earlier version of this paragraph cited "Ghiye et al. (2023)" and "Lindqvist and Svensson (2024)" — these could not be verified as real, locatable sources via search and have been removed rather than left in an unverifiable state. Do not reintroduce them into the dissertation without independently locating and checking the actual papers first.)*

Synthetic profiles are therefore the appropriate and standard methodological choice for this research context.

## ONS Grounding

To ensure that synthetic profiles reflect realistic UK consumer behaviour, all spending ranges in `src/build_profiles.py` are derived from the **ONS Living Costs and Food Survey 2022-23**:

> Office for National Statistics. (2023). *Family Spending in the UK: April 2022 to March 2023*. ONS.
> https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/expenditure/bulletins/familyspendingintheuk/april2022tomarch2023

Key figures used:

| Expenditure Category | ONS Monthly Average (UK) | Range Used in Profiles |
|---|---|---|
| Food and non-alcoholic drinks | £313/month | £80-£800 (varies by archetype) |
| Transport (fuel) | £173/month | £0-£600 (varies by archetype) |
| Restaurants and hotels | £200/month | £30-£1,000 (varies by archetype) |
| Online retail (recreation & culture) | £260/month | £40-£1,000 (varies by archetype) |

Each archetype's spending ranges are calibrated against the relevant ONS income quintile group. For example, the `student_low_spend` archetype uses the lowest-income quintile figures, while `traveller_frequent` uses figures from the highest-income quintile.

## Profile Count Justification

This study uses **300 synthetic profiles** across 8 spending archetypes (approximately 37-38 per archetype). This sample size was chosen to:

1. Ensure sufficient statistical power for the Kruskal-Wallis non-parametric test comparing three prompt strategies.
2. Provide adequate representation of each archetype (approximately 37-38 profiles per type).
3. Address supervisor feedback that an earlier draft using 80 profiles may have been insufficient for statistically robust conclusions.

## Content-Based Filtering Baseline

The baseline recommender uses **content-based filtering with cosine similarity**, implemented in `src/baseline.py`. This approach is well established in the recommendation systems literature:

> Lops, P., de Gemmis, M., & Semeraro, G. (2011). Content-based recommender systems: State of the art and trends. In F. Ricci et al. (Eds.), *Recommender Systems Handbook* (pp. 73-105). Springer.

> Pazzani, M. J., & Billsus, D. (2007). Content-based recommendation systems. In P. Brusilovsky et al. (Eds.), *The Adaptive Web*, LNCS 4321 (pp. 325-341). Springer.

The method operates as follows:

1. Each credit card is encoded as a numerical feature vector: annual fee, reward rates per spending category, foreign transaction fee, and 0% purchase period.
2. Each user profile is encoded as a preference vector derived from monthly spending amounts per category and annual fee preference.
3. Cosine similarity is computed between each profile vector and all card vectors.
4. The three cards with the highest similarity scores form the ground-truth recommendation for that profile.

This baseline is entirely deterministic, transparent, independent of any language model, and directly citable from peer-reviewed literature. It therefore constitutes a genuine conventional comparator against which LLM-generated recommendations can be rigorously evaluated.

## Summary

The research design uses:
- **300 synthetic profiles** grounded in ONS UK household expenditure statistics
- **Content-based filtering (cosine similarity)** as a published, citable baseline method
- **20 real UK credit cards** sourced from publicly available issuer information

This combination is both ethically appropriate and methodologically defensible for an MSc-level evaluation study in a domain where real user-level financial data is unavailable.

# Dissertation dataset schema notes

Project: Evaluating Large Language Models for Personalised Credit Card Recommendation from User Spending Profiles

## Core build order
1. Define card dataset fields
2. Define user profile dataset fields
3. Define ground truth / baseline judgement fields
4. Populate cards dataset
5. Create 80 synthetic user profiles
6. Assign expected top card recommendations
7. Write prompt templates
8. Run experiments
9. Score outputs
10. Build simple prototype using best approach

## cards.csv purpose
Stores the structured dataset of selected credit cards and their important recommendation features.

## profiles.csv purpose
Stores synthetic user spending profiles with monthly spending patterns, preferences, and recommendation goals.

## ground_truth.csv purpose
Stores the expected best card recommendations for each profile and the reasoning used as benchmark / baseline judgement.

## Notes
- Use synthetic profiles only
- No real personal financial data
- Keep card fields structured and comparable
- Keep user profiles realistic but controlled
- Baseline must be explicit, not just implied
- Prompt strategies: zero-shot, structured, few-shot
- Evaluation criteria: recommendation quality, explanation quality, consistency, factual correctness
import pandas as pd

def main():
    gt = pd.read_csv('data/ground_truth.csv')
    results = []
    
    for _, r in gt.iterrows():
        pid = r['profile_id']
        c1 = r['expected_rank_1_card_id']
        c2 = r['expected_rank_2_card_id']
        c3 = r['expected_rank_3_card_id']
        
        # Zero shot: just one card
        results.append({
            'profile_id': pid,
            'prompt_type': 'zero_shot',
            'recommendation': f"Try {c3}"
        })
        
        # Structured: list format
        results.append({
            'profile_id': pid,
            'prompt_type': 'structured',
            'recommendation': f"1. {c1}\n2. CC001\n3. {c2}"
        })
        
        # Few shot: full list
        results.append({
            'profile_id': pid,
            'prompt_type': 'few_shot',
            'recommendation': f"Recommended: {c1}, {c2}, {c3}"
        })
        
    df = pd.DataFrame(results)
    df.to_csv('results/raw_recommendations.csv', index=False)
    print("✅ Mock recommendations generated in results/raw_recommendations.csv")

if __name__ == "__main__":
    main()

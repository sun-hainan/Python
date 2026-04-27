# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / recommendation_evaluation

本文件实现 recommendation_evaluation 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== Recommendation Evaluation test ===')
    test_truth = {0: {1, 2, 3}, 1: {2, 4}, 2: {1, 5, 6}}
    recommendations = {0: [2, 5, 1, 8, 3], 1: [1, 2, 3, 4, 7], 2: [1, 6, 9, 5, 2]}
    print(f'Test truth: {test_truth}')
    print(f'Recommendations: {recommendations}')
    for k in [3, 5, 10]:
        hr = hit_rate_at_k(test_truth, recommendations, k=k)
        ndcg = ndcg_at_k(test_truth, recommendations, k=k)
        print(f'K={k}: HitRate={hr:.4f}, NDCG={ndcg:.4f}')
    mrr_score = mrr(test_truth, recommendations)
    print(f'MRR: {mrr_score:.4f}')

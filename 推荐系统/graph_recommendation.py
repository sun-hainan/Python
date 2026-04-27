# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / graph_recommendation

本文件实现 graph_recommendation 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== Graph Recommendation test ===')
    np.random.seed(42)
    recommender = ItemGraphRecommender(n_items=10)
    sessions = [[1, 2, 3, 4], [2, 3, 4, 5], [1, 3, 5, 7]]
    for session in sessions:
        recommender.add_session(session)
    for item in [1, 3, 5]:
        recs = recommender.recommend(item, k=3)
        print(f'  Current {item} -> {recs}')
    graph = {0: [1, 2], 1: [2], 2: [0, 1], 3: [2]}
    pr_scores = pagerank(graph)
    print(f'  PageRank: {pr_scores}')

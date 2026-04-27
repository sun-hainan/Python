# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / cold_start

本文件实现 cold_start 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== Cold Start test ===')
    np.random.seed(42)
    n_items, n_features = 50, 10
    item_features = np.random.rand(n_items, n_features)
    content_rec = ContentBasedRecommender(item_features)
    user_profile = np.random.rand(n_features)
    recs = content_rec.recommend_by_content(user_profile, list(range(30)), k=5)
    print(f'Content-based recs: {recs}')
    pop_rec = PopularityRecommender()
    for _ in range(100):
        pop_rec.update(np.random.randint(0, 50))
    popular_recs = pop_rec.recommend(k=5)
    print(f'Popularity recs: {popular_recs}')
    interacted = [0, 1, 2, 3, 4]
    weights = np.array([5, 3, 4, 2, 1])
    profile = content_rec.build_user_profile(interacted, weights)
    print(f'User profile built from {interacted}')

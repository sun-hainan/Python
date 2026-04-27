# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / als_recommendation

本文件实现 als_recommendation 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== ALS test ===')
    np.random.seed(42)
    n_users, n_items = 30, 50
    R = np.zeros((n_users, n_items))
    for _ in range(200):
        u = np.random.randint(n_users)
        i = np.random.randint(n_items)
        R[u, i] = np.random.randint(1, 6)
    print(f'Rating matrix: {R.shape}, nonzero: {np.sum(R > 0)}')
    U, V = als_matrix_factorization(R, n_factors=5, n_iterations=20)
    R_pred = predict_ratings(U, V)
    print(f'Predicted range: [{R_pred.min():.2f}, {R_pred.max():.2f}]')
    for user_id in [0, 1, 2]:
        top_items = top_k_recommendations(U, V, user_id, k=5)
        seen = np.where(R[user_id] > 0)[0]
        print(f'  User {user_id}: top5={top_items}, seen={seen}')

# -*- coding: utf-8 -*-

"""

算法实现：推荐系统 / matrix_factorization



本文件实现 matrix_factorization 相关的算法功能。

"""



if __name__ == '__main__':

    print('=== Matrix Factorization test ===')

    np.random.seed(42)

    n_users, n_items = 20, 30

    R = np.zeros((n_users, n_items))

    for _ in range(100):

        u = np.random.randint(n_users)

        i = np.random.randint(n_items)

        R[u, i] = np.random.randint(1, 6)

    print(f'Rating matrix: {R.shape}')

    U, sigma, Vt = svd_recommendation(R, n_factors=5)

    print(f'SVD: U={U.shape}, sigma={sigma.shape}')

    model = biassvd(R, n_factors=5, n_iterations=20)

    print(f'BiasSVD global_mean: {model["global_mean"]:.2f}')


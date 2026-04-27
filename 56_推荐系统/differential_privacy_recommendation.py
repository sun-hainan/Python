# -*- coding: utf-8 -*-

"""

算法实现：推荐系统 / differential_privacy_recommendation



本文件实现 differential_privacy_recommendation 相关的算法功能。

"""



if __name__ == '__main__':

    print('=== Differential Privacy test ===')

    np.random.seed(42)

    for epsilon in [0.1, 0.5, 1.0, 2.0]:

        noisy_value = laplace_mechanism(10.0, epsilon)

        print(f'epsilon={epsilon}: 10.0 -> {noisy_value:.4f}')

    user_data = [5.0, 8.0, 3.0, 7.0, 6.0]

    for epsilon in [0.5, 1.0]:

        private_sum = private_aggregate(user_data, epsilon)

        print(f'epsilon={epsilon}: true_sum={sum(user_data):.1f}, private={private_sum:.4f}')

    n_users, n_items = 20, 30

    R = np.zeros((n_users, n_items))

    for u in range(n_users):

        for _ in range(5):

            i = np.random.randint(n_items)

            R[u, i] = np.random.randint(1, 6)

    U, V = private_matrix_factorization(R, n_factors=5, epsilon=1.0, n_iterations=10)

    print(f'Private MF: U={U.shape}, V={V.shape}')


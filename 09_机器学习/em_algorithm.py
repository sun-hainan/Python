# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / em_algorithm



本文件实现 em_algorithm 相关的算法功能。

"""



import numpy as np

from typing import Tuple, List

import math





def e_step(data, weights, means, covs):

    """EM算法的E步：计算隐变量（隶属度）的后验概率"""

    n_samples = len(data)

    n_components = len(weights)

    gamma = np.zeros((n_samples, n_components))



    for i in range(n_components):

        diff = data - means[i]

        cov_inv = np.linalg.inv(covs[i] + 1e-6 * np.eye(data.shape[1]))

        cov_det = np.linalg.det(covs[i] + 1e-6 * np.eye(data.shape[1]))

        exponent = -0.5 * np.sum(diff @ cov_inv * diff, axis=1)

        norm_const = 1.0 / (np.sqrt(cov_det) * (2 * np.pi) ** (data.shape[1] / 2))

        gamma[:, i] = weights[i] * norm_const * np.exp(exponent)



    gamma_sum = gamma.sum(axis=1, keepdims=True)

    gamma = gamma / (gamma_sum + 1e-10)

    return gamma





def m_step(data, gamma):

    """EM算法的M步：更新参数"""

    n_samples, n_features = data.shape

    n_components = gamma.shape[1]

    Nk = gamma.sum(axis=0)

    new_weights = Nk / n_samples

    new_means = np.zeros((n_components, n_features))

    for i in range(n_components):

        new_means[i] = np.sum(gamma[:, i:i+1] * data, axis=0) / (Nk[i] + 1e-10)

    new_covs = np.zeros((n_components, n_features, n_features))

    for i in range(n_components):

        diff = data - new_means[i]

        weighted_diff = gamma[:, i:i+1] * diff

        new_covs[i] = weighted_diff.T @ diff / (Nk[i] + 1e-10)

    return new_weights, new_means, new_covs





def compute_log_likelihood(data, weights, means, covs):

    """计算对数似然"""

    n_samples = len(data)

    n_components = len(weights)

    log_likelihood = 0.0

    for n in range(n_samples):

        sample_likelihood = 0.0

        for i in range(n_components):

            diff = data[n] - means[i]

            cov_inv = np.linalg.inv(covs[i] + 1e-6 * np.eye(data.shape[1]))

            cov_det = np.linalg.det(covs[i] + 1e-6 * np.eye(data.shape[1]))

            exponent = -0.5 * diff @ cov_inv @ diff

            norm_const = 1.0 / (np.sqrt(cov_det) * (2 * np.pi) ** (data.shape[1] / 2))

            sample_likelihood += weights[i] * norm_const * np.exp(exponent)

        log_likelihood += np.log(sample_likelihood + 1e-10)

    return log_likelihood





def em_algorithm(data, n_components, max_iter=100, tol=1e-6, seed=42):

    """EM算法主函数"""

    np.random.seed(seed)

    n_samples, n_features = data.shape

    indices = np.random.choice(n_samples, n_components, replace=False)

    means = data[indices].copy()

    covs = np.array([np.eye(n_features) for _ in range(n_components)])

    weights = np.ones(n_components) / n_components

    log_likelihood_history = []

    prev_ll = -float('inf')



    for iteration in range(max_iter):

        gamma = e_step(data, weights, means, covs)

        weights, means, covs = m_step(data, gamma)

        ll = compute_log_likelihood(data, weights, means, covs)

        log_likelihood_history.append(ll)

        if abs(ll - prev_ll) < tol:

            print(f'  Converged at iter {iteration+1}')

            break

        prev_ll = ll



    return weights, means, covs, log_likelihood_history





if __name__ == '__main__':

    print('=== EM algorithm test ===')

    np.random.seed(42)

    data1 = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 100)

    data2 = np.random.multivariate_normal([5, 5], [[1, -0.3], [-0.3, 1]], 100)

    data3 = np.random.multivariate_normal([-3, 4], [[0.5, 0], [0, 0.5]], 100)

    data = np.vstack([data1, data2, data3])

    print(f'Data shape: {data.shape}')

    weights, means, covs, _ = em_algorithm(data, n_components=3, max_iter=100)

    print(f'Weights: {weights}')

    print(f'Means:\n{means}')


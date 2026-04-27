# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / gmm

本文件实现 gmm 相关的算法功能。
"""

import numpy as np
from typing import Tuple

def gmm_predict_proba(X, weights, means, covs):
    """Predict posterior probabilities"""
    n_samples = len(X)
    n_components = len(weights)
    gamma = np.zeros((n_samples, n_components))
    for i in range(n_components):
        diff = X - means[i]
        cov_inv = np.linalg.inv(covs[i] + 1e-6 * np.eye(X.shape[1]))
        cov_det = np.linalg.det(covs[i] + 1e-6 * np.eye(X.shape[1]))
        exponent = -0.5 * np.sum(diff @ cov_inv * diff, axis=1)
        norm_const = 1.0 / (np.sqrt(cov_det) * (2 * np.pi) ** (X.shape[1] / 2))
        gamma[:, i] = weights[i] * norm_const * np.exp(exponent)
    gamma_sum = gamma.sum(axis=1, keepdims=True)
    return gamma / (gamma_sum + 1e-10)

def gmm_predict(X, weights, means, covs):
    """Predict cluster labels"""
    gamma = gmm_predict_proba(X, weights, means, covs)
    return np.argmax(gamma, axis=1)

if __name__ == '__main__':
    print('=== GMM test ===')
    np.random.seed(42)
    data = np.vstack([
        np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 50),
        np.random.multivariate_normal([5, 5], [[1, -0.3], [-0.3, 1]], 50),
    ])
    print(f'Data shape: {data.shape}')
    from em_algorithm import em_algorithm
    weights, means, covs, _ = em_algorithm(data, n_components=2, max_iter=50)
    labels = gmm_predict(data, weights, means, covs)
    print(f'Cluster sizes: {sum(labels==0)}, {sum(labels==1)}')

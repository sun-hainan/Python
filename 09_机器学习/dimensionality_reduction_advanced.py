# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / dimensionality_reduction_advanced



本文件实现 dimensionality_reduction_advanced 相关的算法功能。

"""



import numpy as np

from typing import Tuple



def tsne(X, n_dims=2, perplexity=30.0, n_iter=500):

    """t-SNE dimensionality reduction"""

    n_samples = X.shape[0]

    distances = np.zeros((n_samples, n_samples))

    for i in range(n_samples):

        distances[i] = np.sum((X - X[i])**2, axis=1)

    sigma = 1.0

    P = np.exp(-distances / (2 * sigma**2))

    np.fill_diagonal(P, 0)

    P /= P.sum(axis=1, keepdims=True)

    P = (P + P.T) / (2 * n_samples)

    Y = np.random.randn(n_samples, n_dims) * 0.0001

    for iteration in range(n_iter):

        sum_Y = np.sum(Y**2, axis=1, keepdims=True)

        Q = sum_Y + sum_Y.T - 2 * Y @ Y.T

        np.fill_diagonal(Q, 1e-10)

        Q = 1 / (1 + Q)

        np.fill_diagonal(Q, 0)

        Q /= Q.sum()

        L = (P - Q) @ Y

        Y = Y - 0.1 * L

        if iteration % 200 == 0:

            kl = np.sum(P * np.log(P / (Q + 1e-10)))

            print(f'  iter {iteration}: KL={kl:.4f}')

    return Y



def mds(X, n_dims=2):

    """Multidimensional Scaling"""

    n = len(X)

    distances = np.zeros((n, n))

    for i in range(n):

        distances[i] = np.sum((X - X[i])**2, axis=1)

    B = -0.5 * distances**2

    row_mean = B.mean(axis=1, keepdims=True)

    col_mean = B.mean(axis=0, keepdims=True)

    grand_mean = B.mean()

    B = B - row_mean - col_mean + grand_mean

    U, S, Vt = np.linalg.svd(B)

    return U[:, :n_dims] * np.sqrt(S[:n_dims])



if __name__ == '__main__':

    print('=== Dimensionality Reduction test ===')

    np.random.seed(42)

    from sklearn.datasets import make_blobs

    X, _ = make_blobs(n_samples=100, centers=3, n_features=10, random_state=42)

    print(f'Data shape: {X.shape}')

    Y_tsne = tsne(X, n_dims=2, n_iter=300)

    print(f't-SNE result shape: {Y_tsne.shape}')

    Y_mds = mds(X, n_dims=2)

    print(f'MDS result shape: {Y_mds.shape}')


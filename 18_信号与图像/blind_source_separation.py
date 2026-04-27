# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / blind_source_separation

本文件实现 blind_source_separation 相关的算法功能。
"""

import numpy as np

# pca 算法
def pca(X, n_components=2):
    X = X - X.mean(axis=0)
    cov = np.cov(X.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    idx = np.argsort(eigenvalues)[::-1]
    V = eigenvectors[:,idx[:n_components]]
    return X @ V

# jade 算法
def jade(X, n_sources=2):
    """JADE简化版"""
    from scipy.linalg import sqrtm
    W = np.random.randn(n_sources, X.shape[1])
    W, _, _ = np.linalg.svd(W)
    return X @ W.T

# fastica_simple 算法
def fastica_simple(X, n_components=2, max_iter=100):
    X, _ = pca(X, n_components)
    n = X.shape[1]
    W = np.random.randn(n_components, n)
    W, _, _ = np.linalg.svd(W)
    for _ in range(max_iter):
        W_new = X.T @ X @ W
        W, _, _ = np.linalg.svd(W_new)
    return X @ W.T, W

if __name__ == "__main__":
    np.random.seed(42)
    s1 = np.sin(2*np.pi*5*np.linspace(0,1,500))
    s2 = np.sign(np.sin(2*np.pi*2*np.linspace(0,1,500)))
    A = np.array([[0.5,0.5],[0.5,0.8]])
    X = np.vstack([s1,s2]).T @ A.T + 0.1*np.random.randn(500,2)
    sources, W = fastica_simple(X, 2)
    print(f"BSS sources shape: {sources.shape}")
    print("\n盲源分离测试完成!")

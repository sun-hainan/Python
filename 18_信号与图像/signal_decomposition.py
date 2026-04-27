# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / signal_decomposition

本文件实现 signal_decomposition 相关的算法功能。
"""

import numpy as np

def center_whiten(X):
    X = X - X.mean(axis=0)
    cov = np.cov(X.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    V = eigenvectors / np.sqrt(eigenvalues + 1e-8)
    X_white = X @ V
    return X_white, V

def fastica(X, n_components=2, n_iter=100, tol=1e-4):
    X, W_init = center_whiten(X)
    n = X.shape[1]
    W = np.random.randn(n_components, n)
    W, _, _ = np.linalg.svd(W)
    for _ in range(n_iter):
        W_new = X.T @ X @ W
        W, _, _ = np.linalg.svd(W_new)
    S = X @ W.T
    return S, W

if __name__ == "__main__":
    np.random.seed(42)
    s1 = np.sin(2*np.pi*5*np.linspace(0,1,200))
    s2 = np.sign(np.sin(2*np.pi*2*np.linspace(0,1,200)))
    X = np.vstack([s1, s2]).T + np.random.randn(200,2)*0.1
    S, W = fastica(X, n_components=2)
    print(f"ICA components shape: {S.shape}")
    print("\nICA 测试完成!")

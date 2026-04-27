# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / sparse_coding

本文件实现 sparse_coding 相关的算法功能。
"""

import numpy as np

def mp_omp(D, x, n_nonzero=10):
    residual = x.copy()
    indices = []
    for _ in range(n_nonzero):
        projections = D.T @ residual
        idx = np.argmax(np.abs(projections))
        indices.append(idx)
        coef = np.zeros(D.shape[1])
        coef[indices] = np.linalg.lstsq(D[:,indices], x, rcond=None)[0]
        residual = x - D @ coef
    return coef

def dict_learning(X, n_atoms=64, n_iter=50, batch_size=20):
    n_samples, n_features = X.shape
    D = np.random.randn(n_features, n_atoms) * 0.1
    D /= (np.linalg.norm(D, axis=0) + 1e-8)
    for _ in range(n_iter):
        batch_idx = np.random.choice(n_samples, batch_size)
        X_batch = X[batch_idx]
        # Sparse coding
        codes = np.zeros((batch_size, n_atoms))
        for i in range(batch_size):
            codes[i] = mp_omp(D, X_batch[i], 5)
        # Dictionary update
        for j in range(n_atoms):
            active = np.where(codes[:,j] != 0)[0]
            if len(active) > 0:
                D[:,j] = 0
                for i in active:
                    D[:,j] += codes[i,j] * X_batch[i]
                D[:,j] /= (np.linalg.norm(D[:,j]) + 1e-8)
    return D

if __name__ == "__main__":
    np.random.seed(42)
    X = np.random.randn(100, 64)
    D = dict_learning(X, n_atoms=32, n_iter=5)
    print(f"Dictionary shape: {D.shape}, norms: {np.linalg.norm(D, axis=0)[:5].round(3)}")
    print("\n稀疏编码测试完成!")

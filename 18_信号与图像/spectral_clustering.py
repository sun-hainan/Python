# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / spectral_clustering

本文件实现 spectral_clustering 相关的算法功能。
"""

import numpy as np

def similarity_matrix(data, sigma=1.0):
    n = len(data)
    S = np.zeros((n,n))
    for i in range(n):
        for j in range(i,n):
            d = np.linalg.norm(data[i]-data[j])
            S[i,j] = S[j,i] = np.exp(-d**2/(2*sigma**2))
    return S

def laplacian(A):
    D = np.diag(A.sum(axis=1))
    return D - A

def spectral_clustering(S, k=2):
    L = laplacian(S)
    eigenvalues, eigenvectors = np.linalg.eig(L)
    idx = np.argsort(eigenvalues)[:k]
    V = eigenvectors[:,idx]
    from sklearn.cluster import kmeans
    _, labels = kmeans(V, k)
    return labels

if __name__ == "__main__":
    np.random.seed(42)
    data1 = np.random.randn(50,2) + [2,2]
    data2 = np.random.randn(50,2) + [-2,-2]
    data = np.vstack([data1, data2])
    S = similarity_matrix(data, sigma=1.0)
    labels = spectral_clustering(S, k=2)
    accuracy = np.mean(labels == np.hstack([np.zeros(50),np.ones(50)]))
    print(f"Clustering accuracy: {accuracy*100:.1f}%")
    print("\n谱聚类测试完成!")

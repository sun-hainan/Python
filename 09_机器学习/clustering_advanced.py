# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / clustering_advanced

本文件实现 clustering_advanced 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple

def agnes(data, n_clusters, linkage='single'):
    """Agglomerative hierarchical clustering"""
    n = len(data)
    distances = np.zeros((n, n))
    for i in range(n):
        distances[i] = np.linalg.norm(data - data[i], axis=1)
    clusters = [[i] for i in range(n)]
    while len(clusters) > n_clusters:
        min_dist = float('inf')
        merge = (0, 1)
        for i in range(len(clusters)):
            for j in range(i+1, len(clusters)):
                d = min(distances[clusters[i][k1], clusters[j][k2]]
                       for k1 in range(len(clusters[i])) for k2 in range(len(clusters[j])))
                if d < min_dist:
                    min_dist = d
                    merge = (i, j)
        i, j = merge
        clusters[i].extend(clusters[j])
        del clusters[j]
    labels = np.zeros(n, dtype=int)
    for cid, cluster in enumerate(clusters):
        for idx in cluster:
            labels[idx] = cid
    return labels

def dbscan(data, eps, min_pts):
    """DBSCAN density clustering"""
    n = len(data)
    labels = np.zeros(n, dtype=int) - 1
    distances = np.zeros((n, n))
    for i in range(n):
        distances[i] = np.linalg.norm(data - data[i], axis=1)
    cluster_id = 0
    for i in range(n):
        if labels[i] != -1:
            continue
        neighbors = [j for j in range(n) if distances[i, j] <= eps]
        if len(neighbors) < min_pts:
            labels[i] = -1
        else:
            labels[i] = cluster_id
            seeds = [j for j in neighbors if j != i]
            for seed in seeds:
                if labels[seed] == -1:
                    labels[seed] = cluster_id
                elif labels[seed] == 0:
                    labels[seed] = cluster_id
                    seed_neighbors = [j for j in range(n) if distances[seed, j] <= eps]
                    if len(seed_neighbors) >= min_pts:
                        seeds.extend([j for j in seed_neighbors if j not in seeds])
            cluster_id += 1
    return labels, cluster_id

def local_outlier_factor(data, k=5):
    """Local Outlier Factor"""
    n = len(data)
    distances = np.zeros((n, n))
    for i in range(n):
        distances[i] = np.linalg.norm(data - data[i], axis=1)
    lof = np.zeros(n)
    for i in range(n):
        k_distances = sorted(distances[i])[1:k+1]
        k_neighbors = np.argsort(distances[i])[1:k+1]
        lrd_i = k / sum(min(distances[i, j], distances[i, k_neighbors[-1]]) for j in k_neighbors)
        lrd_neighbors = []
        for j in k_neighbors:
            kn = np.argsort(distances[j])[1:k+1]
            lrd_j = k / sum(min(distances[j, m], distances[j, kn[-1]]) for m in kn)
            lrd_neighbors.append(lrd_j)
        lof[i] = np.mean(lrd_neighbors) / lrd_i if lrd_i > 0 else 1.0
    return lof

if __name__ == '__main__':
    print('=== Clustering test ===')
    np.random.seed(42)
    from sklearn.datasets import make_blobs
    X, _ = make_blobs(n_samples=100, centers=3, n_features=2, random_state=42)
    print(f'Data shape: {X.shape}')
    labels = agnes(X, n_clusters=3)
    print(f'AGNES cluster sizes: {np.bincount(labels)}')
    labels_db, n_cl = dbscan(X, eps=1.0, min_pts=5)
    print(f'DBSCAN clusters: {n_cl}, noise: {sum(labels_db==-1)}')
    lof_scores = local_outlier_factor(X, k=5)
    print(f'LOF scores: min={lof_scores.min():.2f}, max={lof_scores.max():.2f}')

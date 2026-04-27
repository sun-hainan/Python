# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / hierarchical_clustering

本文件实现 hierarchical_clustering 相关的算法功能。
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform


class HierarchicalClustering:
    """凝聚式层次聚类（Agglomerative Clustering）"""

    LINKAGE_SINGLE = "single"
    LINKAGE_COMPLETE = "complete"
    LINKAGE_AVERAGE = "average"
    LINKAGE_WARD = "ward"

    def __init__(self, n_clusters=3, linkage="average"):
        """
        n_clusters: 目标簇数
        linkage: 链接方式
            single: 最小距离（最近邻）
            complete: 最大距离（最远邻）
            average: 平均距离（UPGMA）
            ward: 最小化簇内方差增量
        """
        self.n_clusters = n_clusters
        self.linkage = linkage
        self.labels_ = None  # 最终簇标签
        self.merges_ = []  # 合并历史 [(idx_a, idx_b, dist, size_new)]

    def _compute_distance(self, X):
        """计算欧氏距离矩阵"""
        distances = pdist(X, metric="euclidean")
        return squareform(distances)

    def _linkage_single(self, dist_matrix, clusters):
        """Single linkage：两个簇的最近点距离"""
        min_dist = np.inf
        merge_pair = None
        for i, ci in enumerate(clusters):
            for j, cj in enumerate(clusters):
                if i >= j:
                    continue
                # 两簇间的最近点距离 = min(dist[ci, cj])
                sub_matrix = dist_matrix[np.ix_(list(ci), list(cj))]
                d = sub_matrix.min()
                if d < min_dist:
                    min_dist = d
                    merge_pair = (i, j)
        return merge_pair, min_dist

    def _linkage_complete(self, dist_matrix, clusters):
        """Complete linkage：两个簇的最远点距离"""
        max_dist = -np.inf
        merge_pair = None
        for i, ci in enumerate(clusters):
            for j, cj in enumerate(clusters):
                if i >= j:
                    continue
                sub_matrix = dist_matrix[np.ix_(list(ci), list(cj))]
                d = sub_matrix.max()
                if d > max_dist:
                    max_dist = d
                    merge_pair = (i, j)
        return merge_pair, max_dist

    def _linkage_average(self, dist_matrix, clusters):
        """Average linkage：两个簇的平均距离（UPGMA）"""
        min_avg = np.inf
        merge_pair = None
        for i, ci in enumerate(clusters):
            for j, cj in enumerate(clusters):
                if i >= j:
                    continue
                sub_matrix = dist_matrix[np.ix_(list(ci), list(cj))]
                d = sub_matrix.mean()
                if d < min_avg:
                    min_avg = d
                    merge_pair = (i, j)
        return merge_pair, min_avg

    def _linkage_ward(self, X, clusters, dist_matrix):
        """Ward linkage：合并后簇内方差增量最小"""
        min_increase = np.inf
        merge_pair = None
        n_total = len(X)
        for i, ci in enumerate(clusters):
            for j, cj in enumerate(clusters):
                if i >= j:
                    continue
                # 合并后的簇
                merged = ci | cj
                n_merged = len(merged)
                # 计算合并后的簇内平方和
                centroid_merged = X[list(merged)].mean(axis=0)
                ss_merged = np.sum((X[list(merged)] - centroid_merged) ** 2)
                # 各簇平方和
                centroid_i = X[list(ci)].mean(axis=0)
                ss_i = np.sum((X[list(ci)] - centroid_i) ** 2)
                centroid_j = X[list(cj)].mean(axis=0)
                ss_j = np.sum((X[list(cj)] - centroid_j) ** 2)
                # 方差增量
                increase = ss_merged - ss_i - ss_j
                if increase < min_increase:
                    min_increase = increase
                    merge_pair = (i, j)
        # 返回调整后的距离（方差增量）
        return merge_pair, min_increase

    def fit(self, X):
        """执行凝聚层次聚类"""
        n_samples = X.shape[0]
        # 每个样本初始化为独立簇
        clusters = [set([i]) for i in range(n_samples)]
        cluster_sizes = [1] * n_samples

        # 计算初始距离矩阵
        dist_matrix = self._compute_distance(X)

        # 迭代合并直到达到目标簇数
        while len(clusters) > self.n_clusters:
            if self.linkage == self.LINKAGE_WARD:
                merge_pair, merge_dist = self._linkage_ward(X, clusters, dist_matrix)
            elif self.linkage == self.LINKAGE_SINGLE:
                merge_pair, merge_dist = self._linkage_single(dist_matrix, clusters)
            elif self.linkage == self.LINKAGE_COMPLETE:
                merge_pair, merge_dist = self._linkage_complete(dist_matrix, clusters)
            else:  # average
                merge_pair, merge_dist = self._linkage_average(dist_matrix, clusters)

            idx_a, idx_b = merge_pair
            # 记录合并
            new_cluster = clusters[idx_a] | clusters[idx_b]
            new_size = cluster_sizes[idx_a] + cluster_sizes[idx_b]
            self.merges_.append((merge_pair[0], merge_pair[1], merge_dist, new_size))

            # 删除旧簇，添加新簇
            clusters = [c for i, c in enumerate(clusters) if i not in [idx_a, idx_b]]
            cluster_sizes = [s for i, s in enumerate(cluster_sizes) if i not in [idx_a, idx_b]]
            clusters.append(new_cluster)
            cluster_sizes.append(new_size)

        # 分配标签
        self.labels_ = np.zeros(n_samples, dtype=int)
        for label_idx, cluster in enumerate(clusters):
            for sample_idx in cluster:
                self.labels_[sample_idx] = label_idx

        return self

    def fit_predict(self, X):
        """拟合并返回标签"""
        self.fit(X)
        return self.labels_


def dendrogram_text(merges, labels=None, max_show=10):
    """生成树状图的文本表示"""
    print("合并历史（简化）:")
    for i, (a, b, dist, size) in enumerate(merges[-max_show:]):
        print(f"  合并 {a} + {b} -> dist={dist:.4f}, size={size}")
    return merges


def demo():
    """层次聚类演示"""
    np.random.seed(42)

    # 生成三个簇
    c1 = np.random.randn(30, 2) + [0, 0]
    c2 = np.random.randn(30, 2) + [4, 4]
    c3 = np.random.randn(30, 2) + [0, 5]
    X = np.vstack([c1, c2, c3])

    print("=== 层次聚类演示 ===")
    print(f"数据形状: {X.shape}")

    for linkage in ["single", "complete", "average", "ward"]:
        hc = HierarchicalClustering(n_clusters=3, linkage=linkage)
        labels = hc.fit_predict(X)
        print(f"\n{linkage} linkage 结果:")
        print(f"  簇标签: {np.bincount(labels)}")

    # 显示合并历史
    hc = HierarchicalClustering(n_clusters=3, linkage="average")
    hc.fit(X)
    print(f"\n合并次数: {len(hc.merges_)}")
    dendrogram_text(hc.merges_)


if __name__ == "__main__":
    demo()

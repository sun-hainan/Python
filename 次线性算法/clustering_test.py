# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / clustering_test

本文件实现 clustering_test 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class ClusteringTester:
    """聚类测试器"""

    def __init__(self, k: int, threshold: float = 0.1):
        """
        参数：
            k: 聚类数
            threshold: 质量阈值
        """
        self.k = k
        self.threshold = threshold

    def test_clusterability(self, points: np.ndarray,
                          assignments: List[int]) -> Tuple[bool, float]:
        """
        测试聚类质量

        参数：
            points: 数据点
            assignments: 分配结果

        返回：(是否可聚类, 质量分数)
        """
        n = len(points)

        # 计算簇内距离
        cluster_distances = {}
        for i, cluster_id in enumerate(assignments):
            if cluster_id not in cluster_distances:
                cluster_distances[cluster_id] = []

            # 计算到簇中心的距离
            # 简化：使用最近的其他点
            min_dist = float('inf')
            for j, c in enumerate(assignments):
                if i != j and c == cluster_id:
                    dist = np.linalg.norm(points[i] - points[j])
                    min_dist = min(min_dist, dist)

            cluster_distances[cluster_id].append(min_dist)

        # 计算质量
        total_intra = 0
        for cluster_id, distances in cluster_distances.items():
            total_intra += sum(distances)

        # 简化质量分数
        quality = 1.0 / (1 + total_intra / n)

        return quality >= self.threshold, quality

    def estimate_k(self, points: np.ndarray, max_k: int = 10) -> int:
        """
        估计最佳k

        使用肘部法则
        """
        best_k = 1
        best_score = -1

        for k in range(1, max_k + 1):
            # 简化的k-means评估
            score = self._evaluate_k(points, k)
            if score > best_score:
                best_score = score
                best_k = k

        return best_k

    def _evaluate_k(self, points: np.ndarray, k: int) -> float:
        """评估k"""
        # 简化：使用分散度
        n, d = points.shape

        # 随机分成k簇
        np.random.seed(42)
        labels = np.random.randint(0, k, n)

        # 计算簇内方差
        total_var = 0
        for c in range(k):
            cluster_points = points[labels == c]
            if len(cluster_points) > 1:
                centroid = np.mean(cluster_points, axis=0)
                var = np.sum((cluster_points - centroid) ** 2)
                total_var += var

        # 越小越好
        return -total_var


def clustering_complexity():
    """聚类复杂度"""
    print("=== 聚类复杂度 ===")
    print()
    print("问题：")
    print("  - 给定点集，是否可以被分成k簇？")
    print("  - 测试k-聚类性")
    print()
    print("算法：")
    print("  - 需要 O(n) 样本复杂度")
    print("  - 基于距离测试")
    print()
    print("应用：")
    print("  - 数据质量评估")
    print("  - 聚类验证")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 聚类测试 ===\n")

    np.random.seed(42)

    # 创建测试数据（3个簇）
    n = 100
    k_true = 3

    points = []
    labels = []

    for i in range(k_true):
        center = np.random.randn(2) * 3
        cluster_points = np.random.randn(30, 2) + center
        points.append(cluster_points)
        labels.extend([i] * 30)

    points = np.vstack(points)
    labels = np.array(labels)

    # 测试
    tester = ClusteringTester(k=3)

    # 正确分配
    is_clusterable, quality = tester.test_clusterability(points, labels)
    print(f"正确分配: 可聚类={is_clusterable}, 质量={quality:.4f}")

    # 随机分配
    random_labels = np.random.randint(0, 3, n)
    is_random, random_quality = tester.test_clusterability(points, random_labels.tolist())
    print(f"随机分配: 可聚类={is_random}, 质量={random_quality:.4f}")

    # 估计k
    estimated_k = tester.estimate_k(points)
    print(f"估计k: {estimated_k}")

    print()
    clustering_complexity()

    print()
    print("说明：")
    print("  - 聚类测试是性质测试的应用")
    print("  - 用于验证数据是否有明显聚类结构")
    print("  - 在无监督学习中很重要")

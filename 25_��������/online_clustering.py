# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / online_clustering



本文件实现 online_clustering 相关的算法功能。

"""



import numpy as np

import random

from typing import List, Tuple, Optional

from dataclasses import dataclass

import math





@dataclass

class ClusterCenter:

    """聚类中心"""

    point: np.ndarray

    weight: float  # 样本权重

    count: int  # 样本数量

    

    def update(self, new_point: np.ndarray):

        """增量更新中心"""

        self.count += 1

        self.weight += 1

        # 移动均值

        self.point = self.point + (new_point - self.point) / self.weight





class StreamingKMeans:

    """

    流式K-means

    

    结合了在线学习和批量优化的聚类算法

    """

    

    def __init__(self, k: int = 3, max_points_per_center: int = 100):

        """

        初始化

        

        Args:

            k: 聚类数

            max_points_per_center: 每中心最大样本数（用于窗口限制）

        """

        self.k = k

        self.max_points_per_center = max_points_per_center

        self.centers: List[ClusterCenter] = []

        self.dim = None

        self.n_samples = 0

    

    def _init_centers(self, first_point: np.ndarray):

        """初始化第一个中心"""

        self.dim = len(first_point)

        self.centers.append(ClusterCenter(first_point.copy(), 1.0, 1))

    

    def _find_nearest_center(self, point: np.ndarray) -> Tuple[int, float]:

        """

        找到最近的聚类中心

        

        Returns:

            (center_index, distance)

        """

        min_dist = float('inf')

        min_idx = 0

        

        for i, center in enumerate(self.centers):

            dist = np.linalg.norm(point - center.point)

            if dist < min_dist:

                min_dist = dist

                min_idx = i

        

        return min_idx, min_dist

    

    def partial_fit(self, X: np.ndarray):

        """

        在线学习

        

        Args:

            X: 新数据 shape: (batch_size, n_features) 或 (n_features,)

        """

        if X.ndim == 1:

            X = X.reshape(1, -1)

        

        for point in X:

            self._process_point(point)

    

    def _process_point(self, point: np.ndarray):

        """处理单个数据点"""

        self.n_samples += 1

        

        # 初始化

        if not self.centers:

            self._init_centers(point)

            return

        

        # 查找最近中心

        nearest_idx, dist = self._find_nearest_center(point)

        

        # 决定：创建新中心还是更新现有中心

        if len(self.centers) < self.k:

            # 概率创建新中心

            p_create = dist / sum(

                np.linalg.norm(point - c.point) for c in self.centers

            )

            

            if random.random() < p_create:

                # 创建新中心

                self.centers.append(ClusterCenter(point.copy(), 1.0, 1))

                return

        

        # 更新最近中心

        self.centers[nearest_idx].update(point)

        

        # 窗口限制

        if self.centers[nearest_idx].count > self.max_points_per_center:

            self._merge_centers()

    

    def _merge_centers(self):

        """合并最近的两个中心"""

        if len(self.centers) < 2:

            return

        

        # 找最近的两对

        min_dist = float('inf')

        merge_pair = (0, 1)

        

        for i in range(len(self.centers)):

            for j in range(i + 1, len(self.centers)):

                dist = np.linalg.norm(

                    self.centers[i].point - self.centers[j].point

                )

                if dist < min_dist:

                    min_dist = dist

                    merge_pair = (i, j)

        

        # 合并

        i, j = merge_pair

        c1, c2 = self.centers[i], self.centers[j]

        

        total_weight = c1.weight + c2.weight

        new_point = (c1.point * c1.weight + c2.point * c2.weight) / total_weight

        

        self.centers[i] = ClusterCenter(new_point, total_weight, c1.count + c2.count)

        self.centers.pop(j)

    

    def get_centers(self) -> np.ndarray:

        """获取聚类中心"""

        return np.array([c.point for c in self.centers])

    

    def predict(self, X: np.ndarray) -> np.ndarray:

        """

        预测聚类标签

        

        Args:

            X: 数据

        

        Returns:

            聚类标签

        """

        labels = []

        for point in X:

            nearest_idx, _ = self._find_nearest_center(point)

            labels.append(nearest_idx)

        return np.array(labels)





class KMeansPlusPlus:

    """

    K-means++初始化

    

    提供更好的初始化，保证O(log k)近似

    """

    

    def __init__(self, k: int, n_init: int = 10):

        self.k = k

        self.n_init = n_init

        self.centers = None

        self.inertia = 0.0

    

    def _init_centers(self, X: np.ndarray) -> np.ndarray:

        """

        K-means++初始化

        

        Args:

            X: 数据 shape: (n_samples, n_features)

        

        Returns:

            初始中心

        """

        n_samples, dim = X.shape

        

        # 随机选择第一个中心

        centers = [X[random.randint(0, n_samples - 1)]]

        

        # 选择剩余的k-1个中心

        for _ in range(self.k - 1):

            # 计算每个点到最近中心的距离

            distances = []

            for x in X:

                min_dist = min(np.linalg.norm(x - c) for c in centers)

                distances.append(min_dist ** 2)

            

            # 归一化为概率

            probs = np.array(distances) / sum(distances)

            

            # 按概率选择

            cumsum = 0

            r = random.random()

            for i, p in enumerate(probs):

                cumsum += p

                if cumsum >= r:

                    centers.append(X[i])

                    break

        

        return np.array(centers)

    

    def _lloyd_iteration(self, X: np.ndarray, centers: np.ndarray) -> Tuple[np.ndarray, float]:

        """

        Lloyd迭代

        

        Returns:

            (new_centers, inertia)

        """

        n_samples = len(X)

        

        # 分配

        labels = np.zeros(n_samples, dtype=int)

        for i, x in enumerate(X):

            distances = [np.linalg.norm(x - c) for c in centers]

            labels[i] = np.argmin(distances)

        

        # 更新中心

        new_centers = np.zeros_like(centers)

        counts = np.zeros(self.k)

        

        for i, x in enumerate(X):

            label = labels[i]

            new_centers[label] += x

            counts[label] += 1

        

        for j in range(self.k):

            if counts[j] > 0:

                new_centers[j] /= counts[j]

            else:

                new_centers[j] = centers[j]  # 保持原样

        

        # 计算inertia

        inertia = sum(

            np.linalg.norm(X[i] - centers[labels[i]]) ** 2

            for i in range(n_samples)

        )

        

        return new_centers, inertia

    

    def fit(self, X: np.ndarray) -> np.ndarray:

        """

        拟合

        

        Returns:

            最终聚类中心

        """

        best_centers = None

        best_inertia = float('inf')

        

        for _ in range(self.n_init):

            # K-means++初始化

            centers = self._init_centers(X)

            

            # Lloyd迭代

            for _ in range(50):  # 最大迭代

                centers, inertia = self._lloyd_iteration(X, centers)

            

            if inertia < best_inertia:

                best_inertia = inertia

                best_centers = centers

        

        self.centers = best_centers

        self.inertia = best_inertia

        return self.centers

    

    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测"""

        labels = []

        for x in X:

            distances = [np.linalg.norm(x - c) for c in self.centers]

            labels.append(np.argmin(distances))

        return np.array(labels)





def demo_streaming_kmeans():

    """演示流式K-means"""

    print("=== 流式K-means演示 ===\n")

    

    np.random.seed(42)

    

    # 生成3个聚类的数据

    n_per_cluster = 100

    centers = [

        np.array([0, 0]),

        np.array([5, 5]),

        np.array([10, 0]),

    ]

    

    X = []

    for center in centers:

        cluster = np.random.randn(n_per_cluster, 2) * 0.5 + center

        X.extend(cluster)

    

    X = np.array(X)

    np.random.shuffle(X)

    

    print(f"数据形状: {X.shape}")

    print(f"真实聚类中心: {centers}")

    

    # 流式学习

    print("\n流式学习:")

    skm = StreamingKMeans(k=3, max_points_per_center=50)

    

    for i in range(0, len(X), 10):

        batch = X[i:i+10]

        skm.partial_fit(batch)

    

    learned_centers = skm.get_centers()

    print(f"学习到的中心:\n{learned_centers}")

    

    # 预测

    labels = skm.predict(X[:30])

    print(f"\n前30个样本的预测标签: {labels[:30]}")

    

    # 统计

    from collections import Counter

    print(f"\n各聚类样本数: {dict(Counter(labels))}")





def demo_kmeans_plusplus():

    """演示K-means++"""

    print("\n=== K-means++初始化演示 ===\n")

    

    np.random.seed(42)

    

    # 生成数据

    n_per_cluster = 50

    centers = [

        np.array([0, 0]),

        np.array([5, 5]),

        np.array([10, 0]),

    ]

    

    X = []

    for center in centers:

        cluster = np.random.randn(n_per_cluster, 2) * 0.5 + center

        X.extend(cluster)

    

    X = np.array(X)

    

    print(f"数据形状: {X.shape}")

    

    # 随机初始化 vs K-means++

    print("\n随机初始化 vs K-means++:")

    

    # 随机

    random_centers = X[np.random.choice(len(X), 3, replace=False)]

    print(f"随机中心: {random_centers}")

    

    # K-means++

    kpp = KMeansPlusPlus(k=3, n_init=5)

    kpp_centers = kpp.fit(X)

    print(f"K-means++中心:\n{kpp_centers}")

    print(f"K-means++ inertia: {kpp.inertia:.2f}")





def demo_clustering_comparison():

    """对比聚类结果"""

    print("\n=== 聚类质量对比 ===\n")

    

    np.random.seed(42)

    

    # 生成数据

    n = 300

    X1 = np.random.randn(n, 2) + [0, 0]

    X2 = np.random.randn(n, 2) + [5, 5]

    X3 = np.random.randn(n, 2) + [10, 0]

    X = np.vstack([X1, X2, X3])

    

    # K-means++

    kpp = KMeansPlusPlus(k=3, n_init=10)

    labels_kpp = kpp.predict(X)

    

    # 流式K-means

    skm = StreamingKMeans(k=3)

    for i in range(0, len(X), 10):

        skm.partial_fit(X[i:i+10])

    labels_streaming = skm.predict(X)

    

    # 计算聚类质量（简化）

    print("聚类标签分布:")

    

    from collections import Counter

    print(f"  K-means++: {dict(Counter(labels_kpp))}")

    print(f"  流式K-means: {dict(Counter(labels_streaming))}")





def demo_streaming_adaptation():

    """演示流式适应"""

    print("\n=== 流式适应演示 ===\n")

    

    np.random.seed(42)

    

    skm = StreamingKMeans(k=2)

    

    print("模拟分布变化:")

    

    # 阶段1: 两个靠近的聚类

    print("  阶段1: 聚类在(2,2)和(4,4)")

    for _ in range(100):

        skm.partial_fit(np.random.randn(10, 2) + [2, 2])

        skm.partial_fit(np.random.randn(10, 2) + [4, 4])

    

    print(f"    中心1: {skm.centers[0].point}")

    print(f"    中心2: {skm.centers[1].point}")

    

    # 阶段2: 聚类分开

    print("  阶段2: 聚类移动到(2,2)和(8,8)")

    for _ in range(100):

        skm.partial_fit(np.random.randn(10, 2) + [2, 2])

        skm.partial_fit(np.random.randn(10, 2) + [8, 8])

    

    print(f"    中心1: {skm.centers[0].point}")

    print(f"    中心2: {skm.centers[1].point}")





if __name__ == "__main__":

    print("=" * 60)

    print("流式K-means++聚类算法")

    print("=" * 60)

    

    # 流式K-means

    demo_streaming_kmeans()

    

    # K-means++

    demo_kmeans_plusplus()

    

    # 质量对比

    demo_clustering_comparison()

    

    # 流式适应

    demo_streaming_adaptation()

    

    print("\n" + "=" * 60)

    print("算法原理:")

    print("=" * 60)

    print("""

1. K-means++初始化:

   - 第一个中心随机选择

   - 后续中心按距离平方概率选择

   - 保证初始化的质量



2. 流式K-means:

   - 在线处理每个样本

   - 决定：更新中心 or 创建新中心

   - 窗口限制防止概念漂移



3. Lloyd迭代:

   - E步：分配到最近中心

   - M步：更新中心位置

   - 迭代直到收敛



4. 复杂度:

   - 标准K-means: O(n*k*d) 每轮

   - K-means++初始化: O(n*k*d)

   - 流式K-means: O(d) 每样本

""")


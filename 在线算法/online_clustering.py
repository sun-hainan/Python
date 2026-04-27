# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / online_clustering

本文件实现 online_clustering 相关的算法功能。
"""

import numpy as np
import random
import math


class OnlineKMeans:
    """
    在线 K-Means（Mini-Batch 变体）
    
    使用小批量数据更新聚类中心
    """

    def __init__(self, n_clusters=3, batch_size=10, max_iter=10):
        """
        初始化
        
        参数:
            n_clusters: 聚类数
            batch_size: 批大小
            max_iter: 最大迭代次数
        """
        self.n_clusters = n_clusters
        self.batch_size = batch_size
        self.max_iter = max_iter
        # 聚类中心
        self.cluster_centers = None
        # 每个聚类的计数
        self.cluster_counts = None

    def _init_centers(self, X):
        """初始化聚类中心（随机选择 K 个点）"""
        indices = random.sample(range(len(X)), min(self.n_clusters, len(X)))
        self.cluster_centers = X[indices].copy()
        self.cluster_counts = np.zeros(self.n_clusters)

    def _assign_to_nearest(self, X):
        """将点分配到最近的聚类"""
        distances = np.zeros((len(X), self.n_clusters))
        for j in range(self.n_clusters):
            distances[:, j] = np.sum((X - self.cluster_centers[j]) ** 2, axis=1)
        return np.argmin(distances, axis=1)

    def partial_fit(self, X):
        """
        部分拟合（增量更新）
        
        参数:
            X: 数据点 (n_samples, n_features)
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if self.cluster_centers is None:
            self._init_centers(X)

        # 分配点
        labels = self._assign_to_nearest(X)

        # 更新聚类中心
        for j in range(self.n_clusters):
            mask = labels == j
            if np.sum(mask) > 0:
                # 使用学习率更新
                lr = 1.0 / (self.cluster_counts[j] + 1)
                self.cluster_centers[j] = (1 - lr) * self.cluster_centers[j] + lr * X[mask].mean(axis=0)
                self.cluster_counts[j] += np.sum(mask)

    def predict(self, X):
        """预测聚类标签"""
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return self._assign_to_nearest(X)

    def get_centers(self):
        """获取聚类中心"""
        return self.cluster_centers


class StreamingKMeans:
    """
    流式 K-Means（BIRCH 简化版）
    
    使用微聚类维护数据统计
    """

    def __init__(self, n_clusters=3, threshold=0.5):
        """
        初始化
        
        参数:
            n_clusters: 最终聚类数
            threshold: 距离阈值
        """
        self.n_clusters = n_clusters
        self.threshold = threshold
        # 微聚类列表：[MicroCluster]
        self.micro_clusters = []
        # 全局统计
        self.n_samples = 0

    class MicroCluster:
        """微聚类"""
        def __init__(self, point):
            self.n = 1
            self.sum = point.copy()
            self.sumsq = point ** 2
            self.center = point.copy()

        def add_point(self, point):
            self.n += 1
            self.sum += point
            self.sumsq += point ** 2
            self.center = self.sum / self.n

        def distance_to(self, point):
            return np.linalg.norm(self.center - point)

    def _find_nearest_cluster(self, point):
        """找到最近的微聚类"""
        if not self.micro_clusters:
            return None, float('inf')
        
        min_dist = float('inf')
        min_idx = 0
        
        for i, mc in enumerate(self.micro_clusters):
            d = mc.distance_to(point)
            if d < min_dist:
                min_dist = d
                min_idx = i
        
        return min_idx, min_dist

    def _absorb_cluster(self, target_idx, source_idx):
        """吸收另一个微聚类"""
        target = self.micro_clusters[target_idx]
        source = self.micro_clusters[source_idx]
        
        total_n = target.n + source.n
        target.sum += source.sum
        target.sumsq += source.sumsq
        target.n = total_n
        target.center = target.sum / total_n

    def partial_fit(self, X):
        """增量添加点"""
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        for point in X:
            min_idx, min_dist = self._find_nearest_cluster(point)
            
            if min_dist <= self.threshold:
                # 吸收到最近的微聚类
                self.micro_clusters[min_idx].add_point(point)
            else:
                # 创建新的微聚类
                self.micro_clusters.append(self.MicroCluster(point))
            
            self.n_samples += 1
            
            # 如果微聚类过多，合并最近的
            if len(self.micro_clusters) > self.n_clusters * 3:
                self._merge_closest()

    def _merge_closest(self):
        """合并最近的两个微聚类"""
        if len(self.micro_clusters) < 2:
            return
        
        min_dist = float('inf')
        merge_pair = (0, 1)
        
        for i in range(len(self.micro_clusters)):
            for j in range(i + 1, len(self.micro_clusters)):
                d = self.micro_clusters[i].distance_to(self.micro_clusters[j].center)
                if d < min_dist:
                    min_dist = d
                    merge_pair = (i, j)
        
        self._absorb_cluster(merge_pair[0], merge_pair[1])
        del self.micro_clusters[merge_pair[1]]

    def get_clusters(self):
        """获取最终聚类中心"""
        centers = np.array([mc.center for mc in self.micro_clusters])
        
        if len(centers) <= self.n_clusters:
            return centers
        
        # 简化：如果微聚类多于目标，使用它们作为候选
        # 实际应该做进一步聚类
        return centers[:self.n_clusters]

    def predict(self, X):
        """预测"""
        centers = self.get_clusters()
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        distances = np.zeros((len(X), len(centers)))
        for j in range(len(centers)):
            distances[:, j] = np.sum((X - centers[j]) ** 2, axis=1)
        return np.argmin(distances, axis=1)


class HierarchicalOnlineClustering:
    """
    分层在线聚类
    
    维护一个聚类层次树
    """

    def __init__(self, max_depth=5, branching_factor=3):
        """
        初始化
        
        参数:
            max_depth: 最大深度
            branching_factor: 分支因子
        """
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        # 根节点
        self.root = None
        # 节点计数
        self.node_count = 0

    class Node:
        def __init__(self, is_leaf=False, depth=0):
            self.is_leaf = is_leaf
            self.depth = depth
            self.children = []  # 子节点或数据点
            self.n_points = 0
            self.center = None
            self.id = 0

        def add_point(self, point):
            self.n_points += 1
            if self.center is None:
                self.center = point.copy()
            else:
                self.center = self.center * (self.n_points - 1) / self.n_points + point / self.n_points

    def partial_fit(self, X):
        """添加数据"""
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        for point in X:
            if self.root is None:
                self.root = self.Node(is_leaf=True, depth=0)
                self.root.id = self.node_count
                self.node_count += 1
            
            self._insert_point(self.root, point)

    def _insert_point(self, node, point):
        """插入点到节点"""
        node.add_point(point)
        
        if node.is_leaf:
            node.children.append(point)
            
            # 如果叶子节点太满，尝试分裂
            if len(node.children) > self.branching_factor * 2 and node.depth < self.max_depth:
                self._split_leaf(node)
        else:
            # 找到最近的子节点
            best_child = None
            best_dist = float('inf')
            
            for child in node.children:
                d = np.linalg.norm(child.center - point)
                if d < best_dist:
                    best_dist = d
                    best_child = child
            
            self._insert_point(best_child, point)

    def _split_leaf(self, node):
        """分裂叶子节点"""
        if len(node.children) < 2:
            return
        
        # 简单分裂：找到两个最远的点作为新中心
        points = np.array(node.children)
        # 计算距离矩阵
        dists = np.sum((points[:, np.newaxis] - points) ** 2, axis=2)
        # 找到最远的两个点
        max_i, max_j = np.unravel_index(np.argmax(dists), dists.shape)
        
        # 创建两个新节点
        child1 = self.Node(is_leaf=True, depth=node.depth + 1)
        child2 = self.Node(is_leaf=True, depth=node.depth + 1)
        child1.id = self.node_count
        self.node_count += 1
        child2.id = self.node_count
        self.node_count += 1
        
        child1.add_point(points[max_i])
        child2.add_point(points[max_j])
        
        # 重新分配其他点
        for i, p in enumerate(points):
            if i not in (max_i, max_j):
                if np.linalg.norm(p - points[max_i]) < np.linalg.norm(p - points[max_j]):
                    child1.children.append(p)
                else:
                    child2.children.append(p)
                child1.add_point(p)
                child2.add_point(p)
        
        node.is_leaf = False
        node.children = [child1, child2]

    def get_clusters(self, max_nodes=10):
        """获取聚类（作为节点）"""
        if self.root is None:
            return []
        
        # BFS 收集叶子节点
        leaves = []
        queue = [self.root]
        
        while queue and len(leaves) < max_nodes:
            node = queue.pop(0)
            if node.is_leaf:
                leaves.append(node)
            else:
                queue.extend(node.children)
        
        return [(leaf.center, leaf.n_points) for leaf in leaves]


if __name__ == "__main__":
    print("=== 在线聚类测试 ===\n")

    # 生成测试数据
    np.random.seed(42)
    
    # 生成 3 个簇
    n_samples = 300
    X1 = np.random.randn(100, 2) + [0, 0]
    X2 = np.random.randn(100, 2) + [5, 5]
    X3 = np.random.randn(100, 2) + [10, 0]
    X = np.vstack([X1, X2, X3])

    # 在线 K-Means
    print("--- 在线 K-Means ---")
    kmeans = OnlineKMeans(n_clusters=3)
    
    # 分批添加数据
    for i in range(0, len(X), 10):
        batch = X[i:i+10]
        kmeans.partial_fit(batch)
    
    labels = kmeans.predict(X)
    print(f"  聚类中心:\n{kmeans.get_centers()}")
    print(f"  聚类大小: {np.bincount(labels)}")

    # 流式 K-Means
    print("\n--- 流式 K-Means ---")
    streaming = StreamingKMeans(n_clusters=3, threshold=2.0)
    
    for point in X:
        streaming.partial_fit(point.reshape(1, -1))
    
    print(f"  微聚类数: {len(streaming.micro_clusters)}")
    print(f"  聚类中心:\n{streaming.get_clusters()}")

    # 分层聚类
    print("\n--- 分层在线聚类 ---")
    hier = HierarchicalOnlineClustering(max_depth=4, branching_factor=3)
    
    for point in X:
        hier.partial_fit(point.reshape(1, -1))
    
    clusters = hier.get_clusters(max_nodes=5)
    print(f"  聚类数: {len(clusters)}")
    for i, (center, n) in enumerate(clusters):
        print(f"    簇 {i}: center={center}, n={n}")

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    
    # 大数据集
    large_X = np.random.randn(10000, 10)
    
    start = time.time()
    kmeans = OnlineKMeans(n_clusters=5, batch_size=100)
    for i in range(0, len(large_X), 100):
        kmeans.partial_fit(large_X[i:i+100])
    elapsed = time.time() - start
    print(f"  在线 K-Means (10000 点): {elapsed:.3f}s")
    
    start = time.time()
    streaming = StreamingKMeans(n_clusters=5, threshold=1.0)
    for point in large_X:
        streaming.partial_fit(point.reshape(1, -1))
    elapsed = time.time() - start
    print(f"  流式 K-Means (10000 点): {elapsed:.3f}s")

    # 聚类质量测试
    print("\n--- 聚类质量测试 ---")
    from sklearn.metrics import adjusted_rand_score
    
    # 生成有标签的数据
    y_true = np.array([0] * 100 + [1] * 100 + [2] * 100)
    
    kmeans = OnlineKMeans(n_clusters=3)
    for i in range(0, len(X), 10):
        kmeans.partial_fit(X[i:i+10])
    y_pred = kmeans.predict(X)
    
    ari = adjusted_rand_score(y_true, y_pred)
    print(f"  Adjusted Rand Index: {ari:.3f}")

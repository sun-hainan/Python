# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / agglomerative_clustering

本文件实现 agglomerative_clustering 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Callable
from collections import defaultdict
import heapq


class AgglomerativeClustering:
    """
    聚合层次聚类
    
    参数:
        n_clusters: 目标簇数
        linkage: 链接方法 ('single', 'complete', 'average', 'ward')
        metric: 距离度量 ('euclidean', 'manhattan', 'cosine')
    """
    
    def __init__(self, n_clusters: int = 2, linkage: str = 'average',
                 metric: str = 'euclidean'):
        self.n_clusters = n_clusters
        self.linkage = linkage
        self.metric = metric
        
        # 聚类标签
        self.labels_: Optional[np.ndarray] = None
        
        # 合并历史（用于构建树状图）
        self.merges: List[Tuple[int, int, float]] = []
        
        # 统计
        self.n_samples = 0
    
    def fit(self, X: np.ndarray) -> 'AgglomerativeClustering':
        """
        执行聚合层次聚类
        
        参数:
            X: 数据矩阵 (n_samples, n_features)
        """
        X = np.asarray(X)
        self.n_samples = X.shape[0]
        
        # 初始化：每个点是一个簇
        # clusters[i] = 当前簇i包含的样本索引集合
        clusters = [set([i]) for i in range(self.n_samples)]
        
        # 簇索引映射（簇可能已被合并）
        cluster_id = {i: i for i in range(self.n_samples)}
        active_clusters = set(range(self.n_samples))
        
        # 距离矩阵（使用优先队列）
        # (distance, cluster1, cluster2)
        distances = self._compute_initial_distances(X, clusters)
        
        self.merges = []
        
        # 合并直到达到目标簇数
        while len(active_clusters) > self.n_clusters:
            # 找到最近的两个簇
            min_dist = float('inf')
            merge_pair = None
            
            # 从优先队列中找最近的活跃簇对
            while distances:
                dist, c1, c2 = heapq.heappop(distances)
                
                # 检查两个簇是否都活跃
                if c1 not in active_clusters or c2 not in active_clusters:
                    continue
                
                # 验证距离是否是最新的
                current_dist = self._compute_cluster_distance(X, clusters[c1], clusters[c2])
                if abs(dist - current_dist) > 1e-10:
                    # 距离已过期，重新计算并放入
                    heapq.heappush(distances, (current_dist, c1, c2))
                    continue
                
                min_dist = dist
                merge_pair = (c1, c2)
                break
            
            if merge_pair is None:
                break
            
            c1, c2 = merge_pair
            
            # 记录合并
            self.merges.append((cluster_id[c1], cluster_id[c2], min_dist))
            
            # 合并簇
            new_cluster = clusters[c1] | clusters[c2]
            new_id = len(clusters)
            clusters.append(new_cluster)
            
            # 更新活动簇
            active_clusters.discard(c1)
            active_clusters.discard(c2)
            active_clusters.add(new_id)
            cluster_id[new_id] = new_id
            
            # 计算新簇到其他簇的距离
            for other_id in active_clusters:
                if other_id == new_id:
                    continue
                dist = self._compute_cluster_distance(X, new_cluster, clusters[other_id])
                heapq.heappush(distances, (dist, new_id, other_id))
        
        # 为每个样本分配标签
        self.labels_ = np.zeros(self.n_samples, dtype=int)
        
        # 根据最终簇分配标签
        cluster_idx = 0
        for cid in active_clusters:
            for sample_idx in clusters[cid]:
                self.labels_[sample_idx] = cluster_idx
            cluster_idx += 1
        
        return self
    
    def _compute_initial_distances(self, X: np.ndarray, clusters: List[set]) -> List[Tuple[float, int, int]]:
        """计算初始距离矩阵"""
        n = len(clusters)
        distances = []
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = self._compute_cluster_distance(X, clusters[i], clusters[j])
                distances.append((dist, i, j))
        
        heapq.heapify(distances)
        return distances
    
    def _compute_cluster_distance(self, X: np.ndarray, cluster1: set, cluster2: set) -> float:
        """计算两个簇之间的距离"""
        if self.linkage == 'single':
            return self._single_linkage(X, cluster1, cluster2)
        elif self.linkage == 'complete':
            return self._complete_linkage(X, cluster1, cluster2)
        elif self.linkage == 'average':
            return self._average_linkage(X, cluster1, cluster2)
        elif self.linkage == 'ward':
            return self._ward_linkage(X, cluster1, cluster2)
        else:
            return self._average_linkage(X, cluster1, cluster2)
    
    def _single_linkage(self, X: np.ndarray, c1: set, c2: set) -> float:
        """Single Linkage：最近邻距离"""
        min_dist = float('inf')
        for i in c1:
            for j in c2:
                dist = self._distance(X[i], X[j])
                if dist < min_dist:
                    min_dist = dist
        return min_dist
    
    def _complete_linkage(self, X: np.ndarray, c1: set, c2: set) -> float:
        """Complete Linkage：最远邻距离"""
        max_dist = 0.0
        for i in c1:
            for j in c2:
                dist = self._distance(X[i], X[j])
                if dist > max_dist:
                    max_dist = dist
        return max_dist
    
    def _average_linkage(self, X: np.ndarray, c1: set, c2: set) -> float:
        """Average Linkage：平均距离"""
        total_dist = 0.0
        count = 0
        for i in c1:
            for j in c2:
                total_dist += self._distance(X[i], X[j])
                count += 1
        return total_dist / count if count > 0 else 0.0
    
    def _ward_linkage(self, X: np.ndarray, c1: set, c2: set) -> float:
        """Ward's Linkage：最小化合并代价"""
        # 合并代价 = SSE_incremental
        n1, n2 = len(c1), len(c2)
        
        # 计算各自中心
        center1 = np.mean(X[list(c1)], axis=0)
        center2 = np.mean(X[list(c2)], axis=0)
        center_combined = np.mean(X[list(c1 | c2)], axis=0)
        
        # SSE增量
        sse1 = sum(self._distance(X[i], center1) ** 2 for i in c1)
        sse2 = sum(self._distance(X[i], center2) ** 2 for i in c2)
        sse_combined = sum(self._distance(X[i], center_combined) ** 2 for i in (c1 | c2))
        
        return sse_combined - sse1 - sse2
    
    def _distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """计算两点间距离"""
        if self.metric == 'euclidean':
            return np.linalg.norm(x1 - x2)
        elif self.metric == 'manhattan':
            return np.sum(np.abs(x1 - x2))
        elif self.metric == 'cosine':
            dot = np.dot(x1, x2)
            norm1 = np.linalg.norm(x1)
            norm2 = np.linalg.norm(x2)
            if norm1 == 0 or norm2 == 0:
                return 1.0
            return 1.0 - dot / (norm1 * norm2)
        else:
            return np.linalg.norm(x1 - x2)
    
    def get_merges(self) -> List[Tuple[int, int, float]]:
        """返回合并历史"""
        return self.merges
    
    def get_dendrogram_data(self) -> dict:
        """
        获取树状图数据
        
        返回:
            {'left': [...], 'right': [...], 'height': [...]}
        """
        left = [m[0] for m in self.merges]
        right = [m[1] for m in self.merges]
        height = [m[2] for m in self.merges]
        
        return {'left': left, 'right': right, 'height': height}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测（将新数据分配到最近簇中心）
        """
        X = np.asarray(X)
        
        # 计算每个新点到各簇中心的距离
        n_new = X.shape[0]
        n_clusters = len(set(self.labels_))
        
        # 计算簇中心
        centers = []
        for c in range(n_clusters):
            mask = self.labels_ == c
            centers.append(np.mean(X[mask], axis=0) if mask.sum() > 0 else np.zeros(X.shape[1]))
        
        labels = np.zeros(n_new, dtype=int)
        for i, x in enumerate(X):
            min_dist = float('inf')
            best_cluster = 0
            for c, center in enumerate(centers):
                dist = self._distance(x, center)
                if dist < min_dist:
                    min_dist = dist
                    best_cluster = c
            labels[i] = best_cluster
        
        return labels


def simple_dendrogram(left: List[int], right: List[int], height: List[float], 
                      n_leaves: int) -> None:
    """简单打印树状图（文本版本）"""
    print("\n简化树状图:")
    print("-" * 40)
    
    for i, (l, r, h) in enumerate(zip(left, right, height)):
        level = int(h * 5) if height else 0
        indent = "  " * min(level, 10)
        
        if l < n_leaves and r < n_leaves:
            print(f"{indent}合并簇 {l} + {r} -> 距离 {h:.3f}")
        elif l < n_leaves:
            print(f"{indent}合并簇 {l} + 簇{r-n_leaves} -> 距离 {h:.3f}")
        else:
            print(f"{indent}合并簇{l-n_leaves} + 簇{r-n_leaves} -> 距离 {h:.3f}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("聚合层次聚类测试")
    print("=" * 50)
    
    import random
    
    np.random.seed(42)
    random.seed(42)
    
    # 生成演示数据：3个簇
    n_per_cluster = 30
    
    # 簇1：中心(0,0)
    cluster1 = np.random.randn(n_per_cluster, 2) + [0, 0]
    
    # 簇2：中心(5,2)
    cluster2 = np.random.randn(n_per_cluster, 2) + [5, 2]
    
    # 簇3：中心(2,5)
    cluster3 = np.random.randn(n_per_cluster, 2) + [2, 5]
    
    # 合并
    X = np.vstack([cluster1, cluster2, cluster3])
    true_labels = np.array([0] * n_per_cluster + [1] * n_per_cluster + [2] * n_per_cluster)
    
    # 打乱
    shuffle_idx = np.random.permutation(len(X))
    X = X[shuffle_idx]
    
    print(f"\n数据形状: {X.shape}")
    print(f"真实簇: {len(np.unique(true_labels))} 个")
    
    # 测试不同链接方法
    linkage_methods = ['single', 'complete', 'average', 'ward']
    
    for method in linkage_methods:
        print(f"\n--- {method} linkage ---")
        
        model = AgglomerativeClustering(n_clusters=3, linkage=method)
        model.fit(X)
        
        labels = model.labels_
        
        # 计算准确率（使用 Hungarian algorithm 的简化版）
        # 找最佳标签映射
        from collections import Counter
        best_correct = 0
        for true_c in range(3):
            for pred_c in range(3):
                correct = np.sum((true_labels == true_c) & (labels == pred_c))
                best_correct = max(best_correct, correct)
        
        accuracy = best_correct / len(X)
        print(f"聚类准确率: {accuracy:.2%}")
        print(f"簇分布: {Counter(labels)}")
    
    # 树状图数据
    print("\n--- 合并历史 ---")
    
    model = AgglomerativeClustering(n_clusters=3, linkage='ward')
    model.fit(X)
    
    dendro = model.get_dendrogram_data()
    print(f"合并次数: {len(dendro['height'])}")
    print(f"最后5次合并高度: {dendro['height'][-5:]}")
    
    # 性能测试
    print("\n" + "=" * 50)
    print("性能测试")
    print("=" * 50)
    
    import time
    
    for n in [100, 500, 1000]:
        X_large = np.random.randn(n, 5)
        
        for method in ['average', 'ward']:
            start = time.time()
            model = AgglomerativeClustering(n_clusters=5, linkage=method)
            model.fit(X_large)
            elapsed = time.time() - start
            
            print(f"n={n}, linkage={method}: {elapsed:.3f}秒")

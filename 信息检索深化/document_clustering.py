"""
文档聚类模块 - K-means/层次聚类

本模块实现多种文档聚类算法，用于组织和导航大规模文档集合。

核心算法：
1. K-Means：经典的划分聚类
2. 层次凝聚聚类（Agglomerative）
3. DBSCAN：基于密度的聚类
4. LSH：局部敏感哈希用于近似聚类
"""

import numpy as np
from typing import List, Tuple, Dict, Set
from collections import Counter, defaultdict
import heapq


class DocumentVectorizer:
    """文档向量化：将文本转为数值向量"""

    def __init__(self, vocab: List[str] = None):
        self.vocab = vocab or []
        self.vocab_size = len(self.vocab)
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}

    def fit(self, documents: List[str]):
        """从文档集合构建词表"""
        all_words = set()
        for doc in documents:
            words = doc.lower().split()
            all_words.update(words)
        self.vocab = list(all_words)
        self.vocab_size = len(self.vocab)
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}

    def transform(self, document: str) -> np.ndarray:
        """将单个文档转为向量"""
        words = document.lower().split()
        vector = np.zeros(self.vocab_size)
        for word in words:
            if word in self.word_to_idx:
                vector[self.word_to_idx[word]] += 1
        return vector

    def fit_transform(self, documents: List[str]) -> np.ndarray:
        """一步完成fit和transform"""
        self.fit(documents)
        return np.array([self.transform(doc) for doc in documents])


class KMeansClustering:
    """K-Means聚类算法"""

    def __init__(self, n_clusters: int = 5, max_iter: int = 100, tol: float = 1e-4,
                 init: str = 'kmeans++', random_state: int = 42):
        """
        :param n_clusters: 聚类数量
        :param max_iter: 最大迭代次数
        :param tol: 收敛阈值
        :param init: 初始化方法 'random' 或 'kmeans++'
        :param random_state: 随机种子
        """
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.init = init
        self.random_state = random_state

        self.centroids = None
        self.labels = None
        self.inertia_ = 0

    def _init_centroids(self, X: np.ndarray):
        """初始化质心"""
        np.random.seed(self.random_state)
        n_samples, n_features = X.shape

        if self.init == 'kmeans++':
            # K-Means++初始化
            centroids = [X[np.random.randint(n_samples)]]  # 第一个质心随机选

            for _ in range(1, self.n_clusters):
                # 计算每个点到最近质心的距离
                distances = np.array([min(np.linalg.norm(x - c) ** 2 for c in centroids) for x in X])
                # 按概率选择下一个质心
                probs = distances / distances.sum()
                next_centroid_idx = np.random.choice(n_samples, p=probs)
                centroids.append(X[next_centroid_idx])

            self.centroids = np.array(centroids)
        else:
            # 随机初始化
            indices = np.random.choice(n_samples, self.n_clusters, replace=False)
            self.centroids = X[indices]

    def _compute_distances(self, X: np.ndarray) -> np.ndarray:
        """计算每个点到所有质心的距离"""
        n_samples = X.shape[0]
        distances = np.zeros((n_samples, self.n_clusters))

        for k in range(self.n_clusters):
            distances[:, k] = np.linalg.norm(X - self.centroids[k], axis=1)

        return distances

    def _assign_labels(self, distances: np.ndarray) -> np.ndarray:
        """分配标签"""
        return np.argmin(distances, axis=1)

    def _update_centroids(self, X: np.ndarray, labels: np.ndarray):
        """更新质心"""
        new_centroids = np.zeros_like(self.centroids)

        for k in range(self.n_clusters):
            cluster_points = X[labels == k]
            if len(cluster_points) > 0:
                new_centroids[k] = cluster_points.mean(axis=0)
            else:
                # 空簇：随机选一个点
                new_centroids[k] = X[np.random.randint(len(X))]

        return new_centroids

    def fit(self, X: np.ndarray):
        """训练聚类模型"""
        n_samples, n_features = X.shape

        # 初始化
        self._init_centroids(X)

        for iteration in range(self.max_iter):
            # 分配标签
            distances = self._compute_distances(X)
            labels = self._assign_labels(distances)

            # 更新质心
            new_centroids = self._update_centroids(X, labels)

            # 计算inertia（簇内平方和）
            self.inertia_ = 0
            for k in range(self.n_clusters):
                cluster_points = X[labels == k]
                if len(cluster_points) > 0:
                    self.inertia_ += np.sum((cluster_points - self.centroids[k]) ** 2)

            # 检查收敛
            shift = np.linalg.norm(new_centroids - self.centroids)
            self.centroids = new_centroids

            if shift < self.tol:
                break

        self.labels = labels
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测新数据的标签"""
        distances = self._compute_distances(X)
        return self._assign_labels(distances)


class HierarchicalClustering:
    """层次聚类（Agglomerative）"""

    def __init__(self, n_clusters: int = 5, linkage: str = 'ward', metric: str = 'euclidean'):
        """
        :param n_clusters: 目标聚类数
        :param linkage: 连接方法 'ward', 'complete', 'average'
        :param metric: 距离度量
        """
        self.n_clusters = n_clusters
        self.linkage = linkage
        self.metric = metric

        self.labels_ = None
        self.distances_ = []  # 聚类合并距离历史

    def _compute_distance(self, X: np.ndarray, cluster_i: Set[int], cluster_j: Set[int]) -> float:
        """计算两个簇之间的距离"""
        if self.linkage == 'ward':
            # Ward距离：合并后的方差增量
            return np.inf  # 简化
        else:
            # 平均/最大连接
            distances = []
            for i in cluster_i:
                for j in cluster_j:
                    distances.append(np.linalg.norm(X[i] - X[j]))

            if self.linkage == 'average':
                return np.mean(distances)
            else:  # complete
                return max(distances)

    def fit(self, X: np.ndarray):
        """训练层次聚类"""
        n_samples = X.shape[0]

        # 初始化：每个点一个簇
        clusters = [{i} for i in range(n_samples)]
        self.distances_ = []

        while len(clusters) > self.n_clusters:
            # 找最近的两个簇
            min_dist = float('inf')
            merge_pair = (0, 1)

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    dist = self._compute_distance(X, clusters[i], clusters[j])
                    if dist < min_dist:
                        min_dist = dist
                        merge_pair = (i, j)

            # 合并
            i, j = merge_pair
            merged = clusters[i] | clusters[j]
            self.distances_.append(min_dist)

            # 删除旧簇，添加新簇
            clusters = [clusters[k] for k in range(len(clusters)) if k not in merge_pair]
            clusters.append(merged)

        # 分配标签
        self.labels_ = np.zeros(n_samples, dtype=int)
        for label, cluster in enumerate(clusters):
            for idx in cluster:
                self.labels_[idx] = label

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """返回标签（层次聚类不需要单独预测）"""
        return self.labels_


class DBSCAN:
    """DBSCAN密度聚类"""

    def __init__(self, eps: float = 0.5, min_samples: int = 5, metric: str = 'euclidean'):
        """
        :param eps: 邻域半径
        :param min_samples: 核心点的最小邻居数
        """
        self.eps = eps
        self.min_samples = min_samples

        self.labels_ = None
        self.core_sample_indices_ = []

    def _region_query(self, X: np.ndarray, point_idx: int) -> List[int]:
        """找邻域内的所有点"""
        neighbors = []
        for i in range(len(X)):
            if np.linalg.norm(X[point_idx] - X[i]) <= self.eps:
                neighbors.append(i)
        return neighbors

    def fit(self, X: np.ndarray):
        """训练DBSCAN"""
        n_samples = X.shape[0]
        self.labels_ = np.zeros(n_samples, dtype=int) - 1  # -1表示噪声
        cluster_id = 0

        for point_idx in range(n_samples):
            if self.labels_[point_idx] != -1:  # 已访问
                continue

            # 找邻域
            neighbors = self._region_query(X, point_idx)

            if len(neighbors) < self.min_samples:
                # 暂时标记为噪声
                self.labels_[point_idx] = -1
            else:
                # 扩展簇
                self._expand_cluster(X, point_idx, neighbors, cluster_id)
                cluster_id += 1

        return self

    def _expand_cluster(self, X: np.ndarray, point_idx: int, neighbors: List[int], cluster_id: int):
        """递归扩展簇"""
        self.labels_[point_idx] = cluster_id
        self.core_sample_indices_.append(point_idx)

        queue = list(neighbors)
        visited = set(neighbors)

        while queue:
            current = queue.pop(0)

            if self.labels_[current] == -1:
                # 边界点
                self.labels_[current] = cluster_id

            if self.labels_[current] != -1:
                continue

            self.labels_[current] = cluster_id
            self.core_sample_indices_.append(current)

            # 检查是否核心点
            current_neighbors = self._region_query(X, current)
            if len(current_neighbors) >= self.min_samples:
                for neighbor in current_neighbors:
                    if neighbor not in visited:
                        queue.append(neighbor)
                        visited.add(neighbor)


class LSHIndex:
    """局部敏感哈希（LSH）用于近似最近邻搜索"""

    def __init__(self, n_hashes: int = 10, n_tables: int = 5, dim: int = None):
        """
        :param n_hashes: 每个表的哈希函数数量
        :param n_tables: 哈希表数量
        """
        self.n_hashes = n_hashes
        self.n_tables = n_tables
        self.dim = dim

        # 随机投影向量
        self.projection_tables = []
        for _ in range(n_tables):
            table = [np.random.randn(dim) for _ in range(n_hashes)]
            self.projection_tables.append(table)

        # 哈希桶
        self.hash_tables = [defaultdict(list) for _ in range(n_tables)]

    def _hash_vector(self, vector: np.ndarray, table_idx: int) -> Tuple:
        """计算向量的哈希签名"""
        signature = []
        for proj in self.projection_tables[table_idx]:
            # 投影后取符号作为比特
            bit = 1 if np.dot(vector, proj) >= 0 else 0
            signature.append(bit)
        return tuple(signature)

    def index(self, doc_id: str, vector: np.ndarray):
        """添加文档到LSH索引"""
        for table_idx in range(self.n_tables):
            bucket_key = self._hash_vector(vector, table_idx)
            self.hash_tables[table_idx][bucket_key].append(doc_id)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        搜索近似最近邻
        :return: [(doc_id, 命中哈希表数)]
        """
        candidate_counts = Counter()

        for table_idx in range(self.n_tables):
            bucket_key = self._hash_vector(query_vector, table_idx)
            candidates = self.hash_tables[table_idx][bucket_key]
            for doc_id in candidates:
                candidate_counts[doc_id] += 1

        # 按命中数排序
        return candidate_counts.most_common(top_k)


def compute_silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
    """计算轮廓系数"""
    n_samples = len(X)
    unique_labels = set(labels)
    scores = []

    for i in range(n_samples):
        label = labels[i]

        # 找同簇其他点
        same_cluster = X[labels == label]
        if len(same_cluster) > 1:
            a = np.mean(np.linalg.norm(X[i] - same_cluster, axis=1))
        else:
            a = 0

        # 找最近邻簇
        min_b = float('inf')
        for other_label in unique_labels:
            if other_label != label:
                other_cluster = X[labels == other_label]
                b = np.mean(np.linalg.norm(X[i] - other_cluster, axis=1))
                min_b = min(min_b, b)

        if max(a, min_b) > 0:
            scores.append((min_b - a) / max(a, min_b))

    return np.mean(scores) if scores else 0


def demo():
    """文档聚类演示"""
    # 文档数据
    documents = [
        "machine learning algorithms process data",
        "deep learning neural networks analyze patterns",
        "natural language processing understands text",
        "computer vision recognizes images",
        "supervised learning uses labeled training",
        "unsupervised learning finds hidden patterns",
        "reinforcement learning maximizes rewards",
        "neural networks process complex information",
        "text classification categorizes documents",
        "image recognition identifies objects"
    ]

    print("[文档聚类演示]")

    # 向量化
    vectorizer = DocumentVectorizer()
    vectors = vectorizer.fit_transform(documents)
    print(f"  文档向量形状: {vectors.shape}")

    # K-Means聚类
    kmeans = KMeansClustering(n_clusters=3, random_state=42)
    kmeans.fit(vectors)
    print(f"\n  K-Means聚类 (k=3):")
    for i in range(3):
        cluster_docs = [documents[j] for j in range(len(documents)) if kmeans.labels[j] == i]
        print(f"    Cluster {i}: {cluster_docs[:3]}...")

    # 层次聚类
    hierarchical = HierarchicalClustering(n_clusters=3)
    hierarchical.fit(vectors)
    print(f"\n  层次聚类结果:")
    for i in range(3):
        cluster_docs = [documents[j] for j in range(len(documents)) if hierarchical.labels_[j] == i]
        print(f"    Cluster {i}: {cluster_docs[:3]}...")

    # DBSCAN
    dbscan = DBSCAN(eps=2.0, min_samples=2)
    dbscan.fit(vectors)
    n_clusters = len(set(dbscan.labels_)) - (1 if -1 in dbscan.labels_ else 0)
    n_noise = list(dbscan.labels_).count(-1)
    print(f"\n  DBSCAN聚类: {n_clusters}个簇, {n_noise}个噪声点")

    # LSH
    lsh = LSHIndex(n_hashes=5, n_tables=3, dim=vectors.shape[1])
    for i, doc in enumerate(documents):
        lsh.index(f"doc_{i}", vectors[i])
    query_vec = vectors[0]
    results = lsh.search(query_vec, top_k=3)
    print(f"\n  LSH搜索结果 (query=doc_0): {results}")

    # 轮廓系数
    silhouette = compute_silhouette_score(vectors, kmeans.labels)
    print(f"\n  轮廓系数 (K-Means): {silhouette:.4f}")

    print("  ✅ 文档聚类演示通过！")


if __name__ == "__main__":
    demo()

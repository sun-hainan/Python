# -*- coding: utf-8 -*-

"""

算法实现：数据挖掘 / dbscan



本文件实现 dbscan 相关的算法功能。

"""



import numpy as np

from collections import deque





class DBSCAN:

    """DBSCAN 密度聚类算法"""



    def __init__(self, eps=0.5, min_samples=5):

        """

        eps: ε-邻域半径

        min_samples: 核心点的最小邻居数（含自身）

        """

        self.eps = eps

        self.min_samples = min_samples

        self.labels_ = None  # -1 表示噪声

        self.core_indices_ = None  # 核心点索引



    def _region_query(self, X, point_idx):

        """查找 ε-邻域内的所有点"""

        distances = np.linalg.norm(X - X[point_idx], axis=1)

        neighbors = np.where(distances <= self.eps)[0]

        return neighbors



    def _expand_cluster(self, X, labels, point_idx, neighbors, cluster_id):

        """从核心点出发扩展簇（DFS）"""

        labels[point_idx] = cluster_id

        queue = deque(neighbors)

        visited = set(neighbors)



        while queue:

            q_idx = queue.popleft()

            if labels[q_idx] == -1:  # 之前是噪声

                labels[q_idx] = cluster_id

            if labels[q_idx] != 0:  # 已在簇中

                continue



            labels[q_idx] = cluster_id

            # 如果是核心点，扩展其邻域

            q_neighbors = self._region_query(X, q_idx)

            if len(q_neighbors) >= self.min_samples:

                for n_idx in q_neighbors:

                    if n_idx not in visited:

                        queue.append(n_idx)

                        visited.add(n_idx)



    def fit(self, X):

        """训练 DBSCAN"""

        n_samples = X.shape[0]

        labels = np.zeros(n_samples, dtype=int)  # 0=未访问

        cluster_id = 0

        core_indices = []



        for point_idx in range(n_samples):

            if labels[point_idx] != 0:  # 已访问

                continue



            # 找到 ε-邻域

            neighbors = self._region_query(X, point_idx)



            if len(neighbors) < self.min_samples:

                # 噪声点（暂时标记为 -1，后面可能被其他簇合并）

                labels[point_idx] = -1

            else:

                # 核心点：创建新簇

                core_indices.append(point_idx)

                self._expand_cluster(X, labels, point_idx, neighbors, cluster_id)

                cluster_id += 1



        self.labels_ = labels

        self.core_indices_ = np.array(core_indices)

        self.n_clusters_ = cluster_id



        return self



    def fit_predict(self, X):

        """拟合并返回簇标签"""

        self.fit(X)

        return self.labels_





def compute_reachability_plot(X, max_eps=2.0, n_points=100):

    """计算可达距离图（用于选择 ε）"""

    eps_values = np.linspace(0.1, max_eps, n_points)

    core_counts = []

    for eps in eps_values:

        dbscan = DBSCAN(eps=eps, min_samples=5)

        dbscan.fit(X)

        core_counts.append(len(dbscan.core_indices_))

    return eps_values, core_counts





def demo():

    """DBSCAN 聚类演示"""

    np.random.seed(42)



    # 生成簇数据（包含不同密度的簇）

    # 簇1：高密度

    c1 = np.random.randn(100, 2) + [0, 0]

    # 簇2：低密度但形状不规则

    angle = np.random.uniform(0, 2 * np.pi, 50)

    r = 3 + np.random.randn(50) * 0.3

    c2 = np.column_stack([r * np.cos(angle), r * np.sin(angle)]) + [5, 5]

    # 噪声点

    noise = np.random.uniform(-2, 8, (20, 2))



    X = np.vstack([c1, c2, noise])



    print("=== DBSCAN 聚类演示 ===")

    print(f"数据形状: {X.shape}")

    print(f"参数: eps=0.5, min_samples=5")



    dbscan = DBSCAN(eps=0.5, min_samples=5)

    labels = dbscan.fit_predict(X)



    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    print(f"发现的簇数: {n_clusters}")

    print(f"噪声点数: {np.sum(labels == -1)}")

    print(f"核心点数: {len(dbscan.core_indices_)}")

    print(f"各簇样本数: {np.bincount[labels[labels >= 0]]}")



    # 不同参数对比

    print("\n不同参数对比:")

    for eps in [0.3, 0.5, 0.8, 1.0]:

        for min_s in [3, 5, 10]:

            d = DBSCAN(eps=eps, min_samples=min_s)

            lbls = d.fit_predict(X)

            n_c = len(set(lbls)) - (1 if -1 in lbls else 0)

            n_noise = np.sum(lbls == -1)

            print(f"  eps={eps}, min_samples={min_s} -> 簇数={n_c}, 噪声={n_noise}")





if __name__ == "__main__":

    demo()


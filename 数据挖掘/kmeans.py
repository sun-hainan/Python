# -*- coding: utf-8 -*-

"""

算法实现：数据挖掘 / kmeans



本文件实现 kmeans 相关的算法功能。

"""



import numpy as np





class KMeans:

    """K-Means 聚类算法"""



    def __init__(self, n_clusters=3, max_iter=300, tol=1e-4, n_init=10, random_state=None):

        """

        n_clusters: 簇数 K

        max_iter: 最大迭代次数

        tol: 收敛阈值（簇中心变化小于此值则停止）

        n_init: 随机初始化次数（取最优结果）

        random_state: 随机种子

        """

        self.n_clusters = n_clusters

        self.max_iter = max_iter

        self.tol = tol

        self.n_init = n_init

        self.random_state = random_state

        self.cluster_centers_ = None  # (K, D)

        self.labels_ = None  # (N,)

        self.inertia_ = None  # 簇内平方和（惯性）



    def _init_centroids(self, X):

        """K-Means++ 初始化：选择距离现有中心最远的样本作为新中心"""

        n_samples, n_features = X.shape

        centroids = []

        # 随机选第一个中心

        rng = np.random.default_rng(self.random_state)

        idx = rng.integers(0, n_samples)

        centroids.append(X[idx])



        for _ in range(1, self.n_clusters):

            # 计算每个样本到最近中心的距离

            distances = np.full(n_samples, np.inf)

            for c_idx, c in enumerate(centroids):

                dist = np.sum((X - c) ** 2, axis=1)

                distances = np.minimum(distances, dist)

            # 按距离分布采样下一个中心

            probs = distances / distances.sum()

            idx = rng.choice(n_samples, p=probs)

            centroids.append(X[idx])



        return np.array(centroids)



    def _assign_clusters(self, X, centroids):

        """将每个样本分配给最近的簇中心"""

        # 计算每个样本到每个中心的欧氏距离

        distances = np.zeros((X.shape[0], self.n_clusters))

        for k in range(self.n_clusters):

            distances[:, k] = np.sum((X - centroids[k]) ** 2, axis=1)

        # 分配到最近中心

        labels = np.argmin(distances, axis=1)

        return labels, distances



    def _update_centroids(self, X, labels):

        """重新计算簇中心（取均值）"""

        new_centroids = np.zeros((self.n_clusters, X.shape[1]))

        for k in range(self.n_clusters):

            cluster_points = X[labels == k]

            if len(cluster_points) > 0:

                new_centroids[k] = cluster_points.mean(axis=0)

            else:

                # 空簇：用随机点替代

                new_centroids[k] = X[np.random.randint(len(X))]

        return new_centroids



    def fit(self, X):

        """训练 K-Means 模型"""

        n_samples, n_features = X.shape

        best_inertia = np.inf

        best_centroids = None

        best_labels = None



        for init in range(self.n_init):

            # 初始化中心

            centroids = self._init_centroids(X)



            for iteration in range(self.max_iter):

                # E 步：分配簇

                labels, distances = self._assign_clusters(X, centroids)

                # M 步：更新中心

                new_centroids = self._update_centroids(X, labels)

                # 检查收敛

                shift = np.linalg.norm(new_centroids - centroids)

                centroids = new_centroids

                if shift < self.tol:

                    break



            # 计算惯性（簇内平方和）

            inertia = distances[np.arange(n_samples), labels].sum()



            if inertia < best_inertia:

                best_inertia = inertia

                best_centroids = centroids

                best_labels = labels



        self.cluster_centers_ = best_centroids

        self.labels_ = best_labels

        self.inertia_ = best_inertia



        return self



    def predict(self, X):

        """预测新样本的簇标签"""

        labels, _ = self._assign_clusters(X, self.cluster_centers_)

        return labels



    def fit_predict(self, X):

        """拟合并返回簇标签"""

        self.fit(X)

        return self.labels_





def elbow_method(X, max_k=10):

    """肘部法则：计算不同 K 值对应的惯性，用于选择最优 K"""

    inertias = []

    for k in range(1, max_k + 1):

        km = KMeans(n_clusters=k, n_init=10, random_state=42)

        km.fit(X)

        inertias.append(km.inertia_)

    return inertias





def demo():

    """K-Means 聚类演示"""

    np.random.seed(42)



    # 生成三个簇的样本数据

    cluster1 = np.random.randn(50, 2) + [0, 0]

    cluster2 = np.random.randn(50, 2) + [5, 5]

    cluster3 = np.random.randn(50, 2) + [0, 5]

    X = np.vstack([cluster1, cluster2, cluster3])



    print("=== K-Means 聚类演示 ===")

    print(f"数据形状: {X.shape}")



    # 聚类

    km = KMeans(n_clusters=3, n_init=10, random_state=42)

    labels = km.fit_predict(X)



    print(f"簇中心:\n{km.cluster_centers_.round(3)}")

    print(f"各簇样本数: {np.bincount(labels)}")

    print(f"惯性（簇内平方和）: {km.inertia_:.4f}")



    # 预测新样本

    new_point = np.array([[1, 1], [4.5, 4.5]])

    pred_labels = km.predict(new_point)

    print(f"\n新样本 {new_point.tolist()}")

    print(f"预测簇标签: {pred_labels}")



    # 肘部法则

    print("\n肘部法则（K=1~5）:")

    for k, inertia in zip(range(1, 6), elbow_method(X, 5)):

        print(f"  K={k}: 惯性={inertia:.2f}")





if __name__ == "__main__":

    demo()


# -*- coding: utf-8 -*-

"""

算法实现：数据挖掘 / outlier_detection



本文件实现 outlier_detection 相关的算法功能。

"""



import numpy as np

from collections import Counter





class LOF:

    """Local Outlier Factor（局部离群因子）"""



    def __init__(self, n_neighbors=20, contamination=0.1):

        """

        n_neighbors: 邻居数量 K

        contamination: 污染比例（异常点比例）

        """

        self.n_neighbors = n_neighbors

        self.contamination = contamination

        self.decision_scores_ = None  # LOF 分数



    def _compute_lrd(self, X, kdtree=None):

        """计算局部可达密度（Local Reachability Density）"""

        n_samples = X.shape[0]

        lrd = np.zeros(n_samples)

        kdistances = np.zeros(n_samples)  # 第 K 距离

        neighbors = np.zeros((n_samples, self.n_neighbors), dtype=int)



        for i in range(n_samples):

            # 计算到其他所有点的距离

            distances = np.linalg.norm(X - X[i], axis=1)

            # 第 K 近邻的距离

            sorted_dist = np.sort(distances)

            kdistances[i] = sorted_dist[self.n_neighbors]

            # K 个最近邻的索引

            neighbors[i] = np.argsort(distances)[1:self.n_neighbors + 1]



        # 计算可达距离

        for i in range(n_samples):

            k = self.n_neighbors

            reach_dist = np.maximum(kdistances[neighbors[i]], distances[i])

            lrd[i] = k / np.sum(reach_dist)



        return lrd, neighbors



    def fit_predict(self, X):

        """训练并返回异常标签（1=正常, -1=异常）"""

        n_samples = X.shape[0]

        lrd, neighbors = self._compute_lrd(X)



        # 计算 LOF = avg(lrd(neighbor) / lrd(point))

        lof_scores = np.zeros(n_samples)

        for i in range(n_samples):

            neighbor_lrd = lrd[neighbors[i]]

            lof_scores[i] = np.mean(neighbor_lrd / lrd[i])



        self.decision_scores_ = lof_scores



        # 根据污染比例确定阈值

        threshold = np.percentile(lof_scores, (1 - self.contamination) * 100)

        labels = np.where(lof_scores > threshold, -1, 1)



        return labels





class IsolationForest:

    """Isolation Forest（隔离森林）简化版"""



    def __init__(self, n_trees=100, max_height=10, contamination=0.1, random_state=None):

        self.n_trees = n_trees

        self.max_height = max_height

        self.contamination = contamination

        self.random_state = random_state

        self.trees = []



    class TreeNode:

        def __init__(self, feature_idx=None, threshold=None, left=None, right=None, size=0):

            self.feature_idx = feature_idx  # 划分特征索引

            self.threshold = threshold  # 划分阈值

            self.left = left

            self.right = right

            self.size = size  # 节点中的样本数



    def fit(self, X):

        """训练 Isolation Forest"""

        rng = np.random.default_rng(self.random_state)

        self.trees = []



        for _ in range(self.n_trees):

            # 随机采样训练数据（有放回）

            sample_indices = rng.choice(X.shape[0], size=X.shape[0], replace=True)

            X_sample = X[sample_indices]

            tree = self._build_tree(X_sample, depth=0, rng=rng)

            self.trees.append(tree)



        return self



    def _build_tree(self, X, depth, rng):

        """递归构建随机决策树"""

        if depth >= self.max_height or len(X) <= 1:

            return self.TreeNode(size=len(X))



        feature_idx = rng.integers(0, X.shape[1])

        min_val = X[:, feature_idx].min()

        max_val = X[:, feature_idx].max()



        if min_val == max_val:

            return self.TreeNode(size=len(X))



        threshold = rng.uniform(min_val, max_val)

        left_mask = X[:, feature_idx] < threshold

        left = self._build_tree(X[left_mask], depth + 1, rng)

        right = self._build_tree(X[~left_mask], depth + 1, rng)



        return self.TreeNode(feature_idx, threshold, left, right, size=len(X))



    def _path_length(self, x, node, depth=0):

        """计算样本从根到叶的路径长度"""

        if node.left is None or node.right is None:

            return depth

        if x[node.feature_idx] < node.threshold:

            return self._path_length(x, node.left, depth + 1)

        else:

            return self._path_length(x, node.right, depth + 1)



    def decision_function(self, X):

        """计算异常分数（路径长度越短越异常）"""

        n_samples = X.shape[0]

        avg_path_lengths = np.zeros(n_samples)



        for x_idx in range(n_samples):

            total_path = 0

            for tree in self.trees:

                path_len = self._path_length(X[x_idx], tree)

                total_path += path_len

            avg_path_lengths[x_idx] = total_path / self.n_trees



        # 转换为异常分数：指数衰减，路径越短分数越高

        scores = np.exp(-avg_path_lengths / (2 ** self.max_height))

        return scores



    def fit_predict(self, X):

        """拟合并返回异常标签"""

        self.fit(X)

        scores = self.decision_function(X)

        threshold = np.percentile(scores, (1 - self.contamination) * 100)

        return np.where(scores > threshold, -1, 1)





def demo():

    """异常检测演示"""

    np.random.seed(42)



    # 正常数据：两个高斯簇

    normal1 = np.random.randn(200, 2) + [0, 0]

    normal2 = np.random.randn(200, 2) + [5, 5]

    normal_data = np.vstack([normal1, normal2])



    # 异常数据

    outliers = np.random.uniform(-3, 8, (20, 2))



    X = np.vstack([normal_data, outliers])

    true_labels = np.array([1] * 400 + [-1] * 20)



    print("=== 异常检测演示 ===")

    print(f"数据形状: {X.shape}")

    print(f"真实异常点数: {np.sum(true_labels == -1)}")



    # LOF

    lof = LOF(n_neighbors=20, contamination=0.05)

    lof_labels = lof.fit_predict(X)

    print(f"\nLOF 检测异常数: {np.sum(lof_labels == -1)}")

    print(f"LOF 正确检测: {np.sum(lof_labels == true_labels)}")



    # Isolation Forest

    iso = IsolationForest(n_trees=100, contamination=0.05, random_state=42)

    iso_labels = iso.fit_predict(X)

    print(f"\nIsolation Forest 检测异常数: {np.sum(iso_labels == -1)}")

    print(f"Isolation Forest 正确检测: {np.sum(iso_labels == true_labels)}")



    # 显示分数分布

    print(f"\nLOF 分数范围: [{lof.decision_scores_.min():.3f}, {lof.decision_scores_.max():.3f}]")

    print(f"IForest 分数范围: [{iso.decision_function(X).min():.3f}, {iso.decision_function(X).max():.3f}]")





if __name__ == "__main__":

    demo()


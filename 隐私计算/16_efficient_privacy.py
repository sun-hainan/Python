# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 16_efficient_privacy



本文件实现 16_efficient_privacy 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

from dataclasses import dataclass

import math





@dataclass

class PrivacyConfig:

    """隐私配置"""

    epsilon: float = 1.0

    delta: float = 1e-5

    sensitivity: float = 1.0





class PrivacyPreservingLinearRegression:

    """

    隐私保护线性回归



    使用目标扰动(Target Perturbation)方法:

    在目标函数中添加差分隐私噪声来实现隐私保护

    """



    def __init__(self, config: PrivacyConfig = None):

        """

        初始化



        Args:

            config: 隐私配置

        """

        self.config = config or PrivacyConfig()

        self.weights = None



    def fit(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:

        """

        训练模型



        Args:

            X: 特征矩阵 (n_samples, n_features)

            y: 目标向量 (n_samples,)



        Returns:

            训练后的权重

        """

        n_samples, n_features = X.shape



        # 添加偏置项

        X_with_bias = np.column_stack([np.ones(n_samples), X])



        # 计算敏感度

        sensitivity = 2.0 / (n_samples * self.config.sensitivity)



        # 添加噪声到损失函数

        noise_scale = sensitivity / self.config.epsilon

        noise = np.random.normal(0, noise_scale, n_features + 1)



        # 闭式解: w = (X^T X + noise)^{-1} X^T y

        XtX = X_with_bias.T @ X_with_bias

        Xty = X_with_bias.T @ y



        # 添加噪声到X^T X的对角线(简化)

        noisy_XtX = XtX + np.diag(noise)



        # 求解

        try:

            self.weights = np.linalg.solve(noisy_XtX, Xty)

        except np.linalg.LinAlgError:

            # 如果矩阵奇异,使用伪逆

            self.weights = np.linalg.lstsq(noisy_XtX, Xty, rcond=None)[0]



        return self.weights



    def predict(self, X: np.ndarray) -> np.ndarray:

        """

        预测



        Args:

            X: 特征矩阵



        Returns:

            预测值

        """

        n_samples = X.shape[0]

        X_with_bias = np.column_stack([np.ones(n_samples), X])

        return X_with_bias @ self.weights





class PrivacyPreservingKMeans:

    """

    隐私保护K-means聚类



    使用差分隐私的K-means++,初始化聚类中心

    """



    def __init__(self, n_clusters: int, config: PrivacyConfig = None, max_iter: int = 100):

        """

        初始化



        Args:

            n_clusters: 聚类数

            config: 隐私配置

            max_iter: 最大迭代次数

        """

        self.n_clusters = n_clusters

        self.config = config or PrivacyConfig()

        self.max_iter = max_iter

        self.centers = None

        self.labels = None



    def _initialize_centers(self, X: np.ndarray) -> np.ndarray:

        """

        隐私保护的中心初始化



        使用指数机制选择第一个中心,

        之后基于距离的平方概率分布



        Args:

            X: 数据



        Returns:

            初始聚类中心

        """

        n_samples = X.shape[0]

        centers = []



        # 选择第一个中心(使用隐私保护采样)

        first_idx = np.random.randint(0, n_samples)

        centers.append(X[first_idx])



        # 选择剩余中心

        for _ in range(1, self.n_clusters):

            # 计算到最近中心的距离平方

            distances = np.array([

                min(np.linalg.norm(x - c) ** 2 for c in centers)

                for x in X

            ])



            # 添加拉普拉斯噪声到距离

            noise_scale = 2.0 / (self.config.epsilon * self.config.sensitivity)

            noisy_distances = distances + np.random.laplace(0, noise_scale, n_samples)



            # 指数机制采样

            probabilities = np.exp(noisy_distances / (2 * noise_scale))

            probabilities /= probabilities.sum()



            next_idx = np.random.choice(n_samples, p=probabilities)

            centers.append(X[next_idx])



        return np.array(centers)



    def fit(self, X: np.ndarray) -> np.ndarray:

        """

        训练



        Args:

            X: 数据 (n_samples, n_features)



        Returns:

            聚类标签

        """

        n_samples = X.shape[0]



        # 初始化中心

        self.centers = self._initialize_centers(X)



        for iteration in range(self.max_iter):

            # 分配点到最近中心

            distances = np.array([

                [np.linalg.norm(x - c) for c in self.centers]

                for x in X

            ])

            self.labels = np.argmin(distances, axis=1)



            # 更新中心

            new_centers = np.zeros_like(self.centers)

            for k in range(self.n_clusters):

                cluster_points = X[self.labels == k]

                if len(cluster_points) > 0:

                    # 添加噪声到中心

                    noise_scale = 2.0 / (self.config.epsilon * self.config.sensitivity)

                    new_centers[k] = np.mean(cluster_points, axis=0) + \

                                     np.random.laplace(0, noise_scale, X.shape[1])

                else:

                    new_centers[k] = self.centers[k]



            # 检查收敛

            if np.linalg.norm(new_centers - self.centers) < 1e-6:

                break



            self.centers = new_centers



        return self.labels



    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测"""

        distances = np.array([

            [np.linalg.norm(x - c) for c in self.centers]

            for x in X

        ])

        return np.argmin(distances, axis=1)





class PrivacyPreservingDecisionTree:

    """

    隐私保护决策树



    在节点分裂时使用差分隐私

    """



    def __init__(self, max_depth: int = 5, config: PrivacyConfig = None):

        """

        初始化



        Args:

            max_depth: 最大深度

            config: 隐私配置

        """

        self.max_depth = max_depth

        self.config = config or PrivacyConfig()

        self.tree = None



    def _compute_gain(self, X: np.ndarray, y: np.ndarray, feature_idx: int, threshold: float) -> float:

        """

        计算分裂增益



        Args:

            X: 特征

            y: 标签

            feature_idx: 特征索引

            threshold: 阈值



        Returns:

            信息增益

        """

        # 计算父节点熵

        parent_entropy = self._entropy(y)



        # 分裂

        left_mask = X[:, feature_idx] < threshold

        right_mask = ~left_mask



        if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:

            return 0.0



        # 子节点熵

        n = len(y)

        n_left = np.sum(left_mask)

        n_right = np.sum(right_mask)



        child_entropy = (n_left / n) * self._entropy(y[left_mask]) + \

                        (n_right / n) * self._entropy(y[right_mask])



        return parent_entropy - child_entropy



    def _entropy(self, y: np.ndarray) -> float:

        """计算熵"""

        if len(y) == 0:

            return 0.0



        counts = np.bincount(y.astype(int))

        probabilities = counts / len(y)

        probabilities = probabilities[probabilities > 0]



        return -np.sum(probabilities * np.log2(probabilities))



    def _best_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[int, float, float]:

        """

        找到最佳分裂



        使用隐私保护的增益计算



        Returns:

            (特征索引, 阈值, 增益)

        """

        n_features = X.shape[1]

        best_gain = -1

        best_feature = 0

        best_threshold = 0.0



        noise_scale = 2.0 / (self.config.epsilon * self.config.sensitivity)



        for feature_idx in range(n_features):

            # 采样阈值

            thresholds = np.percentile(X[:, feature_idx], [25, 50, 75])



            for threshold in thresholds:

                gain = self._compute_gain(X, y, feature_idx, threshold)



                # 添加噪声

                noisy_gain = gain + np.random.laplace(0, noise_scale)



                if noisy_gain > best_gain:

                    best_gain = noisy_gain

                    best_feature = feature_idx

                    best_threshold = threshold



        return best_feature, best_threshold, best_gain



    def fit(self, X: np.ndarray, y: np.ndarray):

        """

        训练



        Args:

            X: 特征矩阵

            y: 标签

        """

        self.tree = self._build_tree(X, y, depth=0)

        return self



    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> Dict:

        """递归构建树"""

        # 停止条件

        if depth >= self.max_depth or len(np.unique(y)) == 1:

            return {"leaf": True, "class": np.bincount(y.astype(int)).argmax()}



        # 找最佳分裂

        feature_idx, threshold, gain = self._best_split(X, y)



        if gain <= 0:

            return {"leaf": True, "class": np.bincount(y.astype(int)).argmax()}



        # 分裂数据

        left_mask = X[:, feature_idx] < threshold

        right_mask = ~left_mask



        return {

            "leaf": False,

            "feature": feature_idx,

            "threshold": threshold,

            "left": self._build_tree(X[left_mask], y[left_mask], depth + 1),

            "right": self._build_tree(X[right_mask], y[right_mask], depth + 1)

        }



    def predict_single(self, x: np.ndarray, tree: Dict) -> int:

        """预测单个样本"""

        if tree["leaf"]:

            return tree["class"]



        if x[tree["feature"]] < tree["threshold"]:

            return self.predict_single(x, tree["left"])

        else:

            return self.predict_single(x, tree["right"])



    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测"""

        return np.array([self.predict_single(x, self.tree) for x in X])





class PrivacyPreservingRecommender:

    """

    隐私保护推荐系统



    使用差分隐私的协同过滤

    """



    def __init__(self, n_factors: int = 10, config: PrivacyConfig = None):

        """

        初始化



        Args:

            n_factors: 隐因子数量

            config: 隐私配置

        """

        self.n_factors = n_factors

        self.config = config or PrivacyConfig()

        self.user_factors = None

        self.item_factors = None



    def fit(self, ratings: np.ndarray, n_users: int, n_items: int, n_epochs: int = 10) -> None:

        """

        训练



        Args:

            ratings: 评分矩阵 (n_ratings, 3) 包含 (user, item, rating)

            n_users: 用户数

            n_items: 物品数

            n_epochs: 训练轮数

        """

        np.random.seed(42)



        # 初始化因子

        self.user_factors = np.random.randn(n_users, self.n_factors) * 0.1

        self.item_factors = np.random.randn(n_items, self.n_factors) * 0.1



        lr = 0.01

        noise_scale = 2.0 / (self.config.epsilon * self.config.sensitivity)



        for epoch in range(n_epochs):

            for user, item, rating in ratings:

                user, item, rating = int(user), int(item), float(rating)



                # 预测

                pred = np.dot(self.user_factors[user], self.item_factors[item])



                # 误差

                error = rating - pred



                # 更新因子

                self.user_factors[user] += lr * (error * self.item_factors[item])

                self.item_factors[item] += lr * (error * self.user_factors[user])



                # 添加噪声

                self.user_factors[user] += np.random.laplace(0, noise_scale, self.n_factors)

                self.item_factors[item] += np.random.laplace(0, noise_scale, self.n_factors)



    def predict(self, user: int, item: int) -> float:

        """预测评分"""

        return np.dot(self.user_factors[user], self.item_factors[item])





def efficient_privacy_demo():

    """

    高效隐私计算演示

    """



    print("高效隐私计算算法演示")

    print("=" * 60)



    np.random.seed(42)



    # 1. 隐私保护线性回归

    print("\n1. 隐私保护线性回归")

    config = PrivacyConfig(epsilon=1.0)



    X = np.random.randn(200, 5)

    y = X @ np.array([1, -2, 0.5, 3, -1]) + np.random.randn(200) * 0.1



    model = PrivacyPreservingLinearRegression(config)

    weights = model.fit(X, y)



    print(f"   真实系数: [1, -2, 0.5, 3, -1]")

    print(f"   训练系数: {weights[1:]}")  # 跳过偏置

    print(f"   预测MSE: {np.mean((model.predict(X) - y) ** 2):.4f}")



    # 2. 隐私保护K-means

    print("\n2. 隐私保护K-means聚类")

    config = PrivacyConfig(epsilon=0.5)



    # 生成三个簇的数据

    cluster1 = np.random.randn(50, 2) + [0, 0]

    cluster2 = np.random.randn(50, 2) + [5, 5]

    cluster3 = np.random.randn(50, 2) + [0, 5]

    X = np.vstack([cluster1, cluster2, cluster3])



    kmeans = PrivacyPreservingKMeans(n_clusters=3, config=config)

    labels = kmeans.fit(X)



    print(f"   聚类标签分布: {np.bincount(labels)}")

    print(f"   中心点: {kmeans.centers[:3]}")



    # 3. 隐私保护决策树

    print("\n3. 隐私保护决策树")

    config = PrivacyConfig(epsilon=1.0)



    # 生成简单的分类数据

    X = np.random.randn(200, 4)

    y = ((X[:, 0] + X[:, 1] > 0) & (X[:, 2] - X[:, 3] > 0)).astype(int)



    tree = PrivacyPreservingDecisionTree(max_depth=3, config=config)

    tree.fit(X, y)



    predictions = tree.predict(X)

    accuracy = np.mean(predictions == y)

    print(f"   分类准确率: {accuracy:.4f}")



    # 4. 隐私保护推荐系统

    print("\n4. 隐私保护协同过滤推荐")

    config = PrivacyConfig(epsilon=0.5)



    # 生成随机评分数据

    n_ratings = 500

    n_users = 20

    n_items = 30



    ratings = []

    for _ in range(n_ratings):

        user = np.random.randint(0, n_users)

        item = np.random.randint(0, n_items)

        rating = np.random.randint(1, 6)

        ratings.append((user, item, rating))



    ratings = np.array(ratings)



    recommender = PrivacyPreservingRecommender(n_factors=5, config=config)

    recommender.fit(ratings, n_users, n_items)



    # 预测

    test_user = 0

    test_item = 1

    pred_rating = recommender.predict(test_user, test_item)

    print(f"   用户{test_user}对物品{test_item}的预测评分: {pred_rating:.2f}")





if __name__ == "__main__":

    efficient_privacy_demo()



    print("\n" + "=" * 60)

    print("高效隐私计算演示完成!")

    print("=" * 60)


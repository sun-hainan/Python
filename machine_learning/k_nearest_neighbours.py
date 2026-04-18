"""
K近邻算法 (K-Nearest Neighbours, kNN) - 中文注释版
==========================================

算法原理：
    kNN 是一个简单、直观的分类算法。
    对于一个新样本，根据其 K 个最近邻的类别投票决定它的类别。

核心思想：
    "物以类聚，人以群分"
    - 找出新样本在特征空间中最近的 K 个邻居
    - 这 K 个邻居中出现最多的类别，就是新样本的类别

距离度量：
    最常用的是欧几里得距离：
    dist(a, b) = √(Σ(a_i - b_i)²)

算法步骤：
    1. 计算新样本与所有训练样本的距离
    2. 按距离从小到大排序
    3. 取前 K 个最近的邻居
    4. 统计这 K 个邻居的类别，投票决定

超参数 K 的选择：
    - K 太小：容易受噪声影响，可能过拟合
    - K 太大：可能包含太多其他类别的点，欠拟合
    - 通常选择奇数来避免平票

特点：
    - 无模型（non-parametric）：不需要训练，直接存储数据
    - 惰性学习（lazy learning）：直到预测时才计算
    - 时间复杂度 O(n)：每次预测都要遍历所有数据

应用场景：
    - 推荐系统
    - 图像分类
    - 异常检测
"""

from collections import Counter
from heapq import nsmallest
import numpy as np


class KNN:
    def __init__(self, train_data, train_target, class_labels):
        """
        初始化 kNN 分类器

        参数:
            train_data: 训练数据特征
            train_target: 训练数据标签
            class_labels: 类别标签列表
        """
        self.data = zip(train_data, train_target)
        self.labels = class_labels

    @staticmethod
    def _euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
        """
        计算欧几里得距离

        示例:
            >>> KNN._euclidean_distance(np.array([0, 0]), np.array([3, 4]))
            5.0
        """
        return float(np.linalg.norm(a - b))

    def classify(self, pred_point: np.ndarray, k: int = 5) -> str:
        """
        kNN 分类

        参数:
            pred_point: 要分类的新样本
            k: 近邻数量（默认5）

        返回:
            预测的类别标签
        """
        # 1. 计算新样本与所有训练样本的距离
        distances = (
            (self._euclidean_distance(data_point[0], pred_point), data_point[1])
            for data_point in self.data
        )

        # 2. 取 K 个最近的邻居
        votes = (i[1] for i in nsmallest(k, distances))

        # 3. 投票：统计各类别出现的次数
        result = Counter(votes).most_common(1)[0][0]
        return self.labels[result]


if __name__ == "__main__":
    from sklearn import datasets
    from sklearn.model_selection import train_test_split

    # 加载鸢尾花数据集
    iris = datasets.load_iris()
    X = np.array(iris["data"])
    y = np.array(iris["target"])
    iris_classes = iris["target_names"]

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

    # 创建一个样本点进行预测
    iris_point = np.array([4.4, 3.1, 1.3, 1.4])

    # 使用 kNN 分类
    knn = KNN(X_train, y_train, iris_classes)
    result = knn.classify(iris_point, k=3)

    print(f"预测类别: {result}")
    print(f"特征: {iris_point}")
    print(f"真实类别: {iris_classes[y_test[0]]}")

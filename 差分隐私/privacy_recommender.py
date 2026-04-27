# -*- coding: utf-8 -*-
"""
算法实现：差分隐私 / privacy_recommender

本文件实现 privacy_recommender 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class PrivacyPreservingRecommender:
    """隐私保护推荐"""

    def __init__(self, n_users: int, n_items: int, epsilon: float = 1.0):
        """
        参数：
            n_users: 用户数
            n_items: 物品数
            epsilon: 隐私预算
        """
        self.n_users = n_users
        self.n_items = n_items
        self.epsilon = epsilon

    def generate_noisy_rating(self, user_id: int, item_id: int,
                            true_rating: float) -> float:
        """
        生成带噪声的评分

        参数：
            user_id: 用户ID
            item_id: 物品ID
            true_rating: 真实评分

        返回：噪声评分
        """
        # 敏感度 = 最大评分 - 最小评分
        sensitivity = 5.0 - 1.0

        # Laplace噪声
        scale = sensitivity / self.epsilon

        noise = np.random.laplace(0, scale)

        return true_rating + noise

    def aggregate_ratings(self, ratings: List[Tuple[int, int, float]]) -> np.ndarray:
        """
        聚合评分矩阵

        参数：
            ratings: (用户, 物品, 评分) 列表

        返回：评分矩阵
        """
        matrix = np.zeros((self.n_users, self.n_items))

        for user, item, rating in ratings:
            if 0 <= user < self.n_users and 0 <= item < self.n_items:
                matrix[user, item] = rating

        return matrix

    def matrix_factorization(self, ratings: np.ndarray,
                           n_factors: int = 10,
                           n_iterations: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        矩阵分解（带DP）

        参数：
            ratings: 评分矩阵
            n_factors: 隐因子数
            n_iterations: 迭代次数

        返回：(用户矩阵, 物品矩阵)
        """
        # 简化的ALS
        n_users, n_items = ratings.shape

        # 随机初始化
        U = np.random.randn(n_users, n_factors) * 0.1
        V = np.random.randn(n_items, n_factors) * 0.1

        # 迭代
        for iteration in range(n_iterations):
            # 更新U
            for u in range(n_users):
                items_rated = ratings[u] != 0
                if items_rated.sum() > 0:
                    V_rated = V[items_rated]
                    ratings_u = ratings[u, items_rated]

                    # 加噪声的更新
                    grad = (V_rated.T @ (U[u] @ V_rated - ratings_u)) / items_rated.sum()
                    noise = np.random.laplace(0, 0.1 / self.epsilon, grad.shape)
                    grad += noise

                    U[u] -= 0.01 * grad

            # 更新V
            for i in range(n_items):
                users_rated = ratings[:, i] != 0
                if users_rated.sum() > 0:
                    U_rated = U[users_rated]
                    ratings_i = ratings[users_rated, i]

                    grad = (U_rated.T @ (U_rated @ V[i] - ratings_i)) / users_rated.sum()
                    noise = np.random.laplace(0, 0.1 / self.epsilon, grad.shape)
                    grad += noise

                    V[i] -= 0.01 * grad

        return U, V


def privacy_recommender_tradeoff():
    """隐私推荐权衡"""
    print("=== 隐私推荐权衡 ===")
    print()
    print("隐私技术：")
    print("  - 本地差分隐私")
    print("  - 安全聚合")
    print("  - 联邦学习")
    print()
    print("效用损失：")
    print("  - 添加噪声降低准确性")
    print("  - 但整体推荐仍然有效")
    print()
    print("实践建议：")
    print("  - 聚合后加噪声")
    print("  - 只对高活跃用户加噪")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 隐私保护推荐测试 ===\n")

    np.random.seed(42)

    # 简单设置
    n_users, n_items = 10, 20
    recommender = PrivacyPreservingRecommender(n_users, n_items, epsilon=0.5)

    print(f"用户: {n_users}, 物品: {n_items}")
    print(f"隐私预算: ε = 0.5")
    print()

    # 生成一些评分
    ratings = []
    for u in range(n_users):
        for i in range(n_items):
            if np.random.random() > 0.7:
                true_rating = np.random.randint(1, 6)
                noisy_rating = recommender.generate_noisy_rating(u, i, true_rating)
                ratings.append((u, i, noisy_rating))

    print(f"评分数量: {len(ratings)}")

    # 聚合
    matrix = recommender.aggregate_ratings(ratings)

    print(f"评分矩阵稀疏度: {(matrix != 0).sum() / (n_users * n_items) * 100:.1f}%")
    print()

    # 矩阵分解
    U, V = recommender.matrix_factorization(matrix, n_factors=5, n_iterations=10)

    print(f"用户矩阵: {U.shape}")
    print(f"物品矩阵: {V.shape}")

    print()
    privacy_recommender_tradeoff()

    print()
    print("说明：")
    print("  - 隐私保护推荐越来越重要")
    print("  - 差分隐私是主要技术")
    print("  - 需要平衡隐私和效用")

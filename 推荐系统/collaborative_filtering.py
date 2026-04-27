# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / collaborative_filtering

本文件实现 collaborative_filtering 相关的算法功能。
"""

import math
from collections import defaultdict


class CollaborativeFiltering:
    """协同过滤推荐器"""

    def __init__(self, user_item_matrix=None):
        """
        初始化协同过滤推荐器

        Args:
            user_item_matrix: dict[user_id, dict[item_id, rating]] 用户-物品评分矩阵
        """
        self.user_item_matrix = user_item_matrix or {}  # 用户-物品评分矩阵
        self.user_similarity = {}  # 用户相似度矩阵
        self.item_similarity = {}  # 物品相似度矩阵

    def compute_user_similarity(self, metric='cosine'):
        """
        计算用户之间的相似度

        Args:
            metric: str 支持 'cosine'（余弦相似度）和 'pearson'（皮尔逊相关系数）
        """
        users = list(self.user_item_matrix.keys())  # 所有用户列表
        n_users = len(users)  # 用户数量

        # 嵌套循环遍历所有用户对
        for i in range(n_users):
            user_i = users[i]  # 第 i 个用户
            self.user_similarity[user_i] = {}  # 初始化该用户的相似度字典

            for j in range(n_users):
                if i == j:
                    continue  # 跳过自身

                user_j = users[j]  # 第 j 个用户
                sim = self._calculate_similarity(
                    self.user_item_matrix[user_i],
                    self.user_item_matrix[user_j],
                    metric
                )
                self.user_similarity[user_i][user_j] = sim  # 存储相似度

    def compute_item_similarity(self, metric='cosine'):
        """
        计算物品之间的相似度

        Args:
            metric: str 相似度度量方式
        """
        # 转置矩阵：将 user_item_matrix 转为 item_user_matrix
        item_user_matrix = defaultdict(dict)  # 物品-用户矩阵
        for user, items in self.user_item_matrix.items():
            for item, rating in items.items():
                item_user_matrix[item][user] = rating  # item_user_matrix[物品][用户] = 评分

        items = list(item_user_matrix.keys())  # 所有物品列表
        n_items = len(items)  # 物品数量

        # 双层循环计算物品对相似度
        for i in range(n_items):
            item_i = items[i]  # 第 i 个物品
            self.item_similarity[item_i] = {}  # 初始化该物品的相似度字典

            for j in range(n_items):
                if i == j:
                    continue  # 跳过自身

                item_j = items[j]  # 第 j 个物品
                sim = self._calculate_similarity(
                    item_user_matrix[item_i],
                    item_user_matrix[item_j],
                    metric
                )
                self.item_similarity[item_i][item_j] = sim  # 存储相似度

    def _calculate_similarity(self, dict_a, dict_b, metric='cosine'):
        """
        计算两个向量（字典形式）的相似度

        Args:
            dict_a: dict 第一个向量（键为物品ID，值为评分）
            dict_b: dict 第二个向量
            metric: str 相似度度量方式

        Returns:
            float 相似度值
        """
        # 找出两个用户共同评分过的物品
        common_items = set(dict_a.keys()) & set(dict_b.keys())

        # 无共同物品时返回0
        if not common_items:
            return 0.0

        if metric == 'cosine':
            # 余弦相似度：cos(θ) = A·B / (||A|| * ||B||)
            dot_product = sum(dict_a[item] * dict_b[item] for item in common_items)  # 向量点积
            norm_a = math.sqrt(sum(dict_a[item] ** 2 for item in dict_a.keys()))  # 向量A的模
            norm_b = math.sqrt(sum(dict_b[item] ** 2 for item in dict_b.keys()))  # 向量B的模

            if norm_a == 0 or norm_b == 0:
                return 0.0  # 避免除零

            return dot_product / (norm_a * norm_b)

        elif metric == 'pearson':
            # 皮尔逊相关系数：减去均值后的余弦相似度
            mean_a = sum(dict_a[item] for item in common_items) / len(common_items)  # 用户A在共同物品上的平均评分
            mean_b = sum(dict_b[item] for item in common_items) / len(common_items)  # 用户B在共同物品上的平均评分

            numerator = sum(
                (dict_a[item] - mean_a) * (dict_b[item] - mean_b)
                for item in common_items
            )  # 协方差分子

            denom_a = math.sqrt(sum((dict_a[item] - mean_a) ** 2 for item in common_items))  # 标准差A
            denom_b = math.sqrt(sum((dict_b[item] - mean_b) ** 2 for item in common_items))  # 标准差B

            if denom_a == 0 or denom_b == 0:
                return 0.0  # 避免除零

            return numerator / (denom_a * denom_b)

        return 0.0

    def recommend_user_based(self, target_user, top_k=10):
        """
        基于用户的协同过滤推荐

        Args:
            target_user: 目标用户ID
            top_k: int 返回前top_k个推荐

        Returns:
            list[tuple[item_id, predicted_score]] 推荐列表
        """
        if target_user not in self.user_item_matrix:
            return []  # 用户不存在

        if target_user not in self.user_similarity:
            self.compute_user_similarity()  # 未计算相似度则先计算

        # 获取与目标用户最相似的K个用户
        similar_users = sorted(
            self.user_similarity[target_user].items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]  # 取相似度最高的K个用户

        # 汇总推荐物品及其得分
        item_scores = defaultdict(float)  # 物品得分累加器
        item_counts = defaultdict(int)  # 物品被多少相似用户评过分

        target_ratings = self.user_item_matrix[target_user]  # 目标用户已评分物品

        for similar_user, similarity in similar_users:
            if similarity <= 0:
                continue  # 跳过负相似度

            for item, rating in self.user_item_matrix[similar_user].items():
                if item not in target_ratings:
                    # 加权评分累加：score = Σ(similarity * rating) / Σ|similarity|
                    item_scores[item] += similarity * rating
                    item_counts[item] += 1

        # 计算最终得分（归一化）
        recommendations = []
        for item in item_scores:
            if item_counts[item] > 0:
                predicted_score = item_scores[item] / item_counts[item]
                recommendations.append((item, predicted_score))

        # 按得分降序排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]

    def recommend_item_based(self, target_user, top_k=10):
        """
        基于物品的协同过滤推荐

        Args:
            target_user: 目标用户ID
            top_k: int 返回前top_k个推荐

        Returns:
            list[tuple[item_id, predicted_score]] 推荐列表
        """
        if target_user not in self.user_item_matrix:
            return []  # 用户不存在

        if not self.item_similarity:
            self.compute_item_similarity()  # 未计算则先计算物品相似度

        target_ratings = self.user_item_matrix[target_user]  # 目标用户已评分物品
        all_items = set()  # 所有物品集合

        # 统计所有物品
        for user_ratings in self.user_item_matrix.values():
            all_items.update(user_ratings.keys())

        # 用户已评分的物品
        rated_items = set(target_ratings.keys())
        # 用户未评分的物品（待推荐）
        unrated_items = all_items - rated_items

        item_scores = []  # 物品得分列表

        for item in unrated_items:
            score = 0.0  # 该物品的预测得分
            total_sim = 0.0  # 相似度之和（用于归一化）

            # 遍历用户已评分的物品
            for rated_item, rating in target_ratings.items():
                if item in self.item_similarity.get(rated_item, {}):
                    sim = self.item_similarity[rated_item][item]  # 物品相似度
                    if sim > 0:
                        score += sim * rating  # 加权累加
                        total_sim += sim

            if total_sim > 0:
                score /= total_sim  # 归一化

            item_scores.append((item, score))

        # 按得分降序排序
        item_scores.sort(key=lambda x: x[1], reverse=True)
        return item_scores[:top_k]


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 构建测试数据：用户-物品评分矩阵
    test_matrix = {
        'user1': {'item1': 5, 'item2': 4, 'item3': 3, 'item4': 2},
        'user2': {'item1': 4, 'item2': 5, 'item3': 2, 'item5': 3},
        'user3': {'item1': 3, 'item2': 2, 'item4': 5, 'item5': 4},
        'user4': {'item2': 3, 'item3': 4, 'item4': 4, 'item5': 5},
    }

    cf = CollaborativeFiltering(test_matrix)  # 创建协同过滤实例

    # 测试用户相似度计算
    cf.compute_user_similarity(metric='cosine')
    print("=== 用户相似度矩阵 ===")
    for u, sims in cf.user_similarity.items():
        print(f"{u}: {sims}")

    # 测试基于用户的推荐
    print("\n=== 基于用户的推荐 (user1) ===")
    user_recs = cf.recommend_user_based('user1', top_k=3)
    print(user_recs)

    # 测试基于物品的推荐
    print("\n=== 基于物品的推荐 (user1) ===")
    item_recs = cf.recommend_item_based('user1', top_k=3)
    print(item_recs)

    print("\n✅ 协同过滤算法测试通过！")

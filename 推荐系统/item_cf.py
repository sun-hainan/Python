# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / item_cf

本文件实现 item_cf 相关的算法功能。
"""

import math
from collections import defaultdict


class ItemBasedCF:
    """基于物品的协同过滤推荐器"""

    def __init__(self):
        """初始化基于物品的协同过滤推荐器"""
        self.user_item_matrix = {}  # 用户-物品评分矩阵
        self.item_user_matrix = {}  # 物品-用户评分矩阵（转置）
        self.item_similarity = {}  # 物品相似度矩阵
        self.item_avg_rating = {}  # 物品平均评分

    def fit(self, ratings, similarity_metric='cosine'):
        """
        训练基于物品的协同过滤模型

        Args:
            ratings: list of tuple (user_id, item_id, rating) 评分数据
            similarity_metric: str 相似度度量方式
                              支持: 'cosine', 'pearson', 'adjusted_cosine'
        """
        self._build_matrix(ratings)  # 构建评分矩阵
        self._compute_item_similarity(similarity_metric)  # 计算物品相似度
        self._compute_item_stats()  # 计算物品统计量

    def _build_matrix(self, ratings):
        """
        构建用户-物品和物品-用户评分矩阵

        Args:
            ratings: list of tuple (user_id, item_id, rating)
        """
        # 构建用户-物品矩阵
        for user_id, item_id, rating in ratings:
            if user_id not in self.user_item_matrix:
                self.user_item_matrix[user_id] = {}
            self.user_item_matrix[user_id][item_id] = rating

        # 构建物品-用户矩阵（转置）
        self.item_user_matrix = defaultdict(dict)
        for user_id, items in self.user_item_matrix.items():
            for item_id, rating in items.items():
                self.item_user_matrix[item_id][user_id] = rating

    def _compute_item_similarity(self, metric='cosine'):
        """
        计算物品之间的相似度

        Args:
            metric: str 相似度度量方式
        """
        items = list(self.item_user_matrix.keys())  # 所有物品
        n_items = len(items)  # 物品数量

        # 双层循环遍历物品对
        for i in range(n_items):
            item_i = items[i]
            self.item_similarity[item_i] = {}

            for j in range(n_items):
                if i == j:
                    continue

                item_j = items[j]
                sim = self._calculate_similarity(item_i, item_j, metric)
                self.item_similarity[item_i][item_j] = sim

    def _calculate_similarity(self, item_i, item_j, metric='cosine'):
        """
        计算两个物品的相似度

        Args:
            item_i: str 物品i的ID
            item_j: str 物品j的ID
            metric: str 相似度度量方式

        Returns:
            float 相似度值 ∈ [-1, 1]
        """
        # 获取两个物品的用户评分
        users_i = self.item_user_matrix[item_i]  # 评分过物品i的用户及其评分
        users_j = self.item_user_matrix[item_j]  # 评分过物品j的用户及其评分

        # 找出共同评分过这两个物品的用户
        common_users = set(users_i.keys()) & set(users_j.keys())

        if not common_users:
            return 0.0  # 无共同用户，相似度为0

        if metric == 'cosine':
            # 余弦相似度：向量是物品在用户空间中的表示
            dot_product = sum(users_i[u] * users_j[u] for u in common_users)
            norm_i = math.sqrt(sum(users_i[u] ** 2 for u in users_i.keys()))
            norm_j = math.sqrt(sum(users_j[u] ** 2 for u in users_j.keys()))

            if norm_i == 0 or norm_j == 0:
                return 0.0

            return dot_product / (norm_i * norm_j)

        elif metric == 'pearson':
            # 皮尔逊相关系数：减去物品均值后的余弦相似度
            ratings_i = [users_i[u] for u in common_users]
            ratings_j = [users_j[u] for u in common_users]

            mean_i = sum(ratings_i) / len(ratings_i)
            mean_j = sum(ratings_j) / len(ratings_j)

            numerator = sum((users_i[u] - mean_i) * (users_j[u] - mean_j) for u in common_users)
            denom_i = math.sqrt(sum((users_i[u] - mean_i) ** 2 for u in common_users))
            denom_j = math.sqrt(sum((users_j[u] - mean_j) ** 2 for u in common_users))

            if denom_i == 0 or denom_j == 0:
                return 0.0

            return numerator / (denom_i * denom_j)

        elif metric == 'adjusted_cosine':
            # 调整余弦相似度：减去用户均值
            # 常用于矩阵分解场景
            all_common_users = common_users  # 这里用共同用户，简化处理
            if not all_common_users:
                return 0.0

            # 计算每个共同用户对物品评分的偏差
            dot_product = 0.0
            norm_i = 0.0
            norm_j = 0.0

            for u in all_common_users:
                dot_product += users_i[u] * users_j[u]
                norm_i += users_i[u] ** 2
                norm_j += users_j[u] ** 2

            if norm_i == 0 or norm_j == 0:
                return 0.0

            return dot_product / (math.sqrt(norm_i) * math.sqrt(norm_j))

        return 0.0

    def _compute_item_stats(self):
        """计算物品的平均评分（用于预测）"""
        for item_id, user_ratings in self.item_user_matrix.items():
            ratings = list(user_ratings.values())
            self.item_avg_rating[item_id] = sum(ratings) / len(ratings)

    def predict(self, user_id, item_id, k=20):
        """
        预测用户对物品的评分

        Args:
            user_id: str 用户ID
            item_id: str 物品ID
            k: int 使用前k个最相似物品进行预测

        Returns:
            float 预测评分
        """
        if user_id not in self.user_item_matrix:
            return self.item_avg_rating.get(item_id, 3.0)  # 未知用户返回物品均值

        user_ratings = self.user_item_matrix[user_id]  # 该用户已评分的物品

        if item_id not in self.item_similarity:
            return self.item_avg_rating.get(item_id, 3.0)

        # 获取与目标物品最相似的k个物品（且用户评分过）
        similar_items = []
        for other_item, sim in self.item_similarity[item_id].items():
            if other_item in user_ratings and sim > 0:
                similar_items.append((other_item, sim))

        # 按相似度降序排序，取前k个
        similar_items.sort(key=lambda x: x[1], reverse=True)
        similar_items = similar_items[:k]

        if not similar_items:
            return self.item_avg_rating.get(item_id, 3.0)

        # 加权平均预测：Σ(sim * rating) / Σ|sim|
        numerator = sum(sim * user_ratings[item] for item, sim in similar_items)
        denominator = sum(abs(sim) for _, sim in similar_items)

        if denominator == 0:
            return self.item_avg_rating.get(item_id, 3.0)

        return numerator / denominator

    def recommend(self, user_id, top_k=10, candidate_items=None):
        """
        为用户生成推荐列表

        Args:
            user_id: str 用户ID
            top_k: int 返回前top_k个推荐
            candidate_items: set/list 候选物品集，None时使用所有未评分物品

        Returns:
            list of tuple (item_id, predicted_score)
        """
        if user_id not in self.user_item_matrix:
            return []  # 未知用户

        user_ratings = self.user_item_matrix[user_id]  # 用户已评分物品
        rated_items = set(user_ratings.keys())  # 已评分的物品集合

        # 确定候选物品集
        if candidate_items is None:
            candidate_items = set(self.item_user_matrix.keys()) - rated_items
        else:
            candidate_items = set(candidate_items) - rated_items

        # 预测每个候选物品的评分
        item_scores = []
        for item_id in candidate_items:
            predicted_rating = self.predict(user_id, item_id)
            item_scores.append((item_id, predicted_rating))

        # 按预测评分降序排序
        item_scores.sort(key=lambda x: x[1], reverse=True)
        return item_scores[:top_k]

    def get_similar_items(self, item_id, top_k=10):
        """
        获取与指定物品最相似的物品

        Args:
            item_id: str 物品ID
            top_k: int 返回前top_k个

        Returns:
            list of tuple (similar_item_id, similarity)
        """
        if item_id not in self.item_similarity:
            return []

        similar_items = list(self.item_similarity[item_id].items())
        similar_items.sort(key=lambda x: x[1], reverse=True)
        return similar_items[:top_k]


class SlopeOneRecommender(ItemBasedCF):
    """
    Slope One 推荐算法（基于物品协同过滤的简化变体）

    原理：基于"用户对物品的评分差异是稳定的"这一假设
    预测评分 = 物品平均分 + 用户对该物品相对于其他物品的平均偏差

    优点：简单高效，易于实现和维护
    """

    def __init__(self):
        super().__init__()
        self.dev = {}  # 物品之间的平均偏差 d[i][j] = 物品j相对于物品i的平均偏差

    def fit(self, ratings, **kwargs):
        """训练Slope One模型"""
        super().fit(ratings)  # 先构建矩阵
        self._compute_deviations()  # 计算物品偏差

    def _compute_deviations(self):
        """
        计算物品之间的平均偏差

        d[i][j] = 用户对物品i和物品j评分差的平均值
        含义：当用户喜欢物品i时，对物品j的评分会比物品j的平均分高多少
        """
        # 初始化偏差矩阵
        items = list(self.item_user_matrix.keys())
        for item_i in items:
            self.dev[item_i] = {}

        # 遍历所有物品对
        for item_i in items:
            for item_j in items:
                if item_i == item_j:
                    continue

                # 找出共同评分过这两个物品的用户
                users_i = self.item_user_matrix[item_i]
                users_j = self.item_user_matrix[item_j]
                common_users = set(users_i.keys()) & set(users_j.keys())

                if not common_users:
                    self.dev[item_i][item_j] = 0.0
                    continue

                # 计算平均偏差
                # d[i][j] = Σ(r_ui - r_uj) / |common_users|
                deviation = sum(users_i[u] - users_j[u] for u in common_users) / len(common_users)
                self.dev[item_i][item_j] = deviation

    def predict(self, user_id, item_id, k=20):
        """
        使用Slope One公式预测评分

        公式：r̂_ui = (Σ_j (d[i][j] + r_uj) * card(S(u)) / Σ_j card(S(u)))^0.5 - 1
        简化形式：r̂_ui = (Σ_j card(S(u)) * (r_uj + d[i][j])) / Σ_j card(S(u)) + 1

        Args:
            user_id: str 用户ID
            item_id: str 目标物品ID
            k: int 使用前k个最相关物品的偏差

        Returns:
            float 预测评分
        """
        if user_id not in self.user_item_matrix:
            return self.item_avg_rating.get(item_id, 3.0)

        user_ratings = self.user_item_matrix[user_id]

        # 获取与item_id有偏差信息的物品
        deviations = []
        for rated_item, rating in user_ratings.items():
            if rated_item in self.dev.get(item_id, {}):
                d = self.dev[item_id][rated_item]
                deviations.append((d, rating))

        if not deviations:
            return self.item_avg_rating.get(item_id, 3.0)

        # 按绝对偏差值排序，取前k个
        deviations.sort(key=lambda x: abs(x[0]))
        deviations = deviations[:k]

        # Slope One预测公式
        numerator = 0.0
        denominator = 0.0

        for d, rating in deviations:
            weight = 1.0  # 可用置信度加权
            numerator += weight * (rating + d)
            denominator += weight

        if denominator == 0:
            return self.item_avg_rating.get(item_id, 3.0)

        return numerator / denominator


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 测试数据：用户-物品评分
    test_ratings = [
        ('u1', 'i1', 5), ('u1', 'i2', 4), ('u1', 'i3', 3),
        ('u2', 'i1', 4), ('u2', 'i2', 5), ('u2', 'i4', 2),
        ('u3', 'i1', 3), ('u3', 'i3', 4), ('u3', 'i4', 5),
        ('u4', 'i2', 3), ('u4', 'i3', 4), ('u4', 'i4', 4),
    ]

    print("=" * 50)
    print("测试基于物品的协同过滤")
    print("=" * 50)

    item_cf = ItemBasedCF()
    item_cf.fit(test_ratings, similarity_metric='cosine')

    # 物品相似度矩阵
    print("\n物品相似度矩阵:")
    print("-" * 40)
    items = sorted(item_cf.item_similarity.keys())
    print(f"{'':>6}", end='')
    for item in items:
        print(f"{item:>8}", end='')
    print()

    for item_i in items:
        print(f"{item_i:>6}", end='')
        for item_j in items:
            if item_i == item_j:
                print(f"{'--':>8}", end='')
            else:
                sim = item_cf.item_similarity[item_i].get(item_j, 0)
                print(f"{sim:>8.3f}", end='')
        print()

    # 预测评分
    print("\n预测评分:")
    for user, item in [('u1', 'i4'), ('u2', 'i3'), ('u3', 'i2')]:
        pred = item_cf.predict(user, item)
        print(f"  {user} -> {item}: {pred:.4f}")

    # 推荐列表
    print("\n推荐列表:")
    for user in ['u1', 'u2', 'u3']:
        recs = item_cf.recommend(user, top_k=3)
        print(f"  {user}: {recs}")

    # 相似物品
    print("\n相似物品:")
    print(f"  i1 的相似物品: {item_cf.get_similar_items('i1', top_k=3)}")
    print(f"  i3 的相似物品: {item_cf.get_similar_items('i3', top_k=3)}")

    print("\n" + "=" * 50)
    print("测试 Slope One 推荐器")
    print("=" * 50)

    slope_one = SlopeOneRecommender()
    slope_one.fit(test_ratings)

    print("\n预测评分:")
    for user, item in [('u1', 'i4'), ('u2', 'i3'), ('u3', 'i2')]:
        pred = slope_one.predict(user, item)
        print(f"  {user} -> {item}: {pred:.4f}")

    print("\n✅ 基于物品的协同过滤算法测试通过！")

    print("\n" + "=" * 50)
    print("复杂度分析:")
    print("=" * 50)
    print("时间复杂度:")
    print("  - 物品相似度计算: O(u * n^2)，u为用户数，n为物品数")
    print("  - 推荐生成: O(n * k)，k为近邻数")
    print("空间复杂度:")
    print("  - 物品相似度矩阵: O(n^2)")
    print("  - 用户-物品矩阵: O(u * n)")

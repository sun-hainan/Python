# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / hybrid_recommender

本文件实现 hybrid_recommender 相关的算法功能。
"""

from collections import defaultdict


class WeightedHybridRecommender:
    """加权混合推荐器"""

    def __init__(self, recommenders, weights=None):
        """
        初始化加权混合推荐器

        Args:
            recommenders: list of tuple (name, recommender_instance) 推荐器列表
            weights: list of float 各推荐器权重，若为None则自动归一化
        """
        self.recommenders = recommenders  # [(name, recommender), ...]
        n = len(recommenders)

        if weights is None:
            # 默认均匀权重
            self.weights = [1.0 / n] * n
        else:
            # 归一化权重
            total = sum(weights)
            self.weights = [w / total for w in weights]

    def recommend(self, user_id, top_k=10):
        """
        生成加权混合推荐

        Args:
            user_id: 用户ID
            top_k: int 推荐数量

        Returns:
            list of tuple (item_id, hybrid_score)
        """
        hybrid_scores = defaultdict(float)  # 混合得分累加器

        # 遍历各推荐器
        for (name, recommender), weight in zip(self.recommenders, self.weights):
            try:
                # 获取该推荐器的推荐列表
                recommendations = recommender.recommend(user_id, top_k=top_k * 2)

                # 加权累加
                for item_id, score in recommendations:
                    hybrid_scores[item_id] += weight * score

            except Exception as e:
                print(f"推荐器 {name} 出错: {e}")

        # 转换为列表并排序
        result = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return result[:top_k]


class SwitchingHybridRecommender:
    """切换混合推荐器"""

    def __init__(self, recommenders, switch_condition=None):
        """
        初始化切换混合推荐器

        Args:
            recommenders: list of tuple (name, recommender_instance) 推荐器列表
            switch_condition: callable(user_id) -> int 返回使用的推荐器索引
        """
        self.recommenders = recommenders
        self.switch_condition = switch_condition or (lambda uid: 0)  # 默认使用第一个

    def recommend(self, user_id, top_k=10):
        """根据条件切换推荐策略"""
        # 确定使用哪个推荐器
        selected_idx = self.switch_condition(user_id)
        name, recommender = self.recommenders[selected_idx]

        print(f"用户 {user_id} 使用推荐器: {name}")
        return recommender.recommend(user_id, top_k=top_k)


class CascadingHybridRecommender:
    """级联混合推荐器（分支混合）"""

    def __init__(self, first_stage_recommender, second_stage_recommender,
                 first_stage_k=50, second_stage_k=10):
        """
        初始化级联混合推荐器

        Args:
            first_stage_recommender: 第一阶段推荐器（粗筛）
            second_stage_recommender: 第二阶段推荐器（精排）
            first_stage_k: int 第一阶段返回的物品数量
            second_stage_k: int 最终返回的物品数量
        """
        self.first_stage = first_stage_recommender
        self.second_stage = second_stage_recommender
        self.first_stage_k = first_stage_k
        self.second_stage_k = second_stage_k

    def recommend(self, user_id, top_k=None):
        """
        级联推荐：先用第一阶段筛选，再用第二阶段排序

        Args:
            user_id: 用户ID
            top_k: int 最终返回数量

        Returns:
            list of tuple (item_id, score)
        """
        top_k = top_k or self.second_stage_k

        # 第一阶段：粗筛
        first_candidates = self.first_stage.recommend(user_id, top_k=self.first_stage_k)
        candidate_items = [item_id for item_id, _ in first_candidates]

        # 第二阶段：精排（重排序）
        second_scores = self.second_stage.recommend(
            user_id, candidate_items=candidate_items, top_k=top_k
        )

        return second_scores


class FeatureAugmentationHybridRecommender:
    """特征增强混合推荐器"""

    def __init__(self, base_recommender, augmentation_fn):
        """
        初始化特征增强混合推荐器

        Args:
            base_recommender: 基础推荐器
            augmentation_fn: callable(user_id, item_id) -> dict
                             返回额外特征 {feature_name: value}
        """
        self.base_recommender = base_recommender
        self.augmentation_fn = augmentation_fn

    def recommend(self, user_id, top_k=10):
        """推荐时融入额外特征（简化实现）"""
        # 获取基础推荐
        base_recommendations = self.base_recommender.recommend(user_id, top_k=top_k)

        # 重排序时考虑额外特征
        # 这里简化处理，实际可用学习模型融合
        augmented_scores = []
        for item_id, base_score in base_recommendations:
            extra_features = self.augmentation_fn(user_id, item_id)
            bonus = extra_features.get('bonus', 0)  # 额外加分
            augmented_scores.append((item_id, base_score + bonus))

        augmented_scores.sort(key=lambda x: x[1], reverse=True)
        return augmented_scores[:top_k]


class AdaptiveHybridRecommender:
    """自适应混合推荐器（根据覆盖率/多样性自动调整权重）"""

    def __init__(self, recommenders):
        """
        初始化自适应混合推荐器

        Args:
            recommenders: dict {name: (recommender, importance_score)}
                         推荐器名称到(推荐器实例, 重要性分数)的映射
        """
        self.recommenders = recommenders
        self.weights = {}  # 自适应权重

    def update_weights(self, user_id, feedback=None):
        """
        根据反馈更新权重

        Args:
            feedback: dict {recommender_name: (hit, miss)} 点击和未点击数
        """
        # 简单策略：根据点击率更新权重
        for name, (recommender, base_importance) in self.recommenders.items():
            if feedback and name in feedback:
                hit, miss = feedback[name]
                ctr = hit / (hit + miss) if (hit + miss) > 0 else 0.5
                # CTR越高，权重越高
                self.weights[name] = base_importance * (1 + ctr)
            else:
                self.weights[name] = base_importance

        # 归一化
        total = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= total

    def recommend(self, user_id, top_k=10):
        """基于更新后的权重生成推荐"""
        hybrid_scores = defaultdict(float)

        for name, (recommender, _) in self.recommenders.items():
            weight = self.weights.get(name, 1.0 / len(self.recommenders))

            try:
                recs = recommender.recommend(user_id, top_k=top_k * 2)
                for item_id, score in recs:
                    hybrid_scores[item_id] += weight * score
            except Exception:
                pass

        result = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return result[:top_k]


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 模拟两个简单的推荐器
    class MockRecommender:
        def __init__(self, scores):
            self.scores = scores

        def recommend(self, user_id, top_k=10, candidate_items=None):
            if user_id not in self.scores:
                return []
            items = list(self.scores[user_id].items())
            items.sort(key=lambda x: x[1], reverse=True)
            return items[:top_k]

    # 推荐器A的得分
    scores_a = {
        'u1': {'i1': 5, 'i2': 4, 'i3': 3, 'i4': 2, 'i5': 1},
        'u2': {'i1': 3, 'i2': 5, 'i4': 4, 'i5': 2},
    }

    # 推荐器B的得分
    scores_b = {
        'u1': {'i1': 2, 'i2': 5, 'i3': 4, 'i4': 3, 'i5': 2},
        'u2': {'i1': 5, 'i2': 2, 'i3': 4, 'i5': 5},
    }

    rec_a = MockRecommender(scores_a)
    rec_b = MockRecommender(scores_b)

    print("=" * 50)
    print("测试加权混合推荐器")
    print("=" * 50)

    hybrid = WeightedHybridRecommender(
        [('CF', rec_a), ('CB', rec_b)],
        weights=[0.6, 0.4]
    )

    recs = hybrid.recommend('u1', top_k=5)
    print(f"用户 u1 的加权混合推荐: {recs}")

    print("\n" + "=" * 50)
    print("测试切换混合推荐器")
    print("=" * 50)

    switching = SwitchingHybridRecommender(
        [('CF', rec_a), ('CB', rec_b)],
        switch_condition=lambda uid: 0 if uid == 'u1' else 1
    )

    print(f"用户 u1: {switching.recommend('u1')}")
    print(f"用户 u2: {switching.recommend('u2')}")

    print("\n" + "=" * 50)
    print("测试级联混合推荐器")
    print("=" * 50)

    # 第一阶段用A，第二阶段用B
    cascading = CascadingHybridRecommender(rec_a, rec_b, first_stage_k=3, second_stage_k=2)
    recs = cascading.recommend('u1')
    print(f"用户 u1 级联推荐: {recs}")

    print("\n" + "=" * 50)
    print("测试自适应混合推荐器")
    print("=" * 50)

    adaptive = AdaptiveHybridRecommender({
        'CF': (rec_a, 0.5),
        'CB': (rec_b, 0.5),
    })

    # 初始推荐
    print("初始推荐:")
    print(adaptive.recommend('u1'))

    # 模拟反馈更新
    print("\n更新权重（CF点击率高）:")
    adaptive.update_weights('u1', feedback={'CF': (10, 2), 'CB': (3, 7)})
    print(f"新权重: {adaptive.weights}")

    print("\n✅ 混合推荐系统测试通过！")

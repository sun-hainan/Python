# -*- coding: utf-8 -*-
"""
算法实现：算法统计 / pac_learning

本文件实现 pac_learning 相关的算法功能。
"""

import random
from typing import List, Set, Callable


class PACLearner:
    """PAC学习器"""

    def __init__(self, concept_class: Set):
        """
        参数：
            concept_class: 概念类
        """
        self.concepts = concept_class

    def sample(self, distribution: Callable,
              n_samples: int) -> List:
        """
        从分布中采样

        参数：
            distribution: 采样分布
            n_samples: 样本数

        返回：样本列表
        """
        concepts = list(self.concepts)
        return random.choices(concepts, k=n_samples)

    def empirical_risk(self, hypothesis: Set,
                      samples: List) -> float:
        """
        经验风险

        返回：错误比例
        """
        if not samples:
            return 0.0

        errors = 0
        for sample in samples:
            if sample not in hypothesis:
                errors += 1

        return errors / len(samples)

    def pac_learn(self, target_concept: Set,
                 distribution: Callable,
                 epsilon: float, delta: float) -> Set:
        """
        PAC学习

        参数：
            target_concept: 目标概念
            distribution: 采样分布
            epsilon: 误差参数
            delta: 失败概率

        返回：假设
        """
        # 样本复杂度
        # m ≥ (1/ε) log(1/δ)
        import math
        m = int(math.log(1 / delta) / epsilon)

        # 采样
        samples = self.sample(dist, m)

        # 返回最简单的一致假设
        # 简化：返回样本中最常见概念
        from collections import Counter
        counts = Counter(samples)
        return counts.most_common(1)[0][0]

    def sample_complexity(self, epsilon: float,
                         delta: float) -> int:
        """
        样本复杂度

        返回：需要的样本数
        """
        import math
        return int(math.log(1 / delta) / (epsilon ** 2))


def pac_vs_sq():
    """PAC vs SQ"""
    print("=== PAC vs 统计查询 ===")
    print()
    print("PAC学习：")
    print("  - 可以查询任意样本")
    print("  - 需要随机采样")
    print("  - 更强的模型")
    print()
    print("统计查询（SQ）：")
    print("  - 只能查询统计量")
    print("  - 更弱的模型")
    print("  - PAC ⊇ SQ（PAC更强）")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== PAC学习测试 ===\n")

    random.seed(42)

    # 概念类：所有单点集合
    concepts = {frozenset({i}) for i in range(5)}
    learner = PACLearner(concepts)

    print(f"概念类: {concepts}")
    print()

    # 学习参数
    epsilon = 0.1  # 误差
    delta = 0.1   # 失败概率

    sample_complexity = learner.sample_complexity(epsilon, delta)
    print(f"样本复杂度: {sample_complexity}")

    # 简单分布：均匀
    def uniform():
        return frozenset({random.randint(0, 4)})

    # PAC学习
    target = frozenset({2})
    hypothesis = learner.pac_learn(target, uniform, epsilon, delta)

    print(f"目标概念: {target}")
    print(f"学习假设: {hypothesis}")

    # 评估
    samples = learner.sample(uniform, 1000)
    risk = learner.empirical_risk(hypothesis, samples)
    print(f"经验风险: {risk:.3f}")

    print()
    pac_vs_sq()

    print()
    print("说明：")
    print("  - PAC学习是学习理论的基础")
    print("  - 样本复杂度是关键")
    print("  - 用于分析学习算法")

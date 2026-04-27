# -*- coding: utf-8 -*-
"""
算法实现：算法统计 / agnostic_learning

本文件实现 agnostic_learning 相关的算法功能。
"""

import random
from typing import List, Tuple
from collections import Counter


class AgnosticLearner:
    """不可知学习器"""

    def __init__(self, hypothesis_class_size: int):
        """
        参数：
            hypothesis_class_size: 假设类大小
        """
        self.h_size = hypothesis_class_size

    def empirical_risk_minimization(self, examples: List[Tuple[int, int]]) -> int:
        """
        经验风险最小化（ERM）

        参数：
            examples: 样本 (x, y)

        返回：最佳假设索引
        """
        if not examples:
            return 0

        best_h = 0
        best_error = len(examples) + 1

        # 简化的ERM：随机搜索
        for h in range(min(100, self.h_size)):
            error = sum(1 for x, y in examples if self._predict(h, x) != y)

            if error < best_error:
                best_error = error
                best_h = h

        return best_h

    def _predict(self, h: int, x: int) -> int:
        """简化预测"""
        return (h + x) % 2

    def agnostic_bound(self, m: int, epsilon: float, delta: float) -> float:
        """
        不可知学习的样本复杂度上界

        返回：需要的样本数
        """
        import math

        # 不可知学习的上界
        # log(1/delta) + 假设类描述长度
        bound = (math.log(1 / delta) + self.h_size * math.log(2)) / (2 * epsilon ** 2)

        return bound

    def find_nearest_neighbor(self, examples: List[Tuple[int, int]], x: int) -> int:
        """
        最近邻（不可知学习的简单方法）

        参数：
            examples: 样本
            x: 查询点

        返回：预测标签
        """
        if not examples:
            return 0

        # 找最近邻
        min_dist = float('inf')
        nearest_label = 0

        for ex_x, ex_y in examples:
            dist = abs(ex_x - x)
            if dist < min_dist:
                min_dist = dist
                nearest_label = ex_y

        return nearest_label


def agnostic_vs_pac():
    """不可知 vs PAC"""
    print("=== 不可知学习 vs PAC学习 ===")
    print()
    print("PAC学习：")
    print("  - 假设存在完美概念")
    print("  - 可以达到零错误")
    print("  - 样本复杂度 O(log(1/delta)/epsilon)")
    print()
    print("不可知学习：")
    print("  - 无分布假设")
    print("  - 最优可能犯错")
    print("  - 样本复杂度与最优误差有关")
    print()
    print("关系：")
    print("  - PAC是特殊情况（最优误差=0）")
    print("  - 不可知更一般")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 不可知学习测试 ===\n")

    random.seed(42)

    learner = AgnosticLearner(hypothesis_class_size=50)

    # 生成带噪声的样本
    examples = []
    for x in range(20):
        # 真实函数有噪声
        y = 1 if x > 10 else 0
        if random.random() < 0.3:  # 30%噪声
            y = 1 - y
        examples.append((x, y))

    print(f"样本数: {len(examples)}")
    print(f"样本: {[(x, y) for x, y in examples[:10]]}...")  # 显示前10个
    print()

    # ERM
    best_h = learner.empirical_risk_minimization(examples)

    print(f"ERM找到的最佳假设: h={best_h}")

    # 估计误差
    error = sum(1 for x, y in examples if learner._predict(best_h, x) != y) / len(examples)
    print(f"训练误差: {error:.2f}")
    print()

    # 样本复杂度
    m = learner.agnostic_bound(len(examples), epsilon=0.1, delta=0.1)
    print(f"样本复杂度 (ε=0.1, δ=0.1): {m:.0f}")
    print()

    # 最近邻
    pred = learner.find_nearest_neighbor(examples, x=15)
    print(f"最近邻预测 x=15: {pred}")

    print()
    agnostic_vs_pac()

    print()
    print("说明：")
    print("  - 不可知学习是更现实的学习模型")
    print("  - 实际中数据通常有噪声")
    print("  - 算法如SVM、AdaBoost可解释为不可知学习")

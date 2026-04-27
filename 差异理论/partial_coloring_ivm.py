# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / partial_coloring_ivm



本文件实现 partial_coloring_ivm 相关的算法功能。

"""



import random

import numpy as np

from typing import List, Dict





class PartialColoring:

    """部分着色算法"""



    def __init__(self, n_elements: int):

        """

        参数：

            n_elements: 元素数量

        """

        self.n = n_elements



    def color(self, weights: List[float], target_sum: float = 0.0) -> List[float]:

        """

        部分着色



        目标：找到x_i ∈ {-1, 1} 使得 Σ w_i * x_i ≈ target_sum



        参数：

            weights: 权重w_i

            target_sum: 目标加权和



        返回：着色方案 x_i ∈ {-1, 1}

        """

        n = len(weights)

        x = [0.0] * n



        # 简单随机着色

        for i in range(n):

            x[i] = 1 if random.random() < 0.5 else -1



        # 计算当前和

        current_sum = sum(w * xi for w, xi in zip(weights, x))



        # 调整以接近目标

        if abs(current_sum - target_sum) > 0.5:

            # 贪心调整

            for i in range(n):

                old_xi = x[i]

                x[i] = -x[i]

                new_sum = sum(w * xj for w, xj in zip(weights, x))

                if abs(new_sum - target_sum) < abs(current_sum - target_sum):

                    current_sum = new_sum

                else:

                    x[i] = old_xi



        return x



    def expected_discrepancy(self, weights: List[float]) -> float:

        """

        计算期望差异



        E[|Σ w_i * x_i|] ≤ √(Σ w_i²)

        """

        sum_squares = sum(w ** 2 for w in weights)

        return np.sqrt(sum_squares)





class IVMMethod:

    """独立变量法（Instrumental Variable Method）"""



    @staticmethod

    def partial_color(weights: List[float]) -> List[float]:

        """

        IVM部分着色



        核心：每个变量独立随机从{-1,1}中选择

        """

        return [1 if random.random() < 0.5 else -1 for _ in range(len(weights))]



    @staticmethod

    def discrepancy_bound(weights: List[float]) -> float:

        """

        差异上界



        定理：E[discrepancy] ≤ √(Σ w_i²)

        """

        sum_sq = sum(w ** 2 for w in weights)

        return np.sqrt(sum_sq)





def beck_fiala_theorem():

    """Beck-Fiala定理"""

    print("=== Beck-Fiala定理 ===")

    print()

    print("陈述：")

    print("  如果每个元素至多出现在t个集合中")

    print("  那么差异界为 O(√t)")

    print()

    print("应用：")

    print("  - 限制集系统")

    print("  - 约束着色问题")

    print("  - 网络流中的公平分配")





def partial_coloring_algorithm():

    """部分着色算法"""

    print()

    print("=== 部分着色算法 ===")

    print()

    print("步骤：")

    print("  1. 选择一半元素设为+1")

    print("  2. 选择另一半元素设为-1")

    print("  3. 调整直到满足约束")

    print()

    print("复杂度：O(n²)")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 模糊着色差异测试 ===\n")



    np.random.seed(42)



    # 测试数据

    weights = [1.0, 2.0, 3.0, 4.0, 5.0]



    print(f"权重: {weights}")

    print()



    # 部分着色

    pc = PartialColoring(len(weights))



    for trial in range(3):

        coloring = pc.color(weights, target_sum=0.0)

        weighted_sum = sum(w * c for w, c in zip(weights, coloring))

        print(f"尝试{trial+1}: 着色={coloring}, 加权和={weighted_sum:.2f}")



    print()



    # IVM

    print("IVM方法：")

    for trial in range(3):

        coloring = IVMMethod.partial_color(weights)

        weighted_sum = sum(w * c for w, c in zip(weights, coloring))

        print(f"  尝试{trial+1}: 加权和={weighted_sum:.2f}")



    print()



    # 理论界

    theoretical_bound = pc.expected_discrepancy(weights)

    print(f"理论差异界: ≤ {theoretical_bound:.2f}")



    print()

    beck_fiala_theorem()

    partial_coloring_algorithm()



    print()

    print("说明：")

    print("  - 随机方法通常比确定性方法好")

    print("  - IVM是差异理论的基石")

    print("  - 实际用于调度和资源分配")


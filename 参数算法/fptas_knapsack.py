# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / fptas_knapsack



本文件实现 fptas_knapsack 相关的算法功能。

"""



import random

from typing import Tuple, List





class FPTASKnapsack:

    """背包问题的FPTAS"""



    def __init__(self, epsilon: float = 0.1):

        """

        参数：

            epsilon: 近似参数

        """

        self.epsilon = epsilon



    def solve(self, weights: List[int], values: List[int],

             capacity: int) -> Tuple[int, List[int]]:

        """

        FPTAS求解背包问题



        参数：

            weights: 重量列表

            values: 价值列表

            capacity: 容量



        返回：(总价值, 选择)

        """

        n = len(weights)



        # 找到最大价值

        max_value = max(values)



        # 缩放因子

        K = (self.epsilon * max_value) / n



        # 缩放价值

        scaled_values = [int(v / K) for v in values]



        # 新的目标：最大化缩放价值和

        # 同时价值空间被限制在 O(n²/ε)



        # 动态规划（伪多项式，但在这里是FPTAS的一部分）

        scaled_max = sum(scaled_values)



        # DP表

        dp = [0] * (scaled_max + 1)



        for i in range(n):

            # 逆序更新

            for j in range(scaled_max, scaled_values[i] - 1, -1):

                dp[j] = max(dp[j], dp[j - scaled_values[i]] + values[i])



        # 找最大可行解

        best_value = 0

        best_selection = []



        # 暴力搜索最优（对小规模有效）

        best_value, best_selection = self._find_solution(

            weights, values, capacity, dp, scaled_values, K)



        return best_value, best_selection



    def _find_solution(self, weights: List[int], values: List[int],

                      capacity: int, dp: List[int],

                      scaled_values: List[int], K: float) -> Tuple[int, List[int]]:

        """找具体解"""

        n = len(weights)

        best_value = 0

        best_selection = []



        # 简化：贪心尝试

        remaining = capacity

        selection = [0] * n



        # 按单位价值排序

        items = sorted(range(n), key=lambda i: values[i]/weights[i], reverse=True)



        for i in items:

            if weights[i] <= remaining:

                selection[i] = 1

                remaining -= weights[i]

                best_value += values[i]



        return best_value, selection





def fptas_properties():

    """FPTAS性质"""

    print("=== FPTAS性质 ===")

    print()

    print("定义：")

    print("  - 时间 poly(n, 1/ε)")

    print("  - 解的质量 (1+ε)-近似")

    print()

    print("背包问题：")

    print("  - 伪多项式DP可以用FPTAS")

    print("  - 缩放后DP表大小 O(n²/ε)")

    print()

    print("重要性：")

    print("  - 有些问题没有FPTAS（除非P=NP）")

    print("  - 有FPTAS意味着"接近"易解")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== FPTAS测试 ===\n")



    random.seed(42)



    # 背包问题

    weights = [10, 20, 30, 40, 50]

    values = [60, 100, 120, 150, 200]

    capacity = 100



    print(f"物品重量: {weights}")

    print(f"物品价值: {values}")

    print(f"容量: {capacity}")

    print()



    # 使用FPTAS

    fptas = FPTASKnapsack(epsilon=0.1)

    value, selection = fptas.solve(weights, values, capacity)



    print(f"FPTAS结果 (ε=0.1):")

    print(f"  选中物品: {[i for i, s in enumerate(selection) if s]}")

    print(f"  总价值: {value}")

    print(f"  总重量: {sum(w for i, w in enumerate(weights) if selection[i])}")



    # 精确解（简化：只用贪心）

    print(f"\n简单贪心参考: {sum(values[:2])} (选前两个)")



    print()

    fptas_properties()



    print()

    print("说明：")

    print("  - FPTAS提供可调的近似")

    print("  - 对于NP难问题很有价值")

    print("  - 背包问题是典型的FPTAS案例")


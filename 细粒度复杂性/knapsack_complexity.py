# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / knapsack_complexity



本文件实现 knapsack_complexity 相关的算法功能。

"""



from typing import List, Tuple





class KnapsackComplexity:

    """背包问题复杂度"""



    def __init__(self):

        pass



    def solve_dp(self, weights: List[int], values: List[int],

               capacity: int) -> int:

        """

        动态规划求解



        返回：最大价值

        """

        n = len(weights)



        # DP[i][w] = 前i个物品容量w的最大价值

        dp = [[0] * (capacity + 1) for _ in range(n + 1)]



        for i in range(1, n + 1):

            for w in range(capacity + 1):

                dp[i][w] = dp[i-1][w]  # 不选第i个



                if weights[i-1] <= w:

                    dp[i][w] = max(dp[i][w],

                                  dp[i-1][w-weights[i-1]] + values[i-1])



        return dp[n][capacity]



    def estimate_complexity(self, n: int, W: int) -> dict:

        """

        估计复杂度



        返回：复杂度信息

        """

        return {

            'n': n,

            'capacity': W,

            'pseudo_poly': f"O({n} × {W})",

            'truly_poly': "不存在（NP难）",

            'lower_bound': f"Ω(2^{n/2})" if n < 50 else f"Ω(2^{n/10})"

        }



    def fptas(self, weights: List[int], values: List[int],

            capacity: int, epsilon: float) -> int:

        """

        FPTAS近似算法



        参数：

            epsilon: 近似误差



        返回：近似最大值

        """

        n = len(values)

        max_value = max(values)



        # 缩放

        K = epsilon * max_value / n



        scaled_values = [int(v / K) for v in values]



        # 调用DP

        return K * self.solve_dp(weights, scaled_values, capacity)





def knapsack_fine_grained():

    """背包细粒度复杂性"""

    print("=== 背包问题细粒度复杂性 ===")

    print()

    print("已知结果：")

    print("  - 伪多项式时间 O(nW)")

    print("  - FPTAS O(n²/ε)")

    print()

    print("下界（基于SETH）：")

    print("  - 需要 Ω(2^{n/2}) 时间")

    print("  - 即使伪多项式也不够好")

    print()

    print("应用：")

    print("  - 资源分配")

    print("  - 装箱问题")

    print("  - 组合优化")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 背包问题复杂度测试 ===\n")



    knap = KnapsackComplexity()



    # 测试

    weights = [2, 3, 4, 5]

    values = [3, 4, 5, 6]

    capacity = 8



    print(f"物品重量: {weights}")

    print(f"物品价值: {values}")

    print(f"容量: {capacity}")

    print()



    # DP求解

    max_value = knap.solve_dp(weights, values, capacity)



    print(f"最大价值: {max_value}")



    # FPTAS

    approx = knap.fptas(weights, values, capacity, epsilon=0.1)



    print(f"FPTAS近似 (ε=0.1): {approx}")

    print()



    # 复杂度估计

    info = knap.estimate_complexity(n=50, W=1000)



    print("复杂度估计：")

    for key, value in info.items():

        print(f"  {key}: {value}")



    print()

    knapsack_fine_grained()



    print()

    print("说明：")

    print("  - 背包问题是NP难问题的代表")

    print("  - FPTAS是近似解法")

    print("  - 细粒度下界基于SETH")


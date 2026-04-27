# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / knapsack



本文件实现 knapsack 相关的算法功能。

"""



def mf_knapsack(i, wt, val, j):

    """

    记忆化搜索版本的背包问题



    使用全局 dp 表 f[i][j]，初始值设为 -1 表示未计算。

    当需要计算子问题时才求解，避免重复计算。



    参数:

        i: 考虑前 i 个物品

        j: 背包剩余容量

    """

    global f

    if f[i][j] < 0:  # 未计算过

        if j < wt[i - 1]:

            # 物品太重，无法选，只能看前 i-1 个

            val = mf_knapsack(i - 1, wt, val, j)

        else:

            # 选或不选，取较大值

            val = max(

                mf_knapsack(i - 1, wt, val, j),  # 不选

                mf_knapsack(i - 1, wt, val, j - wt[i - 1]) + val[i - 1],  # 选

            )

        f[i][j] = val

    return f[i][j]





def knapsack(w, wt, val, n):

    """

    0-1 背包问题（迭代 DP 版本）



    参数:

        w: 背包最大容量

        wt: 物品重量列表

        val: 物品价值列表

        n: 物品数量



    返回:

        (最大价值, DP 表)

    """

    # dp[i][j] = 前 i 个物品在容量 j 下的最大价值

    dp = [[0] * (w + 1) for _ in range(n + 1)]



    # 逐个物品决策

    for i in range(1, n + 1):

        for w_ in range(1, w + 1):

            if wt[i - 1] <= w_:  # 能装下第 i 个物品

                # 选或不选，取较大值

                dp[i][w_] = max(val[i - 1] + dp[i - 1][w_ - wt[i - 1]], dp[i - 1][w_])

            else:  # 装不下，只能不选

                dp[i][w_] = dp[i - 1][w_]



    return dp[n][w_], dp





def knapsack_with_example_solution(w: int, wt: list, val: list):

    """

    背包问题 - 并返回一个最优解的具体物品组合



    参数:

        w: 背包总容量

        wt: 各物品重量列表

        val: 各物品价值列表



    返回:

        (最大价值, 最优物品组合的索引集合)



    示例:

        >>> knapsack_with_example_solution(10, [1, 3, 5, 2], [10, 20, 100, 22])

        (142, {2, 3, 4})

    """

    if not (isinstance(wt, (list, tuple)) and isinstance(val, (list, tuple))):

        raise ValueError("weights 和 values 都必须是 list 或 tuple")



    num_items = len(wt)

    if num_items != len(val):

        raise ValueError(f"物品数量不一致：{num_items} 个重量 vs {len(val)} 个价值")



    for i in range(num_items):

        if not isinstance(wt[i], int):

            raise TypeError(f"所有重量必须是整数，但第 {i} 个是 {type(wt[i])}")



    optimal_val, dp_table = knapsack(w, wt, val, num_items)

    example_optional_set: set = set()

    _construct_solution(dp_table, wt, num_items, w, example_optional_set)



    return optimal_val, example_optional_set





def _construct_solution(dp: list, wt: list, i: int, j: int, optimal_set: set):

    """

    回溯 DP 表，还原出一个最优解的具体物品组合



    原理：如果 dp[i][j] == dp[i-1][j]，说明第 i 个物品没选

          否则，第 i 个物品被选了

    """

    if i > 0 and j > 0:

        if dp[i - 1][j] == dp[i][j]:

            # 第 i 个物品没选

            _construct_solution(dp, wt, i - 1, j, optimal_set)

        else:

            # 第 i 个物品选了

            optimal_set.add(i)

            _construct_solution(dp, wt, i - 1, j - wt[i - 1], optimal_set)





if __name__ == "__main__":

    # 测试用例

    val = [3, 2, 4, 4]

    wt = [4, 3, 2, 3]

    n = 4

    w = 6



    # 记忆化版本

    f = [[0] * (w + 1)] + [[0] + [-1] * (w + 1) for _ in range(n + 1)]

    optimal_solution, _ = knapsack(w, wt, val, n)

    print(f"最大价值: {optimal_solution}")

    print(f"记忆化搜索结果: {mf_knapsack(n, wt, val, w)}")



    # 测试带解的具体组合

    optimal_solution, optimal_subset = knapsack_with_example_solution(w, wt, val)

    print(f"最大价值 = {optimal_solution}")

    print(f"最优物品组合 (索引) = {optimal_subset}")


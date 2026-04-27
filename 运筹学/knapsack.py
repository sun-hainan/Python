# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / knapsack



本文件实现 knapsack 相关的算法功能。

"""



import numpy as np





def knapsack_dp(values, weights, capacity):

    """

    动态规划解 0-1 背包问题



    状态定义：

    dp[i][w] = 前 i 个物品、容量 w 时的最大价值



    转移：

    dp[i][w] = max(dp[i-1][w], dp[i-1][w-w_i] + v_i) if w >= w_i



    时间复杂度：O(n * W)

    空间复杂度：O(n * W) 或 O(W)（优化）

    """

    n = len(values)



    # 空间优化版本

    dp = np.zeros(capacity + 1, dtype=int)

    choice = np.zeros((capacity + 1, n), dtype=int)  # 追踪选择



    for i in range(n):

        v = values[i]

        w = weights[i]



        # 逆序遍历（避免重复使用同一物品）

        for c in range(capacity, w - 1, -1):

            if dp[c - w] + v > dp[c]:

                dp[c] = dp[c - w] + v

                choice[c, i] = 1



    # 回溯选择

    selected = np.zeros(n, dtype=int)

    c = capacity

    for i in range(n - 1, -1, -1):

        if choice[c, i] == 1:

            selected[i] = 1

            c -= weights[i]



    total_value = dp[capacity]

    total_weight = sum(weights[i] * selected[i] for i in range(n))



    return {

        'selected': selected,

        'total_value': total_value,

        'total_weight': total_weight,

        'dp_table': dp

    }





def knapsack_dp_unbounded(values, weights, capacity):

    """

    完全背包（物品无限）



    状态：

    dp[w] = 容量 w 时的最大价值

    """

    n = len(values)

    dp = np.zeros(capacity + 1, dtype=int)



    for w in range(capacity + 1):

        for i in range(n):

            if weights[i] <= w:

                dp[w] = max(dp[w], dp[w - weights[i]] + values[i])



    return {'max_value': dp[capacity], 'dp': dp}





def knapsack_branch_and_bound(values, weights, capacity):

    """

    分支定界解 0-1 背包



    上界：贪心解（按价值/重量比选择）

    下界：当前最好整数解



    搜索策略：深度优先 + 界限剪枝

    """

    n = len(values)



    # 按价值/重量比排序

    ratios = sorted(range(n), key=lambda i: values[i] / weights[i], reverse=True)



    # 排序后的数据

    values_sorted = [values[i] for i in ratios]

    weights_sorted = [weights[i] for i in ratios]

    original_idx = ratios



    best_value = 0

    best_x = np.zeros(n, dtype=int)



    def bound(x, depth, remaining, current_value):

        """计算上界（贪心）"""

        # 剩余容量

        cap = remaining



        # 计算当前选择的价值

        bound_value = current_value



        for i in range(depth, n):

            if weights_sorted[i] <= cap:

                bound_value += values_sorted[i]

                cap -= weights_sorted[i]

            else:

                # 部分选择

                bound_value += values_sorted[i] / weights_sorted[i] * cap

                break



        return bound_value



    def branch(x, depth, remaining, current_value):

        nonlocal best_value, best_x



        if depth == n:

            # 叶子

            if current_value > best_value:

                best_value = current_value

                # 转换回原始顺序

                best_x[original_idx] = x[:depth]

            return



        # 上界剪枝

        ub = bound(x, depth, remaining, current_value)

        if ub <= best_value:

            return



        i = depth



        # 分支1：选择物品 i

        if weights_sorted[i] <= remaining:

            x[i] = 1

            branch(x, depth + 1, remaining - weights_sorted[i],

                   current_value + values_sorted[i])



        # 分支2：不选择物品 i

        x[i] = 0

        branch(x, depth + 1, remaining, current_value)



    branch(np.zeros(n, dtype=int), 0, capacity, 0)



    return {

        'selected': best_x,

        'total_value': best_value,

        'total_weight': sum(weights[i] * best_x[i] for i in range(n))

    }





def knapsack_greedy(values, weights, capacity):

    """

    贪心近似算法



    按价值/重量比排序，优先选择

    不保证最优，但接近最优

    """

    ratios = [(i, values[i] / weights[i]) for i in range(len(values))]

    ratios.sort(key=lambda x: x[1], reverse=True)



    selected = np.zeros(len(values), dtype=int)

    total_value = 0

    total_weight = 0



    for i, ratio in ratios:

        if weights[i] + total_weight <= capacity:

            selected[i] = 1

            total_value += values[i]

            total_weight += weights[i]



    return {

        'selected': selected,

        'total_value': total_value,

        'total_weight': total_weight,

        'method': 'greedy'

    }





def knapsack_fptas(values, weights, capacity, epsilon=0.1):

    """

    完全多项式时间近似方案 (FPTAS)



        对于任意 ε > 0，在 poly(n, 1/ε) 时间内得到 (1-ε)-近似



    思想：缩放价值，用 DP

    """

    n = len(values)

    max_value = max(values)



    # 计算缩放因子

    K = epsilon * max_value / n



    # 缩放价值

    values_scaled = (values / K).astype(int)



    # DP

    dp = np.zeros(capacity + 1, dtype=int)



    for i in range(n):

        v = values_scaled[i]

        w = weights[i]

        for c in range(capacity, w - 1, -1):

            dp[c] = max(dp[c], dp[c - w] + v)



    # 反缩放

    max_val_scaled = dp[capacity]

    max_val_approx = max_val_scaled * K



    return {

        'approx_value': max_val_approx,

        'guarantee': f'(1-ε)-approx with ε={epsilon}'

    }





if __name__ == "__main__":

    print("=" * 60)

    print("0-1 背包问题")

    print("=" * 60)



    # 测试数据

    values = [60, 100, 120, 80, 50, 70, 30]

    weights = [10, 20, 30, 15, 10, 25, 5]

    capacity = 70



    print(f"\n物品数量: {len(values)}")

    print(f"背包容量: {capacity}")

    print(f"价值: {values}")

    print(f"重量: {weights}")



    # 动态规划

    print("\n--- 动态规划 ---")

    result_dp = knapsack_dp(values, weights, capacity)

    print(f"最优价值: {result_dp['total_value']}")

    print(f"总重量: {result_dp['total_weight']}")

    print(f"选择的物品: {np.where(result_dp['selected'] == 1)[0].tolist()}")



    # 分支定界

    print("\n--- 分支定界 ---")

    result_bb = knapsack_branch_and_bound(values, weights, capacity)

    print(f"最优价值: {result_bb['total_value']}")

    print(f"总重量: {result_bb['total_weight']}")

    print(f"选择的物品: {np.where(result_bb['selected'] == 1)[0].tolist()}")



    # 贪心

    print("\n--- 贪心近似 ---")

    result_greedy = knapsack_greedy(values, weights, capacity)

    print(f"近似价值: {result_greedy['total_value']}")

    print(f"选择的物品: {np.where(result_greedy['selected'] == 1)[0].tolist()}")

    print(f"与最优解的差距: {result_dp['total_value'] - result_greedy['total_value']}")



    # FPTAS

    print("\n--- FPTAS ---")

    result_fptas = knapsack_fptas(values, weights, capacity, epsilon=0.1)

    print(f"近似值: {result_fptas['approx_value']:.2f}")

    print(f"保证: {result_fptas['guarantee']}")



    # 大规模测试

    print("\n--- 大规模测试 ---")

    np.random.seed(42)

    n = 50

    values_large = np.random.randint(10, 100, n)

    weights_large = np.random.randint(5, 50, n)

    capacity_large = 500



    import time



    t1 = time.time()

    result_large = knapsack_dp(values_large.tolist(), weights_large.tolist(), capacity_large)

    t_dp = time.time() - t1



    t1 = time.time()

    result_large_bb = knapsack_branch_and_bound(values_large.tolist(), weights_large.tolist(), capacity_large)

    t_bb = time.time() - t1



    print(f"DP 结果: 价值={result_large['total_value']}, 时间={t_dp:.4f}s")

    print(f"BB 结果: 价值={result_large_bb['total_value']}, 时间={t_bb:.4f}s")


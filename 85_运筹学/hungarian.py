# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / hungarian



本文件实现 hungarian 相关的算法功能。

"""



import numpy as np





def hungarian_algorithm(cost_matrix):

    """

    匈牙利算法解线性分配问题



    步骤：

    1. 行归约：每行减去该行最小值

    2. 列归约：每列减去该列最小值

    3. 覆盖所有零元素：使用最少的线

    4. 若线数 = n，结束

    5. 否则，调整：未被覆盖的最小值减去，加到交叉点



    Parameters

    ----------

    cost_matrix : np.ndarray

        成本矩阵 (n x n)



    Returns

    -------

    dict

        assignment: 分配方案 (worker -> task)

        cost: 最小总成本

    """

    n = cost_matrix.shape[0]

    cost = cost_matrix.astype(float)



    # 复制以避免修改原矩阵

    A = cost.copy()



    # ========== 步骤 1: 行归约 ==========

    # 每行减去该行最小值

    for i in range(n):

        min_val = np.min(A[i, :])

        A[i, :] -= min_val



    # ========== 步骤 2: 列归约 ==========

    # 每列减去该列最小值

    for j in range(n):

        min_val = np.min(A[:, j])

        A[:, j] -= min_val



    # ========== 迭代过程 ==========

    assignment = np.zeros(n, dtype=int)  # assignment[i] = j 表示 i 被分配给 j

    row_covered = np.zeros(n, dtype=bool)

    col_covered = np.zeros(n, dtype=bool)



    def find_zero(A, row_covered, col_covered):

        """找未被覆盖的零元素"""

        for i in range(n):

            for j in range(n):

                if abs(A[i, j]) < 1e-10 and not row_covered[i] and not col_covered[j]:

                    return i, j

        return -1, -1



    def star_zeros(A, assignment, row_covered, col_covered):

        """标记零元素（星号）"""

        # 初始化

        for i in range(n):

            assignment[i] = -1



        # 先找唯一的未覆盖零

        for i in range(n):

            for j in range(n):

                if abs(A[i, j]) < 1e-10 and not col_covered[j]:

                    assignment[i] = j

                    col_covered[j] = True

                    break



    def cover_columns(A, assignment, col_covered):

        """标记有星号零的列"""

        col_covered[:] = False

        for i in range(n):

            if assignment[i] != -1:

                col_covered[assignment[i]] = True



    max_iterations = 1000

    for iteration in range(max_iterations):

        # 步骤 3: 覆盖所有零

        # 先标记星号

        assignment[:] = -1

        row_covered[:] = False

        col_covered[:] = False



        # 标记星号零

        for i in range(n):

            for j in range(n):

                if abs(A[i, j]) < 1e-10 and not col_covered[j]:

                    assignment[i] = j

                    col_covered[j] = True

                    break



        # 覆盖有星号的列

        cover_columns(A, assignment, col_covered)



        # 检查是否所有列都被覆盖

        if np.all(col_covered):

            # 找到最优分配

            break



        # 步骤 4: 找非覆盖最小值

        min_val = np.inf

        for i in range(n):

            for j in range(n):

                if not row_covered[i] and not col_covered[j]:

                    if A[i, j] < min_val:

                        min_val = A[i, j]



        # 步骤 5: 调整

        for i in range(n):

            for j in range(n):

                if row_covered[i]:

                    A[i, j] += min_val

                if not col_covered[j]:

                    A[i, j] -= min_val



    # 提取分配方案

    row_assign = np.zeros(n, dtype=int)  # row_assign[i] = j

    for i in range(n):

        row_assign[i] = assignment[i]



    # 计算成本

    total_cost = sum(cost_matrix[i, row_assign[i]] for i in range(n))



    return {

        'assignment': row_assign,

        'cost': total_cost,

        'total_cost': total_cost

    }





def hungarian_maximum(profit_matrix):

    """

    最大化版本：转换为最小化

    min c_ij = max - profit_ij

    """

    max_profit = np.max(profit_matrix)

    cost_matrix = max_profit - profit_matrix



    result = hungarian_algorithm(cost_matrix)

    result['max_profit'] = result['cost']

    result['cost'] = max_profit * len(profit_matrix) - result['cost']



    return result





def lap_greedy(cost_matrix):

    """

    贪心近似解（快速但不保证最优）

    """

    n = len(cost_matrix)

    assigned = np.zeros(n, dtype=int) - 1

    row_assigned = np.zeros(n, dtype=bool)

    col_assigned = np.zeros(n, dtype=bool)



    # 按成本排序，贪心选择

    pairs = []

    for i in range(n):

        for j in range(n):

            pairs.append((cost_matrix[i, j], i, j))



    pairs.sort()



    for cost, i, j in pairs:

        if not row_assigned[i] and not col_assigned[j]:

            assigned[i] = j

            row_assigned[i] = True

            col_assigned[j] = True



    total_cost = sum(cost_matrix[i, assigned[i]] for i in range(n))



    return {

        'assignment': assigned,

        'cost': total_cost

    }





if __name__ == "__main__":

    print("=" * 60)

    print("匈牙利算法 - 线性分配问题")

    print("=" * 60)



    # 示例：5个工作者，5个任务

    cost_matrix = np.array([

        [9, 2, 7, 8, 5],

        [6, 4, 3, 7, 8],

        [5, 8, 1, 8, 5],

        [7, 6, 9, 4, 6],

        [5, 5, 8, 6, 10]

    ], dtype=float)



    print("\n成本矩阵:")

    print(cost_matrix)



    # 匈牙利算法

    result = hungarian_algorithm(cost_matrix)



    print(f"\n最优分配:")

    for i, j in enumerate(result['assignment']):

        print(f"  工作者 {i+1} -> 任务 {j+1} (成本: {cost_matrix[i, j]:.0f})")



    print(f"\n最小总成本: {result['cost']:.0f}")



    # 验证

    print("\n--- 验证 ---")

    print(f"分配方案: {result['assignment'].tolist()}")

    print(f"总成本: {sum(cost_matrix[i, result['assignment'][i]] for i in range(5))}")



    # 贪心对比

    greedy_result = lap_greedy(cost_matrix)

    print(f"\n贪心近似成本: {greedy_result['cost']:.0f}")

    print(f"与最优差距: {greedy_result['cost'] - result['cost']}")



    # 最大化示例

    print("\n" + "-" * 40)

    print("\n最大化示例（利润矩阵）:")

    profit_matrix = np.array([

        [9, 2, 7, 8, 5],

        [6, 4, 3, 7, 8],

        [5, 8, 1, 8, 5],

        [7, 6, 9, 4, 6],

        [5, 5, 8, 6, 10]

    ])



    result_max = hungarian_maximum(profit_matrix)



    print(f"最大总利润: {result_max['cost']:.0f}")

    print(f"分配方案: {result_max['assignment'].tolist()}")



    # 性能测试

    print("\n" + "-" * 40)

    print("\n性能测试:")

    np.random.seed(42)



    for n in [10, 50, 100, 200]:

        cost = np.random.randint(1, 100, (n, n))



        import time

        t1 = time.time()

        result_perf = hungarian_algorithm(cost)

        t_hungarian = time.time() - t1



        print(f"  n={n:3d}: 耗时 {t_hungarian:.4f}s, 成本={result_perf['cost']}")


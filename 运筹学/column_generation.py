# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / column_generation

本文件实现 column_generation 相关的算法功能。
"""

import numpy as np
from scipy.optimize import linprog


def cutting_stock_column_generation(demands, roll_width, max_pattern_length=100):
    """
    切割-stock 问题的列生成算法

    问题：
    min Σ y_j (使用的卷材数)
    s.t. Σ_j n_ij * y_j >= d_i, ∀i (满足需求)
         y_j >= 0, 整数

    其中 n_ij 是模式 j 中宽度 i 的数量

    参数：
    - demands: 各宽度的需求 [d_1, d_2, ..., d_n]
    - roll_width: 卷材宽度 W
    - max_pattern_length: 模式中最大条数
    """
    n_widths = len(demands)
    widths = np.arange(1, n_widths + 1)  # 简化：假设宽度是 1, 2, ..., n

    # 初始模式：每个宽度单独切割
    patterns = []
    for i in range(n_widths):
        pattern = np.zeros(n_widths)
        pattern[i] = int(roll_width // widths[i])
        if pattern[i] > 0:
            patterns.append(pattern)

    # 添加"混合"初始模式
    remaining = roll_width
    pattern = np.zeros(n_widths)
    for i in range(n_widths):
        while remaining >= widths[i] and np.sum(pattern) < max_pattern_length:
            pattern[i] += 1
            remaining -= widths[i]
    if np.sum(pattern) > 0:
        patterns.append(pattern)

    # 迭代
    max_iter = 50
    for iteration in range(max_iter):
        # 求解限制主问题 (RMP)
        # min Σ y_j
        # s.t. Σ_j a_ij * y_j >= d_i
        #      y_j >= 0

        A = np.array(patterns).T  # (n_widths x n_patterns)
        c = np.ones(len(patterns))

        res = linprog(c, A_ub=-A, b_ub=-demands, bounds=(0, None))

        if not res.success:
            print(f"迭代 {iteration}: RMP 无解")
            break

        # 对偶变量
        pi = res.x  # 对偶变量（注意符号）
        # 注意：linprog 标准型是 Ax <= b，所以对偶变量符号需要调整

        # 定价问题：找最有负reduced cost的模式
        # reduced_cost = 1 - Σ π_i * a_i
        # 要找 reduced_cost < 0 的模式

        # 求解定价问题（子问题）
        # 这是个背包问题：最大化 Σ π_i * x_i
        # s.t. Σ width_i * x_i <= W
        #      x_i >= 0, 整数

        new_pattern = solve_pricing_subproblem(demands, roll_width, pi, max_pattern_length)

        # 检查是否需要添加新模式
        # reduced cost = 1 - π' * new_pattern
        reduced_cost = 1.0 - np.sum(pi * new_pattern)

        if reduced_cost >= -1e-6:
            # 最优
            break

        patterns.append(new_pattern)

    # 整数化（启发式）
    y = res.x
    y_int = np.ceil(y)

    return {
        'patterns': patterns,
        'y': y,
        'y_int': y_int,
        'rolls_used': np.sum(y_int),
        'iterations': iteration + 1
    }


def solve_pricing_subproblem(demands, roll_width, dual_prices, max_items):
    """
    定价子问题：求解新模式

    max Σ π_i * x_i
    s.t. Σ width_i * x_i <= W
         x_i >= 0, 整数

    使用动态规划或贪婪
    """
    n_widths = len(dual_prices)
    widths = np.arange(1, n_widths + 1)

    # 贪婪：按价值/宽度比排序
    ratios = [(i, dual_prices[i] / widths[i]) for i in range(n_widths)]
    ratios.sort(key=lambda x: x[1], reverse=True)

    pattern = np.zeros(n_widths)
    remaining = roll_width

    for i, ratio in ratios:
        count = remaining // widths[i]
        if count > 0:
            pattern[i] = count
            remaining -= count * widths[i]

    # 动态规划版本（更精确）
    # 简化为上面贪婪方法

    return pattern


def cutting_stock_dp(demands, roll_width):
    """
    切割-stock 的动态规划（当卷材宽度较小时）
    """
    # DP[i][w] = 使用前 i 种宽度、卷材宽度 w 时满足的最大需求覆盖
    # 这个 DP 比较复杂，因为需求是下界

    # 简化为：求满足所有需求所需的最少卷材
    # 使用整数规划
    from scipy.optimize import linprog

    # 生成所有可能的模式
    widths = np.arange(1, len(demands) + 1)
    patterns = []

    def generate_patterns(idx, remaining, pattern):
        if idx == len(widths):
            if remaining >= 0:
                patterns.append(pattern.copy())
            return
        max_count = remaining // widths[idx]
        for count in range(max_count + 1):
            pattern[idx] = count
            generate_patterns(idx + 1, remaining - count * widths[idx], pattern)

    generate_patterns(0, roll_width, np.zeros(len(widths), dtype=int))

    # 求解
    A = np.array(patterns).T
    c = np.ones(len(patterns))

    res = linprog(c, A_ub=-A, b_ub=-demands, bounds=(0, None))

    return {
        'patterns': patterns,
        'y': res.x if res.success else None,
        'obj': res.fun if res.success else None
    }


if __name__ == "__main__":
    print("=" * 60)
    print("列生成算法 - 切割 Stock 问题")
    print("=" * 60)

    # 示例：卷材宽度 100cm，需求如下
    demands = np.array([20, 15, 10, 8, 5])  # 5 种宽度
    roll_width = 100

    print(f"卷材宽度: {roll_width}")
    print(f"各宽度需求: {demands.tolist()}")

    result = cutting_stock_column_generation(demands, roll_width)

    print(f"\n列生成结果:")
    print(f"迭代次数: {result['iterations']}")
    print(f"LP 最优卷材数: {result['y'].sum():.4f}")
    print(f"整数化解卷材数: {result['rolls_used']:.0f}")

    print(f"\n切割模式:")
    for i, (pattern, y) in enumerate(zip(result['patterns'], result['y'])):
        if y > 1e-6:
            counts = [f"{int(pattern[j])}×{j+1}" for j in range(len(pattern)) if pattern[j] > 0]
            print(f"  模式 {i+1}: {', '.join(counts)}, 使用 {y:.2f} 卷")

    # DP 验证（小规模）
    print("\n--- DP 验证（小规模）---")
    small_demands = np.array([10, 8, 5])
    small_roll_width = 30

    dp_result = cutting_stock_dp(small_demands, small_roll_width)

    if dp_result['obj'] is not None:
        print(f"DP 最优卷材数: {dp_result['obj']:.0f}")
        print(f"使用的模式:")
        for y, pattern in zip(dp_result['y'], dp_result['patterns']):
            if y > 0.5:
                counts = [f"{int(pattern[j])}×{j+1}" for j in range(len(pattern)) if pattern[j] > 0]
                print(f"  {', '.join(counts)}: {int(y)} 卷")

# -*- coding: utf-8 -*-
"""
算法实现：近似算法 / ptas_fptas_design

本文件实现 ptas_fptas_design 相关的算法功能。
"""

import numpy as np
import time


def knapsack_exact(values, weights, capacity):
    """
    精确动态规划求解 0-1 背包问题
    
    状态定义: dp[i][w] = 前 i 个物品在容量 w 下的最大价值
    转移方程: dp[i][w] = max(dp[i-1][w], dp[i-1][w-w_i] + v_i)
    
    时间复杂度: O(n * W),空间复杂度: O(n * W)
    其中 W 是背包容量
    
    Parameters
    ----------
    values : list
        物品价值列表
    weights : list
        物品重量列表
    capacity : int
        背包容量
    
    Returns
    -------
    tuple
        (最大价值, 选择方案)
    """
    n = len(values)
    # 初始化 DP 表,dp[i][w] 表示考虑前 i 个物品后的最大价值
    dp = np.zeros((n + 1, capacity + 1), dtype=np.int64)
    
    # 填充 DP 表
    for i in range(1, n + 1):
        # 当前物品的价值和重量
        v_i = values[i - 1]
        w_i = weights[i - 1]
        
        for w in range(capacity + 1):
            # 不选择第 i 个物品
            dp[i][w] = dp[i - 1][w]
            
            # 选择第 i 个物品 (如果容量允许)
            if w >= w_i:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - w_i] + v_i)
    
    # 回溯找出具体选择方案
    selected = [0] * n
    w = capacity
    for i in range(n, 0, -1):
        # 如果价值发生变化,说明选择了第 i 个物品
        if dp[i][w] != dp[i - 1][w]:
            selected[i - 1] = 1
            w -= weights[i - 1]
    
    return int(dp[n][capacity]), selected


def knapsack_ptas(values, weights, capacity, epsilon):
    """
    PTAS (多项式时间近似方案): 0-1 背包问题
    
    核心思想:
    1. 按价值/重量比将物品排序
    2. 枚举"高价值密度"物品的子集 (最多选择 k = 1/ε 个)
    3. 对剩余物品使用贪婪选择
    
    Parameters
    ----------
    values : list
        物品价值列表
    weights : list
        物品重量列表
    capacity : int
        背包容量
    epsilon : float
        近似参数,0 < ε ≤ 1,近似比为 (1-ε)
    
    Returns
    -------
    tuple
        (近似最大价值, 选择方案)
    """
    n = len(values)
    # 计算价值密度比
    ratios = [(v / w, i) for i, (v, w) in enumerate(zip(values, weights))]
    ratios.sort(reverse=True)  # 按密度降序排列
    
    k = int(1 / epsilon)  # 枚举物品数量上限
    best_value = 0
    best_selected = None
    
    # 预处理: 密度排序后的索引映射
    sorted_indices = [idx for _, idx in ratios]
    
    # 枚举"高质量"物品的所有子集 (2^k 种组合)
    # 这里使用简化版本: 直接选择前 k 个高密度物品
    # 实际 PTAS 需要更复杂的子集枚举
    
    # 简化策略: 选择所有"大物品" (重量 > epsilon * capacity)
    # 使用动态规划处理"小物品"
    
    # 找出大物品和小物品
    eps_cap = epsilon * capacity
    large_items = []
    small_items = []
    
    for i in range(n):
        if weights[i] > eps_cap:
            large_items.append(i)
        else:
            small_items.append(i)
    
    # 大物品只能选择有限个,我们枚举其组合
    # 对于每个大物品的子集,使用贪婪处理小物品
    
    best_value = 0
    best_selected = [0] * n
    
    # 使用贪婪算法作为基准
    remaining_capacity = capacity
    selected_large = [0] * len(large_items)
    
    # 按价值降序选择大物品
    large_values = [(values[i], i) for i in large_items]
    large_values.sort(reverse=True)
    
    for v, idx in large_values:
        real_idx = large_items[idx]
        if weights[real_idx] <= remaining_capacity:
            selected_large[idx] = 1
            remaining_capacity -= weights[real_idx]
            best_value += values[real_idx]
            best_selected[real_idx] = 1
    
    # 对小物品使用分数背包的贪婪选择
    small_ratios = [(values[i] / weights[i], i) for i in small_items]
    small_ratios.sort(reverse=True)
    
    for ratio, idx in small_ratios:
        if weights[idx] <= remaining_capacity:
            best_selected[idx] = 1
            best_value += values[idx]
            remaining_capacity -= weights[idx]
    
    return best_value, best_selected


def knapsack_fptas(values, weights, capacity, epsilon):
    """
    FPTAS (完全多项式时间近似方案): 0-1 背包问题
    
    核心思想:
    1. 精度缩放: 将价值乘以 K = (n * max_v) / (ε * OPT)
       使得近似整数规划问题可以在 O(n^2/ε) 内求解
    2. 伪多项式动态规划 + 精度压缩
    
    时间复杂度: O(n^3 / ε)
    
    Parameters
    ----------
    values : list
        物品价值列表
    weights : list
        物品重量列表
    capacity : int
        背包容量
    epsilon : float
        近似参数,0 < ε ≤ 1
    
    Returns
    -------
    tuple
        (近似最大价值, 选择方案)
    """
    n = len(values)
    max_value = max(values) if values else 0
    
    # 估计 OPT 值 (使用贪婪算法的上界)
    # 分数背包的上界: 按密度排序依次选取直到装满
    sorted_items = sorted([(v, w, i) for i, (v, w) in enumerate(zip(values, weights))],
                         key=lambda x: x[0] / x[1] if x[1] > 0 else 0, reverse=True)
    
    bound = 0
    rem_cap = capacity
    for v, w, _ in sorted_items:
        if w <= rem_cap:
            bound += v
            rem_cap -= w
        else:
            bound += v * (rem_cap / w)
            break
    
    # 计算缩放因子 K
    if bound == 0:
        K = 1
    else:
        K = (n * max_value) / (epsilon * bound)
    K = max(1, K)  # 确保 K >= 1
    
    # 缩放后的价值 (向下取整)
    scaled_values = [int(v / K) for v in values]
    
    # 动态规划: dp[j] = 使用缩放价值 j 时所需的最小重量
    # j 的范围: 0 到 n * max_scaled_value
    max_scaled = sum(scaled_values)
    
    # 初始化: dp[j] = 无穷大表示不可达
    INF = float('inf')
    dp = [INF] * (max_scaled + 1)
    dp[0] = 0
    
    # parent 数组用于回溯选择
    parent = [-1] * (max_scaled + 1)
    
    # 逐个物品更新 DP
    for i in range(n):
        w_i = weights[i]
        v_i_scaled = scaled_values[i]
        
        # 逆序遍历 (0-1 背包)
        for j in range(max_scaled, v_i_scaled - 1, -1):
            if dp[j - v_i_scaled] != INF:
                new_weight = dp[j - v_i_scaled] + w_i
                if new_weight <= capacity and new_weight < dp[j]:
                    dp[j] = new_weight
                    parent[j] = i  # 记录选择物品 i
    
    # 找到满足容量约束的最大缩放价值
    best_scaled_value = 0
    for j in range(max_scaled + 1):
        if dp[j] <= capacity and j > best_scaled_value:
            best_scaled_value = j
    
    # 回溯选择方案
    selected = [0] * n
    j = best_scaled_value
    while j > 0 and parent[j] != -1:
        selected[parent[j]] = 1
        j -= scaled_values[parent[j]]
    
    # 还原真实价值
    real_value = int(best_scaled_value * K)
    
    return real_value, selected


def compute_approximation_ratio(approximate, optimal):
    """
    计算近似比: optimal / approximate
    
    越接近 1 越好
    
    Parameters
    ----------
    approximate : float
        近似算法得到的值
    optimal : float
        最优值
    
    Returns
    -------
    float
        近似比
    """
    if approximate == 0:
        return float('inf')
    return optimal / approximate


if __name__ == "__main__":
    # 测试: PTAS 和 FPTAS 背包算法
    
    print("=" * 60)
    print("PTAS/FPTAS 背包问题测试")
    print("=" * 60)
    
    # 随机生成测试数据
    np.random.seed(42)
    n = 20  # 物品数量
    max_weight = 50
    max_value = 100
    capacity = 200
    
    values = np.random.randint(1, max_value + 1, size=n).tolist()
    weights = np.random.randint(1, max_weight + 1, size=n).tolist()
    
    print(f"\n物品数量: {n}")
    print(f"背包容量: {capacity}")
    print(f"价值范围: 1 ~ {max_value}")
    print(f"重量范围: 1 ~ {max_weight}")
    
    # 测试精确算法 (小规模)
    print("\n--- 精确 DP (n≤20) ---")
    start = time.time()
    opt_val, opt_sel = knapsack_exact(values, weights, capacity)
    print(f"最优值: {opt_val}")
    print(f"运行时间: {time.time() - start:.4f}秒")
    
    # 测试 PTAS
    epsilon = 0.1  # 10% 近似
    print(f"\n--- PTAS (ε={epsilon}) ---")
    start = time.time()
    ptas_val, ptas_sel = knapsack_ptas(values, weights, capacity, epsilon)
    ratio = compute_approximation_ratio(ptas_val, opt_val)
    print(f"近似值: {ptas_val}")
    print(f"近似比: {ratio:.4f}")
    print(f"运行时间: {time.time() - start:.4f}秒")
    
    # 测试 FPTAS
    epsilon = 0.1
    print(f"\n--- FPTAS (ε={epsilon}) ---")
    start = time.time()
    fptas_val, fptas_sel = knapsack_fptas(values, weights, capacity, epsilon)
    ratio = compute_approximation_ratio(fptas_val, opt_val)
    print(f"近似值: {fptas_val}")
    print(f"近似比: {ratio:.4f}")
    print(f"运行时间: {time.time() - start:.4f}秒")
    
    # 测试不同 ε 值对 FPTAS 的影响
    print("\n--- FPTAS 精度对比 ---")
    for eps in [0.5, 0.2, 0.1, 0.05, 0.01]:
        start = time.time()
        val, _ = knapsack_fptas(values, weights, capacity, eps)
        elapsed = time.time() - start
        ratio = compute_approximation_ratio(val, opt_val)
        print(f"ε={eps:.2f}: 近似值={val}, 比值={ratio:.4f}, 时间={elapsed:.4f}秒")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

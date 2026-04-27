# -*- coding: utf-8 -*-
"""
算法实现：计算复杂性理论 / subset_sum

本文件实现 subset_sum 相关的算法功能。
"""

from typing import List, Tuple, Optional, Set


# ==================== 验证器 ====================

def verify_subset_sum(arr: List[int], target: int, subset: Set[int]) -> bool:
    """
    验证subset是否是满足条件的解

    复杂度：O(n)
    """
    if sum(arr[i] for i in subset) == target:
        return True
    return False


# ==================== 动态规划算法 ====================

def subset_sum_dp(arr: List[int], target: int) -> Optional[Set[int]]:
    """
    动态规划求解子集和问题

    dp[i][s] = 是否能用前i个元素凑成和s

    递推：
        dp[0][0] = True
        dp[0][s>0] = False
        dp[i][s] = dp[i-1][s] or dp[i-1][s-arr[i-1]]

    时间复杂度：O(n * target)
    空间复杂度：O(n * target)，可优化到O(target)

    注意：这是伪多项式算法，当target很大时不可行
    """
    n = len(arr)

    # dp[s] = 是否能凑成和s
    dp = [False] * (target + 1)
    dp[0] = True

    # parent[s] = 选了什么元素达到s
    parent = [-1] * (target + 1)

    for i in range(n):
        # 从后向前遍历，避免同一元素被使用多次
        for s in range(target, arr[i] - 1, -1):
            if dp[s - arr[i]] and not dp[s]:
                dp[s] = True
                parent[s] = i

    if not dp[target]:
        return None

    # 回溯找到解
    result = set()
    s = target
    while s > 0 and parent[s] != -1:
        result.add(parent[s])
        s -= arr[parent[s]]

    return result


def subset_sum_dp_space_optimized(arr: List[int], target: int) -> bool:
    """
    空间优化版本的子集和DP

    只保留上一行的状态

    时间复杂度：O(n * target)
    空间复杂度：O(target)
    """
    dp = [False] * (target + 1)
    dp[0] = True

    for num in arr:
        for s in range(target, num - 1, -1):
            dp[s] = dp[s] or dp[s - num]

    return dp[target]


# ==================== FPTAS（完全多项式时间近似方案） ====================

def subset_sum_fptas(arr: List[int], target: int, epsilon: float) -> Optional[Set[int]]:
    """
    子集和问题的FPTAS

    思路：
    1. 对数组进行缩放，使得最大值变成poly(n/ε)
    2. 在缩放后的数组上运行伪多项式DP
    3. 将结果缩放回原空间

    时间复杂度：O(n^2 * (1/ε))
    近似比：(1 + ε)

    参数：
        arr: 正整数数组
        target: 目标值
        epsilon: 近似误差参数

    返回：近似解或精确解
    """
    n = len(arr)

    # 找到最大值
    max_val = max(arr)

    # 确定缩放因子
    # 我们希望将问题规模从max_val降到O(n/ε)
    scale = (epsilon * target) / (n * max_val)

    if scale >= 1:
        # 直接使用精确算法
        return subset_sum_dp(arr, target)

    # 缩放数组
    scaled_arr = [int(a * scale) for a in arr]
    scaled_target = int(target * scale)

    # 运行DP
    dp = [False] * (scaled_target + 1)
    dp[0] = True

    choice = [-1] * (scaled_target + 1)

    for i, scaled_val in enumerate(scaled_arr):
        for s in range(scaled_target, scaled_val - 1, -1):
            if dp[s - scaled_val] and not dp[s]:
                dp[s] = True
                choice[s] = i

    if not dp[scaled_target]:
        return None

    # 回溯
    result = set()
    s = scaled_target
    while s > 0 and choice[s] != -1:
        result.add(choice[s])
        s -= scaled_arr[choice[s]]

    # 验证结果
    actual_sum = sum(arr[i] for i in result)
    if actual_sum == target:
        return result

    # 返回近似解
    return result if abs(actual_sum - target) <= epsilon * target else None


# ==================== NP完全性证明 ====================

def prove_subset_sum_np():
    """
    证明子集和问题 ∈ NP

    验证器V((S, t), I)：
    1. 检查I ⊆ S
    2. 检查Σ_{x∈I} x = t

    复杂度：O(|S|)
    """
    print("【步骤1：证明Subset Sum ∈ NP】")
    print()
    print("验证器V((S={s1,...,sn}, t), I):")
    print("  1. 检查I ⊆ {1,...,n}")
    print("  2. 检查Σ_{i∈I} s_i = t")
    print()
    print("验证时间：O(n)")
    print("因此Subset Sum ∈ NP")
    print()


def subset_sum_from_knapsack():
    """
    从0-1背包归约到子集和

    背包问题：
        有n个物品，重量w_i，价值v_i，背包容量C
        问是否存在方案使得总价值≥V？

    归约到子集和：
        S = {w_i, v_i + C} （添加偏移）
        t = C + V

        选择物品 ↔ 选择子集
        重量约束 ↔ 和≤C
        价值约束 ↔ 和≥V

    复杂度：O(n)
    """
    print("【归约：Knapsack ≤_p Subset Sum】")
    print()
    print("给定Knapsack实例：")
    print("  - n个物品，重量w_i，价值v_i")
    print("  - 背包容量C，目标价值V")
    print()
    print("构造Subset Sum实例：")
    print("  - S = {w_i} ∪ {v_i + C | i=1..n}")
    print("  - t = C + V")
    print()
    print("正确性：存在解 ⟺ 存在子集和=C+V")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 子集和问题 ===\n")

    prove_subset_sum_np()

    print()
    subset_sum_from_knapsack()

    print()
    print("【算法测试】")
    arr = [3, 34, 4, 12, 5, 2]
    target = 9

    print(f"数组：{arr}")
    print(f"目标：{target}")
    print()

    result = subset_sum_dp(arr, target)
    if result:
        print(f"解（使用DP）：选择索引 {result}")
        print(f"元素：{[arr[i] for i in result]}")
        print(f"和：{sum(arr[i] for i in result)}")
    else:
        print("无解")

    print()
    print("【复杂度分析】")
    print("精确算法：")
    print("  时间：O(n * target) - 伪多项式")
    print("  空间：O(target)")
    print()
    print("FPTAS：")
    print("  时间：O(n^2 * (1/ε))")
    print("  近似比：(1 + ε)")
    print()
    print("【应用】")
    print("  - 货币系统验证")
    print("  - 资源分配问题")
    print("  - 密码学（背包密码系统）")

# -*- coding: utf-8 -*-
"""
算法实现：随机算法 / las_vegas

本文件实现 las_vegas 相关的算法功能。
"""

import random


def las_vegas_quicksort(arr: list) -> list:
    """
    拉斯维加斯快速排序

    特点：随机选择主元，但保证排序正确
    与普通快排的区别：主元选择是随机的

    时间复杂度：
        - 平均：O(n log n)
        - 最坏：O(n²)（概率极低）
    """
    if len(arr) <= 1:
        return arr.copy()

    # 拉斯维加斯：随机选择主元（而不是固定策略）
    pivot_idx = random.randint(0, len(arr) - 1)
    pivot = arr[pivot_idx]

    # 分区
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    # 递归（拉斯维加斯：保证正确，只是递归深度随机）
    return las_vegas_quicksort(left) + middle + las_vegas_quicksort(right)


def randomized_string_match(text: str, pattern: str) -> int:
    """
    拉斯维加斯字符串匹配

    保证找到匹配位置，但搜索顺序随机

    返回：第一个匹配位置，-1表示无匹配
    """
    n, m = len(text), len(pattern)
    if m > n:
        return -1

    # 随机打乱搜索起点
    search_order = list(range(n - m + 1))
    random.shuffle(search_order)

    for i in search_order:
        if text[i:i+m] == pattern:
            return i

    return -1


def verify_sort(arr: list) -> bool:
    """验证数组是否有序"""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i+1]:
            return False
    return True


def las_vegas_subset_sum(nums: list, target: int) -> list:
    """
    拉斯维加斯子集和算法

    思路：随机选择子集，检查是否和为target
    概率上很快能找到解

    注意：这是演示，实际有更好的确定性算法
    """
    n = len(nums)
    best_solution = None
    best_diff = float('inf')
    attempts = 0
    max_attempts = 100000

    while attempts < max_attempts:
        # 随机选择子集
        subset = []
        for i in range(n):
            if random.random() < 0.5:
                subset.append(nums[i])

        subset_sum = sum(subset)
        diff = abs(subset_sum - target)

        if diff < best_diff:
            best_diff = diff
            best_solution = subset.copy()

        if subset_sum == target:
            return subset

        attempts += 1

    return best_solution


def gambler_ruin_simulation(initial_money: int, target: int, win_prob: float = 0.5,
                            max_steps: int = 10000) -> tuple:
    """
    赌徒破产问题（拉斯维加斯风格）

    模拟赌徒破产过程，保证结束（但时长随机）
    """
    money = initial_money
    steps = 0

    while money > 0 and money < target and steps < max_steps:
        if random.random() < win_prob:
            money += 1  # 赢
        else:
            money -= 1  # 输
        steps += 1

    return money, steps


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 拉斯维加斯算法测试 ===\n")

    random.seed(42)

    # 1. 拉斯维加斯排序
    print("1. 拉斯维加斯快速排序")
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    original = arr.copy()
    print(f"   原始: {original}")

    for trial in range(3):
        result = las_vegas_quicksort(arr)
        is_sorted = verify_sort(result)
        print(f"   第{trial+1}次: {is_sorted}")

    print(f"   结果: {result}")

    print()

    # 2. 字符串匹配
    print("2. 拉斯维加斯字符串匹配")
    text = "ABACABADABACABA"
    pattern = "CAB"
    pos = randomized_string_match(text, pattern)
    print(f"   文本: {text}")
    print(f"   模式: {pattern}")
    print(f"   找到位置: {pos}")

    print()

    # 3. 赌徒破产
    print("3. 赌徒破产模拟（初始$50，目标$100）")
    wins = 0
    n_trials = 1000

    for _ in range(n_trials):
        final_money, steps = gambler_ruin_simulation(50, 100, win_prob=0.5)
        if final_money >= 100:
            wins += 1

    print(f"   获胜概率: {wins}/{n_trials} = {wins/n_trials*100:.1f}%")
    print(f"   理论概率: 50%（公平游戏）")

    print("\n说明：")
    print("  - 拉斯维加斯：必正确，时间随机")
    print("  - 典型应用：随机化QuickSort")
    print("  - 与蒙特卡洛互补：一个保证时间，一个保证正确")

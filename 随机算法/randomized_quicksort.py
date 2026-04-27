# -*- coding: utf-8 -*-
"""
算法实现：随机算法 / randomized_quicksort

本文件实现 randomized_quicksort 相关的算法功能。
"""

import random


def partition(arr: list, low: int, high: int) -> int:
    """
    分区操作

    选择最后一个元素作为主元
    将数组分为小于主元和大于主元两部分
    """
    pivot = arr[high]
    i = low - 1

    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def randomized_partition(arr: list, low: int, high: int) -> int:
    """
    随机分区

    拉斯维加斯思想：随机选择主元位置
    """
    # 随机选择主元索引
    pivot_idx = random.randint(low, high)
    # 交换到末尾
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    # 标准分区
    return partition(arr, low, high)


def randomized_quicksort(arr: list, low: int = None, high: int = None) -> list:
    """
    随机化快速排序

    参数：
        arr: 待排序数组
        low, high: 排序范围（递归用）

    返回：排序后的数组（原地排序）
    """
    if low is None:
        low = 0
    if high is None:
        high = len(arr) - 1

    if low < high:
        # 随机分区
        pivot_idx = randomized_partition(arr, low, high)

        # 递归排序左右两边
        randomized_quicksort(arr, low, pivot_idx - 1)
        randomized_quicksort(arr, pivot_idx + 1, high)

    return arr


def randomized_quicksort_iterative(arr: list) -> list:
    """
    迭代版本随机快速排序（使用栈）

    避免递归栈溢出
    """
    arr = arr.copy()
    stack = [(0, len(arr) - 1)]

    while stack:
        low, high = stack.pop()

        if low < high:
            pivot_idx = randomized_partition(arr, low, high)

            # 将大区间入栈
            if pivot_idx - low < high - pivot_idx:
                stack.append((low, pivot_idx - 1))
                stack.append((pivot_idx + 1, high))
            else:
                stack.append((pivot_idx + 1, high))
                stack.append((low, pivot_idx - 1))

    return arr


def analyze_expected_depth(low: int, high: int) -> int:
    """
    分析递归树期望深度

    随机主元选择下，期望深度为O(log n)
    """
    n = high - low + 1
    if n <= 1:
        return 0

    # 期望深度 ≈ 2 * ln(n)
    import math
    return int(2 * math.log(n))


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 随机化快速排序测试 ===\n")

    random.seed(42)

    # 测试用例
    test_cases = [
        [64, 34, 25, 12, 22, 11, 90, 45, 33, 77, 55],
        list(range(20, 0, -1)),  # 逆序
        [1],
        [2, 1],
        list(range(1, 101)),  # 较大有序
    ]

    for arr in test_cases:
        original = arr.copy()
        result = randomized_quicksort(arr.copy())

        is_sorted = all(result[i] <= result[i+1] for i in range(len(result)-1))

        print(f"原始前5个: {original[:5]}...")
        print(f"结果前5个: {result[:5]}...")
        print(f"排序正确: {'✅' if is_sorted else '❌'}")
        print()

    # 性能测试
    import time

    print("性能测试：")
    sizes = [1000, 10000, 50000]

    for size in sizes:
        arr = [random.randint(1, 10000) for _ in range(size)]

        start = time.time()
        randomized_quicksort(arr.copy())
        elapsed = time.time() - start

        print(f"  n={size:5d}: {elapsed*1000:.2f}ms")

    print()

    # 对比普通快排（固定主元）
    print("vs 普通快速排序（固定主元）:")
    arr = list(range(1000, 0, -1))  # 最坏情况

    start = time.time()
    randomized_quicksort(arr.copy())
    rand_time = time.time() - start

    start = time.time()
    # 普通快排用最后一个元素作主元
    def normal_quicksort(a, lo, hi):
        if lo < hi:
            p = partition(a, lo, hi)
            normal_quicksort(a, lo, p - 1)
            normal_quicksort(a, p + 1, hi)

    arr2 = list(range(1000, 0, -1))
    normal_quicksort(arr2, 0, len(arr2) - 1)
    normal_time = time.time() - start

    print(f"  随机化快排（最坏输入）: {rand_time*1000:.2f}ms")
    print(f"  普通快排（最坏输入）: {normal_time*1000:.2f}ms")

    print("\n说明：")
    print("  - 随机主元使最坏情况概率极低")
    print("  - 期望时间O(n log n)")
    print("  - Python的Timsort实际更常用")

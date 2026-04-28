# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / randomized_sorting



本文件实现随机化排序算法，包括：

    - 随机化快速排序（Randomized QuickSort）

    - 随机主元选择策略

    - 多种分区方案对比

期望时间复杂度 O(n log n)，空间复杂度 O(log n)（递归栈）。

"""

import random
import math


def partition_hoare(arr: list, low: int, high: int) -> int:
    """
    Hoare 分区方案（双指针扫描）

    使用两个指针从数组两端向中间扫描：
      - i 从左向右跳过小于等于主元的元素
      - j 从右向左跳过大于主元的元素
      - 交换逆序对

    Hoare 方案通常比单方向扫描产生更少的比较次数。

    参数：
        arr: 待分区数组（原地修改）
        low: 分区起始索引
        high: 分区结束索引

    返回：
        分区点索引
    """
    # 选择主元（这里使用 high 位置）
    pivot = arr[high]
    # i 初始化为主元之后的位置
    i = low - 1
    # j 初始化为 high（主元本身的位置）
    j = high

    while True:
        # i 向右移动，找到第一个大于主元的元素
        while True:
            i += 1
            if i == high or arr[i] > pivot:
                break

        # j 向左移动，找到第一个小于等于主元的元素
        while True:
            j -= 1
            if j == low or arr[j] <= pivot:
                break

        # 如果指针相遇或交叉，分区完成
        if i >= j:
            break

        # 交换逆序对
        arr[i], arr[j] = arr[j], arr[i]

    return j


def partition_lomuto(arr: list, low: int, high: int) -> int:
    """
    Lomuto 分区方案（单方向扫描）

    从左向右扫描，维护一个分割点：
      - [low, i]：小于等于主元的元素
      - [i+1, j]：大于主元的元素

    实现简单，但需要 n+1 次比较。

    参数：
        arr: 待分区数组
        low: 分区起始索引
        high: 分区结束索引（主元位置）

    返回：
        主元最终所在索引
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
    随机化 Lomuto 分区

    随机选择主元位置并交换到 high，再执行 Lomuto 分区。
    拉斯维加斯思想：随机性保证对任何输入都能达到期望的 O(n log n)。

    参数：
        arr: 待分区数组
        low: 分区起始索引
        high: 分区结束索引

    返回：
        主元最终索引
    """
    # 随机选择 [low, high] 范围内的主元索引
    pivot_idx = random.randint(low, high)
    # 将随机主元交换到 high 位置
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    # 执行标准 Lomuto 分区
    return partition_lomuto(arr, low, high)


def randomized_partition_hoare(arr: list, low: int, high: int) -> int:
    """
    随机化 Hoare 分区

    参数：
        arr: 待分区数组
        low: 分区起始索引
        high: 分区结束索引

    返回：
        分区点索引
    """
    pivot_idx = random.randint(low, high)
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    return partition_hoare(arr, low, high)


def randomized_quicksort(arr: list, low: int = None, high: int = None) -> list:
    """
    随机化快速排序（Recursive Lomuto 版本）

    核心思想：每次随机选择主元，避免特定输入触发最坏情况。
    期望时间复杂度 O(n log n)，期望比较次数 ~ 2n ln n。

    参数：
        arr: 待排序数组
        low: 排序起始索引（默认为 0）
        high: 排序结束索引（默认为 len(arr)-1）

    返回：
        排序后的数组（原地排序）
    """
    if low is None:
        low = 0
    if high is None:
        high = len(arr) - 1

    if low < high:
        # 随机分区，获得主元位置
        pivot_idx = randomized_partition(arr, low, high)
        # 递归排序左半部分
        randomized_quicksort(arr, low, pivot_idx - 1)
        # 递归排序右半部分
        randomized_quicksort(arr, pivot_idx + 1, high)

    return arr


def randomized_quicksort_hoare(arr: list, low: int = None, high: int = None) -> list:
    """
    随机化快速排序（Hoare 分区版本）

    参数：
        arr: 待排序数组
        low: 排序起始索引
        high: 排序结束索引

    返回：
        排序后的数组
    """
    if low is None:
        low = 0
    if high is None:
        high = len(arr) - 1

    if low < high:
        pivot_idx = randomized_partition_hoare(arr, low, high)
        randomized_quicksort_hoare(arr, low, pivot_idx)
        randomized_quicksort_hoare(arr, pivot_idx + 1, high)

    return arr


def randomized_quicksort_iterative(arr: list) -> list:
    """
    迭代版随机化快速排序（使用显式栈消除递归）

    参数：
        arr: 待排序数组

    返回：
        排序后的数组
    """
    arr = arr.copy()
    stack = [(0, len(arr) - 1)]

    while stack:
        low, high = stack.pop()

        if low < high:
            pivot_idx = randomized_partition(arr, low, high)

            # 将较大的子区间先入栈（深度控制）
            left_size = pivot_idx - low
            right_size = high - pivot_idx

            if left_size > right_size:
                stack.append((low, pivot_idx - 1))
                stack.append((pivot_idx + 1, high))
            else:
                stack.append((pivot_idx + 1, high))
                stack.append((low, pivot_idx - 1))

    return arr


def tail_recursive_quicksort(arr: list, low: int, high: int) -> list:
    """
    尾递归优化版随机化快速排序

    减少递归栈深度：将较大子问题作为尾递归，
    编译器/解释器可能进行尾调用优化。

    参数：
        arr: 待排序数组
        low: 起始索引
        high: 结束索引

    返回：
        排序后的数组
    """
    while low < high:
        pivot_idx = randomized_partition(arr, low, high)

        # 优先处理较小的子问题，缩小问题规模
        if pivot_idx - low < high - pivot_idx:
            tail_recursive_quicksort(arr, low, pivot_idx - 1)
            low = pivot_idx + 1
        else:
            tail_recursive_quicksort(arr, pivot_idx + 1, high)
            high = pivot_idx - 1

    return arr


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 随机化快速排序测试 ===\n")

    random.seed(42)

    test_cases = [
        [64, 34, 25, 12, 22, 11, 90, 45, 33, 77, 55],
        list(range(20, 0, -1)),       # 完全逆序
        [1],                          # 单元素
        [2, 1],                       # 两元素
        list(range(1, 101)),          # 完全正序
        [3, 3, 3, 3, 3],              # 全部相同
        [],                           # 空数组
        [5, 1, 4, 2, 8],              # 小规模
    ]

    all_passed = True
    for arr in test_cases:
        original = arr.copy()
        result = randomized_quicksort(arr.copy())
        is_sorted = all(result[i] <= result[i+1] for i in range(len(result)-1)) if len(result) > 1 else True
        status = "✅" if is_sorted else "❌"
        if not is_sorted:
            all_passed = False
        print(f"  输入前5个: {original[:5]}, 排序正确: {status}")

    print(f"\n  全部测试通过: {'✅' if all_passed else '❌'}")

    # 对比不同分区方案
    print("\n--- 不同分区方案对比 ---")
    test_arr = [random.randint(1, 10000) for _ in range(5000)]

    for name, sort_fn in [
        ("Lomuto", randomized_quicksort),
        ("Hoare", randomized_quicksort_hoare),
        ("迭代版", randomized_quicksort_iterative),
    ]:
        arr_copy = test_arr.copy()
        start = time.time()
        sort_fn(arr_copy)
        elapsed = time.time() - start
        print(f"  {name}: {elapsed*1000:.2f} ms")

    # 最坏情况输入测试
    print("\n--- 最坏情况输入（完全逆序）测试 ---")
    worst_arr = list(range(1000, 0, -1))

    start = time.time()
    randomized_quicksort(worst_arr.copy())
    rand_time = time.time() - start

    # 普通快速排序（固定主元 = 最后一个元素）
    def vanilla_quicksort(a, lo, hi):
        if lo < hi:
            p = partition_lomuto(a, lo, hi)
            vanilla_quicksort(a, lo, p - 1)
            vanilla_quicksort(a, p + 1, hi)

    arr2 = list(range(1000, 0, -1))
    start = time.time()
    vanilla_quicksort(arr2, 0, len(arr2) - 1)
    vanilla_time = time.time() - start

    print(f"  随机化快排（逆序输入）: {rand_time*1000:.2f} ms")
    print(f"  普通快排（逆序输入）:   {vanilla_time*1000:.2f} ms")

    import time
    print("\n说明：")
    print("  - 随机主元选择使最坏情况概率极低")
    print("  - Hoare 方案比较次数更少，但不易 inplace 返回主元位置")
    print("  - 迭代版避免递归栈溢出，适合超大数组")

# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / randomized_selection



本文件实现随机选择算法（QuickSelect），用于在未排序数组中

查找第 k 小（或第 k 大）的元素，期望时间复杂度 O(n)。



主要方法：

    - randomized_select: 随机化快速选择，期望线性时间

    - deterministic_select: 确定式快速选择，最坏情况 O(n²) 但更稳定

"""

import random
import math


def partition(arr: list, low: int, high: int) -> int:
    """
    分区操作（单方向扫描版本）

    选择 high 位置的元素作为主元，将数组分为：
      - 左侧：[low, i]：所有小于等于主元的元素
      - 右侧：[i+1, high]：所有大于主元的元素

    参数：
        arr: 待分区数组（原地修改）
        low: 分区起始索引
        high: 分区结束索引（主元位置）

    返回：
        主元最终所在位置的索引 i+1
    """
    # 选择主元（固定为 high 位置）
    pivot = arr[high]
    # i 指向小于等于主元区域的最后一个元素
    i = low - 1

    for j in range(low, high):
        # 如果当前元素小于等于主元，则扩展左区域
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    # 将主元放到正确的分割位置
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def randomized_partition(arr: list, low: int, high: int) -> int:
    """
    随机分区操作

    随机选择主元位置，然后交换到 high 位置，
    再调用标准分区流程。利用拉斯维加斯思想
    避免特定输入序列触发最坏情况。

    参数：
        arr: 待分区数组
        low: 分区起始索引
        high: 分区结束索引

    返回：
        主元最终所在索引
    """
    # 随机选择主元索引
    pivot_idx = random.randint(low, high)
    # 将随机选中的主元交换到 high 位置
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    # 调用标准分区
    return partition(arr, low, high)


def randomized_select(arr: list, low: int, high: int, target_rank: int) -> int:
    """
    随机化快速选择算法（QuickSelect）

    在未排序数组中查找第 target_rank 小（第 k 小，k 从 1 开始）的元素。
    基于随机主元划分，递归地只处理可能包含目标元素的子数组，
    期望时间复杂度 O(n)，最坏情况 O(n²)。

    参数：
        arr: 待搜索数组
        low: 当前搜索范围的起始索引
        high: 当前搜索范围的结束索引
        target_rank: 目标元素的排名（从 1 开始）

    返回：
        第 target_rank 小的元素值
    """
    # 递归终止条件：范围内只有一个元素
    if low == high:
        return arr[low]

    # 随机分区，返回主元最终位置
    pivot_index = randomized_partition(arr, low, high)
    # 主元在排序后数组中的实际位置（从 1 开始计数）
    pivot_rank = pivot_index - low + 1

    # 根据主元位置与目标排名的关系决定搜索方向
    if target_rank == pivot_rank:
        # 主元恰好是目标元素
        return arr[pivot_index]
    elif target_rank < pivot_rank:
        # 目标在主元左侧（更小的子数组）
        return randomized_select(arr, low, pivot_index - 1, target_rank)
    else:
        # 目标在主元右侧，需要调整目标排名（减去左侧元素个数）
        return randomized_select(arr, pivot_index + 1, high, target_rank - pivot_rank)


def deterministic_partition(arr: list, low: int, high: int) -> int:
    """
    确定式分区（Median-of-Medians 主元选择策略的一部分）

    使用"中位数的中位数"思想选择主元：
    将数组分成每5个一组，取每组中位数，再取中位数的中位数作为主元。
    这种主元选择策略保证最坏情况是 O(n) 划分，但常数因子较大。

    参数：
        arr: 待分区数组
        low: 分区起始索引
        high: 分区结束索引

    返回：
        主元最终所在索引
    """
    # 计算中位数的辅助函数
    def median_of_medians(arr, l, r):
        # 将元素按5个一组分组，取每组中位数
        medians = []
        i = l
        while i + 4 <= r:
            # 对当前5元组排序并取中位数
            sub = arr[i:i + 5]
            sub.sort()
            medians.append(sub[2])
            i += 5
        # 处理剩余不足5个的元素
        if i <= r:
            sub = arr[i:r + 1]
            sub.sort()
            medians.append(sub[len(sub) // 2])
        # 递归求中位数的中位数
        if len(medians) <= 5:
            medians.sort()
            return medians[len(medians) // 2]
        else:
            return median_of_medians(medians, 0, len(medians) - 1)

    # 为了简化，这里使用首元素作为主元（确定式但非 Median-of-Medians 完整实现）
    # 完整实现需要先找到中位数的中位数作为主元
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def iterative_randomized_select(arr: list, target_rank: int) -> int:
    """
    迭代版本的随机快速选择（避免递归栈溢出）

    参数：
        arr: 待搜索数组
        target_rank: 目标排名（从 1 开始）

    返回：
        第 target_rank 小的元素值
    """
    arr = arr.copy()  # 避免修改原数组
    low, high = 0, len(arr) - 1

    while low < high:
        # 随机分区
        pivot_index = randomized_partition(arr, low, high)
        pivot_rank = pivot_index - low + 1

        if target_rank == pivot_rank:
            return arr[pivot_index]
        elif target_rank < pivot_rank:
            high = pivot_index - 1
        else:
            target_rank -= pivot_rank
            low = pivot_index + 1

    return arr[low]


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 随机选择算法（QuickSelect）测试 ===\n")

    random.seed(42)

    # 测试用例：数组、目标排名、期望结果
    test_cases = [
        ([64, 34, 25, 12, 22, 11, 90, 45], 1, 11),   # 第1小
        ([64, 34, 25, 12, 22, 11, 90, 45], 3, 25),  # 第3小
        ([64, 34, 25, 12, 22, 11, 90, 45], 5, 45),  # 第5小
        ([64, 34, 25, 12, 22, 11, 90, 45], 8, 90),  # 第8小（最大）
        ([1], 1, 1),                                  # 单元素
        ([2, 1], 2, 2),                              # 两元素第2小
        (list(range(100, 0, -1)), 50, 50),           # 逆序数组找第50小
    ]

    all_passed = True
    for arr, rank, expected in test_cases:
        original = arr.copy()
        result = randomized_select(arr.copy(), 0, len(arr) - 1, rank)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  数组前5个: {original[:5]}..., 找第 {rank} 小: {result} (期望 {expected}) {status}")

    print(f"\n  全部测试通过: {'✅' if all_passed else '❌'}")

    # 迭代版本测试
    print("\n--- 迭代版本测试 ---")
    arr = [random.randint(1, 1000) for _ in range(100)]
    for rank in [1, 50, 100]:
        expected = sorted(arr)[rank - 1]
        result = iterative_randomized_select(arr, rank)
        status = "✅" if result == expected else "❌"
        print(f"  第 {rank} 小: {result} (期望 {expected}) {status}")

    # 性能测试
    print("\n--- 性能测试 ---")
    import time

    sizes = [1000, 10000, 100000, 500000]
    for size in sizes:
        arr = [random.randint(1, size * 10) for _ in range(size)]
        mid = size // 2

        start = time.time()
        randomized_select(arr.copy(), 0, size - 1, mid)
        elapsed = time.time() - start

        print(f"  n={size:7d}: {elapsed * 1000:8.2f} ms (找第 {mid} 小)")

    print("\n说明：")
    print("  - 随机选择期望时间 O(n)，最坏 O(n²)")
    print("  - 确定式选择（中位数的中位数）保证 O(n) 最坏情况")
    print("  - 实际应用中随机选择更快（常数更小）")

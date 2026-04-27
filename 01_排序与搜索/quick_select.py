# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / quick_select

本文件实现 quick_select 相关的算法功能。
"""

import random


def _partition(data: list, pivot) -> tuple:
    """
    三路划分：将数据分为小于、等于、大于 pivot 三部分

    参数:
        data: 要划分的数组
        pivot: 基准元素

    返回:
        (小于部分, 等于部分, 大于部分) 三个列表
    """
    less, equal, greater = [], [], []

    for element in data:
        if element < pivot:
            less.append(element)
        elif element > pivot:
            greater.append(element)
        else:
            equal.append(element)

    return less, equal, greater


def quick_select(items: list, index: int):
    """
    快速选择：在无序数组中找到第 index 小的元素

    参数:
        items: 输入数组
        index: 目标排名（0-based，即 index=0 是最小值）

    返回:
        第 index 小的元素值

    注意：
        - 如果 index 超出范围，返回 None
        - 当 index = len(items)//2 时，可用于找中位数

    示例:
        >>> quick_select([2, 4, 5, 7, 899, 54, 32], 5)
        54
        >>> quick_select([2, 4, 5, 7, 899, 54, 32], 1)
        4
        >>> quick_select([5, 4, 3, 2], 2)
        4
        >>> quick_select([3, 5, 7, 10, 2, 12], 3)
        7
    """
    # 非法输入检查
    if index >= len(items) or index < 0:
        return None

    # 随机选择基准（避免最坏情况）
    pivot = items[random.randint(0, len(items) - 1)]

    # 三路划分
    smaller, equal, larger = _partition(items, pivot)

    # 计算各部分大小
    count = len(equal)
    m = len(smaller)  # smaller 部分的大小

    # 判断目标落在哪部分
    if m <= index < m + count:
        # 命中基准
        return pivot
    elif m > index:
        # 目标在 smaller 部分
        return quick_select(smaller, index)
    else:
        # 目标在 larger 部分（索引需要调整）
        return quick_select(larger, index - (m + count))


def median(items: list):
    """
    中位数计算（使用快速选择）

    应用场景：
        - 统计数据分析
        - 防止被极端值影响（比平均值更稳健）
        - 作为其他算法的基准

    参数:
        items: 输入数组

    返回:
        单元素数组的中位数：直接返回值
        双元素数组的中位数：两元素的平均值

    示例:
        >>> median([3, 2, 2, 9, 9])
        3
        >>> median([2, 2, 9, 9, 9, 3])
        6.0
    """
    mid, rem = divmod(len(items), 2)

    if rem != 0:
        # 奇数长度：中位数是中间那个元素
        return quick_select(items=items, index=mid)
    else:
        # 偶数长度：中位数是中间两个元素的平均值
        low_mid = quick_select(items=items, index=mid - 1)
        high_mid = quick_select(items=items, index=mid)
        return (low_mid + high_mid) / 2


if __name__ == "__main__":
    # 功能测试
    print("=== 快速选择算法测试 ===\n")

    test_cases = [
        ([2, 4, 5, 7, 899, 54, 32], 5),
        ([2, 4, 5, 7, 899, 54, 32], 1),
        ([5, 4, 3, 2], 2),
        ([3, 5, 7, 10, 2, 12], 3),
    ]

    print("快速选择测试：")
    for arr, idx in test_cases:
        result = quick_select(arr, idx)
        sorted_arr = sorted(arr)
        expected = sorted_arr[idx]
        status = "✓" if result == expected else "✗"
        print(f"  {status} quick_select({arr}, {idx}) = {result} (期望: {expected})")

    print("\n中位数测试：")
    print(f"  median([3, 2, 2, 9, 9]) = {median([3, 2, 2, 9, 9])} (期望: 3)")
    print(f"  median([2, 2, 9, 9, 9, 3]) = {median([2, 2, 9, 9, 9, 3])} (期望: 6.0)")

    print("\n大规模测试：")
    large_arr = list(range(1000))
    random.shuffle(large_arr)
    for k in [0, 100, 500, 999]:
        result = quick_select(large_arr, k)
        status = "✓" if result == k else "✗"
        print(f"  {status} 第{k}小元素: {result}")

    print("\n=== 所有测试完成 ===")

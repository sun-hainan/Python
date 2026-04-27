# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / quick_sort

本文件实现 quick_sort 相关的算法功能。
"""

from __future__ import annotations
from random import randrange


def quick_sort(collection: list) -> list:
    """
    快速排序

    参数:
        collection: 可变集合，包含可比较的元素

    返回:
        同一集合，按升序排列

    示例:
        >>> quick_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> quick_sort([])
        []
        >>> quick_sort([-2, 5, 0, -45])
        [-45, -2, 0, 5]
    """
    # 递归终止条件：单个元素或空数组已有序
    if len(collection) < 2:
        return collection

    # 随机选择基准元素（避免最坏情况）
    pivot_index = randrange(len(collection))
    pivot = collection.pop(pivot_index)

    # 分区：将元素分成 <= pivot 和 > pivot 两组
    lesser = [item for item in collection if item <= pivot]
    greater = [item for item in collection if item > pivot]

    # 递归排序并合并结果
    return [*quick_sort(lesser), pivot, *quick_sort(greater)]


if __name__ == "__main__":
    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(quick_sort(unsorted))

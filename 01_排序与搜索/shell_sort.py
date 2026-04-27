# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / shell_sort

本文件实现 shell_sort 相关的算法功能。
"""

from __future__ import annotations


def shell_sort(collection: list[int]) -> list[int]:
    """
    希尔排序

    参数:
        collection: 可变集合，包含可比较的元素

    返回:
        同一集合，按升序排列

    示例:
        >>> shell_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> shell_sort([])
        []
        >>> shell_sort([-2, -5, -45])
        [-45, -5, -2]
    """
    # Marcin Ciura 的最优增量序列
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]

    # 逐步缩小增量
    for gap in gaps:
        # 对每个子数组进行插入排序
        for i in range(gap, len(collection)):
            insert_value = collection[i]  # 待插入元素
            j = i

            # 在子数组中找到正确位置
            # 子数组间隔为 gap
            while j >= gap and collection[j - gap] > insert_value:
                collection[j] = collection[j - gap]
                j -= gap

            if j != i:
                collection[j] = insert_value

    return collection


if __name__ == "__main__":
    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(f"排序结果: {shell_sort(unsorted)}")

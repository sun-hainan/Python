"""
快速排序 (Quick Sort) - 中文注释版
==========================================

算法原理：
    快速排序是一种高效的分治排序算法，也是面试中最常考的排序算法。
    它通过选择一个"基准元素"（pivot），将数组分成两部分：
    左半部分所有元素 <= pivot，右半部分所有元素 > pivot。
    然后递归处理左右两部分。

算法步骤：
    1. 选择一个基准元素（通常随机选择）
    2. 分区（partition）：将数组分成两部分
    3. 递归对左右两部分执行快速排序
    4. 合并结果

时间复杂度：
    - 平均: O(n log n)
    - 最坏: O(n²)（每次都选到最大/最小值）
    - 最好: O(n log n)

空间复杂度：O(log n)（递归调用栈）

算法特点：
    - 不稳定排序
    - 是实际应用中最常用的排序算法
    - 通过随机选择 pivot 可以避免最坏情况
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

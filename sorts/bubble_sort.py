"""
冒泡排序 (Bubble Sort) - 中文注释版
==========================================

算法原理：
    冒泡排序是最基础的排序算法之一。它重复地遍历要排序的列表，
    比较相邻的两个元素，如果顺序错误就交换它们。
    遍历重复进行，直到没有需要交换的元素为止，此时列表已完全排序。

时间复杂度：
    - 平均: O(n²)
    - 最坏: O(n²)
    - 最好: O(n)（当列表已经有序时，可以优化提前终止）

空间复杂度：O(1) - 原地排序

算法特点：
    - 稳定排序（相等的元素不会交换位置）
    - 简单直观，适合初学者学习
    - 对于大规模数据效率较低，实际应用中较少使用
"""
from typing import Any


def bubble_sort_iterative(collection: list[Any]) -> list[Any]:
    """冒泡排序（迭代版）

    参数:
        collection: 一个可变的有序集合，包含可比较的元素

    返回:
        同一个集合，按升序排列

    算法步骤:
        1. 从列表第一个元素开始，比较相邻的两个元素
        2. 如果前一个元素大于后一个元素，则交换它们
        3. 每一轮遍历后，最大的元素会"冒泡"到最后
        4. 重复上述过程，直到没有需要交换的元素

    示例:
        >>> bubble_sort_iterative([0, 5, 2, 3, 2])
        [0, 2, 2, 3, 5]
        >>> bubble_sort_iterative([])
        []
        >>> bubble_sort_iterative([-2, -45, -5])
        [-45, -5, -2]
    """
    length = len(collection)
    # 从后向前遍历，每一轮确定一个最大元素的位置
    for i in reversed(range(length)):
        swapped = False  # 标记本轮是否有交换
        for j in range(i):
            # 比较相邻元素，如果顺序错误则交换
            if collection[j] > collection[j + 1]:
                swapped = True
                collection[j], collection[j + 1] = collection[j + 1], collection[j]
        # 如果本轮没有交换，说明列表已经有序，可以提前终止
        if not swapped:
            break
    return collection


def bubble_sort_recursive(collection: list[Any]) -> list[Any]:
    """冒泡排序（递归版）

    递归思路:
        1. 一轮遍历：将最大元素移动到最后
        2. 递归处理剩余的前 n-1 个元素
        3. 递归终止条件：没有元素需要交换

    示例:
        >>> bubble_sort_recursive([0, 5, 2, 3, 2])
        [0, 2, 2, 3, 5]
        >>> bubble_sort_recursive([])
        []
    """
    length = len(collection)
    swapped = False

    # 一轮遍历：比较相邻元素并交换
    for i in range(length - 1):
        if collection[i] > collection[i + 1]:
            collection[i], collection[i + 1] = collection[i + 1], collection[i]
            swapped = True

    # 如果没有交换，说明已经有序，递归终止
    # 否则递归处理剩余元素
    return collection if not swapped else bubble_sort_recursive(collection)


if __name__ == "__main__":
    import doctest
    from random import sample
    from timeit import timeit

    doctest.testmod()

    # 性能基准测试
    num_runs = 10_000
    unsorted = sample(range(-50, 50), 100)

    # 测试迭代版
    timer_iterative = timeit(
        "bubble_sort_iterative(unsorted[:])", globals=globals(), number=num_runs
    )
    print("\n迭代版冒泡排序:")
    print(*bubble_sort_iterative(unsorted), sep=",")
    print(f"处理时间 (迭代版): {timer_iterative:.5f}s ({num_runs:,} 次)")

    # 测试递归版
    unsorted = sample(range(-50, 50), 100)
    timer_recursive = timeit(
        "bubble_sort_recursive(unsorted[:])", globals=globals(), number=num_runs
    )
    print("\n递归版冒泡排序:")
    print(*bubble_sort_recursive(unsorted), sep=",")
    print(f"处理时间 (递归版): {timer_recursive:.5f}s ({num_runs:,} 次)")

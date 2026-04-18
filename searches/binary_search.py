#!/usr/bin/env python3

"""
二分搜索 (Binary Search) 算法 - 中文注释版
==========================================

算法原理：
    二分搜索用于在有序数组中查找目标元素。
    每一次查找都将搜索范围缩小一半，因此搜索效率为 O(log n)。

前提条件：
    - 数组必须有序（升序）
    - 元素必须支持比较操作

核心思想：
    1. 确定搜索范围的中间位置
    2. 比较中间元素与目标值
    3. 如果相等，找到目标，返回位置
    4. 如果目标较小，搜索左半部分
    5. 如果目标较大，搜索右半部分
    6. 重复直到找到目标或范围为空

时间复杂度：O(log n)
空间复杂度：O(1)（迭代版）/ O(log n)（递归版，因为调用栈）
"""

import bisect
from itertools import pairwise


def bisect_left(
    sorted_collection: list[int], item: int, lo: int = 0, hi: int = -1
) -> int:
    """
    查找第一个 >= 目标值的位置（左边界）

    与 Python 标准库 bisect.bisect_left 接口相同。

    参数:
        sorted_collection: 升序排列的集合
        item: 要查找的目标值
        lo: 搜索范围起始索引
        hi: 搜索范围结束索引（不包含）

    返回:
        索引 i，使得所有 sorted_collection[lo:i] < item
        所有 sorted_collection[i:hi] >= item

    示例:
        >>> bisect_left([0, 5, 7, 10, 15], 0)
        0
        >>> bisect_left([0, 5, 7, 10, 15], 6)
        2
    """
    if hi < 0:
        hi = len(sorted_collection)

    while lo < hi:
        mid = lo + (hi - lo) // 2
        if sorted_collection[mid] < item:
            lo = mid + 1
        else:
            hi = mid

    return lo


def bisect_right(
    sorted_collection: list[int], item: int, lo: int = 0, hi: int = -1
) -> int:
    """
    查找第一个 > 目标值的位置（右边界）

    与 Python 标准库 bisect.bisect_right 接口相同。

    返回:
        索引 i，使得所有 sorted_collection[lo:i] <= item
        所有 sorted_collection[i:hi] > item

    示例:
        >>> bisect_right([0, 5, 7, 10, 15], 0)
        1
        >>> bisect_right([0, 5, 7, 10, 15], 15)
        5
    """
    if hi < 0:
        hi = len(sorted_collection)

    while lo < hi:
        mid = lo + (hi - lo) // 2
        if sorted_collection[mid] <= item:
            lo = mid + 1
        else:
            hi = mid

    return lo


def insort_left(
    sorted_collection: list[int], item: int, lo: int = 0, hi: int = -1
) -> None:
    """
    将元素插入到已排序数组中（插入到相等元素的最左侧位置）

    示例:
        >>> sorted_collection = [0, 5, 7, 10, 15]
        >>> insort_left(sorted_collection, 6)
        >>> sorted_collection
        [0, 5, 6, 7, 10, 15]
    """
    sorted_collection.insert(bisect_left(sorted_collection, item, lo, hi), item)


def insort_right(
    sorted_collection: list[int], item: int, lo: int = 0, hi: int = -1
) -> None:
    """
    将元素插入到已排序数组中（插入到相等元素的最右侧位置）

    示例:
        >>> sorted_collection = [0, 5, 7, 10, 15]
        >>> insort_right(sorted_collection, 6)
        >>> sorted_collection
        [0, 5, 6, 7, 10, 15]
    """
    sorted_collection.insert(bisect_right(sorted_collection, item, lo, hi), item)


def binary_search(sorted_collection: list[int], item: int) -> int:
    """
    二分搜索（迭代版）

    在有序数组中查找目标值，返回其索引；如果未找到返回 -1。

    注意:
        数组必须升序排列，否则结果不可预测。

    参数:
        sorted_collection: 升序排列的集合
        item: 要查找的目标值

    返回:
        目标值的索引，未找到返回 -1

    示例:
        >>> binary_search([0, 5, 7, 10, 15], 0)
        0
        >>> binary_search([0, 5, 7, 10, 15], 15)
        4
        >>> binary_search([0, 5, 7, 10, 15], 6)
        -1
    """
    # 校验数组是否有序
    if any(a > b for a, b in pairwise(sorted_collection)):
        raise ValueError("sorted_collection 必须是升序排列")

    left = 0
    right = len(sorted_collection) - 1

    # 迭代搜索
    while left <= right:
        midpoint = left + (right - left) // 2  # 防止整数溢出
        current_item = sorted_collection[midpoint]

        if current_item == item:
            return midpoint
        elif item < current_item:
            # 目标在左半部分
            right = midpoint - 1
        else:
            # 目标在右半部分
            left = midpoint + 1

    return -1  # 未找到


def binary_search_std_lib(sorted_collection: list[int], item: int) -> int:
    """
    二分搜索（使用 Python 标准库 bisect）

    示例:
        >>> binary_search_std_lib([0, 5, 7, 10, 15], 5)
        1
        >>> binary_search_std_lib([0, 5, 7, 10, 15], 6)
        -1
    """
    if list(sorted_collection) != sorted(sorted_collection):
        raise ValueError("sorted_collection 必须是升序排列")

    index = bisect.bisect_left(sorted_collection, item)
    if index != len(sorted_collection) and sorted_collection[index] == item:
        return index
    return -1


def binary_search_with_duplicates(sorted_collection: list[int], item: int) -> list[int]:
    """
    二分搜索（支持重复元素）

    当目标值出现多次时，返回所有出现位置的索引列表。

    算法思想：
        1. 使用 lower_bound 找到第一个 >= 目标值的位置
        2. 使用 upper_bound 找到第一个 > 目标值的位置
        3. 两者之间的所有位置都是目标值出现的位置

    示例:
        >>> binary_search_with_duplicates([1, 2, 2, 2, 3], 2)
        [1, 2, 3]
        >>> binary_search_with_duplicates([1, 2, 2, 2, 3], 4)
        []
    """
    if list(sorted_collection) != sorted(sorted_collection):
        raise ValueError("sorted_collection 必须是升序排列")

    def lower_bound(sorted_collection: list[int], item: int) -> int:
        """查找第一个 >= item 的位置（左边界）"""
        left = 0
        right = len(sorted_collection)
        while left < right:
            midpoint = left + (right - left) // 2
            current_item = sorted_collection[midpoint]
            if current_item < item:
                left = midpoint + 1
            else:
                right = midpoint
        return left

    def upper_bound(sorted_collection: list[int], item: int) -> int:
        """查找第一个 > item 的位置（右边界）"""
        left = 0
        right = len(sorted_collection)
        while left < right:
            midpoint = left + (right - left) // 2
            current_item = sorted_collection[midpoint]
            if current_item <= item:
                left = midpoint + 1
            else:
                right = midpoint
        return left

    left = lower_bound(sorted_collection, item)
    right = upper_bound(sorted_collection, item)

    if left == len(sorted_collection) or sorted_collection[left] != item:
        return []  # 未找到
    return list(range(left, right))


def binary_search_by_recursion(
    sorted_collection: list[int], item: int, left: int = 0, right: int = -1
) -> int:
    """
    二分搜索（递归版）

    参数:
        left: 搜索范围起始索引（默认 0）
        right: 搜索范围结束索引（默认 len-1）

    示例:
        >>> binary_search_by_recursion([0, 5, 7, 10, 15], 5, 0, 4)
        1
        >>> binary_search_by_recursion([0, 5, 7, 10, 15], 6, 0, 4)
        -1
    """
    if right < 0:
        right = len(sorted_collection) - 1
    if list(sorted_collection) != sorted(sorted_collection):
        raise ValueError("sorted_collection 必须是升序排列")

    if right < left:
        return -1  # 搜索范围为空

    midpoint = left + (right - left) // 2

    if sorted_collection[midpoint] == item:
        return midpoint
    elif sorted_collection[midpoint] > item:
        # 目标在左半部分，递归搜索
        return binary_search_by_recursion(sorted_collection, item, left, midpoint - 1)
    else:
        # 目标在右半部分，递归搜索
        return binary_search_by_recursion(sorted_collection, item, midpoint + 1, right)


def exponential_search(sorted_collection: list[int], item: int) -> int:
    """
    指数搜索 (Exponential Search)

    算法思想：
        1. 首先找到目标值可能存在的范围（bound = 1, 2, 4, 8, ...）
        2. 确定范围后，使用二分搜索在该范围内查找

    时间复杂度：O(log n)，在目标位于数组开头时比二分搜索更快

    示例:
        >>> exponential_search([0, 5, 7, 10, 15], 0)
        0
        >>> exponential_search([0, 5, 7, 10, 15], 6)
        -1
    """
    if list(sorted_collection) != sorted(sorted_collection):
        raise ValueError("sorted_collection 必须是升序排列")

    # 找到目标值所在范围
    bound = 1
    while bound < len(sorted_collection) and sorted_collection[bound] < item:
        bound *= 2

    # 确定最终搜索范围
    left = bound // 2
    right = min(bound, len(sorted_collection) - 1)

    # 在范围内使用二分搜索
    last_result = binary_search_by_recursion(
        sorted_collection=sorted_collection, item=item, left=left, right=right
    )
    if last_result is None:
        return -1
    return last_result


if __name__ == "__main__":
    import doctest
    import timeit

    doctest.testmod()

    # 测试所有搜索算法
    print("\n=== 二分搜索算法测试 ===")
    for search in (binary_search_std_lib, binary_search, exponential_search, binary_search_by_recursion):
        result = search([0, 5, 7, 10, 15], 10)
        print(f"{search.__name__:>30}: 找到位置 {result}")

    print("\n=== 性能基准测试 ===")
    setup = "collection = range(1000)"
    for search in (binary_search_std_lib, binary_search, exponential_search, binary_search_by_recursion):
        print(
            f"{search.__name__:>30}:",
            timeit.timeit(f"{search.__name__}(collection, 500)", setup=setup, number=5_000, globals=globals()),
            "秒"
        )

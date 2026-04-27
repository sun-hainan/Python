# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / max_subarray_sum

本文件实现 max_subarray_sum 相关的算法功能。
"""

from collections.abc import Sequence


def max_subarray_sum(
    arr: Sequence[float], allow_empty_subarrays: bool = False
) -> float:
    """
    最大子数组和 - Kadane 算法

    参数:
        arr: 输入数组
        allow_empty_subarrays: 是否允许空子数组（允许则返回 0）

    返回:
        最大子数组和

    示例:
        >>> max_subarray_sum([2, 8, 9])
        19
        >>> max_subarray_sum([0, 0])
        0
        >>> max_subarray_sum([-1.0, 0.0, 1.0])
        1.0
        >>> max_subarray_sum([1, 2, 3, 4, -2])
        10
        >>> max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])
        6
        >>> max_subarray_sum([-2, -3, -1, -4, -6])
        -1
        >>> max_subarray_sum([-2, -3, -1, -4, -6], allow_empty_subarrays=True)
        0
        >>> max_subarray_sum([])
        0
    """
    if not arr:
        return 0

    # 初始化
    max_sum = 0 if allow_empty_subarrays else float("-inf")
    curr_sum = 0.0

    for num in arr:
        # 核心公式：要么接在前面，要么重新开始
        # 如果允许空数组，则可以从 0 开始
        curr_sum = max(0 if allow_empty_subarrays else num, curr_sum + num)
        max_sum = max(max_sum, curr_sum)

    return max_sum


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(f"最大子数组和: {max_subarray_sum(nums)}")  # 6

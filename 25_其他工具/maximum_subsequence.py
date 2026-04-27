# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / maximum_subsequence

本文件实现 maximum_subsequence 相关的算法功能。
"""

from collections.abc import Sequence



# max_subsequence_sum 函数实现
def max_subsequence_sum(nums: Sequence[int] | None = None) -> int:
    """Return the maximum possible sum amongst all non - empty subsequences.

    Raises:
      ValueError: when nums is empty.

    >>> max_subsequence_sum([1,2,3,4,-2])
    10
    >>> max_subsequence_sum([-2, -3, -1, -4, -6])
    -1
    >>> max_subsequence_sum([])
    Traceback (most recent call last):
        . . .
    ValueError: Input sequence should not be empty
    >>> max_subsequence_sum()
    Traceback (most recent call last):
        . . .
    ValueError: Input sequence should not be empty
    """
    if nums is None or not nums:
    # 条件判断
        raise ValueError("Input sequence should not be empty")

    ans = nums[0]
    for i in range(1, len(nums)):
    # 遍历循环
        num = nums[i]
        ans = max(ans, ans + num, num)

    return ans
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    # Try on a sample input from the user
    n = int(input("Enter number of elements : ").strip())
    array = list(map(int, input("\nEnter the numbers : ").strip().split()))[:n]
    print(max_subsequence_sum(array))

"""
最长递增子序列 (Longest Increasing Subsequence, LIS) - 中文注释版
==========================================

问题定义：
    给定一个数组，找出其中最长的递增子序列。
    子序列是指数组中删除若干元素后剩余的元素序列（相对顺序不变）。

经典问题，与 LCS 密切相关。

应用场景：
    - 俄罗斯套娃信封问题
    - Maximum ascending subsequence
    - 合唱队形（IOI 题目）

解法对比：
    1. 暴力 O(2^n)：枚举所有子序列
    2. DP O(n²)：经典动态规划
    3. 贪心 + 二分 O(n log n)：最优解

动态规划思路（O(n²)）：
    定义 dp[i] = 以第 i 个元素结尾的 LIS 长度

    dp[i] = max(dp[j] + 1) 其中 j < i 且 arr[j] < arr[i]

时间复杂度：O(n²)
空间复杂度：O(n)
"""

from __future__ import annotations


def longest_subsequence(array: list[int]) -> list[int]:
    """
    最长递增子序列 - 递归版

    思路：
        选择数组首元素作为基准（pivot）
        递归地找比 pivot 大的元素序列
        同时检查不选 pivot 的情况

    参数:
        array: 输入数组

    返回:
        最长递增子序列

    示例:
        >>> longest_subsequence([10, 22, 9, 33, 21, 50, 41, 60, 80])
        [10, 22, 33, 41, 60, 80]
        >>> longest_subsequence([4, 8, 7, 5, 1, 12, 2, 3, 9])
        [1, 2, 3, 9]
        >>> longest_subsequence([28, 26, 12, 23, 35, 39])
        [12, 23, 35, 39]
        >>> longest_subsequence([9, 8, 7, 6, 5, 7])
        [5, 7]
        >>> longest_subsequence([1, 1, 1])
        [1, 1, 1]
        >>> longest_subsequence([])
        []
    """
    array_length = len(array)

    # 递归终止条件：单个或空数组直接返回
    if array_length <= 1:
        return array

    pivot = array[0]
    i = 1
    longest_subseq: list[int] = []
    is_found = False

    # 找到第一个比 pivot 大的元素作为新的起点
    while not is_found and i < array_length:
        if array[i] < pivot:
            is_found = True
            temp_array = array[i:]
            temp_array = longest_subsequence(temp_array)
            if len(temp_array) > len(longest_subseq):
                longest_subseq = temp_array
        else:
            i += 1

    # 选 pivot 的情况
    temp_array = [element for element in array[1:] if element >= pivot]
    temp_array = [pivot, *longest_subsequence(temp_array)]

    if len(temp_array) > len(longest_subseq):
        return temp_array
    else:
        return longest_subseq


if __name__ == "__main__":
    import doctest
    doctest.testmod()

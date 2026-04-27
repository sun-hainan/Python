# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / longest_increasing_subsequence



本文件实现 longest_increasing_subsequence 相关的算法功能。

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


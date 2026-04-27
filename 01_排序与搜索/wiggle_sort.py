# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / wiggle_sort



本文件实现 wiggle_sort 相关的算法功能。

"""



# wiggle_sort 函数实现

def wiggle_sort(nums: list) -> list:

    """

    Python implementation of wiggle.

    Example:

    >>> wiggle_sort([0, 5, 3, 2, 2])

    [0, 5, 2, 3, 2]

    >>> wiggle_sort([])

    []

    >>> wiggle_sort([-2, -5, -45])

    [-45, -2, -5]

    >>> wiggle_sort([-2.1, -5.68, -45.11])

    [-45.11, -2.1, -5.68]

    """

    for i, _ in enumerate(nums):

    # 遍历循环

        if (i % 2 == 1) == (nums[i - 1] > nums[i]):

    # 条件判断

            nums[i - 1], nums[i] = nums[i], nums[i - 1]



    return nums

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    print("Enter the array elements:")

    array = list(map(int, input().split()))

    print("The unsorted array is:")

    print(array)

    print("Array after Wiggle sort:")

    print(wiggle_sort(array))


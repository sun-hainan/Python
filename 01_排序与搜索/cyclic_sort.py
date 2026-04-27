# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / cyclic_sort



本文件实现 cyclic_sort 相关的算法功能。

"""



# cyclic_sort 函数实现

def cyclic_sort(nums: list[int]) -> list[int]:

    """

    Sorts the input list of n integers from 1 to n in-place

    using the Cyclic Sort algorithm.



    :param nums: List of n integers from 1 to n to be sorted.

    :return: The same list sorted in ascending order.



    Time complexity: O(n), where n is the number of integers in the list.



    Examples:

    >>> cyclic_sort([])

    []

    >>> cyclic_sort([3, 5, 2, 1, 4])

    [1, 2, 3, 4, 5]

    """



    # Perform cyclic sort

    index = 0

    while index < len(nums):

    # 条件循环

        # Calculate the correct index for the current element

        correct_index = nums[index] - 1

        # If the current element is not at its correct position,

        # swap it with the element at its correct index

        if index != correct_index:

    # 条件判断

            nums[index], nums[correct_index] = nums[correct_index], nums[index]

        else:

            # If the current element is already in its correct position,

            # move to the next element

            index += 1



    return nums

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    user_input = input("Enter numbers separated by a comma:\n").strip()

    unsorted = [int(item) for item in user_input.split(",")]

    print(*cyclic_sort(unsorted), sep=",")


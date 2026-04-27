# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / ternary_search

本文件实现 ternary_search 相关的算法功能。
"""

from __future__ import annotations

"""
This is a type of divide and conquer algorithm which divides the search space into
3 parts and finds the target value based on the property of the array or list
(usually monotonic property).

Time Complexity  : O(log3 N)
Space Complexity : O(1)
"""


# This is the precision for this function which can be altered.
# It is recommended for users to keep this number greater than or equal to 10.
precision = 10


# This is the linear search that will occur after the search space has become smaller.



# lin_search 函数实现
def lin_search(left: int, right: int, array: list[int], target: int) -> int:
    """Perform linear search in list. Returns -1 if element is not found.

    Parameters
    ----------
    left : int
        left index bound.
    right : int
        right index bound.
    array : List[int]
        List of elements to be searched on
    target : int
        Element that is searched

    Returns
    -------
    int
        index of element that is looked for.

    Examples
    --------
    >>> lin_search(0, 4, [4, 5, 6, 7], 7)
    3
    >>> lin_search(0, 3, [4, 5, 6, 7], 7)
    -1
    >>> lin_search(0, 2, [-18, 2], -18)
    0
    >>> lin_search(0, 1, [5], 5)
    0
    >>> lin_search(0, 3, ['a', 'c', 'd'], 'c')
    1
    >>> lin_search(0, 3, [.1, .4 , -.1], .1)
    0
    >>> lin_search(0, 3, [.1, .4 , -.1], -.1)
    2
    """
    for i in range(left, right):
    # 遍历循环
        if array[i] == target:
    # 条件判断
            return i
    # 返回结果
    return -1
    # 返回结果



# ite_ternary_search 函数实现
def ite_ternary_search(array: list[int], target: int) -> int:
    """Iterative method of the ternary search algorithm.
    >>> test_list = [0, 1, 2, 8, 13, 17, 19, 32, 42]
    >>> ite_ternary_search(test_list, 3)
    -1
    >>> ite_ternary_search(test_list, 13)
    4
    >>> ite_ternary_search([4, 5, 6, 7], 4)
    0
    >>> ite_ternary_search([4, 5, 6, 7], -10)
    -1
    >>> ite_ternary_search([-18, 2], -18)
    0
    >>> ite_ternary_search([5], 5)
    0
    >>> ite_ternary_search(['a', 'c', 'd'], 'c')
    1
    >>> ite_ternary_search(['a', 'c', 'd'], 'f')
    -1
    >>> ite_ternary_search([], 1)
    -1
    >>> ite_ternary_search([.1, .4 , -.1], .1)
    0
    """

    left = 0
    right = len(array)
    while left <= right:
    # 条件循环
        if right - left < precision:
    # 条件判断
            return lin_search(left, right, array, target)
    # 返回结果

        one_third = (left + right) // 3 + 1
        two_third = 2 * (left + right) // 3 + 1

        if array[one_third] == target:
    # 条件判断
            return one_third
    # 返回结果
        elif array[two_third] == target:
            return two_third
    # 返回结果

        elif target < array[one_third]:
            right = one_third - 1
        elif array[two_third] < target:
            left = two_third + 1

        else:
            left = one_third + 1
            right = two_third - 1
    return -1
    # 返回结果



# rec_ternary_search 函数实现
def rec_ternary_search(left: int, right: int, array: list[int], target: int) -> int:
    """Recursive method of the ternary search algorithm.

    >>> test_list = [0, 1, 2, 8, 13, 17, 19, 32, 42]
    >>> rec_ternary_search(0, len(test_list), test_list, 3)
    -1
    >>> rec_ternary_search(4, len(test_list), test_list, 42)
    8
    >>> rec_ternary_search(0, 2, [4, 5, 6, 7], 4)
    0
    >>> rec_ternary_search(0, 3, [4, 5, 6, 7], -10)
    -1
    >>> rec_ternary_search(0, 1, [-18, 2], -18)
    0
    >>> rec_ternary_search(0, 1, [5], 5)
    0
    >>> rec_ternary_search(0, 2, ['a', 'c', 'd'], 'c')
    1
    >>> rec_ternary_search(0, 2, ['a', 'c', 'd'], 'f')
    -1
    >>> rec_ternary_search(0, 0, [], 1)
    -1
    >>> rec_ternary_search(0, 3, [.1, .4 , -.1], .1)
    0
    """
    if left < right:
    # 条件判断
        if right - left < precision:
    # 条件判断
            return lin_search(left, right, array, target)
    # 返回结果
        one_third = (left + right) // 3 + 1
        two_third = 2 * (left + right) // 3 + 1

        if array[one_third] == target:
    # 条件判断
            return one_third
    # 返回结果
        elif array[two_third] == target:
            return two_third
    # 返回结果

        elif target < array[one_third]:
            return rec_ternary_search(left, one_third - 1, array, target)
    # 返回结果
        elif array[two_third] < target:
            return rec_ternary_search(two_third + 1, right, array, target)
    # 返回结果
        else:
            return rec_ternary_search(one_third + 1, two_third - 1, array, target)
    # 返回结果
    else:
        return -1
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    user_input = input("Enter numbers separated by comma:\n").strip()
    collection = [int(item.strip()) for item in user_input.split(",")]
    assert collection == sorted(collection), f"List must be ordered.\n{collection}."
    target = int(input("Enter the number to be found in the list:\n").strip())
    result1 = ite_ternary_search(collection, target)
    result2 = rec_ternary_search(0, len(collection) - 1, collection, target)
    if result2 != -1:
    # 条件判断
        print(f"Iterative search: {target} found at positions: {result1}")
        print(f"Recursive search: {target} found at positions: {result2}")
    else:
        print("Not found")

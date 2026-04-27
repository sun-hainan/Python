# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / linear_search



本文件实现 linear_search 相关的算法功能。

"""



# linear_search 函数实现

def linear_search(sequence: list, target: int) -> int:

    """A pure Python implementation of a linear search algorithm



    :param sequence: a collection with comparable items (sorting is not required for

        linear search)

    :param target: item value to search

    :return: index of found item or -1 if item is not found



    Examples:

    >>> linear_search([0, 5, 7, 10, 15], 0)

    0

    >>> linear_search([0, 5, 7, 10, 15], 15)

    4

    >>> linear_search([0, 5, 7, 10, 15], 5)

    1

    >>> linear_search([0, 5, 7, 10, 15], 6)

    -1

    """

    for index, item in enumerate(sequence):

    # 遍历循环

        if item == target:

    # 条件判断

            return index

    # 返回结果

    return -1

    # 返回结果







# rec_linear_search 函数实现

def rec_linear_search(sequence: list, low: int, high: int, target: int) -> int:

    """

    A pure Python implementation of a recursive linear search algorithm



    :param sequence: a collection with comparable items (as sorted items not required

        in Linear Search)

    :param low: Lower bound of the array

    :param high: Higher bound of the array

    :param target: The element to be found

    :return: Index of the key or -1 if key not found



    Examples:

    >>> rec_linear_search([0, 30, 500, 100, 700], 0, 4, 0)

    0

    >>> rec_linear_search([0, 30, 500, 100, 700], 0, 4, 700)

    4

    >>> rec_linear_search([0, 30, 500, 100, 700], 0, 4, 30)

    1

    >>> rec_linear_search([0, 30, 500, 100, 700], 0, 4, -6)

    -1

    """

    if not (0 <= high < len(sequence) and 0 <= low < len(sequence)):

    # 条件判断

        raise Exception("Invalid upper or lower bound!")

    if high < low:

    # 条件判断

        return -1

    # 返回结果

    if sequence[low] == target:

    # 条件判断

        return low

    # 返回结果

    if sequence[high] == target:

    # 条件判断

        return high

    # 返回结果

    return rec_linear_search(sequence, low + 1, high - 1, target)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    user_input = input("Enter numbers separated by comma:\n").strip()

    sequence = [int(item.strip()) for item in user_input.split(",")]



    target = int(input("Enter a single number to be found in the list:\n").strip())

    result = linear_search(sequence, target)

    if result != -1:

    # 条件判断

        print(f"linear_search({sequence}, {target}) = {result}")

    else:

        print(f"{target} was not found in {sequence}")


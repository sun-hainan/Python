# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / double_linear_search_recursion

本文件实现 double_linear_search_recursion 相关的算法功能。
"""

# search 函数实现
def search(list_data: list, key: int, left: int = 0, right: int = 0) -> int:
    """
    Iterate through the array to find the index of key using recursion.
    :param list_data: the list to be searched
    :param key: the key to be searched
    :param left: the index of first element
    :param right: the index of last element
    :return: the index of key value if found, -1 otherwise.

    >>> search(list(range(0, 11)), 5)
    5
    >>> search([1, 2, 4, 5, 3], 4)
    2
    >>> search([1, 2, 4, 5, 3], 6)
    -1
    >>> search([5], 5)
    0
    >>> search([], 1)
    -1
    """
    right = right or len(list_data) - 1
    if left > right:
    # 条件判断
        return -1
    # 返回结果
    elif list_data[left] == key:
        return left
    # 返回结果
    elif list_data[right] == key:
        return right
    # 返回结果
    else:
        return search(list_data, key, left + 1, right - 1)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

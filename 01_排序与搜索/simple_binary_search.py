# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / simple_binary_search

本文件实现 simple_binary_search 相关的算法功能。
"""

from __future__ import annotations

"""
Pure Python implementation of a binary search algorithm.

For doctests run following command:
python3 -m doctest -v simple_binary_search.py

For manual testing run:
python3 simple_binary_search.py
"""




# binary_search 函数实现
def binary_search(a_list: list[int], item: int) -> bool:
    """
    >>> test_list = [0, 1, 2, 8, 13, 17, 19, 32, 42]
    >>> binary_search(test_list, 3)
    False
    >>> binary_search(test_list, 13)
    True
    >>> binary_search([4, 4, 5, 6, 7], 4)
    True
    >>> binary_search([4, 4, 5, 6, 7], -10)
    False
    >>> binary_search([-18, 2], -18)
    True
    >>> binary_search([5], 5)
    True
    >>> binary_search(['a', 'c', 'd'], 'c')
    True
    >>> binary_search(['a', 'c', 'd'], 'f')
    False
    >>> binary_search([], 1)
    False
    >>> binary_search([-.1, .1 , .8], .1)
    True
    >>> binary_search(range(-5000, 5000, 10), 80)
    True
    >>> binary_search(range(-5000, 5000, 10), 1255)
    False
    >>> binary_search(range(0, 10000, 5), 2)
    False
    """
    if len(a_list) == 0:
    # 条件判断
        return False
    # 返回结果
    midpoint = len(a_list) // 2
    if a_list[midpoint] == item:
    # 条件判断
        return True
    # 返回结果
    if item < a_list[midpoint]:
    # 条件判断
        return binary_search(a_list[:midpoint], item)
    # 返回结果
    else:
        return binary_search(a_list[midpoint + 1 :], item)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    user_input = input("Enter numbers separated by comma:\n").strip()
    sequence = [int(item.strip()) for item in user_input.split(",")]
    target = int(input("Enter the number to be found in the list:\n").strip())
    not_str = "" if binary_search(sequence, target) else "not "
    print(f"{target} was {not_str}found in {sequence}")

# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / odd_even_transposition_single_threaded

本文件实现 odd_even_transposition_single_threaded 相关的算法功能。
"""

# odd_even_transposition 函数实现
def odd_even_transposition(arr: list) -> list:
    """
    >>> odd_even_transposition([5, 4, 3, 2, 1])
    [1, 2, 3, 4, 5]

    >>> odd_even_transposition([13, 11, 18, 0, -1])
    [-1, 0, 11, 13, 18]

    >>> odd_even_transposition([-.1, 1.1, .1, -2.9])
    [-2.9, -0.1, 0.1, 1.1]
    """
    arr_size = len(arr)
    for _ in range(arr_size):
    # 遍历循环
        for i in range(_ % 2, arr_size - 1, 2):
    # 遍历循环
            if arr[i + 1] < arr[i]:
    # 条件判断
                arr[i], arr[i + 1] = arr[i + 1], arr[i]

    return arr
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    arr = list(range(10, 0, -1))
    print(f"Original: {arr}. Sorted: {odd_even_transposition(arr)}")

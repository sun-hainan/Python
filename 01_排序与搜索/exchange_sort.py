# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / exchange_sort

本文件实现 exchange_sort 相关的算法功能。
"""

# exchange_sort 函数实现
def exchange_sort(numbers: list[int]) -> list[int]:
    """
    Uses exchange sort to sort a list of numbers.
    Source: https://en.wikipedia.org/wiki/Sorting_algorithm#Exchange_sort
    >>> exchange_sort([5, 4, 3, 2, 1])
    [1, 2, 3, 4, 5]
    >>> exchange_sort([-1, -2, -3])
    [-3, -2, -1]
    >>> exchange_sort([1, 2, 3, 4, 5])
    [1, 2, 3, 4, 5]
    >>> exchange_sort([0, 10, -2, 5, 3])
    [-2, 0, 3, 5, 10]
    >>> exchange_sort([])
    []
    """
    numbers_length = len(numbers)
    for i in range(numbers_length):
    # 遍历循环
        for j in range(i + 1, numbers_length):
    # 遍历循环
            if numbers[j] < numbers[i]:
    # 条件判断
                numbers[i], numbers[j] = numbers[j], numbers[i]
    return numbers
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    user_input = input("Enter numbers separated by a comma:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(exchange_sort(unsorted))

# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / dutch_national_flag_sort

本文件实现 dutch_national_flag_sort 相关的算法功能。
"""

# Python program to sort a sequence containing only 0, 1 and 2 in a single pass.
red = 0  # The first color of the flag.
white = 1  # The second color of the flag.
blue = 2  # The third color of the flag.
colors = (red, white, blue)



# dutch_national_flag_sort 函数实现
def dutch_national_flag_sort(sequence: list) -> list:
    """
    A pure Python implementation of Dutch National Flag sort algorithm.
    :param data: 3 unique integer values (e.g., 0, 1, 2) in an sequence
    :return: The same collection in ascending order

    >>> dutch_national_flag_sort([])
    []
    >>> dutch_national_flag_sort([0])
    [0]
    >>> dutch_national_flag_sort([2, 1, 0, 0, 1, 2])
    [0, 0, 1, 1, 2, 2]
    >>> dutch_national_flag_sort([0, 1, 1, 0, 1, 2, 1, 2, 0, 0, 0, 1])
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2]
    >>> dutch_national_flag_sort("abacab")
    Traceback (most recent call last):
      ...
    ValueError: The elements inside the sequence must contains only (0, 1, 2) values
    >>> dutch_national_flag_sort("Abacab")
    Traceback (most recent call last):
      ...
    ValueError: The elements inside the sequence must contains only (0, 1, 2) values
    >>> dutch_national_flag_sort([3, 2, 3, 1, 3, 0, 3])
    Traceback (most recent call last):
      ...
    ValueError: The elements inside the sequence must contains only (0, 1, 2) values
    >>> dutch_national_flag_sort([-1, 2, -1, 1, -1, 0, -1])
    Traceback (most recent call last):
      ...
    ValueError: The elements inside the sequence must contains only (0, 1, 2) values
    >>> dutch_national_flag_sort([1.1, 2, 1.1, 1, 1.1, 0, 1.1])
    Traceback (most recent call last):
      ...
    ValueError: The elements inside the sequence must contains only (0, 1, 2) values
    """
    if not sequence:
    # 条件判断
        return []
    # 返回结果
    if len(sequence) == 1:
    # 条件判断
        return list(sequence)
    # 返回结果
    low = 0
    high = len(sequence) - 1
    mid = 0
    while mid <= high:
    # 条件循环
        if sequence[mid] == colors[0]:
    # 条件判断
            sequence[low], sequence[mid] = sequence[mid], sequence[low]
            low += 1
            mid += 1
        elif sequence[mid] == colors[1]:
            mid += 1
        elif sequence[mid] == colors[2]:
            sequence[mid], sequence[high] = sequence[high], sequence[mid]
            high -= 1
        else:
            msg = f"The elements inside the sequence must contains only {colors} values"
            raise ValueError(msg)
    return sequence
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    user_input = input("Enter numbers separated by commas:\n").strip()
    unsorted = [int(item.strip()) for item in user_input.split(",")]
    print(f"{dutch_national_flag_sort(unsorted)}")

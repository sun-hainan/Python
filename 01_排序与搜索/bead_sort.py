# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / bead_sort

本文件实现 bead_sort 相关的算法功能。
"""

# bead_sort 函数实现
def bead_sort(sequence: list) -> list:
    """
    >>> bead_sort([6, 11, 12, 4, 1, 5])
    [1, 4, 5, 6, 11, 12]

    >>> bead_sort([9, 8, 7, 6, 5, 4 ,3, 2, 1])
    [1, 2, 3, 4, 5, 6, 7, 8, 9]

    >>> bead_sort([5, 0, 4, 3])
    [0, 3, 4, 5]

    >>> bead_sort([8, 2, 1])
    [1, 2, 8]

    >>> bead_sort([1, .9, 0.0, 0, -1, -.9])
    Traceback (most recent call last):
        ...
    TypeError: Sequence must be list of non-negative integers

    >>> bead_sort("Hello world")
    Traceback (most recent call last):
        ...
    TypeError: Sequence must be list of non-negative integers
    """
    if any(not isinstance(x, int) or x < 0 for x in sequence):
    # 条件判断
        raise TypeError("Sequence must be list of non-negative integers")
    for _ in range(len(sequence)):
    # 遍历循环
        for i, (rod_upper, rod_lower) in enumerate(zip(sequence, sequence[1:])):  # noqa: RUF007
    # 遍历循环
            if rod_upper > rod_lower:
    # 条件判断
                sequence[i] -= rod_upper - rod_lower
                sequence[i + 1] += rod_upper - rod_lower
    return sequence
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    assert bead_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert bead_sort([7, 9, 4, 3, 5]) == [3, 4, 5, 7, 9]

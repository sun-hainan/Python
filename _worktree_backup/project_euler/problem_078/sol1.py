# -*- coding: utf-8 -*-
"""
Project Euler Problem 078

解决 Project Euler 第 078 题的 Python 实现。
https://projecteuler.net/problem=078
"""

import itertools



# =============================================================================
# Project Euler 问题 078
# =============================================================================
def solution(number: int = 1000000) -> int:
    """
    >>> solution(1)
    1

    >>> solution(9)
    14

    >>> solution()
    55374
    """
    partitions = [1]

    for i in itertools.count(len(partitions)):
    # 遍历循环
        item = 0
        for j in itertools.count(1):
    # 遍历循环
            sign = -1 if j % 2 == 0 else +1
            index = (j * j * 3 - j) // 2
            if index > i:
                break
            item += partitions[i - index] * sign
            item %= number
            index += j
            if index > i:
                break
            item += partitions[i - index] * sign
            item %= number

        if item == 0:
            return i
    # 返回结果
        partitions.append(item)

    return 0
    # 返回结果


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    print(f"{solution() = }")

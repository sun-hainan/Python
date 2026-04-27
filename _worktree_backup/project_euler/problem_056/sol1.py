# -*- coding: utf-8 -*-
"""
Project Euler Problem 056

解决 Project Euler 第 056 题的 Python 实现。
https://projecteuler.net/problem=056
"""

# =============================================================================
# Project Euler 问题 056
# =============================================================================
def solution(a: int = 100, b: int = 100) -> int:
    """
    Considering natural numbers of the form, a**b, where a, b < 100,
    what is the maximum digital sum?
    :param a:
    :param b:
    :return:
    >>> solution(10,10)
    45

    >>> solution(100,100)
    972

    >>> solution(100,200)
    1872
    """

    # RETURN the MAXIMUM from the list of SUMs of the list of INT converted from STR of
    # BASE raised to the POWER
    return max(
    # 返回结果
        sum(int(x) for x in str(base**power)) for base in range(a) for power in range(b)
    )


# Tests
if __name__ == "__main__":
    import doctest

    doctest.testmod()

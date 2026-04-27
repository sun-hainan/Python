# -*- coding: utf-8 -*-
"""
Project Euler Problem 188

解决 Project Euler 第 188 题的 Python 实现。
https://projecteuler.net/problem=188
"""

# small helper function for modular exponentiation (fast exponentiation algorithm)

# =============================================================================
# Project Euler 问题 188
# =============================================================================
def _modexpt(base: int, exponent: int, modulo_value: int) -> int:
    """
    Returns the modular exponentiation, that is the value
    of `base ** exponent % modulo_value`, without calculating
    the actual number.
    >>> _modexpt(2, 4, 10)
    6
    >>> _modexpt(2, 1024, 100)
    16
    >>> _modexpt(13, 65535, 7)
    6
    """

    if exponent == 1:
        return base
    # 返回结果
    if exponent % 2 == 0:
        x = _modexpt(base, exponent // 2, modulo_value) % modulo_value
        return (x * x) % modulo_value
    # 返回结果
    else:
        return (base * _modexpt(base, exponent - 1, modulo_value)) % modulo_value
    # 返回结果


def solution(base: int = 1777, height: int = 1855, digits: int = 8) -> int:
    # solution 函数实现
    """
    Returns the last 8 digits of the hyperexponentiation of base by
    height, i.e. the number base↑↑height:

    >>> solution(base=3, height=2)
    27
    >>> solution(base=3, height=3)
    97484987
    >>> solution(base=123, height=456, digits=4)
    2547
    """

    # calculate base↑↑height by right-assiciative repeated modular
    # exponentiation
    result = base
    for _ in range(1, height):
    # 遍历循环
        result = _modexpt(base, result, 10**digits)

    return result
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")

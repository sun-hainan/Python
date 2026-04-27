# -*- coding: utf-8 -*-
"""
Project Euler Problem 040

解决 Project Euler 第 040 题的 Python 实现。
https://projecteuler.net/problem=040
"""

# =============================================================================
# Project Euler 问题 040
# =============================================================================
def solution():
    """Returns

    >>> solution()
    210
    """
    constant = []
    i = 1

    while len(constant) < 1e6:
    # 条件循环
        constant.append(str(i))
        i += 1

    constant = "".join(constant)

    return (
    # 返回结果
        int(constant[0])
        * int(constant[9])
        * int(constant[99])
        * int(constant[999])
        * int(constant[9999])
        * int(constant[99999])
        * int(constant[999999])
    )


if __name__ == "__main__":
    print(solution())

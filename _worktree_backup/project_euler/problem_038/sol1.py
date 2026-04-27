# -*- coding: utf-8 -*-

"""

Project Euler Problem 038



解决 Project Euler 第 038 题的 Python 实现。

https://projecteuler.net/problem=038

"""



from __future__ import annotations



"""

Project Euler Problem 038 — 中文注释版

https://projecteuler.net/problem=038



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""













# =============================================================================

# Project Euler 问题 038

# =============================================================================

def is_9_pandigital(n: int) -> bool:

    """

    Checks whether n is a 9-digit 1 to 9 pandigital number.

    >>> is_9_pandigital(12345)

    False

    >>> is_9_pandigital(156284973)

    True

    >>> is_9_pandigital(1562849733)

    False

    """

    s = str(n)

    return len(s) == 9 and set(s) == set("123456789")

    # 返回结果





def solution() -> int | None:

    # solution 函数实现

    """

    Return the largest 1 to 9 pandigital 9-digital number that can be formed as the

    concatenated product of an integer with (1,2,...,n) where n > 1.

    """

    for base_num in range(9999, 4999, -1):

    # 遍历循环

        candidate = 100002 * base_num

        if is_9_pandigital(candidate):

            return candidate

    # 返回结果



    for base_num in range(333, 99, -1):

    # 遍历循环

        candidate = 1002003 * base_num

        if is_9_pandigital(candidate):

            return candidate

    # 返回结果



    return None

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")


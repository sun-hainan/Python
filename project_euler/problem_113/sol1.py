# -*- coding: utf-8 -*-

"""

Project Euler Problem 113



解决 Project Euler 第 113 题的 Python 实现。

https://projecteuler.net/problem=113

"""



# =============================================================================

# Project Euler 问题 113

# =============================================================================

def choose(n: int, r: int) -> int:

    """

    Calculate the binomial coefficient c(n,r) using the multiplicative formula.

    >>> choose(4,2)

    6

    >>> choose(5,3)

    10

    >>> choose(20,6)

    38760

    """

    ret = 1.0

    for i in range(1, r + 1):

    # 遍历循环

        ret *= (n + 1 - i) / i

    return round(ret)

    # 返回结果





def non_bouncy_exact(n: int) -> int:

    # non_bouncy_exact 函数实现

    """

    Calculate the number of non-bouncy numbers with at most n digits.

    >>> non_bouncy_exact(1)

    9

    >>> non_bouncy_exact(6)

    7998

    >>> non_bouncy_exact(10)

    136126

    """

    return choose(8 + n, n) + choose(9 + n, n) - 10

    # 返回结果





def non_bouncy_upto(n: int) -> int:

    # non_bouncy_upto 函数实现

    """

    Calculate the number of non-bouncy numbers with at most n digits.

    >>> non_bouncy_upto(1)

    9

    >>> non_bouncy_upto(6)

    12951

    >>> non_bouncy_upto(10)

    277032

    """

    return sum(non_bouncy_exact(i) for i in range(1, n + 1))

    # 返回结果





def solution(num_digits: int = 100) -> int:

    # solution 函数实现

    """

    Calculate the number of non-bouncy numbers less than a googol.

    >>> solution(6)

    12951

    >>> solution(10)

    277032

    """

    return non_bouncy_upto(num_digits)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")


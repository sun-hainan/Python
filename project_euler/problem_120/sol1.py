# -*- coding: utf-8 -*-

"""

Project Euler Problem 120



解决 Project Euler 第 120 题的 Python 实现。

https://projecteuler.net/problem=120

"""



# =============================================================================

# Project Euler 问题 120

# =============================================================================

def solution(n: int = 1000) -> int:

    """

    Returns ∑ r_max for 3 <= a <= n as explained above

    >>> solution(10)

    300

    >>> solution(100)

    330750

    >>> solution(1000)

    333082500

    """

    return sum(2 * a * ((a - 1) // 2) for a in range(3, n + 1))

    # 返回结果





if __name__ == "__main__":

    print(solution())


# -*- coding: utf-8 -*-

"""

Project Euler Problem 136



解决 Project Euler 第 136 题的 Python 实现。

https://projecteuler.net/problem=136

"""



# =============================================================================

# Project Euler 问题 136

# =============================================================================

def solution(n_limit: int = 50 * 10**6) -> int:

    """

    Define n count list and loop over delta, y to get the counts, then check

    which n has count == 1.



    >>> solution(3)

    0

    >>> solution(10)

    3

    >>> solution(100)

    25

    >>> solution(110)

    27

    """

    n_sol = [0] * n_limit



    for delta in range(1, (n_limit + 1) // 4 + 1):

    # 遍历循环

        for y in range(4 * delta - 1, delta, -1):

            n = y * (4 * delta - y)

            if n >= n_limit:

                break

            n_sol[n] += 1



    ans = 0

    for i in range(n_limit):

    # 遍历循环

        if n_sol[i] == 1:

            ans += 1



    return ans

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")


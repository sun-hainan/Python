# -*- coding: utf-8 -*-

"""

Project Euler Problem 014



解决 Project Euler 第 014 题的 Python 实现。

https://projecteuler.net/problem=014

"""



from __future__ import annotations



"""

Project Euler Problem 014 — 中文注释版

https://projecteuler.net/problem=014



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









COLLATZ_SEQUENCE_LENGTHS = {1: 1}







# =============================================================================

# Project Euler 问题 014

# =============================================================================

def collatz_sequence_length(n: int) -> int:

    """Returns the Collatz sequence length for n."""

    if n in COLLATZ_SEQUENCE_LENGTHS:

        return COLLATZ_SEQUENCE_LENGTHS[n]

    # 返回结果

    next_n = n // 2 if n % 2 == 0 else 3 * n + 1

    sequence_length = collatz_sequence_length(next_n) + 1

    COLLATZ_SEQUENCE_LENGTHS[n] = sequence_length

    return sequence_length

    # 返回结果





def solution(n: int = 1000000) -> int:

    # solution 函数实现

    """Returns the number under n that generates the longest Collatz sequence.



    >>> solution(1000000)

    837799

    >>> solution(200)

    171

    >>> solution(5000)

    3711

    >>> solution(15000)

    13255

    """



    result = max((collatz_sequence_length(i), i) for i in range(1, n))

    return result[1]

    # 返回结果





if __name__ == "__main__":

    print(solution(int(input().strip())))


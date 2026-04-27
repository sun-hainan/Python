# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / collatz_sequence

本文件实现 collatz_sequence 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""




from collections.abc import Generator



# =============================================================================
# 算法模块：collatz_sequence
# =============================================================================
def collatz_sequence(n: int) -> Generator[int]:
    # collatz_sequence function

    # collatz_sequence function
    """
    Generate the Collatz sequence starting at n.
    >>> tuple(collatz_sequence(2.1))
    Traceback (most recent call last):
        ...
    Exception: Sequence only defined for positive integers
    >>> tuple(collatz_sequence(0))
    Traceback (most recent call last):
        ...
    Exception: Sequence only defined for positive integers
    >>> tuple(collatz_sequence(4))
    (4, 2, 1)
    >>> tuple(collatz_sequence(11))
    (11, 34, 17, 52, 26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1)
    >>> tuple(collatz_sequence(31))     # doctest: +NORMALIZE_WHITESPACE
    (31, 94, 47, 142, 71, 214, 107, 322, 161, 484, 242, 121, 364, 182, 91, 274, 137,
    412, 206, 103, 310, 155, 466, 233, 700, 350, 175, 526, 263, 790, 395, 1186, 593,
    1780, 890, 445, 1336, 668, 334, 167, 502, 251, 754, 377, 1132, 566, 283, 850, 425,
    1276, 638, 319, 958, 479, 1438, 719, 2158, 1079, 3238, 1619, 4858, 2429, 7288, 3644,
    1822, 911, 2734, 1367, 4102, 2051, 6154, 3077, 9232, 4616, 2308, 1154, 577, 1732,
    866, 433, 1300, 650, 325, 976, 488, 244, 122, 61, 184, 92, 46, 23, 70, 35, 106, 53,
    160, 80, 40, 20, 10, 5, 16, 8, 4, 2, 1)
    >>> tuple(collatz_sequence(43))     # doctest: +NORMALIZE_WHITESPACE
    (43, 130, 65, 196, 98, 49, 148, 74, 37, 112, 56, 28, 14, 7, 22, 11, 34, 17, 52, 26,
    13, 40, 20, 10, 5, 16, 8, 4, 2, 1)
    """
    if not isinstance(n, int) or n < 1:
        raise Exception("Sequence only defined for positive integers")

    yield n
    while n != 1:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        yield n


def main():
    # main function

    # main function
    n = int(input("Your number: "))
    sequence = tuple(collatz_sequence(n))
    print(sequence)
    print(f"Collatz sequence from {n} took {len(sequence)} steps.")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Project Euler Problem 074

解决 Project Euler 第 074 题的 Python 实现。
https://projecteuler.net/problem=074
"""

DIGIT_FACTORIALS = {
    "0": 1,
    "1": 1,
    "2": 2,
    "3": 6,
    "4": 24,
    "5": 120,
    "6": 720,
    "7": 5040,
    "8": 40320,
    "9": 362880,
}

CACHE_SUM_DIGIT_FACTORIALS = {145: 145}

CHAIN_LENGTH_CACHE = {
    145: 0,
    169: 3,
    36301: 3,
    1454: 3,
    871: 2,
    45361: 2,
    872: 2,
}



# =============================================================================
# Project Euler 问题 074
# =============================================================================
def sum_digit_factorials(n: int) -> int:
    """
    Return the sum of the factorial of the digits of n.
    >>> sum_digit_factorials(145)
    145
    >>> sum_digit_factorials(45361)
    871
    >>> sum_digit_factorials(540)
    145
    """
    if n in CACHE_SUM_DIGIT_FACTORIALS:
        return CACHE_SUM_DIGIT_FACTORIALS[n]
    # 返回结果
    ret = sum(DIGIT_FACTORIALS[let] for let in str(n))
    CACHE_SUM_DIGIT_FACTORIALS[n] = ret
    return ret
    # 返回结果


def chain_length(n: int, previous: set | None = None) -> int:
    # chain_length 函数实现
    """
    Calculate the length of the chain of non-repeating terms starting with n.
    Previous is a set containing the previous member of the chain.
    >>> chain_length(10101)
    11
    >>> chain_length(555)
    20
    >>> chain_length(178924)
    39
    """
    previous = previous or set()
    if n in CHAIN_LENGTH_CACHE:
        return CHAIN_LENGTH_CACHE[n]
    # 返回结果
    next_number = sum_digit_factorials(n)
    if next_number in previous:
        CHAIN_LENGTH_CACHE[n] = 0
        return 0
    # 返回结果
    else:
        previous.add(n)
        ret = 1 + chain_length(next_number, previous)
        CHAIN_LENGTH_CACHE[n] = ret
        return ret
    # 返回结果


def solution(num_terms: int = 60, max_start: int = 1000000) -> int:
    # solution 函数实现
    """
    Return the number of chains with a starting number below one million which
    contain exactly n non-repeating terms.
    >>> solution(10,1000)
    28
    """
    return sum(1 for i in range(1, max_start) if chain_length(i) == num_terms)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")

# -*- coding: utf-8 -*-

"""

Project Euler Problem 077



解决 Project Euler 第 077 题的 Python 实现。

https://projecteuler.net/problem=077

"""



from __future__ import annotations



"""

Project Euler Problem 077 — 中文注释版

https://projecteuler.net/problem=077



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









from functools import lru_cache

from math import ceil



NUM_PRIMES = 100



primes = set(range(3, NUM_PRIMES, 2))

primes.add(2)

prime: int



for prime in range(3, ceil(NUM_PRIMES**0.5), 2):

    # 遍历循环

    if prime not in primes:

        continue

    primes.difference_update(set(range(prime * prime, NUM_PRIMES, prime)))





@lru_cache(maxsize=100)



# =============================================================================

# Project Euler 问题 077

# =============================================================================

def partition(number_to_partition: int) -> set[int]:

    """

    Return a set of integers corresponding to unique prime partitions of n.

    The unique prime partitions can be represented as unique prime decompositions,

    e.g. (7+3) <-> 7*3 = 12, (3+3+2+2) = 3*3*2*2 = 36

    >>> partition(10)

    {32, 36, 21, 25, 30}

    >>> partition(15)

    {192, 160, 105, 44, 112, 243, 180, 150, 216, 26, 125, 126}

    >>> len(partition(20))

    26

    """

    if number_to_partition < 0:

        return set()

    # 返回结果

    elif number_to_partition == 0:

        return {1}

    # 返回结果



    ret: set[int] = set()

    prime: int

    sub: int



    for prime in primes:

    # 遍历循环

        if prime > number_to_partition:

            continue

        for sub in partition(number_to_partition - prime):

    # 遍历循环

            ret.add(sub * prime)



    return ret

    # 返回结果





def solution(number_unique_partitions: int = 5000) -> int | None:

    # solution 函数实现

    """

    Return the smallest integer that can be written as the sum of primes in over

    m unique ways.

    >>> solution(4)

    10

    >>> solution(500)

    45

    >>> solution(1000)

    53

    """

    for number_to_partition in range(1, NUM_PRIMES):

    # 遍历循环

        if len(partition(number_to_partition)) > number_unique_partitions:

            return number_to_partition

    # 返回结果

    return None





if __name__ == "__main__":

    print(f"{solution() = }")


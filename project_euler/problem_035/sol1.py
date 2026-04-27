# -*- coding: utf-8 -*-

"""

Project Euler Problem 035



解决 Project Euler 第 035 题的 Python 实现。

https://projecteuler.net/problem=035

"""



from __future__ import annotations



"""

Project Euler Problem 035 — 中文注释版

https://projecteuler.net/problem=035



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









sieve = [True] * 1000001

i = 2

while i * i <= 1000000:

    # 条件循环

    if sieve[i]:

        for j in range(i * i, 1000001, i):

    # 遍历循环

            sieve[j] = False

    i += 1







# =============================================================================

# Project Euler 问题 035

# =============================================================================

def is_prime(n: int) -> bool:

    """

    For 2 <= n <= 1000000, return True if n is prime.

    >>> is_prime(87)

    False

    >>> is_prime(23)

    True

    >>> is_prime(25363)

    False

    """

    return sieve[n]

    # 返回结果





def contains_an_even_digit(n: int) -> bool:

    # contains_an_even_digit 函数实现

    """

    Return True if n contains an even digit.

    >>> contains_an_even_digit(0)

    True

    >>> contains_an_even_digit(975317933)

    False

    >>> contains_an_even_digit(-245679)

    True

    """

    return any(digit in "02468" for digit in str(n))

    # 返回结果





def find_circular_primes(limit: int = 1000000) -> list[int]:

    # find_circular_primes 函数实现

    """

    Return circular primes below limit.

    >>> len(find_circular_primes(100))

    13

    >>> len(find_circular_primes(1000000))

    55

    """

    result = [2]  # result already includes the number 2.

    for num in range(3, limit + 1, 2):

    # 遍历循环

        if is_prime(num) and not contains_an_even_digit(num):

            str_num = str(num)

            list_nums = [int(str_num[j:] + str_num[:j]) for j in range(len(str_num))]

            if all(is_prime(i) for i in list_nums):

                result.append(num)

    return result

    # 返回结果





def solution() -> int:

    # solution 函数实现

    """

    >>> solution()

    55

    """

    return len(find_circular_primes())

    # 返回结果





if __name__ == "__main__":

    print(f"{len(find_circular_primes()) = }")


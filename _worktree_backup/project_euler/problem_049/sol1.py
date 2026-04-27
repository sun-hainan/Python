# -*- coding: utf-8 -*-
"""
Project Euler Problem 049

解决 Project Euler 第 049 题的 Python 实现。
https://projecteuler.net/problem=049
"""

import math
from itertools import permutations



# =============================================================================
# Project Euler 问题 049
# =============================================================================
def is_prime(number: int) -> bool:
    """Checks to see if a number is a prime in O(sqrt(n)).

    A number is prime if it has exactly two factors: 1 and itself.

    >>> is_prime(0)
    False
    >>> is_prime(1)
    False
    >>> is_prime(2)
    True
    >>> is_prime(3)
    True
    >>> is_prime(27)
    False
    >>> is_prime(87)
    False
    >>> is_prime(563)
    True
    >>> is_prime(2999)
    True
    >>> is_prime(67483)
    False
    """

    if 1 < number < 4:
        # 2 and 3 are primes
        return True
    # 返回结果
    elif number < 2 or number % 2 == 0 or number % 3 == 0:
        # Negatives, 0, 1, all even numbers, all multiples of 3 are not primes
        return False
    # 返回结果

    # All primes number are in format of 6k +/- 1
    for i in range(5, int(math.sqrt(number) + 1), 6):
    # 遍历循环
        if number % i == 0 or number % (i + 2) == 0:
            return False
    # 返回结果
    return True


def search(target: int, prime_list: list) -> bool:
    # search 函数实现
    """
    function to search a number in a list using Binary Search.
    >>> search(3, [1, 2, 3])
    True
    >>> search(4, [1, 2, 3])
    False
    >>> search(101, list(range(-100, 100)))
    False
    """

    left, right = 0, len(prime_list) - 1
    while left <= right:
    # 条件循环
        middle = (left + right) // 2
        if prime_list[middle] == target:
            return True
    # 返回结果
        elif prime_list[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return False
    # 返回结果


def solution():
    # solution 函数实现
    """
    Return the solution of the problem.
    >>> solution()
    296962999629
    """
    prime_list = [n for n in range(1001, 10000, 2) if is_prime(n)]
    candidates = []

    for number in prime_list:
    # 遍历循环
        tmp_numbers = []

        for prime_member in permutations(list(str(number))):
    # 遍历循环
            prime = int("".join(prime_member))

            if prime % 2 == 0:
                continue

            if search(prime, prime_list):
                tmp_numbers.append(prime)

        tmp_numbers.sort()
        if len(tmp_numbers) >= 3:
            candidates.append(tmp_numbers)

    passed = []
    for candidate in candidates:
    # 遍历循环
        length = len(candidate)
        found = False

        for i in range(length):
    # 遍历循环
            for j in range(i + 1, length):
                for k in range(j + 1, length):
    # 遍历循环
                    if (
                        abs(candidate[i] - candidate[j])
                        == abs(candidate[j] - candidate[k])
                        and len({candidate[i], candidate[j], candidate[k]}) == 3
                    ):
                        passed.append(
                            sorted([candidate[i], candidate[j], candidate[k]])
                        )
                        found = True

                    if found:
                        break
                if found:
                    break
            if found:
                break

    answer = set()
    for seq in passed:
    # 遍历循环
        answer.add("".join([str(i) for i in seq]))

    return max(int(x) for x in answer)
    # 返回结果


if __name__ == "__main__":
    print(solution())

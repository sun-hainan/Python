# -*- coding: utf-8 -*-

"""

Project Euler Problem 036



解决 Project Euler 第 036 题的 Python 实现。

https://projecteuler.net/problem=036

"""



from __future__ import annotations



"""

Project Euler Problem 036 — 中文注释版

https://projecteuler.net/problem=036



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""













# =============================================================================

# Project Euler 问题 036

# =============================================================================

def is_palindrome(n: int | str) -> bool:

    """

    Return true if the input n is a palindrome.

    Otherwise return false. n can be an integer or a string.



    >>> is_palindrome(909)

    True

    >>> is_palindrome(908)

    False

    >>> is_palindrome('10101')

    True

    >>> is_palindrome('10111')

    False

    """

    n = str(n)

    return n == n[::-1]

    # 返回结果





def solution(n: int = 1000000):

    # solution 函数实现

    """Return the sum of all numbers, less than n , which are palindromic in

    base 10 and base 2.



    >>> solution(1000000)

    872187

    >>> solution(500000)

    286602

    >>> solution(100000)

    286602

    >>> solution(1000)

    1772

    >>> solution(100)

    157

    >>> solution(10)

    25

    >>> solution(2)

    1

    >>> solution(1)

    0

    """

    total = 0



    for i in range(1, n):

    # 遍历循环

        if is_palindrome(i) and is_palindrome(bin(i).split("b")[1]):

            total += i

    return total

    # 返回结果





if __name__ == "__main__":

    print(solution(int(str(input().strip()))))


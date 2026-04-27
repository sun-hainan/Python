# -*- coding: utf-8 -*-

"""

Project Euler Problem 025



解决 Project Euler 第 025 题的 Python 实现。

https://projecteuler.net/problem=025

"""



from collections.abc import Generator







# =============================================================================

# Project Euler 问题 025

# =============================================================================

def fibonacci_generator() -> Generator[int]:

    """

    A generator that produces numbers in the Fibonacci sequence



    >>> generator = fibonacci_generator()

    >>> next(generator)

    1

    >>> next(generator)

    2

    >>> next(generator)

    3

    >>> next(generator)

    5

    >>> next(generator)

    8

    """

    a, b = 0, 1

    while True:

    # 条件循环

        a, b = b, a + b

        yield b





def solution(n: int = 1000) -> int:

    # solution 函数实现

    """Returns the index of the first term in the Fibonacci sequence to contain

    n digits.



    >>> solution(1000)

    4782

    >>> solution(100)

    476

    >>> solution(50)

    237

    >>> solution(3)

    12

    """

    answer = 1

    gen = fibonacci_generator()

    while len(str(next(gen))) < n:

    # 条件循环

        answer += 1

    return answer + 1

    # 返回结果





if __name__ == "__main__":

    print(solution(int(str(input()).strip())))


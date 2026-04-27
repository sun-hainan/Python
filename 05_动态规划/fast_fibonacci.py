# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / fast_fibonacci



本文件实现 fast_fibonacci 相关的算法功能。

"""



from __future__ import annotations



#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

fast_fibonacci



算法分类：动态规划

描述：实现 fast_fibonacci 算法的核心逻辑。

"""









"""

This program calculates the nth Fibonacci number in O(log(n)).

It's possible to calculate F(1_000_000) in less than a second.

"""





import sys





def fibonacci(n: int) -> int:

    """

    return F(n)

    >>> [fibonacci(i) for i in range(13)]

    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

    """

    if n < 0:

        raise ValueError("Negative arguments are not supported")

    return _fib(n)[0]





# returns (F(n), F(n-1))

def _fib(n: int) -> tuple[int, int]:

    if n == 0:  # (F(0), F(1))

        return (0, 1)



    # F(2n) = F(n)[2F(n+1) - F(n)]

    # F(2n+1) = F(n+1)^2+F(n)^2

    a, b = _fib(n // 2)

    c = a * (b * 2 - a)

    d = a * a + b * b

    return (d, c + d) if n % 2 else (c, d)





if __name__ == "__main__":

    n = int(sys.argv[1])

    print(f"fibonacci({n}) is {fibonacci(n)}")


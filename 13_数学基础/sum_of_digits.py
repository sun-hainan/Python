# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / sum_of_digits

本文件实现 sum_of_digits 相关的算法功能。
"""

# =============================================================================
# 算法模块：sum_of_digits
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def sum_of_digits(n: int) -> int:
    # sum_of_digits function

    # sum_of_digits function
    """
    Find the sum of digits of a number.
    >>> sum_of_digits(12345)
    15
    >>> sum_of_digits(123)
    6
    >>> sum_of_digits(-123)
    6
    >>> sum_of_digits(0)
    0
    """

    n = abs(n)
    res = 0
    while n > 0:
        res += n % 10
        n //= 10
    return res


def sum_of_digits_recursion(n: int) -> int:
    # sum_of_digits_recursion function

    # sum_of_digits_recursion function
    """
    Find the sum of digits of a number using recursion
    >>> sum_of_digits_recursion(12345)
    15
    >>> sum_of_digits_recursion(123)
    6
    >>> sum_of_digits_recursion(-123)
    6
    >>> sum_of_digits_recursion(0)
    0
    """
    n = abs(n)
    return n if n < 10 else n % 10 + sum_of_digits(n // 10)


def sum_of_digits_compact(n: int) -> int:
    # sum_of_digits_compact function

    # sum_of_digits_compact function
    """
    Find the sum of digits of a number
    >>> sum_of_digits_compact(12345)
    15
    >>> sum_of_digits_compact(123)
    6
    >>> sum_of_digits_compact(-123)
    6
    >>> sum_of_digits_compact(0)
    0
    """
    return sum(int(c) for c in str(abs(n)))


def benchmark() -> None:
    # benchmark function

    # benchmark function
    """
    Benchmark multiple functions, with three different length int values.
    """
    from collections.abc import Callable
    from timeit import timeit

    def benchmark_a_function(func: Callable, value: int) -> None:
    # benchmark_a_function function

    # benchmark_a_function function
        call = f"{func.__name__}({value})"
        timing = timeit(f"__main__.{call}", setup="import __main__")
        print(f"{call:56} = {func(value)} -- {timing:.4f} seconds")

    for value in (262144, 1125899906842624, 1267650600228229401496703205376):
        for func in (sum_of_digits, sum_of_digits_recursion, sum_of_digits_compact):
            benchmark_a_function(func, value)
        print()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    benchmark()

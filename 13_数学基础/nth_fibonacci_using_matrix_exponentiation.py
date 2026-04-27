# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / nth_fibonacci_using_matrix_exponentiation

本文件实现 nth_fibonacci_using_matrix_exponentiation 相关的算法功能。
"""

# =============================================================================
# 算法模块：multiply
# =============================================================================
def multiply(matrix_a: list[list[int]], matrix_b: list[list[int]]) -> list[list[int]]:
    # multiply function

    # multiply function
    matrix_c = []
    n = len(matrix_a)
    for i in range(n):
        list_1 = []
        for j in range(n):
            val = 0
            for k in range(n):
                val = val + matrix_a[i][k] * matrix_b[k][j]
            list_1.append(val)
        matrix_c.append(list_1)
    return matrix_c


def identity(n: int) -> list[list[int]]:
    # identity function

    # identity function
    return [[int(row == column) for column in range(n)] for row in range(n)]


def nth_fibonacci_matrix(n: int) -> int:
    # nth_fibonacci_matrix function

    # nth_fibonacci_matrix function
    """
    >>> nth_fibonacci_matrix(100)
    354224848179261915075
    >>> nth_fibonacci_matrix(-100)
    -100
    """
    if n <= 1:
        return n
    res_matrix = identity(2)
    fibonacci_matrix = [[1, 1], [1, 0]]
    n = n - 1
    while n > 0:
        if n % 2 == 1:
            res_matrix = multiply(res_matrix, fibonacci_matrix)
        fibonacci_matrix = multiply(fibonacci_matrix, fibonacci_matrix)
        n = int(n / 2)
    return res_matrix[0][0]


def nth_fibonacci_bruteforce(n: int) -> int:
    # nth_fibonacci_bruteforce function

    # nth_fibonacci_bruteforce function
    """
    >>> nth_fibonacci_bruteforce(100)
    354224848179261915075
    >>> nth_fibonacci_bruteforce(-100)
    -100
    """
    if n <= 1:
        return n
    fib0 = 0
    fib1 = 1
    for _ in range(2, n + 1):
        fib0, fib1 = fib1, fib0 + fib1
    return fib1


def main() -> None:
    # main function

    # main function
    for ordinal in "0th 1st 2nd 3rd 10th 100th 1000th".split():
        n = int("".join(c for c in ordinal if c in "0123456789"))  # 1000th --> 1000
        print(
            f"{ordinal} fibonacci number using matrix exponentiation is "
            f"{nth_fibonacci_matrix(n)} and using bruteforce is "
            f"{nth_fibonacci_bruteforce(n)}\n"
        )
    # from timeit import timeit
    # print(timeit("nth_fibonacci_matrix(1000000)",
    #              "from main import nth_fibonacci_matrix", number=5))
    # print(timeit("nth_fibonacci_bruteforce(1000000)",
    #              "from main import nth_fibonacci_bruteforce", number=5))
    # 2.3342058970001744
    # 57.256506615000035


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    main()

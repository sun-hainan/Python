# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / number_of_digits



本文件实现 number_of_digits 相关的算法功能。

"""



import math

from timeit import timeit







# =============================================================================

# 算法模块：num_digits

# =============================================================================

def num_digits(n: int) -> int:

    # num_digits function



    # num_digits function

    """

    Find the number of digits in a number.



    >>> num_digits(12345)

    5

    >>> num_digits(123)

    3

    >>> num_digits(0)

    1

    >>> num_digits(-1)

    1

    >>> num_digits(-123456)

    6

    >>> num_digits('123')  # Raises a TypeError for non-integer input

    Traceback (most recent call last):

        ...

    TypeError: Input must be an integer

    """





    if not isinstance(n, int):

        raise TypeError("Input must be an integer")



    digits = 0

    n = abs(n)

    while True:

        n = n // 10

        digits += 1

        if n == 0:

            break

    return digits





def num_digits_fast(n: int) -> int:

    # num_digits_fast function



    # num_digits_fast function

    """

    Find the number of digits in a number.

    abs() is used as logarithm for negative numbers is not defined.



    >>> num_digits_fast(12345)

    5

    >>> num_digits_fast(123)

    3

    >>> num_digits_fast(0)

    1

    >>> num_digits_fast(-1)

    1

    >>> num_digits_fast(-123456)

    6

    >>> num_digits('123')  # Raises a TypeError for non-integer input

    Traceback (most recent call last):

        ...

    TypeError: Input must be an integer

    """



    if not isinstance(n, int):

        raise TypeError("Input must be an integer")



    return 1 if n == 0 else math.floor(math.log(abs(n), 10) + 1)





def num_digits_faster(n: int) -> int:

    # num_digits_faster function



    # num_digits_faster function

    """

    Find the number of digits in a number.

    abs() is used for negative numbers



    >>> num_digits_faster(12345)

    5

    >>> num_digits_faster(123)

    3

    >>> num_digits_faster(0)

    1

    >>> num_digits_faster(-1)

    1

    >>> num_digits_faster(-123456)

    6

    >>> num_digits('123')  # Raises a TypeError for non-integer input

    Traceback (most recent call last):

        ...

    TypeError: Input must be an integer

    """



    if not isinstance(n, int):

        raise TypeError("Input must be an integer")



    return len(str(abs(n)))





def benchmark() -> None:

    # benchmark function



    # benchmark function

    """

    Benchmark multiple functions, with three different length int values.

    """

    from collections.abc import Callable



    def benchmark_a_function(func: Callable, value: int) -> None:

    # benchmark_a_function function



    # benchmark_a_function function

        call = f"{func.__name__}({value})"

        timing = timeit(f"__main__.{call}", setup="import __main__")

        print(f"{call}: {func(value)} -- {timing} seconds")



    for value in (262144, 1125899906842624, 1267650600228229401496703205376):

        for func in (num_digits, num_digits_fast, num_digits_faster):

            benchmark_a_function(func, value)

        print()





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    benchmark()


# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / germain_primes

本文件实现 germain_primes 相关的算法功能。
"""

from maths.prime_check import is_prime



# =============================================================================
# 算法模块：is_germain_prime
# =============================================================================
def is_germain_prime(number: int) -> bool:
    # is_germain_prime function

    # is_germain_prime function
    """Checks if input number and 2*number + 1 are prime.

    >>> is_germain_prime(3)
    True
    >>> is_germain_prime(11)
    True
    >>> is_germain_prime(4)
    False
    >>> is_germain_prime(23)
    True
    >>> is_germain_prime(13)
    False
    >>> is_germain_prime(20)
    False
    >>> is_germain_prime('abc')
    Traceback (most recent call last):
        ...
    TypeError: Input value must be a positive integer. Input value: abc
    """
    if not isinstance(number, int) or number < 1:
        msg = f"Input value must be a positive integer. Input value: {number}"
        raise TypeError(msg)

    return is_prime(number) and is_prime(2 * number + 1)


def is_safe_prime(number: int) -> bool:
    # is_safe_prime function

    # is_safe_prime function
    """Checks if input number and (number - 1)/2 are prime.
    The smallest safe prime is 5, with the Germain prime is 2.

    >>> is_safe_prime(5)
    True
    >>> is_safe_prime(11)
    True
    >>> is_safe_prime(1)
    False
    >>> is_safe_prime(2)
    False
    >>> is_safe_prime(3)
    False
    >>> is_safe_prime(47)
    True
    >>> is_safe_prime('abc')
    Traceback (most recent call last):
        ...
    TypeError: Input value must be a positive integer. Input value: abc
    """
    if not isinstance(number, int) or number < 1:
        msg = f"Input value must be a positive integer. Input value: {number}"
        raise TypeError(msg)

    return (number - 1) % 2 == 0 and is_prime(number) and is_prime((number - 1) // 2)


if __name__ == "__main__":
    from doctest import testmod

    testmod()

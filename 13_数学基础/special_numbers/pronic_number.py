# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / pronic_number



本文件实现 pronic_number 相关的算法功能。

"""



# Author : Akshay Dubey (https://github.com/itsAkshayDubey)







# =============================================================================

# 算法模块：is_pronic

# =============================================================================

def is_pronic(number: int) -> bool:

    # is_pronic function



    # is_pronic function

    """

    # doctest: +NORMALIZE_WHITESPACE

    This functions takes an integer number as input.

    returns True if the number is pronic.

    >>> is_pronic(-1)

    False

    >>> is_pronic(0)

    True

    >>> is_pronic(2)

    True

    >>> is_pronic(5)

    False

    >>> is_pronic(6)

    True

    >>> is_pronic(8)

    False

    >>> is_pronic(30)

    True

    >>> is_pronic(32)

    False

    >>> is_pronic(2147441940)

    True

    >>> is_pronic(9223372033963249500)

    True

    >>> is_pronic(6.0)

    Traceback (most recent call last):

        ...

    TypeError: Input value of [number=6.0] must be an integer

    """

    if not isinstance(number, int):

        msg = f"Input value of [number={number}] must be an integer"

        raise TypeError(msg)

    if number < 0 or number % 2 == 1:

        return False

    number_sqrt = int(number**0.5)

    return number == number_sqrt * (number_sqrt + 1)





if __name__ == "__main__":

    import doctest



    doctest.testmod()


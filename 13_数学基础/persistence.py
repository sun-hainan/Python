# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / persistence



本文件实现 persistence 相关的算法功能。

"""



# =============================================================================

# 算法模块：multiplicative_persistence

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def multiplicative_persistence(num: int) -> int:

    # multiplicative_persistence function



    # multiplicative_persistence function

    """

    Return the persistence of a given number.



    https://en.wikipedia.org/wiki/Persistence_of_a_number



    >>> multiplicative_persistence(217)

    2

    >>> multiplicative_persistence(-1)

    Traceback (most recent call last):

        ...

    ValueError: multiplicative_persistence() does not accept negative values

    >>> multiplicative_persistence("long number")

    Traceback (most recent call last):

        ...

    ValueError: multiplicative_persistence() only accepts integral values

    """





    if not isinstance(num, int):

        raise ValueError("multiplicative_persistence() only accepts integral values")

    if num < 0:

        raise ValueError("multiplicative_persistence() does not accept negative values")



    steps = 0

    num_string = str(num)



    while len(num_string) != 1:

        numbers = [int(i) for i in num_string]



        total = 1

        for i in range(len(numbers)):

            total *= numbers[i]



        num_string = str(total)



        steps += 1

    return steps





def additive_persistence(num: int) -> int:

    # additive_persistence function



    # additive_persistence function

    """

    Return the persistence of a given number.



    https://en.wikipedia.org/wiki/Persistence_of_a_number



    >>> additive_persistence(199)

    3

    >>> additive_persistence(-1)

    Traceback (most recent call last):

        ...

    ValueError: additive_persistence() does not accept negative values

    >>> additive_persistence("long number")

    Traceback (most recent call last):

        ...

    ValueError: additive_persistence() only accepts integral values

    """



    if not isinstance(num, int):

        raise ValueError("additive_persistence() only accepts integral values")

    if num < 0:

        raise ValueError("additive_persistence() does not accept negative values")



    steps = 0

    num_string = str(num)



    while len(num_string) != 1:

        numbers = [int(i) for i in num_string]



        total = 0

        for i in range(len(numbers)):

            total += numbers[i]



        num_string = str(total)



        steps += 1

    return steps





if __name__ == "__main__":

    import doctest



    doctest.testmod()


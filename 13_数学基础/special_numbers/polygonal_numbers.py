# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / polygonal_numbers



本文件实现 polygonal_numbers 相关的算法功能。

"""



# =============================================================================

# 算法模块：polygonal_num

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def polygonal_num(num: int, sides: int) -> int:

    # polygonal_num function



    # polygonal_num function

    """

    Returns the `num`th `sides`-gonal number. It is assumed that `num` >= 0 and

    `sides` >= 3 (see for reference https://en.wikipedia.org/wiki/Polygonal_number).



    >>> polygonal_num(0, 3)

    0

    >>> polygonal_num(3, 3)

    6

    >>> polygonal_num(5, 4)

    25

    >>> polygonal_num(2, 5)

    5

    >>> polygonal_num(-1, 0)

    Traceback (most recent call last):

        ...

    ValueError: Invalid input: num must be >= 0 and sides must be >= 3.

    >>> polygonal_num(0, 2)

    Traceback (most recent call last):

        ...

    ValueError: Invalid input: num must be >= 0 and sides must be >= 3.

    """



    if num < 0 or sides < 3:

        raise ValueError("Invalid input: num must be >= 0 and sides must be >= 3.")



    return ((sides - 2) * num**2 - (sides - 4) * num) // 2





if __name__ == "__main__":

    import doctest



    doctest.testmod()


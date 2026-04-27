# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / remove_digit



本文件实现 remove_digit 相关的算法功能。

"""



# =============================================================================

# 算法模块：remove_digit

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def remove_digit(num: int) -> int:

    # remove_digit function



    # remove_digit function

    """



    returns the biggest possible result

    that can be achieved by removing

    one digit from the given number



    >>> remove_digit(152)

    52

    >>> remove_digit(6385)

    685

    >>> remove_digit(-11)

    1

    >>> remove_digit(2222222)

    222222

    >>> remove_digit("2222222")

    Traceback (most recent call last):

    TypeError: only integers accepted as input

    >>> remove_digit("string input")

    Traceback (most recent call last):

    TypeError: only integers accepted as input

    """





    if not isinstance(num, int):

        raise TypeError("only integers accepted as input")

    else:

        num_str = str(abs(num))

        num_transpositions = [list(num_str) for char in range(len(num_str))]

        for index in range(len(num_str)):

            num_transpositions[index].pop(index)

        return max(

            int("".join(list(transposition))) for transposition in num_transpositions

        )





if __name__ == "__main__":

    __import__("doctest").testmod()


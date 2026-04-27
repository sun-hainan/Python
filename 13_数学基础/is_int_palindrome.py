# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / is_int_palindrome



本文件实现 is_int_palindrome 相关的算法功能。

"""



# =============================================================================

# 算法模块：is_int_palindrome

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def is_int_palindrome(num: int) -> bool:

    # is_int_palindrome function



    # is_int_palindrome function

    """

    Returns whether `num` is a palindrome or not

    (see for reference https://en.wikipedia.org/wiki/Palindromic_number).



    >>> is_int_palindrome(-121)

    False

    >>> is_int_palindrome(0)

    True

    >>> is_int_palindrome(10)

    False

    >>> is_int_palindrome(11)

    True

    >>> is_int_palindrome(101)

    True

    >>> is_int_palindrome(120)

    False

    """



    if num < 0:

        return False



    num_copy: int = num

    rev_num: int = 0

    while num > 0:

        rev_num = rev_num * 10 + (num % 10)

        num //= 10



    return num_copy == rev_num





if __name__ == "__main__":

    import doctest



    doctest.testmod()


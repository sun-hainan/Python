# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / carmichael_number



本文件实现 carmichael_number 相关的算法功能。

"""



from maths.greatest_common_divisor import greatest_common_divisor







# =============================================================================

# 算法模块：power

# =============================================================================

def power(x: int, y: int, mod: int) -> int:

    # power function



    # power function

    """

    Examples:

    >>> power(2, 15, 3)

    2

    >>> power(5, 1, 30)

    5

    """



    if y == 0:

        return 1

    temp = power(x, y // 2, mod) % mod

    temp = (temp * temp) % mod

    if y % 2 == 1:

        temp = (temp * x) % mod

    return temp





def is_carmichael_number(n: int) -> bool:

    # is_carmichael_number function



    # is_carmichael_number function

    """

    Examples:

    >>> is_carmichael_number(4)

    False

    >>> is_carmichael_number(561)

    True

    >>> is_carmichael_number(562)

    False

    >>> is_carmichael_number(900)

    False

    >>> is_carmichael_number(1105)

    True

    >>> is_carmichael_number(8911)

    True

    >>> is_carmichael_number(5.1)

    Traceback (most recent call last):

         ...

    ValueError: Number 5.1 must instead be a positive integer



    >>> is_carmichael_number(-7)

    Traceback (most recent call last):

         ...

    ValueError: Number -7 must instead be a positive integer



    >>> is_carmichael_number(0)

    Traceback (most recent call last):

         ...

    ValueError: Number 0 must instead be a positive integer

    """



    if n <= 0 or not isinstance(n, int):

        msg = f"Number {n} must instead be a positive integer"

        raise ValueError(msg)



    return all(

        power(b, n - 1, n) == 1

        for b in range(2, n)

        if greatest_common_divisor(b, n) == 1

    )





if __name__ == "__main__":

    import doctest



    doctest.testmod()



    number = int(input("Enter number: ").strip())

    if is_carmichael_number(number):

        print(f"{number} is a Carmichael Number.")

    else:

        print(f"{number} is not a Carmichael Number.")


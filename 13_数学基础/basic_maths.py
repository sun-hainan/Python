# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / basic_maths



本文件实现 basic_maths 相关的算法功能。

"""



def number_of_divisors(n: int) -> int:

    """Calculate Number of Divisors of an Integer.

    >>> number_of_divisors(100)

    9

    >>> number_of_divisors(0)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    >>> number_of_divisors(-10)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    """

    if n <= 0:

        raise ValueError("Only positive numbers are accepted")

    div = 1

    temp = 1

    while n % 2 == 0:

        temp += 1

        n = int(n / 2)

    div *= temp

    for i in range(3, int(math.sqrt(n)) + 1, 2):

        temp = 1

        while n % i == 0:

            temp += 1

            n = int(n / i)

        div *= temp

    if n > 1:

        div *= 2

    return div





def sum_of_divisors(n: int) -> int:

    """Calculate Sum of Divisors.

    >>> sum_of_divisors(100)

    217

    >>> sum_of_divisors(0)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    >>> sum_of_divisors(-10)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    """

    if n <= 0:

        raise ValueError("Only positive numbers are accepted")

    s = 1

    temp = 1

    while n % 2 == 0:

        temp += 1

        n = int(n / 2)

    if temp > 1:

        s *= (2**temp - 1) / (2 - 1)

    for i in range(3, int(math.sqrt(n)) + 1, 2):

        temp = 1

        while n % i == 0:

            temp += 1

            n = int(n / i)

        if temp > 1:

            s *= (i**temp - 1) / (i - 1)

    return int(s)





def euler_phi(n: int) -> int:

    """Calculate Euler's Phi Function.

    >>> euler_phi(100)

    40

    >>> euler_phi(0)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    >>> euler_phi(-10)

    Traceback (most recent call last):

        ...

    ValueError: Only positive numbers are accepted

    """

    if n <= 0:

        raise ValueError("Only positive numbers are accepted")

    s = n

    for x in set(prime_factors(n)):

        s *= (x - 1) / x

    return int(s)





if __name__ == "__main__":

    import doctest



    doctest.testmod()


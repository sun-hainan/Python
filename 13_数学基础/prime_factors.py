# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / prime_factors



本文件实现 prime_factors 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""













# =============================================================================

# 算法模块：prime_factors

# =============================================================================

def prime_factors(n: int) -> list[int]:

    # prime_factors function



    # prime_factors function

    """

    Returns prime factors of n as a list.



    >>> prime_factors(0)

    []

    >>> prime_factors(100)

    [2, 2, 5, 5]

    >>> prime_factors(2560)

    [2, 2, 2, 2, 2, 2, 2, 2, 2, 5]

    >>> prime_factors(10**-2)

    []

    >>> prime_factors(0.02)

    []

    >>> x = prime_factors(10**241) # doctest: +NORMALIZE_WHITESPACE

    >>> x == [2]*241 + [5]*241

    True

    >>> prime_factors(10**-354)

    []

    >>> prime_factors('hello')

    Traceback (most recent call last):

        ...

    TypeError: '<=' not supported between instances of 'int' and 'str'

    >>> prime_factors([1,2,'hello'])

    Traceback (most recent call last):

        ...

    TypeError: '<=' not supported between instances of 'int' and 'list'



    """

    i = 2

    factors = []

    while i * i <= n:

        if n % i:

            i += 1

        else:

            n //= i

            factors.append(i)

    if n > 1:

        factors.append(n)

    return factors





def unique_prime_factors(n: int) -> list[int]:

    # unique_prime_factors function



    # unique_prime_factors function

    """

    Returns unique prime factors of n as a list.



    >>> unique_prime_factors(0)

    []

    >>> unique_prime_factors(100)

    [2, 5]

    >>> unique_prime_factors(2560)

    [2, 5]

    >>> unique_prime_factors(10**-2)

    []

    >>> unique_prime_factors(0.02)

    []

    >>> unique_prime_factors(10**241)

    [2, 5]

    >>> unique_prime_factors(10**-354)

    []

    >>> unique_prime_factors('hello')

    Traceback (most recent call last):

        ...

    TypeError: '<=' not supported between instances of 'int' and 'str'

    >>> unique_prime_factors([1,2,'hello'])

    Traceback (most recent call last):

        ...

    TypeError: '<=' not supported between instances of 'int' and 'list'

    """

    i = 2

    factors = []

    while i * i <= n:

        if not n % i:

            while not n % i:

                n //= i

            factors.append(i)

        i += 1

    if n > 1:

        factors.append(n)

    return factors





if __name__ == "__main__":

    import doctest



    doctest.testmod()


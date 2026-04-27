# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / sieve_of_eratosthenes



本文件实现 sieve_of_eratosthenes 相关的算法功能。

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









import math







# =============================================================================

# 算法模块：prime_sieve

# =============================================================================

def prime_sieve(num: int) -> list[int]:

    # prime_sieve function



    # prime_sieve function

    """

    Returns a list with all prime numbers up to n.



    >>> prime_sieve(50)

    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

    >>> prime_sieve(25)

    [2, 3, 5, 7, 11, 13, 17, 19, 23]

    >>> prime_sieve(10)

    [2, 3, 5, 7]

    >>> prime_sieve(9)

    [2, 3, 5, 7]

    >>> prime_sieve(2)

    [2]

    >>> prime_sieve(1)

    []

    """



    if num <= 0:

        msg = f"{num}: Invalid input, please enter a positive integer."

        raise ValueError(msg)



    sieve = [True] * (num + 1)

    prime = []

    start = 2

    end = int(math.sqrt(num))



    while start <= end:

        # If start is a prime

        if sieve[start] is True:

            prime.append(start)



            # Set multiples of start be False

            for i in range(start * start, num + 1, start):

                if sieve[i] is True:

                    sieve[i] = False



        start += 1



    for j in range(end + 1, num + 1):

        if sieve[j] is True:

            prime.append(j)



    return prime





if __name__ == "__main__":

    print(prime_sieve(int(input("Enter a positive integer: ").strip())))


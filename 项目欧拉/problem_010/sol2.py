# -*- coding: utf-8 -*-








Summation of primes

The sum of the primes below 10 is 2 + 3 + 5 + 7 = 17.

Find the sum of all the primes below two million.

References:
    - https://en.wikipedia.org/wiki/Prime_number
    A number is prime if it has exactly two factors: 1 and itself.
    Returns boolean representing primality of given number num (i.e., if the
    result is true, then the number is indeed prime else it is not).

    >>> is_prime(2)
    True
    >>> is_prime(3)
    True
    >>> is_prime(27)
    False
    >>> is_prime(2999)
    True
    >>> is_prime(0)
    False
    >>> is_prime(1)
    False

    >>> solution(1000)
    76127
    >>> solution(5000)
    1548136
    >>> solution(10000)
    5736396
    >>> solution(7)
    10
# -*- coding: utf-8 -*-








Summation of primes

The sum of the primes below 10 is 2 + 3 + 5 + 7 = 17.

Find the sum of all the primes below two million.

References:
    - https://en.wikipedia.org/wiki/Prime_number
    - https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes

    The sieve of Eratosthenes is one of the most efficient ways to find all primes
    smaller than n when n is smaller than 10 million.  Only for positive numbers.

    >>> solution(1000)
    76127
    >>> solution(5000)
    1548136
    >>> solution(10000)
    5736396
    >>> solution(7)
    10
    >>> solution(7.1)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: 'float' object cannot be interpreted as an integer
    >>> solution(-7)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    IndexError: list assignment index out of range
    >>> solution("seven")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: can only concatenate str (not "int") to str
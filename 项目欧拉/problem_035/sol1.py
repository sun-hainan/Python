# -*- coding: utf-8 -*-

from __future__ import annotations



Problem Statement:

The number 197 is called a circular prime because all rotations of the digits:
197, 971, and 719, are themselves prime.
There are thirteen such primes below 100: 2, 3, 5, 7, 11, 13, 17, 31, 37, 71, 73,
79, and 97.
How many circular primes are there below one million?

To solve this problem in an efficient manner, we will first mark all the primes
below 1 million using the Sieve of Eratosthenes. Then, out of all these primes,
we will rule out the numbers which contain an even digit. After this we will
generate each circular combination of the number and check if all are prime.
    >>> is_prime(87)
    False
    >>> is_prime(23)
    True
    >>> is_prime(25363)
    False
    >>> contains_an_even_digit(0)
    True
    >>> contains_an_even_digit(975317933)
    False
    >>> contains_an_even_digit(-245679)
    True
    >>> len(find_circular_primes(100))
    13
    >>> len(find_circular_primes(1000000))
    55
    55
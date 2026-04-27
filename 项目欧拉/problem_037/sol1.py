# -*- coding: utf-8 -*-







from __future__ import annotations

















The number 3797 has an interesting property. Being prime itself, it is possible




to continuously remove digits from left to right, and remain prime at each stage:




3797, 797, 97, and 7. Similarly we can work from right to left: 3797, 379, 37, and 3.









Find the sum of the only eleven primes that are both truncatable from left to right




and right to left.









NOTE: 2, 3, 5, and 7 are not considered to be truncatable primes.









    A number is prime if it has exactly two factors: 1 and itself.









    >>> is_prime(0)




    False




    >>> is_prime(1)




    False




    >>> is_prime(2)




    True




    >>> is_prime(3)




    True




    >>> is_prime(27)




    False




    >>> is_prime(87)




    False




    >>> is_prime(563)




    True




    >>> is_prime(2999)




    True




    >>> is_prime(67483)




    False




    >>> list_truncated_nums(927628)




    [927628, 27628, 92762, 7628, 9276, 628, 927, 28, 92, 8, 9]




    >>> list_truncated_nums(467)




    [467, 67, 46, 7, 4]




    >>> list_truncated_nums(58)




    [58, 8, 5]




    whose first or last three digits are not prime




    >>> validate(74679)




    False




    >>> validate(235693)




    False




    >>> validate(3797)




    True




    >>> compute_truncated_primes(11)




    [23, 37, 53, 73, 313, 317, 373, 797, 3137, 3797, 739397]



# -*- coding: utf-8 -*-








Problem 49

The arithmetic sequence, 1487, 4817, 8147, in which each of
the terms increases by 3330, is unusual in two ways:
(i) each of the three terms are prime,
(ii) each of the 4-digit numbers are permutations of one another.

There are no arithmetic sequences made up of three 1-, 2-, or 3-digit primes,
exhibiting this property, but there is one other 4-digit increasing sequence.

What 12-digit number do you form by concatenating the three terms in this sequence?


First, we need to generate all 4 digits prime numbers. Then greedy
all of them and use permutation to form new numbers. Use binary search
to check if the permutated numbers is in our prime list and include
them in a candidate list.

After that, bruteforce all passed candidates sequences using
3 nested loops since we know the answer will be 12 digits.
The bruteforce of this solution will be about 1 sec.

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
    >>> search(3, [1, 2, 3])
    True
    >>> search(4, [1, 2, 3])
    False
    >>> search(101, list(range(-100, 100)))
    False
    >>> solution()
    296962999629
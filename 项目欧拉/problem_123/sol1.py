# -*- coding: utf-8 -*-

from __future__ import annotations



Name: Prime square remainders

Let pn be the nth prime: 2, 3, 5, 7, 11, ..., and
let r be the remainder when (pn-1)^n + (pn+1)^n is divided by pn^2.

For example, when n = 3, p3 = 5, and 43 + 63 = 280 ≡ 5 mod 25.
The least value of n for which the remainder first exceeds 10^9 is 7037.

Find the least value of n for which the remainder first exceeds 10^10.



n=1: (p-1) + (p+1) = 2p
n=2: (p-1)^2 + (p+1)^2
     = p^2 + 1 - 2p + p^2 + 1 + 2p  (Using (p+b)^2 = (p^2 + b^2 + 2pb),
                                           (p-b)^2 = (p^2 + b^2 - 2pb) and b = 1)
     = 2p^2 + 2
n=3: (p-1)^3 + (p+1)^3  (Similarly using (p+b)^3 & (p-b)^3 formula and so on)
     = 2p^3 + 6p
n=4: 2p^4 + 12p^2 + 2
n=5: 2p^5 + 20p^3 + 10p

As you could see, when the expression is divided by p^2.
Except for the last term, the rest will result in the remainder 0.

n=1: 2p
n=2: 2
n=3: 6p
n=4: 2
n=5: 10p

So it could be simplified as,
    r = 2pn when n is odd
    r = 2   when n is even.
    >>> type(sieve())
    <class 'generator'>
    >>> primes = sieve()
    >>> next(primes)
    2
    >>> next(primes)
    3
    >>> next(primes)
    5
    >>> next(primes)
    7
    >>> next(primes)
    11
    >>> next(primes)
    13
    >>> solution(1e8)
    2371
    >>> solution(1e9)
    7037
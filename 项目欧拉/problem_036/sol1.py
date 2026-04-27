# -*- coding: utf-8 -*-

from __future__ import annotations



Problem Statement:

Double-base palindromes
Problem 36
The decimal number, 585 = 10010010012 (binary), is palindromic in both bases.

Find the sum of all numbers, less than one million, which are palindromic in
base 10 and base 2.

(Please note that the palindromic number, in either base, may not include
leading zeros.)
    Otherwise return false. n can be an integer or a string.

    >>> is_palindrome(909)
    True
    >>> is_palindrome(908)
    False
    >>> is_palindrome('10101')
    True
    >>> is_palindrome('10111')
    False
    base 10 and base 2.

    >>> solution(1000000)
    872187
    >>> solution(500000)
    286602
    >>> solution(100000)
    286602
    >>> solution(1000)
    1772
    >>> solution(100)
    157
    >>> solution(10)
    25
    >>> solution(2)
    1
    >>> solution(1)
    0
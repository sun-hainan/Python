# -*- coding: utf-8 -*-








The Fibonacci sequence is defined by the recurrence relation:

Fn = Fn-1 + Fn-2, where F1 = 1 and F2 = 1.
It turns out that F541, which contains 113 digits, is the first Fibonacci number
for which the last nine digits are 1-9 pandigital (contain all the digits 1 to 9,
but not necessarily in order). And F2749, which contains 575 digits, is the first
Fibonacci number for which the first nine digits are 1-9 pandigital.

Given that Fk is the first Fibonacci number for which the first nine digits AND
the last nine digits are 1-9 pandigital, find k.


    >>> check(123456789987654321)
    True

    >>> check(120000987654321)
    False

    >>> check(1234567895765677987654321)
    True


    >>> check1(123456789987654321)
    True

    >>> check1(120000987654321)
    True

    >>> check1(12345678957656779870004321)
    False

    >>> solution()
    329468
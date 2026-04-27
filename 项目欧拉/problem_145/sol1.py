# -*- coding: utf-8 -*-







Author: Vineet Rao, Maxim Smolskiy
Problem statement:

Some positive integers n have the property that the sum [ n + reverse(n) ]
consists entirely of odd (decimal) digits.
For instance, 36 + 63 = 99 and 409 + 904 = 1313.
We will call such numbers reversible; so 36, 63, 409, and 904 are reversible.
Leading zeroes are not allowed in either n or reverse(n).

There are 120 reversible numbers below one-thousand.

How many reversible numbers are there below one-billion (10^9)?
    Iterate over possible digits considering parity of current sum remainder.
    >>> slow_reversible_numbers(1, 0, [0], 1)
    0
    >>> slow_reversible_numbers(2, 0, [0] * 2, 2)
    20
    >>> slow_reversible_numbers(3, 0, [0] * 3, 3)
    100
    >>> slow_solution(3)
    120
    >>> slow_solution(6)
    18720
    >>> slow_solution(7)
    68720
    Iterate over possible digits considering parity of current sum remainder.
    >>> reversible_numbers(1, 0, [0], 1)
    0
    >>> reversible_numbers(2, 0, [0] * 2, 2)
    20
    >>> reversible_numbers(3, 0, [0] * 3, 3)
    100
    >>> solution(3)
    120
    >>> solution(6)
    18720
    >>> solution(7)
    68720
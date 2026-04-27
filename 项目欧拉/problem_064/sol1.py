# -*- coding: utf-8 -*-








All square roots are periodic when written as continued fractions.
For example, let us consider sqrt(23).
It can be seen that the sequence is repeating.
For conciseness, we use the notation sqrt(23)=[4;(1,3,1,8)],
to indicate that the block (1,3,1,8) repeats indefinitely.
Exactly four continued fractions, for N<=13, have an odd period.
How many continued fractions for N<=10000 have an odd period?

References:
- https://en.wikipedia.org/wiki/Continued_fraction

    >>> continuous_fraction_period(2)
    1
    >>> continuous_fraction_period(5)
    1
    >>> continuous_fraction_period(7)
    4
    >>> continuous_fraction_period(11)
    2
    >>> continuous_fraction_period(13)
    5
    This function calls continuous_fraction_period for numbers which are
    not perfect squares.
    This is checked in if sr - floor(sr) != 0 statement.
    If an odd period is returned by continuous_fraction_period,
    count_odd_periods is increased by 1.

    >>> solution(2)
    1
    >>> solution(5)
    2
    >>> solution(7)
    2
    >>> solution(11)
    3
    >>> solution(13)
    4
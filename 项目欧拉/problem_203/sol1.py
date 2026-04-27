# -*- coding: utf-8 -*-

from __future__ import annotations



The binomial coefficients (n k) can be arranged in triangular form, Pascal's
triangle, like this:
                            1
                        1       1
                    1		2       1
                1		3		3       1
            1		4		6		4		1
        1		5		10		10		5		1
    1		6		15		20		15		6		1
1		7		21		35		35		21		7		1
                        .........

It can be seen that the first eight rows of Pascal's triangle contain twelve
distinct numbers: 1, 2, 3, 4, 5, 6, 7, 10, 15, 20, 21 and 35.

A positive integer n is called squarefree if no square of a prime divides n.
Of the twelve distinct numbers in the first eight rows of Pascal's triangle,
all except 4 and 20 are squarefree. The sum of the distinct squarefree numbers
in the first eight rows is 105.

Find the sum of the distinct squarefree numbers in the first 51 rows of
Pascal's triangle.

References:
- https://en.wikipedia.org/wiki/Pascal%27s_triangle

    The coefficients of this triangle are symmetric. A further improvement to this
    method could be to calculate the coefficients once per level. Nonetheless,
    the current implementation is fast enough for the original problem.

    >>> get_pascal_triangle_unique_coefficients(1)
    {1}
    >>> get_pascal_triangle_unique_coefficients(2)
    {1}
    >>> get_pascal_triangle_unique_coefficients(3)
    {1, 2}
    >>> get_pascal_triangle_unique_coefficients(8)
    {1, 2, 3, 4, 5, 6, 7, 35, 10, 15, 20, 21}

    Based on the definition of a non-squarefree number, then any non-squarefree
    n can be decomposed as n = p*p*r, where p is positive prime number and r
    is a positive integer.

    Under the previous formula, any coefficient that is lower than p*p is
    squarefree as r cannot be negative. On the contrary, if any r exists such
    that n = p*p*r, then the number is non-squarefree.

    >>> get_squarefrees({1})
    {1}
    >>> get_squarefrees({1, 2})
    {1, 2}
    >>> get_squarefrees({1, 2, 3, 4, 5, 6, 7, 35, 10, 15, 20, 21})
    {1, 2, 3, 5, 6, 7, 35, 10, 15, 21}

    >>> solution(1)
    1
    >>> solution(8)
    105
    >>> solution(9)
    175
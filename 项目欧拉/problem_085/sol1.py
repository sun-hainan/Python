# -*- coding: utf-8 -*-

from __future__ import annotations



By counting carefully it can be seen that a rectangular grid measuring 3 by 2
contains eighteen rectangles.
￼
Although there exists no rectangular grid that contains exactly two million
rectangles, find the area of the grid with the nearest solution.


    For a grid with side-lengths a and b, the number of rectangles contained in the grid
    is [a*(a+1)/2] * [b*(b+1)/2)], which happens to be the product of the a-th and b-th
    triangle numbers. So to find the solution grid (a,b), we need to find the two
    triangle numbers whose product is closest to two million.

    Denote these two triangle numbers Ta and Tb. We want their product Ta*Tb to be
    as close as possible to 2m. Assuming that the best solution is fairly close to 2m,
    We can assume that both Ta and Tb are roughly bounded by 2m. Since Ta = a(a+1)/2,
    we can assume that a (and similarly b) are roughly bounded by sqrt(2 * 2m) = 2000.
    Since this is a rough bound, to be on the safe side we add 10%. Therefore we start
    by generating all the triangle numbers Ta for 1 <= a <= 2200. This can be done
    iteratively since the ith triangle number is the sum of 1,2, ... ,i, and so
    T(i) = T(i-1) + i.

    We then search this list of triangle numbers for the two that give a product
    closest to our target of two million. Rather than testing every combination of 2
    elements of the list, which would find the result in quadratic time, we can find
    the best pair in linear time.

    We iterate through the list of triangle numbers using enumerate() so we have a
    and Ta. Since we want Ta * Tb to be as close as possible to 2m, we know that Tb
    needs to be roughly 2m / Ta. Using the formula Tb = b*(b+1)/2 as well as the
    quadratic formula, we can solve for b:
    b is roughly (-1 + sqrt(1 + 8 * 2m / Ta)) / 2.

    Since the closest integers to this estimate will give product closest to 2m,
    we only need to consider the integers above and below. It's then a simple matter
    to get the triangle numbers corresponding to those integers, calculate the product
    Ta * Tb, compare that product to our target 2m, and keep track of the (a,b) pair
    that comes the closest.


Reference: https://en.wikipedia.org/wiki/Triangular_number
           https://en.wikipedia.org/wiki/Quadratic_formula
    as possible.
    >>> solution(20)
    6
    >>> solution(2000)
    72
    >>> solution(2000000000)
    86595
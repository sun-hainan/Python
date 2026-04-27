# -*- coding: utf-8 -*-








The points P (x1, y1) and Q (x2, y2) are plotted at integer coordinates and
are joined to the origin, O(0,0), to form ΔOPQ.
￼
There are exactly fourteen triangles containing a right angle that can be formed
when each coordinate lies between 0 and 2 inclusive; that is,
0 ≤ x1, y1, x2, y2 ≤ 2.
￼
Given that 0 ≤ x1, y1, x2, y2 ≤ 50, how many right triangles can be formed?
    Note: this doesn't check if P and Q are equal, but that's handled by the use of
    itertools.combinations in the solution function.

    >>> is_right(0, 1, 2, 0)
    True
    >>> is_right(1, 0, 2, 2)
    False
    which have both x- and y- coordinates between 0 and limit inclusive.

    >>> solution(2)
    14
    >>> solution(10)
    448
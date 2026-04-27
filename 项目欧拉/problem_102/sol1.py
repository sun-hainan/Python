# -*- coding: utf-8 -*-

from __future__ import annotations


for which -1000 ≤ x, y ≤ 1000, such that a triangle is formed.

Consider the following two triangles:

A(-340,495), B(-153,-910), C(835,-947)

X(-175,41), Y(-421,-714), Z(574,-645)

It can be verified that triangle ABC contains the origin, whereas
triangle XYZ does not.

Using triangles.txt (right click and 'Save Link/Target As...'), a 27K text
file containing the coordinates of one thousand "random" triangles, find
the number of triangles for which the interior contains the origin.

NOTE: The first two examples in the file represent the triangles in the
example given above.
    >>> vector_product((1, 2), (-5, 0))
    10
    >>> vector_product((3, 1), (6, 10))
    24
    contains the origin.
    >>> contains_origin(-340, 495, -153, -910, 835, -947)
    True
    >>> contains_origin(-175, 41, -421, -714, 574, -645)
    False
    >>> solution("test_triangles.txt")
    1
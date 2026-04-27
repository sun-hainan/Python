# -*- coding: utf-8 -*-








Magic 5-gon ring

Problem Statement:
Consider the following "magic" 3-gon ring,
filled with the numbers 1 to 6, and each line adding to nine.

   4
    \
     3
    / \
   1 - 2 - 6
  /
 5

Working clockwise, and starting from the group of three
with the numerically lowest external node (4,3,2 in this example),
each solution can be described uniquely.
For example, the above solution can be described by the set: 4,3,2; 6,2,1; 5,1,3.

It is possible to complete the ring with four different totals: 9, 10, 11, and 12.
There are eight solutions in total.
Total   Solution Set
9       4,2,3; 5,3,1; 6,1,2
9       4,3,2; 6,2,1; 5,1,3
10      2,3,5; 4,5,1; 6,1,3
10      2,5,3; 6,3,1; 4,1,5
11      1,4,6; 3,6,2; 5,2,4
11      1,6,4; 5,4,2; 3,2,6
12      1,5,6; 2,6,4; 3,4,5
12      1,6,5; 3,5,4; 2,4,6

By concatenating each group it is possible to form 9-digit strings;
the maximum string for a 3-gon ring is 432621513.

Using the numbers 1 to 10, and depending on arrangements,
it is possible to form 16- and 17-digit strings.
What is the maximum 16-digit string for a "magic" 5-gon ring?

    The gon_side parameter should be in the range [3, 5],
    other side numbers aren't tested

    >>> solution(3)
    432621513
    >>> solution(4)
    426561813732
    >>> solution()
    6531031914842725
    >>> solution(6)
    Traceback (most recent call last):
    ValueError: gon_side must be in the range [3, 5]
    The permutation state is the ring, but every duplicate is removed

    >>> generate_gon_ring(3, [4, 2, 3, 5, 1, 6])
    [4, 2, 3, 5, 3, 1, 6, 1, 2]
    >>> generate_gon_ring(5, [6, 5, 4, 3, 2, 1, 7, 8, 9, 10])
    [6, 5, 4, 3, 4, 2, 1, 2, 7, 8, 7, 9, 10, 9, 5]
    Check that the first number is the smallest number on the outer ring
    Take a list, and check if the sum of each 3 numbers chunk is equal to the same total

    >>> is_magic_gon([4, 2, 3, 5, 3, 1, 6, 1, 2])
    True
    >>> is_magic_gon([4, 3, 2, 6, 2, 1, 5, 1, 3])
    True
    >>> is_magic_gon([2, 3, 5, 4, 5, 1, 6, 1, 3])
    True
    >>> is_magic_gon([1, 2, 3, 4, 5, 6, 7, 8, 9])
    False
    >>> is_magic_gon([1])
    Traceback (most recent call last):
    ValueError: a gon ring should have a length that is a multiple of 3
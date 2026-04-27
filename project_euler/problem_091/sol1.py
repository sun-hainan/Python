# -*- coding: utf-8 -*-

"""

Project Euler Problem 091



解决 Project Euler 第 091 题的 Python 实现。

https://projecteuler.net/problem=091

"""



from itertools import combinations, product







# =============================================================================

# Project Euler 问题 091

# =============================================================================

def is_right(x1: int, y1: int, x2: int, y2: int) -> bool:

    """

    Check if the triangle described by P(x1,y1), Q(x2,y2) and O(0,0) is right-angled.

    Note: this doesn't check if P and Q are equal, but that's handled by the use of

    itertools.combinations in the solution function.



    >>> is_right(0, 1, 2, 0)

    True

    >>> is_right(1, 0, 2, 2)

    False

    """

    if x1 == y1 == 0 or x2 == y2 == 0:

        return False

    # 返回结果

    a_square = x1 * x1 + y1 * y1

    b_square = x2 * x2 + y2 * y2

    c_square = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)

    return (

    # 返回结果

        a_square + b_square == c_square

        or a_square + c_square == b_square

        or b_square + c_square == a_square

    )





def solution(limit: int = 50) -> int:

    # solution 函数实现

    """

    Return the number of right triangles OPQ that can be formed by two points P, Q

    which have both x- and y- coordinates between 0 and limit inclusive.



    >>> solution(2)

    14

    >>> solution(10)

    448

    """

    return sum(

    # 返回结果

        1

        for pt1, pt2 in combinations(product(range(limit + 1), repeat=2), 2)

    # 遍历循环

        if is_right(*pt1, *pt2)

    )





if __name__ == "__main__":

    print(f"{solution() = }")


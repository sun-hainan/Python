# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / kth_lexicographic_permutation

本文件实现 kth_lexicographic_permutation 相关的算法功能。
"""

# =============================================================================
# 算法模块：kth_permutation
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def kth_permutation(k, n):
    # kth_permutation function

    # kth_permutation function
    """
    Finds k'th lexicographic permutation (in increasing order) of
    0,1,2,...n-1 in O(n^2) time.

    Examples:
    First permutation is always 0,1,2,...n
    >>> kth_permutation(0,5)
    [0, 1, 2, 3, 4]

    The order of permutation of 0,1,2,3 is [0,1,2,3], [0,1,3,2], [0,2,1,3],
    [0,2,3,1], [0,3,1,2], [0,3,2,1], [1,0,2,3], [1,0,3,2], [1,2,0,3],
    [1,2,3,0], [1,3,0,2]
    >>> kth_permutation(10,4)
    [1, 3, 0, 2]
    """

    # Factorails from 1! to (n-1)!
    factorials = [1]
    for i in range(2, n):
        factorials.append(factorials[-1] * i)
    assert 0 <= k < factorials[-1] * n, "k out of bounds"

    permutation = []
    elements = list(range(n))

    # Find permutation
    while factorials:
        factorial = factorials.pop()
        number, k = divmod(k, factorial)
        permutation.append(elements[number])
        elements.remove(elements[number])
    permutation.append(elements[0])

    return permutation


if __name__ == "__main__":
    import doctest

    doctest.testmod()

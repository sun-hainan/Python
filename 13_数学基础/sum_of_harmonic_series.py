# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / sum_of_harmonic_series

本文件实现 sum_of_harmonic_series 相关的算法功能。
"""

# =============================================================================
# 算法模块：sum_of_harmonic_progression
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def sum_of_harmonic_progression(
    # sum_of_harmonic_progression function

    # sum_of_harmonic_progression function
    first_term: float, common_difference: float, number_of_terms: int
) -> float:
    """
    https://en.wikipedia.org/wiki/Harmonic_progression_(mathematics)

    Find the sum of n terms in an harmonic progression.  The calculation starts with the
    first_term and loops adding the common difference of Arithmetic Progression by which
    the given Harmonic Progression is linked.

    >>> sum_of_harmonic_progression(1 / 2, 2, 2)
    0.75
    >>> sum_of_harmonic_progression(1 / 5, 5, 5)
    0.45666666666666667
    """

    arithmetic_progression = [1 / first_term]
    first_term = 1 / first_term
    for _ in range(number_of_terms - 1):
        first_term += common_difference
        arithmetic_progression.append(first_term)
    harmonic_series = [1 / step for step in arithmetic_progression]
    return sum(harmonic_series)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(sum_of_harmonic_progression(1 / 2, 2, 2))

# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / quadratic_equations_complex_numbers



本文件实现 quadratic_equations_complex_numbers 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









from cmath import sqrt







# =============================================================================

# 算法模块：quadratic_roots

# =============================================================================

def quadratic_roots(a: int, b: int, c: int) -> tuple[complex, complex]:

    # quadratic_roots function



    # quadratic_roots function

    """

    Given the numerical coefficients a, b and c,

    calculates the roots for any quadratic equation of the form ax^2 + bx + c



    >>> quadratic_roots(a=1, b=3, c=-4)

    (1.0, -4.0)

    >>> quadratic_roots(5, 6, 1)

    (-0.2, -1.0)

    >>> quadratic_roots(1, -6, 25)

    ((3+4j), (3-4j))

    """





    if a == 0:

        raise ValueError("Coefficient 'a' must not be zero.")

    delta = b * b - 4 * a * c



    root_1 = (-b + sqrt(delta)) / (2 * a)

    root_2 = (-b - sqrt(delta)) / (2 * a)



    return (

        root_1.real if not root_1.imag else root_1,

        root_2.real if not root_2.imag else root_2,

    )





def main():

    # main function



    # main function

    solution1, solution2 = quadratic_roots(a=5, b=6, c=1)

    print(f"The solutions are: {solution1} and {solution2}")





if __name__ == "__main__":

    main()


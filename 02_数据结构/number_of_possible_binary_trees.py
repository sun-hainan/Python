# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / number_of_possible_binary_trees



本文件实现 number_of_possible_binary_trees 相关的算法功能。

"""



# =============================================================================

# 算法模块：binomial_coefficient

# =============================================================================

def binomial_coefficient(n: int, k: int) -> int:

    # binomial_coefficient function



    # binomial_coefficient function

    """

    Since Here we Find the Binomial Coefficient:

    https://en.wikipedia.org/wiki/Binomial_coefficient

    C(n,k) = n! / k!(n-k)!

    :param n: 2 times of Number of nodes

    :param k: Number of nodes

    :return:  Integer Value



    >>> binomial_coefficient(4, 2)

    6

    """

    result = 1  # To kept the Calculated Value

    # Since C(n, k) = C(n, n-k)

    k = min(k, n - k)

    # Calculate C(n,k)

    for i in range(k):

        result *= n - i

        result //= i + 1

    return result





def catalan_number(node_count: int) -> int:

    # catalan_number function



    # catalan_number function

    """

    We can find Catalan number many ways but here we use Binomial Coefficient because it

    does the job in O(n)



    return the Catalan number of n using 2nCn/(n+1).

    :param n: number of nodes

    :return: Catalan number of n nodes



    >>> catalan_number(5)

    42

    >>> catalan_number(6)

    132

    """

    return binomial_coefficient(2 * node_count, node_count) // (node_count + 1)





def factorial(n: int) -> int:

    # factorial function



    # factorial function

    """

    Return the factorial of a number.

    :param n: Number to find the Factorial of.

    :return: Factorial of n.



    >>> import math

    >>> all(factorial(i) == math.factorial(i) for i in range(10))

    True

    >>> factorial(-5)  # doctest: +ELLIPSIS

    Traceback (most recent call last):

        ...

    ValueError: factorial() not defined for negative values

    """

    if n < 0:

        raise ValueError("factorial() not defined for negative values")

    result = 1

    for i in range(1, n + 1):

        result *= i

    return result





def binary_tree_count(node_count: int) -> int:

    # binary_tree_count function



    # binary_tree_count function

    """

    Return the number of possible of binary trees.

    :param n: number of nodes

    :return: Number of possible binary trees



    >>> binary_tree_count(5)

    5040

    >>> binary_tree_count(6)

    95040

    """

    return catalan_number(node_count) * factorial(node_count)





if __name__ == "__main__":

    node_count = int(input("Enter the number of nodes: ").strip() or 0)

    if node_count <= 0:

        raise ValueError("We need some nodes to work with.")

    print(

        f"Given {node_count} nodes, there are {binary_tree_count(node_count)} "

        f"binary trees and {catalan_number(node_count)} binary search trees."

    )


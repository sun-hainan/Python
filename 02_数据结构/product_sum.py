# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / product_sum



本文件实现 product_sum 相关的算法功能。

"""



# =============================================================================

# 算法模块：product_sum

# =============================================================================

def product_sum(arr: list[int | list], depth: int) -> int:

    # product_sum function



    # product_sum function

    """

    Recursively calculates the product sum of an array.



    The product sum of an array is defined as the sum of its elements multiplied by

    their respective depths.  If an element is a list, its product sum is calculated

    recursively by multiplying the sum of its elements with its depth plus one.



    Args:

        arr: The array of integers and nested lists.

        depth: The current depth level.



    Returns:

        int: The product sum of the array.



    Examples:

        >>> product_sum([1, 2, 3], 1)

        6

        >>> product_sum([-1, 2, [-3, 4]], 2)

        8

        >>> product_sum([1, 2, 3], -1)

        -6

        >>> product_sum([1, 2, 3], 0)

        0

        >>> product_sum([1, 2, 3], 7)

        42

        >>> product_sum((1, 2, 3), 7)

        42

        >>> product_sum({1, 2, 3}, 7)

        42

        >>> product_sum([1, -1], 1)

        0

        >>> product_sum([1, -2], 1)

        -1

        >>> product_sum([-3.5, [1, [0.5]]], 1)

        1.5



    """

    total_sum = 0

    for ele in arr:

        total_sum += product_sum(ele, depth + 1) if isinstance(ele, list) else ele

    return total_sum * depth





def product_sum_array(array: list[int | list]) -> int:

    # product_sum_array function



    # product_sum_array function

    """

    Calculates the product sum of an array.



    Args:

        array (List[Union[int, List]]): The array of integers and nested lists.



    Returns:

        int: The product sum of the array.



    Examples:

        >>> product_sum_array([1, 2, 3])

        6

        >>> product_sum_array([1, [2, 3]])

        11

        >>> product_sum_array([1, [2, [3, 4]]])

        47

        >>> product_sum_array([0])

        0

        >>> product_sum_array([-3.5, [1, [0.5]]])

        1.5

        >>> product_sum_array([1, -2])

        -1



    """

    return product_sum(array, 1)





if __name__ == "__main__":

    import doctest



    doctest.testmod()


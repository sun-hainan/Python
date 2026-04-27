# -*- coding: utf-8 -*-

"""

算法实现：arrays / equilibrium_index_in_array



本文件实现 equilibrium_index_in_array 相关的算法功能。

"""



# =============================================================================

# 算法模块：equilibrium_index

# =============================================================================

def equilibrium_index(arr: list[int]) -> int:

    # equilibrium_index function



    # equilibrium_index function

    """

    Find the equilibrium index of an array.



    Args:

        arr (list[int]): The input array of integers.



    Returns:

        int: The equilibrium index or -1 if no equilibrium index exists.



    Examples:

        >>> equilibrium_index([-7, 1, 5, 2, -4, 3, 0])

        3

        >>> equilibrium_index([1, 2, 3, 4, 5])

        -1

        >>> equilibrium_index([1, 1, 1, 1, 1])

        2

        >>> equilibrium_index([2, 4, 6, 8, 10, 3])

        -1

    """

    total_sum = sum(arr)

    left_sum = 0



    for i, value in enumerate(arr):

        total_sum -= value

        if left_sum == total_sum:

            return i

        left_sum += value



    return -1





if __name__ == "__main__":

    import doctest



    doctest.testmod()


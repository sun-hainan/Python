# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / triangular_numbers



本文件实现 triangular_numbers 相关的算法功能。

"""



# =============================================================================

# 算法模块：triangular_number

# =============================================================================

def triangular_number(position: int) -> int:

    # triangular_number function



    # triangular_number function

    """

    Generate the triangular number at the specified position.



    Args:

        position (int): The position of the triangular number to generate.



    Returns:

        int: The triangular number at the specified position.



    Raises:

        ValueError: If `position` is negative.



    Examples:

    >>> triangular_number(1)

    1

    >>> triangular_number(3)

    6

    >>> triangular_number(-1)

    Traceback (most recent call last):

        ...

    ValueError: param `position` must be non-negative

    """

    if position < 0:

        raise ValueError("param `position` must be non-negative")



    return position * (position + 1) // 2





if __name__ == "__main__":

    import doctest



    doctest.testmod()


# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / base_neg2_conversion



本文件实现 base_neg2_conversion 相关的算法功能。

"""



# =============================================================================

# 算法模块：decimal_to_negative_base_2

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def decimal_to_negative_base_2(num: int) -> int:

    # decimal_to_negative_base_2 function



    # decimal_to_negative_base_2 function

    """

    This function returns the number negative base 2

        of the decimal number of the input data.



    Args:

        int: The decimal number to convert.



    Returns:

        int: The negative base 2 number.



    Examples:

        >>> decimal_to_negative_base_2(0)

        0

        >>> decimal_to_negative_base_2(-19)

        111101

        >>> decimal_to_negative_base_2(4)

        100

        >>> decimal_to_negative_base_2(7)

        11011

    """



    if num == 0:

        return 0

    ans = ""

    while num != 0:

        num, rem = divmod(num, -2)

        if rem < 0:

            rem += 2

            num += 1

        ans = str(rem) + ans

    return int(ans)





if __name__ == "__main__":

    import doctest



    doctest.testmod()


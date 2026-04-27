# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / iterating_through_submasks



本文件实现 iterating_through_submasks 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""









def list_of_submasks(mask: int) -> list[int]:

    # list_of_submasks function



    # list_of_submasks function

    # list_of_submasks 函数实现

    """

    Args:

        mask : number which shows mask ( always integer > 0, zero does not have any

            submasks )



    Returns:

        all_submasks : the list of submasks of mask (mask s is called submask of mask

        m if only bits that were included in original mask are set



    Raises:

        AssertionError: mask not positive integer



    >>> list_of_submasks(15)

    [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    >>> list_of_submasks(13)

    [13, 12, 9, 8, 5, 4, 1]

    >>> list_of_submasks(-7)  # doctest: +ELLIPSIS

    Traceback (most recent call last):

        ...

    AssertionError: mask needs to be positive integer, your input -7

    >>> list_of_submasks(0)  # doctest: +ELLIPSIS

    Traceback (most recent call last):

        ...

    AssertionError: mask needs to be positive integer, your input 0



    """



    assert isinstance(mask, int) and mask > 0, (

        f"mask needs to be positive integer, your input {mask}"

    )



    """

    first submask iterated will be mask itself then operation will be performed

    to get other submasks till we reach empty submask that is zero ( zero is not

    included in final submasks list )

    """

    all_submasks = []

    submask = mask



    while submask:

        all_submasks.append(submask)

        submask = (submask - 1) & mask



    return all_submasks





if __name__ == "__main__":

    import doctest



    doctest.testmod()


# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / ceil



本文件实现 ceil 相关的算法功能。

"""



# =============================================================================

# 算法模块：ceil

# =============================================================================

def ceil(x: float) -> int:

    # ceil function



    # ceil function

    """

    Return the ceiling of x as an Integral.



    :param x: the number

    :return: the smallest integer >= x.



    >>> import math

    >>> all(ceil(n) == math.ceil(n) for n

    ...     in (1, -1, 0, -0, 1.1, -1.1, 1.0, -1.0, 1_000_000_000))

    True

    """

    return int(x) if x - int(x) <= 0 else int(x) + 1





if __name__ == "__main__":

    import doctest



    doctest.testmod()


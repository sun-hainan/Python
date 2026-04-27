# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / floor

本文件实现 floor 相关的算法功能。
"""

# =============================================================================
# 算法模块：floor
# =============================================================================
def floor(x: float) -> int:
    # floor function

    # floor function
    """
    Return the floor of x as an Integral.
    :param x: the number
    :return: the largest integer <= x.
    >>> import math
    >>> all(floor(n) == math.floor(n) for n
    ...     in (1, -1, 0, -0, 1.1, -1.1, 1.0, -1.0, 1_000_000_000))
    True
    """
    return int(x) if x - int(x) >= 0 else int(x) - 1


if __name__ == "__main__":
    import doctest

    doctest.testmod()

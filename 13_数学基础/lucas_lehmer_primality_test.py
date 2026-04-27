# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / lucas_lehmer_primality_test



本文件实现 lucas_lehmer_primality_test 相关的算法功能。

"""



# Primality test 2^p - 1

# Return true if 2^p - 1 is prime



# =============================================================================

# 算法模块：lucas_lehmer_test

# =============================================================================

def lucas_lehmer_test(p: int) -> bool:

    """

    >>> lucas_lehmer_test(p=7)

    True



    >>> lucas_lehmer_test(p=11)

    False



    # M_11 = 2^11 - 1 = 2047 = 23 * 89

    """



    if p < 2:

        raise ValueError("p should not be less than 2!")

    elif p == 2:

        return True



    s = 4

    m = (1 << p) - 1

    for _ in range(p - 2):

        s = ((s * s) - 2) % m

    return s == 0





if __name__ == "__main__":

    print(lucas_lehmer_test(7))

    print(lucas_lehmer_test(11))


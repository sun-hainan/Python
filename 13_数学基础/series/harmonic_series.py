# -*- coding: utf-8 -*-

"""

算法实现：series / harmonic_series



本文件实现 harmonic_series 相关的算法功能。

"""



# =============================================================================

# 算法模块：harmonic_series

# =============================================================================

def harmonic_series(n_term: str) -> list:

    # harmonic_series function



    # harmonic_series function

    """Pure Python implementation of Harmonic Series algorithm



    :param n_term: The last (nth) term of Harmonic Series

    :return: The Harmonic Series starting from 1 to last (nth) term



    Examples:

    >>> harmonic_series(5)

    ['1', '1/2', '1/3', '1/4', '1/5']

    >>> harmonic_series(5.0)

    ['1', '1/2', '1/3', '1/4', '1/5']

    >>> harmonic_series(5.1)

    ['1', '1/2', '1/3', '1/4', '1/5']

    >>> harmonic_series(-5)

    []

    >>> harmonic_series(0)

    []

    >>> harmonic_series(1)

    ['1']

    """

    if n_term == "":

        return []

    series: list = []

    for temp in range(int(n_term)):

        series.append(f"1/{temp + 1}" if series else "1")

    return series





if __name__ == "__main__":

    nth_term = input("Enter the last number (nth term) of the Harmonic Series")

    print("Formula of Harmonic Series => 1+1/2+1/3 ..... 1/n")

    print(harmonic_series(nth_term))


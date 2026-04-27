# -*- coding: utf-8 -*-

"""

算法实现：07_贪心与分治 / fractional_knapsack



本文件实现 fractional_knapsack 相关的算法功能。

"""



from bisect import bisect

from itertools import accumulate





# frac_knapsack 算法

def frac_knapsack(vl, wt, w, n):

    """

    >>> frac_knapsack([60, 100, 120], [10, 20, 30], 50, 3)

    240.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 10, 4)

    105.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 8, 4)

    95.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6], 8, 4)

    60.0

    >>> frac_knapsack([10, 40, 30], [5, 4, 6, 3], 8, 4)

    60.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 0, 4)

    0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 8, 0)

    95.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], -8, 4)

    0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 8, -4)

    95.0

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 800, 4)

    130

    >>> frac_knapsack([10, 40, 30, 50], [5, 4, 6, 3], 8, 400)

    95.0

    >>> frac_knapsack("ABCD", [5, 4, 6, 3], 8, 400)

    Traceback (most recent call last):

        ...

    TypeError: unsupported operand type(s) for /: 'str' and 'int'

    """



    r = sorted(zip(vl, wt), key=lambda x: x[0] / x[1], reverse=True)

    vl, wt = [i[0] for i in r], [i[1] for i in r]

    acc = list(accumulate(wt))

    k = bisect(acc, w)

    return (

        0

        if k == 0

        else sum(vl[:k]) + (w - acc[k - 1]) * (vl[k]) / (wt[k])

        if k != n

        else sum(vl[:k])

    )





if __name__ == "__main__":

    import doctest



    doctest.testmod()


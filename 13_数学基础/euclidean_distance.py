# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / euclidean_distance



本文件实现 euclidean_distance 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









import typing

from collections.abc import Iterable



import numpy as np



Vector = typing.Union[Iterable[float], Iterable[int], np.ndarray]  # noqa: UP007

VectorOut = typing.Union[np.float64, int, float]  # noqa: UP007







# =============================================================================

# 算法模块：euclidean_distance

# =============================================================================

def euclidean_distance(vector_1: Vector, vector_2: Vector) -> VectorOut:

    # euclidean_distance function



    # euclidean_distance function

    """

    Calculate the distance between the two endpoints of two vectors.

    A vector is defined as a list, tuple, or numpy 1D array.

    >>> float(euclidean_distance((0, 0), (2, 2)))

    2.8284271247461903

    >>> float(euclidean_distance(np.array([0, 0, 0]), np.array([2, 2, 2])))

    3.4641016151377544

    >>> float(euclidean_distance(np.array([1, 2, 3, 4]), np.array([5, 6, 7, 8])))

    8.0

    >>> float(euclidean_distance([1, 2, 3, 4], [5, 6, 7, 8]))

    8.0

    """



    return np.sqrt(np.sum((np.asarray(vector_1) - np.asarray(vector_2)) ** 2))





def euclidean_distance_no_np(vector_1: Vector, vector_2: Vector) -> VectorOut:

    # euclidean_distance_no_np function



    # euclidean_distance_no_np function

    """

    Calculate the distance between the two endpoints of two vectors without numpy.

    A vector is defined as a list, tuple, or numpy 1D array.

    >>> euclidean_distance_no_np((0, 0), (2, 2))

    2.8284271247461903

    >>> euclidean_distance_no_np([1, 2, 3, 4], [5, 6, 7, 8])

    8.0

    """

    return sum((v1 - v2) ** 2 for v1, v2 in zip(vector_1, vector_2)) ** (1 / 2)





if __name__ == "__main__":



    def benchmark() -> None:

    # benchmark function



    # benchmark function

        """

        Benchmarks

        """

        from timeit import timeit



        print("Without Numpy")

        print(

            timeit(

                "euclidean_distance_no_np([1, 2, 3], [4, 5, 6])",

                number=10000,

                globals=globals(),

            )

        )

        print("With Numpy")

        print(

            timeit(

                "euclidean_distance([1, 2, 3], [4, 5, 6])",

                number=10000,

                globals=globals(),

            )

        )



    benchmark()


# -*- coding: utf-8 -*-

"""

算法实现：arrays / index_2d_array_in_1d



本文件实现 index_2d_array_in_1d 相关的算法功能。

"""



from collections.abc import Iterator

from dataclasses import dataclass





@dataclass



# =============================================================================

# 算法模块：index_2d_array_in_1d

# =============================================================================

class Index2DArrayIterator:

    # Index2DArrayIterator class



    # Index2DArrayIterator class

    matrix: list[list[int]]



    def __iter__(self) -> Iterator[int]:

    # __iter__ function



    # __iter__ function

        """

        >>> tuple(Index2DArrayIterator([[5], [-523], [-1], [34], [0]]))

        (5, -523, -1, 34, 0)

        >>> tuple(Index2DArrayIterator([[5, -523, -1], [34, 0]]))

        (5, -523, -1, 34, 0)

        >>> tuple(Index2DArrayIterator([[5, -523, -1, 34, 0]]))

        (5, -523, -1, 34, 0)

        >>> t = Index2DArrayIterator([[5, 2, 25], [23, 14, 5], [324, -1, 0]])

        >>> tuple(t)

        (5, 2, 25, 23, 14, 5, 324, -1, 0)

        >>> list(t)

        [5, 2, 25, 23, 14, 5, 324, -1, 0]

        >>> sorted(t)

        [-1, 0, 2, 5, 5, 14, 23, 25, 324]

        >>> tuple(t)[3]

        23

        >>> sum(t)

        397

        >>> -1 in t

        True

        >>> t = iter(Index2DArrayIterator([[5], [-523], [-1], [34], [0]]))

        >>> next(t)

        5

        >>> next(t)

        -523

        """

        for row in self.matrix:

            yield from row





def index_2d_array_in_1d(array: list[list[int]], index: int) -> int:

    # index_2d_array_in_1d function



    # index_2d_array_in_1d function

    """

    Retrieves the value of the one-dimensional index from a two-dimensional array.



    Args:

        array: A 2D array of integers where all rows are the same size and all

               columns are the same size.

        index: A 1D index.



    Returns:

        int: The 0-indexed value of the 1D index in the array.



    Examples:

    >>> index_2d_array_in_1d([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], 5)

    5

    >>> index_2d_array_in_1d([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], -1)

    Traceback (most recent call last):

        ...

    ValueError: index out of range

    >>> index_2d_array_in_1d([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], 12)

    Traceback (most recent call last):

        ...

    ValueError: index out of range

    >>> index_2d_array_in_1d([[]], 0)

    Traceback (most recent call last):

        ...

    ValueError: no items in array

    """

    rows = len(array)

    cols = len(array[0])



    if rows == 0 or cols == 0:

        raise ValueError("no items in array")



    if index < 0 or index >= rows * cols:

        raise ValueError("index out of range")



    return array[index // cols][index % cols]





if __name__ == "__main__":

    import doctest



    doctest.testmod()


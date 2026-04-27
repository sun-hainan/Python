# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / hamming_distance



本文件实现 hamming_distance 相关的算法功能。

"""



def hamming_distance(string1: str, string2: str) -> int:

    # hamming_distance function



    # hamming_distance function

    # hamming_distance 函数实现

    """Calculate the Hamming distance between two equal length strings

    In information theory, the Hamming distance between two strings of equal

    length is the number of positions at which the corresponding symbols are

    different. https://en.wikipedia.org/wiki/Hamming_distance



    Args:

        string1 (str): Sequence 1

        string2 (str): Sequence 2



    Returns:

        int: Hamming distance



    >>> hamming_distance("python", "python")

    0

    >>> hamming_distance("karolin", "kathrin")

    3

    >>> hamming_distance("00000", "11111")

    5

    >>> hamming_distance("karolin", "kath")

    Traceback (most recent call last):

      ...

    ValueError: String lengths must match!

    """

    if len(string1) != len(string2):

        raise ValueError("String lengths must match!")



    count = 0



    for char1, char2 in zip(string1, string2):

        if char1 != char2:

            count += 1



    return count





if __name__ == "__main__":

    import doctest



    doctest.testmod()


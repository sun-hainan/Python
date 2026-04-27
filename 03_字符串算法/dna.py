# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / dna



本文件实现 dna 相关的算法功能。

"""



import re





def dna(dna: str) -> str:

    # dna function



    # dna function

    # dna 函数实现

    """

    https://en.wikipedia.org/wiki/DNA

    Returns the second side of a DNA strand



    >>> dna("GCTA")

    'CGAT'

    >>> dna("ATGC")

    'TACG'

    >>> dna("CTGA")

    'GACT'

    >>> dna("GFGG")

    Traceback (most recent call last):

        ...

    ValueError: Invalid Strand

    """



    if len(re.findall("[ATCG]", dna)) != len(dna):

        raise ValueError("Invalid Strand")



    return dna.translate(dna.maketrans("ATCG", "TAGC"))





if __name__ == "__main__":

    import doctest



    doctest.testmod()


# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / h_index



本文件实现 h_index 相关的算法功能。

"""



# h_index 函数实现

def h_index(citations: list[int]) -> int:

    """

    Return H-index of citations



    >>> h_index([3, 0, 6, 1, 5])

    3

    >>> h_index([1, 3, 1])

    1

    >>> h_index([1, 2, 3])

    2

    >>> h_index('test')

    Traceback (most recent call last):

        ...

    ValueError: The citations should be a list of non negative integers.

    >>> h_index([1,2,'3'])

    Traceback (most recent call last):

        ...

    ValueError: The citations should be a list of non negative integers.

    >>> h_index([1,2,-3])

    Traceback (most recent call last):

        ...

    ValueError: The citations should be a list of non negative integers.

    """



    # validate:

    if not isinstance(citations, list) or not all(

        isinstance(item, int) and item >= 0 for item in citations

    ):

        raise ValueError("The citations should be a list of non negative integers.")



    citations.sort()

    len_citations = len(citations)



    for i in range(len_citations):

    # 遍历循环

        if citations[len_citations - 1 - i] <= i:

    # 条件判断

            return i

    # 返回结果



    return len_citations

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()


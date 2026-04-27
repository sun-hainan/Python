# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / stalin_sort



本文件实现 stalin_sort 相关的算法功能。

"""



# stalin_sort 函数实现

def stalin_sort(sequence: list[int]) -> list[int]:

    """

    Sorts a list using the Stalin sort algorithm.



    >>> stalin_sort([4, 3, 5, 2, 1, 7])

    [4, 5, 7]



    >>> stalin_sort([1, 2, 3, 4])

    [1, 2, 3, 4]



    >>> stalin_sort([4, 5, 5, 2, 3])

    [4, 5, 5]



    >>> stalin_sort([6, 11, 12, 4, 1, 5])

    [6, 11, 12]



    >>> stalin_sort([5, 0, 4, 3])

    [5]



    >>> stalin_sort([5, 4, 3, 2, 1])

    [5]



    >>> stalin_sort([1, 2, 3, 4, 5])

    [1, 2, 3, 4, 5]



    >>> stalin_sort([1, 2, 8, 7, 6])

    [1, 2, 8]

    """

    result = [sequence[0]]

    for element in sequence[1:]:

    # 遍历循环

        if element >= result[-1]:

    # 条件判断

            result.append(element)



    return result

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()


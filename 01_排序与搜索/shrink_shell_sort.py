# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / shrink_shell_sort



本文件实现 shrink_shell_sort 相关的算法功能。

"""



# shell_sort 函数实现

def shell_sort(collection: list) -> list:

    """Implementation of shell sort algorithm in Python

    :param collection:  Some mutable ordered collection with heterogeneous

    comparable items inside

    :return:  the same collection ordered by ascending



    >>> shell_sort([3, 2, 1])

    [1, 2, 3]

    >>> shell_sort([])

    []

    >>> shell_sort([1])

    [1]

    """



    # Choose an initial gap value

    gap = len(collection)



    # Set the gap value to be decreased by a factor of 1.3

    # after each iteration

    shrink = 1.3



    # Continue sorting until the gap is 1

    while gap > 1:

    # 条件循环

        # Decrease the gap value

        gap = int(gap / shrink)



        # Sort the elements using insertion sort

        for i in range(gap, len(collection)):

    # 遍历循环

            temp = collection[i]

            j = i

            while j >= gap and collection[j - gap] > temp:

    # 条件循环

                collection[j] = collection[j - gap]

                j -= gap

            collection[j] = temp



    return collection

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()


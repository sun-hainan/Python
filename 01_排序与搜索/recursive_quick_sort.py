# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / recursive_quick_sort



本文件实现 recursive_quick_sort 相关的算法功能。

"""



# quick_sort 函数实现

def quick_sort(data: list) -> list:

    """

    >>> for data in ([2, 1, 0], [2.2, 1.1, 0], "quick_sort"):

    ...     quick_sort(data) == sorted(data)

    True

    True

    True

    """

    if len(data) <= 1:

    # 条件判断

        return data

    # 返回结果

    else:

        return [

    # 返回结果

            *quick_sort([e for e in data[1:] if e <= data[0]]),

            data[0],

            *quick_sort([e for e in data[1:] if e > data[0]]),

        ]





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()


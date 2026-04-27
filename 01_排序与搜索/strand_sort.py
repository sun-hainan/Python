# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / strand_sort

本文件实现 strand_sort 相关的算法功能。
"""

import operator



# strand_sort 函数实现
def strand_sort(arr: list, reverse: bool = False, solution: list | None = None) -> list:
    """
    Strand sort implementation
    source: https://en.wikipedia.org/wiki/Strand_sort

    :param arr: Unordered input list
    :param reverse: Descent ordering flag
    :param solution: Ordered items container

    Examples:
    >>> strand_sort([4, 2, 5, 3, 0, 1])
    [0, 1, 2, 3, 4, 5]

    >>> strand_sort([4, 2, 5, 3, 0, 1], reverse=True)
    [5, 4, 3, 2, 1, 0]
    """
    _operator = operator.lt if reverse else operator.gt
    solution = solution or []

    if not arr:
    # 条件判断
        return solution
    # 返回结果

    sublist = [arr.pop(0)]
    for i, item in enumerate(arr):
    # 遍历循环
        if _operator(item, sublist[-1]):
    # 条件判断
            sublist.append(item)
            arr.pop(i)

    #  merging sublist into solution list
    if not solution:
    # 条件判断
        solution.extend(sublist)
    else:
        while sublist:
    # 条件循环
            item = sublist.pop(0)
            for i, xx in enumerate(solution):
    # 遍历循环
                if not _operator(item, xx):
    # 条件判断
                    solution.insert(i, item)
                    break
            else:
                solution.append(item)

    strand_sort(arr, reverse, solution)
    return solution
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    assert strand_sort([4, 3, 5, 1, 2]) == [1, 2, 3, 4, 5]
    assert strand_sort([4, 3, 5, 1, 2], reverse=True) == [5, 4, 3, 2, 1]

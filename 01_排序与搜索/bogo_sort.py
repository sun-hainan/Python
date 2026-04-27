# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / bogo_sort



本文件实现 bogo_sort 相关的算法功能。

"""



import random







# bogo_sort 函数实现

def bogo_sort(collection: list) -> list:

    """Pure implementation of the bogosort algorithm in Python

    :param collection: some mutable ordered collection with heterogeneous

    comparable items inside

    :return: the same collection ordered by ascending

    Examples:

    >>> bogo_sort([0, 5, 3, 2, 2])

    [0, 2, 2, 3, 5]

    >>> bogo_sort([])

    []

    >>> bogo_sort([-2, -5, -45])

    [-45, -5, -2]

    """





# is_sorted 函数实现

    def is_sorted(collection: list) -> bool:

        for i in range(len(collection) - 1):

    # 遍历循环

            if collection[i] > collection[i + 1]:

    # 条件判断

                return False

    # 返回结果

        return True

    # 返回结果



    while not is_sorted(collection):

    # 条件循环

        random.shuffle(collection)

    return collection

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    user_input = input("Enter numbers separated by a comma:\n").strip()

    unsorted = [int(item) for item in user_input.split(",")]

    print(bogo_sort(unsorted))


# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / gnome_sort



本文件实现 gnome_sort 相关的算法功能。

"""



# gnome_sort 函数实现

def gnome_sort(lst: list) -> list:

    """

    Pure implementation of the gnome sort algorithm in Python



    Take some mutable ordered collection with heterogeneous comparable items inside as

    arguments, return the same collection ordered by ascending.



    Examples:

    >>> gnome_sort([0, 5, 3, 2, 2])

    [0, 2, 2, 3, 5]



    >>> gnome_sort([])

    []



    >>> gnome_sort([-2, -5, -45])

    [-45, -5, -2]



    >>> "".join(gnome_sort(list(set("Gnomes are stupid!"))))

    ' !Gadeimnoprstu'

    """

    if len(lst) <= 1:

    # 条件判断

        return lst

    # 返回结果



    i = 1



    while i < len(lst):

    # 条件循环

        if lst[i - 1] <= lst[i]:

    # 条件判断

            i += 1

        else:

            lst[i - 1], lst[i] = lst[i], lst[i - 1]

            i -= 1

            if i == 0:

    # 条件判断

                i = 1



    return lst

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    user_input = input("Enter numbers separated by a comma:\n").strip()

    unsorted = [int(item) for item in user_input.split(",")]

    print(gnome_sort(unsorted))


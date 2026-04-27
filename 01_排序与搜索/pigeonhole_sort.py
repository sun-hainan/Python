# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / pigeonhole_sort



本文件实现 pigeonhole_sort 相关的算法功能。

"""



# Python program to implement Pigeonhole Sorting in python



# Algorithm for the pigeonhole sorting







# pigeonhole_sort 函数实现

def pigeonhole_sort(a):

    """

    >>> a = [8, 3, 2, 7, 4, 6, 8]

    >>> b = sorted(a)  # a nondestructive sort

    >>> pigeonhole_sort(a)  # a destructive sort

    >>> a == b

    True



    >>> pigeonhole_sort([])

    """

    if not a:

    # 条件判断

        return

    # size of range of values in the list (ie, number of pigeonholes we need)



    min_val = min(a)  # min() finds the minimum value

    max_val = max(a)  # max() finds the maximum value



    size = max_val - min_val + 1  # size is difference of max and min values plus one



    # list of pigeonholes of size equal to the variable size

    holes = [0] * size



    # Populate the pigeonholes.

    for x in a:

    # 遍历循环

        assert isinstance(x, int), "integers only please"

        holes[x - min_val] += 1



    # Putting the elements back into the array in an order.

    i = 0

    for count in range(size):

    # 遍历循环

        while holes[count] > 0:

    # 条件循环

            holes[count] -= 1

            a[i] = count + min_val

            i += 1







# main 函数实现

def main():

    a = [8, 3, 2, 7, 4, 6, 8]

    pigeonhole_sort(a)

    print("Sorted order is:", *a)





if __name__ == "__main__":

    # 条件判断

    main()


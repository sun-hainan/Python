# -*- coding: utf-8 -*-

"""

算法实现：Sorting / 02_Quick_Sort



本文件实现 02_Quick_Sort 相关的算法功能。

"""



def quick_sort(arr):

    """

    快速排序

    

    Args:

        arr: 待排序列表

        

    Returns:

        排序后的新列表

    """

    if len(arr) <= 1:

        return arr

    mid = len(arr) // 2

    pivot = arr[mid]

    less = []

    greater = []

    for item in arr:

        if item == arr[mid]:

            continue

        if item <= pivot:

            less.append(item)

        else:

            greater.append(item)

    return quick_sort(less) + [pivot] + quick_sort(greater)





if __name__ == "__main__":

    # 测试: quick_sort

    result = quick_sort()

    print(result)


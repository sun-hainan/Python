# -*- coding: utf-8 -*-

"""

算法实现：Sorting / 04_Insertion_Sort



本文件实现 04_Insertion_Sort 相关的算法功能。

"""



def insertion_sort(arr):

    """

    插入排序

    """

    for i in range(1, len(arr)):

        key = arr[i]

        j = i - 1

        while j >= 0 and arr[j] > key:

            arr[j + 1] = arr[j]

            j -= 1

        arr[j + 1] = key

    return arr





if __name__ == "__main__":

    # 测试: insertion_sort

    result = insertion_sort()

    print(result)


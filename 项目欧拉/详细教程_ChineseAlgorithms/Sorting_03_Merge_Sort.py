# -*- coding: utf-8 -*-

"""

算法实现：Sorting / 03_Merge_Sort



本文件实现 03_Merge_Sort 相关的算法功能。

"""



def merge_sort(arr):

    """

    归并排序

    

    Args:

        arr: 待排序列表

        

    Returns:

        排序后的新列表

    """

    if len(arr) <= 1:

        return arr

    mid = len(arr) // 2

    left = merge_sort(arr[:mid])

    right = merge_sort(arr[mid:])

    return merge(left, right)



def merge(left, right):

    """

    合并两个有序数组

    """

    result = []

    i = j = 0

    while i < len(left) and j < len(right):

        if left[i] <= right[j]:

            result.append(left[i])

            i += 1

        else:

            result.append(right[j])

            j += 1

    result.extend(left[i:])

    result.extend(right[j:])

    return result





if __name__ == "__main__":

    # 测试: merge

    result = merge()

    print(result)


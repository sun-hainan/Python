# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 07_Shell_Sort

本文件实现 07_Shell_Sort 相关的算法功能。
"""

def shell_sort(arr):
    """
    希尔排序
    """
    n = len(arr)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
    return arr


if __name__ == "__main__":
    # 测试: shell_sort
    result = shell_sort()
    print(result)

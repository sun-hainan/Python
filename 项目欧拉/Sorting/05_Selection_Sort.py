# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 05_Selection_Sort

本文件实现 05_Selection_Sort 相关的算法功能。
"""

def selection_sort(arr):
    """
    选择排序
    """
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


if __name__ == "__main__":
    # 测试: selection_sort
    result = selection_sort()
    print(result)

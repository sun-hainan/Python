# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 01_Bubble_Sort

本文件实现 01_Bubble_Sort 相关的算法功能。
"""

def bubble_sort(arr):
    """
    冒泡排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
    """
    n = len(arr)
    for i in range(n - 1, 0, -1):
        for j in range(i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


if __name__ == "__main__":
    # 测试: bubble_sort
    result = bubble_sort()
    print(result)

# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 06_Heap_Sort

本文件实现 06_Heap_Sort 相关的算法功能。
"""

def heap_sort(arr):
    """
    堆排序
    """
    n = len(arr)
    def heapify(arr, n, i):
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        if left < n and arr[left] > arr[largest]:
            largest = left
        if right < n and arr[right] > arr[largest]:
            largest = right
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr


if __name__ == "__main__":
    # 测试: heapify
    result = heapify()
    print(result)

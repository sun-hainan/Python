"""
Insertion Sort - 插入排序
==========================================

【算法原理】
像整理扑克牌，将每个元素插入到左侧已排序部分的正确位置。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】稳定
【特点】适合基本有序的数据、小规模数据
"""

def insertion_sort(arr):
    """
    插入排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
    """
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

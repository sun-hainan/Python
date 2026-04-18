"""
Quick Sort - 快速排序
==========================================

【算法原理】
分治策略：
1. 选择一个基准元素(pivot)
2. 将数组分为两部分：<= pivot 和 > pivot
3. 递归排序左右两部分
4. 合并结果

【时间复杂度】O(n log n) 平均, O(n^2) 最坏
【空间复杂度】O(log n)
【稳定性】不稳定
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

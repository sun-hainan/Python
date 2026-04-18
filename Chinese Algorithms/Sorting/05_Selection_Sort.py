"""
Selection Sort - 选择排序
==========================================

【算法原理】
每轮在未排序部分找到最小元素，放到已排序部分的末尾。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】不稳定
"""

def selection_sort(arr):
    """
    选择排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
    """
    n = len(arr)
    
    for i in range(n):
        # 找到未排序部分的最小元素
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        
        # 交换到已排序部分末尾
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    
    return arr


# ---------- Heap Sort ----------
FILES['Chinese Algorithms/Sorting/06_Heap_Sort.py'] = 
Heap Sort - 堆排序
==========================================

【算法原理】
1. 构建最大堆
2. 堆顶(最大元素)与堆尾交换
3. 堆大小减1，调整堆
4. 重复直到堆大小为1

【时间复杂度】O(n log n)
【空间复杂度】O(1)
【稳定性】不稳定

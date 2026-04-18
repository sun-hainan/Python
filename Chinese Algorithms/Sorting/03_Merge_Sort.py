"""
Merge Sort - 归并排序
==========================================

【算法原理】
分治策略：
1. 将数组从中间分成两半
2. 递归地对左右两部分进行归并排序
3. 合并两个有序数组

【时间复杂度】O(n log n)
【空间复杂度】O(n)
【稳定性】稳定
【特点】适合外部排序、大数据排序
"""

def merge_sort(arr):
    """
    归并排序
    
    Args:
        arr: 待排序列表
        
    Returns:
        排序后的新列表
    """
    # 递归终止条件
    if len(arr) <= 1:
        return arr
    
    # 分割：分成两半
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # 合并两个有序数组
    return merge(left, right)


def merge(left, right):
    """
    合并两个有序数组
    
    Args:
        left: 左半部分(已排序)
        right: 右半部分(已排序)
        
    Returns:
        合并后的有序数组
    """
    result = []
    i = j = 0
    
    # 比较并合并
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # 添加剩余元素
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result


# ---------- Insertion Sort ----------
FILES['Chinese Algorithms/Sorting/04_Insertion_Sort.py'] = 
Insertion Sort - 插入排序
==========================================

【算法原理】
像整理扑克牌一样，将每个元素插入到左侧已排序部分中的正确位置。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】稳定
【特点】适合基本有序的数据、小规模数据

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

【应用场景】
- 需要稳定排序的大数据
- 外部排序（文件、数据库）
- 链表排序
- 多路归并场景

【何时使用】
- 需要稳定排序
- 数据量非常大，需要外部存储
- 链表排序（可实现O(1)空间）
- 面试/考试要求稳定排序

【实际案例】
# 银行交易记录按时间排序（需要稳定，保持相同时间的原始顺序）
transactions = [(1000, "转账"), (1500, "存款"), (1000, "缴费")]
merge_sort(transactions)  # 相同金额保持原有顺序
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
    
    Args:
        left: 左半部分(已排序)
        right: 右半部分(已排序)
        
    Returns:
        合并后的有序数组
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

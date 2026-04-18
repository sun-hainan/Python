"""
Quick Sort - 快速排序
==========================================

【算法原理】
分治策略：选择基准，分组，递归处理左右两部分。

【时间复杂度】O(n log n) 平均, O(n^2) 最坏
【空间复杂度】O(log n)
【稳定性】不稳定

【应用场景】
- 电商商品按价格/销量排序
- 数据库索引排序
- 搜索引擎结果排序
- 通用排序需求

【何时使用】
- 通用场景首选
- 数据量较大 n > 100
- 对排序稳定性无要求
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

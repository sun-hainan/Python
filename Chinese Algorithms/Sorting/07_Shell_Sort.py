"""
Shell Sort - 希尔排序
==========================================

【算法原理】
插入排序的改进版，使用增量(gap)分组进行插入排序，
最后gap=1时就是完整的插入排序。

【时间复杂度】O(n^1.3)
【空间复杂度】O(1)
【稳定性】不稳定
"""

def shell_sort(arr):
    """
    希尔排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
    """
    n = len(arr)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]  # 最佳增量序列
    
    for gap in gaps:
        # 按增量分组
        for i in range(gap, n):
            temp = arr[i]
            j = i
            
            # 组内插入排序
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            
            arr[j] = temp
    
    return arr


# ---------- Counting Sort ----------
FILES['Chinese Algorithms/Sorting/08_Counting_Sort.py'] = 
Counting Sort - 计数排序
==========================================

【算法原理】
非比较排序：
1. 统计每个元素出现的次数
2. 计算元素的位置前缀和
3. 根据位置放置元素

【时间复杂度】O(n + k)
【空间复杂度】O(n + k)
【稳定性】稳定
【限制】只适合整数、范围不宜过大

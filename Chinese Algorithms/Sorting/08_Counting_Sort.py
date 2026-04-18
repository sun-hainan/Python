"""
Counting Sort - 计数排序
==========================================

【算法原理】
非比较排序：
1. 统计每个元素出现次数
2. 计算元素位置前缀和
3. 根据位置放置元素

【时间复杂度】O(n + k)
【空间复杂度】O(n + k)
【稳定性】稳定
【限制】只适合整数
"""

def counting_sort(arr):
    """
    计数排序
    
    Args:
        arr: 待排序整数列表
        
    Returns:
        排序后的新列表
    """
    if not arr:
        return []
    
    min_val, max_val = min(arr), max(arr)
    count = [0] * (max_val - min_val + 1)
    
    for num in arr:
        count[num - min_val] += 1
    
    for i in range(1, len(count)):
        count[i] += count[i - 1]
    
    result = [0] * len(arr)
    for num in reversed(arr):
        result[count[num - min_val] - 1] = num
        count[num - min_val] -= 1
    
    return result

"""
Counting Sort - 计数排序
==========================================

【算法原理】
非比较排序：统计次数 -> 计算前缀和 -> 放置元素。

【时间复杂度】O(n + k)
【空间复杂度】O(n + k)
【稳定性】稳定

【应用场景】
- 学生考试成绩排序（0-100分）
- 高考成绩排序（0-750分）
- 员工工号排序
- 年龄排序（0-150岁）

【何时使用】
- 数据范围k不大
- 整数排序
- 需要稳定排序
"""

def counting_sort(arr):
    """
    计数排序
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

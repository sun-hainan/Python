"""
Selection Sort - 选择排序
==========================================

【算法原理】
每轮在未排序部分找到最小元素，放到已排序部分末尾。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】不稳定

【应用场景】
- 选秀节目海选排名（每轮选最高分）
- 交换成本高的数据排序
- 简单选择场景

【何时使用】
- 数据量小 n < 100
- 交换成本远高于比较成本
- 不要求稳定性
"""

def selection_sort(arr):
    """
    选择排序
    """
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

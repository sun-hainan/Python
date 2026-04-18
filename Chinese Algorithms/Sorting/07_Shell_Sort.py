"""
Shell Sort - 希尔排序
==========================================

【算法原理】
插入排序改进版，使用增量分组进行排序，最后gap=1。

【时间复杂度】O(n^1.3)
【空间复杂度】O(1)
【稳定性】不稳定

【应用场景】
- 中等规模数据排序
- 嵌入式系统
- 避免递归的排序需求

【何时使用】
- 数据量 100 < n < 10000
- 不想用递归
- 需要较稳定的退化性能
"""

def shell_sort(arr):
    """
    希尔排序
    """
    n = len(arr)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
    return arr

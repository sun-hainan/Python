"""
Heap Sort - 堆排序
==========================================

【算法原理】
1. 构建最大堆 2. 堆顶与堆尾交换 3. 调整堆 4. 重复。

【时间复杂度】O(n log n)
【空间复杂度】O(1)
【稳定性】不稳定

【应用场景】
- 游戏排行榜Top-K（显示前10名玩家）
- 医院急诊室优先队列（病情严重先处理）
- 任务调度系统（高优先级任务先执行）
- 实时流数据Top-K

【何时使用】
- 求Top-K元素
- 实现优先队列
- 需要O(1)空间排序
"""

def heap_sort(arr):
    """
    堆排序
    """
    n = len(arr)
    def heapify(arr, n, i):
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        if left < n and arr[left] > arr[largest]:
            largest = left
        if right < n and arr[right] > arr[largest]:
            largest = right
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr

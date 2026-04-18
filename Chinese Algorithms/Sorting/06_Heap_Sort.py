"""
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

【应用场景】
- Top-K 问题（求最大/最小的K个元素）
- 优先级队列
- 任务调度
- 实时排行榜

【何时使用】
- 求 Top-K 元素
- 实现优先级队列
- 需要 O(1) 空间的排序
- 面试/考试重点

【实际案例】
# 游戏排行榜 - 显示积分前10名
# 不需要全部排序，只排出前10即可
player_scores = [1200, 3500, 8900, 4200, 6700, 2300, 9800, 5400, 3100, 7800]
heap_sort(player_scores)  # 高效排序

# 实现优先队列（医院急诊排队）
# 病情严重的患者自动排到前面
"""

def heap_sort(arr):
    """
    堆排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
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

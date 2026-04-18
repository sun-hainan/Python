"""
Shell Sort - 希尔排序
==========================================

【算法原理】
插入排序的改进版，使用增量(gap)分组进行插入排序，
最后gap=1时就是完整的插入排序。

【时间复杂度】O(n^1.3)
【空间复杂度】O(1)
【稳定性】不稳定

【应用场景】
- 中等规模数据排序
- 对性能有一定要求的场景
- 嵌入式排序需求

【何时使用】
- 数据量中等 100 < n < 10000
- 不想用快速排序的递归
- 需要较稳定的退化性能
- 作为更复杂排序的子步骤

【实际案例】
# 运动会成绩排序
# 先按项目分组排序，再整体排序
records = [("100米", 12.5), ("跳远", 6.8), ("100米", 11.8), ("跳远", 7.2)]
shell_sort(records)  # 按成绩排序
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

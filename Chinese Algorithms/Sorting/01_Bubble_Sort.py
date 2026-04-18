"""
Bubble Sort - 冒泡排序
==========================================

【算法原理】
遍历数组，比较相邻元素，如果顺序错误就交换。
每轮遍历后，最大元素会"冒泡"到最后。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】稳定
"""

def bubble_sort(arr):
    """
    冒泡排序主函数
    
    Args:
        arr: 待排序列表
        
    Returns:
        排序后的列表
    """
    n = len(arr)
    
    # 外层循环：遍历所有轮次
    for i in range(n - 1, 0, -1):
        # 内层循环：比较相邻元素
        for j in range(i):
            if arr[j] > arr[j + 1]:
                # 交换位置
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr


# ---------- Quick Sort ----------
FILES['Chinese Algorithms/Sorting/02_Quick_Sort.py'] = 
Quick Sort - 快速排序
==========================================

【算法原理】
分治策略：
1. 选择一个基准元素(pivot)
2. 将数组分为两部分：<= pivot 和 > pivot
3. 递归排序左右两部分
4. 合并结果

【时间复杂度】O(n log n) 平均, O(n^2) 最坏
【空间复杂度】O(log n)
【稳定性】不稳定

"""
Selection Sort - 选择排序
==========================================

【算法原理】
每轮在未排序部分找到最小元素，放到已排序部分末尾。

【时间复杂度】O(n^2)
【空间复杂度】O(1)
【稳定性】不稳定

【应用场景】
- 简单选择场景
- 交换成本高的数据（如大型记录）
- 内存受限环境

【何时使用】
- 数据量小 n < 100
- 交换成本远高于比较成本
- 不要求稳定性
- 教学演示基础排序

【实际案例】
# 选秀节目海选排名
# 每轮选出当前最高分的选手
contestants = [
    {"name": "张三", "score": 85},
    {"name": "李四", "score": 92},
    {"name": "王五", "score": 78}
]
# 选择排序：每次选最高分的，移到已选区域
"""

def selection_sort(arr):
    """
    选择排序
    
    Args:
        arr: 待排序列表(原地修改)
        
    Returns:
        排序后的列表
    """
    n = len(arr)
    
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    
    return arr

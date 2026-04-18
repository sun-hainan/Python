"""
快速排序 (Quick Sort) - 完整中文注释版
==========================================

【算法原理】
快速排序采用分治策略：
1. 选择一个基准元素(pivot)
2. 将数组分为两部分：左 <= pivot < 右
3. 递归对左右两部分排序

【复杂度分析】
|   情况   |  时间复杂度  |  空间复杂度  |   稳定性   |
|----------|-------------|-------------|-----------|
|   平均   | O(n log n)  |   O(log n)  |   不稳定   |
|   最坏   |    O(n^2)    |    O(n)     |   不稳定   |
|   最好   | O(n log n)  |   O(log n)  |   不稳定   |

【算法特点】
+ 高效：平均 O(n log n)，实际应用最广泛
+ 就地：不需要额外存储空间
- 不稳定：相等元素可能改变相对次序

【优化策略】
1. 随机选择 pivot：避免最坏情况
2. 三数取中：选择首、中、尾的中位数
"""

from __future__ import annotations
from random import randrange


def quick_sort(collection: list) -> list:
    """
    快速排序
    
    示例:
        >>> quick_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> quick_sort([])
        []
    """
    if len(collection) < 2:
        return collection
    
    pivot_index = randrange(len(collection))
    pivot = collection.pop(pivot_index)
    
    lesser = [item for item in collection if item <= pivot]
    greater = [item for item in collection if item > pivot]
    
    return [*quick_sort(lesser), pivot, *quick_sort(greater)]


if __name__ == "__main__":
    import doctest
    doctest.testmod()

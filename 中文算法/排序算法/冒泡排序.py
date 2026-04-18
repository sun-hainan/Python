"""
冒泡排序 (Bubble Sort) - 完整中文注释版
==========================================

【算法原理】
冒泡排序是最基础的排序算法，因每轮排序后最大元素逐渐"冒泡"到顶部而得名。
属于比较排序，通过不断比较相邻元素并在需要时交换位置来达到排序目的。

【算法步骤图解】
以 [5, 3, 8, 4, 2] 为例：
第1轮: [3, 5, 4, 2, 8]  - 5和3交换，5和8不交换，8和4交换，8和2交换
第2轮: [3, 4, 2, 5, 8]  - 3和4不交换，4和2交换
第3轮: [3, 2, 4, 5, 8]  - 3和2交换
第4轮: [2, 3, 4, 5, 8]  - 已排序完成

【复杂度分析】
|   情况   |  时间复杂度  |  空间复杂度  |   稳定性   |
|----------|-------------|-------------|-----------|
|   平均   |    O(n^2)   |    O(1)     |    稳定    |
|   最坏   |    O(n^2)   |    O(1)     |    稳定    |
|   最好   |    O(n)     |    O(1)     |    稳定    |

【算法特点】
+ 稳定排序：相等的元素不会交换位置
+ 原地排序：不需要额外存储空间
+ 实现简单：代码直观易懂
- 时间复杂度高：不适合大规模数据

【优化方案】
1. 提前终止：如果一轮没有发生交换，说明已排序完成
2. 记录最后交换位置：减少不必要的比较
3. 双向冒泡：同时从两端冒泡

【适用场景】
- 数据规模较小（n < 1000）
- 基本有序或部分有序的数据
- 教学和学习排序算法原理
"""

from typing import Any


def bubble_sort_iterative(collection: list[Any]) -> list[Any]:
    """
    冒泡排序（迭代版）
    
    参数:
        collection (list): 要排序的可变列表
        
    返回:
        list: 排序后的列表（原地修改）
        
    示例:
        >>> bubble_sort_iterative([0, 5, 2, 3, 2])
        [0, 2, 2, 3, 5]
        >>> bubble_sort_iterative([])
        []
        >>> bubble_sort_iterative([-2, -5, -45])
        [-45, -5, -2]
    """
    length = len(collection)
    
    # 外层循环：控制排序轮数
    for i in reversed(range(length)):
        swapped = False  # 优化：标记本轮是否有交换
        
        # 内层循环：比较并交换相邻元素
        for j in range(i):
            if collection[j] > collection[j + 1]:
                swapped = True
                collection[j], collection[j + 1] = collection[j + 1], collection[j]
        
        # 优化：如果本轮没有交换，说明已排序完成
        if not swapped:
            break
    
    return collection


def bubble_sort_recursive(collection: list[Any]) -> list[Any]:
    """
    冒泡排序（递归版）
    """
    length = len(collection)
    swapped = False
    
    for i in range(length - 1):
        if collection[i] > collection[i + 1]:
            collection[i], collection[i + 1] = collection[i + 1], collection[i]
            swapped = True
    
    if not swapped:
        return collection
    
    return bubble_sort_recursive(collection)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

"""
冒泡排序 (Bubble Sort) - 完整中文注释版
==========================================

【算法原理】
冒泡排序是最基础的排序算法之一，因其排序过程像气泡上浮而得名。
核心思想是：重复遍历列表，比较相邻元素，逐步将最大元素"冒泡"到最后。

【算法步骤】
1. 从列表第一个元素开始，比较相邻的两个元素
2. 如果前一个元素 > 后一个元素，则交换它们的位置
3. 每一轮遍历后，最大的元素会"冒泡"到最后
4. 重复 1-3，直到没有需要交换的元素

【复杂度分析】
- 时间复杂度：
  - 平均: O(n²)
  - 最坏: O(n²) - 逆序数组
  - 最好: O(n) - 已排序数组（优化后可提前终止）
- 空间复杂度：O(1) - 原地排序

【算法特点】
✓ 稳定排序：相等的元素不会交换位置
✓ 简单直观：适合初学者学习
✗ 大规模数据效率低：实际应用中较少使用

【优化方向】
1. 提前终止：如果一轮没有交换，说明已排序
2. 记录最后交换位置：减少不必要的比较
3. 双向冒泡：同时冒泡最大和最小

【Python 实现】
"""

from typing import Any


def bubble_sort_iterative(collection: list[Any]) -> list[Any]:
    """
    冒泡排序（迭代版）
    
    参数:
        collection: 要排序的可变列表
        
    返回:
        排序后的列表（原地修改）
        
    示例:
        >>> bubble_sort_iterative([0, 5, 2, 3, 2])
        [0, 2, 2, 3, 5]
    """
    length = len(collection)
    
    # 从后向前遍历，每一轮确定一个最大元素的位置
    for i in reversed(range(length)):
        swapped = False  # 标记本轮是否有交换
        for j in range(i):
            # 比较相邻元素，顺序错误则交换
            if collection[j] > collection[j + 1]:
                swapped = True
                collection[j], collection[j + 1] = collection[j + 1], collection[j]
        
        # 如果本轮没有交换，说明已排序，提前终止
        if not swapped:
            break
    
    return collection


def bubble_sort_recursive(collection: list[Any]) -> list[Any]:
    """
    冒泡排序（递归版）
    
    递归思想：
    1. 一轮遍历：将最大元素移动到最后
    2. 递归处理剩余的前 n-1 个元素
    3. 递归终止：没有元素需要交换
    """
    length = len(collection)
    swapped = False
    
    # 一轮遍历
    for i in range(length - 1):
        if collection[i] > collection[i + 1]:
            collection[i], collection[i + 1] = collection[i + 1], collection[i]
            swapped = True
    
    # 如果没有交换，说明已经有序，递归终止
    if not swapped:
        return collection
    
    # 递归处理剩余元素
    return bubble_sort_recursive(collection)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    # 测试
    test_list = [64, 34, 25, 12, 22, 11, 90]
    print(f"原始列表: {test_list}")
    print(f"排序后:   {bubble_sort_iterative(test_list.copy())}")

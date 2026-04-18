"""
归并排序 (Merge Sort) - 完整中文注释版
==========================================

【算法原理】
归并排序采用分治策略：
1. 分解：将数组分成两半
2. 解决：递归地对两个子数组排序
3. 合并：将两个有序子数组合并

【复杂度分析】
|   情况   |  时间复杂度  |  空间复杂度  |   稳定性   |
|----------|-------------|-------------|-----------|
|   平均   | O(n log n)  |    O(n)     |    稳定    |
|   最坏   | O(n log n)  |    O(n)     |    稳定    |
|   最好   | O(n log n)  |    O(n)     |    稳定    |

【算法特点】
+ 稳定排序
+ 时间稳定：任何情况下都是 O(n log n)
+ 适合外部排序
- 需要 O(n) 额外空间
"""


def merge_sort(collection: list) -> list:
    """
    归并排序
    
    示例:
        >>> merge_sort([38, 27, 43, 3, 9, 82, 10])
        [3, 9, 10, 27, 38, 43, 82]
        >>> merge_sort([])
        []
    """
    
    def merge(left: list, right: list) -> list:
        result = []
        while left and right:
            result.append(left.pop(0) if left[0] <= right[0] else right.pop(0))
        result.extend(left)
        result.extend(right)
        return result
    
    if len(collection) <= 1:
        return collection
    
    mid = len(collection) // 2
    left = merge_sort(collection[:mid])
    right = merge_sort(collection[mid:])
    
    return merge(left, right)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

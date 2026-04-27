# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / sliding_window_maximum

本文件实现 sliding_window_maximum 相关的算法功能。
"""

from collections import deque


def sliding_window_maximum(numbers: list[int], window_size: int) -> list[int]:
    """
    计算滑动窗口最大值。
    
    Args:
        numbers: 整数数组
        window_size: 窗口大小（必须为正整数）
    
    Returns:
        每个窗口的最大值列表
    
    Raises:
        ValueError: 窗口大小非法
    
    示例:
        >>> sliding_window_maximum([1, 3, -1, -3, 5, 3, 6, 7], 3)
        [3, 3, 5, 5, 6, 7]
        >>> sliding_window_maximum([9, 11], 2)
        [11]
        >>> sliding_window_maximum([], 3)
        []
    """
    if window_size <= 0:
        raise ValueError("Window size must be a positive integer")
    if not numbers:
        return []

    result: list[int] = []
    index_deque: deque[int] = deque()

    for current_index, current_value in enumerate(numbers):
        # 移除超出窗口范围的元素
        if index_deque and index_deque[0] == current_index - window_size:
            index_deque.popleft()

        # 移除比当前元素小的无用元素（从队尾）
        while index_deque and numbers[index_deque[-1]] < current_value:
            index_deque.pop()

        # 当前元素索引入队
        index_deque.append(current_index)

        # 当窗口形成后，记录队首（最大值）
        if current_index >= window_size - 1:
            result.append(numbers[index_deque[0]])

    return result


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        ([1, 3, -1, -3, 5, 3, 6, 7], 3),
        ([9, 11], 2),
        ([4, 2, 12, 3], 1),
        ([1], 1),
    ]
    
    print("=== 滑动窗口最大值测试 ===")
    for nums, k in test_cases:
        result = sliding_window_maximum(nums, k)
        print(f"数组: {nums}, 窗口: {k} -> 结果: {result}")

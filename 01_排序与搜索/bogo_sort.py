# -*- coding: utf-8 -*-
"""
Bogo Sort（猴子排序）
==========================================

【算法原理】
随机打乱数组，直到恰好有序。
一种幽默的"暴力美学"算法。

【时间复杂度】
- 平均: O((n+1)!)
- 最坏: ∞（可能永远不会排好）

【空间复杂度】O(1)

【应用场景】
- 教学演示（笑点算法）
- 概率论演示

【何时使用】
- 永远不要在实际项目中使用
- 除非你需要随机数生成器的测试用例
"""

import random
from typing import List


def bogo_sort(collection: List[int]) -> List[int]:
    """
    Bogo Sort（猴子排序）

    【算法步骤】
    1. 检查数组是否已有序
    2. 如果无序，随机打乱
    3. 重复直到有序

    【警告】
    这个算法可能运行很长时间！

    【参数】
    - collection: 待排序数组

    【返回】
    - 排序后的数组
    """
    def is_sorted(collection: List[int]) -> bool:
        """检查数组是否有序"""
        for i in range(len(collection) - 1):
            if collection[i] > collection[i + 1]:
                return False
        return True

    # -------- 主循环 --------
    # 直到数组有序为止
    while not is_sorted(collection):
        # 随机打乱
        random.shuffle(collection)

    return collection


def bogo_sort_counted(collection: List[int], max_attempts: int = 100000) -> List[int]:
    """
    带计数器的Bogo Sort

    【参数】
    - collection: 待排序数组
    - max_attempts: 最大尝试次数

    【返回】
    - 排序后的数组，如果超时返回None

    【用途】
    - 用于测试，限制最大运行时间
    """
    def is_sorted(collection: List[int]) -> bool:
        for i in range(len(collection) - 1):
            if collection[i] > collection[i + 1]:
                return False
        return True

    attempts = 0
    while not is_sorted(collection) and attempts < max_attempts:
        random.shuffle(collection)
        attempts += 1

    if attempts >= max_attempts:
        return None  # 超时

    return collection


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Bogo Sort（猴子排序） - 测试")
    print("=" * 50)

    # 测试1：小数组（必须很小，否则会卡住）
    print("\n【测试1】小数组（3-4个元素）")
    test_cases = [
        ([3, 1, 2], [1, 2, 3]),
        ([2, 1], [1, 2]),
        ([1, 2, 3], [1, 2, 3]),
    ]

    for arr, expected in test_cases:
        result = bogo_sort_counted(arr.copy(), max_attempts=1000)
        if result is not None:
            print(f"  ✅ {arr} -> {result}")
        else:
            print(f"  ⏱️ {arr} -> 超时")

    # 测试2：空数组和单元素
    print("\n【测试2】边界情况")
    print(f"  [] -> {bogo_sort_counted([], 100)}")
    print(f"  [1] -> {bogo_sort_counted([1], 100)}")

    # 测试3：统计概率
    print("\n【测试3】排序成功概率估计")
    n = 3
    arr = [3, 2, 1]
    success_count = 0
    trials = 100

    for _ in range(trials):
        test_arr = arr.copy()
        result = bogo_sort_counted(test_arr, max_attempts=100)
        if result is not None:
            success_count += 1

    print(f"  {trials}次试验中，{success_count}次在100次内成功")
    print(f"  成功率: {success_count/trials:.1%}")

    print("\n" + "=" * 50)
    print("警告：不要对大数组使用Bogo Sort！")
    print("=" * 50)

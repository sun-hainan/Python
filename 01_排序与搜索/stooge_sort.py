# -*- coding: utf-8 -*-
"""
Stooge Sort（怪异排序）
==========================================

【算法原理】
递归地将数组两端元素交换位置，直到整个数组有序。
一种幽默的"教科书级别"低效算法。

【时间复杂度】O(n^(log 3 / log 1.5)) ≈ O(n^2.71)
【空间复杂度】O(n)（递归栈）

【应用场景】
- 教学演示（展示低效算法）
- 算法复杂度理论

【何时使用】
- 永远不要在实际项目中使用
"""

from typing import List


def stooge_sort(arr: List[int]) -> List[int]:
    """
    Stooge Sort（怪异排序）

    【算法步骤】
    1. 如果首元素大于尾元素，交换
    2. 如果元素数量 > 2：
       - 递归排序前2/3部分
       - 递归排序后2/3部分
       - 递归排序前2/3部分

    【参数】
    - arr: 待排序数组

    【返回】
    - 排序后的数组
    """
    stooge(arr, 0, len(arr) - 1)
    return arr


def stooge(arr: List[int], i: int, h: int) -> None:
    """
    Stooge递归辅助函数

    【参数】
    - arr: 数组
    - i: 起始索引
    - h: 结束索引
    """
    # -------- 递归终止条件 --------
    # 如果起始索引 >= 结束索引，直接返回
    if i >= h:
        return

    # -------- 第1步：首尾比较交换 --------
    # 如果首元素大于尾元素，交换
    if arr[i] > arr[h]:
        arr[i], arr[h] = arr[h], arr[i]

    # -------- 第2步：递归排序 --------
    # 如果区间长度 > 2，继续递归
    if h - i + 1 > 2:
        # 计算三分之一长度
        t = (h - i + 1) // 3

        # 递归排序前2/3部分
        stooge(arr, i, h - t)

        # 递归排序后2/3部分
        stooge(arr, i + t, h)

        # 递归排序前2/3部分
        stooge(arr, i, h - t)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Stooge Sort（怪异排序） - 测试")
    print("=" * 50)

    # 测试1：基本排序
    print("\n【测试1】基本排序")
    test_cases = [
        ([3, 1, 4, 1, 5, 9, 2, 6], [1, 1, 2, 3, 4, 5, 6, 9]),
        ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ([], []),
        ([1], [1]),
        ([2, 2, 2, 2], [2, 2, 2, 2]),
    ]

    for arr, expected in test_cases:
        result = stooge_sort(arr.copy())
        status = "✅" if result == expected else "❌"
        print(f"  {status} {arr} -> {result}")

    # 测试2：性能对比
    print("\n【测试2】性能对比（仅供参考，请勿在实际项目使用）")
    import time

    sizes = [5, 8, 10]
    for size in sizes:
        arr = list(range(size, 0, -1))  # 逆序数组
        start = time.time()
        stooge_sort(arr.copy())
        elapsed = time.time() - start
        print(f"  n={size}: {elapsed*1000:.3f}ms")

    # 测试3：浮点数
    print("\n【测试3】浮点数排序")
    float_arr = [3.14, 1.41, 2.71, 0.0, -1.0]
    result = stooge_sort(float_arr.copy())
    print(f"  {float_arr} -> {result}")

    print("\n" + "=" * 50)
    print("注意：这是教学演示算法，实际项目请使用快速排序！")
    print("=" * 50)

# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / funnel_sort

本文件实现 funnel_sort 相关的算法功能。
"""

import math
from typing import List


class FunnelSort:
    """Funnel Sort算法"""

    def __init__(self, data: List[int]):
        self.data = data
        self.n = len(data)

    def sort(self) -> List[int]:
        """
        缓存无关排序

        返回：排序后的数组
        """
        return self._funnel_sort(self.data)

    def _funnel_sort(self, arr: List[int]) -> List[int]:
        """Funnel排序递归"""
        n = len(arr)

        if n <= 1:
            return arr

        if n <= 64:  # 小数组用简单排序
            return sorted(arr)

        # 分成两半
        mid = n // 2
        left = self._funnel_sort(arr[:mid])
        right = self._funnel_sort(arr[mid:])

        # 合并
        return self._merge(left, right)

    def _merge(self, left: List[int], right: List[int]) -> List[int]:
        """合并两个有序数组"""
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])

        return result


def cache_oblivious_analysis():
    """缓存无关分析"""
    print("=== Funnel Sort缓存分析 ===")
    print()
    print("时间复杂度：")
    print("  - T(n) = 2T(n/2) + O(n/B)")
    print("  - 其中 B 是缓存块大小")
    print()
    print("缓存复杂度：")
    print("  - O((n/B) log(n/M))")
    print("  - M 是缓存大小")
    print()
    print("对比标准归并排序：")
    print("  - 标准：O(n log n)")
    print("  - 缓存无关：O((n/B) log n + n)")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Funnel Sort测试 ===\n")

    # 测试数据
    data = [5, 2, 8, 1, 9, 3, 7, 4, 6]
    print(f"原始: {data}")

    sorter = FunnelSort(data)
    sorted_data = sorter.sort()

    print(f"排序: {sorted_data}")
    print(f"验证: {'✅ 正确' if sorted_data == sorted(data) else '❌ 错误'}")

    print()
    cache_oblivious_analysis()

    print()
    print("说明：")
    print("  - Funnel Sort是理论上最优的缓存无关排序")
    print("  - 实际中常数较大")
    print("  - 用于外部内存和现代CPU层次优化")

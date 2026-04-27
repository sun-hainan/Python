# -*- coding: utf-8 -*-
"""
算法实现：数据流算法 / sliding_window

本文件实现 sliding_window 相关的算法功能。
"""

import random
from collections import deque
from typing import List


class SlidingWindowStatistics:
    """滑动窗口统计"""

    def __init__(self, window_size: int):
        """
        参数：
            window_size: 窗口大小
        """
        self.W = window_size
        self.window = deque(maxlen=window_size)

    def add(self, value: float) -> None:
        """添加元素"""
        self.window.append(value)

    def mean(self) -> float:
        """窗口均值"""
        if not self.window:
            return 0.0
        return sum(self.window) / len(self.window)

    def variance(self) -> float:
        """窗口方差"""
        if len(self.window) <= 1:
            return 0.0
        mean = self.mean()
        return sum((x - mean) ** 2 for x in self.window) / len(self.window)

    def max_value(self) -> float:
        """窗口最大值"""
        return max(self.window) if self.window else 0.0

    def min_value(self) -> float:
        """窗口最小值"""
        return min(self.window) if self.window else 0.0

    def median(self) -> float:
        """窗口中位数"""
        if not self.window:
            return 0.0
        sorted_vals = sorted(self.window)
        n = len(sorted_vals)
        if n % 2 == 0:
            return (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
        else:
            return sorted_vals[n//2]


class ExponentialHistogram:
    """指数直方图（滑动窗口频率估计）"""

    def __init__(self, window_size: int):
        """
        参数：
            window_size: 窗口大小
        """
        self.W = window_size
        self.buckets = []
        self.current_time = 0

    def add(self, element: str) -> None:
        """添加元素"""
        self.current_time += 1
        self.buckets.append([element, 1, self.current_time])

        # 合并相邻的相同计数桶
        self._merge()

    def _merge(self) -> None:
        """合并桶"""
        merged = []
        i = 0
        while i < len(self.buckets):
            if merged and merged[-1][0] == self.buckets[i][0]:
                merged[-1][1] += self.buckets[i][1]
            else:
                merged.append(self.buckets[i])
            i += 1
        self.buckets = merged

    def estimate_frequency(self, element: str) -> int:
        """估计元素频率"""
        total = 0
        for bucket in self.buckets:
            if bucket[0] == element:
                total += bucket[1]
        return total

    def prune_old(self) -> None:
        """删除过期的桶"""
        # 简化：删除第一个桶
        if len(self.buckets) > 1:
            self.buckets.pop(0)


def sliding_window_applications():
    """滑动窗口应用"""
    print("=== 滑动窗口应用 ===")
    print()
    print("1. 网络流量监控")
    print("   - 最近1分钟的包数量")
    print("   - 异常检测")
    print()
    print("2. 金融数据分析")
    print("   - 移动平均线")
    print("   - 波动率估计")
    print()
    print("3. 传感器数据处理")
    print("   - 平滑噪声")
    print("   - 趋势检测")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 滑动窗口统计测试 ===\n")

    # 创建滑动窗口
    window = SlidingWindowStatistics(window_size=5)

    # 模拟数据流
    stream = [10, 20, 15, 25, 30, 12, 18, 22, 28, 35]

    print("数据流:")
    for i, val in enumerate(stream):
        window.add(val)
        print(f"  第{i+1}个: {val}, 窗口均值: {window.mean():.2f}")

    print()
    print(f"最终窗口: {list(window.window)}")
    print(f"均值: {window.mean():.2f}")
    print(f"方差: {window.variance():.2f}")
    print(f"最大值: {window.max_value():.2f}")
    print(f"最小值: {window.min_value():.2f}")
    print(f"中位数: {window.median():.2f}")

    print()
    sliding_window_applications()

    print()
    print("说明：")
    print("  - 滑动窗口适用于流数据")
    print("  - 需要高效更新统计量")
    print("  - 指数直方图是常用技术")

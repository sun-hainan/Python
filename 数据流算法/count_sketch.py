# -*- coding: utf-8 -*-
"""
算法实现：数据流算法 / count_sketch

本文件实现 count_sketch 相关的算法功能。
"""

import hashlib
import random
from typing import List


class CountSketch:
    """Count Sketch"""

    def __init__(self, width: int, depth: int):
        """
        参数：
            width: 计数器数组宽度（w）
            depth: 哈希函数数量（d）
        """
        self.w = width
        self.d = depth
        self.counters = [[0] * width for _ in range(depth)]

    def _hash(self, item: int, seed: int) -> int:
        """哈希函数"""
        h = hashlib.md5(f"{item}_{seed}".encode())
        return int(h.hexdigest(), 16) % self.w

    def _sign_hash(self, item: int, seed: int) -> int:
        """符号哈希"""
        h = hashlib.md5(f"sign_{item}_{seed}".encode())
        return 1 if int(h.hexdigest(), 16) % 2 == 0 else -1

    def add(self, item: int, count: int = 1) -> None:
        """添加元素"""
        for i in range(self.d):
            idx = self._hash(item, i)
            sign = self._sign_hash(item, i)
            self.counters[i][idx] += sign * count

    def estimate(self, item: int) -> float:
        """
        估计元素频率

        返回：频率估计（中位数）
        """
        estimates = []

        for i in range(self.d):
            idx = self._hash(item, i)
            sign = self._sign_hash(item, i)

            # 反解频率：count = counter * sign
            estimates.append(self.counters[i][idx] * sign)

        # 取中位数
        estimates.sort()
        return estimates[self.d // 2]

    def estimate_f2(self) -> float:
        """
        估计二阶矩 F2 = Σ f_i²

        返回：F2估计
        """
        sum_sq = 0
        for i in range(self.d):
            sq = sum(c * c for c in self.counters[i])
            sum_sq += sq

        return sum_sq / self.d


def count_sketch_vs_count_min():
    """Count Sketch vs Count-Min"""
    print("=== Count Sketch vs Count-Min ===")
    print()
    print("Count-Min:")
    print("  - 记录最小计数器值")
    print("  - 给出上界估计（偏大）")
    print("  - 简单实现")
    print()
    print("Count Sketch:")
    print("  - 使用正负号抵消冲突")
    print("  - 取中位数估计")
    print("  - 更准确但稍复杂")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Count Sketch测试 ===\n")

    random.seed(42)

    # 创建Sketch
    sketch = CountSketch(width=100, depth=5)

    # 数据流
    stream = [1, 2, 1, 3, 1, 2, 1, 4, 1, 2, 1, 3, 1, 2, 1]

    print(f"数据流: {stream}")
    print()

    # 添加到Sketch
    for item in stream:
        sketch.add(item)

    # 估计频率
    print("频率估计：")
    for item in [1, 2, 3, 4]:
        est = sketch.estimate(item)
        print(f"  元素 {item}: 估计频率 = {est:.1f}")

    # 真实频率
    from collections import Counter
    freq = Counter(stream)
    print("真实频率：")
    for item, count in freq.items():
        print(f"  元素 {item}: {count}")

    print()
    print("F2估计：")
    f2_est = sketch.estimate_f2()
    f2_real = sum(f ** 2 for f in freq.values())
    print(f"  估计: {f2_est:.2f}")
    print(f"  真实: {f2_real}")

    print()
    count_sketch_vs_count_min()

    print()
    print("说明：")
    print("  - Count Sketch比Count-Min更准确")
    print("  - 适用于Heavy Hitters检测")
    print("  - 空间效率高：O(w * d) = O(1/ε²)")

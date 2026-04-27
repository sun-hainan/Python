# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / bloom_filter

本文件实现 bloom_filter 相关的算法功能。
"""

import math


class BloomFilter:
    """布隆过滤器"""

    def __init__(self, n: int, fp_rate: float = 0.01):
        """
        参数：
            n: 预计元素数量
            fp_rate: 期望假阳性率
        """
        self.n = n
        self.fp_rate = fp_rate

        # 计算位数组大小和哈希函数数量
        self.m = int(-n * math.log(fp_rate) / (math.log(2) ** 2)) + 1
        self.k = int((self.m / n) * math.log(2)) + 1

        self.bits = [False] * self.m

    def _hash(self, item, seed: int) -> int:
        """哈希函数（简单实现）"""
        h = seed
        for char in str(item):
            h = (h * 31 + ord(char)) % self.m
        return h

    def add(self, item):
        """添加元素"""
        for seed in range(self.k):
            idx = self._hash(item, seed)
            self.bits[idx] = True

    def contains(self, item) -> bool:
        """查询元素（可能假阳性）"""
        for seed in range(self.k):
            idx = self._hash(item, seed)
            if not self.bits[idx]:
                return False  # 一定不存在
        return True  # 可能存在

    def reset(self):
        """清空"""
        self.bits = [False] * self.m

    def estimate_fill_ratio(self) -> float:
        """估计填充率"""
        return sum(self.bits) / self.m


class CountingBloomFilter:
    """计数布隆过滤器（支持删除）"""

    def __init__(self, n: int, fp_rate: float = 0.01):
        self.bf = BloomFilter(n, fp_rate)
        self.counters = [0] * self.bf.m

    def add(self, item):
        for seed in range(self.bf.k):
            idx = self.bf._hash(item, seed)
            self.counters[idx] += 1
            self.bf.bits[idx] = True

    def remove(self, item):
        for seed in range(self.bf.k):
            idx = self.bf._hash(item, seed)
            if self.counters[idx] > 0:
                self.counters[idx] -= 1
            if self.counters[idx] == 0:
                self.bf.bits[idx] = False

    def contains(self, item):
        return self.bf.contains(item)


def simulated_benchmark():
    """模拟基准测试"""
    import random

    print("=== 布隆过滤器基准测试 ===\n")

    n = 10000
    fp_rate = 0.01

    bf = BloomFilter(n, fp_rate)

    # 插入n个元素
    items = [random.randint(1, 1000000) for _ in range(n)]
    for item in items:
        bf.add(item)

    print(f"参数：n={n}, fp_rate={fp_rate}")
    print(f"位数组大小：{bf.m} bits = {bf.m/8:.2f} bytes")
    print(f"哈希函数数量：{bf.k}")
    print(f"填充率：{bf.estimate_fill_ratio()*100:.1f}%")
    print()

    # 测试假阳性率
    false_positives = 0
    test_items = [random.randint(1, 1000000) for _ in range(100000)]
    for item in test_items:
        if item not in items and bf.contains(item):
            false_positives += 1

    measured_fp = false_positives / len(test_items)
    print(f"测试 {len(test_items)} 个不存在元素")
    print(f"假阳性数：{false_positives}")
    print(f"实际假阳性率：{measured_fp*100:.2f}%")
    print(f"预期假阳性率：{fp_rate*100:.2f}%")

    # 对比普通集合
    regular_set = set(items)
    regular_set_size = len(regular_set) * 8 * 2  # Python对象开销大
    bf_size = bf.m / 8

    print()
    print(f"空间对比：")
    print(f"  布隆过滤器：{bf_size:.2f} bytes")
    print(f"  普通集合（估算）：~{regular_set_size:,} bytes")
    print(f"  节省：{(1 - bf_size/regular_set_size)*100:.1f}%")


if __name__ == "__main__":
    print("=== 布隆过滤器测试 ===\n")

    bf = BloomFilter(1000, 0.01)

    # 添加元素
    test_items = ["apple", "banana", "cherry", "date"]
    for item in test_items:
        bf.add(item)
        print(f"添加：{item}")

    print()

    # 查询
    queries = ["apple", "banana", "grape", "mango"]
    for q in queries:
        result = bf.contains(q)
        status = "✅ 可能存在" if result else "❌ 不存在"
        note = " (假阳性)" if result and q not in test_items else ""
        print(f"查询：{q} -> {status}{note}")

    print()
    simulated_benchmark()

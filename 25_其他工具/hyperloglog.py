# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / hyperloglog

本文件实现 hyperloglog 相关的算法功能。
"""

import math


class HyperLogLog:
    """HyperLogLog 去重计数器"""

    # 偏差修正用的常量
    ALPHA = 0.7213  # 调和常数
    REGISTERS = 1 << 10  # 寄存器数量（1024个）

    def __init__(self, registers: int = None):
        """
        参数：
            registers: 寄存器数量（2的幂），默认1024
        """
        self.registers = registers or self.REGISTERS
        self.m = self.registers
        self.data = [0] * self.m

    def _hash(self, item: str) -> int:
        """简单的哈希函数（实际应用应用更好的哈希）"""
        h = 2166136261  # FNV offset
        for char in item:
            h ^= ord(char)
            h *= 16777619
            h &= 0xFFFFFFFF
        return h

    def add(self, item: str):
        """添加一个元素"""
        # 计算哈希值
        h = self._hash(item)

        # 使用前log2(m)位作为桶索引
        p = int(math.log2(self.m))
        idx = h & (self.m - 1)

        # 计算前导零+1（ρ函数）
        # 去掉索引位，看剩余位的前导零
        remaining = h >> p
        if remaining == 0:
            # 特殊处理：所有位都是0
            leading_zeros = 32 - p
        else:
            leading_zeros = (remaining ^ (remaining - 1)).bit_length()
            # 实际上要重新计算
            bits = remaining
            count = 0
            while bits & 1 == 0 and count < 32:
                bits >>= 1
                count += 1
            leading_zeros = count

        # ρ函数：前导零+1
        rho = 32 - p - leading_zeros + 1
        rho = max(1, min(rho, 32 - p))

        # 更新寄存器
        self.data[idx] = max(self.data[idx], rho)

    def count(self) -> int:
        """
        估计基数（去重后的元素数量）
        """
        # 计算调和平均
        sum_inv = 0.0
        for v in self.data:
            sum_inv += 2.0 ** (-v)

        # 原始估计
        raw_estimate = self.ALPHA * self.m * self.m / sum_inv

        # 偏差修正
        if raw_estimate <= 2.5 * self.m:
            # 小基数修正：暴力统计
            zeros = self.data.count(0)
            if zeros != 0:
                return int(self.m * math.log(self.m / zeros))
        elif raw_estimate > (1 << 32) / 30.0:
            # 大基数修正
            return -int(2 ** 32 * math.log(1 - raw_estimate / (1 << 32)))

        return int(raw_estimate)

    def reset(self):
        """重置"""
        self.data = [0] * self.m


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== HyperLogLog 测试 ===\n")

    import random

    hll = HyperLogLog()

    # 测试1：已知数量
    n = 100000
    items = [f"user_{i}" for i in range(n)]

    for item in items:
        hll.add(item)

    estimate = hll.count()
    error = abs(estimate - n) / n * 100

    print(f"插入 {n} 个元素")
    print(f"估计值: {estimate}")
    print(f"相对误差: {error:.2f}%")

    # 测试2：大量重复
    print("\n--- 大量重复 ---")
    hll2 = HyperLogLog()
    duplicates = ["item"] * 10000 + ["other"] * 5000

    for item in duplicates:
        hll2.add(item)

    estimate2 = hll2.count()
    print(f"10000个'item' + 5000个'other'")
    print(f"估计去重后: {estimate2} (实际: 2)")

    # 测试3：空间对比
    print("\n--- 空间效率对比 ---")
    n_large = 10000000

    exact_set = set()
    for i in range(n_large):
        exact_set.add(f"item_{i}")

    # HyperLogLog 空间
    hll_space = hll.registers  # int数组
    # set 空间（粗略估算）
    set_space = len(exact_set) * 8  # Python对象开销很大

    print(f"计数 {n_large:,} 个元素：")
    print(f"  HyperLogLog: {hll_space} 个寄存器 ≈ {hll_space * 8} bytes")
    print(f"  精确Set: ≈ {set_space:,} bytes")
    print(f"  节省空间: {(1 - (hll_space*8)/set_space)*100:.2f}%")

    print("\n说明：")
    print("  - 标准误差约 1.625 / sqrt(m)")
    print("  - m=1024 时，标准误差约 5%")
    print("  - Google BigQuery、Redis 都内置了 HyperLogLog")

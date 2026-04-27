# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / hyperloglog

本文件实现 hyperloglog 相关的算法功能。
"""

import math
import hashlib
from typing import List


class HyperLogLog:
    """
    HyperLogLog算法
    使用哈希函数和桶来估计不同元素的数量
    """
    
    def __init__(self, p: int = 10):
        """
        初始化
        
        Args:
            p: 位数(决定桶数量m = 2^p)
        """
        self.p = p
        self.m = 2 ** p
        
        # 桶
        self.registers = [0] * self.m
        
        # 哈希函数参数
        self._seed = 42
    
    def _hash(self, item: str) -> int:
        """计算哈希值"""
        h = hashlib.sha256(f"{self._seed}{item}".encode()).hexdigest()
        return int(h, 16)
    
    def add(self, item: str):
        """添加元素"""
        # 计算哈希
        h = self._hash(item)
        
        # 取前p位作为桶索引
        bucket_idx = h & (self.m - 1)
        
        # 取剩余位中前导零的数量+1
        remaining = h >> self.p
        leading_zeros = (remaining.bit_length() + self.m.bit_length() - remaining.bit_length()) if remaining else 0
        
        # 计算前导零(从最高位开始)
        max_bits = 64 - self.p
        zeros = 0
        for i in range(max_bits - 1, -1, -1):
            if (remaining >> i) & 1:
                break
            zeros += 1
        
        # 更新桶
        self.registers[bucket_idx] = max(self.registers[bucket_idx], zeros + 1)
    
    def count(self) -> int:
        """
        估计基数
        
        Returns:
            估计的不同元素数量
        """
        # 调和平均
        m = self.m
        sum_inv = sum(2 ** (-reg) for reg in self.registers)
        
        # 原始估计
        estimate = m * m / sum_inv
        
        # 修正(小基数)
        if estimate < 2.5 * m:
            # 使用线性计数
            zero_count = self.registers.count(0)
            if zero_count > 0:
                estimate = m * math.log(m / zero_count)
        
        # 修正(大基数)
        if estimate > 2 ** 32 / 30:
            estimate = -2 ** 32 * math.log(1 - estimate / 2 ** 32)
        
        return int(estimate)
    
    def merge(self, other: 'HyperLogLog'):
        """合并另一个HyperLogLog"""
        if self.m != other.m:
            raise ValueError("不能合并不同大小的HyperLogLog")
        
        for i in range(self.m):
            self.registers[i] = max(self.registers[i], other.registers[i])
    
    def clear(self):
        """清空"""
        self.registers = [0] * self.m


def create_hyperloglog(error_rate: float = 0.01) -> HyperLogLog:
    """
    根据期望误差率创建HyperLogLog
    
    Args:
        error_rate: 期望的相对标准误差
    
    Returns:
        HyperLogLog实例
    """
    # 标准误差 = 1.04 / sqrt(m)
    # m = (1.04 / error_rate)^2
    m = int((1.04 / error_rate) ** 2)
    p = int(math.log2(m))
    return HyperLogLog(p)


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本功能
    print("测试1 - 基本功能:")
    hll = HyperLogLog(p=10)  # 1024个桶
    
    items = ["apple", "banana", "cherry", "date", "apple", "banana"]
    
    for item in items:
        hll.add(item)
    
    estimate = hll.count()
    print(f"  添加了{len(items)}个元素,实际不同值={len(set(items))}")
    print(f"  估计基数: {estimate}")
    
    # 测试2: 大规模测试
    print("\n测试2 - 大规模测试:")
    import random
    
    random.seed(42)
    
    n = 100000
    unique_items = [f"item_{i}" for i in range(n)]
    
    hll2 = HyperLogLog(p=12)  # 4096个桶
    
    for item in unique_items:
        hll2.add(item)
    
    estimate2 = hll2.count()
    print(f"  实际基数: {n}")
    print(f"  估计基数: {estimate2}")
    print(f"  误差: {abs(estimate2 - n) / n:.4%}")
    
    # 测试3: 不同精度
    print("\n测试3 - 不同精度:")
    for p in [8, 10, 12, 14]:
        hll_p = HyperLogLog(p=p)
        for item in unique_items[:10000]:
            hll_p.add(item)
        
        estimate_p = hll_p.count()
        error = abs(estimate_p - 10000) / 10000
        print(f"  p={p}, m={hll_p.m}: 估计={estimate_p}, 误差={error:.2%}")
    
    # 测试4: 合并
    print("\n测试4 - 合并:")
    hll_a = HyperLogLog(p=10)
    hll_b = HyperLogLog(p=10)
    
    items_a = [f"a_{i}" for i in range(1000)]
    items_b = [f"b_{i}" for i in range(1000)]
    
    for item in items_a:
        hll_a.add(item)
    
    for item in items_b:
        hll_b.add(item)
    
    count_a = hll_a.count()
    count_b = hll_b.count()
    
    hll_a.merge(hll_b)
    count_ab = hll_a.count()
    
    print(f"  A基数: {count_a}")
    print(f"  B基数: {count_b}")
    print(f"  合并基数: {count_ab}")
    print(f"  实际唯一: {len(set(items_a + items_b))}")
    
    # 测试5: 便捷函数
    print("\n测试5 - 便捷函数:")
    hll_auto = create_hyperloglog(0.01)
    print(f"  创建HLL: p={hll_auto.p}, m={hll_auto.m}")
    
    print("\n所有测试完成!")

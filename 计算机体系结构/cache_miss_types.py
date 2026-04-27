# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / cache_miss_types

本文件实现 cache_miss_types 相关的算法功能。
"""

from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import Counter


class Cache:
    """简单缓存模拟器（用于miss分析）"""

    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):
        self.num_sets = num_sets
        self.associativity = associativity
        self.line_size = line_size

        # 缓存数据：[set][way] = (tag, valid, last_used)
        self.cache: List[List[Tuple[int, bool, int]]] = [
            [(0, False, 0) for _ in range(associativity)]
            for _ in range(num_sets)
        ]

        # 统计
        self.hits = 0
        self.misses = 0
        self.compulsory_misses = 0
        self.capacity_misses = 0
        self.conflict_misses = 0

        # 访问历史（用于判断capacity miss）
        self.access_history: List[int] = []  # 访问过的唯一行地址
        self.unique_lines: Set[int] = set()

        # 时间戳
        self.timestamp = 0

    def _get_set(self, address: int) -> int:
        return (address // self.line_size) % self.num_sets

    def _get_tag(self, address: int) -> int:
        return address // (self.line_size * self.num_sets)

    def _get_line_addr(self, address: int) -> int:
        return (address // self.line_size) * self.line_size

    def access(self, address: int) -> str:
        """
        访问缓存
        return: 'hit', 'compulsory', 'capacity', 'conflict'
        """
        self.timestamp += 1
        set_idx = self._get_set(address)
        tag = self._get_tag(address)
        line_addr = self._get_line_addr(address)

        # 记录唯一行
        if line_addr not in self.unique_lines:
            self.unique_lines.add(line_addr)
            is_first_access = True
        else:
            is_first_access = False

        # 检查是否命中
        for way in range(self.associativity):
            cache_tag, valid, last_used = self.cache[set_idx][way]
            if valid and cache_tag == tag:
                self.hits += 1
                self.cache[set_idx][way] = (tag, True, self.timestamp)
                return 'hit'

        # 未命中
        self.misses += 1

        # 判断miss类型
        if is_first_access:
            # 首次访问一定是compulsory miss
            self.compulsory_misses += 1
            miss_type = 'compulsory'
        else:
            # 检查缓存中是否有空位
            has_empty = any(not valid for _, valid, _ in self.cache[set_idx])

            if has_empty:
                # 有空位但冲突，是conflict miss
                self.conflict_misses += 1
                miss_type = 'conflict'
            else:
                # 没有空位，需要驱逐
                # 检查被驱逐的行是否可能是capacity miss
                # 如果unique_lines太多超过缓存容量，则是capacity
                max_capacity = self.num_sets * self.associativity
                if len(self.unique_lines) > max_capacity * 2:
                    self.capacity_misses += 1
                    miss_type = 'capacity'
                else:
                    self.conflict_misses += 1
                    miss_type = 'conflict'

        # 驱逐并加载新行（LRU）
        lru_way = 0
        min_last_used = float('inf')
        for way in range(self.associativity):
            _, _, last_used = self.cache[set_idx][way]
            if last_used < min_last_used:
                min_last_used = last_used
                lru_way = way

        self.cache[set_idx][lru_way] = (tag, True, self.timestamp)
        return miss_type

    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.hits + self.misses
        return {
            'total_accesses': total,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total * 100 if total > 0 else 0,
            'compulsory': self.compulsory_misses,
            'capacity': self.capacity_misses,
            'conflict': self.conflict_misses,
            'unique_lines': len(self.unique_lines),
        }


def simulate_cache_miss_analysis():
    """
    模拟缓存未命中分析
    """
    print("=" * 60)
    print("Cache Miss 类型分析")
    print("=" * 60)

    # 创建缓存：4组，每组2路，64字节行
    cache = Cache(num_sets=4, associativity=2, line_size=64)

    print("\n缓存配置:")
    print(f"  组数: {cache.num_sets}")
    print(f"  相联度: {cache.associativity}")
    print(f"  行大小: {cache.line_size} bytes")
    print(f"  总容量: {cache.num_sets * cache.associativity * cache.line_size} bytes")

    # 测试序列1：Compulsory Miss演示
    print("\n" + "-" * 50)
    print("测试1: Compulsory Miss（首次访问）")
    print("-" * 50)

    # 连续访问不同的行（首次访问都是compulsory miss）
    addresses = [0x0000, 0x0040, 0x0080, 0x00C0]  # 每个都是不同的行首

    print("\n访问序列:")
    for i, addr in enumerate(addresses):
        result = cache.access(addr)
        print(f"  访问 0x{addr:04X}: {result}")

    stats = cache.get_stats()
    print(f"\n统计:")
    print(f"  Compulsory Misses: {stats['compulsory']}")
    print(f"  Capacity Misses: {stats['capacity']}")
    print(f"  Conflict Misses: {stats['conflict']}")

    # 测试序列2：Capacity Miss演示
    print("\n" + "-" * 50)
    print("测试2: Capacity Miss（工作集超过容量）")
    print("-" * 50)

    # 重置缓存
    cache = Cache(num_sets=4, associativity=2, line_size=64)

    # 访问大量不同的行（超过8个slot）
    print("\n访问8个不同行（循环2次）:")
    for round in range(2):
        for i in range(8):
            addr = i * 0x100  # 256字节间隔，确保不同行
            result = cache.access(addr)
            if round == 0:
                print(f"  Round {round+1}: 访问 0x{addr:04X}: {result}")

    stats = cache.get_stats()
    print(f"\n统计:")
    print(f"  Unique Lines: {stats['unique_lines']}")
    print(f"  Compulsory Misses: {stats['compulsory']}")
    print(f"  Capacity Misses: {stats['capacity']}")
    print(f"  Conflict Misses: {stats['conflict']}")

    # 测试序列3：Conflict Miss演示
    print("\n" + "-" * 50)
    print("测试3: Conflict Miss（组相联冲突）")
    print("-" * 50)

    # 重置缓存
    cache = Cache(num_sets=2, associativity=2, line_size=64)

    # 访问映射到同一组的不同行
    # 由于相联度为2，只有2个slot
    print("\n访问映射到同一组的4个不同行:")
    addresses = [0x0000, 0x0040, 0x0080, 0x00C0]  # 都映射到set 0
    results = []
    for addr in addresses:
        result = cache.access(addr)
        results.append(result)

    print(f"\n结果:")
    for i, (addr, result) in enumerate(zip(addresses, results)):
        print(f"  0x{addr:04X}: {result}")

    stats = cache.get_stats()
    print(f"\n统计:")
    print(f"  Compulsory Misses: {stats['compulsory']}")
    print(f"  Conflict Misses: {stats['conflict']}")

    # Miss类型总结
    print("\n" + "=" * 60)
    print("Miss类型总结")
    print("=" * 60)

    print("""
    ┌──────────────┬─────────────────────────────────────┐
    │ 类型         │ 原因                                │
    ├──────────────┼─────────────────────────────────────┤
    │ Compulsory  │ 首次访问某行，冷启动miss            │
    │ Capacity    │ 工作集 > 缓存容量                   │
    │ Conflict    │ 同组内驱逐 (组相联限制)              │
    └──────────────┴─────────────────────────────────────┘

    减少miss的方法:
    - Compulsory: 增加缓存预取
    - Capacity: 增加缓存容量或降低工作集
    - Conflict: 增加相联度或调整缓存映射
    """)


if __name__ == "__main__":
    simulate_cache_miss_analysis()

# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / cache_hierarchy

本文件实现 cache_hierarchy 相关的算法功能。
"""

import random


class CacheLevel:
    """单级缓存。"""

    def __init__(self, size, block_size, name="L1"):
        self.size = size  # 缓存大小（块数）
        self.block_size = block_size
        self.name = name
        self.blocks = {}  # block_id -> data
        self.access_count = 0
        self.miss_count = 0

    def access(self, block_id):
        """访问块。"""
        self.access_count += 1
        if block_id in self.blocks:
            return True  # 命中
        self.miss_count += 1
        return False  # 未命中

    def store(self, block_id, data):
        """存储块（可能触发驱逐）。"""
        if len(self.blocks) >= self.size and block_id not in self.blocks:
            # LRU 驱逐：移除最旧的块
            oldest = next(iter(self.blocks))
            evicted_data = self.blocks.pop(oldest)
            return evicted_data
        self.blocks[block_id] = data
        return None

    def hit_rate(self):
        """缓存命中率。"""
        if self.access_count == 0:
            return 0.0
        return 1 - (self.miss_count / self.access_count)


class CacheHierarchy:
    """多级缓存层次结构。"""

    def __init__(self, levels_config):
        """
        初始化缓存层次。

        参数:
            levels_config: [(size, block_size, name), ...]
        """
        self.levels = []
        for size, block_size, name in levels_config:
            self.levels.append(CacheLevel(size, block_size, name))

    def access(self, block_id):
        """访问块（从 L1 到 Ln）。"""
        for level in self.levels:
            if level.access(block_id):
                return True
        return False

    def store(self, block_id, data):
        """存储块。"""
        for level in self.levels:
            evicted = level.store(block_id, data)
            if evicted is not None:
                # 驱逐块传递到下一级
                data = evicted

    def get_stats(self):
        """获取统计信息。"""
        stats = []
        total_access = 0
        total_miss = 0

        for level in self.levels:
            total_access += level.access_count
            total_miss += level.miss_count
            stats.append({
                'name': level.name,
                'accesses': level.access_count,
                'misses': level.miss_count,
                'hit_rate': level.hit_rate()
            })

        overall_hit_rate = 1 - (total_miss / total_access) if total_access > 0 else 0
        return stats, overall_hit_rate


def simulate_access_pattern(data_size, pattern_type, cache_config):
    """
    模拟不同访问模式下的缓存性能。

    参数:
        data_size: 数据大小
        pattern_type: 'sequential', 'random', 'localized'
        cache_config: 缓存配置
    """
    cache = CacheHierarchy(cache_config)

    if pattern_type == 'sequential':
        # 顺序访问
        for i in range(data_size):
            cache.access(i)

    elif pattern_type == 'random':
        # 随机访问
        random.seed(42)
        for _ in range(data_size):
            i = random.randint(0, data_size - 1)
            cache.access(i)

    elif pattern_type == 'localized':
        # 局部访问（80-20 模式）
        popular = data_size // 5  # 20% 的数据被 80% 访问
        random.seed(42)
        for _ in range(data_size):
            if random.random() < 0.8:
                i = random.randint(0, popular)
            else:
                i = random.randint(popular, data_size - 1)
            cache.access(i)

    return cache.get_stats()


if __name__ == "__main__":
    print("=== 缓存层次结构模拟 ===")

    # 缓存配置：L1 8KB, L2 64KB, L3 256KB
    # 块大小 64 字节
    block_size = 64
    cache_config = [
        (128, block_size, "L1"),    # 8KB
        (1024, block_size, "L2"),    # 64KB
        (4096, block_size, "L3"),    # 256KB
    ]

    data_size = 8192  # 512KB 数据

    # 测试不同访问模式
    for pattern in ['sequential', 'random', 'localized']:
        cache = CacheHierarchy(cache_config)
        stats, overall = simulate_access_pattern(data_size, pattern, cache_config)

        print(f"\n=== 访问模式: {pattern} ===")
        print(f"数据大小: {data_size} 块 ({data_size * block_size / 1024:.0f} KB)")

        for level_stat in stats:
            print(f"  {level_stat['name']}: 访问={level_stat['accesses']}, "
                  f"未命中={level_stat['misses']}, "
                  f"命中率={level_stat['hit_rate']:.2%}")

        print(f"  总体命中率: {overall:.2%}")

    # 预取效果测试
    print("\n=== 预取效果测试 ===")
    block_size = 64
    cache_config_prefetch = [
        (64, block_size, "L1"),
        (256, block_size, "L2"),
    ]

    # 顺序访问（有预取）
    cache_prefetch = CacheHierarchy(cache_config_prefetch)
    # 模拟预取：每次访问后预取下一个块
    for i in range(0, 4096, 2):
        cache_prefetch.access(i)
        cache_prefetch.access(i + 1)

    stats, overall = cache_prefetch.get_stats()
    print(f"预取模式命中: {overall:.2%}")

    print("\n缓存优化策略:")
    print("  预取: 提前加载可能需要的数据")
    print("  替换策略: LRU、LFU、FIFO")
    print("  写策略: 写直达、写回")
    print("  多级缓存: 减少主存访问")

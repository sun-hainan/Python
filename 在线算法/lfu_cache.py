# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / lfu_cache

本文件实现 lfu_cache 相关的算法功能。
"""

from collections import defaultdict, OrderedDict


class LFUCache:
    """LFU 缓存"""

    def __init__(self, capacity):
        """
        初始化 LFU 缓存
        
        参数:
            capacity: 缓存容量
        """
        self.capacity = capacity
        # 缓存数据：{key: value}
        self.cache = {}
        # 使用计数：{key: frequency}
        self.freq = {}
        # 按频率组织的键：{frequency: OrderedDict(keys by recency)}
        self.freq_map = defaultdict(OrderedDict)
        # 最小频率（用于快速访问）
        self.min_freq = 0
        # 命中/未命中计数
        self.hits = 0
        self.misses = 0

    def _update_freq(self, key):
        """
        更新键的访问频率
        
        参数:
            key: 缓存键
        """
        f = self.freq[key]
        # 从当前频率列表移除
        del self.freq_map[f][key]
        
        # 如果当前频率列表为空且是 min_freq，更新 min_freq
        if not self.freq_map[f] and f == self.min_freq:
            # 找到新的最小频率
            if self.min_freq + 1 in self.freq_map:
                self.min_freq = f + 1
            else:
                # 如果没有更高的频率，设置为 1
                self.min_freq = 1
        
        # 增加频率
        new_freq = f + 1
        self.freq[key] = new_freq
        self.freq_map[new_freq][key] = None
        
        # 更新 min_freq
        if new_freq < self.min_freq:
            self.min_freq = new_freq

    def get(self, key):
        """
        获取缓存值
        
        参数:
            key: 缓存键
        返回:
            value: 缓存值，未命中返回 -1
        """
        if key in self.cache:
            self.hits += 1
            self._update_freq(key)
            return self.cache[key]
        else:
            self.misses += 1
            return -1

    def put(self, key, value):
        """
        放入缓存
        
        参数:
            key: 缓存键
            value: 缓存值
        """
        if self.capacity <= 0:
            return

        # 如果键已存在，更新值和频率
        if key in self.cache:
            self.cache[key] = value
            self._update_freq(key)
            return

        # 缓存已满，淘汰最少使用的
        if len(self.cache) >= self.capacity:
            # 获取最小频率对应的最旧键
            if self.freq_map[self.min_freq]:
                # 取出最旧的（最先插入的）
                evict_key, _ = self.freq_map[self.min_freq].popitem(last=False)
                del self.cache[evict_key]
                del self.freq[evict_key]
            else:
                # 理论上不应该发生，但为了安全
                self.min_freq += 1
                if self.freq_map[self.min_freq]:
                    evict_key, _ = self.freq_map[self.min_freq].popitem(last=False)
                    del self.cache[evict_key]
                    del self.freq[evict_key]

        # 插入新键
        self.cache[key] = value
        self.freq[key] = 1
        self.freq_map[1][key] = None
        self.min_freq = 1

    def remove(self, key):
        """
        手动删除缓存项
        
        参数:
            key: 要删除的键
        """
        if key not in self.cache:
            return
        
        f = self.freq[key]
        del self.freq_map[f][key]
        del self.cache[key]
        del self.freq[key]

    def get_stats(self):
        """获取统计信息"""
        total = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0,
            'size': len(self.cache)
        }

    def __len__(self):
        return len(self.cache)

    def __contains__(self, key):
        return key in self.cache

    def __str__(self):
        return f"LFUCache(capacity={self.capacity}, size={len(self.cache)})"


class LFUCacheOptimized:
    """
    优化的 LFU 缓存
    
    使用懒清理策略，避免频繁更新 min_freq
    """

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.freq = {}
        self.freq_map = defaultdict(OrderedDict)
        self.min_freq = 0
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key not in self.cache:
            self.misses += 1
            return -1
        
        self.hits += 1
        f = self.freq[key]
        new_freq = f + 1
        self.freq[key] = new_freq
        
        # 从旧频率列表移动到新频率列表
        del self.freq_map[f][key]
        self.freq_map[new_freq][key] = None
        
        return self.cache[key]

    def put(self, key, value):
        if self.capacity <= 0:
            return

        if key in self.cache:
            self.cache[key] = value
            self.get(key)  # 复用 get 的频率更新逻辑
            return

        # 检查容量
        if len(self.cache) >= self.capacity:
            # 淘汰最小频率的最旧项
            self._evict()

        self.cache[key] = value
        self.freq[key] = 1
        self.freq_map[1][key] = None
        self.min_freq = 1

    def _evict(self):
        """淘汰一个缓存项"""
        if not self.freq_map:
            return
        
        # 确保 min_freq 对应的列表存在且非空
        while self.min_freq not in self.freq_map or not self.freq_map[self.min_freq]:
            self.min_freq += 1
        
        # 淘汰最旧的项
        evict_key, _ = self.freq_map[self.min_freq].popitem(last=False)
        del self.cache[evict_key]
        del self.freq[evict_key]

    def get_stats(self):
        total = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0,
            'size': len(self.cache)
        }


if __name__ == "__main__":
    print("=== LFU 缓存测试 ===\n")

    # 测试基本功能
    print("--- 基本操作测试 ---")
    cache = LFUCache(capacity=3)
    
    operations = [
        ('put', 1, 1),
        ('put', 2, 2),
        ('put', 3, 3),
        ('get', 1),
        ('put', 4, 4),  # 应淘汰 key=2（使用次数最少）
        ('get', 2),
        ('get', 3),
        ('get', 4),
    ]
    
    for op in operations:
        if op[0] == 'put':
            cache.put(op[1], op[2])
            print(f"  put({op[1]}, {op[2]})")
        else:
            result = cache.get(op[1])
            print(f"  get({op[1]}) = {result}")
    
    print(f"\n统计: {cache.get_stats()}")

    # 频率增加测试
    print("\n--- 频率增加测试 ---")
    cache2 = LFUCache(capacity=2)
    cache2.put(1, 1)  # freq(1) = 1
    cache2.put(2, 2)  # freq(2) = 1
    cache2.get(1)     # freq(1) = 2
    cache2.put(3, 3)  # 应淘汰 freq=1 的 key=2
    print(f"  get(1) = {cache2.get(1)}")  # 2
    print(f"  get(2) = {cache2.get(2)}")  # -1
    print(f"  get(3) = {cache2.get(3)}")  # 3

    # 相同频率测试
    print("\n--- 相同频率测试（LRU 行为）---")
    cache3 = LFUCache(capacity=2)
    cache3.put(1, 1)
    cache3.put(2, 2)
    cache3.get(1)     # freq(1)=2, freq(2)=1
    cache3.put(3, 3)  # 应淘汰 freq=1 的 key=2
    print(f"  get(1) = {cache3.get(1)}")  # 1
    print(f"  get(2) = {cache3.get(2)}")  # -1
    print(f"  get(3) = {cache3.get(3)}")  # 3

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    import random
    
    cache_large = LFUCache(capacity(10000))
    n_operations = 100000
    
    start = time.time()
    for i in range(n_operations):
        if random.random() < 0.7:  # 70% 读
            cache_large.get(random.randint(0, 50000))
        else:  # 30% 写
            cache_large.put(random.randint(0, 50000), i)
    elapsed = time.time() - start
    
    stats = cache_large.get_stats()
    print(f"  操作数: {n_operations}")
    print(f"  耗时: {elapsed:.2f}s")
    print(f"  吞吐量: {n_operations/elapsed:.0f} ops/s")
    print(f"  命中率: {stats['hit_rate']:.2%}")

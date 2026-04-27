# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / k_lru

本文件实现 k_lru 相关的算法功能。
"""

from collections import OrderedDict


class KLRUCache:
    """
    K-LRU 缓存（候选区版本）
    
    结构：
    - 主缓存区（main）：大小为 capacity - k
    - 候选区（candidates）：大小为 k
    """

    def __init__(self, capacity, k=5):
        """
        初始化 K-LRU 缓存
        
        参数:
            capacity: 总容量
            k: 候选区大小
        """
        self.capacity = capacity
        self.k = min(k, capacity // 2) if capacity > 1 else 1
        self.main_cache = OrderedDict()  # 主缓存
        self.candidate_cache = OrderedDict()  # 候选区
        self.hits = 0
        self.misses = 0

    def _promote_candidates(self):
        """
        将候选区的所有项提升到主缓存
        
        触发时机：候选区满时
        """
        while self.candidate_cache:
            # 从候选区取出最旧的
            key, value = self.candidate_cache.popitem(last=False)
            
            # 如果主缓存满，先淘汰一项
            if len(self.main_cache) >= self.capacity - self.k:
                self.main_cache.popitem(last=False)
            
            # 放入主缓存（最常用位置）
            self.main_cache[key] = value

    def _touch_in_main(self, key):
        """在主缓存中访问一项（移到末尾）"""
        if key in self.main_cache:
            self.main_cache.move_to_end(key)
            return True
        return False

    def _touch_in_candidates(self, key):
        """在候选区中访问一项（移到末尾）"""
        if key in self.candidate_cache:
            self.candidate_cache.move_to_end(key)
            return True
        return False

    def get(self, key):
        """
        获取缓存值
        
        参数:
            key: 缓存键
        返回:
            value: 缓存值，未命中返回 -1
        """
        # 先在主缓存查找
        if key in self.main_cache:
            self.hits += 1
            self._touch_in_main(key)
            return self.main_cache[key]
        
        # 再在候选区查找
        if key in self.candidate_cache:
            self.hits += 1
            self._touch_in_candidates(key)
            return self.candidate_cache[key]
        
        self.misses += 1
        return -1

    def put(self, key, value):
        """
        放入缓存
        
        参数:
            key: 缓存键
            value: 缓存值
        """
        # 如果已存在，更新
        if key in self.main_cache:
            self.main_cache[key] = value
            self._touch_in_main(key)
            return
        if key in self.candidate_cache:
            self.candidate_cache[key] = value
            self._touch_in_candidates(key)
            return

        # 新键
        # 检查候选区是否满
        if len(self.candidate_cache) >= self.k:
            # 候选区满，提升候选区到主缓存
            self._promote_candidates()
        
        # 添加到候选区
        self.candidate_cache[key] = value

    def get_stats(self):
        """获取统计信息"""
        total = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0,
            'main_size': len(self.main_cache),
            'candidate_size': len(self.candidate_cache)
        }


class MultiLevelLRU:
    """
    多级 LRU 缓存（另一种 K-LRU）
    
    结构：L1 -> L2 -> L3 -> ... -> LK
    每层大小递减（通常是上一层的 1/k）
    """

    def __init__(self, total_capacity, num_levels=3, ratio=10):
        """
        初始化多级 LRU
        
        参数:
            total_capacity: 总容量
            num_levels: 层级数
            ratio: 每层与上一层容量的比例
        """
        self.num_levels = num_levels
        # 计算每层容量
        self.levels = []
        remaining = total_capacity
        for i in range(num_levels - 1):
            level_size = remaining // (ratio * (num_levels - i - 1))
            level_size = max(1, level_size)
            self.levels.append((level_size, OrderedDict()))
            remaining -= level_size
        self.levels.append((remaining, OrderedDict()))  # 最后一级
        
        self.hits = 0
        self.misses = 0

    def _find_level(self, key):
        """查找键所在的层级"""
        for i, (size, level) in enumerate(self.levels):
            if key in level:
                return i, level
        return None, None

    def get(self, key):
        """获取缓存值"""
        level_idx, level = self._find_level(key)
        
        if level is not None:
            self.hits += 1
            # 移到该层末尾
            level.move_to_end(key)
            
            # 如果不在最高层，尝试提升
            if level_idx > 0:
                self._promote(key, level_idx)
            
            return level[key]
        
        self.misses += 1
        return -1

    def _promote(self, key, from_level):
        """将项从低层提升到高层"""
        value = self.levels[from_level][0][1]
        
        # 从低层移除
        del self.levels[from_level][1][key]
        
        # 尝试放入高层
        for i in range(from_level):
            level_size, level = self.levels[i]
            if len(level) < level_size:
                level[key] = value
                return
        
        # 高层都满了，进行逐出
        self._evict_to_make_room(from_level, key, value)

    def _evict_to_make_room(self, from_level, key, value):
        """腾出空间"""
        # 从最高层开始逐出，直到能放入
        for i in range(self.num_levels - 1, -1, -1):
            level_size, level = self.levels[i]
            
            if len(level) < level_size:
                level[key] = value
                return
            
            # 淘汰最旧的
            evict_key, _ = level.popitem(last=False)
            
            if i > from_level:
                # 放入下一层
                self.levels[i + 1][1][evict_key] = None

    def put(self, key, value):
        """放入缓存"""
        level_idx, level = self._find_level(key)
        
        if level is not None:
            level[key] = value
            level.move_to_end(key)
            if level_idx > 0:
                self._promote(key, level_idx)
            return
        
        # 新键
        top_size, top_level = self.levels[0]
        
        # 检查顶层是否满
        if len(top_level) >= top_size:
            # 需要逐出
            self._evict_top(key, value)
        else:
            top_level[key] = value

    def _evict_top(self, key, value):
        """从顶层逐出"""
        # 逐出顶层最旧的
        for i in range(self.num_levels):
            level_size, level = self.levels[i]
            
            if len(level) > 0:
                evict_key, _ = level.popitem(last=False)
                
                if i < self.num_levels - 1:
                    # 放入下一层
                    self.levels[i + 1][1][evict_key] = None
                
                if i == 0:
                    break
        
        # 放入顶层
        self.levels[0][1][key] = value

    def get_stats(self):
        """获取统计信息"""
        total = self.hits + self.misses
        sizes = [len(level) for _, level in self.levels]
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0,
            'level_sizes': sizes
        }


if __name__ == "__main__":
    print("=== K-LRU 缓存测试 ===\n")

    # 测试候选区 K-LRU
    print("--- 候选区 K-LRU ---")
    cache = KLRUCache(capacity=5, k=2)
    
    print("操作序列:")
    ops = [
        ('put', 1, 1),
        ('put', 2, 2),
        ('put', 3, 3),
        ('get', 1),   # 命中
        ('put', 4, 4),  # 候选区满，候选区全部提升
        ('get', 2),   # 从提升区来
        ('get', 3),
        ('put', 5, 5),  # 触发再次提升
    ]
    
    for op in ops:
        if op[0] == 'put':
            cache.put(op[1], op[2])
            print(f"  put({op[1]}, {op[2]})")
        else:
            result = cache.get(op[1])
            print(f"  get({op[1]}) = {result}")
    
    stats = cache.get_stats()
    print(f"\n统计: 主缓存={stats['main_size']}, 候选区={stats['candidate_size']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")

    # 测试多层 LRU
    print("\n--- 多层 LRU ---")
    mcache = MultiLevelLRU(total_capacity=20, num_levels=3, ratio=5)
    
    print("操作序列:")
    for i in range(1, 11):
        mcache.put(i, i * 100)
        print(f"  put({i}, {i*100})")
    
    print("\n访问序列:")
    access = [1, 5, 8, 2, 1, 5, 10, 3]
    for key in access:
        result = mcache.get(key)
        print(f"  get({key}) = {result}")
    
    stats = mcache.get_stats()
    print(f"\n统计: 每层大小 {stats['level_sizes']}, 命中率: {stats['hit_rate']:.2%}")

    # 比较测试
    print("\n--- K-LRU vs 普通 LRU 比较 ---")
    import random
    
    # 普通 LRU
    lru_cache = OrderedDict()
    lru_hits, lru_misses = 0, 0
    
    # K-LRU
    klru_cache = KLRUCache(capacity=100, k=20)
    
    n = 10000
    keys = list(range(200))  # 200 个不同的键
    
    for _ in range(n):
        key = random.choice(keys)
        
        # LRU
        if key in lru_cache:
            lru_hits += 1
            lru_cache.move_to_end(key)
        else:
            lru_misses += 1
            if len(lru_cache) >= 100:
                lru_cache.popitem(last=False)
            lru_cache[key] = None
        
        # K-LRU
        klru_cache.get(key)
        if random.random() < 0.5:  # 50% 写入
            klru_cache.put(key, key)
    
    lru_total = lru_hits + lru_misses
    klru_stats = klru_cache.get_stats()
    
    print(f"操作数: {n}")
    print(f"LRU 命中率: {lru_hits/lru_total:.2%}")
    print(f"K-LRU 命中率: {klru_stats['hit_rate']:.2%}")

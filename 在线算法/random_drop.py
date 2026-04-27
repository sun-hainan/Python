# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / random_drop

本文件实现 random_drop 相关的算法功能。
"""

import random
from collections import deque


class RandomDropCache:
    """随机丢弃缓存"""

    def __init__(self, capacity):
        """
        初始化随机丢弃缓存
        
        参数:
            capacity: 缓存容量
        """
        self.capacity = capacity
        self.cache = {}
        self.access_order = []  # 用于随机选择

    def get(self, key):
        """
        获取值
        
        参数:
            key: 缓存键
        返回:
            value: 缓存值，未命中返回 None
        """
        if key in self.cache:
            return self.cache[key]
        return None

    def put(self, key, value):
        """
        放入缓存
        
        参数:
            key: 缓存键
            value: 缓存值
        """
        # 如果键已存在
        if key in self.cache:
            self.cache[key] = value
            return

        # 如果缓存满，随机丢弃一个
        if len(self.cache) >= self.capacity:
            drop_key = random.choice(list(self.cache.keys()))
            del self.cache[drop_key]

        self.cache[key] = value

    def __len__(self):
        return len(self.cache)

    def __contains__(self, key):
        return key in self.cache


class RandomDropBuffer:
    """随机丢弃缓冲区（FIFO 风格）"""

    def __init__(self, capacity):
        """
        初始化缓冲区
        
        参数:
            capacity: 缓冲区容量
        """
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        # 存储额外元数据
        self.metadata = {}

    def add(self, item, metadata=None):
        """
        添加项目到缓冲区
        
        参数:
            item: 要添加的项目
            metadata: 可选的元数据
        """
        if len(self.buffer) >= self.capacity:
            # 随机丢弃一个项目
            if len(self.buffer) > 0:
                idx = random.randint(0, len(self.buffer) - 1)
                self.buffer.remove(self.buffer[idx])
        
        self.buffer.append(item)
        if metadata:
            self.metadata[id(item)] = metadata

    def get_all(self):
        """获取所有项目"""
        return list(self.buffer)

    def sample(self, n=1):
        """
        随机采样项目
        
        参数:
            n: 采样数量
        返回:
            samples: 采样的项目列表
        """
        if n >= len(self.buffer):
            return list(self.buffer)
        return random.sample(list(self.buffer), n)


class RandomDropPriority:
    """
    带优先级的随机丢弃
    
    结合随机选择和优先级
    """

    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []  # [(key, value, priority), ...]

    def _get_weights(self):
        """计算每个项目的权重（基于优先级）"""
        weights = []
        for _, _, priority in self.items:
            # 优先级越高，权重越低（越不可能被丢弃）
            weight = 1.0 / (priority + 0.1)
            weights.append(weight)
        return weights

    def get(self, key):
        """获取值"""
        for k, v, p in self.items:
            if k == key:
                return v
        return None

    def put(self, key, value, priority=1):
        """
        放入项目
        
        参数:
            key: 键
            value: 值
            priority: 优先级（越高越重要，越不可能被丢弃）
        """
        # 检查是否已存在
        for i, (k, v, p) in enumerate(self.items):
            if k == key:
                self.items[i] = (key, value, priority)
                return

        # 如果满了，基于优先级概率丢弃
        if len(self.items) >= self.capacity:
            weights = self._get_weights()
            total_weight = sum(weights)
            probs = [w / total_weight for w in weights]
            
            r = random.random()
            cumsum = 0
            drop_idx = len(self.items) - 1
            
            for i, prob in enumerate(probs):
                cumsum += prob
                if r <= cumsum:
                    drop_idx = i
                    break
            
            del self.items[drop_idx]

        self.items.append((key, value, priority))

    def increment_priority(self, key):
        """增加键的优先级"""
        for i, (k, v, p) in enumerate(self.items):
            if k == key:
                self.items[i] = (k, v, p + 1)
                return


class ProbabilisticDrop:
    """
    概率丢弃算法
    
    每项有一个丢弃概率，基于某种分布
    """

    def __init__(self, capacity, drop_probability=0.1):
        """
        初始化
        
        参数:
            capacity: 容量
            drop_probability: 基础丢弃概率
        """
        self.capacity = capacity
        self.base_drop_prob = drop_probability
        self.items = {}
        self.hit_count = {}
        self.total_requests = 0

    def _compute_drop_prob(self, key):
        """
        计算键的丢弃概率
        
        访问频率越低，丢弃概率越高
        """
        if key not in self.hit_count or self.total_requests == 0:
            return self.base_drop_prob
        
        # 访问频率
        freq = self.hit_count[key] / self.total_requests
        # 频率越低，丢弃概率越高
        return 1.0 - freq

    def get(self, key):
        """获取"""
        self.total_requests += 1
        if key not in self.hit_count:
            self.hit_count[key] = 0
        self.hit_count[key] += 1
        
        return self.items.get(key)

    def put(self, key, value):
        """放入"""
        if key in self.items:
            self.items[key] = value
            return

        # 检查是否需要随机丢弃
        if len(self.items) >= self.capacity:
            # 以一定概率丢弃
            if random.random() < self.base_drop_prob:
                drop_key = random.choice(list(self.items.keys()))
                del self.items[drop_key]
                if drop_key in self.hit_count:
                    del self.hit_count[drop_key]

        self.items[key] = value
        self.hit_count[key] = 0

    def get_stats(self):
        """获取统计"""
        total = sum(self.hit_count.values())
        return {
            'unique_keys': len(self.items),
            'total_hits': total,
            'total_requests': self.total_requests
        }


class ReservoirSampler:
    """
    水库采样器
    
    从无限流中随机采样固定数量的元素
    使用 Random Drop 策略
    """

    def __init__(self, reservoir_size):
        """
        初始化水库采样器
        
        参数:
            reservoir_size: 水库大小（采样数量）
        """
        self.reservoir_size = reservoir_size
        self.reservoir = []
        self.n_seen = 0

    def add(self, item):
        """
        添加元素到水库
        
        参数:
            item: 要添加的元素
        """
        self.n_seen += 1
        
        if len(self.reservoir) < self.reservoir_size:
            self.reservoir.append(item)
        else:
            # 以概率 k/n 替换
            j = random.randint(0, self.n_seen - 1)
            if j < self.reservoir_size:
                self.reservoir[j] = item

    def get_sample(self):
        """获取当前样本"""
        return list(self.reservoir)

    def size(self):
        """获取已看到的元素数"""
        return self.n_seen


class TimedRandomDrop:
    """
    带时间的随机丢弃
    
    基于时间的随机丢弃，每隔一段时间重新随机化
    """

    def __init__(self, capacity, reset_interval=1000):
        """
        初始化
        
        参数:
            capacity: 容量
            reset_interval: 重置间隔（操作数）
        """
        self.capacity = capacity
        self.reset_interval = reset_interval
        self.items = {}
        self.operation_count = 0

    def _maybe_reset(self):
        """可能重置（模拟时间过期）"""
        self.operation_count += 1
        if self.operation_count >= self.reset_interval:
            # 以一定概率重置
            if random.random() < 0.5:
                # 保留一半，随机丢弃另一半
                keep_count = self.capacity // 2
                keys = list(self.items.keys())
                random.shuffle(keys)
                for i, k in enumerate(keys):
                    if i >= keep_count:
                        del self.items[k]
            self.operation_count = 0

    def get(self, key):
        """获取"""
        self._maybe_reset()
        return self.items.get(key)

    def put(self, key, value):
        """放入"""
        self._maybe_reset()
        
        if key in self.items:
            self.items[key] = value
            return

        if len(self.items) >= self.capacity:
            drop_key = random.choice(list(self.items.keys()))
            del self.items[drop_key]

        self.items[key] = value


if __name__ == "__main__":
    print("=== Random Drop 算法测试 ===\n")

    # 基本缓存测试
    print("--- 随机丢弃缓存 ---")
    cache = RandomDropCache(capacity=3)
    
    operations = [
        ('put', 1, 'a'),
        ('put', 2, 'b'),
        ('put', 3, 'c'),
        ('get', 1),
        ('put', 4, 'd'),  # 可能丢弃一个
        ('get', 2),
    ]
    
    for op in operations:
        if op[0] == 'put':
            cache.put(op[1], op[2])
            print(f"  put({op[1]}, {op[2]})")
        else:
            result = cache.get(op[1])
            print(f"  get({op[1]}) = {result}")

    # 带优先级测试
    print("\n--- 带优先级随机丢弃 ---")
    pcache = RandomDropPriority(capacity=3)
    
    pcache.put('a', 1, priority=1)
    pcache.put('b', 2, priority=2)
    pcache.put('c', 3, priority=1)
    pcache.put('d', 4, priority=3)  # 高优先级，不容易被丢弃
    
    print(f"  a={pcache.get('a')}, b={pcache.get('b')}, "
          f"c={pcache.get('c')}, d={pcache.get('d')}")

    # 水库采样测试
    print("\n--- 水库采样 ---")
    sampler = ReservoirSampler(reservoir_size=5)
    
    for i in range(100):
        sampler.add(i)
    
    print(f"  看到元素数: {sampler.size()}")
    print(f"  样本: {sorted(sampler.get_sample())}")

    # 概率丢弃测试
    print("\n--- 概率丢弃 ---")
    pdrop = ProbabilisticDrop(capacity=5, drop_probability=0.2)
    
    for i in range(50):
        pdrop.put(f'key_{i % 20}', f'value_{i}')
    
    for i in range(10):
        pdrop.get(f'key_{i}')
    
    stats = pdrop.get_stats()
    print(f"  唯一键: {stats['unique_keys']}, "
          f"总命中: {stats['total_hits']}, 总请求: {stats['total_requests']}")

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    
    # 随机丢弃缓存
    cache = RandomDropCache(capacity=1000)
    n = 100000
    
    start = time.time()
    for i in range(n):
        key = random.randint(0, 2000)
        if random.random() < 0.7:  # 70% 读
            cache.get(key)
        else:  # 30% 写
            cache.put(key, i)
    elapsed = time.time() - start
    print(f"  随机丢弃缓存 {n} 次操作: {elapsed:.3f}s ({n/elapsed:.0f} ops/s)")
    
    # 水库采样
    sampler = ReservoirSampler(reservoir_size=100)
    start = time.time()
    for i in range(n):
        sampler.add(i)
    elapsed = time.time() - start
    print(f"  水库采样 {n} 次: {elapsed:.3f}s ({n/elapsed:.0f} ops/s)")

    # 比较测试
    print("\n--- 命中率比较 ---")
    import random
    
    def test_cache(cache_class, name, n_ops=10000):
        """测试缓存命中率"""
        cache = cache_class(capacity=100)
        hits = 0
        
        # 模拟访问模式：一些键频繁访问
        keys = list(range(50)) * 2 + list(range(200))
        random.shuffle(keys)
        
        for key in keys[:n_ops]:
            if random.random() < 0.8:  # 80% 读
                if cache.get(key) is not None:
                    hits += 1
            else:  # 20% 写
                cache.put(key, key)
        
        return hits / n_ops
        
        for _ in range(n_ops):
            key = random.randint(0, 99)
            if cache.get(key) is not None:
                hits += 1
            else:
                cache.put(key, key)
        
        return hits / n_ops
    
    # Random Drop vs LRU
    class SimpleLRU:
        def __init__(self, capacity):
            self.capacity = capacity
            self.cache = {}
            self.order = []
        
        def get(self, key):
            if key in self.cache:
                self.order.remove(key)
                self.order.append(key)
                return self.cache[key]
            return None
        
        def put(self, key, value):
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.capacity:
                oldest = self.order.pop(0)
                del self.cache[oldest]
            self.cache[key] = value
            self.order.append(key)
    
    # 模拟访问模式：80-20 规则
    random.seed(42)
    
    print("  80-20 访问模式（热门键占 80% 流量）:")
    print(f"    Random Drop 命中率: {test_cache(RandomDropCache, 'RandomDrop', 10000):.2%}")
    print(f"    Simple LRU 命中率: {test_cache(SimpleLRU, 'LRU', 10000):.2%}")

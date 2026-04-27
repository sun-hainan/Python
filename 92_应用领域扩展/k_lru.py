# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / k_lru



本文件实现 k_lru 相关的算法功能。

"""



from collections import OrderedDict

from dataclasses import dataclass

from typing import Any, Optional, List





@dataclass

class KLRU:

    """

    K-LRU缓存

    

    K个缓存层级，每层有不同的淘汰策略

    """

    

    cache_size: int  # 总缓存大小

    k: int = 2  # 层级数

    

    def __post_init__(self):

        self.level_sizes = [self.cache_size // self.k] * self.k

        self.levels: List[OrderedDict] = [OrderedDict() for _ in range(self.k)]

        self.access_count = [0] * self.k

        self.hit_count = 0

        self.miss_count = 0

    

    def _promote(self, key: str, from_level: int):

        """

        将项从低级缓存提升到高级缓存

        

        Args:

            key: 缓存键

            from_level: 源层级

        """

        if from_level >= self.k - 1:

            return  # 已在最高层

        

        # 获取值

        value = self.levels[from_level].pop(key)

        

        # 插入到上一级

        target_level = from_level + 1

        

        # 如果目标层已满，先淘汰一个

        if len(self.levels[target_level]) >= self.level_sizes[target_level]:

            self._evict_from(target_level)

        

        self.levels[target_level][key] = value

    

    def _demote(self, key: str, from_level: int):

        """

        将项从高级缓存降级到低级缓存

        

        Args:

            key: 缓存键

            from_level: 源层级

        """

        if from_level <= 0:

            # 已在最低层，直接丢弃

            return

        

        # 获取值

        value = self.levels[from_level].pop(key)

        

        # 插入到下一级

        target_level = from_level - 1

        

        # 如果目标层已满，先淘汰一个

        if len(self.levels[target_level]) >= self.level_sizes[target_level]:

            self._evict_from(target_level)

        

        self.levels[target_level][key] = value

    

    def _evict_from(self, level: int):

        """

        从指定层级淘汰一个元素

        

        Args:

            level: 层级

        """

        if not self.levels[level]:

            return

        

        # LRU淘汰

        key, _ = self.levels[level].popitem(last=False)

        

        # 降级到下一层（如果存在）

        if level > 0:

            self._demote(key, level)

    

    def _insert_to_level(self, key: str, value: Any, level: int):

        """

        插入到指定层级

        

        Args:

            key: 缓存键

            value: 缓存值

            level: 目标层级

        """

        # 如果该层已有，移除

        for l in range(self.k):

            if key in self.levels[l]:

                del self.levels[l][key]

        

        # 如果层已满，先淘汰

        if len(self.levels[level]) >= self.level_sizes[level]:

            self._evict_from(level)

        

        self.levels[level][key] = value

    

    def get(self, key: str) -> Optional[Any]:

        """

        获取缓存值

        

        Args:

            key: 缓存键

        

        Returns:

            缓存值或None

        """

        # 从最高层开始查找

        for level in range(self.k - 1, -1, -1):

            if key in self.levels[level]:

                value = self.levels[level][key]

                

                # 记录命中

                self.access_count[level] += 1

                

                if level < self.k - 1:

                    # 提升到更高层

                    self._promote(key, level)

                else:

                    # 最高层：移动到末尾（最新）

                    self.levels[level].move_to_end(key)

                

                self.hit_count += 1

                return value

        

        self.miss_count += 1

        return None

    

    def put(self, key: str, value: Any):

        """

        放入缓存

        

        Args:

            key: 缓存键

            value: 缓存值

        """

        # 如果已存在，更新并提升

        for level in range(self.k - 1, -1, -1):

            if key in self.levels[level]:

                self.levels[level][key] = value

                if level < self.k - 1:

                    self._promote(key, level)

                return

        

        # 新插入：放入最高层

        self._insert_to_level(key, value, self.k - 1)

    

    def evict(self) -> Optional[str]:

        """

        主动淘汰

        

        Returns:

            被淘汰的键

        """

        # 从最底层淘汰

        for level in range(0, self.k):

            if self.levels[level]:

                key, _ = self.levels[level].popitem(last=False)

                return key

        return None

    

    def stats(self) -> dict:

        """获取统计信息"""

        total_items = sum(len(l) for l in self.levels)

        return {

            'total_items': total_items,

            'items_per_level': [len(l) for l in self.levels],

            'access_per_level': self.access_count.copy(),

            'hit_count': self.hit_count,

            'miss_count': self.miss_count,

            'hit_rate': self.hit_count / (self.hit_count + self.miss_count) 

                       if self.hit_count + self.miss_count > 0 else 0

        }





class TwoQueueLRU:

    """

    TwoQueue LRU (K=2的K-LRU)

    

    L1: 使用FIFO，适合短期热点

    L2: 使用LRU，适合长期热点

    """

    

    def __init__(self, cache_size: int, l1_ratio: float = 0.5):

        self.l1_size = int(cache_size * l1_ratio)

        self.l2_size = cache_size - self.l1_size

        

        self.l1 = OrderedDict()  # FIFO队列

        self.l2 = OrderedDict()  # LRU队列

        

        self.hit_count = 0

        self.miss_count = 0

    

    def get(self, key: str) -> Optional[Any]:

        """获取缓存"""

        # 优先检查L2（LRU）

        if key in self.l2:

            self.l2.move_to_end(key)

            self.hit_count += 1

            return self.l2[key]

        

        # 检查L1（FIFO）

        if key in self.l1:

            # 从L1移到L2

            value = self.l1.pop(key)

            self.l2[key] = value

            self.hit_count += 1

            return value

        

        self.miss_count += 1

        return None

    

    def put(self, key: str, value: Any):

        """放入缓存"""

        # 如果已在L2，更新

        if key in self.l2:

            self.l2[key] = value

            self.l2.move_to_end(key)

            return

        

        # 如果已在L1，更新并移到L2

        if key in self.l1:

            self.l1.pop(key)

            self.l2[key] = value

            return

        

        # 新键：先放入L1

        self.l1[key] = value

        

        # L1满了，移到L2

        if len(self.l1) > self.l1_size:

            oldest_key = next(iter(self.l1))

            self.l1.pop(oldest_key)

            

            # L2满了，淘汰最旧的

            if len(self.l2) >= self.l2_size:

                self.l2.pop(oldest=False)

            

            self.l2[oldest_key] = True  # 只保留键





class ARCLRU:

    """

    ARC (Adaptive Replacement Cache) 简化实现

    

    ARC结合了四种缓存：

    - T1: 最近使用的（MRU移动到T2）

    - T2: 频繁使用的

    - B1: 已淘汰的T1

    - B2: 已淘汰的T2

    

    动态调整T1/T2大小

    """

    

    def __init__(self, cache_size: int):

        self.cache_size = cache_size

        

        self.t1 = OrderedDict()  # 热点

        self.t2 = OrderedDict()  # 频繁

        self.b1 = OrderedDict()  # 从T1淘汰的

        self.b2 = OrderedDict()  # 从T2淘汰的

        

        self.p = 0  # T1的目标大小

    

    def get(self, key: str) -> Optional[Any]:

        """获取缓存"""

        # T1命中

        if key in self.t1:

            self.t1.move_to_end(key)

            return self.t1[key]

        

        # T2命中

        if key in self.t2:

            self.t2.move_to_end(key)

            return self.t2[key]

        

        return None

    

    def put(self, key: str, value: Any):

        """放入缓存"""

        total = len(self.t1) + len(self.t2)

        

        # 新键

        if key not in self.t1 and key not in self.t2:

            # 缓存满时调整

            if total >= self.cache_size:

                self._replace(key)

            

            self.t1[key] = value

    

    def _replace(self, replace_key: str):

        """替换"""

        if len(self.t1) > 0 and (len(self.t1) > self.p or 

            (replace_key in self.b1 and len(self.t1) == self.p)):

            # 从T1淘汰到B1

            oldest = next(iter(self.t1))

            self.b1[oldest] = self.t1.pop(oldest)

        else:

            # 从T2淘汰到B2

            if self.t2:

                oldest = next(iter(self.t2))

                self.b2[oldest] = self.t2.pop(oldest)





def demo_k_lru():

    """演示K-LRU"""

    print("=== K-LRU缓存演示 ===\n")

    

    cache = KLRU(cache_size=10, k=3)

    

    # 模拟访问

    accesses = [

        ('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5),

        ('f', 6), ('g', 7), ('a', 8), ('h', 9), ('i', 10),

        ('a', 11), ('j', 12), ('b', 13), ('k', 14)

    ]

    

    print("访问序列: ", end="")

    for key, val in accesses:

        cache.put(key, val)

        print(key, end=" ")

    print()

    

    stats = cache.stats()

    print(f"\n最终状态:")

    print(f"  每层元素数: {stats['items_per_level']}")

    print(f"  每层访问: {stats['access_per_level']}")

    print(f"  命中率: {stats['hit_rate']:.2%}")





def demo_two_queue():

    """演示TwoQueue LRU"""

    print("\n=== TwoQueue LRU演示 ===\n")

    

    cache = TwoQueueLRU(cache_size=6, l1_ratio=0.5)

    

    print("TwoQueue配置:")

    print(f"  L1 (FIFO) 大小: {cache.l1_size}")

    print(f"  L2 (LRU) 大小: {cache.l2_size}")

    print()

    

    # 访问序列

    accesses = ['a', 'b', 'c', 'd', 'a', 'e', 'f', 'g', 'a', 'h']

    

    print("访问序列:", ' '.join(accesses))

    print()

    

    for key in accesses:

        cache.get(key)

    

    print(f"最终状态:")

    print(f"  L1: {list(cache.l1.keys())}")

    print(f"  L2: {list(cache.l2.keys())}")





def demo_arc():

    """演示ARC"""

    print("\n=== ARC演示 ===\n")

    

    cache = ARCLRU(cache_size=5)

    

    accesses = ['a', 'b', 'c', 'd', 'a', 'e', 'f', 'g', 'a', 'h', 'b', 'i']

    

    print("访问序列:", ' '.join(accesses))

    print()

    

    for key in accesses:

        cache.get(key)

    

    print(f"最终状态:")

    print(f"  T1 (热点): {list(cache.t1.keys())}")

    print(f"  T2 (频繁): {list(cache.t2.keys())}")

    print(f"  B1 (已淘汰): {list(cache.b1.keys())}")

    print(f"  B2 (已淘汰): {list(cache.b2.keys())}")





def demo_k_lru_probability():

    """概率分析"""

    print("\n=== K-LRU概率分析 ===\n")

    

    print("K-LRU的缓存效率取决于:")

    print("  1. 访问模式（访问频率、局部性）")

    print("  2. K值的选择")

    print("  3. 各层大小的分配")

    print()

    

    print("分层效果:")

    print("  L1 (最热): 通常包含少量极高频访问的项")

    print("  L2: 中等频率项")

    print("  ... : 递降频率")

    print()

    

    print("优势:")

    print("  1. 防止突发热点污染缓存")

    print("  2. 更好地适应访问模式变化")

    print("  3. 比简单LRU更节能（高层缓存小）")





if __name__ == "__main__":

    print("=" * 60)

    print("K-LRU 缓存算法实现")

    print("=" * 60)

    

    # K-LRU演示

    demo_k_lru()

    

    # TwoQueue演示

    demo_two_queue()

    

    # ARC演示

    demo_arc()

    

    # 概率分析

    demo_k_lru_probability()

    

    print("\n" + "=" * 60)

    print("缓存策略对比:")

    print("=" * 60)

    print("""

| 策略     | 优点                     | 缺点              |

|---------|--------------------------|-------------------|

| LRU     | 简单，对热点友好          | 对突发访问不友好  |

| K-LRU   | 分层保护，适应性更好      | 复杂度稍高        |

| TwoQueue| 区分短期/长期热点         | 需要维护两个队列  |

| ARC     | 自适应，性能好            | 实现复杂          |

| LFU     | 对高频访问最优            | 冷启动问题        |

| FIFO    | 极其简单                  | 不考虑访问模式    |

""")


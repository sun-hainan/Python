# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / cache_replacement

本文件实现 cache_replacement 相关的算法功能。
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import random
import heapq


@dataclass
class CacheLine:
    """缓存行"""
    tag: int
    valid: bool = False
    data: any = None


class CacheReplacementPolicy:
    """缓存替换策略基类"""

    def __init__(self, num_sets: int, associativity: int):
        self.num_sets = num_sets
        self.associativity = associativity

    def get_replacement_candidate(self, set_idx: int) -> int:
        """返回应被替换的行索引"""
        raise NotImplementedError

    def update(self, set_idx: int, way_idx: int):
        """更新访问状态"""
        raise NotImplementedError


class LRUReplacementPolicy(CacheReplacementPolicy):
    """
    LRU (Least Recently Used) 替换策略

    使用访问时间戳追踪每行的最近使用时间，
    替换时选择最久未使用的行。

    实现：
    - 为每个set维护一个访问顺序列表
    - 每次访问时更新列表顺序
    """

    def __init__(self, num_sets: int, associativity: int):
        super().__init__(num_sets, associativity)
        # 每个set的访问历史（way索引列表，最近使用的在末尾）
        self.access_history: Dict[int, List[int]] = {
            i: list(range(associativity)) for i in range(num_sets)
        }

    def get_replacement_candidate(self, set_idx: int) -> int:
        """返回LRU行的way索引"""
        history = self.access_history[set_idx]
        # LRU是列表第一个（最久未使用）
        return history[0]

    def update(self, set_idx: int, way_idx: int):
        """更新访问状态：将访问的行移到列表末尾"""
        history = self.access_history[set_idx]
        if way_idx in history:
            history.remove(way_idx)
        history.append(way_idx)


class PLRUReplacementPolicy(CacheReplacementPolicy):
    """
    PLRU (Pseudo-LRU) 替换策略

    树形LRU的近似实现，开销更小。
    对于8路组相联，使用7个二进制位追踪。

    实现：
    - 每个set有一个树结构
    - 每次访问将路径上的节点标记为"未访问"
    - 替换时选择标记为"未访问"的叶节点
    """

    def __init__(self, num_sets: int, associativity: int):
        super().__init__(num_sets, associativity)
        # 树节点状态：0或1，表示应该选择左子树还是右子树
        self.tree_bits: Dict[int, List[int]] = {}
        for s in range(num_sets):
            # 对于N路关联，需要N-1个位
            num_bits = associativity - 1
            self.tree_bits[s] = [0] * num_bits

    def _get_leaf_index(self, set_idx: int, tree_pos: int = 0) -> int:
        """递归找到应该替换的叶节点索引"""
        bits = self.tree_bits[set_idx]
        n = self.associativity

        # 如果是叶节点
        if tree_pos >= n - 1:
            return tree_pos - (n - 1)

        # 根据当前位决定遍历方向
        if bits[tree_pos] == 0:
            # 选择左子树
            return self._get_leaf_index(set_idx, 2 * tree_pos + 1)
        else:
            # 选择右子树
            return self._get_leaf_index(set_idx, 2 * tree_pos + 2)

    def get_replacement_candidate(self, set_idx: int) -> int:
        """返回PLRU候选行"""
        return self._get_leaf_index(set_idx)

    def update(self, set_idx: int, way_idx: int):
        """更新PLRU树"""
        bits = self.tree_bits[set_idx]
        n = self.associativity

        # 从叶节点向上更新
        pos = way_idx + n - 1

        while pos > 0:
            parent = (pos - 1) // 2
            # 判断当前节点是左子还是右子
            if pos == 2 * parent + 1:
                # 左子节点，标记为选择右子树
                bits[parent] = 1
            else:
                # 右子节点，标记为选择左子树
                bits[parent] = 0
            pos = parent


class FIFOReplacementPolicy(CacheReplacementPolicy):
    """
    FIFO (First In First Out) 替换策略

    驱逐最早进入缓存的行。
    简单但可能性能不佳（Belady异常）。
    """

    def __init__(self, num_sets: int, associativity: int):
        super().__init__(num_sets, associativity)
        # 每个set的FIFO队列（way索引）
        self.fifo_queues: Dict[int, List[int]] = {
            i: list(range(associativity)) for i in range(num_sets)
        }

    def get_replacement_candidate(self, set_idx: int) -> int:
        """返回FIFO队列队首（最老的行）"""
        queue = self.fifo_queues[set_idx]
        return queue[0]

    def update(self, set_idx: int, way_idx: int):
        """更新FIFO：将替换出的行移到最后"""
        queue = self.fifo_queues[set_idx]
        # 队首出队，插入队尾
        if way_idx == queue[0]:
            queue.pop(0)
            queue.append(way_idx)


class RandomReplacementPolicy(CacheReplacementPolicy):
    """
    Random 替换策略

    随机选择一个行替换。
    实现最简单，在某些场景下性能意外地好。
    """

    def __init__(self, num_sets: int, associativity: int):
        super().__init__(num_sets, associativity)

    def get_replacement_candidate(self, set_idx: int) -> int:
        """随机返回way索引"""
        return random.randint(0, self.associativity - 1)

    def update(self, set_idx: int, way_idx: int):
        """随机策略不需要更新"""
        pass


class BeladyOptimalPolicy(CacheReplacementPolicy):
    """
    Belady 最优替换策略 (OPT/OPTIMAL)

    驱逐将来最长时间不使用的行。
    这需要预知未来访问序列，因此在实际中不可实现，
    但可以作为理论最优来评估其他策略。

    实现方式：
    - 记录每个way下次被访问的距离
    - 替换距离最大的（最久不使用）
    """

    def __init__(self, num_sets: int, associativity: int):
        super().__init__(num_sets, associativity)
        # 访问历史记录
        self.access_records: Dict[int, Dict[int, int]] = {}

    def set_future_accesses(self, set_idx: int, future_accesses: Dict[int, List[int]]):
        """
        设置每个way的未来访问序列
        param set_idx: set索引
        param future_accesses: {way_idx: [access_positions...]}
        """
        self.access_records[set_idx] = future_accesses

    def get_replacement_candidate(self, set_idx: int) -> int:
        """返回将来最久不用的行"""
        if set_idx not in self.access_records:
            return 0

        records = self.access_records[set_idx]
        max_distance = -1
        victim = 0

        for way_idx, accesses in records.items():
            if not accesses:
                # 永远不会再被访问，优先替换
                return way_idx
            # 下次访问距离
            distance = accesses[0]
            if distance > max_distance:
                max_distance = distance
                victim = way_idx

        return victim

    def update(self, set_idx: int, way_idx: int):
        """使用后移除已访问的记录"""
        if set_idx in self.access_records:
            records = self.access_records[set_idx]
            if way_idx in records and records[way_idx]:
                records[way_idx].pop(0)


class CacheSimulator:
    """缓存模拟器，支持多种替换策略"""

    def __init__(self, num_sets: int, associativity: int, line_size: int = 64,
                 replacement_policy: str = "LRU"):
        self.num_sets = num_sets
        self.associativity = associativity
        self.line_size = line_size
        self.replacement_policy_name = replacement_policy

        # 缓存数据
        self.cache_data: Dict[int, List[Optional[CacheLine]]] = {
            i: [None] * associativity for i in range(num_sets)
        }

        # 替换策略
        if replacement_policy == "LRU":
            self.policy = LRUReplacementPolicy(num_sets, associativity)
        elif replacement_policy == "PLRU":
            self.policy = PLRUReplacementPolicy(num_sets, associativity)
        elif replacement_policy == "FIFO":
            self.policy = FIFOReplacementPolicy(num_sets, associativity)
        elif replacement_policy == "RANDOM":
            self.policy = RandomReplacementPolicy(num_sets, associativity)
        elif replacement_policy == "BELADY":
            self.policy = BeladyOptimalPolicy(num_sets, associativity)
        else:
            self.policy = LRUReplacementPolicy(num_sets, associativity)

        # 统计
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _get_set_index(self, address: int) -> int:
        return (address // self.line_size) % self.num_sets

    def _get_tag(self, address: int) -> int:
        return address // (self.line_size * self.num_sets)

    def access(self, address: int) -> bool:
        """
        访问缓存
        return: True表示命中，False表示未命中
        """
        set_idx = self._get_set_index(address)
        tag = self._get_tag(address)

        # 检查命中
        for way_idx, line in enumerate(self.cache_data[set_idx]):
            if line and line.tag == tag and line.valid:
                # 命中
                self.hits += 1
                self.policy.update(set_idx, way_idx)
                return True

        # 未命中
        self.misses += 1

        # 找空位
        for way_idx, line in enumerate(self.cache_data[set_idx]):
            if line is None or not line.valid:
                # 有空位
                self.cache_data[set_idx][way_idx] = CacheLine(tag=tag, valid=True)
                self.policy.update(set_idx, way_idx)
                return False

        # 需要替换
        victim_way = self.policy.get_replacement_candidate(set_idx)
        self.cache_data[set_idx][victim_way] = CacheLine(tag=tag, valid=True)
        self.policy.update(set_idx, victim_way)
        self.evictions += 1
        return False

    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0


def simulate_cache_replacement():
    """
    模拟不同缓存替换策略
    """
    print("=" * 60)
    print("缓存替换策略模拟")
    print("=" * 60)

    # 测试序列
    addresses = [
        0x1000, 0x1100, 0x1200, 0x1300,  # 填充set 0
        0x1000, 0x1100, 0x1400,           # 触发替换
        0x1500, 0x1600, 0x1700,           # 更多替换
        0x1000, 0x1300, 0x1500,           # 重复访问
    ]

    policies = ["LRU", "FIFO", "RANDOM"]

    print("\n测试地址序列:", [hex(a) for a in addresses])
    print(f"缓存配置: 1 set, 4 ways, line_size=64")
    print("-" * 60)

    for policy_name in policies:
        cache = CacheSimulator(num_sets=1, associativity=4, line_size=64,
                               replacement_policy=policy_name)

        print(f"\n策略: {policy_name}")
        for addr in addresses:
            hit = cache.access(addr)
            print(f"  访问 0x{addr:04X}: {'命中' if hit else '未命中'}")

        print(f"  最终命中率: {cache.get_hit_rate() * 100:.1f}%")
        print(f"  替换次数: {cache.evictions}")

    # 演示Belady最优策略
    print("\n" + "=" * 60)
    print("Belady 最优策略")
    print("=" * 60)

    # 为Belady设置未来访问信息
    belady = BeladyOptimalPolicy(num_sets=1, associativity=4)

    # 模拟：way0将被访问，way1将永远不再访问，way2很快会被访问，way3很快会被访问
    future = {
        0: [5, 10],   # way0在第5和10次访问时被访问
        1: [],         # way1永远不再访问
        2: [1],         # way2在第1次访问时被访问
        3: [2],         # way3在第2次访问时被访问
    }
    belady.set_future_accesses(0, future)

    # 替换选择
    victim = belady.get_replacement_candidate(0)
    print(f"Belady选择替换: way{victim} (因为它将来最久不会被访问)")


if __name__ == "__main__":
    simulate_cache_replacement()

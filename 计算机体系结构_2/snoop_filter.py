# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / snoop_filter

本文件实现 snoop_filter 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto


class Cache_State(Enum):
    """缓存行状态（MESI简化）"""
    INVALID = 0
    SHARED = 1      # 共享/干净
    MODIFIED = 2    # 修改/脏
    EXCLUSIVE = 3   # 独占/干净


class Request_Type(Enum):
    """总线请求类型"""
    READ = auto()           # 读请求
    WRITE = auto()          # 写请求
    READ_FOR_OWN = auto()   # Read-for-Ownership（获取独占权）
    WRITE_BACK = auto()     # 回写


@dataclass
class Snoop_Filter_Entry:
    """Snoop过滤器条目"""
    tag: int = 0                # 地址标签
    state: Cache_State = Cache_State.INVALID
    sharers: Set[int] = field(default_factory=set)  # 共享者集合（核心ID）
    owner: Optional[int] = None  # 当前持有者（如果是MODIFIED）


class Snoop_Filter:
    """Snoop过滤器"""
    def __init__(self, num_entries: int = 256):
        self.num_entries = num_entries
        self.index_mask = num_entries - 1
        self.entries: Dict[int, Snoop_Filter_Entry] = {}
        # 统计
        self.hits: int = 0
        self.misses: int = 0
        self.filtered_snoops: int = 0  # 被过滤的snoop请求
        self.total_snoops: int = 0


    def _get_index(self, addr: int) -> int:
        """从地址计算索引"""
        return (addr >> 6) & self.index_mask  # 假设64字节缓存行


    def lookup(self, addr: int) -> Tuple[bool, Optional[Snoop_Filter_Entry]]:
        """查找地址是否在过滤器中"""
        index = self._get_index(addr)
        tag = addr >> (6 + 8)  # 简化标签
        if index in self.entries:
            entry = self.entries[index]
            if entry.tag == tag and entry.state != Cache_State.INVALID:
                self.hits += 1
                return True, entry
        self.misses += 1
        return False, None


    def allocate(self, addr: int, core_id: int, state: Cache_State):
        """分配新条目"""
        index = self._get_index(addr)
        tag = addr >> (6 + 8)
        entry = Snoop_Filter_Entry(tag=tag, state=state)
        if state in [Cache_State.SHARED, Cache_State.EXCLUSIVE]:
            entry.sharers.add(core_id)
        elif state == Cache_State.MODIFIED:
            entry.owner = core_id
        self.entries[index] = entry


    def update_on_read(self, addr: int, core_id: int) -> Cache_State:
        """处理读请求，更新状态"""
        hit, entry = self.lookup(addr)
        if not hit:
            # 未命中，分配新条目，状态变为SHARED
            self.allocate(addr, core_id, Cache_State.SHARED)
            return Cache_State.INVALID  # 需要从内存/总线获取
        # 命中，处理请求
        if entry.state == Cache_State.MODIFIED:
            # 需要从owner获取数据
            entry.owner = None
            entry.state = Cache_State.SHARED
            entry.sharers.add(core_id)
            return Cache_State.MODIFIED
        elif entry.state == Cache_State.EXCLUSIVE:
            # 变为SHARED
            entry.state = Cache_State.SHARED
            entry.sharers.add(core_id)
            return Cache_State.EXCLUSIVE
        elif entry.state == Cache_State.SHARED:
            # 已在共享状态
            entry.sharers.add(core_id)
            return Cache_State.SHARED
        return Cache_State.INVALID


    def update_on_write(self, addr: int, core_id: int) -> Tuple[Cache_State, List[int]]:
        """
        处理写请求，返回需要snoop的核心列表
        """
        hit, entry = self.lookup(addr)
        if not hit:
            # 未命中，需要获取独占权
            self.allocate(addr, core_id, Cache_State.EXCLUSIVE)
            return Cache_State.INVALID, []
        # 命中，需要snoop其他核心
        snoop_targets = []
        if entry.state == Cache_State.SHARED:
            # 需要invalidate所有sharer
            snoop_targets = list(entry.sharers)
            entry.sharers.clear()
            entry.sharers.add(core_id)
            entry.state = Cache_State.EXCLUSIVE
            return Cache_State.SHARED, snoop_targets
        elif entry.state == Cache_State.EXCLUSIVE:
            # 只snoop一个核心
            if entry.sharers:
                snoop_targets = [next(iter(entry.sharers))]
            entry.sharers.clear()
            entry.sharers.add(core_id)
            entry.state = Cache_State.EXCLUSIVE
            return Cache_State.EXCLUSIVE, snoop_targets
        elif entry.state == Cache_State.MODIFIED:
            # 需要将脏数据写回
            snoop_targets = [entry.owner] if entry.owner else []
            entry.owner = core_id
            return Cache_State.MODIFIED, snoop_targets
        return Cache_State.INVALID, []


    def invalidate(self, addr: int, core_id: int):
        """invalidate一个缓存行"""
        hit, entry = self.lookup(addr)
        if hit:
            if entry.state == Cache_State.SHARED:
                entry.sharers.discard(core_id)
                if not entry.sharers:
                    entry.state = Cache_State.INVALID
            elif entry.state == Cache_State.EXCLUSIVE:
                if core_id in entry.sharers:
                    entry.sharers.clear()
                    entry.state = Cache_State.INVALID
            elif entry.state == Cache_State.MODIFIED and entry.owner == core_id:
                entry.state = Cache_State.INVALID
                entry.owner = None


    def filter_snoop(self, addr: int, requester: int) -> bool:
        """
        判断snoop请求是否可以被过滤
        如果请求者已经持有该缓存行，可以过滤
        """
        hit, entry = self.lookup(addr)
        if not hit:
            return False  # 未命中，无法过滤
        if requester in entry.sharers:
            return True  # 请求者已持有，可以过滤
        if entry.owner == requester:
            return True
        return False


class MultiCoreSystem:
    """多核系统（使用Snoop Filter）"""
    def __init__(self, num_cores: int = 4):
        self.num_cores = num_cores
        self.snoop_filter = Snoop_Filter(num_entries=256)
        # 每个核心的缓存状态（简化）
        self.core_caches: List[Dict[int, Cache_State]] = [{} for _ in range(num_cores)]
        # 统计
        self.total_requests: int = 0
        self.filtered_requests: int = 0


    def handle_request(self, core_id: int, addr: int, req_type: Request_Type):
        """处理核心的内存请求"""
        self.total_requests += 1
        if req_type == Request_Type.READ:
            state = self.snoop_filter.update_on_read(addr, core_id)
            self.core_caches[core_id][addr] = Cache_State.SHARED if state != Cache_State.INVALID else Cache_State.EXCLUSIVE
        elif req_type == Request_Type.WRITE:
            state, snoop_list = self.snoop_filter.update_on_write(addr, core_id)
            # 如果有snoop目标，发送invalidate
            for target in snoop_list:
                if target in self.core_caches[target]:
                    del self.core_caches[target][addr]
            self.core_caches[core_id][addr] = Cache_State.EXCLUSIVE
        elif req_type == Request_Type.READ_FOR_OWN:
            # Read-for-Ownership（获取脏副本）
            state, snoop_list = self.snoop_filter.update_on_write(addr, core_id)
            for target in snoop_list:
                if target in self.core_caches[target]:
                    del self.core_caches[target][addr]
            self.core_caches[core_id][addr] = Cache_State.MODIFIED
        # 检查是否可以过滤snoop
        if self.snoop_filter.filter_snoop(addr, core_id):
            self.filtered_requests += 1


def basic_test():
    """基本功能测试"""
    print("=== Snooper过滤器测试 ===")
    system = Multi-Core_System(num_cores=4)
    print(f"核心数: {system.num_cores}")
    # 模拟请求序列
    print("\n模拟请求序列:")
    requests = [
        (0, 0x1000, Request_Type.READ),
        (1, 0x1000, Request_Type.READ),  # 共享同一个缓存行
        (2, 0x2000, Request_Type.READ),
        (3, 0x1000, Request_Type.WRITE),  # 需要snoop core 0和1
        (0, 0x3000, Request_Type.READ),
        (1, 0x2000, Request_Type.WRITE),  # 需要snoop core 2
    ]
    for i, (core_id, addr, req_type) in enumerate(requests):
        system.handle_request(core_id, addr, req_type)
        print(f"  请求{i}: Core{core_id} -> {req_type.name} @ 0x{addr:x}")
    print(f"\n统计:")
    print(f"  总请求数: {system.total_requests}")
    print(f"  过滤的请求: {system.filtered_requests}")
    print(f"  Snoop过滤器命中率: {system.snoop_filter.hits / (system.snoop_filter.hits + system.snoop_filter.misses):.2%}")
    print(f"  Snoop过滤器条目数: {len(system.snoop_filter.entries)}")


if __name__ == "__main__":
    basic_test()

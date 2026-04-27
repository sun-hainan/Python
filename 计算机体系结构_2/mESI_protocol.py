# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / mESI_protocol

本文件实现 mESI_protocol 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto


class MESI_State(Enum):
    """MESI状态"""
    MODIFIED = "M"    # 已修改（脏）
    EXCLUSIVE = "E"  # 独占/干净
    SHARED = "S"     # 共享/干净
    INVALID = "I"     # 无效


class MOESI_State(Enum):
    """MOESI状态"""
    MODIFIED = "M"
    OWNED = "O"       # Owned（持有但可能已共享）
    EXCLUSIVE = "E"
    SHARED = "S"
    INVALID = "I"


class Bus_Request_Type(Enum):
    """总线请求类型"""
    BUS_READ = auto()           # 总线读
    BUS_READ_EXCLUSIVE = auto() # 总线读以进行写（获取独占）
    BUS_WRITE_BACK = auto()     # 回写
    FLUSH = auto()             # 刷新缓存行


@dataclass
class Cache_Line:
    """缓存行"""
    tag: int = 0
    state: MESI_State = MESI_State.INVALID
    data: Optional[bytes] = None
    sharers: Set[int] = field(default_factory=set)  # 共享者集合


class Cache_Controller:
    """缓存控制器"""
    def __init__(self, core_id: int, cache_size: int = 32 * 1024):
        self.core_id = core_id
        self.cache_size = cache_size
        self.num_lines = cache_size // 64  # 假设64字节行
        self.cache: Dict[int, Cache_Line] = {}
        self.pending_requests: List[Tuple[int, Bus_Request_Type]] = []
        # 统计
        self.loads: int = 0
        self.stores: int = 0
        self.hits: int = 0
        self.misses: int = 0


    def find_line(self, addr: int) -> Optional[Cache_Line]:
        """查找缓存行"""
        index = (addr >> 6) % self.num_lines
        return self.cache.get(index)


    def allocate_line(self, addr: int, state: MESI_State):
        """分配新缓存行"""
        index = (addr >> 6) % self.num_lines
        # 简单直接替换
        line = Cache_Line(tag=addr >> 12, state=state)
        self.cache[index] = line
        return line


class MESI_Protocol:
    """MESI一致性协议"""
    def __init__(self, num_cores: int = 4):
        self.num_cores = num_cores
        self.caches: List[Cache_Controller] = [
            Cache_Controller(core_id=i) for i in range(num_cores)
        ]
        # 共享总线（简化）
        self.bus_requests: List[Tuple[int, Bus_Request_Type, int]] = []  # (addr, type, requester)
        # 统计
        self.bus_transactions: int = 0


    def handle_load(self, core_id: int, addr: int) -> bool:
        """处理加载请求"""
        cache = self.caches[core_id]
        cache.loads += 1
        line = cache.find_line(addr)
        if line is not None and line.state != MESI_State.INVALID:
            cache.hits += 1
            return True
        cache.misses += 1
        # 发送总线读请求
        self.bus_requests.append((addr, Bus_Request_Type.BUS_READ, core_id))
        self.bus_transactions += 1
        # 总线事务处理
        self.process_bus_request(addr, Bus_Request_Type.BUS_READ, core_id)
        # 分配缓存行
        # 检查其他缓存是否有有效副本
        has_shared = False
        for i, c in enumerate(self.caches):
            if i != core_id:
                other_line = c.find_line(addr)
                if other_line is not None and other_line.state == MESI_State.SHARED:
                    has_shared = True
                    break
                if other_line is not None and other_line.state == MESI_State.EXCLUSIVE:
                    has_shared = True
                    other_line.state = MESI_State.SHARED
                    other_line.sharers.add(core_id)
                    break
        new_state = MESI_State.SHARED if has_shared else MESI_State.EXCLUSIVE
        cache.allocate_line(addr, new_state)
        return True


    def handle_store(self, core_id: int, addr: int) -> bool:
        """处理存储请求"""
        cache = self.caches[core_id]
        cache.stores += 1
        line = cache.find_line(addr)
        if line is not None and line.state == MESI_State.EXCLUSIVE:
            # 已是独占，可以直接写
            line.state = MESI_State.MODIFIED
            return True
        if line is not None and line.state == MESI_State.MODIFIED:
            # 已是修改状态
            return True
        # 需要获取独占权
        self.bus_requests.append((addr, Bus_Request_Type.BUS_READ_EXCLUSIVE, core_id))
        self.bus_transactions += 1
        # 总线事务处理
        self.process_bus_request(addr, Bus_Request_Type.BUS_READ_EXCLUSIVE, core_id)
        # Invalidate其他缓存
        for i, c in enumerate(self.caches):
            if i != core_id:
                other_line = c.find_line(addr)
                if other_line is not None and other_line.state != MESI_State.INVALID:
                    other_line.state = MESI_State.INVALID
                    other_line.sharers.clear()
        cache.allocate_line(addr, MESI_State.EXCLUSIVE)
        return True


    def process_bus_request(self, addr: int, req_type: Bus_Request_Type, requester: int):
        """处理总线请求"""
        # 对于读请求，如果有修改状态，需要回写数据
        if req_type == Bus_Request_Type.BUS_READ:
            for i, c in enumerate(self.caches):
                if i != requester:
                    line = c.find_line(addr)
                    if line is not None and line.state == MESI_State.MODIFIED:
                        # 回写到内存（这里简化处理）
                        line.state = MESI_State.SHARED
                        line.sharers.add(requester)
                        break
        elif req_type == Bus_Request_Type.BUS_READ_EXCLUSIVE:
            for i, c in enumerate(self.caches):
                if i != requester:
                    line = c.find_line(addr)
                    if line is not None and line.state != MESI_State.INVALID:
                        line.state = MESI_State.INVALID
                        line.sharers.clear()
                        break


class MESIF_Protocol(MESI_Protocol):
    """MESIF协议（用于Intel QPI/UPI）
    F(Forward)状态：指定一个节点响应共享请求
    """
    def __init__(self, num_cores: int = 4):
        super().__init__(num_cores)
        self.forward_node: Optional[int] = None


    def handle_load(self, core_id: int, addr: int) -> bool:
        """处理加载请求"""
        cache = self.caches[core_id]
        line = cache.find_line(addr)
        if line is not None and line.state != MESI_State.INVALID:
            cache.hits += 1
            return True
        cache.misses += 1
        # 广播读请求
        self.bus_requests.append((addr, Bus_Request_Type.BUS_READ, core_id))
        self.bus_transactions += 1
        self.process_bus_request(addr, Bus_Request_Type.BUS_READ, core_id)
        # 分配为SHARED
        cache.allocate_line(addr, MESI_State.SHARED)
        return True


class MOESI_Protocol:
    """MOESI一致性协议"""
    def __init__(self, num_cores: int = 4):
        self.num_cores = num_cores
        self.caches: List[Cache_Controller] = [
            Cache_Controller(core_id=i) for i in range(num_cores)
        ]
        self.bus_transactions: int = 0
        # 在MOESI中，缓存行可以同时是脏的和共享的（Owned状态）
        # Owned状态表示："我持有数据，其他人可能也有干净副本"


    def handle_load(self, core_id: int, addr: int) -> bool:
        """处理加载请求"""
        cache = self.caches[core_id]
        cache.loads += 1
        line = cache.find_line(addr)
        if line is not None and line.state != MOESI_State.INVALID:
            cache.hits += 1
            return True
        cache.misses += 1
        # 查找是否有脏数据
        owner = None
        for i, c in enumerate(self.caches):
            if i != core_id:
                other_line = c.find_line(addr)
                if other_line is not None:
                    if other_line.state == MOESI_State.MODIFIED:
                        owner = i
                        break
                    elif other_line.state == MOESI_State.OWNED:
                        owner = i
                        break
        if owner is not None:
            # 从owner获取数据，变为SHARED
            self.caches[owner].find_line(addr).state = MOESI_State.OWNED
        cache.allocate_line(addr, MOESI_State.SHARED if owner is not None else MOESI_State.EXCLUSIVE)
        return True


def basic_test():
    """基本功能测试"""
    print("=== MESI协议变体测试 ===")
    # MESI协议
    print("\n[MESI协议]")
    mesi = MESI_Protocol(num_cores=4)
    print(f"核心数: {mesi.num_cores}")
    # 模拟操作序列
    ops = [
        (0, 0x1000, "LOAD"),  # Core0 读取 0x1000
        (1, 0x1000, "LOAD"),  # Core1 读取 0x1000（共享）
        (2, 0x2000, "LOAD"),  # Core2 读取 0x2000
        (3, 0x1000, "STORE"), # Core3 写入 0x1000（需要invalidate）
        (0, 0x3000, "LOAD"),  # Core0 读取 0x3000
    ]
    for core_id, addr, op in ops:
        if op == "LOAD":
            mesi.handle_load(core_id, addr)
            print(f"  Core{core_id} LOAD @0x{addr:x}")
        else:
            mesi.handle_store(core_id, addr)
            print(f"  Core{core_id} STORE @0x{addr:x}")
    print(f"\nMESI统计:")
    print(f"  总加载: {sum(c.loads for c in mesi.caches)}")
    print(f"  总存储: {sum(c.stores for c in mesi.caches)}")
    print(f"  总命中: {sum(c.hits for c in mesi.caches)}")
    print(f"  总未命中: {sum(c.misses for c in mesi.caches)}")
    print(f"  总线事务数: {mesi.bus_transactions}")
    # MESIF协议
    print("\n" + "=" * 50)
    print("\n[MESIF协议]")
    mesif = MESIF_Protocol(num_cores=4)
    for core_id, addr, op in ops[:3]:
        if op == "LOAD":
            mesif.handle_load(core_id, addr)
            print(f"  Core{core_id} LOAD @0x{addr:x}")
    print(f"  MESIF总事务数: {mesif.bus_transactions}")
    # MOESI协议
    print("\n" + "=" * 50)
    print("\n[MOESI协议]")
    moesi = MOESI_Protocol(num_cores=4)
    for core_id, addr, op in ops[:3]:
        if op == "LOAD":
            moesi.handle_load(core_id, addr)
            print(f"  Core{core_id} LOAD @0x{addr:x}")


if __name__ == "__main__":
    basic_test()

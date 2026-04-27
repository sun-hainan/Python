# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / directory_coherence

本文件实现 directory_coherence 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto


class Directory_State(Enum):
    """目录状态"""
    UNCACHED = auto()     # 未缓存（不在任何核）
    SHARED = auto()      # 共享（多个核持有干净副本）
    EXCLUSIVE = auto()    # 独占（一个核持有脏或干净副本）


@dataclass
class Directory_Entry:
    """目录条目"""
    state: Directory_State = Directory_State.UNCACHED
    owner: Optional[int] = None    # 独占持有者
    sharers: Set[int] = field(default_factory=set)  # 共享者集合


class Memory_Controller:
    """内存控制器（包含目录）"""
    def __init__(self, num_cores: int = 4, num_lines: int = 1024):
        self.num_cores = num_cores
        self.num_lines = num_lines
        # 目录（每个内存行一个目录条目）
        self.directory: List[Optional[Directory_Entry]] = [None] * num_lines
        # 内存数据（简化）
        self.memory: Dict[int, bytes] = {}
        # 统计
        self.directory_updates: int = 0
        self.data_from_memory: int = 0
        self.data_from_owner: int = 0


    def get_line_index(self, addr: int) -> int:
        """从地址获取目录索引"""
        return (addr >> 6) % self.num_lines


    def get_directory(self, addr: int) -> Directory_Entry:
        """获取目录条目"""
        idx = self.get_line_index(addr)
        if self.directory[idx] is None:
            self.directory[idx] = Directory_Entry()
        return self.directory[idx]


    def get_data(self, addr: int) -> bytes:
        """从内存读取数据"""
        self.data_from_memory += 1
        if addr not in self.memory:
            self.memory[addr] = bytes(64)  # 模拟64字节行
        return self.memory[addr]


    def write_data(self, addr: int, data: bytes):
        """写数据到内存"""
        self.memory[addr] = data


class Cache_Controller:
    """缓存控制器（使用目录协议）"""
    def __init__(self, core_id: int, memory_controller: Memory_Controller):
        self.core_id = core_id
        self.memory = memory_controller
        self.cache: Dict[int, Tuple[bytes, Directory_State]] = {}  # addr -> (data, state)
        # 挂起的请求
        self.pending_requests: List[Tuple[int, str]] = []
        # 统计
        self.loads: int = 0
        self.stores: int = 0
        self.hits: int = 0
        self.misses: int = 0


    def handle_load(self, addr: int) -> bool:
        """处理加载请求"""
        self.loads += 1
        if addr in self.cache:
            self.hits += 1
            return True
        self.misses += 1
        # 向目录请求数据
        dir_entry = self.memory.get_directory(addr)
        if dir_entry.state == Directory_State.UNCACHED:
            # 数据来自内存
            data = self.memory.get_data(addr)
            self.cache[addr] = (data, Directory_State.SHARED)
            # 更新目录
            dir_entry.state = Directory_State.SHARED
            dir_entry.sharers.add(self.core_id)
            self.memory.directory_updates += 1
        elif dir_entry.state == Directory_State.EXCLUSIVE:
            # 数据来自owner
            owner = dir_entry.owner
            # 假设owner将数据发送给请求者
            data = self.memory.get_data(addr)  # 简化：实际从owner获取
            self.cache[addr] = (data, Directory_State.SHARED)
            # 更新目录
            dir_entry.state = Directory_State.SHARED
            dir_entry.sharers.add(self.core_id)
            dir_entry.sharers.add(owner)
            dir_entry.owner = None
            self.memory.directory_updates += 1
            self.memory.data_from_owner += 1
        elif dir_entry.state == Directory_State.SHARED:
            # 数据已在共享状态
            data = self.memory.get_data(addr)
            self.cache[addr] = (data, Directory_State.SHARED)
            dir_entry.sharers.add(self.core_id)
            self.memory.directory_updates += 1
        return True


    def handle_store(self, addr: int, data: bytes) -> bool:
        """处理存储请求"""
        self.stores += 1
        if addr in self.cache:
            state = self.cache[addr][1]
            if state == Directory_State.EXCLUSIVE:
                # 直接写入
                self.cache[addr] = (data, Directory_State.EXCLUSIVE)
                return True
        # 需要获取独占权
        dir_entry = self.memory.get_directory(addr)
        if dir_entry.state == Directory_State.EXCLUSIVE:
            # Invalidate owner
            old_owner = dir_entry.owner
            if old_owner is not None:
                # 通知owner invalidate
                pass
        elif dir_entry.state == Directory_State.SHARED:
            # Invalidate所有sharer
            for sharer in dir_entry.sharers:
                if sharer != self.core_id:
                    pass  # 发送invalidate
        # 获取数据（如果需要）
        if addr not in self.cache:
            line_data = self.memory.get_data(addr)
            self.cache[addr] = (line_data, Directory_State.EXCLUSIVE)
        else:
            self.cache[addr] = (data, Directory_State.EXCLUSIVE)
        # 更新目录
        dir_entry.state = Directory_State.EXCLUSIVE
        dir_entry.owner = self.core_id
        dir_entry.sharers.clear()
        dir_entry.sharers.add(self.core_id)
        self.memory.directory_updates += 1
        return True


    def handle_write_back(self, addr: int):
        """处理写回"""
        if addr in self.cache:
            data, state = self.cache[addr]
            if state == Directory_State.EXCLUSIVE:
                # 写回内存
                self.memory.write_data(addr, data)
                self.cache[addr] = (data, Directory_State.SHARED)
                dir_entry = self.memory.get_directory(addr)
                dir_entry.state = Directory_State.SHARED
                dir_entry.owner = None


class Directory_Protocol_Simulator:
    """目录协议模拟器"""
    def __init__(self, num_cores: int = 4):
        self.num_cores = num_cores
        self.memory = Memory_Controller(num_cores=num_cores)
        self.cores: List[Cache_Controller] = [
            Cache_Controller(core_id=i, memory_controller=self.memory)
            for i in range(num_cores)
        ]
        self.cycles: int = 0


    def run_operation(self, core_id: int, addr: int, op: str, data: bytes = None):
        """运行单个操作"""
        cache = self.cores[core_id]
        if op == "LOAD":
            cache.handle_load(addr)
            print(f"  Cycle {self.cycles}: Core{core_id} LOAD @0x{addr:x}")
        elif op == "STORE":
            cache.handle_store(addr, data if data else bytes(64))
            print(f"  Cycle {self.cycles}: Core{core_id} STORE @0x{addr:x}")
        elif op == "WRITE_BACK":
            cache.handle_write_back(addr)
            print(f"  Cycle {self.cycles}: Core{core_id} WRITE_BACK @0x{addr:x}")
        self.cycles += 1


def basic_test():
    """基本功能测试"""
    print("=== 目录协议模拟器测试 ===")
    sim = Directory_Protocol_Simulator(num_cores=4)
    print(f"核心数: {sim.num_cores}")
    print(f"目录条目数: {sim.memory.num_lines}")
    # 模拟操作序列
    print("\n操作序列:")
    ops = [
        (0, 0x1000, "LOAD"),
        (1, 0x1000, "LOAD"),   # Core1也读取同一行（共享）
        (2, 0x2000, "LOAD"),
        (3, 0x1000, "STORE", bytes(64)),  # Core3写入，需要获取独占权
        (0, 0x3000, "LOAD"),
        (2, 0x2000, "STORE", bytes(64)),  # Core2写入
    ]
    for op_data in ops:
        core_id = op_data[0]
        addr = op_data[1]
        op = op_data[2]
        data = op_data[3] if len(op_data) > 3 else None
        sim.run_operation(core_id, addr, op, data)
    print(f"\n统计:")
    print(f"  总周期: {sim.cycles}")
    print(f"  目录更新次数: {sim.memory.directory_updates}")
    print(f"  从内存读取: {sim.memory.data_from_memory}")
    print(f"  从owner获取: {sim.memory.data_from_owner}")
    for i, core in enumerate(sim.cores):
        print(f"  Core{i}: 加载={core.loads}, 存储={core.stores}, 命中={core.hits}, 未命中={core.misses}")


if __name__ == "__main__":
    basic_test()

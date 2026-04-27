# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / memory_disambiguation

本文件实现 memory_disambiguation 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto


class Memory_Op_Type(Enum):
    """内存操作类型"""
    LOAD = auto()
    STORE = auto()


class Disambiguation_Strategy(Enum):
    """消歧策略"""
    CONSERVATIVE = auto()  # 保守策略：等待所有更早STORE完成地址计算
    SPECTULATIVE = auto()  # 投机策略：猜测可以安全执行
    ADVANCED = auto()      # 高级策略：使用地址追踪


@dataclass
class Memory_Operation:
    """内存操作描述"""
    id: int = 0
    op_type: Memory_Op_Type = Memory_Op_Type.LOAD
    virtual_addr: int = 0
    physical_addr: int = 0
    data: Optional[int] = None
    rob_id: int = -1
    pc: int = 0
    age: int = 0
    addr_ready: bool = False
    data_ready: bool = False
    executed: bool = False


class Address_Dependency_Tracker:
    """地址依赖追踪器"""
    def __init__(self):
        # 待地址计算的STORE列表
        self.pending_stores: List[Memory_Operation] = []
        # 已完成地址计算的STORE（按地址索引）
        self.completed_stores: Dict[int, Memory_Operation] = {}


    def add_pending_store(self, op: Memory_Operation):
        """添加待地址计算的STORE"""
        self.pending_stores.append(op)


    def store_addr_ready(self, store_id: int, physical_addr: int):
        """STORE地址计算完成"""
        for i, op in enumerate(self.pending_stores):
            if op.id == store_id:
                op.physical_addr = physical_addr
                op.addr_ready = True
                op.data_ready = True  # 假设数据也同时就绪
                # 移到已完成列表
                self.completed_stores[physical_addr] = op
                self.pending_stores.pop(i)
                break


    def check_load_can_proceed(self, load_op: Memory_Operation) -> Tuple[bool, Optional[int]]:
        """
        检查LOAD是否可以安全执行
        返回: (是否可以执行, 转发数据如果有)
        """
        # 激进策略：允许LOAD在STORE地址未知时执行
        # 如果后续发现冲突再squash
        # 查找是否有地址匹配的已完成STORE
        for addr, store in self.completed_stores.items():
            if store.physical_addr == load_op.physical_addr:
                # 地址匹配，可以转发
                return True, store.data
        # 保守策略：如果有待地址计算的STORE，需要等待
        # 这里实现激进策略
        return True, None


    def squash_stores_after(self, rob_id: int):
        """Squash所有 rob_id 之后的STORE"""
        self.pending_stores = [op for op in self.pending_stores if op.rob_id < rob_id]
        self.completed_stores = {
            addr: op for addr, op in self.completed_stores.items()
            if op.rob_id < rob_id
        }


class Memory_Disambiguation_Unit:
    """内存消歧单元"""
    def __init__(self, strategy: Disambiguation_Strategy = Disambiguation_Strategy.SPECTULATIVE):
        self.strategy = strategy
        self.tracker = Address_Dependency_Tracker()
        self.inflight_ops: List[Memory_Operation] = []
        self.next_id: int = 0
        # 统计数据
        self.speculative_loads: int = 0
        self.squashed_loads: int = 0
        self.forwarded_loads: int = 0
        self.conflict_detected: int = 0


    def add_load(self, virtual_addr: int, rob_id: int, pc: int) -> int:
        """添加LOAD操作"""
        op = Memory_Operation(
            id=self.next_id,
            op_type=Memory_Op_Type.LOAD,
            virtual_addr=virtual_addr,
            rob_id=rob_id,
            pc=pc,
            age=len(self.inflight_ops)
        )
        self.next_id += 1
        self.inflight_ops.append(op)
        if self.strategy == Disambiguation_Strategy.SPECTULATIVE:
            self.speculative_loads += 1
        return op.id


    def add_store(self, virtual_addr: int, data: int, rob_id: int, pc: int) -> int:
        """添加STORE操作"""
        op = Memory_Operation(
            id=self.next_id,
            op_type=Memory_Op_Type.STORE,
            virtual_addr=virtual_addr,
            data=data,
            rob_id=rob_id,
            pc=pc,
            age=len(self.inflight_ops)
        )
        self.next_id += 1
        self.inflight_ops.append(op)
        self.tracker.add_pending_store(op)
        return op.id


    def set_addr_ready(self, op_id: int, physical_addr: int):
        """设置操作的地址已就绪"""
        for op in self.inflight_ops:
            if op.id == op_id:
                op.physical_addr = physical_addr
                op.addr_ready = True
                if op.op_type == Memory_Op_Type.STORE:
                    self.tracker.store_addr_ready(op_id, physical_addr)
                break


    def execute_load(self, load_id: int) -> Tuple[bool, Optional[int]]:
        """
        执行LOAD
        返回: (成功标志, 数据值)
        """
        for op in self.inflight_ops:
            if op.id == load_id and op.op_type == Memory_Op_Type.LOAD:
                if not op.addr_ready:
                    return False, None
                # 检查是否可以执行
                can_proceed, forwarded_data = self.tracker.check_load_can_proceed(op)
                if not can_proceed:
                    return False, None
                op.executed = True
                if forwarded_data is not None:
                    self.forwarded_loads += 1
                    return True, forwarded_data
                # 模拟从缓存/内存获取
                return True, random.randint(1, 100)
        return False, None


    def detect_conflict(self, load_id: int, store_id: int) -> bool:
        """检测LOAD和STORE之间的冲突"""
        for load in self.inflight_ops:
            if load.id == load_id:
                for store in self.inflight_ops:
                    if store.id == store_id and store.op_type == Memory_Op_Type.STORE:
                        if store.age < load.age:  # STORE在LOAD之前
                            if store.physical_addr == load.physical_addr:
                                return True
        return False


    def squash_after(self, rob_id: int):
        """Squash所有 rob_id 之后的相关操作"""
        old_len = len(self.inflight_ops)
        self.inflight_ops = [
            op for op in self.inflight_ops
            if op.rob_id < rob_id or op.op_type == Memory_Op_Type.LOAD
        ]
        self.squashed_loads += old_len - len(self.inflight_ops)
        self.tracker.squash_stores_after(rob_id)


    def retire_store(self, store_id: int):
        """退役STORE（从inflight列表移除）"""
        self.inflight_ops = [
            op for op in self.inflight_ops
            if op.id != store_id or op.op_type != Memory_Op_Type.STORE
        ]


def basic_test():
    """基本功能测试"""
    print("=== 内存消歧模拟器测试 ===")
    mdu = Memory_Disambiguation_Unit(strategy=Disambiguation_Strategy.SPECTULATIVE)
    print(f"消歧策略: 激进（投机）")
    # 场景1：Store-Load转发
    print("\n场景1：Store-Load 转发")
    store_id = mdu.add_store(virtual_addr=0x1000, data=42, rob_id=1, pc=0x100)
    mdu.set_addr_ready(store_id, 0x1000)
    load_id = mdu.add_load(virtual_addr=0x1000, rob_id=2, pc=0x104)
    mdu.set_addr_ready(load_id, 0x1000)
    success, data = mdu.execute_load(load_id)
    print(f"  STORE @0x1000=42, LOAD @0x1000 -> success={success}, data={data}, forwarded={mdu.forwarded_loads > 0}")
    # 场景2：Load-Load乱序
    print("\n场景2：Load-Load 乱序执行")
    mdu2 = Memory_Disambiguation_Unit(strategy=Disambiguation_Strategy.SPECTULATIVE)
    load1 = mdu2.add_load(virtual_addr=0x2000, rob_id=1, pc=0x200)
    mdu2.set_addr_ready(load1, 0x2000)
    load2 = mdu2.add_load(virtual_addr=0x2004, rob_id=2, pc=0x204)
    mdu2.set_addr_ready(load2, 0x2004)
    # 先执行load2，再执行load1（乱序）
    success2, data2 = mdu2.execute_load(load2)
    success1, data1 = mdu2.execute_load(load1)
    print(f"  LOAD1 @0x2000 -> success={success1}, data={data1}")
    print(f"  LOAD2 @0x2004 -> success={success2}, data={data2}")
    print(f"\n统计:")
    print(f"  场景1 存储转发次数: {mdu.forwarded_loads}")
    print(f"  场景2 投机LOAD次数: {mdu2.speculative_loads}")
    print(f"  总squash次数: {mdu.squashed_loads + mdu2.squashed_loads}")


if __name__ == "__main__":
    basic_test()

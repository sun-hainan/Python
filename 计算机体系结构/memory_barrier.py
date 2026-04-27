# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / memory_barrier

本文件实现 memory_barrier 相关的算法功能。
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading
import time


class BarrierType(Enum):
    """内存屏障类型"""
    SS = "store_store"     # Store-Store屏障
    SL = "store_load"     # Store-Load屏障
    LS = "load_store"     # Load-Store屏障
    LL = "load_load"      # Load-Load屏障
    FULL = "full"         # 全屏障（所有类型）


@dataclass
class MemoryOperation:
    """内存操作"""
    op_type: str  # 'load' or 'store'
    address: int
    value: int = 0
    timestamp: int = 0


class ThreadContext:
    """线程上下文（模拟CPU核心）"""

    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        self.operations: List[MemoryOperation] = []
        self.pending_stores: Dict[int, int] = {}  # 待提交的store
        self.committed_stores: Dict[int, int] = {}  # 已提交的store

        # Store Buffer (用于模拟Store-Load重排)
        self.store_buffer: List[Tuple[int, int]] = []

        # Memory (共享)
        self.shared_memory: Dict[int, int] = {}

    def load(self, address: int) -> int:
        """
        Load操作
        在TSO模型下，可能看到store buffer中的值（Store-Load重排）
        """
        # 先检查store buffer
        for addr, val in reversed(self.store_buffer):
            if addr == address:
                op = MemoryOperation('load', address, val, len(self.operations))
                self.operations.append(op)
                return val

        # 检查已提交的store
        if address in self.committed_stores:
            val = self.committed_stores[address]
        else:
            val = self.shared_memory.get(address, 0)

        op = MemoryOperation('load', address, val, len(self.operations))
        self.operations.append(op)
        return val

    def store(self, address: int, value: int):
        """Store操作"""
        # 放入store buffer
        self.store_buffer.append((address, value))
        self.pending_stores[address] = value

        op = MemoryOperation('store', address, value, len(self.operations))
        self.operations.append(op)

    def commit_stores(self):
        """提交store buffer中的所有操作到共享内存"""
        for addr, val in self.store_buffer:
            self.shared_memory[addr] = val
            self.committed_stores[addr] = val
        self.store_buffer.clear()
        self.pending_stores.clear()

    def sfence(self):
        """
        Store Fence (x86的SFENCE)
        确保所有store在屏障前都已提交到内存
        """
        self.commit_stores()


class MemoryBarrier:
    """
    内存屏障实现

    在真实硬件中，内存屏障是CPU指令。
    这里模拟其语义。
    """

    def __init__(self, barrier_type: BarrierType = BarrierType.FULL):
        self.barrier_type = barrier_type

    def execute(self, ctx: ThreadContext):
        """
        执行内存屏障
        清除store buffer，强制所有pending store提交
        """
        if self.barrier_type in (BarrierType.SS, BarrierType.SL, BarrierType.FULL):
            # Store-Store屏障：确保之前的store先于之后的store
            ctx.commit_stores()

        if self.barrier_type in (BarrierType.LS, BarrierType.SL, BarrierType.FULL):
            # Load-Store屏障：确保之前的load先于之后的store
            # 清除pending loads（如果有）
            pass

        if self.barrier_type in (BarrierType.LL, BarrierType.LS, BarrierType.FULL):
            # Load-Load屏障：确保之前的load先于之后的load
            pass

        if self.barrier_type == BarrierType.FULL:
            # 全屏障：所有操作顺序完成
            ctx.sfence()


class FenceInstruction:
    """
    Fence指令

    模拟不同架构的fence指令：
    - x86: MFENCE (全屏障), SFENCE (store), LFENCE (load)
    - ARM: DMB (数据存储屏障), DSB (数据同步屏障)
    - Power: SYNC
    """

    @staticmethod
    def mfence(ctx: ThreadContext):
        """
        MFENCE (x86全屏障)
        确保所有内存操作在屏障前都已对所有线程可见
        """
        ctx.sfence()

    @staticmethod
    def sfence(ctx: ThreadContext):
        """
        SFENCE (x86 store屏障)
        确保之前的store先于之后的任何内存操作
        """
        ctx.commit_stores()

    @staticmethod
    def lfence(ctx: ThreadContext):
        """
        LFENCE (x86 load屏障)
        确保之前的load先于之后的load
        （x86上load不会重排，所以这是空操作）
        """
        pass

    @staticmethod
    def dmb_arm(ctx: ThreadContext, option: str = "sy"):
        """
        DMB (ARM数据存储屏障)
        option: 'sy' (全屏障), 'st' (store), 'ld' (load)
        """
        if option in ('sy', 'st'):
            ctx.commit_stores()
        # 对于load屏障，在ARM上需要特殊处理

    @staticmethod
    def dsb_arm(ctx: ThreadContext, option: str = "sy"):
        """
        DSB (ARM数据同步屏障)
        比DMB更强，确保所有操作完成
        """
        ctx.commit_stores()

    @staticmethod
    def sync_power(ctx: ThreadContext):
        """
        SYNC (Power指令)
        最强的屏障，确保所有内存操作完成
        """
        ctx.commit_stores()


class SpinLock:
    """
    自旋锁实现（使用内存屏障）

    正确的自旋锁需要：
    1. 使用原子操作 (CAS) 来获取锁
    2. 使用ACQUIRE语义确保锁保护的数据正确读取
    3. 使用RELEASE语义确保修改在释放锁前对其他线程可见
    """

    def __init__(self):
        self.locked = 0  # 0=未锁, 1=已锁
        self.owner = -1
        self.waiters: List[int] = []

    def acquire(self, ctx: ThreadContext, core_id: int):
        """获取锁（使用原子CAS）"""
        # 使用原子操作尝试获取锁
        # 这里简化为普通操作
        while True:
            # 先检查锁是否可用
            if ctx.load(id(self.locked)) == 0:
                # 尝试CAS（简化）
                ctx.store(id(self.locked), 1)
                # 隐含的屏障确保锁保护的共享变量正确同步
                self.owner = core_id
                return True
            # 自旋等待
            time.sleep(0.001)

    def release(self, ctx: ThreadContext):
        """释放锁"""
        # RELEASE语义：在释放锁前，所有修改必须对其他线程可见
        ctx.commit_stores()
        ctx.store(id(self.locked), 0)
        self.owner = -1

    def is_acquired(self) -> bool:
        """检查锁是否被持有"""
        return self.locked == 1


class PetersonLock:
    """
    Peterson算法实现的锁（演示内存屏障的作用）

    正确实现需要内存屏障来确保：
    1. 对flag的写入顺序
    2. 对victim的写入顺序
    """

    def __init__(self):
        self.flag: List[int] = [0, 0]  # 两个线程的标志
        self.victim = 0
        self.memory: Dict[int, int] = {}

    def lock(self, thread_id: int, ctx: ThreadContext):
        """
        获取锁
        thread_id: 0 或 1
        """
        other = 1 - thread_id

        # flag[thread_id] = 1
        self.flag[thread_id] = 1
        ctx.store(id(self.flag), 1)

        # 内存屏障：确保flag设置在victim之前
        FenceInstruction.mfence(ctx)

        # victim = thread_id
        self.victim = thread_id
        ctx.store(id(self.victim), thread_id)

        # 内存屏障
        FenceInstruction.mfence(ctx)

        # while (flag[other] == 1 && victim == thread_id) ;
        while self.flag[other] == 1 and self.victim == thread_id:
            # 自旋等待
            time.sleep(0.001)

    def unlock(self, thread_id: int, ctx: ThreadContext):
        """释放锁"""
        self.flag[thread_id] = 0
        ctx.store(id(self.flag), 0)


def simulate_memory_barriers():
    """
    模拟内存屏障的效果
    """
    print("=" * 60)
    print("内存屏障 (Memory Barrier) 模拟")
    print("=" * 60)

    # 场景1: 无屏障时的Store-Load重排
    print("\n场景1: Store-Load重排（无屏障）")
    print("-" * 50)

    ctx1 = ThreadContext(0)
    ctx1.shared_memory = {0x1000: 0, 0x2000: 0}  # X=0, Y=0

    print("初始: X=0, Y=0")
    print("执行: STORE X=1; LOAD r0=Y;")

    ctx1.store(0x1000, 1)  # X = 1
    # 此时store在store buffer中，未提交到memory
    r0 = ctx1.load(0x2000)  # r0 = Y (Y=0)

    print(f"结果: r0 = {r0}")
    print("解释: 因为X的store在buffer中，可能在Y的load之后提交")
    print("      导致r0=0（如果Y的load在X的store之前执行）")

    # 场景2: 有SFENCE屏障
    print("\n场景2: 使用SFENCE屏障")
    print("-" * 50)

    ctx2 = ThreadContext(1)
    ctx2.shared_memory = {0x1000: 0, 0x2000: 0}

    print("执行: STORE X=1; SFENCE; LOAD r0=Y;")

    ctx2.store(0x1000, 1)  # X = 1
    FenceInstruction.sfence(ctx2)  # 强制store提交
    r0 = ctx2.load(0x2000)  # r0 = Y

    print(f"结果: r0 = {r0}")
    print("解释: SFENCE确保X=1在LOAD之前提交到内存")

    # 场景3: 互斥锁
    print("\n场景3: 自旋锁与内存屏障")
    print("-" * 50)

    lock = SpinLock()
    shared_data = {'value': 0}
    ctx_a = ThreadContext(10)
    ctx_b = ThreadContext(11)
    ctx_a.shared_memory = shared_data
    ctx_b.shared_memory = shared_data

    print("线程A: 获取锁; data = 42; 释放锁")
    print("线程B: 获取锁; temp = data; 释放锁")

    # 简化的锁操作演示
    lock.acquire(ctx_a, 10)
    ctx_a.store(id(shared_data['value']), 42)
    lock.release(ctx_a)

    lock.acquire(ctx_b, 11)
    temp = ctx_b.load(id(shared_data['value']))
    lock.release(ctx_b)

    print(f"线程B读到: data = {temp}")


if __name__ == "__main__":
    simulate_memory_barriers()

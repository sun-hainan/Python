# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / memory_ordering

本文件实现 memory_ordering 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import time


class MemoryOrder(Enum):
    """内存访问顺序"""
    RELAXED = "relaxed"      # 完全松弛
    ACQUIRE = "acquire"     # 获取
    RELEASE = "release"     # 释放
    SEQ_CST = "seq_cst"     # 顺序一致（最强）


@dataclass
class MemoryAccess:
    """内存访问操作"""
    thread_id: int
    access_type: str  # 'load' or 'store'
    address: int
    value: int = 0
    order: MemoryOrder = MemoryOrder.RELAXED
    timestamp: int = 0


class StoreBuffer:
    """
    Store Buffer（x86 TSO模型的一部分）

    Store操作先进入Store Buffer，而不是直接写入缓存。
    这导致后续的Load可能看不到刚才Store的结果（Store Load重排）。
    """

    def __init__(self, size: int = 10):
        self.size = size
        self.buffer: List[Tuple[int, int]] = []  # (address, value)
        self.memory: Dict[int, int] = {}  # 模拟内存

    def store(self, address: int, value: int):
        """将store放入buffer"""
        if len(self.buffer) >= self.size:
            # Buffer满时，flush到内存
            self._flush()
        self.buffer.append((address, value))

    def _flush(self):
        """将buffer内容flush到内存"""
        for addr, val in self.buffer:
            self.memory[addr] = val
        self.buffer.clear()

    def load(self, address: int) -> Optional[int]:
        """
        读取数据
        先检查store buffer，再检查内存
        """
        # 先检查store buffer
        for addr, val in reversed(self.buffer):
            if addr == address:
                return val
        # 再检查内存
        return self.memory.get(address)

    def fence(self):
        """
        内存屏障（SFENCE）
        确保所有store在屏障前都已写入内存
        """
        self._flush()


class InvalidationQueue:
    """
    Invalidation Queue（x86 TSO模型的一部分）

    存储来自其他核的失效请求。
    Load在读取数据前需要检查此队列。
    """

    def __init__(self):
        self.queue: List[Tuple[int, int]] = []  # (address, timestamp)
        self.cache: Dict[int, int] = {}  # 模拟缓存

    def enqueue(self, address: int, timestamp: int):
        """入队失效请求"""
        self.queue.append((address, timestamp))

    def check(self, address: int) -> bool:
        """检查地址是否在invalidation queue中"""
        for addr, _ in self.queue:
            if addr == address:
                return True
        return False

    def process(self):
        """处理invalidation queue"""
        # 简化处理
        processed = []
        for addr, ts in self.queue:
            if addr in self.cache:
                del self.cache[addr]
            processed.append((addr, ts))
        for item in processed:
            self.queue.remove(item)


class TSOCore:
    """
    TSO (Total Store Order) 核心

    模拟x86处理器的内存模型行为。
    每个核有自己的Store Buffer。
    """

    def __init__(self, core_id: int):
        self.core_id = core_id
        self.store_buffer = StoreBuffer()
        self.invalidation_queue = InvalidationQueue()
        self.memory: Dict[int, int] = {}  # 共享内存
        self.pending_stores: List[Tuple[int, int]] = []  # 待提交的store

        # 执行历史（用于检测问题）
        self.load_history: List[Tuple[int, int]] = []  # (address, value)
        self.store_history: List[Tuple[int, int]] = []  # (address, value)

    def store(self, address: int, value: int):
        """Store操作（先入store buffer）"""
        self.store_buffer.store(address, value)
        self.store_history.append((address, value))

    def load(self, address: int) -> int:
        """Load操作"""
        value = self.store_buffer.load(address)
        if value is None:
            value = self.memory.get(address, 0)
        self.load_history.append((address, value))
        return value

    def fence(self):
        """内存屏障"""
        self.store_buffer.fence()

    def write_to_shared_memory(self, address: int, value: int):
        """直接写共享内存（模拟缓存一致性的最后一步）"""
        self.memory[address] = value


class WeakMemoryCore:
    """
    Weak Memory Ordering 核心 (Power/ARM风格)

    允许更多重排，需要显式屏障。
    """

    def __init__(self, core_id: int):
        self.core_id = core_id
        self.memory: Dict[int, int] = {}
        self.local_buffer: Dict[int, int] = {}  # 本地store buffer

        # 内存屏障标志
        self.pending_loads: List[int] = []
        self.pending_stores: List[int] = []

        # 执行历史
        self.load_history: List[Tuple[int, int]] = []
        self.store_history: List[Tuple[int, int]] = []

    def store(self, address: int, value: int, order: MemoryOrder = MemoryOrder.RELAXED):
        """
        Store操作
        - RELAXED: 可能延迟很久
        - RELEASE: 确保之前的store在之前
        """
        if order == MemoryOrder.RELEASE:
            # Release barrier: 之前的store必须先完成
            self._drain_stores()

        self.local_buffer[address] = value
        self.store_history.append((address, value))

    def load(self, address: int, order: MemoryOrder = MemoryOrder.RELAXED) -> int:
        """
        Load操作
        - RELAXED: 可能读到旧值
        - ACQUIRE: 确保之后的load不会重排到之前
        """
        if order == MemoryOrder.ACQUIRE:
            # Acquire barrier: 之后的load不能重排到之前
            pass  # 简化处理

        # 先查本地buffer
        if address in self.local_buffer:
            value = self.local_buffer[address]
        else:
            value = self.memory.get(address, 0)

        self.load_history.append((address, value))
        return value

    def _drain_stores(self):
        """Drain local stores to memory"""
        for addr, val in list(self.local_buffer.items()):
            self.memory[addr] = val
            del self.local_buffer[addr]

    def fence(self, order: MemoryOrder = MemoryOrder.SEQ_CST):
        """内存屏障"""
        if order == MemoryOrder.SEQ_CST:
            # 顺序一致：所有之前的store和load必须完成
            self._drain_stores()
            # 确保所有pending操作完成
            self.pending_loads.clear()
            self.pending_stores.clear()


class MemoryOrderingSimulator:
    """
    内存排序模型模拟器

    演示TSO和Weak Ordering的区别
    """

    def __init__(self):
        self.cores: List[TSOCore] = []
        self.weak_cores: List[WeakMemoryCore] = []

    def simulate_tso(self):
        """
        模拟TSO (x86) 模型
        演示Store Buffer导致的Store-Load重排
        """
        print("=" * 60)
        print("TSO (Total Store Order) 模型模拟")
        print("=" * 60)

        # 创建两个核
        core0 = TSOCore(0)
        core1 = TSOCore(1)
        core0.memory = core1.memory  # 共享内存

        # 共享变量
        addr_x = 0x1000
        addr_y = 0x2000

        print("\n场景: Store-Load重排")
        print("-" * 40)
        print("初始: X = 0, Y = 0")
        print("线程0: X = 1; r0 = Y")
        print("线程1: Y = 1; r1 = X")

        # 线程0执行
        core0.store(addr_x, 1)  # X = 1
        r0 = core0.load(addr_y)  # r0 = Y

        # 线程1执行
        core1.store(addr_y, 1)  # Y = 1
        r1 = core1.load(addr_x)  # r1 = X

        # 刷新store buffer
        core0.fence()
        core1.fence()

        print(f"\n结果:")
        print(f"  线程0: r0 = {r0}")
        print(f"  线程1: r1 = {r1}")

        if r0 == 0 and r1 == 0:
            print(f"\n观察到 r0=0 且 r1=0 (在TSO中理论上不应该发生，但由于Store Buffer可能发生)")
        elif r0 == 1 and r1 == 1:
            print(f"\n正常结果: r0=1 且 r1=1")
        else:
            print(f"\n结果: ({r0}, {r1})")

        # 验证内存顺序
        print(f"\n执行顺序分析:")
        print(f"  线程0 store X=1 在store buffer中，Y={r0} 读到旧值")
        print(f"  线程1 store Y=1 在store buffer中，X={r1} 可能读到旧值")

    def simulate_weak_memory(self):
        """
        模拟Weak Memory Ordering (Power/ARM)
        演示需要显式屏障
        """
        print("\n" + "=" * 60)
        print("Weak Memory Ordering (Power/ARM) 模型模拟")
        print("=" * 60)

        core0 = WeakMemoryCore(0)
        core1 = WeakMemoryCore(1)
        core0.memory = core1.memory
        core1.memory = core1.memory

        addr_x = 0x1000
        addr_y = 0x2000
        addr_flag = 0x3000

        print("\n场景: 数据竞争需要屏障")
        print("-" * 40)
        print("初始: data = 0, flag = 0")
        print("生产者: data = 42; flag = 1; (RELEASE)")
        print("消费者: if (flag == 1) print data; (ACQUIRE)")

        # 生产者
        core0.store(addr_x, 42, MemoryOrder.RELAXED)  # data = 42
        core0.store(addr_flag, 1, MemoryOrder.RELEASE)  # flag = 1 (RELEASE barrier)

        # 消费者
        flag = core1.load(addr_flag, MemoryOrder.ACQUIRE)  # ACQUIRE barrier
        if flag == 1:
            data = core1.load(addr_x, MemoryOrder.RELAXED)
            print(f"  消费者读到: flag={flag}, data={data}")
        else:
            print(f"  消费者读到: flag={flag} (数据未就绪)")

        # 如果没有ACQUIRE/RELEASE，可能读到旧值
        print("\n如果没有屏障:")
        print("  消费者可能看到 flag=1 但 data=0 (重排)")
        print("  因为RELAXED操作可能任意重排")

    def simulate_lock_example(self):
        """
        模拟互斥锁的内存语义
        """
        print("\n" + "=" * 60)
        print("互斥锁的内存语义")
        print("=" * 60)

        print("\n正确使用ACQUIRE/RELEASE:")

        # 模拟一个简单的自旋锁
        addr_lock = 0x4000
        addr_data = 0x5000

        # 持有锁的核
        lock_holder = WeakMemoryCore(0)
        lock_holder.memory = lock_holder.memory

        # 等待锁的核
        lock_waiter = WeakMemoryCore(1)
        lock_waiter.memory = lock_holder.memory

        print("线程0 (锁持有者):")
        print("  lock.value = 1 (RELEASE)")
        print("  data = 42")
        lock_holder.store(addr_lock, 1, MemoryOrder.RELEASE)
        lock_holder.store(addr_data, 42, MemoryOrder.RELAXED)

        print("线程1 (锁等待者):")
        print("  while (lock != 1) ;")
        print("  data = data (ACQUIRE)")
        while True:
            lock_val = lock_waiter.load(addr_lock, MemoryOrder.ACQUIRE)
            if lock_val == 1:
                data = lock_waiter.load(addr_data, MemoryOrder.RELAXED)
                print(f"  获取到锁，读到 data={data}")
                break


def simulate_memory_ordering():
    """
    主模拟函数
    """
    print("=" * 70)
    print("内存排序模型 (Memory Ordering Models) 模拟")
    print("=" * 70)
    print("\n本模拟演示三种内存模型：")
    print("1. TSO (Total Store Order) - x86使用")
    print("2. Weak Memory Ordering - Power/ARM使用")
    print("3. 互斥锁的ACQUIRE/RELEASE语义")

    sim = MemoryOrderingSimulator()

    sim.simulate_tso()
    sim.simulate_weak_memory()
    sim.simulate_lock_example()


if __name__ == "__main__":
    simulate_memory_ordering()

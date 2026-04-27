# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / atomic_operations

本文件实现 atomic_operations 相关的算法功能。
"""

from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time


class CASResult(Enum):
    """CAS操作结果"""
    SUCCESS = "success"
    FAILURE = "failure"


class LLSCResult(Enum):
    """LL/SC操作结果"""
    SUCCESS = "success"
    FAILURE = "failure"


class SharedMemory:
    """共享内存（模拟多核共享内存）"""

    def __init__(self):
        self.data: dict = {}
        self.locks: dict = {}  # 地址 -> 锁
        self.link_register: dict = {}  # link register: 地址 -> linked value
        self.modified_since_ll: dict = {}  # 地址 -> 是否被修改

    def read(self, address: int) -> int:
        """读取内存"""
        return self.data.get(address, 0)

    def write(self, address: int, value: int):
        """写入内存"""
        self.data[address] = value

    def is_modified(self, address: int) -> bool:
        """检查地址是否被修改"""
        return self.modified_since_ll.get(address, False)

    def set_modified(self, address: int, modified: bool):
        """设置修改标志"""
        self.modified_since_ll[address] = modified


class AtomicCAS:
    """
    Compare-And-Swap 原子操作

    伪代码:
    def CAS(addr, expected, new_value):
        actual = load(addr)
        if actual == expected:
            store(addr, new_value)
            return SUCCESS
        return FAILURE
    """

    def __init__(self, memory: SharedMemory):
        self.memory = memory

    def compare_and_swap(self, address: int, expected: int, new_value: int) -> CASResult:
        """
        执行CAS操作
        param address: 内存地址
        param expected: 预期值
        param new_value: 新值
        return: 成功或失败
        """
        # 读取当前值
        actual = self.memory.read(address)

        if actual == expected:
            # 值匹配，执行swap
            self.memory.write(address, new_value)
            return CASResult.SUCCESS
        else:
            # 值不匹配，CAS失败
            return CASResult.FAILURE


class LLSCEngine:
    """
    Load-Linked / Store-Conditional 引擎

    LL操作标记一个内存地址，SC检查是否有其他CPU修改过该地址。
    """

    def __init__(self, memory: SharedMemory):
        self.memory = memory

    def load_linked(self, address: int) -> int:
        """
        Load-Linked (LL)
        读取内存并标记该地址
        """
        value = self.memory.read(address)
        # 记录link register
        self.memory.link_register[threading.current_thread().ident] = address
        # 清除修改标志
        self.memory.set_modified(address, False)
        return value

    def store_conditional(self, address: int, value: int) -> LLSCResult:
        """
        Store-Conditional (SC)
        仅当自LL之后没有被修改时写入
        """
        # 检查link register
        current_thread = threading.current_thread().ident
        linked_addr = self.memory.link_register.get(current_thread)

        if linked_addr != address:
            # 没有执行过LL，或者LL的是不同地址
            return LLSCResult.FAILURE

        # 检查是否被修改
        if self.memory.is_modified(address):
            # 被修改了，SC失败
            return LLSCResult.FAILURE

        # 执行store
        self.memory.write(address, value)
        return LLSCResult.SUCCESS


class AtomicCounter:
    """
    使用CAS实现的原子计数器
    演示如何在没有硬件原子指令的情况下实现原子操作
    """

    def __init__(self, initial_value: int = 0):
        self.memory = SharedMemory()
        self.address = 0x1000
        self.memory.write(self.address, initial_value)
        self.cas = AtomicCAS(self.memory)

    def increment(self) -> int:
        """
        原子递增
        使用CAS实现
        """
        while True:
            old_value = self.memory.read(self.address)
            new_value = old_value + 1

            # 尝试CAS
            result = self.cas.compare_and_swap(self.address, old_value, new_value)
            if result == CASResult.SUCCESS:
                return new_value

            # CAS失败，重试
            # （可能被其他线程修改了）

    def decrement(self) -> int:
        """原子递减"""
        while True:
            old_value = self.memory.read(self.address)
            new_value = old_value - 1

            result = self.cas.compare_and_swap(self.address, old_value, new_value)
            if result == CASResult.SUCCESS:
                return new_value

    def get(self) -> int:
        """获取当前值"""
        return self.memory.read(self.address)


class AtomicStack:
    """
    使用CAS实现的Lock-Free栈

    支持push和pop操作，无需锁。
    """

    def __init__(self):
        self.memory = SharedMemory()
        self.head_address = 0x2000
        self.memory.write(self.head_address, 0)  # 栈为空
        self.cas = AtomicCAS(self.memory)

        # 节点池
        self.node_pool: dict = {}
        self.next_node_id = 1

    def _allocate_node(self, value: int) -> int:
        """分配节点"""
        node_id = self.next_node_id
        self.next_node_id += 1
        self.node_pool[node_id] = {'value': value, 'next': 0}
        return node_id

    def push(self, value: int) -> bool:
        """
        原子push
        """
        while True:
            # 读取当前head
            head = self.memory.read(self.head_address)

            # 分配新节点
            new_node = self._allocate_node(value)
            self.node_pool[new_node]['next'] = head

            # 尝试CAS更新head
            result = self.cas.compare_and_swap(self.head_address, head, new_node)
            if result == CASResult.SUCCESS:
                return True

            # 失败，重试
            time.sleep(0.0001)

    def pop(self) -> Optional[int]:
        """
        原子pop
        """
        while True:
            # 读取当前head
            head = self.memory.read(self.head_address)

            if head == 0:
                # 栈为空
                return None

            # 读取head指向的节点
            node = self.node_pool.get(head)
            if node is None:
                return None

            next_node = node['next']

            # 尝试CAS更新head
            result = self.cas.compare_and_swap(self.head_address, head, next_node)
            if result == CASResult.SUCCESS:
                # 成功，移除节点并返回值
                value = node['value']
                del self.node_pool[head]
                return value

            # 失败，重试
            time.sleep(0.0001)


class LLSCBasedAtomicCounter:
    """
    基于LL/SC的原子计数器
    """

    def __init__(self, initial_value: int = 0):
        self.memory = SharedMemory()
        self.address = 0x3000
        self.memory.write(self.address, initial_value)
        self.llsc = LLSCEngine(self.memory)

    def increment(self) -> int:
        """原子递增（使用LL/SC）"""
        while True:
            # LL: 读取并标记
            old_value = self.llsc.load_linked(self.address)
            new_value = old_value + 1

            # SC: 尝试写入
            result = self.llsc.store_conditional(self.address, new_value)
            if result == LLSCResult.SUCCESS:
                return new_value

            # SC失败，重试
            # （可能被其他CPU修改了）


class LLSCBasedSpinLock:
    """
    基于LL/SC的自旋锁

    LL/SC比CAS更灵活，可以实现更复杂的原子操作。
    """

    def __init__(self):
        self.memory = SharedMemory()
        self.lock_address = 0x4000
        self.memory.write(self.lock_address, 0)  # 0=未锁定, 1=锁定
        self.llsc = LLSCEngine(self.memory)

    def acquire(self):
        """获取锁"""
        while True:
            # LL: 读取锁状态
            locked = self.llsc.load_linked(self.lock_address)

            if locked == 0:
                # 锁未持有，尝试获取
                # SC: 如果锁仍为0，则设为1
                result = self.llsc.store_conditional(self.lock_address, 1)
                if result == LLSCResult.SUCCESS:
                    return  # 获取成功

            # 锁已被持有或SC失败，自旋等待
            time.sleep(0.0001)

    def release(self):
        """释放锁"""
        # 释放锁很简单，直接写0
        self.memory.write(self.lock_address, 0)


def simulate_atomic_operations():
    """
    模拟原子操作
    """
    print("=" * 60)
    print("原子操作：CAS 与 LL/SC")
    print("=" * 60)

    # CAS示例
    print("\n" + "-" * 40)
    print("1. Compare-And-Swap (CAS)")
    print("-" * 40)

    memory = SharedMemory()
    cas = AtomicCAS(memory)
    addr = 0x1000

    print(f"\n初始: memory[0x{addr:X}] = 0")

    # 第一次CAS：期望0，新值42
    result = cas.compare_and_swap(addr, 0, 42)
    print(f"CAS(addr, 0, 42) -> {result.name}")
    print(f"memory[0x{addr:X}] = {memory.read(addr)}")

    # 第二次CAS：期望0（但实际是42），新值100
    result = cas.compare_and_swap(addr, 0, 100)
    print(f"CAS(addr, 0, 100) -> {result.name}")
    print(f"memory[0x{addr:X}] = {memory.read(addr)}")

    # 第三次CAS：期望42，新值100
    result = cas.compare_and_swap(addr, 42, 100)
    print(f"CAS(addr, 42, 100) -> {result.name}")
    print(f"memory[0x{addr:X}] = {memory.read(addr)}")

    # 原子计数器示例
    print("\n" + "-" * 40)
    print("2. 原子计数器 (使用CAS实现)")
    print("-" * 40)

    counter = AtomicCounter(0)
    print(f"初始值: {counter.get()}")

    for i in range(5):
        new_val = counter.increment()
        print(f"increment() -> {new_val}")

    print(f"最终值: {counter.get()}")

    # LL/SC示例
    print("\n" + "-" * 40)
    print("3. Load-Linked / Store-Conditional")
    print("-" * 40)

    memory2 = SharedMemory()
    llsc = LLSCEngine(memory2)
    addr2 = 0x2000

    print(f"\n初始: memory[0x{addr2:X}] = 0")

    # LL: 读取并标记
    value = llsc.load_linked(addr2)
    print(f"LL(0x{addr2:X}) -> {value}")
    print(f"  (地址0x{addr2:X}被标记)")

    # SC: 尝试写入（应该成功）
    result = llsc.store_conditional(addr2, 42)
    print(f"SC(0x{addr2:X}, 42) -> {result.name}")
    print(f"memory[0x{addr2:X}] = {memory2.read(addr2)}")

    # 模拟其他CPU修改
    memory2.write(addr2, 100)
    memory2.set_modified(addr2, True)  # 标记已被修改

    # 再次LL
    value = llsc.load_linked(addr2)
    print(f"\n模拟其他CPU修改后:")
    print(f"LL(0x{addr2:X}) -> {value}")

    # SC应该失败
    result = llsc.store_conditional(addr2, 50)
    print(f"SC(0x{addr2:X}, 50) -> {result.name}")
    print(f"memory[0x{addr2:X}] = {memory2.read(addr2)} (未改变)")

    # Lock-Free栈示例
    print("\n" + "-" * 40)
    print("4. Lock-Free 栈 (使用CAS)")
    print("-" * 40)

    stack = AtomicStack()
    print("Push: 10, 20, 30")
    stack.push(10)
    stack.push(20)
    stack.push(30)

    print("Pop:", end=" ")
    while True:
        val = stack.pop()
        if val is None:
            break
        print(val, end=" ")
    print()


if __name__ == "__main__":
    simulate_atomic_operations()

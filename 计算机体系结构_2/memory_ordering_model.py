# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / memory_ordering_model



本文件实现 memory_ordering_model 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Tuple, Set

from dataclasses import dataclass, field

from enum import Enum, auto





class Memory_Order(Enum):

    """内存操作顺序"""

    RELAXED = auto()       # 宽松排序

    ACQUIRE = auto()       # 获取屏障

    RELEASE = auto()       # 释放屏障

    SEQ_CST = auto()       # 顺序一致





class Architecture_Type(Enum):

    """架构类型"""

    X86_TSO = "x86 TSO (Total Store Order)"

    ARM_WO = "ARM (Weak Ordering)"

    POWER_PO = "Power (Processor Consistent)"





@dataclass

class Memory_Operation:

    """内存操作"""

    thread_id: int

    op_type: str  # "LOAD" or "STORE"

    address: int

    value: int

    order: Memory_Order = Memory_Order.RELAXED

    timestamp: int = 0





class Store_Buffer:

    """存储缓冲（用于TSO模拟）"""

    def __init__(self):

        self.entries: List[Tuple[int, int]] = []  # (address, value)

        self.pending_writes: List[Tuple[int, int]] = []





    def add_store(self, addr: int, value: int):

        """添加存储操作"""

        self.entries.append((addr, value))

        self.pending_writes.append((addr, value))





    def flush_to_memory(self, memory: Dict[int, int]):

        """将存储缓冲刷新到内存"""

        while self.pending_writes:

            addr, value = self.pending_writes.pop(0)

            memory[addr] = value





class Memory_Model_Simulator:

    """内存模型模拟器基类"""

    def __init__(self, name: str, arch_type: Architecture_Type):

        self.name = name

        self.arch_type = arch_type

        self.memory: Dict[int, int] = {}

        self.threads: Dict[int, List[Memory_Operation]] = {}

        self.completion_order: List[Memory_Operation] = []

        self.timestamp: int = 0





    def add_operation(self, thread_id: int, op: Memory_Operation):

        """添加内存操作"""

        op.timestamp = self.timestamp

        self.timestamp += 1

        if thread_id not in self.threads:

            self.threads[thread_id] = []

        self.threads[thread_id].append(op)

        self.completion_order.append(op)





    def execute_load(self, op: Memory_Operation) -> int:

        """执行加载"""

        # 默认：从内存读取（子类可以override）

        return self.memory.get(op.address, 0)





    def execute_store(self, op: Memory_Operation):

        """执行存储"""

        self.memory[op.address] = op.value





    def run(self):

        """运行所有操作"""

        for op in self.completion_order:

            if op.op_type == "LOAD":

                value = self.execute_load(op)

                op.value = value

            else:

                self.execute_store(op)





class X86_TSO_Simulator(Memory_Model_Simulator):

    """

    x86 TSO (Total Store Order) 模拟器

    特性：

    - 所有存储按程序顺序出现（对所有线程）

    - 存储缓冲（Store Buffer）导致Store-Load重排

    - 加载可以speculatively执行

    - MFENCE提供存储顺序和缓存一致性

    """

    def __init__(self):

        super().__init__("x86 TSO", Architecture_Type.X86_TSO)

        self.store_buffer = Store_Buffer()

        self.pending_stores: Dict[int, List[Tuple[int, int]]] = {}  # thread -> stores





    def execute_load(self, op: Memory_Operation) -> int:

        """x86 TSO：加载时检查Store Buffer"""

        # 检查当前线程的Store Buffer

        thread_buffer = self.pending_stores.get(op.thread_id, [])

        # 逆序查找（最老的在后）

        for addr, value in reversed(thread_buffer):

            if addr == op.address:

                return value

        return self.memory.get(op.address, 0)





    def execute_store(self, op: Memory_Operation):

        """x86 TSO：存储进入Store Buffer"""

        if op.thread_id not in self.pending_stores:

            self.pending_stores[op.thread_id] = []

        self.pending_stores[op.thread_id].append((op.address, op.value))

        # 在x86 TSO中，存储通常在后续加载/存储之前被刷回

        # 这里简化：每条存储后检查是否可以刷回





class ARM_WO_Simulator(Memory_Model_Simulator):

    """

    ARM 宽松排序 (Weak Ordering) 模拟器

    特性：

    - 几乎没有顺序保证

    - 需要显式屏障（dmb, dsb）

    - 加载/存储可能重排

    - 存储到自身地址可以重排

    """

    def __init__(self):

        super().__init__("ARM WO", Architecture_Type.ARM_WO)

        self.pending_stores: Dict[int, List[Tuple[int, int]]] = {}

        self.last_store_addr: Dict[int, int] = {}  # 每个线程最后的存储地址





    def execute_load(self, op: Memory_Operation) -> int:

        """ARM WO：加载可能返回陈旧数据（如果存储尚未刷回）"""

        # 宽松模型：存储可能还未刷回

        # 简化：80%概率存储已刷回，20%概率使用旧值

        thread_buffer = self.pending_stores.get(op.thread_id, [])

        for addr, value in reversed(thread_buffer):

            if addr == op.address:

                if random.random() < 0.8:

                    return value

                else:

                    break

        return self.memory.get(op.address, 0)





    def execute_store(self, op: Memory_Operation):

        """ARM WO：存储可能延迟刷回"""

        if op.thread_id not in self.pending_stores:

            self.pending_stores[op.thread_id] = []

        # 宽松模型：存储可能延迟

        if random.random() < 0.9:  # 90%概率立即刷回

            self.memory[op.address] = op.value

        else:

            self.pending_stores[op.thread_id].append((op.address, op.value))





class Power_PO_Simulator(Memory_Model_Simulator):

    """

    Power 处理器一致 (Processor Consistent) 模拟器

    特性：

    - 存储缓冲导致Store-Load重排

    - 加载可以重排

    - 需要sync/isync屏障

    - 对同一地址的存储保证顺序

    """

    def __init__(self):

        super().__init__("Power PO", Architecture_Type.POWER_PO)

        self.pending_stores: Dict[int, List[Tuple[int, int]]] = {}

        self.sync_barriers: Set[int] = set()  # 同步点





    def execute_load(self, op: Memory_Operation) -> int:

        """Power PO：处理同步屏障"""

        # 检查是否有sync屏障在加载之前

        thread_ops = self.threads.get(op.thread_id, [])

        for prev_op in thread_ops:

            if prev_op.timestamp >= op.timestamp:

                break

            if prev_op.order == Memory_Order.RELEASE and prev_op.timestamp < op.timestamp:

                # 释放屏障后的加载需要等待之前的存储刷回

                pass

        thread_buffer = self.pending_stores.get(op.thread_id, [])

        for addr, value in reversed(thread_buffer):

            if addr == op.address:

                return value

        return self.memory.get(op.address, 0)





    def execute_store(self, op: Memory_Operation):

        """Power PO：存储处理"""

        if op.thread_id not in self.pending_stores:

            self.pending_stores[op.thread_id] = []

        if op.order == Memory_Order.RELEASE:

            # 释放屏障：刷回所有pending stores

            for addr, value in self.pending_stores[op.thread_id]:

                self.memory[addr] = value

            self.pending_stores[op.thread_id].clear()

        else:

            self.pending_stores[op.thread_id].append((op.address, op.value))





class Memory_Model_Comparison:

    """内存模型对比测试"""

    @staticmethod

    def create_test_program() -> List[Tuple[int, str, int, int, Memory_Order]]:

        """

        创建测试程序：线程0执行 x=1; r1=y; 线程1执行 y=1; r2=x;

        用于检测Store-Load重排

        """

        program = [

            # (thread_id, op_type, address, value, order)

            (0, "STORE", 0x1000, 1, Memory_Order.RELAXED),  # x=1

            (0, "LOAD", 0x2000, 0, Memory_Order.RELAXED),   # r1=y

            (1, "STORE", 0x2000, 1, Memory_Order.RELAXED),  # y=1

            (1, "LOAD", 0x1000, 0, Memory_Order.RELAXED),   # r2=x

        ]

        return program





    @staticmethod

    def run_on_model(simulator: Memory_Model_Simulator, program: List[Tuple]) -> Dict[str, int]:

        """在指定模型上运行测试程序"""

        # 清空状态

        simulator.memory = {0x1000: 0, 0x2000: 0}

        simulator.threads = {}

        simulator.completion_order = []

        simulator.timestamp = 0

        if hasattr(simulator, 'pending_stores'):

            simulator.pending_stores = {}

        # 添加操作（打乱顺序模拟并发）

        ops = []

        for thread_id, op_type, addr, value, order in program:

            op = Memory_Operation(thread_id, op_type, addr, value, order)

            ops.append(op)

        # 随机顺序添加（模拟并发）

        random.shuffle(ops)

        for op in ops:

            simulator.add_operation(op.thread_id, op)

        # 运行

        simulator.run()

        # 收集结果

        r1 = r2 = None

        for op in simulator.completion_order:

            if op.thread_id == 0 and op.op_type == "LOAD":

                r1 = op.value

            elif op.thread_id == 1 and op.op_type == "LOAD":

                r2 = op.value

        return {"r1": r1, "r2": r2, "x": simulator.memory.get(0x1000), "y": simulator.memory.get(0x2000)}





def basic_test():

    """基本功能测试"""

    print("=== 内存排序模型对比测试 ===")

    program = Memory_Model_Comparison.create_test_program()

    print("\n测试程序（检测Store-Load重排）:")

    print("  线程0: x=1; r1=y;")

    print("  线程1: y=1; r2=x;")

    print("\n预期结果组合:")

    print("  x86 TSO: 不会发生 r1=0 && r2=0 (Store-Load重排)")

    print("  ARM WO:  可能发生 r1=0 && r2=0")

    print("  Power:   可能发生 r1=0 && r2=0")

    # x86 TSO

    print("\n" + "=" * 50)

    print("\n[x86 TSO 模拟器]")

    x86_sim = X86_TSO_Simulator()

    results_seen = set()

    for i in range(10):

        result = Memory_Model_Comparison.run_on_model(x86_sim, program)

        key = (result["r1"], result["r2"])

        results_seen.add(key)

    print(f"  观察到的结果组合: {results_seen}")

    # ARM

    print("\n" + "=" * 50)

    print("\n[ARM WO 模拟器]")

    arm_sim = ARM_WO_Simulator()

    results_seen = set()

    for i in range(10):

        result = Memory_Model_Comparison.run_on_model(arm_sim, program)

        key = (result["r1"], result["r2"])

        results_seen.add(key)

    print(f"  观察到的结果组合: {results_seen}")

    # Power

    print("\n" + "=" * 50)

    print("\n[Power PO 模拟器]")

    power_sim = Power_PO_Simulator()

    results_seen = set()

    for i in range(10):

        result = Memory_Model_Comparison.run_on_model(power_sim, program)

        key = (result["r1"], result["r2"])

        results_seen.add(key)

    print(f"  观察到的结果组合: {results_seen}")

    # 对比表格

    print("\n" + "=" * 50)

    print("\n内存模型特性对比:")

    print("  | 特性           | x86 TSO | ARM WO | Power PO |")

    print("  |----------------|---------|--------|----------|")

    print("  | Store-Load重排  | 不允许  | 允许   | 允许     |")

    print("  | Load-Load重排   | 不允许  | 允许   | 允许     |")

    print("  | Store-Store重排 | 不允许  | 允许   | 允许     |")

    print("  | 存储缓冲       | 有      | 无     | 有       |")





if __name__ == "__main__":

    basic_test()


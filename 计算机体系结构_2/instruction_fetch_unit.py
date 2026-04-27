# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / instruction_fetch_unit



本文件实现 instruction_fetch_unit 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Branch_Direction(Enum):

    """分支方向预测"""

    NOT_TAKEN = auto()

    TAKEN = auto()





@dataclass

class Fetch_Bundle:

    """取指Bundle（一次取出的多条指令）"""

    pc: int                      # Bundle起始PC

    instructions: List[int]      # 指令列表（编码）

    valid_count: int             # 有效指令数

    taken: bool = False         # 是否发生分支跳转

    target: int = 0             # 跳转目标（如果taken）





@dataclass

class ICache_Line:

    """指令缓存行"""

    tag: int = 0                # 标签

    data: bytes = field(default_factory=bytes)  # 指令数据

    valid: bool = False         # 有效位

    lru_age: int = 0            # LRU年龄





class Instruction_Cache:

    """指令缓存（L1 ICache）"""

    def __init__(self, num_sets: int = 64, associativity: int = 4, line_size: int = 64):

        self.num_sets = num_sets

        self.associativity = associativity

        self.line_size = line_size

        self.index_bits = (num_sets.bit_length() - 1)

        self.offset_bits = (line_size.bit_length() - 1)

        self.tag_bits = 32 - self.index_bits - self.offset_bits

        # 缓存数组 [set][way]

        self.lines: List[List[ICache_Line]] = [

            [ICache_Line() for _ in range(associativity)]

            for _ in range(num_sets)

        ]

        # 统计

        self.hits: int = 0

        self.misses: int = 0





    def _get_set(self, addr: int) -> int:

        """从地址中提取set索引"""

        return (addr >> self.offset_bits) & ((1 << self.index_bits) - 1)





    def _get_tag(self, addr: int) -> int:

        """从地址中提取tag"""

        return addr >> (self.index_bits + self.offset_bits)





    def lookup(self, addr: int) -> Tuple[bool, ICache_Line]:

        """查找ICache"""

        set_idx = self._get_set(addr)

        tag = self._get_tag(addr)

        for way in range(self.associativity):

            line = self.lines[set_idx][way]

            if line.valid and line.tag == tag:

                self.hits += 1

                return True, line

        self.misses += 1

        return False, ICache_Line()





    def fill(self, addr: int, data: bytes):

        """填充ICache行（模拟填充）"""

        set_idx = self._get_set(addr)

        tag = self._get_tag(addr)

        # 简单LFU替换

        min_age = float('inf')

        min_way = 0

        for way in range(self.associativity):

            if not self.lines[set_idx][way].valid:

                min_way = way

                break

            if self.lines[set_idx][way].lru_age < min_age:

                min_age = self.lines[set_idx][way].lru_age

                min_way = way

        # 填充

        line = self.lines[set_idx][min_way]

        line.tag = tag

        line.data = data

        line.valid = True

        line.lru_age = 0





    def get_hit_rate(self) -> float:

        """计算命中率"""

        total = self.hits + self.misses

        return self.hits / total if total > 0 else 0.0





class BTB_Stub:

    """简化的BTB（用于IFU集成）"""

    def __init__(self):

        self.entries: Dict[int, int] = {}  # PC -> target





    def lookup(self, pc: int) -> Optional[int]:

        """查找分支目标"""

        return self.entries.get(pc)





    def update(self, pc: int, target: int):

        """更新BTB"""

        self.entries[pc] = target





class Instruction_Fetch_Unit:

    """指令预取单元"""

    def __init__(self, fetch_width: int = 4, icache: Instruction_Cache = None):

        self.fetch_width = fetch_width             # 取指宽度（每周期取指条数）

        self.pc: int = 0x1000                     # 当前取指PC

        self.icache = icache if icache else Instruction_Cache()

        self.btb = BTB_Stub()

        # 分支历史缓冲

        self.bhr: int = 0

        self.bhr_length: int = 8

        # 预取状态

        self.prefetch_outstanding: bool = False

        self.prefetch_addr: int = 0

        # 统计

        self.cycles: int = 0

        self.fetched_instructions: int = 0

        self.branches_encountered: int = 0

        self.branches_predicted: int = 0

        self.branches_mispredicted: int = 0





    def predict_branch(self, pc: int) -> Tuple[bool, int]:

        """分支预测"""

        # 查找BTB

        target = self.btb.lookup(pc)

        if target is not None:

            # 有BTB条目，预测taken

            return True, target

        # 无BTB，使用BHR预测（这里简化处理）

        if self.bhr & 1:

            # 预测taken，使用PC简单计算目标

            target = pc + 4 + ((self.bhr & 0xFF) << 2)

            return True, target

        return False, pc + self.fetch_width * 4





    def fetch(self) -> Fetch_Bundle:

        """执行一次取指"""

        self.cycles += 1

        bundle = Fetch_Bundle(

            pc=self.pc,

            instructions=[],

            valid_count=0

        )

        # 分支预测

        predicted_taken, predicted_target = self.predict_branch(self.pc)

        if predicted_taken:

            self.branches_predicted += 1

        # 尝试从ICache获取指令

        for i in range(self.fetch_width):

            addr = self.pc + i * 4

            hit, line = self.icache.lookup(addr)

            if hit:

                # 模拟从缓存行提取指令（这里简化用随机数）

                instr = random.randint(0, 0xFFFFFFFF)

                bundle.instructions.append(instr)

                bundle.valid_count += 1

                self.fetched_instructions += 1

                # 模拟检测分支（随机）

                if random.random() < 0.1:  # 10%概率是分支

                    self.branches_encountered += 1

                    target = addr + random.randint(1, 3) * 4

                    self.btb.update(addr, target)

            else:

                # ICache miss，模拟填充（这里简化处理）

                self.icache.fill(addr, bytes(64))

        # 更新PC

        if predicted_taken:

            bundle.taken = True

            bundle.target = predicted_target

            self.pc = predicted_target

        else:

            self.pc += bundle.valid_count * 4

        # 更新BHR

        self.bhr = ((self.bhr << 1) | (1 if predicted_taken else 0)) & ((1 << self.bhr_length) - 1)

        return bundle





    def run(self, num_cycles: int = 100):

        """运行IFU模拟指定周期"""

        print(f"=== IFU模拟 {num_cycles} 周期 ===")

        for i in range(num_cycles):

            bundle = self.fetch()

            if i % 20 == 0:

                print(f"Cycle {self.cycles}: PC=0x{self.pc:x}, fetched={bundle.valid_count}, taken={bundle.taken}")

        print(f"\n统计:")

        print(f"  总周期数: {self.cycles}")

        print(f"  总取指数: {self.fetched_instructions}")

        print(f"  分支数: {self.branches_encountered}")

        print(f"  分支预测数: {self.branches_predicted}")

        print(f"  ICache命中率: {self.icache.get_hit_rate():.2%}")





def basic_test():

    """基本功能测试"""

    print("=== IFU模拟器测试 ===")

    icache = Instruction_Cache(num_sets=64, associativity=4, line_size=64)

    ifu = Instruction_Fetch_Unit(fetch_width=4, icache=icache)

    # 模拟一些分支

    ifu.btb.update(0x1000, 0x2000)

    ifu.btb.update(0x2000, 0x3000)

    ifu.btb.update(0x3000, 0x4000)

    # 运行

    ifu.run(num_cycles=50)

    # 详细测试ICache

    print("\n=== ICache详细测试 ===")

    icache2 = Instruction_Cache(num_sets=8, associativity=2, line_size=16)

    test_addrs = [0x1000, 0x1004, 0x2000, 0x2004, 0x1000, 0x3000, 0x1004]

    for addr in test_addrs:

        hit, _ = icache2.lookup(addr)

        print(f"  addr=0x{addr:x}: {'HIT' if hit else 'MISS'}")

    print(f"  命中率: {icache2.get_hit_rate():.2%}")





if __name__ == "__main__":

    basic_test()


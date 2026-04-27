# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / linear_scan_reg



本文件实现 linear_scan_reg 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

from dataclasses import dataclass, field

import random



from liveness_analysis import LivenessAnalysis, LiveInterval





@dataclass

class RangeEndpoint:

    """区间端点"""

    position: int  # 位置(指令索引)

    is_start: bool  # True为起点, False为终点

    interval: LiveInterval  # 所属区间





class LinearScanAllocator:

    """

    线性扫描寄存器分配器



    算法步骤:

    1. 按区间起点排序所有活跃区间

    2. 维护当前活跃区间集合

    3. 遇到新区间起点时:

       - 释放已结束的区间

       - 如果有空闲寄存器,分配

       - 否则溢出某个区间到内存

    4. 遇到区间终点时: 释放寄存器

    """



    def __init__(self, live_analysis: LivenessAnalysis, num_registers: int = 16):

        self.live_analysis = live_analysis

        self.num_registers = num_registers

        self.free_registers: Set[int] = set()  # 空闲寄存器集合

        self.active: List[LiveInterval] = []  # 当前活跃区间(按终点排序)

        self.allocation: Dict[str, int] = {}  # 变量 -> 寄存器

        self.spilled: Set[str] = set()  # 溢出变量集合

        self.registers: List[str] = [f"r{i}" for i in range(num_registers)]



        # 初始化空闲寄存器

        for i in range(num_registers):

            self.free_registers.add(i)



    def allocate(self) -> Dict[str, int]:

        """

        执行线性扫描分配



        返回:

            变量 -> 寄存器编号 映射

        """

        intervals = self.live_analysis.intervals.copy()



        # 按起点排序

        intervals.sort(key=lambda x: x.start)



        # 创建事件点列表

        events = self._create_events(intervals)



        # 按位置处理事件

        current_position = -1

        for event in events:

            pos = event.position



            if pos != current_position:

                current_position = pos

                self._expire_old_intervals(pos)

                self._handle_interval_starts(intervals, pos)



        return self.allocation



    def _create_events(self, intervals: List[LiveInterval]) -> List[RangeEndpoint]:

        """创建事件点列表"""

        events = []



        for interval in intervals:

            events.append(RangeEndpoint(position=interval.start, is_start=True, interval=interval))

            events.append(RangeEndpoint(position=interval.end, is_start=False, interval=interval))



        # 按位置排序,起点优先于终点

        events.sort(key=lambda e: (e.position, e.is_start))

        return events



    def _expire_old_intervals(self, position: int):

        """

        过期已结束的区间,释放寄存器

        """

        expired = []

        for interval in self.active:

            if interval.end < position:

                expired.append(interval)



        for interval in expired:

            self.active.remove(interval)

            if interval.variable in self.allocation:

                reg = self.allocation[interval.variable]

                self.free_registers.add(reg)



    def _handle_interval_starts(self, intervals: List[LiveInterval], position: int):

        """处理当前位置开始的区间"""

        for interval in intervals:

            if interval.start == position:

                self._allocate_interval(interval)



    def _allocate_interval(self, interval: LiveInterval):

        """

        为单个区间分配寄存器

        """

        var = interval.variable



        # 如果已经分配,跳过

        if var in self.allocation:

            return



        # 查找空闲寄存器

        if self.free_registers:

            reg = self.free_registers.pop()

            self.allocation[var] = reg

            self._add_to_active(interval)

            return



        # 没有空闲寄存器,溢出

        self._spill_at_alloc(interval)



    def _spill_at_alloc(self, interval: LiveInterval):

        """

        溢出策略: 溢出终点最远的活跃区间

        """

        # 找到终点最远的区间

        spill_candidate = None

        max_end = -1



        for active_interval in self.active:

            if active_interval.end > max_end:

                max_end = active_interval.end

                spill_candidate = active_interval



        if spill_candidate and spill_candidate.end > interval.end:

            # 溢出终点更远的区间

            spilled_var = spill_candidate.variable

            reg = self.allocation.pop(spilled_var, None)

            if reg is not None:

                self.allocation[interval.variable] = reg

                self.spilled.add(spilled_var)

            else:

                # 没有寄存器可用,当前变量也溢出

                self.spilled.add(interval.variable)

        else:

            # 溢出当前区间

            self.spilled.add(interval.variable)



    def _add_to_active(self, interval: LiveInterval):

        """添加区间到活跃列表(按终点排序)"""

        # 按终点排序插入

        inserted = False

        for i, active_interval in enumerate(self.active):

            if interval.end < active_interval.end:

                self.active.insert(i, interval)

                inserted = True

                break



        if not inserted:

            self.active.append(interval)



    def get_register(self, var: str) -> str:

        """获取变量分配的寄存器名"""

        if var in self.allocation:

            reg_num = self.allocation[var]

            return self.registers[reg_num]

        return f"mem[{var}]"



    def is_spilled(self, var: str) -> bool:

        """检查变量是否溢出"""

        return var in self.spilled



    def get_statistics(self) -> Dict[str, int]:

        """获取分配统计"""

        return {

            "total_variables": len(self.allocation) + len(self.spilled),

            "allocated": len(self.allocation),

            "spilled": len(self.spilled),

            "register_count": self.num_registers

        }





def print_allocation_result(allocator: LinearScanAllocator):

    """打印分配结果"""

    stats = allocator.get_statistics()



    print("=== 线性扫描寄存器分配结果 ===")

    print(f"总变量数: {stats['total_variables']}")

    print(f"寄存器分配: {stats['allocated']}")

    print(f"溢出变量: {stats['spilled']}")



    print("\n分配详情:")

    for var, reg_num in sorted(allocator.allocation.items()):

        print(f"  {var} -> r{reg_num}")



    if allocator.spilled:

        print(f"\n溢出变量:")

        for var in sorted(allocator.spilled):

            print(f"  {var} -> [溢出]")





def compare_allocators(live: LivenessAnalysis, num_regs: int = 8):

    """比较不同分配策略"""

    from register_alloc_graph import RegisterAllocator



    print(f"\n{'='*50}")

    print(f"比较寄存器分配 (寄存器数={num_regs})")

    print(f"{'='*50}")



    # 图着色

    print("\n1. 图着色算法:")

    gc_allocator = RegisterAllocator(live, num_registers=num_regs)

    gc_allocator.allocate()

    gc_spilled = len([v for v in gc_allocator.color if gc_allocator.color[v] < 0])

    print(f"   溢出: {gc_spilled}")



    # 线性扫描

    print("\n2. 线性扫描算法:")

    ls_allocator = LinearScanAllocator(live, num_registers=num_regs)

    ls_allocator.allocate()

    ls_stats = ls_allocator.get_statistics()

    print(f"   溢出: {ls_stats['spilled']}")



    return gc_spilled, ls_stats['spilled']





if __name__ == "__main__":

    from intermediate_representation import IRGenerator, Address, OpCode

    from basic_block import BasicBlockBuilder

    from cfg_builder import ControlFlowGraph



    # 生成测试IR - 模拟复杂寄存器使用

    gen = IRGenerator()



    # 多变量同时活跃

    t1 = gen.new_temp()

    t2 = gen.new_temp()

    t3 = gen.new_temp()

    t4 = gen.new_temp()

    t5 = gen.new_temp()



    gen.emit_binary(OpCode.ADD, t1, Address.variable("a"), Address.variable("b"))

    gen.emit_binary(OpCode.MUL, t2, t1, Address.variable("c"))

    gen.emit_binary(OpCode.SUB, t3, t2, Address.variable("d"))

    gen.emit_binary(OpCode.ADD, t4, t3, Address.variable("e"))

    gen.emit_binary(OpCode.MUL, t5, t4, Address.variable("f"))

    gen.emit(OpCode.STORE, result=Address.variable("result"), arg1=t5)



    instructions = gen.generate()



    # 构建CFG和活跃性分析

    builder = BasicBlockBuilder()

    blocks = builder.build(instructions)

    cfg = ControlFlowGraph(blocks)

    live = LivenessAnalysis(instructions, cfg)

    live.analyze()



    # 打印活跃区间

    print("=== 活跃区间 ===")

    for interval in live.intervals:

        print(f"  {interval.variable}: [{interval.start}, {interval.end}]")



    # 线性扫描分配

    print("\n" + "="*50)

    allocator = LinearScanAllocator(live, num_registers=4)

    allocator.allocate()

    print_allocation_result(allocator)



    # 比较不同寄存器数量

    print("\n" + "="*50)

    print("不同寄存器数量的分配结果:")

    for num_regs in [2, 3, 4, 6, 8]:

        ls_allocator = LinearScanAllocator(live, num_registers=num_regs)

        ls_allocator.allocate()

        stats = ls_allocator.get_statistics()

        print(f"  {num_regs} 寄存器: 溢出 {stats['spilled']} 个变量")


# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / register_file

本文件实现 register_file 相关的算法功能。
"""

import random
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class Rename_Table:
    """寄存器重命名表"""
    # 逻辑寄存器到物理寄存器的映射
    map_table: Dict[int, int] = field(default_factory=dict)
    # 逻辑寄存器总数
    num_logical: int = 16


@dataclass
class Physical_Register_File:
    """物理寄存器文件"""
    # 物理寄存器总数
    num_physical: int = 64
    # 空闲物理寄存器列表
    free_list: List[int] = field(default_factory=list)
    # 物理寄存器当前值（None表示未初始化或待计算）
    values: List[Optional[int]] = field(default_factory=lambda: [None] * 64)
    # 物理寄存器是否已写入（用于调度判断）
    written: List[bool] = field(default_factory=lambda: [False] * 64)


class Register_Renamer:
    """寄存器重命名器"""
    def __init__(self, num_logical: int = 16, num_physical: int = 64):
        self.num_logical = num_logical              # 逻辑寄存器数
        self.num_physical = num_physical            # 物理寄存器数
        # 初始化重命名表（逻辑寄存器0-15映射到物理寄存器0-15）
        self.rename_table = Rename_Table(num_logical=num_logical)
        for i in range(num_logical):
            self.rename_table.map_table[i] = i
        # 初始化物理寄存器文件
        self.phys_reg_file = Physical_Register_File(
            num_physical=num_physical
        )
        # 物理寄存器0-15保留给逻辑寄存器初始映射，其余加入空闲列表
        self.phys_reg_file.free_list = list(range(num_logical, num_physical))
        # 已映射逻辑寄存器集合
        self.mapped_logical: Set[int] = set(range(num_logical))


    def rename_dest(self, logical_reg: int) -> Optional[int]:
        """为目的操作数分配新的物理寄存器（重命名）"""
        # 检查是否有空闲物理寄存器
        if not self.phys_reg_file.free_list:
            return None  # 重命名失败，无可用寄存器
        # 分配新的物理寄存器
        new_phys = self.phys_reg_file.free_list.pop(0)
        # 记录旧映射（用于ROB恢复）
        old_phys = self.rename_table.map_table.get(logical_reg)
        # 更新重命名表
        self.rename_table.map_table[logical_reg] = new_phys
        self.mapped_logical.add(logical_reg)
        return new_phys


    def rename_src(self, logical_reg: int) -> int:
        """为源操作数查找当前映射的物理寄存器"""
        return self.rename_table.map_table.get(logical_reg, logical_reg)


    def restore(self, logical_reg: int, old_phys: Optional[int]):
        """恢复旧映射（ROB回滚时调用）"""
        if old_phys is None:
            # 从已映射中移除
            self.mapped_logical.discard(logical_reg)
            if logical_reg in self.rename_table.map_table:
                old = self.rename_table.map_table[logical_reg]
                del self.rename_table.map_table[logical_reg]
                # 释放当前映射的物理寄存器
                self.free_phys_reg(old)
        else:
            self.rename_table.map_table[logical_reg] = old_phys


    def free_phys_reg(self, phys_reg: int):
        """释放物理寄存器（加入空闲列表）"""
        if phys_reg >= self.num_logical:  # 不释放保留的物理寄存器
            self.phys_reg_file.values[phys_reg] = None
            self.phys_reg_file.written[phys_reg] = False
            if phys_reg not in self.phys_reg_file.free_list:
                self.phys_reg_file.free_list.append(phys_reg)


    def write_reg(self, phys_reg: int, value: int):
        """写入物理寄存器"""
        if 0 <= phys_reg < self.num_physical:
            self.phys_reg_file.values[phys_reg] = value
            self.phys_reg_file.written[phys_reg] = True


    def read_reg(self, phys_reg: int) -> Optional[int]:
        """读取物理寄存器值"""
        if 0 <= phys_reg < self.num_physical:
            return self.phys_reg_file.values[phys_reg]
        return None


    def is_ready(self, phys_reg: int) -> bool:
        """判断物理寄存器是否已就绪（已写入）"""
        if 0 <= phys_reg < self.num_physical:
            return self.phys_reg_file.written[phys_reg]
        return True  # 保留寄存器视为永远就绪


    def get_free_count(self) -> int:
        """获取当前空闲物理寄存器数量"""
        return len(self.phys_reg_file.free_list)


    def snapshot(self) -> Dict[int, int]:
        """获取重命名表快照（用于Speculative执行）"""
        return dict(self.rename_table.map_table)


    def restore_snapshot(self, snapshot: Dict[int, int], freed_since: Set[int]):
        """从快照恢复重命名表"""
        self.rename_table.map_table = dict(snapshot)
        # 释放快照之后分配的新物理寄存器
        for phys in freed_since:
            self.free_phys_reg(phys)


class Instruction_Rename:
    """带重命名信息的指令"""
    def __init__(self, id: int, dest_logical: Optional[int], src1_logical: Optional[int], src2_logical: Optional[int]):
        self.id = id
        self.dest_logical = dest_logical          # 目的逻辑寄存器
        self.dest_physical: Optional[int] = None  # 目的物理寄存器（重命名后）
        self.src1_logical = src1_logical
        self.src1_physical: Optional[int] = None  # 源1物理寄存器（重命名后）
        self.src2_logical = src2_logical
        self.src2_physical: Optional[int] = None  # 源2物理寄存器（重命名后）


def rename_instruction(instr: Instruction_Rename, renamer: Register_Renamer) -> bool:
    """对单条指令执行寄存器重命名"""
    # 重命名目的寄存器
    if instr.dest_logical is not None:
        instr.dest_physical = renamer.rename_dest(instr.dest_logical)
        if instr.dest_physical is None:
            return False  # 重命名失败
    # 重命名源寄存器
    if instr.src1_logical is not None:
        instr.src1_physical = renamer.rename_src(instr.src1_logical)
    if instr.src2_logical is not None:
        instr.src2_physical = renamer.rename_src(instr.src2_logical)
    return True


def basic_test():
    """基本功能测试"""
    print("=== 寄存器文件与重命名测试 ===")
    renamer = Register_Renamer(num_logical=16, num_physical=64)
    print(f"逻辑寄存器数: {renamer.num_logical}")
    print(f"物理寄存器数: {renamer.num_physical}")
    print(f"初始空闲物理寄存器数: {renamer.get_free_count()}")
    # 重命名一些寄存器
    renamed = []
    for i in range(8):
        instr = Instruction_Rename(id=i, dest_logical=i % 16, src1_logical=(i + 1) % 16, src2_logical=(i + 2) % 16)
        success = rename_instruction(instr, renamer)
        if success:
            renamed.append(instr)
            print(f"  指令{i}: 逻辑目的寄存器 r{instr.dest_logical} -> 物理寄存器 p{instr.dest_physical}")
    print(f"\n重命名后空闲物理寄存器数: {renamer.get_free_count()}")
    # 写入一些值
    for instr in renamed[:4]:
        renamer.write_reg(instr.dest_physical, random.randint(1, 100))
    # 读取验证
    print("\n读取验证:")
    for instr in renamed[:4]:
        val = renamer.read_reg(instr.dest_physical)
        ready = renamer.is_ready(instr.dest_physical)
        print(f"  物理寄存器 p{instr.dest_physical}: 值={val}, 已就绪={ready}")


if __name__ == "__main__":
    basic_test()

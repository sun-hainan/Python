# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / branch_target_buffer

本文件实现 branch_target_buffer 相关的算法功能。
"""

import random
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from enum import Enum


class BTB_Entry_State(Enum):
    """BTB条目状态"""
    INVALID = 0      # 无效（从未被占用）
    VALID = 1        # 有效
    WEAKLY_TAKEN = 2 # 弱分支
    WEAKLY_NOT = 3   # 弱不分支
    STRONGLY_TAKEN = 4   # 强分支
    STRONGLY_NOT = 5     # 强不分支


@dataclass
class BTB_Entry:
    """BTB条目"""
    tag: int = 0                 # 标签（用于区分不同分支）
    target: int = 0              # 分支目标地址
    state: BTB_Entry_State = BTB_Entry_State.INVALID  # 状态
    branch_type: str = "unknown" # 分支类型（call/ret/cond/uncond）


class Branch_History_Buffer:
    """分支历史缓冲（BHB），记录近期分支方向历史"""
    def __init__(self, size: int = 8):
        self.size = size                      # BHB位宽
        self.history: int = 0                 # 历史寄存器（位向量）


    def update(self, taken: bool):
        """更新分支历史"""
        self.history = ((self.history << 1) | (1 if taken else 0)) & ((1 << self.size) - 1)


    def get_history(self) -> int:
        """获取当前历史值"""
        return self.history


    def shift_distance(self, distance: int) -> int:
        """获取指定距离的历史值"""
        if distance <= 0 or distance > self.size:
            return self.history
        mask = (1 << distance) - 1
        return (self.history >> (self.size - distance)) & mask


class Branch_Target_Buffer:
    """分支目标缓冲器"""
    def __init__(self, num_entries: int = 256, tag_bits: int = 16, addr_bits: int = 32):
        self.num_entries = num_entries        # BTB条目数（2的幂）
        self.tag_bits = tag_bits              # 标签位数
        self.addr_bits = addr_bits            # 地址位数
        self.index_bits = addr_bits - tag_bits # 索引位数
        self.index_mask = (1 << self.index_bits) - 1  # 索引掩码
        self.tag_mask = (1 << tag_bits) - 1            # 标签掩码
        # BTB存储数组
        self.entries: List[BTB_Entry] = [BTB_Entry() for _ in range(num_entries)]
        # BHB（用于全局历史）
        self.bhb = Branch_History_Buffer(size=8)
        # 命中/未命中统计
        self.hits: int = 0
        self.misses: int = 0


    def _extract_index(self, pc: int) -> int:
        """从PC中提取索引"""
        return pc & self.index_mask


    def _extract_tag(self, pc: int) -> int:
        """从PC中提取标签"""
        return (pc >> self.index_bits) & self.tag_mask


    def lookup(self, pc: int) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        BTB查找
        返回: (命中标志, 目标地址, 分支类型)
        """
        index = self._extract_index(pc)
        tag = self._extract_tag(pc)
        entry = self.entries[index]
        # 检查标签匹配和有效性
        if entry.tag == tag and entry.state != BTB_Entry_State.INVALID:
            self.hits += 1
            return True, entry.target, entry.branch_type
        self.misses += 1
        return False, None, None


    def update_btb(self, pc: int, target: int, branch_type: str = "cond", taken: bool = True):
        """更新BTB条目"""
        index = self._extract_index(pc)
        tag = self._extract_tag(pc)
        entry = self.entries[index]
        # 更新标签和目标
        entry.tag = tag
        entry.target = target
        entry.branch_type = branch_type
        # 更新状态机
        if entry.state == BTB_Entry_State.INVALID:
            entry.state = BTB_Entry_State.WEAKLY_TAKEN if taken else BTB_Entry_State.WEAKLY_NOT
        elif entry.state == BTB_Entry_State.WEAKLY_NOT and not taken:
            entry.state = BTB_Entry_State.STRONGLY_NOT
        elif entry.state == BTB_Entry_State.WEAKLY_TAKEN and taken:
            entry.state = BTB_Entry_State.STRONGLY_TAKEN
        elif entry.state == BTB_Entry_State.STRONGLY_NOT and taken:
            entry.state = BTB_Entry_State.WEAKLY_NOT
        elif entry.state == BTB_Entry_State.STRONGLY_TAKEN and not taken:
            entry.state = BTB_Entry_State.WEAKLY_TAKEN
        elif entry.state == BTB_Entry_State.WEAKLY_NOT and taken:
            entry.state = BTB_Entry_State.WEAKLY_TAKEN
        elif entry.state == BTB_Entry_State.WEAKLY_TAKEN and not taken:
            entry.state = BTB_Entry_State.WEAKLY_NOT


    def predict(self, pc: int) -> bool:
        """基于BTB状态预测分支方向"""
        index = self._extract_index(pc)
        entry = self.entries[index]
        if entry.state in [BTB_Entry_State.INVALID, BTB_Entry_State.WEAKLY_NOT, BTB_Entry_State.STRONGLY_NOT]:
            return False
        return True


    def update_history(self, taken: bool):
        """更新全局分支历史"""
        self.bhb.update(taken)


    def get_hit_rate(self) -> float:
        """计算BTB命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class BTBSimulator:
    """BTB模拟器（高层封装）"""
    def __init__(self, num_entries: int = 256):
        self.btb = Branch_Target_Buffer(num_entries=num_entries)
        # PC模拟器
        self.pc: int = 0x1000
        # 指令计数
        self.instr_count: int = 0


    def step(self, branch: bool, target: int, branch_type: str = "cond"):
        """模拟一步执行"""
        self.instr_count += 1
        # 查找BTB
        hit, predicted_target, btype = self.btb.lookup(self.pc)
        # 预测
        predicted_taken = self.btb.predict(self.pc) if hit else False
        # 更新BTB
        self.btb.update_btb(self.pc, target, branch_type, branch)
        self.btb.update_history(branch)
        # 更新PC
        if predicted_taken and hit:
            self.pc = predicted_target
        else:
            self.pc += 4


def basic_test():
    """基本功能测试"""
    print("=== BTB模拟器测试 ===")
    sim = BTBSimulator(num_entries=64)
    # 模拟一些分支指令
    branches = [
        (True, 0x2000, "cond"),   # 分支到0x2000
        (True, 0x3000, "cond"),   # 分支到0x3000
        (False, 0x4000, "cond"), # 不分支
        (True, 0x5000, "uncond"), # 无条件跳转
        (True, 0x2000, "cond"),   # 重复分支（测试命中）
        (True, 0x3000, "cond"),   # 重复分支（测试命中）
    ]
    print("执行分支序列:")
    for i, (branch, target, btype) in enumerate(branches):
        sim.step(branch, target, btype)
        print(f"  步骤{i+1}: PC=0x{sim.pc:x}, 分支={'采取' if branch else '不采取'}, 目标=0x{target:x}")
    print(f"\nBTB统计:")
    print(f"  命中次数: {sim.btb.hits}")
    print(f"  未命中次数: {sim.btb.misses}")
    print(f"  命中率: {sim.btb.get_hit_rate():.2%}")
    print(f"  全局历史: {sim.btb.bhb.get_history():08b}")


if __name__ == "__main__":
    basic_test()

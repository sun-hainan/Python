# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / indirect_branch_predictor

本文件实现 indirect_branch_predictor 相关的算法功能。
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Predictor_Type(Enum):
    """预测器类型"""
    BHR = "Branch History Register"
    BTB_ONLY = "BTB Only"
    TARGET_CACHE = "Target Cache"
    ITTAGE = "Indirect Target Predictor"


@dataclass
class Global_BHR:
    """全局分支历史寄存器"""
    bits: int = 0           # 历史位向量
    length: int = 16        # 历史长度
    mask: int = 0xFFFF      # 掩码


    def update(self, taken: bool):
        """左移并追加分支结果"""
        self.bits = ((self.bits << 1) | (1 if taken else 0)) & self.mask


    def get_bits(self) -> int:
        """获取当前历史值"""
        return self.bits


@dataclass
class Path_History:
    """路径历史：记录近期分支目标PC"""
    history: List[int] = field(default_factory=list)
    max_length: int = 16


    def push(self, pc: int):
        """追加PC到路径历史"""
        self.history.append(pc)
        if len(self.history) > self.max_length:
            self.history.pop(0)


    def get_path_hash(self) -> int:
        """计算路径历史的哈希值"""
        result = 0
        for pc in self.history:
            result = ((result << 5) - result + pc) & 0xFFFF
        return result


class Target_Cache:
    """目标缓存：存储(PC, 历史) -> 目标的映射"""
    def __init__(self, num_entries: int = 256):
        self.num_entries = num_entries
        self.entries: Dict[Tuple[int, int], int] = {}
        self.hits: int = 0
        self.misses: int = 0


    def lookup(self, pc: int, history: int) -> Optional[int]:
        """查找预测目标"""
        key = (pc, history)
        if key in self.entries:
            self.hits += 1
            return self.entries[key]
        self.misses += 1
        return None


    def update(self, pc: int, history: int, target: int):
        """更新目标缓存"""
        key = (pc, history)
        self.entries[key] = target
        # 简单淘汰策略：超过容量限制时删除最旧条目
        if len(self.entries) > self.num_entries:
            oldest_key = next(iter(self.entries))
            del self.entries[oldest_key]


class BHR_Indirect_Predictor:
    """基于BHR的间接分支预测器"""
    def __init__(self, bhr_length: int = 16, target_entries: int = 256):
        self.bhr_length = bhr_length
        self.mask = (1 << bhr_length) - 1
        self.bhr = Global_BHR(length=bhr_length)
        self.target_cache = Target_Cache(num_entries=target_entries)
        # 每个历史模式对应一个目标缓存
        self.history_tables: Dict[int, Target_Cache] = {}


    def predict(self, pc: int) -> Optional[int]:
        """预测间接分支目标"""
        history = self.bhr.get_bits()
        # 多级历史模式
        for pattern_len in [4, 8, 16]:
            pattern = history & ((1 << pattern_len) - 1)
            if pattern not in self.history_tables:
                self.history_tables[pattern] = Target_Cache(num_entries=64)
            target = self.history_tables[pattern].lookup(pc, pattern)
            if target is not None:
                return target
        # 回退到全局目标缓存
        return self.target_cache.lookup(pc, history)


    def update(self, pc: int, target: int, taken: bool):
        """更新预测器状态"""
        history = self.bhr.get_bits()
        # 更新历史表
        for pattern_len in [4, 8, 16]:
            pattern = history & ((1 << pattern_len) - 1)
            if pattern not in self.history_tables:
                self.history_tables[pattern] = Target_Cache(num_entries=64)
            self.history_tables[pattern].update(pc, pattern, target)
        # 更新全局缓存
        self.target_cache.update(pc, history, target)
        # 更新BHR
        self.bhr.update(taken)


class ITTAGE_Predictor:
    """
    ITTAGE (Indirect Target Predictor with TAGE-like design)
    借鉴TAGE的思想，使用多个基于不同历史长度的预测表
    """
    def __init__(self):
        # 基础预测器（无历史）
        self.base_predictor: Dict[int, int] = {}
        # 多个带历史的预测器
        self.history_predictors: Dict[int, Dict[int, int]] = {
            4: {},   # 历史长度4
            8: {},   # 历史长度8
            16: {},  # 历史长度16
        }
        self.bhr = Global_BHR(length=16)
        self.used_provider: Optional[int] = None  # 使用的预测器
        self.hits: int = 0
        self.misses: int = 0


    def _hash_pc_history(self, pc: int, history: int, hist_len: int) -> int:
        """计算PC和历史的混合哈希"""
        return ((pc ^ (history << (32 - hist_len))) & 0xFFFF)


    def predict(self, pc: int) -> Optional[int]:
        """使用最长的匹配历史进行预测"""
        history = self.bhr.get_bits()
        best_target = None
        best_len = -1
        # 尝试从最长历史开始
        for hist_len in [16, 8, 4]:
            h = history & ((1 << hist_len) - 1)
            key = self._hash_pc_history(pc, h, hist_len)
            if key in self.history_predictors[hist_len]:
                target = self.history_predictors[hist_len][key]
                best_target = target
                best_len = hist_len
                break
        # 如果没有历史匹配，使用基础预测器
        if best_target is None:
            best_target = self.base_predictor.get(pc)
            self.used_provider = 0
        else:
            self.used_provider = best_len
        return best_target


    def update(self, pc: int, target: int, taken: bool):
        """更新预测器"""
        history = self.bhr.get_bits()
        # 更新基础预测器
        self.base_predictor[pc] = target
        # 更新历史预测器
        for hist_len in [4, 8, 16]:
            h = history & ((1 << hist_len) - 1)
            key = self._hash_pc_history(pc, h, hist_len)
            self.history_predictors[hist_len][key] = target
        # 更新BHR
        self.bhr.update(taken)


def basic_test():
    """基本功能测试"""
    print("=== 间接分支预测器测试 ===")
    # 测试BHR预测器
    bhr_pred = BHR_Indirect_Predictor(bhr_length=16, target_entries=256)
    print("\n[BHR间接分支预测器]")
    # 模拟虚函数调用场景
    virtual_calls = [
        (0x1000, 0x2000),  # obj.method() -> A::method
        (0x1000, 0x3000),  # obj.method() -> B::method
        (0x1000, 0x2000),  # obj.method() -> A::method
        (0x1000, 0x3000),  # obj.method() -> B::method
        (0x1000, 0x2000),  # obj.method() -> A::method
    ]
    print("虚函数调用序列:")
    for i, (pc, target) in enumerate(virtual_calls):
        pred = bhr_pred.predict(pc)
        bhr_pred.update(pc, target, taken=True)
        match = "✓" if pred == target else "✗" if pred else "?"
        print(f"  调用{i+1}: PC=0x{pc:x}, 目标=0x{target:x}, 预测=0x{pred if pred else 0:x} {match}")
    print(f"\nBHR预测器统计: 命中={bhr_pred.target_cache.hits}, 未命中={bhr_pred.target_cache.misses}")
    # 测试ITTAGE预测器
    itage = ITTAGE_Predictor()
    print("\n[ITTAGE间接分支预测器]")
    print("间接跳转表查找序列:")
    for i, (pc, target) in enumerate(virtual_calls):
        pred = itage.predict(pc)
        itage.update(pc, target, taken=True)
        match = "✓" if pred == target else "✗" if pred else "?"
        provider = f"(基础)" if itage.used_provider == 0 else f"(历史{itage.used_provider})"
        print(f"  跳转{i+1}: PC=0x{pc:x}, 目标=0x{target:x}, 预测=0x{pred if pred else 0:x} {match} {provider if pred else ''}")


if __name__ == "__main__":
    basic_test()

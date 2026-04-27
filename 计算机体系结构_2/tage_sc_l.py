# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构_2 / tage_sc_l

本文件实现 tage_sc_l 相关的算法功能。
"""

import random
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class Tage_Table_Entry:
    """TAGE表条目"""
    counter: int = 0           # 2位饱和计数器
    tag: int = 0               # 标签
    useful: int = 0            # 有用计数器（用于淘汰）


class Tage_Table:
    """TAGE表"""
    def __init__(self, num_entries: int, tag_bits: int, history_length: int):
        self.num_entries = num_entries
        self.tag_bits = tag_bits
        self.history_length = history_length
        self.index_mask = num_entries - 1
        self.tag_mask = (1 << tag_bits) - 1
        self.entries: List[Optional[Tage_Table_Entry]] = [None] * num_entries
        for i in range(num_entries):
            self.entries[i] = Tage_Table_Entry()
        # 初始化计数器为弱不taken状态
        for entry in self.entries:
            entry.counter = 1  # WN


    def _compute_index(self, pc: int, history: int) -> int:
        """计算索引（PC和历史的哈希）"""
        # 简单的哈希：PC XOR history
        return ((pc ^ (history & 0xFFFF)) & self.index_mask)


    def _compute_tag(self, pc: int, history: int) -> int:
        """计算标签"""
        return ((pc ^ (history >> 3)) & self.tag_mask)


    def lookup(self, pc: int, history: int) -> Tuple[bool, int, int]:
        """
        查找TAGE表
        返回: (是否命中, 索引, 预测方向)
        """
        idx = self._compute_index(pc, history)
        tag = self._compute_tag(pc, history)
        entry = self.entries[idx]
        if entry.tag == tag:
            # 命中
            prediction = entry.counter >= 2
            return True, idx, prediction
        return False, idx, 1  # 默认弱不taken


class Tage_Predictor:
    """TAGE分支预测器"""
    def __init__(self):
        # 基础预测器（直接映射，无历史）
        self.base_predictor: List[int] = [1] * 256  # 2位计数器表
        # TAGE表：多个历史长度（几何级数）
        self.history_lengths = [4, 8, 16, 32, 64, 128]
        self.tables: List[Tage_Table] = []
        for hist_len in self.history_lengths:
            num_entries = 256 >> (self.history_lengths.index(hist_len) // 2)
            self.tables.append(Tage_Table(num_entries=max(16, num_entries), tag_bits=8, history_length=hist_len))
        # 全局分支历史
        self.global_history: int = 0
        self.ghr_length: int = max(self.history_lengths) if self.history_lengths else 128
        # 统计
        self.total_predictions: int = 0
        self.correct_predictions: int = 0
        self.tage_hits: int = 0
        self.base_hits: int = 0


    def _get_alt_pred(self, pc: int, history: int) -> bool:
        """获取备用预测（使用更短的历史）"""
        for table in reversed(self.tables):
            hit, _, pred = table.lookup(pc, history)
            if hit:
                return pred
        return self.base_predictor[pc & 0xFF] >= 2


    def predict(self, pc: int) -> bool:
        """预测分支方向"""
        self.total_predictions += 1
        history = self.global_history
        # 从最长历史开始查找
        provider_pred: Optional[bool] = None
        provider_table_idx: int = -1
        for i, table in enumerate(self.tables):
            hit, idx, pred = table.lookup(pc, history)
            if hit:
                provider_pred = pred
                provider_table_idx = i
                self.tage_hits += 1
                break
        if provider_pred is not None:
            return provider_pred
        # 无TAGE命中，使用基础预测器
        self.base_hits += 1
        return self.base_predictor[pc & 0xFF] >= 2


    def update(self, pc: int, actual: bool):
        """更新预测器"""
        history = self.global_history
        # 找到提供预测的表
        provider_idx = -1
        for i, table in enumerate(self.tables):
            hit, idx, _ = table.lookup(pc, history)
            if hit:
                provider_idx = i
                break
        # 更新命中的表
        if provider_idx >= 0:
            table = self.tables[provider_idx]
            idx = table._compute_index(pc, history)
            entry = table.entries[idx]
            # 更新计数器
            if actual:
                entry.counter = min(3, entry.counter + 1)
            else:
                entry.counter = max(0, entry.counter - 1)
            # 更新统计
            predicted = entry.counter >= 2
            if predicted == actual:
                self.correct_predictions += 1
        else:
            # 更新基础预测器
            idx = pc & 0xFF
            if actual:
                self.base_predictor[idx] = min(3, self.base_predictor[idx] + 1)
            else:
                self.base_predictor[idx] = max(0, self.base_predictor[idx] - 1)
            predicted = self.base_predictor[idx] >= 2
            if predicted == actual:
                self.correct_predictions += 1
        # 更新全局历史
        self.global_history = ((self.global_history << 1) | (1 if actual else 0)) & ((1 << self.ghr_length) - 1)


class SC_Predictor:
    """SC（Statistical Corrector）预测器：用于纠正TAGE的错误预测"""
    def __init__(self, Tage_Predictor):
        self.tage = Tage_Predictor
        # 纠错表
        self.corrector_table: List[int] = [0] * 256  # +1/-1计数器
        self.total_corrections: int = 0
        self.correction_accuracy: int = 0


    def predict(self, pc: int) -> bool:
        """预测（先TAGE，再SC纠错）"""
        tage_pred = self.tage.predict(pc)
        # 获取一些额外信息用于纠错
        history = self.tage.global_history
        confidence = self._get_confidence(pc, history)
        # 低置信度时考虑纠错
        if confidence < 2:  # 低置信度
            corrector_idx = (pc ^ (history & 0xFF)) & 0xFF
            correction = self.corrector_table[corrector_idx]
            if correction > 0:
                return True
            elif correction < 0:
                return False
        return tage_pred


    def _get_confidence(self, pc: int, history: int) -> int:
        """获取TAGE预测的置信度"""
        for table in reversed(self.tage.tables):
            hit, idx, pred = table.lookup(pc, history)
            if hit:
                return table.entries[idx].counter
        return 1  # 基础预测器，弱置信度


    def update(self, pc: int, actual: bool):
        """更新SC预测器"""
        # 先更新TAGE
        self.tage.update(pc, actual)
        # 检查是否需要纠错
        tage_pred = self.tage.base_predictor[pc & 0xFF] >= 2 if not any(t.lookup(pc, self.tage.global_history)[0] for t in self.tage.tables) else False
        # 获取实际使用的预测（简化）
        history = self.tage.global_history
        provider_idx = -1
        for i, table in enumerate(self.tage.tables):
            hit, _, _ = table.lookup(pc, history)
            if hit:
                provider_idx = i
                break
        if provider_idx >= 0:
            table = self.tage.tables[provider_idx]
            idx = table._compute_index(pc, history)
            pred = table.entries[idx].counter >= 2
            if pred != actual:
                # TAGE预测错误，更新SC
                corrector_idx = (pc ^ (history & 0xFF)) & 0xFF
                if actual:
                    self.corrector_table[corrector_idx] = min(3, self.corrector_table[corrector_idx] + 1)
                else:
                    self.corrector_table[corrector_idx] = max(-3, self.corrector_table[corrector_idx] - 1)
                self.total_corrections += 1


class L_Predictor:
    """L（Loop）预测器：检测和预测循环分支"""
    def __init__(self):
        # 循环检测表：(pc -> (count, current_iter, direction))
        self.loop_table: Dict[int, Tuple[int, int, str]] = {}
        self.loop_predictions: int = 0


    def predict(self, pc: int) -> Optional[bool]:
        """预测循环分支，返回None表示不是循环分支"""
        if pc in self.loop_table:
            count, current, direction = self.loop_table[pc]
            if count > 2:  # 至少执行3次才算循环
                self.loop_predictions += 1
                if direction == "up":
                    # 递增方向，正在循环中
                    return True
                else:
                    return False
        return None


    def update(self, pc: int, actual: bool):
        """更新循环预测器"""
        if pc not in self.loop_table:
            self.loop_table[pc] = (1, 0, "up" if actual else "down")
        else:
            count, current, direction = self.loop_table[pc]
            if direction == "up" and actual:
                # 继续循环
                self.loop_table[pc] = (count, current + 1, "up")
            elif direction == "up" and not actual:
                # 循环结束
                self.loop_table[pc] = (current + 1, 0, "down")
            elif direction == "down" and not actual:
                # 继续不taken
                self.loop_table[pc] = (count, 0, "down")
            elif direction == "down" and actual:
                # 新的循环开始
                self.loop_table[pc] = (1, 0, "up")


def basic_test():
    """基本功能测试"""
    print("=== TAGE-SC-L 分支预测器测试 ===")
    tage = Tage_Predictor()
    print(f"TAGE历史长度: {tage.history_lengths}")
    # 模拟分支序列
    branches = []
    for i in range(100):
        taken = random.random() < 0.7  # 70% taken
        branches.append(taken)
    print(f"\n模拟 {len(branches)} 条分支:")
    for i, actual in enumerate(branches):
        pred = tage.predict(0x1000 + i * 4)
        tage.update(0x1000 + i * 4, actual)
        if i < 20:
            match = "✓" if pred == actual else "✗"
            print(f"  分支{i}: 预测={'T' if pred else 'N'}, 实际={'T' if actual else 'N'} {match}")
    print(f"\n统计:")
    print(f"  总预测: {tage.total_predictions}")
    print(f"  正确: {tage.correct_predictions}")
    print(f"  准确率: {tage.correct_predictions / tage.total_predictions:.2%}")
    print(f"  TAGE命中: {tage.tage_hits}")
    print(f"  基础预测: {tage.base_hits}")
    # 测试完整TAGE-SC-L
    print("\n" + "=" * 50)
    print("\nTAGE-SC-L 组合预测器测试:")
    tage_pred = Tage_Predictor()
    sc = SC_Predictor(tage_pred)
    l_pred = L_Predictor()
    print("模拟100条分支:")
    for i in range(100):
        actual = random.random() < 0.6
        # 先尝试L预测
        l_result = l_pred.predict(0x1000 + i * 4)
        if l_result is not None:
            pred = l_result
        else:
            pred = sc.predict(0x1000 + i * 4)
        l_pred.update(0x1000 + i * 4, actual)
        sc.update(0x1000 + i * 4, actual)
    print(f"  SC纠错次数: {sc.total_corrections}")


if __name__ == "__main__":
    basic_test()

# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / rfid_collision

本文件实现 rfid_collision 相关的算法功能。
"""

import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class RFIDState(Enum):
    """RFID标签状态"""
    READY = 0      # 就绪
    TRANSMIT = 1   # 传输中
    SUCCESS = 2   # 成功识别
    COLLISION = 3 # 碰撞
    IDLE = 4      # 空闲


@dataclass
class RFIDTag:
    """RFID标签"""
    tag_id: str
    state: RFIDState = RFIDState.READY
    attempts: int = 0
    
    def reset(self):
        self.state = RFIDState.READY
        self.attempts = 0


@dataclass
class RFIDReader:
    """RFID阅读器"""
    reader_id: str
    num_slots: int = 16  # 时隙数
    frame_size: int = 16


class PureALOHA:
    """
    纯ALOHA防碰撞算法
    
    标签随机选择时间发送，无时隙概念
    碰撞概率高，效率低 (约18%)
    """
    
    def __init__(self, num_tags: int):
        self.num_tags = num_tags
        self.tags = [RFIDTag(f"TAG-{i:04d}") for i in range(num_tags)]
        
        # 统计
        self.total_slots = 0
        self.successful = 0
        self.collisions = 0
    
    def simulate_round(self) -> Tuple[int, int, int]:
        """
        模拟一轮传输
        
        Returns:
            (成功数, 碰撞数, 空闲数)
        """
        self.total_slots += 1
        
        # 每个标签独立决定是否发送
        transmitting = [t for t in self.tags 
                       if t.state == RFIDState.READY 
                       and random.random() < 0.3]  # 30%概率发送
        
        if len(transmitting) == 1:
            # 成功
            transmitting[0].state = RFIDState.SUCCESS
            self.successful += 1
            return 1, 0, 0
        elif len(transmitting) > 1:
            # 碰撞
            for t in transmitting:
                t.state = RFIDState.READY  # 重试
            self.collisions += 1
            return 0, len(transmitting), 0
        else:
            # 空闲
            return 0, 0, 1
    
    def run(self, max_rounds: int = 100) -> dict:
        """运行识别"""
        identified = []
        
        for round in range(max_rounds):
            success, collision, idle = self.simulate_round()
            identified.extend([t for t in self.tags if t.state == RFIDState.SUCCESS])
            
            if len(identified) >= self.num_tags:
                break
        
        return {
            'total_rounds': self.total_slots,
            'identified': len(identified),
            'success': self.successful,
            'collisions': self.collisions,
            'efficiency': len(identified) / self.total_slots if self.total_slots > 0 else 0
        }


class SlottedALOHA:
    """
    时隙ALOHA防碰撞算法 (ISO 14443)
    
    将时间分为固定时隙，标签只能在时隙开始时发送
    效率提高到36%
    """
    
    def __init__(self, num_tags: int, frame_size: int = 16):
        self.num_tags = num_tags
        self.frame_size = frame_size
        self.tags = [RFIDTag(f"TAG-{i:04d}") for i in range(num_tags)]
        
        # 统计
        self.total_frames = 0
        self.successful = 0
        self.collisions = 0
        self.idle_slots = 0
    
    def simulate_frame(self) -> Tuple[int, int, int]:
        """
        模拟一帧
        
        Returns:
            (成功时隙数, 碰撞时隙数, 空闲时隙数)
        """
        self.total_frames += 1
        
        success = 0
        collision = 0
        idle = 0
        
        for slot in range(self.frame_size):
            # 选择当前帧内发送的标签
            ready_tags = [t for t in self.tags if t.state == RFIDState.READY]
            
            if len(ready_tags) == 0:
                idle += 1
                continue
            
            # 简化：假设每个就绪标签以固定概率选择此帧
            transmitting = ready_tags[:min(1, len(ready_tags))]
            
            if len(transmitting) == 1:
                transmitting[0].state = RFIDState.SUCCESS
                success += 1
                self.successful += 1
            elif len(transmitting) > 1:
                collision += 1
                self.collisions += 1
        
        return success, collision, idle
    
    def run(self, max_frames: int = 50) -> dict:
        """运行识别"""
        identified = []
        
        for frame in range(max_frames):
            success, collision, idle = self.simulate_frame()
            identified.extend([t for t in self.tags if t.state == RFIDState.SUCCESS])
            
            if all(t.state == RFIDState.SUCCESS for t in self.tags):
                break
        
        total_slots = self.total_frames * self.frame_size
        
        return {
            'total_frames': self.total_frames,
            'total_slots': total_slots,
            'identified': len(identified),
            'success': self.successful,
            'collisions': self.collisions,
            'idle': self.idle_slots,
            'efficiency': len(identified) / total_slots if total_slots > 0 else 0
        }


class DynamicSlottedALOHA:
    """
    动态时隙ALOHA
    
    根据上一帧的碰撞/空闲情况动态调整帧大小
    效率可达43%
    """
    
    def __init__(self, num_tags: int):
        self.num_tags = num_tags
        self.tags = [RFIDTag(f"TAG-{i:04d}") for i in range(num_tags)]
        
        # 帧大小
        self.frame_size = 8
        self.min_frame_size = 8
        self.max_frame_size = 256
        
        # 统计
        self.total_slots = 0
        self.successful = 0
        self.collisions = 0
    
    def _adjust_frame_size(self, c: int, i: int):
        """
        调整帧大小
        
        Args:
            c: 碰撞时隙数
            i: 空闲时隙数
        """
        # 简单策略：碰撞多则增大帧，空闲多则减小帧
        if c > i:
            self.frame_size = min(self.frame_size * 2, self.max_frame_size)
        elif i > c * 2:
            self.frame_size = max(self.frame_size // 2, self.min_frame_size)
    
    def run_step(self) -> Tuple[int, int, int]:
        """执行一步"""
        ready_tags = [t for t in self.tags if t.state == RFIDState.READY]
        if not ready_tags:
            return 0, 0, 0
        
        # 选择此帧的标签
        selected = ready_tags[:min(self.frame_size, len(ready_tags))]
        
        success = 0
        collision = 0
        idle = self.frame_size - len(selected)
        
        for t in selected:
            if len(selected) == 1:
                t.state = RFIDState.SUCCESS
                success += 1
                self.successful += 1
            else:
                collision += 1
        
        self.total_slots += self.frame_size
        
        # 调整下一帧大小
        self._adjust_frame_size(collision, idle)
        
        return success, collision, idle
    
    def run(self, max_iterations: int = 100) -> dict:
        """运行识别"""
        identified = []
        
        for i in range(max_iterations):
            success, collision, idle = self.run_step()
            identified = [t for t in self.tags if t.state == RFIDState.SUCCESS]
            
            ready = len([t for t in self.tags if t.state == RFIDState.READY])
            
            if i % 10 == 0:
                print(f"  迭代{i}: 识别{len(identified)}, 待识别{ready}, 帧大小={self.frame_size}")
            
            if ready == 0:
                break
        
        return {
            'total_slots': self.total_slots,
            'identified': len(identified),
            'success': self.successful,
            'collisions': self.collisions,
            'efficiency': len(identified) / self.total_slots if self.total_slots > 0 else 0
        }


class BinaryTreeProtocol:
    """
    二叉树防碰撞算法 (ISO 18000-3)
    
    碰撞后分成两组，分别查询
    优点：确定性，100%识别率
    缺点：延迟较长
    """
    
    def __init__(self, num_tags: int):
        self.num_tags = num_tags
        self.tags = [RFIDTag(f"TAG-{i:04d}") for i in range(num_tags)]
        
        # 查询堆栈
        self.query_stack = []
        
        # 统计
        self.total_queries = 0
        self.slots = 0
    
    def _bits_to_tags(self, tags: List[RFIDTag], prefix: str) -> List[RFIDTag]:
        """根据前缀筛选标签"""
        return [t for t in tags if t.tag_id.startswith(prefix)]
    
    def run(self) -> dict:
        """运行查询"""
        identified = []
        self.query_stack = [('', 0, len(self.tags))]  # (前缀, bit位置, 估计数量)
        
        while self.query_stack:
            prefix, bit_pos, est_count = self.query_stack.pop()
            
            if est_count == 0:
                continue
            
            self.total_queries += 1
            
            # 查询
            matching = self._bits_to_tags(
                [t for t in self.tags if t.state == RFIDState.READY],
                prefix
            )
            
            if len(matching) == 0:
                # 无标签
                continue
            elif len(matching) == 1:
                # 成功识别
                matching[0].state = RFIDState.SUCCESS
                identified.append(matching[0])
            else:
                # 碰撞，分支
                self.query_stack.append((prefix + '0', bit_pos + 1, est_count // 2))
                self.query_stack.append((prefix + '1', bit_pos + 1, est_count // 2))
        
        return {
            'total_queries': self.total_queries,
            'identified': len(identified),
            'efficiency': len(identified) / self.total_queries if self.total_queries > 0 else 0
        }


class QueryTreeProtocol:
    """
    查询树防碰撞算法
    
    简化版二叉树，阅读器发送前缀，标签响应匹配前缀的下一个比特
    """
    
    def __init__(self, num_tags: int):
        self.num_tags = num_tags
        self.tags = [RFIDTag(f"TAG-{i:04d}") for i in range(num_tags)]
        
        self.queries = []  # 待处理查询
        self.total_slots = 0
    
    def _match_prefix(self, tag_id: str, prefix: str) -> Optional[str]:
        """检查标签是否匹配前缀，返回下一个比特"""
        if tag_id.startswith(prefix):
            return tag_id[len(prefix)]
        return None
    
    def run(self) -> dict:
        """运行查询"""
        identified = []
        self.queries = ['']  # 从空前缀开始
        
        while self.queries:
            prefix = self.queries.pop(0)
            self.total_slots += 1
            
            # 查找匹配的标签
            matching_tags = []
            for t in self.tags:
                if t.state == RFIDState.READY:
                    if t.tag_id.startswith(prefix):
                        matching_tags.append(t)
            
            if len(matching_tags) == 0:
                continue
            elif len(matching_tags) == 1:
                matching_tags[0].state = RFIDState.SUCCESS
                identified.append(matching_tags[0])
            else:
                # 碰撞，添加新的查询
                self.queries.append(prefix + '0')
                self.queries.append(prefix + '1')
        
        return {
            'total_slots': self.total_slots,
            'identified': len(identified),
            'efficiency': len(identified) / self.total_slots if self.total_slots > 0 else 0
        }


def compare_algorithms():
    """
    比较不同防碰撞算法
    """
    print("=== RFID防碰撞算法对比 ===\n")
    
    num_tags = 100
    
    print(f"标签数量: {num_tags}")
    print()
    
    # Pure ALOHA
    print("1. 纯ALOHA:")
    aloha = PureALOHA(num_tags)
    result = aloha.run(max_rounds=1000)
    print(f"   总时隙: {result['total_rounds']}")
    print(f"   识别: {result['identified']}")
    print(f"   效率: {result['efficiency']:.2%}")
    
    # Slotted ALOHA
    print("\n2. 时隙ALOHA:")
    slotted = SlottedALOHA(num_tags, frame_size=64)
    result = slotted.run(max_frames=100)
    print(f"   总时隙: {result['total_slots']}")
    print(f"   识别: {result['identified']}")
    print(f"   效率: {result['efficiency']:.2%}")
    
    # Dynamic Slotted ALOHA
    print("\n3. 动态时隙ALOHA:")
    dynamic = DynamicSlottedALOHA(num_tags)
    result = dynamic.run(max_iterations=50)
    print(f"   总时隙: {result['total_slots']}")
    print(f"   识别: {result['identified']}")
    print(f"   效率: {result['efficiency']:.2%}")
    
    # Binary Tree
    print("\n4. 二叉树:")
    bt = BinaryTreeProtocol(num_tags)
    result = bt.run()
    print(f"   总查询: {result['total_queries']}")
    print(f"   识别: {result['identified']}")
    print(f"   效率: {result['efficiency']:.2%}")
    
    # Query Tree
    print("\n5. 查询树:")
    qt = QueryTreeProtocol(num_tags)
    result = qt.run()
    print(f"   总时隙: {result['total_slots']}")
    print(f"   识别: {result['identified']}")
    print(f"   效率: {result['efficiency']:.2%}")


def demo_theoretical_efficiency():
    """
    演示理论效率
    """
    print("\n=== 理论效率分析 ===\n")
    
    print("ALOHA类算法理论最大效率:")
    print()
    print("| 算法              | 最大效率 | 理论原因 |")
    print("|-------------------|---------|----------|")
    print("| Pure ALOHA        | 18.4%   | 碰撞窗口2T |")
    print("| Slotted ALOHA     | 36.8%   | 碰撞窗口T |")
    print("| 帧时隙ALOHA       | 36.8%   | 最优帧大小 |")
    print("| 动态帧时隙ALOHA   | 43.0%   | 自适应调整 |")
    print()
    
    print("树协议效率:")
    print("| 算法              | 效率范围 | 特点 |")
    print("|-------------------|---------|------|")
    print("| 二叉树            | 30-50%  | 确定 |")
    print("| 查询树            | 30-50%  | 简单 |")
    print("| 混合算法          | 40-60%  | 结合 |")


def demo_iso_standards():
    """
    演示ISO标准
    """
    print("\n=== ISO RFID标准 ===\n")
    
    print("| 标准            | 频率    | 防碰撞算法 |")
    print("|----------------|---------|-----------|")
    print("| ISO 14443      | 13.56MHz| 时隙ALOHA |")
    print("| ISO 15693      | 13.56MHz| 查询树    |")
    print("| ISO 18000-3    | 13.56MHz| 二叉树    |")
    print("| ISO 18000-6    | UHF     | 动态ALOHA |")
    print("| EPC Gen2       | UHF     | 随机槽    |")


if __name__ == "__main__":
    print("=" * 60)
    print("RFID防碰撞算法实现")
    print("=" * 60)
    
    # 算法对比
    compare_algorithms()
    
    # 理论效率
    demo_theoretical_efficiency()
    
    # ISO标准
    demo_iso_standards()
    
    print("\n" + "=" * 60)
    print("算法选择指南:")
    print("=" * 60)
    print("""
场景            | 推荐算法
---------------|----------
标签数量少     | 纯ALOHA
标签数量多     | 动态时隙ALOHA
需要确定性延迟 | 二叉树
硬件简单       | 查询树
EPC标签        | 随机槽(EPC Gen2)

关键优化:
1. 帧大小自适应调整
2. 标签分组处理
3. 碰撞位追踪
4. 混合使用ALOHA和树协议
""")

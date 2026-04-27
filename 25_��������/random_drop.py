# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / random_drop

本文件实现 random_drop 相关的算法功能。
"""

import random
import math
from collections import deque
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Packet:
    """数据包"""
    id: int
    size: int = 1  # 简化：单位大小
    timestamp: float = 0.0


class QueueBase:
    """队列基类"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.queue = deque(maxlen=capacity)
        self.packets_dropped = 0
        self.packets_served = 0
    
    def enqueue(self, packet: Packet) -> bool:
        """入队"""
        raise NotImplementedError
    
    def dequeue(self) -> Optional[Packet]:
        """出队"""
        raise NotImplementedError
    
    def size(self) -> int:
        return len(self.queue)
    
    def utilization(self) -> float:
        return len(self.queue) / self.capacity


class TailDropQueue(QueueBase):
    """
    Tail Drop队列
    
    当队列满时丢弃新到达的包
    最简单的丢包策略
    """
    
    def enqueue(self, packet: Packet) -> bool:
        """入队（满则丢弃）"""
        if len(self.queue) >= self.capacity:
            self.packets_dropped += 1
            return False
        
        self.queue.append(packet)
        return True
    
    def dequeue(self) -> Optional[Packet]:
        """出队"""
        if not self.queue:
            return None
        
        packet = self.queue.popleft()
        self.packets_served += 1
        return packet


class RandomDropQueue(QueueBase):
    """
    Random Drop队列
    
    当队列满时，随机选择一个包丢弃
    比Tail更公平
    """
    
    def enqueue(self, packet: Packet) -> bool:
        """入队"""
        if len(self.queue) >= self.capacity:
            # 随机丢弃一个
            drop_idx = random.randint(0, len(self.queue) - 1)
            self.queue.pop(drop_idx)
            self.packets_dropped += 1
        
        self.queue.append(packet)
        return True


class REDQueue(QueueBase):
    """
    Random Early Detection (RED) 队列
    
    在队列满之前就开始随机丢包
    目的：提前通知发送方拥塞，避免全局同步
    """
    
    def __init__(self, capacity: int, 
                 min_threshold: float = 0.1,
                 max_threshold: float = 0.5,
                 max_drop_prob: float = 0.1):
        super().__init__(capacity)
        
        self.min_threshold = min_threshold  # 开始丢包的队列长度比例
        self.max_threshold = max_threshold  # 达到最大丢包率的队列长度比例
        self.max_drop_prob = max_drop_prob  # 最大丢包概率
        
        # 指数加权移动平均
        self.avg_queue_size = 0.0
        self.ema_weight = 0.3  # EWMA权重
        
        # 计算阈值
        self.min_q = int(capacity * min_threshold)
        self.max_q = int(capacity * max_threshold)
    
    def _calculate_drop_prob(self) -> float:
        """
        计算丢包概率
        
        线性插值：
        - avg < min_q: 丢包概率 = 0
        - avg > max_q: 丢包概率 = max_p
        - min_q <= avg <= max_q: 线性插值
        """
        avg = self.avg_queue_size
        
        if avg <= self.min_q:
            return 0.0
        elif avg >= self.max_q:
            return self.max_drop_prob
        else:
            # 线性插值
            ratio = (avg - self.min_q) / (self.max_q - self.min_q)
            return self.max_drop_prob * ratio
    
    def enqueue(self, packet: Packet) -> bool:
        """入队（带RED丢包）"""
        # 更新平均队列长度
        self.avg_queue_size = (self.avg_queue_size * (1 - self.ema_weight) + 
                              len(self.queue) * self.ema_weight)
        
        # 计算丢包概率
        drop_prob = self._calculate_drop_prob()
        
        # 随机丢包
        if random.random() < drop_prob:
            self.packets_dropped += 1
            return False
        
        # 如果队列满了，也丢包
        if len(self.queue) >= self.capacity:
            # RED此时应该已经以较高概率丢包
            self.packets_dropped += 1
            return False
        
        self.queue.append(packet)
        return True
    
    def dequeue(self) -> Optional[Packet]:
        """出队"""
        if not self.queue:
            return None
        
        packet = self.queue.popleft()
        self.packets_served += 1
        return packet
    
    def get_stats(self) -> dict:
        """获取统计"""
        return {
            'avg_queue': self.avg_queue_size,
            'current_queue': len(self.queue),
            'drop_prob': self._calculate_drop_prob(),
            'dropped': self.packets_dropped,
            'served': self.packets_served
        }


class ECNQueue(QueueBase):
    """
    ECN (Explicit Congestion Notification) 队列
    
    不丢包，而是标记ECN位通知拥塞
    需要网络设备支持
    """
    
    def __init__(self, capacity: int, threshold: float = 0.5):
        super().__init__(capacity)
        self.threshold = threshold  # 标记阈值
        self.marked_packets = 0
    
    def enqueue(self, packet: Packet) -> Tuple[bool, bool]:
        """
        入队
        
        Returns:
            (enqueued, marked) - 是否入队，是否ECN标记
        """
        if len(self.queue) >= self.capacity:
            # 队列满，丢包
            self.packets_dropped += 1
            return False, False
        
        marked = False
        
        # 检查是否需要ECN标记
        if len(self.queue) / self.capacity > self.threshold:
            marked = True
            self.marked_packets += 1
        
        self.queue.append(packet)
        return True, marked
    
    def dequeue(self) -> Optional[Packet]:
        """出队"""
        if not self.queue:
            return None
        
        self.packets_served += 1
        return self.queue.popleft()


def simulate_queue():
    """模拟队列"""
    print("=== 队列丢包策略模拟 ===\n")
    
    capacity = 100
    n_packets = 500
    
    strategies = {
        'Tail Drop': TailDropQueue(capacity),
        'Random Drop': RandomDropQueue(capacity),
        'RED': REDQueue(capacity, min_threshold=0.1, max_threshold=0.5, max_drop_prob=0.15),
    }
    
    print(f"队列容量: {capacity}, 总包数: {n_packets}")
    print()
    
    for name, queue in strategies.items():
        # 重置
        queue.queue.clear()
        queue.packets_dropped = 0
        queue.packets_served = 0
        
        # 模拟到达（泊松到达）
        for i in range(n_packets):
            # 模拟到达间隔
            if random.random() < 0.5:  # 50%概率到达
                packet = Packet(id=i, timestamp=i * 0.01)
                queue.enqueue(packet)
            
            # 模拟服务
            if random.random() < 0.3:  # 30%概率服务
                queue.dequeue()
        
        print(f"{name}:")
        print(f"  丢弃: {queue.packets_dropped}")
        print(f"  服务: {queue.packets_served}")
        print(f"  剩余: {queue.size()}")
        
        if hasattr(queue, 'get_stats'):
            stats = queue.get_stats()
            print(f"  平均队列: {stats['avg_queue']:.1f}")
            print(f"  当前丢包率: {queue.packets_dropped/n_packets*100:.1f}%")


def demo_red_probability():
    """演示RED丢包概率"""
    print("\n=== RED丢包概率分析 ===\n")
    
    red = REDQueue(capacity=100, min_threshold=0.1, max_threshold=0.5, max_drop_prob=0.2)
    
    print("RED配置:")
    print(f"  min_threshold: {red.min_threshold * 100:.0f}%")
    print(f"  max_threshold: {red.max_threshold * 100:.0f}%")
    print(f"  max_drop_prob: {red.max_drop_prob * 100:.0f}%")
    print()
    
    print("丢包概率 vs 队列利用率:")
    print("| 利用率 | 丢包概率 |")
    
    for util in range(0, 110, 10):
        red.avg_queue_size = util
        prob = red._calculate_drop_prob()
        bar = '█' * int(prob * 50)
        print(f"| {util:6.0f}% | {prob*100:6.1f}% {bar:15s}|")


def demo_ecn_vs_red():
    """对比ECN和RED"""
    print("\n=== ECN vs RED 对比 ===\n")
    
    capacity = 100
    
    ecn = ECNQueue(capacity, threshold=0.5)
    red = REDQueue(capacity, min_threshold=0.3, max_threshold=0.7, max_drop_prob=0.1)
    
    print("模拟拥塞:")
    
    for i in range(200):
        # 高负载
        for _ in range(3):
            p1, m1 = ecn.enqueue(Packet(i))
            red.enqueue(Packet(i))
        
        # 服务
        ecn.dequeue()
        red.dequeue()
    
    print(f"RED: 丢弃={red.packets_dropped}, 服务={red.packets_served}")
    print(f"ECN: 丢弃={ecn.packets_dropped}, 标记={ecn.marked_packets}, 服务={ecn.packets_served}")
    
    print("\n结论:")
    print("  - RED通过丢包通知拥塞")
    print("  - ECN通过标记代替丢包")
    print("  - ECN更高效，但需要端到端支持")


def demo_queueing_discipline():
    """演示队列调度"""
    print("\n=== 队列调度算法 ===\n")
    
    print("常见队列调度算法:")
    print()
    
    print("1. FIFO (First In First Out):")
    print("   - 最简单，先来先服务")
    print("   - 可能导致长流饥饿短流")
    
    print("\n2. Priority Queue:")
    print("   - 高优先级先服务")
    print("   - 可能饿死低优先级")
    
    print("\n3. Fair Queueing (FQ):")
    print("   - 每个流一个队列")
    print("   - 轮询服务，保证公平")
    
    print("\n4. Deficit Round Robin (DRR):")
    print("   - FQ的改进，量化服务")
    print("   - 更精确的公平性")
    
    print("\n5. Weighted Fair Queueing (WFQ):")
    print("   - 按权重分配带宽")
    print("   - 适合区分服务")


def demo_global_synchronization():
    """演示全局同步问题"""
    print("\n=== 全局同步问题 ===\n")
    
    print("问题描述:")
    print("  - 多个TCP连接共享瓶颈链路")
    print("  - 同时丢包导致同时减窗")
    print("  - 然后同时增长，导致再次同时丢包")
    print("  - 形成同步震荡")
    
    print("\n解决方案:")
    print("  - RED: 随机丢包，打破同步")
    print("  - ECN: 提前标记，避免丢包")
    print("  - Randomized dropping: 随机化丢包时机")


if __name__ == "__main__":
    print("=" * 60)
    print("随机丢包策略 (Random/Tail/RED)")
    print("=" * 60)
    
    # 队列模拟
    simulate_queue()
    
    # RED概率分析
    demo_red_probability()
    
    # ECN vs RED
    demo_ecn_vs_red()
    
    # 队列调度
    demo_queueing_discipline()
    
    # 全局同步
    demo_global_synchronization()
    
    print("\n" + "=" * 60)
    print("应用场景:")
    print("=" * 60)
    print("""
| 策略     | 适用场景                |
|----------|------------------------|
| Tail Drop| 简单场景，不关心拥塞控制 |
| Random   | 需要一定公平性          |
| RED      | 路由器，TCP拥塞控制     |
| ECN      | 现代网络，DC, LTE       |

RED参数调整建议:
- min_threshold: 平时队列长度
- max_threshold: 触发拥塞的队列长度
- max_p: 最大丢包率，通常10-20%
""")

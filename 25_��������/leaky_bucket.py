# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / leaky_bucket

本文件实现 leaky_bucket 相关的算法功能。
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Any


class LeakyBucket:
    """
    漏桶算法实现
    
    核心原理：
    1. 水滴以固定速率从桶底漏出
    2. 输入的水滴进入桶顶
    3. 如果桶满了，新水滴溢出（丢弃）
    4. 输出始终是固定速率
    """
    
    def __init__(self, leak_rate: float, capacity: int):
        """
        初始化漏桶
        
        Args:
            leak_rate: 漏出速率（滴/秒）
            capacity: 桶容量（最大滴数）
        """
        self.leak_rate = leak_rate  # 滴/秒
        self.capacity = capacity  # 桶容量
        self.bucket_level = 0  # 当前水位
        self.last_leak_time = time.time()
        
        # 统计
        self.total_input = 0
        self.total_output = 0
        self.total_dropped = 0
    
    def _leak(self):
        """漏出水滴"""
        now = time.time()
        elapsed = now - self.last_leak_time
        
        # 计算漏出的水量
        leaked = elapsed * self.leak_rate
        self.bucket_level = max(0, self.bucket_level - leaked)
        self.last_leak_time = now
        
        # 统计输出
        if leaked > 0:
            self.total_output += leaked
    
    def add(self, drops: int = 1, block: bool = False) -> bool:
        """
        加入水滴
        
        Args:
            drops: 加入的滴数
            block: 是否阻塞等待桶空
        
        Returns:
            是否成功加入
        """
        if block:
            while True:
                self._leak()
                if self.bucket_level + drops <= self.capacity:
                    self.bucket_level += drops
                    self.total_input += drops
                    return True
                time.sleep(0.001)
        else:
            self._leak()
            
            if self.bucket_level + drops <= self.capacity:
                self.bucket_level += drops
                self.total_input += drops
                return True
            else:
                self.total_dropped += drops
                return False
    
    def get_output_time(self) -> float:
        """
        获取下一个输出剩余时间
        
        Returns:
            秒数（0表示立即可输出）
        """
        if self.bucket_level > 0:
            return self.bucket_level / self.leak_rate
        return 0.0
    
    def drain(self) -> int:
        """
        漏出所有当前水
        
        Returns:
            漏出的滴数
        """
        self._leak()
        leaked = int(self.bucket_level)
        self.bucket_level = 0
        return leaked
    
    def get_status(self) -> dict:
        """获取状态"""
        self._leak()
        return {
            'level': self.bucket_level,
            'capacity': self.capacity,
            'leak_rate': self.leak_rate,
            'utilization': self.bucket_level / self.capacity if self.capacity > 0 else 0
        }


class PacketQueue:
    """
    基于漏桶的分组队列
    """
    
    def __init__(self, output_rate: float, queue_size: int):
        """
        初始化
        
        Args:
            output_rate: 输出速率（包/秒）
            queue_size: 队列大小
        """
        self.leaky_bucket = LeakyBucket(output_rate, queue_size)
        self.queue = deque()
        self.last_process_time = time.time()
    
    def enqueue(self, packet: Any) -> bool:
        """
        入队
        
        Args:
            packet: 数据包
        
        Returns:
            是否入队成功
        """
        if self.leaky_bucket.add(1, block=False):
            self.queue.append(packet)
            return True
        return False
    
    def dequeue(self) -> Optional[Any]:
        """
        出队（按照漏桶速率）
        
        Returns:
            数据包或None
        """
        if self.queue:
            # 按漏桶速率检查
            if self.leaky_bucket.bucket_level >= 1:
                self.leaky_bucket._leak()
                if self.leaky_bucket.bucket_level >= 1:
                    self.leaky_bucket.bucket_level -= 1
                    return self.queue.popleft()
        
        return None
    
    def process_all(self) -> List[Any]:
        """处理所有队列中的包"""
        processed = []
        while True:
            pkt = self.dequeue()
            if pkt is None:
                break
            processed.append(pkt)
        return processed


class TokenBucketAsLeakyBucket:
    """
    用令牌桶模拟漏桶
    
    令牌桶补充速率=漏桶漏水速率
    令牌桶容量=漏桶容量
    """
    
    def __init__(self, leak_rate: float, capacity: int):
        # 令牌桶以leak_rate速率生成令牌
        # 每次操作消耗1个令牌
        self.rate = leak_rate
        self.capacity = capacity
        self.tokens = capacity  # 初始满桶
        self.last_update = time.time()
        
        self.total_processed = 0
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
    
    def process(self, block: bool = False) -> bool:
        """
        处理一个单位
        
        Returns:
            是否成功处理
        """
        self._refill()
        
        if self.tokens >= 1:
            self.tokens -= 1
            self.total_processed += 1
            return True
        
        if block:
            # 等待
            wait_time = (1 - self.tokens) / self.rate
            time.sleep(wait_time)
            self.tokens = 1
            self.total_processed += 1
            return True
        
        return False
    
    def add(self, item: Any, block: bool = False) -> bool:
        """
        添加并立即处理
        
        Returns:
            是否成功
        """
        return self.process(block)


class HierarchicalLeakyBucket:
    """
    分层漏桶（HTB-like，带宽分配）
    """
    
    def __init__(self, total_rate: float, classes: List[tuple]):
        """
        初始化分层漏桶
        
        Args:
            total_rate: 总速率
            classes: [(rate, capacity, children), ...]
        """
        self.total_rate = total_rate
        self.classes = {}  # class_id -> LeakyBucket
        self.parent = None
        
        # 创建根桶
        self.root = LeakyBucket(total_rate, total_rate * 10)
        
        for class_id, (rate, capacity) in enumerate(classes):
            self.classes[class_id] = LeakyBucket(rate, capacity)
            self.classes[class_id].parent = self.root


def simulate_leaky_bucket():
    """
    模拟漏桶
    """
    print("=== 漏桶算法模拟 ===\n")
    
    # 创建漏桶: 10滴/秒, 容量20
    bucket = LeakyBucket(leak_rate=10, capacity=20)
    
    print(f"漏桶配置: leak_rate=10/s, capacity=20")
    print()
    
    # 模拟突发输入
    print("突发输入 (30个请求):")
    
    for i in range(30):
        success = bucket.add(1, block=False)
        status = "加入" if success else "溢出"
        print(f"  请求{i:2d}: {status} (level={bucket.bucket_level:.1f})")
    
    print(f"\n统计:")
    print(f"  输入: {bucket.total_input}")
    print(f"  溢出: {bucket.total_dropped}")
    print(f"  当前水位: {bucket.bucket_level:.1f}")
    
    # 等待漏完
    print("\n等待漏桶漏空...")
    time.sleep(3)
    
    bucket._leak()
    print(f"漏空后水位: {bucket.bucket_level:.1f}")


def demo_traffic_shaping():
    """
    演示流量整形
    """
    print("\n=== 流量整形演示 ===\n")
    
    # 创建队列: 100包/秒, 队列100
    queue = PacketQueue(output_rate=100, queue_size=100)
    
    print("队列配置: 100 pkt/s, 队列深度=100")
    print()
    
    # 模拟突发
    print("模拟1秒内突发1000个包:")
    start = time.time()
    
    accepted = 0
    dropped = 0
    for i in range(1000):
        if queue.enqueue(f"pkt-{i}"):
            accepted += 1
        else:
            dropped += 1
    
    print(f"  入队: {accepted}")
    print(f"  丢弃: {dropped}")
    
    # 处理
    print(f"\n处理队列...")
    processed = 0
    while queue.queue:
        pkt = queue.dequeue()
        if pkt:
            processed += 1
        time.sleep(0.01)
    
    elapsed = time.time() - start
    print(f"  处理完成: {processed} packets in {elapsed:.2f}s")
    print(f"  实际速率: {processed/elapsed:.1f} pkt/s")


def demo_fixed_rate_output():
    """
    演示固定速率输出
    """
    print("\n=== 固定速率输出演示 ===\n")
    
    # 模拟视频编码: 30fps, 恒定码率
    fps = 30
    bucket = LeakyBucket(leak_rate=fps, capacity=fps * 2)  # 2帧缓冲
    
    print(f"视频帧队列: {fps} fps, 容量={fps*2}")
    print()
    
    # 模拟编码器输出
    frames = []
    for i in range(90):  # 3秒
        # 模拟编码器输出（可变）
        if random.random() < 0.3:
            frames.append(f"frame-{i}")  # 丢帧模拟
    
    print(f"编码器输出: {len(frames)} frames (模拟丢帧)")
    
    # 入队
    for f in frames:
        bucket.add(1, block=False)
    
    # 按固定速率输出
    print("\n固定速率播放:")
    
    last_time = time.time()
    output_count = 0
    bucket.drain()  # 清空
    
    # 重新填充
    for f in frames:
        bucket.add(1)
    
    # 播放
    for i in range(len(frames)):
        time.sleep(1/fps)
        pkt = bucket.add(0)  # 只检查
        bucket._leak()
        output_count += 1
        if output_count % 30 == 0:
            print(f"  第{output_count//30}秒完成")


def demo_vs_token_bucket():
    """
    对比漏桶与令牌桶
    """
    print("\n=== 漏桶 vs 令牌桶 对比 ===\n")
    
    # 漏桶
    leaky = LeakyBucket(leak_rate=10, capacity=20)
    
    # 令牌桶
    from token_bucket import TokenBucket
    token = TokenBucket(rate=10, capacity=20)
    
    print("配置相同: rate=10/s, capacity=20")
    print()
    
    # 突发测试
    print("突发测试 (30个请求同时到达):")
    
    leaky_success = 0
    token_success = 0
    
    for _ in range(30):
        if leaky.add(1, block=False):
            leaky_success += 1
        if token.allow(1):
            token_success += 1
    
    print(f"  漏桶通过: {leaky_success} (固定容量)" )
    print(f"  令牌桶通过: {token_success} (允许突发)")
    
    print("\n关键差异:")
    print("  漏桶: 突发进入的请求会被丢弃")
    print("  令牌桶: 突发进入的请求会暂存，等待后续令牌")
    
    print("\n时间序列对比:")
    print()
    print("时间 | 漏桶(累计) | 令牌桶(累计)")
    print("-----|-----------|------------")
    
    # 重置
    leaky = LeakyBucket(leak_rate=10, capacity=20)
    token = TokenBucket(rate=10, capacity=20)
    
    for t in range(5):
        # t=0时突发30
        if t == 0:
            for _ in range(30):
                leaky.add(1)
                token.allow(1)
        else:
            time.sleep(0.5)
            leaky._leak()
        
        leaky_out = leaky.total_output
        token_out = token.total_requests_allowed
        
        print(f"  {t}s | {int(leaky_out):10d} | {token_out:10d}")


if __name__ == "__main__":
    import random
    
    print("=" * 60)
    print("漏桶算法实现")
    print("=" * 60)
    
    # 基本模拟
    simulate_leaky_bucket()
    
    # 流量整形
    demo_traffic_shaping()
    
    # 固定速率
    demo_fixed_rate_output()
    
    # 对比
    demo_vs_token_bucket()
    
    print("\n" + "=" * 60)
    print("漏桶 vs 令牌桶:")
    print("=" * 60)
    print("""
| 场景          | 漏桶      | 令牌桶      |
|--------------|-----------|-------------|
| 流量整形      | 固定速率   | 可变速率    |
| 突发容忍      | 不允许    | 允许        |
| 网络整形      | 一般      | 推荐        |
| API限流       | 一般      | 推荐        |
| 公平队列      | 简单      | 复杂但公平  |

漏桶适用场景:
- CBR(恒定码率)视频编码
- 固定速率输出
- 硬实时系统

令牌桶适用场景:
- 网络QoS
- API速率限制
- 弹性带宽
""")

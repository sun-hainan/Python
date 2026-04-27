# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / leaky_bucket

本文件实现 leaky_bucket 相关的算法功能。
"""

import time
import threading
from collections import deque


class LeakyBucket:
    """漏桶算法实现"""

    def __init__(self, capacity, leak_rate):
        """
        初始化漏桶
        
        参数:
            capacity: 桶的容量（最大排队数据包数）
            leak_rate: 漏水速率（数据包/秒）
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        # 桶内当前排队的包
        self.bucket = deque()
        # 上次漏水时间
        self.last_leak = time.time()
        # 锁
        self._lock = threading.Lock()

    def _leak(self):
        """漏水操作：移除过期的数据包"""
        now = time.time()
        elapsed = now - self.last_leak
        
        # 计算应该漏出的包数
        num_to_leak = int(elapsed * self.leak_rate)
        
        # 移除已漏出的包
        for _ in range(min(num_to_leak, len(self.bucket))):
            self.bucket.popleft()
        
        self.last_leak = now

    def add(self, packet=None):
        """
        添加数据包到桶中
        
        参数:
            packet: 要添加的数据包（可以是任意对象）
        返回:
            success: 是否成功添加
        """
        with self._lock:
            self._leak()
            
            if len(self.bucket) < self.capacity:
                self.bucket.append(packet)
                return True
            return False

    def get_next_packet_time(self):
        """
        获取下一个数据包可被发送的时间
        
        返回:
            time: 下个数据包的发送时间，如果桶空返回 None
        """
        with self._lock:
            if not self.bucket:
                return None
            return self.last_leak + (1.0 / self.leak_rate) * len(self.bucket)

    def size(self):
        """获取桶内数据包数"""
        with self._lock:
            self._leak()
            return len(self.bucket)


class LeakyBucketRateShaper:
    """基于漏桶的速率整形器"""

    def __init__(self, output_rate, buffer_size=1000):
        """
        初始化速率整形器
        
        参数:
            output_rate: 输出速率（字节/秒）
            buffer_size: 缓冲区大小（字节）
        """
        self.output_rate = output_rate
        self.buffer_size = buffer_size
        self.buffer = bytearray()
        self.last_send_time = time.time()
        self._lock = threading.Lock()

    def add_data(self, data):
        """
        添加数据到缓冲区
        
        参数:
            data: 要发送的数据字节
        返回:
            success: 是否成功添加
        """
        with self._lock:
            if len(self.buffer) + len(data) <= self.buffer_size:
                self.buffer.extend(data)
                return True
            return False

    def _send_from_buffer(self):
        """从缓冲区发送数据"""
        now = time.time()
        elapsed = now - self.last_send_time
        
        # 计算可以发送的字节数
        bytes_to_send = int(elapsed * self.output_rate)
        
        if bytes_to_send > 0 and len(self.buffer) > 0:
            sent = min(bytes_to_send, len(self.buffer))
            self.buffer = self.buffer[sent:]
            self.last_send_time = now
            return sent
        return 0

    def get_available_data(self, max_bytes=None):
        """
        获取可发送的数据（实时发送）
        
        参数:
            max_bytes: 最大获取字节数
        返回:
            data: 可发送的数据
        """
        with self._lock:
            self._send_from_buffer()
            
            if not self.buffer:
                return b''
            
            if max_bytes is None:
                data = bytes(self.buffer)
                self.buffer = bytearray()
            else:
                data = bytes(self.buffer[:max_bytes])
                self.buffer = self.buffer[max_bytes:]
            
            return data

    def get_buffer_fill_level(self):
        """获取缓冲区填充程度"""
        with self._lock:
            return len(self.buffer) / self.buffer_size


class PollingLeakyBucket:
    """轮询式漏桶（用于模拟网络接口）"""

    def __init__(self, interface_rate=1000000000, mtu=1500):
        """
        初始化轮询式漏桶
        
        参数:
            interface_rate: 接口速率（字节/秒）
            mtu: 最大传输单元
        """
        self.interface_rate = interface_rate
        self.mtu = mtu
        self.packets = deque()
        self.last_poll = time.time()

    def enqueue(self, packet):
        """
        入队数据包
        
        参数:
            packet: 数据包（字节）
        返回:
            success: 是否成功入队
        """
        # 计算包长（简化为 MTU）
        packet_size = len(packet) if packet else self.mtu
        
        # 估计队列占用的时间
        queue_time = packet_size / self.interface_rate
        
        # 简化的入队检查（不实现真正的队列管理）
        self.packets.append(packet)
        return True

    def dequeue(self):
        """
        出队数据包
        
        返回:
            packet: 数据包，如果没有则返回 None
        """
        now = time.time()
        elapsed = now - self.last_poll
        
        # 计算可发送的包数
        bytes_allowed = elapsed * self.interface_rate
        
        if bytes_allowed >= self.mtu and self.packets:
            self.last_poll = now
            return self.packets.popleft()
        
        return None

    def queue_length(self):
        """获取队列长度（包数）"""
        return len(self.packets)


class TokenBucketEquivalent:
    """
    令牌桶等价的漏桶实现
    
    说明：漏桶和令牌桶在数学上是等价的，可以相互模拟
    """

    def __init__(self, rate, capacity):
        """
        初始化
        
        参数:
            rate: 速率（令牌/秒 = 漏出速率）
            capacity: 容量（令牌桶容量 = 漏桶队列上限）
        """
        self.rate = rate
        self.capacity = capacity
        # 令牌等价量
        self.tokens = capacity  # 从满开始
        self.last_update = time.time()

    def _update_tokens(self):
        """更新令牌（模拟漏桶的漏出）"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 漏桶每时间单位漏出，与令牌桶每时间单位补充等效
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    def add_packet(self, packet_cost=1):
        """
        添加数据包（消耗令牌等价于漏桶入队）
        
        参数:
            packet_cost: 数据包消耗的令牌数
        返回:
            success: 是否成功
        """
        self._update_tokens()
        
        if self.tokens >= packet_cost:
            self.tokens -= packet_cost
            return True
        return False

    def get_available_capacity(self):
        """获取可用容量（漏桶剩余空间）"""
        self._update_tokens()
        return self.capacity - self.tokens


class LeakyBucketSimulator:
    """漏桶模拟器"""

    def __init__(self, capacity, leak_rate):
        """
        初始化模拟器
        
        参数:
            capacity: 桶容量
            leak_rate: 漏出速率（包/秒）
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.queue = []
        self.last_leak = time.time()
        self.stats = {
            'total_arrivals': 0,
            'total_drops': 0,
            'total_sent': 0
        }

    def process_arrival(self, packet, current_time):
        """
        处理数据包到达
        
        参数:
            packet: 数据包
            current_time: 当前时间
        """
        self.stats['total_arrivals'] += 1
        
        # 先漏水
        self._leak(current_time)
        
        # 尝试入队
        if len(self.queue) < self.capacity:
            self.queue.append(packet)
        else:
            self.stats['total_drops'] += 1

    def _leak(self, current_time):
        """漏水"""
        elapsed = current_time - self.last_leak
        num_to_leak = int(elapsed * self.leak_rate)
        
        for _ in range(min(num_to_leak, len(self.queue))):
            self.queue.pop(0)
            self.stats['total_sent'] += 1
        
        self.last_leak = current_time

    def get_stats(self):
        """获取统计信息"""
        total = self.stats['total_arrivals']
        return {
            'arrivals': self.stats['total_arrivals'],
            'sent': self.stats['total_sent'],
            'drops': self.stats['total_drops'],
            'drop_rate': self.stats['total_drops'] / total if total > 0 else 0,
            'queue_length': len(self.queue)
        }


if __name__ == "__main__":
    # 测试漏桶算法
    print("=== 漏桶算法测试 ===\n")

    # 基本漏桶
    print("--- 基本漏桶 ---")
    bucket = LeakyBucket(capacity=5, leak_rate=2)  # 容量5，漏出率2包/秒
    
    print(f"初始队列长度: {bucket.size()}")
    
    # 模拟入队
    print("\n模拟入队（容量5）:")
    for i in range(8):
        success = bucket.add(f"packet_{i}")
        print(f"  添加 packet_{i}: {'成功' if success else '失败'}, 队列长度: {bucket.size()}")
        time.sleep(0.1)  # 间隔 100ms

    # 速率整形器
    print("\n--- 速率整形器 ---")
    shaper = LeakyBucketRateShaper(output_rate=1000, buffer_size=100)
    
    # 添加数据
    data_chunks = [b"Hello ", b"World!", b" This is a test."]
    for chunk in data_chunks:
        success = shaper.add_data(chunk)
        print(f"  添加 {len(chunk)} 字节: {'成功' if success else '失败'}")
    
    print(f"  缓冲区填充: {shaper.get_buffer_fill_level():.1%}")
    
    # 获取数据
    print("\n获取可发送数据:")
    time.sleep(0.1)
    data = shaper.get_available_data()
    print(f"  发送: {len(data)} 字节 - {data}")

    # 轮询式漏桶
    print("\n--- 轮询式漏桶 ---")
    polling_bucket = PollingLeakyBucket(interface_rate=10000000, mtu=1500)  # 10MB/s
    
    # 入队一些包
    for i in range(5):
        polling_bucket.enqueue(f"packet_{i}".encode())
    
    print(f"入队后队列长度: {polling_bucket.queue_length()}")
    
    # 模拟轮询
    print("模拟轮询（10次）:")
    for i in range(10):
        packet = polling_bucket.dequeue()
        print(f"  轮询 {i+1}: {'收到 ' + str(packet) if packet else '无数据'}")
        time.sleep(0.001)

    # 模拟器
    print("\n--- 漏桶模拟器 ---")
    import random
    
    simulator = LeakyBucketSimulator(capacity=10, leak_rate=5)
    
    # 模拟到达过程（泊松过程简化）
    current_time = 0
    for i in range(20):
        current_time += random.expovariate(10)  # 平均到达率 10包/秒
        simulator.process_arrival(f"packet_{i}", current_time)
    
    stats = simulator.get_stats()
    print(f"统计:")
    print(f"  总到达: {stats['arrivals']}")
    print(f"  发送: {stats['sent']}")
    print(f"  丢弃: {stats['drops']}")
    print(f"  丢包率: {stats['drop_rate']:.1%}")
    print(f"  当前队列: {stats['queue_length']}")

    # 令牌桶等价
    print("\n--- 令牌桶等价漏桶 ---")
    equiv = TokenBucketEquivalent(rate=10, capacity=5)
    
    print("测试数据包处理:")
    for i in range(8):
        success = equiv.add_packet()
        print(f"  packet_{i}: {'成功' if success else '拒绝'}, "
              f"可用容量: {equiv.get_available_capacity():.1f}")

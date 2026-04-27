# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / token_bucket

本文件实现 token_bucket 相关的算法功能。
"""

import time
import threading


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, capacity, refill_rate):
        """
        初始化令牌桶
        
        参数:
            capacity: 桶的容量（令牌数/字节数）
            refill_rate: 令牌补充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        # 当前令牌数
        self.tokens = float(capacity)
        # 最后补充时间
        self.last_refill = time.time()
        # 是否正在漏桶（溢出时）
        self.leaking = False
        # 锁（用于线程安全）
        self._lock = threading.Lock()

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # 计算应该补充的令牌数
        new_tokens = elapsed * self.refill_rate
        
        # 更新令牌数（不超过容量）
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens=1):
        """
        尝试消耗令牌
        
        参数:
            tokens: 要消耗的令牌数
        返回:
            success: 是否成功消耗
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def consume_bytes(self, num_bytes):
        """
        尝试消耗指定字节对应的令牌
        
        参数:
            num_bytes: 字节数
        返回:
            success: 是否成功
        """
        return self.consume(tokens=num_bytes)

    def get_tokens(self):
        """获取当前令牌数"""
        with self._lock:
            self._refill()
            return self.tokens

    def get_tokens_available(self):
        """获取可用令牌数（不触发补充）"""
        return self.tokens


class RateLimiter:
    """基于令牌桶的速率限制器"""

    def __init__(self, rate, burst_size):
        """
        初始化速率限制器
        
        参数:
            rate: 速率（请求/秒 或 字节/秒）
            burst_size: 突发大小（桶容量）
        """
        self.rate = rate
        self.burst_size = burst_size
        self.bucket = TokenBucket(capacity=burst_size, refill_rate=rate)
        # 统计数据
        self.allowed_requests = 0
        self.rejected_requests = 0
        self.total_wait_time = 0

    def allow_request(self, cost=1):
        """
        检查是否允许请求
        
        参数:
            cost: 请求消耗的令牌数
        返回:
            allowed: 是否允许
        """
        if self.bucket.consume(cost):
            self.allowed_requests += 1
            return True
        else:
            self.rejected_requests += 1
            return False

    def wait_for_token(self, cost=1, timeout=None):
        """
        等待直到获得令牌
        
        参数:
            cost: 需要消耗的令牌数
            timeout: 超时时间（秒）
        返回:
            success: 是否成功获得令牌
        """
        start_time = time.time()
        
        while True:
            if self.bucket.consume(cost):
                self.allowed_requests += 1
                return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.rejected_requests += 1
                    return False
            
            # 等待一小段时间后重试
            wait_time = 0.001  # 1ms
            time.sleep(wait_time)
            self.total_wait_time += wait_time

    def get_stats(self):
        """获取统计信息"""
        total = self.allowed_requests + self.rejected_requests
        return {
            'allowed': self.allowed_requests,
            'rejected': self.rejected_requests,
            'total': total,
            'allow_rate': self.allowed_requests / total if total > 0 else 0
        }


class TokenBucketWithPriority:
    """支持优先级的令牌桶"""

    # 优先级常量
    PRIORITY_HIGH = 2
    PRIORITY_NORMAL = 1
    PRIORITY_LOW = 0

    def __init__(self, capacity, refill_rate):
        """
        初始化优先级令牌桶
        
        参数:
            capacity: 桶容量
            refill_rate: 补充速率
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        # 三个优先级的桶
        self.high_bucket = TokenBucket(capacity * 0.3, refill_rate * 0.3)
        self.normal_bucket = TokenBucket(capacity * 0.5, refill_rate * 0.5)
        self.low_bucket = TokenBucket(capacity * 0.2, refill_rate * 0.2)
        self.shared_bucket = TokenBucket(capacity, refill_rate)

    def consume(self, tokens, priority=PRIORITY_NORMAL):
        """
        消耗令牌（带优先级）
        
        参数:
            tokens: 令牌数
            priority: 优先级
        返回:
            success: 是否成功
        """
        # 按优先级尝试
        if priority == self.PRIORITY_HIGH:
            # 先尝试高优先级桶，再尝试共享桶
            if self.high_bucket.consume(tokens):
                return True
            if self.shared_bucket.consume(tokens):
                return True
            return False
        elif priority == self.PRIORITY_NORMAL:
            # 先尝试普通桶，再共享桶
            if self.normal_bucket.consume(tokens):
                return True
            if self.shared_bucket.consume(tokens):
                return True
            return False
        else:
            # 低优先级：只使用低优先级桶
            return self.low_bucket.consume(tokens)


class MultiTokenBucket:
    """多令牌桶（用于复合限制）"""

    def __init__(self, rate, capacity, num_buckets):
        """
        初始化多令牌桶
        
        参数:
            rate: 每个桶的速率
            capacity: 每个桶的容量
            num_buckets: 桶的数量
        """
        self.rate = rate
        self.capacity = capacity
        self.num_buckets = num_buckets
        self.buckets = [
            TokenBucket(capacity, rate)
            for _ in range(num_buckets)
        ]

    def consume_all(self, tokens):
        """
        从所有桶中消耗令牌（AND 语义）
        
        所有桶都有足够令牌才允许
        """
        for bucket in self.buckets:
            if not bucket.consume(tokens):
                return False
        return True

    def consume_any(self, tokens):
        """
        从任意一个桶中消耗令牌（OR 语义）
        """
        for bucket in self.buckets:
            if bucket.consume(tokens):
                return True
        return False


class TokenBucketSimulator:
    """令牌桶模拟器（用于可视化分析）"""

    def __init__(self, capacity, refill_rate, packet_size=1):
        """
        初始化模拟器
        
        参数:
            capacity: 桶容量
            refill_rate: 补充速率（令牌/秒）
            packet_size: 数据包大小（令牌）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.packet_size = packet_size
        self.tokens = float(capacity)
        self.last_refill = time.time()
        # 历史记录
        self.history = []

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def simulate(self, packets_arrival_times):
        """
        模拟数据包处理
        
        参数:
            packets_arrival_times: 数据包到达时间列表（秒）
        返回:
            results: 处理结果列表
        """
        results = []
        
        for arrival_time in packets_arrival_times:
            self._refill()
            
            # 检查是否可以发送
            if self.tokens >= self.packet_size:
                self.tokens -= self.packet_size
                result = 'allowed'
            else:
                result = 'dropped'
            
            results.append({
                'time': arrival_time,
                'tokens': self.tokens,
                'result': result
            })
            
            # 记录历史
            self.history.append({
                'time': arrival_time,
                'tokens': self.tokens,
                'result': result
            })
        
        return results

    def get_drop_rate(self):
        """计算丢包率"""
        if not self.history:
            return 0
        dropped = sum(1 for h in self.history if h['result'] == 'dropped')
        return dropped / len(self.history)

    def print_summary(self):
        """打印模拟摘要"""
        if not self.history:
            print("无历史数据")
            return
        
        allowed = sum(1 for h in self.history if h['result'] == 'allowed')
        dropped = len(self.history) - allowed
        
        print(f"总数据包: {len(self.history)}")
        print(f"允许: {allowed}, 丢弃: {dropped}")
        print(f"丢包率: {self.get_drop_rate():.2%}")


if __name__ == "__main__":
    # 测试令牌桶算法
    print("=== 令牌桶算法测试 ===\n")

    # 基本令牌桶
    print("--- 基本令牌桶 ---")
    bucket = TokenBucket(capacity=10, refill_rate=5)  # 容量10，速率5令牌/秒
    
    print(f"初始令牌: {bucket.get_tokens():.2f}")
    
    # 模拟数据包到达
    print("\n模拟数据包到达（每个包消耗1令牌）:")
    for i in range(15):
        time.sleep(0.2)  # 间隔 200ms
        allowed = bucket.consume(1)
        print(f"  时间 {i*0.2:.1f}s: 包{i+1} {'允许' if allowed else '拒绝'}, "
              f"剩余令牌: {bucket.get_tokens():.2f}")

    # 速率限制器
    print("\n--- 速率限制器 ---")
    limiter = RateLimiter(rate=10, burst_size=5)  # 10请求/秒，突发5
    
    print("模拟 20 个请求:")
    for i in range(20):
        allowed = limiter.allow_request()
        print(f"  请求 {i+1}: {'允许' if allowed else '拒绝'}")
    
    stats = limiter.get_stats()
    print(f"\n统计: 允许={stats['allowed']}, 拒绝={stats['rejected']}, "
          f"通过率={stats['allow_rate']:.1%}")

    # 模拟器测试
    print("\n--- 令牌桶模拟器 ---")
    simulator = TokenBucketSimulator(capacity=5, refill_rate=10, packet_size=1)
    
    # 模拟突发到达
    arrival_times = [0.0, 0.05, 0.1, 0.15, 0.2,   # 突发 5 个包
                     0.6, 0.65, 0.7, 0.75, 0.8,    # 突发 5 个包
                     1.2, 1.25, 1.3]              # 突发 3 个包
    
    results = simulator.simulate(arrival_times)
    
    print("数据包处理结果:")
    for r in results:
        print(f"  时间 {r['time']:.2f}s: {r['result']:7}, 令牌: {r['tokens']:.1f}")
    
    simulator.print_summary()

    # 优先级令牌桶
    print("\n--- 优先级令牌桶 ---")
    priority_bucket = TokenBucketWithPriority(capacity=100, refill_rate=50)
    
    print("测试优先级:")
    print(f"  高优先级请求 (5令牌): {priority_bucket.consume(5, TokenBucketWithPriority.PRIORITY_HIGH)}")
    print(f"  普通优先级请求 (5令牌): {priority_bucket.consume(5, TokenBucketWithPriority.PRIORITY_NORMAL)}")
    print(f"  低优先级请求 (5令牌): {priority_bucket.consume(5, TokenBucketWithPriority.PRIORITY_LOW)}")

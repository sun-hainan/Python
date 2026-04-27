# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / token_bucket



本文件实现 token_bucket 相关的算法功能。

"""



import time

from dataclasses import dataclass

from typing import Optional





class TokenBucket:

    """

    令牌桶算法

    

    核心原理：

    1. 桶以固定速率r填充令牌

    2. 每个令牌允许发送1个数据包（或b个字节）

    3. 桶容量为b，超出容量的令牌溢出

    4. 发送数据时消耗令牌

    """

    

    def __init__(self, rate: float, capacity: float, burst: bool = True):

        """

        初始化令牌桶

        

        Args:

            rate: 令牌填充速率（令牌/秒）

            capacity: 桶容量（最大令牌数）

            burst: 是否允许突发

        """

        self.rate = rate  # 令牌/秒

        self.capacity = capacity  # 桶容量

        self.tokens = capacity  # 当前令牌数

        self.last_update = time.time()

        

        # 统计

        self.total_tokens_consumed = 0

        self.total_requests_dropped = 0

        self.total_requests_allowed = 0

    

    def _refill(self):

        """重新填充令牌"""

        now = time.time()

        elapsed = now - self.last_update

        

        # 添加令牌

        new_tokens = elapsed * self.rate

        self.tokens = min(self.capacity, self.tokens + new_tokens)

        self.last_update = now

    

    def consume(self, tokens: float = 1.0, block: bool = False) -> bool:

        """

        消耗令牌

        

        Args:

            tokens: 要消耗的令牌数

            block: 是否阻塞等待令牌

        

        Returns:

            是否成功获取令牌

        """

        if block:

            # 阻塞直到获得令牌

            while True:

                self._refill()

                if self.tokens >= tokens:

                    self.tokens -= tokens

                    self.total_tokens_consumed += tokens

                    self.total_requests_allowed += 1

                    return True

                time.sleep(0.001)  # 等待一小段时间

        else:

            # 非阻塞

            self._refill()

            

            if self.tokens >= tokens:

                self.tokens -= tokens

                self.total_tokens_consumed += tokens

                self.total_requests_allowed += 1

                return True

            else:

                self.total_requests_dropped += 1

                return False

    

    def allow(self, tokens: float = 1.0) -> bool:

        """

        检查是否允许通过（非阻塞）

        

        Args:

            tokens: 要消耗的令牌数

        

        Returns:

            是否允许

        """

        return self.consume(tokens, block=False)

    

    def get_status(self) -> dict:

        """获取状态"""

        self._refill()

        return {

            'tokens': self.tokens,

            'capacity': self.capacity,

            'fill_rate': self.rate,

            'utilization': self.total_tokens_consumed / (self.rate * (time.time() - self.last_update + 0.001))

        }





class RateLimiter:

    """

    基于令牌桶的速率限制器

    """

    

    def __init__(self, requests_per_second: float, burst_size: int):

        """

        初始化

        

        Args:

            requests_per_second: 每秒请求数

            burst_size: 突发大小

        """

        self.bucket = TokenBucket(

            rate=requests_per_second,

            capacity=burst_size

        )

    

    def is_allowed(self) -> bool:

        """检查是否允许请求"""

        return self.bucket.allow(1.0)





class TokenBucketMultiTier:

    """

    多层令牌桶（支持不同优先级）

    """

    

    def __init__(self, tiers: list):

        """

        初始化多层令牌桶

        

        Args:

            tiers: [(rate, capacity), ...] 按优先级从高到低

        """

        self.tiers = []

        for i, (rate, capacity) in enumerate(tiers):

            self.tiers.append({

                'bucket': TokenBucket(rate, capacity),

                'priority': i,

                'rate': rate,

                'capacity': capacity

            })

    

    def consume(self, tokens: float, priority: int) -> bool:

        """

        按优先级消耗令牌

        

        Args:

            tokens: 令牌数

            priority: 优先级（0最高）

        

        Returns:

            是否成功

        """

        if priority >= len(self.tiers):

            priority = len(self.tiers) - 1

        

        # 首先尝试当前优先级

        if self.tiers[priority]['bucket'].allow(tokens):

            return True

        

        # 尝试借用低优先级桶的令牌

        for i in range(priority + 1, len(self.tiers)):

            if self.tiers[i]['bucket'].allow(tokens):

                # 借用后恢复

                return True

        

        return False





class TokenBucketWithQueue:

    """

    带队列的令牌桶（可排队等待）

    """

    

    def __init__(self, rate: float, capacity: float, queue_size: int):

        self.bucket = TokenBucket(rate, capacity)

        self.queue_size = queue_size

        self.queue = []

    

    def enqueue(self, item) -> bool:

        """入队"""

        if len(self.queue) < self.queue_size:

            self.queue.append(item)

            return True

        return False

    

    def process(self) -> Optional:

        """处理队列中的项目"""

        if self.queue and self.bucket.allow():

            return self.queue.pop(0)

        return None





def simulate_token_bucket():

    """

    模拟令牌桶行为

    """

    print("=== 令牌桶算法模拟 ===\n")

    

    # 创建令牌桶: 10令牌/秒, 容量20

    bucket = TokenBucket(rate=10, capacity=20)

    

    print(f"令牌桶配置: rate=10/s, capacity=20")

    print()

    

    # 模拟突发请求

    print("模拟突发请求 (30个请求同时到达):")

    

    for i in range(30):

        allowed = bucket.allow(1.0)

        status = "✓" if allowed else "✗"

        print(f"  请求{i:2d}: {status} (tokens={bucket.tokens:.1f})")

    

    print(f"\n统计:")

    print(f"  允许: {bucket.total_requests_allowed}")

    print(f"  拒绝: {bucket.total_requests_dropped}")

    

    # 模拟令牌补充

    print("\n\n等待令牌补充 (2秒后再次尝试10个请求):")

    time.sleep(2)

    

    for i in range(10):

        allowed = bucket.allow(1.0)

        status = "✓" if allowed else "✗"

        print(f"  请求{i:2d}: {status} (tokens={bucket.tokens:.1f})")





def demo_rate_limiting():

    """

    演示API速率限制

    """

    print("\n=== API速率限制演示 ===\n")

    

    # 限制: 5请求/秒, 突发10

    limiter = RateLimiter(requests_per_second=5, burst_size=10)

    

    print("API速率限制: 5 req/s, 突发=10")

    print()

    

    # 模拟API调用

    print("模拟API调用:")

    for i in range(20):

        allowed = limiter.is_allowed()

        print(f"  API调用{i:2d}: {'成功' if allowed else '限流'}")

        

        # 每个请求间隔0.1秒

        if i < 19:

            time.sleep(0.1)





def demo_burst_handling():

    """

    演示突发流量处理

    """

    print("\n=== 突发流量处理演示 ===\n")

    

    # 配置

    rates = [100, 50, 20]  # 不同优先级

    capacities = [10, 20, 50]

    

    multi = TokenBucketMultiTier(list(zip(rates, capacities)))

    

    print("多层令牌桶配置:")

    for i, (rate, cap) in enumerate(zip(rates, capacities)):

        print(f"  优先级{i}: rate={rate}/s, capacity={cap}")

    

    print("\n突发请求测试:")

    

    # 高优先级突发

    print("\n高优先级突发 (30个请求):")

    allowed = 0

    for i in range(30):

        if multi.consume(1, priority=0):

            allowed += 1

    print(f"  允许: {allowed}/30")

    

    # 中优先级突发

    print("\n中优先级突发 (40个请求):")

    allowed = 0

    for i in range(40):

        if multi.consume(1, priority=1):

            allowed += 1

    print(f"  允许: {allowed}/40")

    

    # 低优先级突发

    print("\n低优先级突发 (100个请求):")

    allowed = 0

    for i in range(100):

        if multi.consume(1, priority=2):

            allowed += 1

    print(f"  允许: {allowed}/100")





def demo_bandwidth_shaping():

    """

    演示带宽整形

    """

    print("\n=== 带宽整形演示 ===\n")

    

    # 1Mbps带宽限制，突发2Mbps

    # 假设MTU=1500字节, 1Mbps ≈ 83包/秒

    bucket = TokenBucket(rate=83, capacity=166)  # 2秒突发容量

    

    print("带宽整形配置:")

    print("  速率: 83 packets/s (≈1Mbps)")

    print("  容量: 166 packets (≈2Mbps突发)")

    print()

    

    # 模拟大流量

    print("模拟大流量 (200个包同时到达):")

    

    allowed = 0

    dropped = 0

    

    for i in range(200):

        if bucket.allow(1):

            allowed += 1

        else:

            dropped += 1

    

    print(f"  允许通过: {allowed}")

    print(f"  整形丢弃: {dropped}")

    print(f"  整形后速率: {allowed}/s (符合1Mbps限制)")

    

    # 等待补充后再发

    print("\n等待2秒后再次发送100个包:")

    time.sleep(2)

    

    allowed2 = sum(1 for _ in range(100) if bucket.allow(1))

    print(f"  允许通过: {allowed2}/100")





def compare_with_leaky_bucket():

    """

    对比令牌桶与漏桶

    """

    print("\n=== 令牌桶 vs 漏桶 对比 ===\n")

    

    print("| 特性       | 令牌桶              | 漏桶              |")

    print("|------------|---------------------|-------------------|")

    print("| 输出模式   | 可变(取决于令牌)     | 固定速率          |")

    print("| 突发能力   | 支持(桶满时)        | 不支持            |")

    print("| 适用场景   | 速率限制, QoS       | 流量整形          |")

    print("| 公平性     | 更好(允许突发)      | 一般              |")





if __name__ == "__main__":

    print("=" * 60)

    print("令牌桶算法实现")

    print("=" * 60)

    

    # 基本模拟

    simulate_token_bucket()

    

    # API限流

    demo_rate_limiting()

    

    # 突发处理

    demo_burst_handling()

    

    # 带宽整形

    demo_bandwidth_shaping()

    

    # 算法对比

    compare_with_leaky_bucket()

    

    print("\n" + "=" * 60)

    print("令牌桶数学分析:")

    print("=" * 60)

    print("""

令牌桶状态方程:

  dTokens/dt = r - a(t)

  

其中:

  r = 令牌填充速率

  a(t) = 令牌消耗速率



令牌数变化:

  Tokens(t) = min(C, Tokens(0) + r*t - ∫a(τ)dτ)



关键指标:

1. 长期平均速率 ≤ r

2. 突发量 ≤ C (桶容量)

3. 突发持续时间 ≤ C/r



应用场景:

- API Gateway限流

- CDN带宽控制

- 网络QoS

- 视频码率控制

""")


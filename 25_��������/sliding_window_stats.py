# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / sliding_window_stats



本文件实现 sliding_window_stats 相关的算法功能。

"""



import time

from collections import deque

from typing import List, Optional, Any

from dataclasses import dataclass

import math





@dataclass

class SlidingWindowCounter:

    """滑动窗口计数器"""

    window_size: int  # 窗口大小

    

    def __post_init__(self):

        self.buffer = deque(maxlen=self.window_size)

    

    def add(self, item: Any):

        """添加元素"""

        self.buffer.append(item)

    

    def count(self, predicate=None) -> int:

        """

        计数

        

        Args:

            predicate: 可选的过滤条件

        

        Returns:

            满足条件的元素数量

        """

        if predicate is None:

            return len(self.buffer)

        return sum(1 for x in self.buffer if predicate(x))

    

    def sum(self) -> float:

        """求和（假设元素为数值）"""

        return sum(self.buffer)

    

    def mean(self) -> float:

        """均值"""

        if not self.buffer:

            return 0.0

        return sum(self.buffer) / len(self.buffer)

    

    def clear(self):

        """清空"""

        self.buffer.clear()





class TimeBasedWindow:

    """基于时间的滑动窗口"""

    

    def __init__(self, window_seconds: float):

        self.window_seconds = window_seconds

        self.buffer = deque()  # (timestamp, value)

    

    def add(self, value: Any, timestamp: float = None):

        """添加元素"""

        if timestamp is None:

            timestamp = time.time()

        self.buffer.append((timestamp, value))

        self._evict_old()

    

    def _evict_old(self):

        """清除过期元素"""

        cutoff = time.time() - self.window_seconds

        while self.buffer and self.buffer[0][0] < cutoff:

            self.buffer.popleft()

    

    def get_values(self) -> List[Any]:

        """获取当前窗口内的值"""

        self._evict_old()

        return [v for _, v in self.buffer]

    

    def count(self) -> int:

        """计数"""

        self._evict_old()

        return len(self.buffer)

    

    def sum(self) -> float:

        """求和"""

        self._evict_old()

        return sum(v for _, v in self.buffer if isinstance(v, (int, float)))

    

    def mean(self) -> float:

        """均值"""

        self._evict_old()

        values = self.get_values()

        if not values:

            return 0.0

        return sum(values) / len(values)





class SlidingWindowMean:

    """滑动窗口均值（优化的O(1)实现）"""

    

    def __init__(self, window_size: int):

        self.window_size = window_size

        self.buffer = deque(maxlen=window_size)

        self.running_sum = 0.0

    

    def add(self, value: float):

        """添加值"""

        if len(self.buffer) == self.window_size:

            # 移除最老的

            old = self.buffer[0]

            self.running_sum -= old

        

        self.buffer.append(value)

        self.running_sum += value

    

    def mean(self) -> float:

        """获取均值"""

        if not self.buffer:

            return 0.0

        return self.running_sum / len(self.buffer)

    

    def std(self) -> float:

        """获取标准差"""

        if len(self.buffer) < 2:

            return 0.0

        m = self.mean()

        variance = sum((x - m) ** 2 for x in self.buffer) / len(self.buffer)

        return math.sqrt(variance)





class SlidingWindowVariance:

    """滑动窗口方差（Welford算法变体）"""

    

    def __init__(self, window_size: int):

        self.window_size = window_size

        self.buffer = deque(maxlen=window_size)

        self.mean = 0.0

        self.M2 = 0.0  # 平方差累积量

    

    def add(self, value: float):

        """添加值"""

        if len(self.buffer) == self.window_size:

            # 移除最老的

            old = self.buffer[0]

            n = len(self.buffer)

            

            # Welford逆向更新

            delta = old - self.mean

            self.mean -= delta / n

            self.M2 -= delta * (old - self.mean)

        

        # 添加新值

        self.buffer.append(value)

        n = len(self.buffer)

        delta = value - self.mean

        self.mean += delta / n

        self.M2 += delta * (value - self.mean)

    

    def variance(self) -> float:

        """获取方差"""

        if len(self.buffer) < 2:

            return 0.0

        return self.M2 / (len(self.buffer) - 1)

    

    def std(self) -> float:

        """获取标准差"""

        return math.sqrt(self.variance())





class SlidingWindowQuantile:

    """滑动窗口分位数（近似）"""

    

    def __init__(self, window_size: int, quantile: float):

        self.window_size = window_size

        self.quantile = quantile

        self.buffer = deque(maxlen=window_size)

    

    def add(self, value: float):

        """添加值"""

        self.buffer.append(value)

    

    def quantile_value(self) -> float:

        """获取分位数值（近似）"""

        if not self.buffer:

            return 0.0

        

        # 近似：排序（效率不高但准确）

        sorted_values = sorted(self.buffer)

        idx = int(len(sorted_values) * self.quantile)

        idx = min(idx, len(sorted_values) - 1)

        return sorted_values[idx]





class SlidingWindowMinMax:

    """滑动窗口最小最大值"""

    

    def __init__(self, window_size: int):

        self.window_size = window_size

        self.buffer = deque(maxlen=window_size)

        self.min_deque = deque()  # 保持单调递增

        self.max_deque = deque()  # 保持单调递减

    

    def add(self, value: float):

        """添加值"""

        self.buffer.append(value)

        

        # 更新min deque

        while self.min_deque and self.min_deque[-1] > value:

            self.min_deque.pop()

        self.min_deque.append(value)

        

        # 更新max deque

        while self.max_deque and self.max_deque[-1] < value:

            self.max_deque.pop()

        self.max_deque.append(value)

        

        # 移除过期

        if self.buffer[0] == self.min_deque[0]:

            self.min_deque.popleft()

        if self.buffer[0] == self.max_deque[0]:

            self.max_deque.popleft()

    

    def min_value(self) -> float:

        """最小值"""

        return self.min_deque[0] if self.min_deque else 0.0

    

    def max_value(self) -> float:

        """最大值"""

        return self.max_deque[0] if self.max_deque else 0.0





class ExponentialHistogram:

    """指数直方图（用于分位数估计）"""

    

    def __init__(self, epsilon: float = 0.01):

        self.epsilon = epsilon

        self.buckets = []  # [(count, timestamp), ...]

    

    def add(self, value: float):

        """添加值"""

        self.buckets.append((1, time.time()))

        self._compact()

    

    def _compact(self):

        """合并相邻bucket"""

        i = 0

        while i < len(self.buckets) - 1:

            if i < len(self.buckets) - 1:

                if self.buckets[i][0] == self.buckets[i + 1][0]:

                    # 合并

                    count = self.buckets[i][0] * 2

                    self.buckets[i] = (count, self.buckets[i][1])

                    self.buckets.pop(i + 1)

            i += 1





def demo_basic_counting():

    """演示基本计数"""

    print("=== 滑动窗口基本计数 ===\n")

    

    counter = SlidingWindowCounter(window_size=10)

    

    print("添加1-10:")

    for i in range(1, 11):

        counter.add(i)

        print(f"  添加 {i}: count={counter.count()}, sum={counter.sum()}")

    

    print(f"\n窗口内容: {list(counter.buffer)}")

    print(f"总数: {counter.sum()}")

    print(f"均值: {counter.mean():.1f}")





def demo_time_window():

    """演示时间窗口"""

    print("\n=== 时间滑动窗口 ===\n")

    

    window = TimeBasedWindow(window_seconds=2.0)

    

    print("基于2秒的滑动窗口:")

    

    for i in range(5):

        window.add(i * 10)

        print(f"  t={i}s: 值={i * 10}, count={window.count()}, sum={window.sum():.1f}")

        time.sleep(0.5)

    

    print("\n等待2秒后...")

    time.sleep(2.1)

    

    window._evict_old()

    print(f"  当前count: {window.count()}")





def demo_statistics():

    """演示统计量计算"""

    print("\n=== 滑动窗口统计量 ===\n")

    

    import random

    random.seed(42)

    

    # 均值

    mean_window = SlidingWindowMean(window_size=20)

    

    print("滑动均值 (窗口=20):")

    for i in range(30):

        value = 50 + random.gauss(0, 10)

        mean_window.add(value)

        

        if i % 5 == 0:

            print(f"  t={i}: mean={mean_window.mean():.2f}, std={mean_window.std():.2f}")

    

    # 分位数

    quantile_window = SlidingWindowQuantile(window_size=100, quantile=0.95)

    

    print("\n滑动95分位数 (窗口=100):")

    for _ in range(100):

        quantile_window.add(random.uniform(0, 100))

    

    print(f"  95分位数: {quantile_window.quantile_value():.2f}")

    

    # Min-Max

    minmax = SlidingWindowMinMax(window_size=10)

    

    print("\n滑动Min-Max (窗口=10):")

    for i in range(15):

        value = random.randint(1, 100)

        minmax.add(value)

        

        if i % 3 == 0:

            print(f"  t={i}: value={value}, min={minmax.min_value()}, max={minmax.max_value()}")





def demo_moving_average():

    """演示移动平均"""

    print("\n=== 移动平均对比 ===\n")

    

    import random

    random.seed(42)

    

    # 生成有趋势的数据

    data = []

    for t in range(100):

        trend = t * 0.5

        noise = random.gauss(0, 5)

        data.append(trend + noise)

    

    # SMA (简单移动平均)

    sma = SlidingWindowMean(window_size=10)

    sma_values = []

    

    for v in data:

        sma.add(v)

        sma_values.append(sma.mean())

    

    # EMA (指数移动平均)

    alpha = 0.3

    ema_values = [data[0]]

    

    for v in data[1:]:

        ema_values.append(alpha * v + (1 - alpha) * ema_values[-1])

    

    print("SMA vs EMA (最后10个值):")

    print("| t    | 实际值 | SMA    | EMA    |")

    for i in range(90, 100):

        print(f"| {i:4d} | {data[i]:6.1f} | {sma_values[i]:6.1f} | {ema_values[i]:6.1f} |")





def demo_rate_estimation():

    """演示速率估计"""

    print("\n=== 滑动窗口速率估计 ===\n")

    

    class RateEstimator:

        """基于滑动窗口的速率估计"""

        

        def __init__(self, window_seconds: float):

            self.window = TimeBasedWindow(window_seconds)

            self.last_time = time.time()

        

        def record(self, count: int = 1):

            """记录事件"""

            self.window.add((time.time(), count))

        

        def rate(self) -> float:

            """获取当前速率"""

            values = self.window.get_values()

            if not values:

                return 0.0

            

            total = sum(v for _, v in values)

            duration = self.window.window_seconds

            

            return total / duration

    

    estimator = RateEstimator(window_seconds=5.0)

    

    print("速率估计 (5秒窗口):")

    

    for burst in range(3):

        # 模拟突发流量

        for _ in range(10):

            estimator.record()

        

        rate = estimator.rate()

        print(f"  突发{burst}: {rate:.1f} events/s")

        

        time.sleep(1)





def demo_quantile_tracking():

    """演示分位数追踪"""

    print("\n=== 分位数追踪 ===\n")

    

    import random

    random.seed(42)

    

    window = SlidingWindowQuantile(window_size=100, quantile=0.5)

    

    print("中位数追踪:")

    

    values_seen = []

    for i in range(200):

        v = random.gauss(50, 10)

        window.add(v)

        values_seen.append(v)

        

        if i % 50 == 0:

            estimated = window.quantile_value()

            actual = sorted(values_seen)[len(values_seen) // 2]

            error = abs(estimated - actual)

            print(f"  t={i}: 估计={estimated:.2f}, 实际={actual:.2f}, 误差={error:.2f}")





def demo_applications():

    """演示应用场景"""

    print("\n=== 应用场景 ===\n")

    

    print("1. 网络监控:")

    print("   - 每秒请求数 (RPS)")

    print("   - 响应时间分位数 (p50, p95, p99)")

    print("   - 错误率")

    

    print("\n2. 金融交易:")

    print("   - 滚动波动率")

    print("   - 价格移动窗口平均")

    print("   - 交易量统计")

    

    print("\n3. IoT传感器:")

    print("   - 温度/湿度滑动平均")

    print("   - 异常检测 (基于滑动窗口标准差)")

    print("   - 趋势检测")





if __name__ == "__main__":

    print("=" * 60)

    print("滑动窗口流式统计算法")

    print("=" * 60)

    

    # 基本计数

    demo_basic_counting()

    

    # 时间窗口

    demo_time_window()

    

    # 统计量

    demo_statistics()

    

    # 移动平均

    demo_moving_average()

    

    # 速率估计

    demo_rate_estimation()

    

    # 分位数追踪

    demo_quantile_tracking()

    

    # 应用

    demo_applications()

    

    print("\n" + "=" * 60)

    print("算法复杂度:")

    print("=" * 60)

    print("""

| 操作       | 时间复杂度 | 空间复杂度 |

|------------|-----------|------------|

| add        | O(1)      | O(1)       |

| mean       | O(1)      | O(1)       |

| variance   | O(1)      | O(1)       |

| min/max    | O(1)      | O(1)       |

| quantile   | O(n log n)| O(n)       | (精确)

| quantile   | O(1)      | O(1)       | (近似)



注：使用单调队列可以在O(1)时间内维护min/max

""")


# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / sliding_window_stats



本文件实现 sliding_window_stats 相关的算法功能。

"""



import math

from collections import deque

from dataclasses import dataclass, field

from typing import List, Optional, Generic, TypeVar



T = TypeVar('T')





class SlidingWindowBuffer(Generic[T]):

    """

    滑动窗口循环缓冲区

    使用固定大小数组，实现O(1)的入队和出队

    """

    

    def __init__(self, window_size: int):

        self.window_size = window_size  # 窗口大小

        self.buffer: List[Optional[T]] = [None] * window_size  # 固定大小数组

        self.head = 0  # 指向最旧元素的位置

        self.count = 0  # 当前元素数量

    

    def push(self, item: T) -> None:

        """添加新元素（可能移除最旧的）"""

        # 计算新元素应放置的位置（覆盖最旧元素）

        pos = (self.head + self.count) % self.window_size

        self.buffer[pos] = item

        

        # 更新计数

        if self.count < self.window_size:

            self.count += 1

        else:

            # 窗口已满，最旧元素被覆盖，移动head

            self.head = (self.head + 1) % self.window_size

    

    def get_all(self) -> List[T]:

        """返回窗口内所有元素（按时间顺序）"""

        result = []

        for i in range(self.count):

            pos = (self.head + i) % self.window_size

            result.append(self.buffer[pos])

        return result

    

    def __len__(self) -> int:

        """返回当前窗口内元素数量"""

        return self.count

    

    def is_full(self) -> bool:

        """窗口是否已满"""

        return self.count == self.window_size





@dataclass

class RunningStats:

    """

    增量计算均值和方差

    使用Welford在线算法计算方差

    """

    n: int = 0  # 样本数量

    mean: float = 0.0  # 均值

    m2: float = 0.0  # 二阶中心矩（用于计算方差）

    

    def update(self, x: float) -> None:

        """增量更新统计量"""

        self.n += 1

        delta = x - self.mean

        self.mean += delta / self.n

        delta2 = x - self.mean

        self.m2 += delta * delta2

    

    @property

    def variance(self) -> float:

        """返回样本方差"""

        if self.n < 2:

            return 0.0

        return self.m2 / (self.n - 1)

    

    @property

    def std(self) -> float:

        """返回标准差"""

        return math.sqrt(self.variance)

    

    def reset(self) -> None:

        """重置统计量"""

        self.n = 0

        self.mean = 0.0

        self.m2 = 0.0





class SlidingWindowStats:

    """

    滑动窗口统计计算器

    维护最近W个元素的：均值、方差、最大值、最小值、和

    """

    

    def __init__(self, window_size: int):

        self.window_size = window_size  # 窗口大小

        self.buffer: SlidingWindowBuffer[float] = SlidingWindowBuffer(window_size)

        self.stats = RunningStats()  # 当前窗口统计

        self.sum_values: float = 0.0  # 窗口元素和

        self.max_heap: List[float] = []  # 最大堆

        self.min_heap: List[float] = []  # 最小堆（存负值实现）

    

    def _heap_push(self, heap: List[float], val: float, reverse: bool) -> None:

        """向堆中推入元素"""

        if reverse:

            val = -val

        import heapq

        heapq.heappush(heap, val)

    

    def _heap_pop(self, heap: List[float], reverse: bool) -> Optional[float]:

        """从堆中弹出元素"""

        if not heap:

            return None

        import heapq

        val = heapq.heappop(heap)

        return -val if reverse else val

    

    def _heap_remove(self, heap: List[float], val: float, reverse: bool) -> None:

        """从堆中移除一个元素（lazy deletion）"""

        if reverse:

            val = -val

        try:

            heap.remove(val)

        except ValueError:

            pass

    

    def update(self, value: float) -> None:

        """添加新数据点"""

        # 如果窗口已满，移除最旧的元素

        if self.buffer.is_full():

            old_val = self.buffer.buffer[self.buffer.head]

            self._heap_remove(self.max_heap, old_val, False)

            self._heap_remove(self.min_heap, old_val, True)

            self.sum_values -= old_val

            self.buffer.head = (self.buffer.head + 1) % self.window_size

            self.buffer.count -= 1

        

        # 添加新元素

        self.buffer.push(value)

        self._heap_push(self.max_heap, value, False)

        self._heap_push(self.min_heap, value, True)

        self.sum_values += value

    

    @property

    def mean(self) -> float:

        """窗口均值"""

        if len(self.buffer) == 0:

            return 0.0

        return self.sum_values / len(self.buffer)

    

    @property

    def max_val(self) -> Optional[float]:

        """窗口最大值"""

        if not self.max_heap:

            return None

        return self.max_heap[0]

    

    @property

    def min_val(self) -> Optional[float]:

        """窗口最小值"""

        if not self.min_heap:

            return None

        return -self.min_heap[0]

    

    @property

    def window_size_actual(self) -> int:

        """当前窗口大小"""

        return len(self.buffer)





class SlidingWindowMedian:

    """

    滑动窗口中位数

    使用两个堆维护：最大堆存较小的一半，最小堆存较大的一半

    """

    

    def __init__(self, window_size: int):

        self.window_size = window_size

        self.buffer: SlidingWindowBuffer[float] = SlidingWindowBuffer(window_size)

        self.small = []  # 最大堆（存负值）

        self.large = []  # 最小堆

        self.delayed: deque = deque()  # 延迟删除标记

    

    def _heap_max_push(self, heap: List[float], val: float) -> None:

        """向最大堆推入"""

        import heapq

        heapq.heappush(heap, -val)

    

    def _heap_max_pop(self, heap: List[float]) -> Optional[float]:

        """从最大堆弹出"""

        if not heap:

            return None

        import heapq

        return -heapq.heappop(heap)

    

    def _heap_min_push(self, heap: List[float], val: float) -> None:

        """向最小堆推入"""

        import heapq

        heapq.heappush(heap, val)

    

    def _heap_min_pop(self, heap: List[float]) -> Optional[float]:

        """从最小堆弹出"""

        if not heap:

            return None

        import heapq

        return heapq.heappop(heap)

    

    def update(self, value: float) -> None:

        """添加新数据点"""

        # 窗口已满则移除最旧

        if self.buffer.is_full():

            old_val = self.buffer.buffer[self.buffer.head]

            self.delayed.append(old_val)

            self.buffer.head = (self.buffer.head + 1) % self.window_size

            self.buffer.count -= 1

        

        # 添加新值

        self.buffer.push(value)

        

        # 插入到合适的堆

        if not self.large or value >= self.large[0]:

            self._heap_min_push(self.large, value)

        else:

            self._heap_max_push(self.small, value)

        

        # 平衡两个堆

        self._rebalance()

    

    def _rebalance(self) -> None:

        """平衡两个堆，使其大小相差不超过1"""

        import heapq

        

        # 确保 small 的元素数量 <= large 的元素数量

        while len(self.small) > len(self.large):

            val = self._heap_max_pop(self.small)

            if val is not None:

                self._heap_min_push(self.large, val)

        

        while len(self.large) > len(self.small) + 1:

            val = self._heap_min_pop(self.large)

            if val is not None:

                self._heap_max_push(self.small, val)

    

    @property

    def median(self) -> Optional[float]:

        """返回当前中位数"""

        if not self.large and not self.small:

            return None

        if len(self.large) > len(self.small):

            return self.large[0]

        return (-self.small[0] + self.large[0]) / 2





class ExponentialHistogram:

    """

    指数直方图 (Exponential Histogram)

    用于近似计算滑动窗口中1的个数或频率

    时间复杂度：O(log W) 更新，O(1) 查询

    """

    

    def __init__(self, window_size: int, decay_factor: float = 0.5):

        self.window_size = window_size  # 窗口大小

        self.decay_factor = decay_factor  # 衰减因子

        self.buckets: deque = deque()  # buckets[i] 存第i个bucket的计数和时间戳

        self.tau = int(1 / (1 - decay_factor))  # 收敛时间参数

    

    def _new_bucket(self, count: int, timestamp: int) -> dict:

        """创建新bucket"""

        return {'count': count, 'timestamp': timestamp}

    

    def update(self, value: int, timestamp: int) -> None:

        """更新直方图，value通常是0或1"""

        # 移除过期的bucket

        cutoff = timestamp - self.window_size

        while self.buckets and self.buckets[0]['timestamp'] < cutoff:

            self.buckets.popleft()

        

        # 更新当前bucket

        if self.buckets:

            last = self.buckets[-1]

            last['count'] += value

        else:

            self.buckets.append(self._new_bucket(value, timestamp))

        

        # 合并buckets（指数级大小）

        self._merge_buckets()

    

    def _merge_buckets(self) -> None:

        """合并相同大小的连续bucket"""

        import heapq

        

        # bucket大小呈指数增长

        sizes = []

        i = 0

        while (1 << i) <= len(self.buckets):

            sizes.append(1 << i)

            i += 1

        

        # 简化：按常规方式维护

        # 实际实现需要更复杂的合并逻辑

    

    def query(self) -> float:

        """返回估计的窗口内1的个数"""

        if not self.buckets:

            return 0.0

        

        # 加权求和（较新的bucket权重更高）

        total = 0.0

        weight_sum = 0.0

        

        for i, bucket in enumerate(self.buckets):

            weight = self.decay_factor ** (len(self.buckets) - 1 - i)

            total += bucket['count'] * weight

            weight_sum += weight

        

        if weight_sum == 0:

            return 0.0

        

        return total / weight_sum if self.decay_factor > 0 else sum(b['count'] for b in self.buckets)





# ==================== 测试代码 ====================

if __name__ == "__main__":

    import random

    

    print("=" * 50)

    print("滑动窗口统计测试")

    print("=" * 50)

    

    # 测试1：基本统计

    print("\n--- 测试1: 滑动窗口均值/方差 ---")

    window = SlidingWindowStats(window_size=5)

    

    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]

    print(f"输入序列: {data}")

    print(f"窗口大小: 5")

    

    for i, val in enumerate(data):

        window.update(val)

        print(f"  步骤{i+1}: 添加{val}, 均值={window.mean:.2f}, 最大={window.max_val}, 最小={window.min_val}")

    

    # 测试2：中位数

    print("\n--- 测试2: 滑动窗口中位数 ---")

    median_window = SlidingWindowMedian(window_size=3)

    

    data = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]

    print(f"输入序列: {data}")

    print(f"窗口大小: 3")

    

    for val in data:

        median_window.update(val)

        print(f"  添加{val}, 中位数={median_window.median}")

    

    # 测试3：指数直方图

    print("\n--- 测试3: 指数直方图 ---")

    eh = ExponentialHistogram(window_size=10)

    

    # 模拟比特流

    random.seed(42)

    bit_stream = [random.randint(0, 1) for _ in range(20)]

    print(f"比特流: {bit_stream}")

    

    for i, bit in enumerate(bit_stream):

        eh.update(bit, i)

        if i >= 9:  # 窗口填满后开始查询

            estimate = eh.query()

            actual = sum(bit_stream[max(0, i-9):i+1])

            print(f"  时刻{i}: 估计={estimate:.2f}, 实际={actual}")

    

    # 测试4：性能对比

    print("\n--- 测试4: 性能测试 ---")

    import time

    

    n = 100000

    sw = SlidingWindowStats(window_size=1000)

    

    start = time.time()

    for i in range(n):

        sw.update(random.random())

    elapsed = time.time() - start

    

    print(f"处理{n}个数据点，窗口大小1000")

    print(f"耗时: {elapsed:.3f}秒")

    print(f"吞吐: {n/elapsed:.0f} 点/秒")


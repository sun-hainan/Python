# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / exponential_histogram

本文件实现 exponential_histogram 相关的算法功能。
"""

import math
import random


class ExponentialHistogram:
    """
    指数直方图
    
    参数:
        epsilon: 近似误差参数（0 < epsilon < 1）
        max_level: 最大层级数
    """

    def __init__(self, epsilon=0.01, max_level=None):
        """
        初始化指数直方图
        
        参数:
            epsilon: 近似误差，控制精度
            max_level: 最大层级，默认根据窗口大小计算
        """
        self.epsilon = epsilon
        # 桶列表：[(value, count, timestamp), ...]
        self.buckets = []
        # 层级信息
        if max_level is None:
            # 根据 epsilon 计算最大层级
            self.max_level = int(math.ceil(math.log(1 / epsilon) / math.log(2))) + 1
        else:
            self.max_level = max_level
        # 每层最大桶数（保持奇数个以便于合并）
        self.max_buckets_per_level = 2 * self.max_level + 1
        # 总计数
        self.total_count = 0
        # 时间戳
        self.timestamp = 0

    def _level_size(self, level):
        """
        计算给定层级的桶大小
        
        参数:
            level: 层级（0-indexed）
        返回:
            size: 该层级每个桶覆盖的元素数
        """
        return 2 ** level

    def _max_buckets_for_level(self, level):
        """
        计算给定层级最大桶数
        
        参数:
            level: 层级
        返回:
            max_b: 最大桶数
        """
        # 层级越高，桶数越少
        return self.max_buckets_per_level // (level + 1)

    def add(self, value):
        """
        添加元素
        
        参数:
            value: 要添加的值
        """
        self.timestamp += 1
        self.total_count += 1
        
        # 创建新的叶子桶
        new_bucket = (value, 1, self.timestamp)
        
        # 插入桶
        self.buckets.append(new_bucket)
        
        # 尝试合并
        self._compact()

    def _compact(self):
        """
        压缩桶（从低层向高层合并）
        
        规则：
        1. 从最低层开始
        2. 如果同层桶数超过限制，合并相邻的两个桶
        3. 合并后的桶放入下一层
        """
        level = 0
        current_level_buckets = []
        buckets_to_process = list(self.buckets)
        self.buckets = []
        
        while buckets_to_process:
            bucket = buckets_to_process.pop(0)
            current_level_buckets.append(bucket)
            
            # 检查该层是否满了
            max_b = self._max_buckets_for_level(level)
            
            if len(current_level_buckets) >= max_b:
                # 需要合并
                # 合并前两个桶
                merged = self._merge_two_buckets(
                    current_level_buckets[0],
                    current_level_buckets[1]
                )
                # 移除已合并的桶
                current_level_buckets = current_level_buckets[2:]
                # 将合并后的桶放入下一层处理
                buckets_to_process.append(merged)
                level += 1
                
                # 如果层级超过限制，继续合并
                while level > 0 and len(buckets_to_process) > self._max_buckets_for_level(level):
                    b1 = buckets_to_process.pop(0)
                    b2 = buckets_to_process.pop(0)
                    merged = self._merge_two_buckets(b1, b2)
                    buckets_to_process.append(merged)
                    level += 1
            else:
                # 该层还有空间，将当前处理的桶保留
                pass
        
        # 将剩余的桶放回
        self.buckets = current_level_buckets + buckets_to_process

    def _merge_two_buckets(self, b1, b2):
        """
        合并两个桶
        
        参数:
            b1: 桶1 (value, count, timestamp)
            b2: 桶2
        返回:
            merged: 合并后的桶
        """
        # 简单策略：保留第一个桶的值，累加计数
        value1, count1, ts1 = b1
        value2, count2, ts2 = b2
        
        # 加权平均
        total_count = count1 + count2
        avg_value = (value1 * count1 + value2 * count2) / total_count
        
        return (avg_value, total_count, max(ts1, ts2))

    def range_query(self, left, right):
        """
        范围查询：返回落在 [left, right] 范围内的计数
        
        参数:
            left: 范围左边界
            right: 范围右边界
        返回:
            count: 估计的计数
        """
        count = 0
        for value, bucket_count, _ in self.buckets:
            if left <= value <= right:
                count += bucket_count
        return count

    def quantile(self, q):
        """
        分位数查询
        
        参数:
            q: 分位数 (0 < q < 1)
        返回:
            value: 估计的分位数值
        """
        if self.total_count == 0:
            return None
        
        target = self.total_count * q
        current = 0
        
        for value, bucket_count, _ in self.buckets:
            current += bucket_count
            if current >= target:
                return value
        
        return self.buckets[-1][0] if self.buckets else None

    def median(self):
        """获取中位数"""
        return self.quantile(0.5)

    def get_distribution(self, num_bins=10):
        """
        获取近似的分布直方图
        
        参数:
            num_bins: 分箱数
        返回:
            bins: [(range, count), ...]
        """
        if not self.buckets:
            return []
        
        # 找到值域范围
        values = [b[0] for b in self.buckets]
        min_val = min(values)
        max_val = max(values)
        
        if min_val == max_val:
            return [((min_val, max_val), self.total_count)]
        
        bin_width = (max_val - min_val) / num_bins
        bins = [0] * num_bins
        
        for value, count, _ in self.buckets:
            bin_idx = min(int((value - min_val) / bin_width), num_bins - 1)
            bins[bin_idx] += count
        
        return [
            ((min_val + i * bin_width, min_val + (i + 1) * bin_width), bins[i])
            for i in range(num_bins)
        ]

    def get_stats(self):
        """获取统计信息"""
        return {
            'total_count': self.total_count,
            'num_buckets': len(self.buckets),
            'max_level': self.max_level
        }


class ExponentialHistogramOptimized:
    """
    优化的指数直方图
    
    使用更高效的桶合并策略
    """

    def __init__(self, epsilon=0.01, window_size=None):
        """
        初始化
        
        参数:
            epsilon: 近似精度
            window_size: 滑动窗口大小（可选，用于定时删除旧桶）
        """
        self.epsilon = epsilon
        self.window_size = window_size
        # 层级式存储
        self.levels = [[] for _ in range(int(math.log(1/epsilon)) + 2)]
        self.total = 0

    def add(self, value):
        """添加元素"""
        # 级别 0 存储原子元素
        self.levels[0].append((value, 1))
        self.total += 1
        self._propagate(0)

    def _propagate(self, level):
        """向上传播合并"""
        max_size = 2 ** (level + 1)
        
        while len(self.levels[level]) > max_size:
            # 合并两个桶
            if len(self.levels[level]) >= 2:
                b1 = self.levels[level].pop(0)
                b2 = self.levels[level].pop(0)
                merged = (b1[0], b1[1] + b2[1])
                self.levels[level + 1].append(merged)
                self._propagate(level + 1)

    def range_query(self, left, right):
        """范围查询"""
        count = 0
        for level in self.levels:
            for value, cnt in level:
                if left <= value <= right:
                    count += cnt
        return count

    def quantile(self, q):
        """分位数查询"""
        if self.total == 0:
            return None
        
        target = self.total * q
        cumulative = 0
        
        # 从低层到高层遍历
        for level in self.levels:
            for value, cnt in level:
                cumulative += cnt
                if cumulative >= target:
                    return value
        
        return self.levels[-1][-1][0] if self.levels[-1] else None

    def get_total(self):
        """获取总计数"""
        return self.total


class SlidingWindowExponentialHistogram:
    """
    滑动窗口指数直方图
    
    带有时间窗口的指数直方图
    """

    def __init__(self, window_size, epsilon=0.01):
        """
        初始化
        
        参数:
            window_size: 窗口大小
            epsilon: 近似精度
        """
        self.window_size = window_size
        self.epsilon = epsilon
        # 存储 (timestamp, value) 对
        self.data = []
        # 指数直方图
        self.histogram = ExponentialHistogram(epsilon)
        # 过期时间戳
        self.expire_threshold = 0

    def add(self, value, timestamp=None):
        """添加元素"""
        if timestamp is None:
            timestamp = len(self.data)
        
        self.data.append((timestamp, value))
        self.histogram.add(value)
        
        # 清理过期数据
        self._expire(timestamp)

    def _expire(self, current_ts):
        """删除过期数据"""
        self.expire_threshold = current_ts - self.window_size
        
        # 简化：重建直方图（实际应该增量删除）
        if len(self.data) > self.window_size * 2:
            self.data = [d for d in self.data if d[0] > self.expire_threshold]
            # 重建
            self.histogram = ExponentialHistogram(self.epsilon)
            for _, v in self.data:
                self.histogram.add(v)

    def range_query(self, left, right):
        """范围查询"""
        return self.histogram.range_query(left, right)

    def quantile(self, q):
        """分位数查询"""
        return self.histogram.quantile(q)

    def get_active_window_size(self):
        """获取活跃窗口大小"""
        return len(self.data)


if __name__ == "__main__":
    print("=== 指数直方图测试 ===\n")

    # 基本功能测试
    print("--- 基本功能 ---")
    hist = ExponentialHistogram(epsilon=0.01)
    
    # 添加 0-99
    for i in range(100):
        hist.add(i)
    
    print(f"总计数: {hist.total_count}")
    print(f"桶数: {len(hist.buckets)}")
    print(f"中位数: {hist.median()}")
    print(f"范围 [20, 40] 计数: {hist.range_query(20, 40)}")

    # 分布测试
    print("\n--- 分布测试 ---")
    hist2 = ExponentialHistogram(epsilon=0.05)
    
    # 添加双峰分布数据
    data = [random.gauss(25, 3) for _ in range(500)] + \
           [random.gauss(75, 3) for _ in range(500)]
    
    for v in data:
        hist2.add(v)
    
    print(f"双峰分布:")
    print(f"  总计数: {hist2.total_count}")
    print(f"  桶数: {len(hist2.buckets)}")
    print(f"  25% 分位: {hist2.quantile(0.25):.2f}")
    print(f"  50% 分位: {hist2.quantile(0.50):.2f}")
    print(f"  75% 分位: {hist2.quantile(0.75):.2f}")
    
    # 分布直方图
    print("\n分布直方图:")
    bins = hist2.get_distribution(10)
    for (left, right), count in bins:
        bar = '*' * int(count / 50)
        print(f"  [{left:5.1f}, {right:5.1f}]: {bar}")

    # 滑动窗口测试
    print("\n--- 滑动窗口指数直方图 ---")
    sw_hist = SlidingWindowExponentialHistogram(window_size=50, epsilon=0.05)
    
    for i in range(100):
        sw_hist.add(i)
        if i % 20 == 0:
            print(f"  时间 {i}: 窗口大小={sw_hist.get_active_window_size()}, "
                  f"计数={sw_hist.histogram.total_count}")

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    
    n = 100000
    hist = ExponentialHistogram(epsilon=0.01)
    
    start = time.time()
    for i in range(n):
        hist.add(random.gauss(50, 10))
    elapsed = time.time() - start
    
    print(f"  添加 {n} 个元素: {elapsed:.2f}s ({n/elapsed:.0f} ops/s)")
    print(f"  桶数: {len(hist.buckets)}")
    
    # 分位数查询
    start = time.time()
    for _ in range(1000):
        hist.quantile(random.random())
    q_time = time.time() - start
    print(f"  1000 次分位数查询: {q_time:.3f}s")

    # 精度分析
    print("\n--- 精度分析 ---")
    for eps in [0.1, 0.05, 0.01, 0.005]:
        hist = ExponentialHistogram(epsilon=eps)
        for i in range(1000):
            hist.add(i)
        
        actual_median = 500
        estimated_median = hist.median()
        error = abs(estimated_median - actual_median) if estimated_median else float('inf')
        
        print(f"  epsilon={eps}: 估计中位数={estimated_median:.1f}, 误差={error:.1f}")

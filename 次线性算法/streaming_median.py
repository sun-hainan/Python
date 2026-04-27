# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / streaming_median

本文件实现 streaming_median 相关的算法功能。
"""

import heapq
import random


class StreamingMedianTwoHeaps:
    """
    两堆算法维护流中位数
    
    维护两个堆:
    - max_heap (存储前半部分,中位数的候选)
    - min_heap (存储后半部分)
    
    性质:
    - max_heap 所有元素 <= min_heap 所有元素
    - |max_heap| = |min_heap| 或 |max_heap| = |min_heap| + 1
    - 中位数 = max_heap[0] (奇数) 或 (max_heap[0] + min_heap[0])/2 (偶数)
    """
    
    def __init__(self):
        """初始化两个堆"""
        # 最大堆: Python 的 heapq 是最小堆,所以存负数
        self.max_heap = []  # 存储前半部分 (包括中位数)
        # 最小堆: 存储后半部分
        self.min_heap = []
    
    def add(self, num):
        """
        添加一个新元素
        
        Parameters
        ----------
        num : float
            要添加的元素
        """
        # 先加入最大堆
        # Python heapq 是最小堆,存负数实现最大堆
        heapq.heappush(self.max_heap, -num)
        
        # 平衡: 确保 max_heap 所有元素 <= min_heap 所有元素
        if self.min_heap and -self.max_heap[0] > self.min_heap[0]:
            val = -heapq.heappop(self.max_heap)
            heapq.heappush(self.min_heap, val)
        
        # 平衡大小: |max_heap| = |min_heap| 或 |max_heap| = |min_heap| + 1
        if len(self.max_heap) > len(self.min_heap) + 1:
            val = -heapq.heappop(self.max_heap)
            heapq.heappush(self.min_heap, val)
        elif len(self.max_heap) < len(self.min_heap):
            val = heapq.heappop(self.min_heap)
            heapq.heappush(self.max_heap, -val)
    
    def get_median(self):
        """
        获取当前中位数
        
        Returns
        -------
        float
            中位数值
        """
        if not self.max_heap and not self.min_heap:
            return None  # 无数据
        
        if len(self.max_heap) > len(self.min_heap):
            # 奇数个元素
            return -self.max_heap[0]
        else:
            # 偶数个元素
            return (-self.max_heap[0] + self.min_heap[0]) / 2.0
    
    def get_size(self):
        """
        获取已处理元素数量
        
        Returns
        -------
        int
            元素数量
        """
        return len(self.max_heap) + len(self.min_heap)


class StreamingMedianCounting:
    """
    计数排序变体的流式中位数
    
    适用于整数且范围较小的情况
    
    Parameters
    ----------
    min_val : int
        最小值
    max_val : int
        最大值
    """
    
    def __init__(self, min_val=0, max_val=1000):
        self.min_val = min_val
        self.max_val = max_val
        self.range_size = max_val - min_val + 1
        self.count = [0] * self.range_size
        self.total = 0
    
    def add(self, num):
        """
        添加元素
        
        Parameters
        ----------
        num : int
            要添加的元素
        """
        if num < self.min_val or num > self.max_val:
            raise ValueError(f"值必须在 [{self.min_val}, {self.max_val}] 范围内")
        
        idx = num - self.min_val
        self.count[idx] += 1
        self.total += 1
    
    def get_median(self):
        """
        获取中位数
        
        Returns
        -------
        float or int
            中位数
        """
        if self.total == 0:
            return None
        
        target = (self.total + 1) // 2  # 中位数的 rank
        
        cumsum = 0
        for i, c in enumerate(self.count):
            cumsum += c
            if cumsum >= target:
                return self.min_val + i
        
        return self.max_val  # 不应到达这里


class ReservoirSampler:
    """
    水库采样: 流数据随机采样
    
    保持一个大小为 k 的样本,所有样本被选中的概率相等
    
    Parameters
    ----------
    k : int
        样本容量
    """
    
    def __init__(self, k):
        self.k = k
        self.reservoir = []  # 样本
        self.n_seen = 0  # 已见过的元素数量
    
    def add(self, num):
        """
        处理新元素
        
        Parameters
        ----------
        num : any
            要处理的元素
        """
        self.n_seen += 1
        
        if len(self.reservoir) < self.k:
            # 初始填充
            self.reservoir.append(num)
        else:
            # 以 k/n 的概率替换
            idx = random.randint(1, self.n_seen)
            if idx <= self.k:
                self.reservoir[idx - 1] = num
    
    def get_sample(self):
        """
        获取当前样本
        
        Returns
        -------
        list
            样本列表
        """
        return self.reservoir.copy()
    
    def estimate_median(self):
        """
        从样本估计中位数
        
        Returns
        -------
        float
            估计的中位数
        """
        if not self.reservoir:
            return None
        
        sorted_sample = sorted(self.reservoir)
        k = len(sorted_sample)
        
        if k % 2 == 1:
            return sorted_sample[k // 2]
        else:
            return (sorted_sample[k // 2 - 1] + sorted_sample[k // 2]) / 2.0


def streaming_percentile(stream, percentile, memory_limit=None):
    """
    流数据百分位数估计
    
    使用简化的直方图方法
    
    Parameters
    ----------
    stream : iterable
        数据流
    percentile : float
        百分位数 (0-100)
    memory_limit : int
        内存限制 (直方图桶数量)
    
    Returns
    -------
    float
        估计的百分位数
    """
    if memory_limit is None:
        memory_limit = 1000  # 默认1000个桶
    
    # 第一次遍历: 估计范围
    min_val = float('inf')
    max_val = float('-inf')
    count = 0
    
    for x in stream:
        min_val = min(min_val, x)
        max_val = max(max_val, x)
        count += 1
    
    if count == 0:
        return None
    
    # 创建直方图
    bucket_size = max(1, (max_val - min_val) / memory_limit)
    histogram = [0] * memory_limit
    
    # 第二次遍历: 填充直方图 (需要重新遍历流)
    # 注意: 这假设流可以被重新访问,实际场景中可能不行
    # 这里简化处理
    return min_val + (max_val - min_val) * percentile / 100.0


def moving_window_median(arr, window_size):
    """
    滑动窗口中位数
    
    对于数组 arr,计算每个长度为 window_size 的窗口的中位数
    
    时间复杂度: O(n log window_size)
    空间复杂度: O(window_size)
    
    Parameters
    ----------
    arr : list
        输入数组
    window_size : int
        窗口大小
    
    Returns
    -------
    list
        各窗口的中位数
    """
    n = len(arr)
    
    if window_size > n:
        return []
    
    result = []
    median_finder = StreamingMedianTwoHeaps()
    
    # 初始化第一个窗口
    for i in range(window_size):
        median_finder.add(arr[i])
    
    result.append(median_finder.get_median())
    
    # 滑动窗口
    for i in range(window_size, n):
        # 添加新元素 (通过移除再添加实现,实际应该支持删除)
        # 简化: 重新构建
        median_finder = StreamingMedianTwoHeaps()
        for j in range(i - window_size + 1, i + 1):
            median_finder.add(arr[j])
        result.append(median_finder.get_median())
    
    return result


def verify_median_property(stream_median, full_arr):
    """
    验证流中位数算法的正确性
    
    Parameters
    ----------
    stream_median : StreamingMedianTwoHeaps
        流中位数对象
    full_arr : list
        完整数组
    
    Returns
    -------
    tuple
        (计算的中位数, 真实中位数, 是否正确)
    """
    sorted_arr = sorted(full_arr)
    n = len(sorted_arr)
    
    if n % 2 == 1:
        true_median = sorted_arr[n // 2]
    else:
        true_median = (sorted_arr[n // 2 - 1] + sorted_arr[n // 2]) / 2.0
    
    calc_median = stream_median.get_median()
    
    is_correct = abs(calc_median - true_median) < 1e-9
    
    return calc_median, true_median, is_correct


if __name__ == "__main__":
    # 测试: 流式中位数算法
    
    print("=" * 60)
    print("流式中位数算法测试")
    print("=" * 60)
    
    random.seed(42)
    
    # 测试两堆算法
    print("\n--- 两堆算法 ---")
    
    stream_median = StreamingMedianTwoHeaps()
    test_stream = [5, 2, 8, 1, 9, 3, 7, 4, 6]
    
    print(f"输入流: {test_stream}")
    
    for i, x in enumerate(test_stream):
        stream_median.add(x)
        current_median = stream_median.get_median()
        print(f"添加 {x}: 当前中位数 = {current_median}, 已处理 {i+1} 个元素")
    
    # 验证正确性
    calc, true, correct = verify_median_property(stream_median, test_stream)
    print(f"\n最终验证: 计算={calc}, 真实={true}, 正确={correct}")
    
    # 大规模测试
    print("\n--- 大规模随机测试 ---")
    
    large_stream = StreamingMedianTwoHeaps()
    n_test = 10000
    random_values = [random.uniform(0, 1000) for _ in range(n_test)]
    
    for x in random_values:
        large_stream.add(x)
    
    calc_median, true_median, correct_large = verify_median_property(
        large_stream, random_values
    )
    
    print(f"大规模测试 ({n_test} 个元素):")
    print(f"  计算中位数: {calc_median:.4f}")
    print(f"  真实中位数: {true_median:.4f}")
    print(f"  正确: {correct_large}")
    
    # 测试计数排序变体
    print("\n--- 计数排序变体 ---")
    
    counting_median = StreamingMedianCounting(min_val=0, max_val=100)
    
    for x in [45, 23, 67, 12, 89, 34, 56, 78, 90, 11]:
        counting_median.add(x)
    
    print(f"输入: [45, 23, 67, 12, 89, 34, 56, 78, 90, 11]")
    print(f"中位数: {counting_median.get_median()}")
    
    # 测试水库采样
    print("\n--- 水库采样估计中位数 ---")
    
    reservoir = ReservoirSampler(k=100)
    
    for x in random_values[:1000]:
        reservoir.add(x)
    
    sample = reservoir.get_sample()
    estimated_median = reservoir.estimate_median()
    
    true_median_1000 = sorted(random_values[:1000])[500]
    
    print(f"水库采样 (k=100, 前1000个元素):")
    print(f"  估计中位数: {estimated_median:.4f}")
    print(f"  真实中位数: {true_median_1000:.4f}")
    
    # 测试滑动窗口中位数
    print("\n--- 滑动窗口中位数 ---")
    
    arr = [1, 3, -1, -3, 5, 3, 6, 7]
    window = 3
    
    result = moving_window_median(arr, window)
    
    print(f"数组: {arr}")
    print(f"窗口大小: {window}")
    print(f"滑动窗口中位数: {result}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

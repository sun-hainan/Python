# -*- coding: utf-8 -*-
"""
算法实现：数据流算法 / count_min_sketch

本文件实现 count_min_sketch 相关的算法功能。
"""

import hashlib
import math
from typing import Dict, List, Optional, Any, Callable


class CountMinSketch:
    """
    Count-Min Sketch 频率估计器
    
    使用多个哈希函数将元素映射到二维计数器数组。
    估计某个元素的频率时，返回所有对应计数器中的最小值。
    这种设计确保估计值 >= 真实频率（上界估计）。
    
    参数:
        epsilon: 误差参数，控制估计精度 (误差 <= ε * total_count)
        delta: 失败概率参数 (成功概率 >= 1 - δ)
        seed: 随机种子，用于生成独立的哈希函数
    """
    
    def __init__(self, epsilon: float = 0.01, delta: float = 0.01, seed: int = 42):
        # epsilon: 误差上界参数，越小精度越高
        self.epsilon = epsilon
        
        # delta: 置信度参数，越小成功概率越高
        self.delta = delta
        
        # width: 计数器数组的宽度，基于ε计算
        self.width = math.ceil(math.e / epsilon)
        
        # depth: 哈希函数的数量，基于δ计算
        self.depth = math.ceil(math.log(1 / delta))
        
        # table: 二维计数器表，depth x width
        self.table = [[0] * self.width for _ in range(self.depth)]
        
        # seed: 随机种子，确保可重复性
        self.seed = seed
        
        # hash_agents: 哈希函数生成器列表
        self.hash_agents = self._generate_hash_functions()
        
        # total_count: 已添加元素的总数
        self.total_count = 0
        
        # item_count: 实际添加的唯一元素数量
        self.item_count = 0
    
    def _generate_hash_functions(self) -> List[Callable[[str], int]]:
        """
        生成depth个独立的哈希函数
        
        使用多个不同的哈希算法组合来生成独立的哈希函数。
        每个哈希函数将字符串映射到[0, width-1]范围内。
        
        返回:
            List[Callable[[str], int]]: 哈希函数列表
        """
        # hash_funcs: 基础哈希函数列表，使用不同算法
        hash_funcs = [
            lambda x: int(hashlib.md5(x.encode()).hexdigest(), 16),
            lambda x: int(hashlib.sha1(x.encode()).hexdigest(), 16),
            lambda x: int(hashlib.sha256(x.encode()).hexdigest(), 16),
        ]
        
        # result: 生成的哈希函数列表
        result = []
        
        for i in range(self.depth):
            # base_hash: 基础哈希函数选择器
            base_hash = hash_funcs[i % len(hash_funcs)]
            
            # salt: 加盐值，确保不同深度的哈希函数不同
            salt = self.seed + i * 12345
            
            # hash_func: 组合后的哈希函数
            hash_func = lambda x, bh=base_hash, s=salt: (bh(x) + s) % self.width
            
            result.append(hash_func)
        
        return result
    
    def update(self, item: Any, count: int = 1) -> None:
        """
        更新某个元素的频率计数
        
        将元素通过所有哈希函数映射，并在对应计数器上加count。
        时间复杂度: O(depth) = O(log(1/δ))
        
        参数:
            item: 要更新的元素（会被转换为字符串后哈希）
            count: 增加的计数，默认为1
        """
        # item_str: 元素转换为字符串
        item_str = str(item)
        
        # 更新所有哈希函数对应的计数器
        for i in range(self.depth):
            # hash_idx: 当前哈希函数返回的索引
            hash_idx = self.hash_agents[i](item_str)
            
            # table[i][hash_idx]: 对应的计数器加count
            self.table[i][hash_idx] += count
        
        # total_count: 更新总计数
        self.total_count += count
        
        # 如果这是新元素，更新唯一元素计数
        if not hasattr(self, '_seen'):
            self._seen = set()
        if item not in self._seen:
            self._seen.add(item)
            self.item_count += 1
    
    def estimate(self, item: Any) -> int:
        """
        估计某个元素的频率
        
        返回所有对应计数器中的最小值。
        这给出了真实频率的上界估计。
        时间复杂度: O(depth) = O(log(1/δ))
        
        参数:
            item: 要估计的元素
        
        返回:
            int: 频率的估计值（保证 >= 真实频率）
        """
        # item_str: 元素转换为字符串
        item_str = str(item)
        
        # min_count: 最小估计值，初始化为无穷大
        min_count = float('inf')
        
        # 遍历所有哈希函数，取最小值
        for i in range(self.depth):
            # hash_idx: 当前哈希函数返回的索引
            hash_idx = self.hash_agents[i](item_str)
            
            # current_count: 当前计数器值
            current_count = self.table[i][hash_idx]
            
            # 更新最小值
            if current_count < min_count:
                min_count = current_count
        
        return int(min_count)
    
    def merge(self, other: 'CountMinSketch') -> None:
        """
        合并另一个Count-Min Sketch到当前结构
        
        两个sketch必须具有相同的epsilon和delta参数。
        合并后，当前sketch包含两个sketch的信息。
        
        参数:
            other: 要合并的另一个CountMinSketch
        
        异常:
            ValueError: 当参数不匹配时抛出
        """
        # 参数检查
        if self.epsilon != other.epsilon or self.delta != other.delta:
            raise ValueError("Cannot merge Count-Min Sketches with different parameters")
        
        # 合并计数器表
        for i in range(self.depth):
            for j in range(self.width):
                # table[i][j]: 当前计数器
                # other.table[i][j]: 被合并的计数器
                self.table[i][j] += other.table[i][j]
        
        # 更新统计信息
        self.total_count += other.total_count
        self.item_count += other.item_count
    
    def get_heavy_hitters(self, threshold: float = 0.001) -> List[tuple]:
        """
        获取重击者（频繁项）
        
        返回频率超过threshold * total_count的所有元素。
        这是一种近似算法，可能包含假阳性。
        
        参数:
            threshold: 频率阈值，默认为0.1%（总计数的千分之一）
        
        返回:
            List[tuple]: (元素, 估计频率) 列表，按频率降序排列
        """
        # heavy_hitters: 重击者列表
        heavy_hitters = []
        
        # threshold_count: 转换为绝对计数阈值
        threshold_count = threshold * self.total_count
        
        # 遍历所有已知的元素
        for item in getattr(self, '_seen', set()):
            # estimate: 元素的估计频率
            estimate = self.estimate(item)
            
            # 如果超过阈值，添加到结果
            if estimate >= threshold_count:
                heavy_hitters.append((item, estimate))
        
        # 按频率降序排序
        heavy_hitters.sort(key=lambda x: x[1], reverse=True)
        
        return heavy_hitters
    
    def reset(self) -> None:
        """
        重置所有计数器为零
        
        清空所有计数，但保留哈希函数和参数配置。
        """
        # table: 重置为全零
        self.table = [[0] * self.width for _ in range(self.depth)]
        
        # total_count: 重置为0
        self.total_count = 0
        
        # item_count: 重置为0
        self.item_count = 0
        
        # _seen: 清空已见元素集合
        if hasattr(self, '_seen'):
            self._seen.clear()
    
    def get_memory_usage(self) -> int:
        """
        获取当前内存使用量估计（字节）
        
        返回:
            int: 估计的内存使用量
        """
        # 每个计数器是整数，在Python中通常是28字节
        # counter_size: 单个计数器的大小
        counter_size = 28
        
        # total_size: 总内存使用
        total_size = self.depth * self.width * counter_size
        
        return total_size
    
    def __repr__(self) -> str:
        """返回Count-Min Sketch的字符串表示"""
        return f"CountMinSketch(width={self.width}, depth={self.depth}, total_count={self.total_count})"


class CountMinSketchWithConservativeUpdate(CountMinSketch):
    """
    保守更新版本的Count-Min Sketch
    
    在更新时，对于给定的元素，只在当前值小于估算值时才更新计数器。
    这种方法可以减少过估计问题，提高准确性。
    
    继承自CountMinSketch，覆盖update方法。
    """
    
    def update(self, item: Any, count: int = 1) -> None:
        """
        保守更新元素的频率计数
        
        只有当当前估算值小于要更新的计数值时才更新。
        这种方法可以减少过估计，使估计值更接近真实值。
        
        参数:
            item: 要更新的元素
            count: 增加的计数，默认为1
        """
        # item_str: 元素转换为字符串
        item_str = str(item)
        
        # current_estimate: 当前对该元素的估计
        current_estimate = self.estimate(item)
        
        # new_count: 新的目标计数值
        new_count = current_estimate + count
        
        # 保守更新：只在需要时才更新
        for i in range(self.depth):
            # hash_idx: 当前哈希函数返回的索引
            hash_idx = self.hash_agents[i](item_str)
            
            # 如果当前计数器值小于新计数值，则更新
            if self.table[i][hash_idx] < new_count:
                self.table[i][hash_idx] = new_count
        
        # 更新统计信息
        self.total_count += count
        
        # 如果是新元素，更新唯一元素计数
        if not hasattr(self, '_seen'):
            self._seen = set()
        if item not in self._seen:
            self._seen.add(item)
            self.item_count += 1


class CountMinSketchWithDecay(CountMinSketch):
    """
    带衰减功能的Count-Min Sketch
    
    支持对旧数据进行指数衰减，使得最近的数据有更高的权重。
    适用于需要追踪滑动时间窗口内频率的场景。
    
    参数:
        decay_factor: 衰减因子，每次更新时旧数据乘以此因子
    """
    
    def __init__(self, epsilon: float = 0.01, delta: float = 0.01, seed: int = 42, decay_factor: float = 0.99):
        # 调用父类构造函数
        super().__init__(epsilon, delta, seed)
        
        # decay_factor: 衰减因子，范围(0, 1)，越小衰减越快
        self.decay_factor = decay_factor
        
        # update_count: 更新次数计数器
        self.update_count = 0
    
    def update(self, item: Any, count: int = 1) -> None:
        """
        更新元素频率并应用衰减
        
        在更新之前，先对所有计数器应用衰减。
        然后再添加新的计数。
        
        参数:
            item: 要更新的元素
            count: 增加的计数，默认为1
        """
        # update_count: 更新计数器
        self.update_count += 1
        
        # 每隔一定次数应用衰减（避免每次都遍历整个表）
        if self.update_count % 100 == 0:
            self._apply_decay()
        
        # 调用父类更新方法
        super().update(item, count)
    
    def _apply_decay(self) -> None:
        """
        对所有计数器应用衰减
        
        将每个计数器乘以衰减因子并向下取整。
        """
        for i in range(self.depth):
            for j in range(self.width):
                # table[i][j]: 当前计数器值
                # decay_factor: 衰减因子
                self.table[i][j] = int(self.table[i][j] * self.decay_factor)


if __name__ == "__main__":
    print("=" * 60)
    print("Count-Min Sketch 测试")
    print("=" * 60)
    
    # 创建Count-Min Sketch实例
    # epsilon=0.01, delta=0.01 表示99%置信度下误差不超过1%
    sketch = CountMinSketch(epsilon=0.01, delta=0.01, seed=42)
    
    print(f"\n[初始化] Count-Min Sketch 创建成功")
    print(f"  - Width (计数器宽度): {sketch.width}")
    print(f"  - Depth (哈希函数数量): {sketch.depth}")
    print(f"  - 内存使用: {sketch.get_memory_usage()} bytes")
    
    # 测试数据流：模拟网络请求日志
    print("\n[模拟数据流] 开始处理数据流...")
    
    # 数据流：包含大量重复元素
    data_stream = [
        "IP_A", "IP_B", "IP_A", "IP_C", "IP_A", "IP_B", "IP_A",
        "IP_D", "IP_A", "IP_B", "IP_A", "IP_A", "IP_A", "IP_C",
        "IP_B", "IP_A", "IP_D", "IP_A", "IP_B", "IP_A"
    ]
    
    # 更新频率统计
    # expected_freq: 预期频率字典
    expected_freq = {}
    for item in data_stream:
        expected_freq[item] = expected_freq.get(item, 0) + 1
    
    print(f"  - 数据流长度: {len(data_stream)}")
    print(f"  - 唯一元素数: {len(expected_freq)}")
    
    # 更新sketch
    for item in data_stream:
        sketch.update(item)
    
    print(f"\n[更新完成] 所有元素已更新到Sketch")
    print(f"  - 总计数: {sketch.total_count}")
    
    # 测试频率估计
    print("\n[频率估计测试]")
    print("-" * 60)
    print(f"{'元素':<10} {'真实频率':<12} {'估计频率':<12} {'误差':<10}")
    print("-" * 60)
    
    for item, true_freq in sorted(expected_freq.items(), key=lambda x: x[1], reverse=True):
        estimate = sketch.estimate(item)
        error = estimate - true_freq
        error_pct = (error / true_freq * 100) if true_freq > 0 else 0
        print(f"{item:<10} {true_freq:<12} {estimate:<12} {error:>+6} ({error_pct:>+.1f}%)")
    
    # 测试重击者检测
    print("\n[重击者检测测试]")
    print(f"阈值: 0.1 (10% of total)")
    threshold = 0.1
    heavy_hitters = sketch.get_heavy_hitters(threshold)
    print(f"检测到的重击者数量: {len(heavy_hitters)}")
    for item, freq in heavy_hitters:
        print(f"  - {item}: {freq} (占比: {freq/sketch.total_count*100:.1f}%)")
    
    # 测试合并操作
    print("\n[合并操作测试]")
    sketch2 = CountMinSketch(epsilon=0.01, delta=0.01, seed=100)
    
    # 新数据流
    new_data = ["IP_A", "IP_E", "IP_A", "IP_E", "IP_A"]
    for item in new_data:
        sketch2.update(item)
    
    print(f"  - Sketch2 总计数: {sketch2.total_count}")
    print(f"  - 合并前 Sketch1 总计数: {sketch.total_count}")
    
    sketch.merge(sketch2)
    
    print(f"  - 合并后总计数: {sketch.total_count}")
    
    # 测试保守更新版本
    print("\n[保守更新版本测试]")
    conservative_sketch = CountMinSketchWithConservativeUpdate(epsilon=0.01, delta=0.01, seed=42)
    
    for item in data_stream:
        conservative_sketch.update(item)
    
    print(f"  - 保守更新后总计数: {conservative_sketch.total_count}")
    for item, true_freq in sorted(expected_freq.items(), key=lambda x: x[1], reverse=True):
        estimate = conservative_sketch.estimate(item)
        print(f"  - {item}: 真实={true_freq}, 估计={estimate}")
    
    # 测试带衰减版本
    print("\n[衰减版本测试]")
    decay_sketch = CountMinSketchWithDecay(epsilon=0.01, delta=0.01, seed=42, decay_factor=0.5)
    
    for item in data_stream:
        decay_sketch.update(item)
    
    print(f"  - 衰减后总计数: {decay_sketch.total_count}")
    print(f"  - 衰减版本估计:")
    for item, true_freq in sorted(expected_freq.items(), key=lambda x: x[1], reverse=True):
        estimate = decay_sketch.estimate(item)
        print(f"  - {item}: 真实={true_freq}, 估计={estimate}")
    
    # 大规模测试
    print("\n[大规模数据流测试]")
    large_stream_size = 100000
    large_sketch = CountMinSketch(epsilon=0.001, delta=0.0001, seed=42)
    
    import random
    import string
    
    # 生成随机元素
    random.seed(42)
    large_stream = [f"item_{random.randint(0, 1000)}" for _ in range(large_stream_size)]
    
    print(f"  - 生成 {large_stream_size} 个随机元素")
    
    for item in large_stream:
        large_sketch.update(item)
    
    print(f"  - 更新完成，总计数: {large_sketch.total_count}")
    
    # 统计估计准确性
    large_freq = {}
    for item in large_stream:
        large_freq[item] = large_freq.get(item, 0) + 1
    
    errors = []
    for item, true_freq in large_freq.items():
        estimate = large_sketch.estimate(item)
        error = abs(estimate - true_freq) / true_freq if true_freq > 0 else 0
        errors.append(error)
    
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    
    print(f"  - 相对误差: 平均={avg_error*100:.2f}%, 最大={max_error*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("Count-Min Sketch 测试完成")
    print("=" * 60)

# -*- coding: utf-8 -*-
"""
算法实现：数据流算法 / ams_sketch

本文件实现 ams_sketch 相关的算法功能。
"""

import hashlib
import math
import random
from typing import List, Dict, Any, Optional, Tuple


class AMSSketch:
    """
    AMS Sketch 二阶矩估计器
    
    使用多个独立的随机变量来估计二阶矩。
    核心思想：对于频率向量f，其二阶矩 ||f||^2 = Σ f_i^2。
    通过对向量与随机哈希函数的点积来估计这个值。
    
    参数:
        epsilon: 精度参数，控制估计的相对误差
        seed: 随机种子，确保可重复性
    """
    
    def __init__(self, epsilon: float = 0.01, seed: int = 42):
        # epsilon: 精度参数，越小估计越精确
        self.epsilon = epsilon
        
        # m: 独立变量的数量，基于ε计算
        # m = O(1/epsilon^2)
        self.m = int(math.ceil(1 / (epsilon ** 2)))
        
        # seed: 随机种子
        self.seed = seed
        
        # random_generator: 随机数生成器
        self.random_generator = random.Random(seed)
        
        # X: 存储m个独立随机变量的数组
        # 每个X[i]是一个随机变量，用于估计二阶矩
        self.X = [0.0] * self.m
        
        # Z: 存储m个辅助随机变量的数组
        # 用于计算方差缩减
        self.Z = [0.0] * self.m
        
        # counter: 当前处理的元素计数
        self.counter = 0
        
        # frequency_vector: 真实频率向量（仅用于测试）
        self.frequency_vector = {}
        
        # hash_functions: 哈希函数列表
        self.hash_funcs = self._generate_hash_functions()
        
        # hash_para_a: 哈希函数的参数a（随机系数）
        self.hash_para_a = [self.random_generator.randint(1, 10**9) for _ in range(self.m)]
        
        # hash_para_b: 哈希函数的参数b（随机偏移）
        self.hash_para_b = [self.random_generator.randint(0, 10**9) for _ in range(self.m)]
        
        # hash_prime: 哈希函数的模数
        self.hash_prime = 2**61 - 1  # 一个大的质数
    
    def _generate_hash_functions(self) -> List[callable]:
        """
        生成m个独立的哈希函数
        
        每个哈希函数将元素映射到{-1, +1}或{0, 1}。
        这里使用4-stable分布生成随机哈希函数。
        
        返回:
            List[callable]: 哈希函数列表
        """
        # hash_funcs: 哈希函数列表
        hash_funcs = []
        
        for i in range(self.m):
            # 选择哈希类型：1表示4-stable，2表示简单的符号哈希
            hash_type = i % 2
            
            if hash_type == 0:
                # stable_hash: 使用高斯随机系数的哈希函数
                # h(x) = sign(a * x + b)，其中a服从高斯分布
                gaussian_coeff = self.random_generator.gauss(0, 1)
                
                def stable_hash(x, coeff=gaussian_coeff, p=self.hash_prime):
                    """4-stable分布哈希函数"""
                    # hash_val: 将x转换为哈希值
                    hash_val = hash(x) % p
                    # 计算带高斯系数的线性组合
                    raw_val = coeff * hash_val
                    # 返回符号
                    return 1 if raw_val >= 0 else -1
                
                hash_funcs.append(stable_hash)
            else:
                # simple_hash: 简单的伪随机哈希
                def simple_hash(x, a=self.hash_para_a[i], b=self.hash_para_b[i]):
                    """简单的模哈希函数"""
                    hash_val = hash(x)
                    return ((a * hash_val + b) % self.hash_prime) % 2 * 2 - 1
                
                hash_funcs.append(simple_hash)
        
        return hash_funcs
    
    def _compute_hash_value(self, item: Any, i: int) -> int:
        """
        计算元素在第i个哈希函数下的值
        
        参数:
            item: 要哈希的元素
            i: 哈希函数的索引
        
        返回:
            int: -1或+1
        """
        return self.hash_funcs[i](item)
    
    def update(self, item: Any, count: int = 1) -> None:
        """
        更新某个元素的频率
        
        对每个随机变量X[i]，加上该元素对应的哈希值乘以count。
        时间复杂度: O(m) = O(1/ε^2)
        
        参数:
            item: 要更新的元素
            count: 增加的计数，默认为1
        """
        # item_str: 元素转换为字符串
        item_str = str(item)
        
        # 更新频率向量（仅用于验证）
        self.frequency_vector[item_str] = self.frequency_vector.get(item_str, 0) + count
        
        # 更新每个随机变量
        for i in range(self.m):
            # hash_val: 第i个哈希函数对该元素的哈希值（-1或+1）
            hash_val = self._compute_hash_value(item_str, i)
            
            # X[i]: 累加哈希值乘以计数
            self.X[i] += hash_val * count
        
        # counter: 更新处理计数
        self.counter += count
    
    def estimate_second_moment(self) -> float:
        """
        估计二阶矩
        
        使用存储的随机变量X计算二阶矩的估计值。
        公式: E[||X||^2] = m * ||f||^2
        
        返回:
            float: 二阶矩的估计值
        """
        # sum_squared: X[i]^2的累加和
        sum_squared = sum(x * x for x in self.X)
        
        # second_moment_estimate: 二阶矩估计
        # 除以m，然后乘以一个修正因子
        second_moment_estimate = sum_squared / self.m
        
        return second_moment_estimate
    
    def estimate_f0(self) -> float:
        """
        估计零阶矩（即元素总数）
        
        返回:
            float: 元素总数的估计
        """
        return sum(abs(x) for x in self.X) / self.m
    
    def estimate_change(self, other: 'AMSSketch') -> float:
        """
        估计两个数据流之间的变化（二阶矩差异）
        
        可以用于检测数据流中的显著变化。
        
        参数:
            other: 另一个AMSSketch
        
        返回:
            float: 变化的估计值
        """
        # 检查参数匹配
        if self.m != other.m:
            raise ValueError("Cannot compare AMSSketches with different parameters")
        
        # diff_squared_sum: (X[i] - Y[i])^2的累加和
        diff_squared_sum = sum((self.X[i] - other.X[i]) ** 2 for i in range(self.m))
        
        # change_estimate: 变化估计
        change_estimate = diff_squared_sum / self.m
        
        return change_estimate
    
    def get_frequency(self, item: Any) -> int:
        """
        获取某个元素的真实频率（仅用于测试）
        
        参数:
            item: 要查询的元素
        
        返回:
            int: 真实频率
        """
        return self.frequency_vector.get(str(item), 0)
    
    def reset(self) -> None:
        """
        重置所有随机变量
        """
        # X: 重置为全零
        self.X = [0.0] * self.m
        
        # frequency_vector: 清空
        self.frequency_vector = {}
        
        # counter: 重置为0
        self.counter = 0
    
    def get_memory_usage(self) -> int:
        """
        获取内存使用量（字节）
        
        返回:
            int: 内存使用量估计
        """
        # 每个浮点数约8字节
        float_size = 8
        
        # total_size: 总大小
        total_size = self.m * float_size * 2  # X和Z数组
        
        return total_size
    
    def __repr__(self) -> str:
        """返回AMS Sketch的字符串表示"""
        return f"AMSSketch(m={self.m}, counter={self.counter})"


class AMSSketchWithVarianceReduction(AMSSketch):
    """
    带方差缩减的AMS Sketch
    
    使用Z变量进行方差缩减，提高估计精度。
    Z变量与X变量负相关，可以减少估计的方差。
    """
    
    def __init__(self, epsilon: float = 0.01, seed: int = 42):
        # 调用父类构造函数
        super().__init__(epsilon, seed)
        
        # Z: 辅助随机变量数组，用于方差缩减
        self.Z = [0.0] * self.m
    
    def update(self, item: Any, count: int = 1) -> None:
        """
        更新元素（同时更新X和Z）
        
        参数:
            item: 要更新的元素
            count: 增加的计数
        """
        # item_str: 元素字符串
        item_str = str(item)
        
        # 更新频率向量
        self.frequency_vector[item_str] = self.frequency_vector.get(item_str, 0) + count
        
        # 更新每个随机变量对
        for i in range(self.m):
            # hash_val: 哈希值
            hash_val = self._compute_hash_value(item_str, i)
            
            # X[i]: 累加
            self.X[i] += hash_val * count
            
            # Z[i]: 使用不同的哈希函数（互补哈希）
            # 这里使用-X[i]作为简化的互补版本
            Z_hash = -hash_val
            self.Z[i] += Z_hash * count
        
        # counter: 更新计数
        self.counter += count
    
    def estimate_second_moment_reduced(self) -> float:
        """
        使用方差缩减估计二阶矩
        
        使用公式: E[(X - Z)^2] / 4 = ||f||^2
        
        返回:
            float: 二阶矩的估计值
        """
        # diff_squared_sum: (X[i] - Z[i])^2的累加和
        diff_squared_sum = sum((self.X[i] - self.Z[i]) ** 2 for i in range(self.m))
        
        # second_moment_estimate: 缩减后的估计
        second_moment_estimate = diff_squared_sum / (4 * self.m)
        
        return second_moment_estimate


class StreamSnapshot:
    """
    数据流快照管理器
    
    用于保存和恢复AMS Sketch的状态，
    方便比较不同时间窗口的数据流。
    """
    
    def __init__(self, epsilon: float = 0.01, seed: int = 42):
        # sketch: 关联的AMS Sketch
        self.sketch = AMSSketch(epsilon, seed)
        
        # snapshots: 保存的快照列表
        self.snapshots = []
    
    def save_snapshot(self) -> int:
        """
        保存当前状态为快照
        
        返回:
            int: 快照的索引
        """
        # state: 当前状态的深拷贝
        state = {
            'X': self.sketch.X.copy(),
            'frequency_vector': self.sketch.frequency_vector.copy(),
            'counter': self.sketch.counter
        }
        
        # snapshots: 添加新快照
        snapshot_id = len(self.snapshots)
        self.snapshots.append(state)
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: int) -> None:
        """
        恢复到指定快照的状态
        
        参数:
            snapshot_id: 快照索引
        """
        if snapshot_id >= len(self.snapshots):
            raise ValueError(f"Snapshot {snapshot_id} does not exist")
        
        # state: 获取快照状态
        state = self.snapshots[snapshot_id]
        
        # 恢复到快照
        self.sketch.X = state['X'].copy()
        self.sketch.frequency_vector = state['frequency_vector'].copy()
        self.sketch.counter = state['counter']
    
    def update(self, item: Any, count: int = 1) -> None:
        """更新当前sketch"""
        self.sketch.update(item, count)
    
    def estimate(self) -> float:
        """估计二阶矩"""
        return self.sketch.estimate_second_moment()
    
    def get_change_since(self, snapshot_id: int) -> float:
        """
        获取从指定快照以来的变化
        
        参数:
            snapshot_id: 快照索引
        
        返回:
            float: 变化估计值
        """
        if snapshot_id >= len(self.snapshots):
            raise ValueError(f"Snapshot {snapshot_id} does not exist")
        
        # current_X: 当前X值
        current_X = self.sketch.X.copy()
        
        # snapshot_X: 快照中的X值
        snapshot_X = self.snapshots[snapshot_id]['X']
        
        # 计算变化
        diff_squared_sum = sum(
            (current_X[i] - snapshot_X[i]) ** 2 
            for i in range(self.sketch.m)
        )
        
        return diff_squared_sum / self.sketch.m


class AMSKmeansEstimator:
    """
    基于AMS Sketch的K-means距离估计器
    
    使用AMS Sketch来估计数据流中点与聚类中心的距离平方和。
    """
    
    def __init__(self, k: int, epsilon: float = 0.01, seed: int = 42):
        # k: 聚类数量
        self.k = k
        
        # epsilon: 精度参数
        self.epsilon = epsilon
        
        # centers: 聚类中心列表
        self.centers = [[0.0] * 2 for _ in range(k)]  # 简化版本，假设2D数据
        
        # cluster_counts: 每个聚类的计数
        self.cluster_counts = [0] * k
        
        # sketch: AMS Sketch用于频率估计
        self.sketch = AMSSketch(epsilon, seed)
        
        # dimension: 数据维度
        self.dimension = 2
    
    def update_point(self, point: List[float], cluster_id: int) -> None:
        """
        更新一个数据点
        
        参数:
            point: 数据点坐标列表
            cluster_id: 分配的聚类ID
        """
        # 更新聚类计数
        self.cluster_counts[cluster_id] += 1
        
        # 更新聚类中心（简化版本）
        center = self.centers[cluster_id]
        count = self.cluster_counts[cluster_id]
        
        for d in range(self.dimension):
            # incremental_update: 增量更新中心
            center[d] = center[d] + (point[d] - center[d]) / count
        
        # 更新sketch
        self.sketch.update(f"cluster_{cluster_id}")
    
    def estimate_cost(self) -> float:
        """
        估计K-means目标函数值
        
        公式: Σ Σ ||point - center||^2
        
        返回:
            float: 成本估计值
        """
        # 使用sketch的二阶矩估计
        second_moment = self.sketch.estimate_second_moment()
        
        # 简化的成本估计
        # 实际实现需要更复杂的处理
        return second_moment


if __name__ == "__main__":
    print("=" * 60)
    print("AMS Sketch 测试")
    print("=" * 60)
    
    # 测试1: 基本功能
    print("\n[测试1] 基本功能测试")
    print("-" * 60)
    
    # 创建AMS Sketch
    # epsilon=0.1 表示10%的相对误差
    ams = AMSSketch(epsilon=0.1, seed=42)
    
    print(f"AMS Sketch 创建成功")
    print(f"  - m (随机变量数): {ams.m}")
    print(f"  - epsilon: {ams.epsilon}")
    
    # 数据流
    data_stream = ["A", "B", "A", "C", "A", "B", "A", "D", "A", "B"]
    
    print(f"\n数据流: {data_stream}")
    
    # 更新sketch
    for item in data_stream:
        ams.update(item)
    
    # 计算真实二阶矩
    freq = {}
    for item in data_stream:
        freq[item] = freq.get(item, 0) + 1
    
    true_second_moment = sum(f ** 2 for f in freq.values())
    
    print(f"\n真实频率分布:")
    for item, count in freq.items():
        print(f"  {item}: {count}")
    
    print(f"\n真实二阶矩: {true_second_moment}")
    
    # 估计二阶矩
    estimated_second_moment = ams.estimate_second_moment()
    error = abs(estimated_second_moment - true_second_moment) / true_second_moment
    
    print(f"估计二阶矩: {estimated_second_moment:.2f}")
    print(f"相对误差: {error * 100:.2f}%")
    
    # 测试2: 不同epsilon的影响
    print("\n[测试2] 不同epsilon的影响")
    print("-" * 60)
    
    epsilons = [0.5, 0.2, 0.1, 0.05, 0.01]
    
    # 生成大规模数据流
    import random
    random.seed(42)
    
    # large_stream: 大规模测试数据
    stream_size = 10000
    unique_elements = 100
    
    large_stream = [f"elem_{random.randint(0, unique_elements-1)}" for _ in range(stream_size)]
    
    # 计算真实二阶矩
    large_freq = {}
    for item in large_stream:
        large_freq[item] = large_freq.get(item, 0) + 1
    
    true_large_second_moment = sum(f ** 2 for f in large_freq.values())
    
    print(f"大规模测试: {stream_size} 个元素, {unique_elements} 个唯一值")
    print(f"真实二阶矩: {true_large_second_moment}")
    
    for eps in epsilons:
        test_ams = AMSSketch(epsilon=eps, seed=42)
        
        for item in large_stream:
            test_ams.update(item)
        
        estimate = test_ams.estimate_second_moment()
        error = abs(estimate - true_large_second_moment) / true_large_second_moment
        
        print(f"  epsilon={eps:.2f}: 估计={estimate:.2f}, 相对误差={error*100:.2f}%, m={test_ams.m}")
    
    # 测试3: 方差缩减版本
    print("\n[测试3] 方差缩减版本测试")
    print("-" * 60)
    
    reduced_ams = AMSSketchWithVarianceReduction(epsilon=0.1, seed=42)
    
    for item in data_stream:
        reduced_ams.update(item)
    
    reduced_estimate = reduced_ams.estimate_second_moment_reduced()
    
    print(f"原始AMS估计: {ams.estimate_second_moment():.2f}")
    print(f"方差缩减估计: {reduced_estimate:.2f}")
    print(f"真实二阶矩: {true_second_moment}")
    
    # 测试4: 快照功能
    print("\n[测试4] 快照功能测试")
    print("-" * 60)
    
    snapshot_manager = StreamSnapshot(epsilon=0.1, seed=42)
    
    # 第一个时间窗口
    window1 = ["A", "B", "A", "C", "A", "D", "A"]
    print(f"时间窗口1: {window1}")
    
    for item in window1:
        snapshot_manager.update(item)
    
    snapshot_id = snapshot_manager.save_snapshot()
    estimate1 = snapshot_manager.estimate()
    print(f"快照{snapshot_id}保存，估计二阶矩: {estimate1:.2f}")
    
    # 第二个时间窗口
    window2 = ["A", "B", "E", "A", "B", "F", "A", "G"]
    print(f"时间窗口2: {window2}")
    
    for item in window2:
        snapshot_manager.update(item)
    
    estimate2 = snapshot_manager.estimate()
    print(f"当前估计二阶矩: {estimate2:.2f}")
    
    # 计算变化
    change = snapshot_manager.get_change_since(snapshot_id)
    print(f"从快照{snapshot_id}以来的变化: {change:.2f}")
    
    # 测试5: 变化检测
    print("\n[测试5] 变化检测测试")
    print("-" * 60)
    
    sketch1 = AMSSketch(epsilon=0.05, seed=100)
    sketch2 = AMSSketch(epsilon=0.05, seed=100)
    
    # 两个不同的数据分布
    stream1 = [f"item_{i % 20}" for i in range(5000)]
    stream2 = [f"item_{i % 50}" for i in range(5000)]  # 不同的分布
    
    print(f"流1: 20个唯一元素")
    print(f"流2: 50个唯一元素")
    
    for item in stream1:
        sketch1.update(item)
    
    for item in stream2:
        sketch2.update(item)
    
    # 估计各自的二阶矩
    est1 = sketch1.estimate_second_moment()
    est2 = sketch2.estimate_second_moment()
    
    # 计算变化
    change_estimate = sketch1.estimate_change(sketch2)
    
    print(f"流1二阶矩估计: {est1:.2f}")
    print(f"流2二阶矩估计: {est2:.2f}")
    print(f"两流之间的变化估计: {change_estimate:.2f}")
    
    # 测试6: 频率估计
    print("\n[测试6] 频率估计测试")
    print("-" * 60)
    
    test_stream = ["X", "Y", "X", "Z", "X", "Y", "X", "X"]
    
    freq_ams = AMSSketch(epsilon=0.1, seed=42)
    
    for item in test_stream:
        freq_ams.update(item)
    
    print(f"测试数据流: {test_stream}")
    print(f"\n元素频率:")
    
    # 计算真实频率
    true_freq = {}
    for item in test_stream:
        true_freq[item] = true_freq.get(item, 0) + 1
    
    for item in set(test_stream):
        true = true_freq[item]
        print(f"  {item}: 真实={true}")
    
    # 测试7: 大规模准确性测试
    print("\n[测试7] 大规模准确性测试")
    print("-" * 60)
    
    random.seed(12345)
    
    sizes = [10000, 50000, 100000]
    
    for size in sizes:
        test_stream = [f"elem_{random.randint(0, 1000)}" for _ in range(size)]
        
        # 计算真实二阶矩
        freq_dict = {}
        for item in test_stream:
            freq_dict[item] = freq_dict.get(item, 0) + 1
        
        true_moment = sum(f ** 2 for f in freq_dict.values())
        
        # 使用不同的epsilon测试
        for eps in [0.1, 0.05, 0.01]:
            test_ams = AMSSketch(epsilon=eps, seed=42)
            
            for item in test_stream:
                test_ams.update(item)
            
            estimated = test_ams.estimate_second_moment()
            error = abs(estimated - true_moment) / true_moment
            
            print(f"规模={size:6d}, eps={eps:.2f}: 真实={true_moment:12.0f}, 估计={estimated:12.2f}, 误差={error*100:5.2f}%")
    
    print("\n" + "=" * 60)
    print("AMS Sketch 测试完成")
    print("=" * 60)

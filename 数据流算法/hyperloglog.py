# -*- coding: utf-8 -*-
"""
算法实现：数据流算法 / hyperloglog

本文件实现 hyperloglog 相关的算法功能。
"""

import hashlib
import math
from typing import List, Dict, Any


class HyperLogLog:
    """
    HyperLogLog 基数估计器
    
    使用多个桶来记录每个元素哈希值中前导零的最大数量。
    基数估计基于观察到的最大前导零数量。
    
    参数:
        error_rate: 期望的相对误差率，默认0.01表示1%误差
        seed: 随机种子，确保哈希函数的可重复性
    """
    
    def __init__(self, error_rate: float = 0.01, seed: int = 42):
        # error_rate: 相对误差率，范围(0, 1)
        self.error_rate = error_rate
        
        # m: 桶的数量，基于误差率计算
        # m = 1.04 / error_rate^2
        self.m = math.ceil(1.04 / (error_rate ** 2))
        
        # alpha: 修正因子，用于提高估计精度
        self.alpha = self._compute_alpha()
        
        # registers: 桶寄存器数组，记录每个桶的最大前导零数+1
        self.registers = [0] * self.m
        
        # seed: 随机种子
        self.seed = seed
        
        # count: 已添加元素总数
        self.count = 0
        
        # hash_bits: 哈希值的位数
        self.hash_bits = 64
        
        # p: 用于从哈希值中提取桶索引的位数
        self.p = int(math.log2(self.m))
    
    def _compute_alpha(self) -> float:
        """
        计算HyperLogLog的修正因子alpha
        
        alpha用于修正由于均匀分布假设带来的偏差。
        对于不同的桶数量m，alpha有不同的理论值。
        
        返回:
            float: 修正因子alpha的值
        """
        # m: 桶的数量
        m = self.m
        
        if m == 16:
            # small_m_case: 小桶数量的特殊值
            return 0.673
        elif m == 32:
            return 0.697
        elif m == 64:
            return 0.709
        else:
            # large_m_formula: 大桶数量的通用公式
            # alpha = (m * (3 * log(2) - 1)) / (4 * (m - 1))
            # 这是一个近似公式，适用于较大的m
            return 0.7213 / (1 + 1.079 / m)
    
    def _hash(self, item: Any) -> int:
        """
        计算元素的哈希值
        
        使用SHA-256哈希函数，将元素转换为整数。
        使用种子进行加盐处理。
        
        参数:
            item: 要哈希的元素
        
        返回:
            int: 64位哈希值
        """
        # item_str: 元素转换为字符串
        item_str = str(item)
        
        # combined: 添加种子后的字符串
        combined = f"{self.seed}_{item_str}"
        
        # hash_obj: SHA-256哈希对象
        hash_obj = hashlib.sha256(combined.encode())
        
        # hash_hex: 哈希值的十六进制表示
        hash_hex = hash_obj.hexdigest()
        
        # 返回64位整数（取前16字节）
        return int(hash_hex[:16], 16)
    
    def _get_bucket_and_rank(self, hash_value: int) -> tuple:
        """
        从哈希值中提取桶索引和秩（前导零数量+1）
        
        将哈希值分为两部分：
        - 高位用于确定桶索引
        - 低位用于计算前导零数量
        
        参数:
            hash_value: 哈希值
        
        返回:
            tuple: (桶索引, 秩)
        """
        #桶索引：从哈希值的高p位提取
        # bucket: 使用位移和掩码提取桶索引
        bucket = hash_value >> (self.hash_bits - self.p)
        
        # 秩计算：从哈希值的剩余位计算前导零数量+1
        # mask: 用于提取低位的掩码 (2^p - 1)
        mask = (1 << self.p) - 1
        
        # low_bits: 哈希值的低p位
        low_bits = hash_value & mask
        
        # remaining_bits: 剩余用于计算前导零的位数
        remaining_bits = self.hash_bits - self.p
        
        # 如果低位全为0，需要特殊处理
        if low_bits == 0 and hash_value == 0:
            # zero_hash: 全零哈希值的情况
            rank = remaining_bits + 1
        else:
            # 计算前导零数量
            # 使用位移操作找到第一个1的位置
            # rank: 前导零数量加1（0个前导零时rank=1）
            rank = 1
            
            # 检查剩余位中的前导零
            temp = low_bits
            while temp > 0 and rank <= remaining_bits:
                if temp & 1:
                    break
                rank += 1
                temp >>= 1
            
            # 如果低p位全为0，检查剩余的高位
            if rank == 1 and low_bits == 0:
                # high_bits: 哈希值的高位部分
                high_val = hash_value >> self.p
                while high_val > 0 and rank <= remaining_bits:
                    if high_val & 1:
                        break
                    rank += 1
                    high_val >>= 1
        
        # 确保rank不会超过remaining_bits + 1
        rank = min(rank, remaining_bits + 1)
        
        return bucket, rank
    
    def add(self, item: Any) -> None:
        """
        添加一个元素到HyperLogLog
        
        计算元素的哈希值，更新对应桶的寄存器。
        时间复杂度: O(1)
        
        参数:
            item: 要添加的元素
        """
        # hash_val: 元素的哈希值
        hash_val = self._hash(item)
        
        # bucket: 桶索引
        # rank: 秩（最大前导零数+1）
        bucket, rank = self._get_bucket_and_rank(hash_val)
        
        # 更新桶的寄存器：只保留更大的值
        if rank > self.registers[bucket]:
            self.registers[bucket] = rank
        
        # count: 更新元素计数
        self.count += 1
    
    def estimate(self) -> float:
        """
        估计当前集合的基数（唯一元素数量）
        
        使用调和平均数公式计算估计值。
        时间复杂度: O(m)
        
        返回:
            float: 基数估计值
        """
        # sum_inv: 2^(-register[i])的累加和
        sum_inv = 0.0
        
        for i in range(self.m):
            # inv_power: 2的-register[i]次方的倒数
            inv_power = 1.0 / (1 << self.registers[i])
            sum_inv += inv_power
        
        # estimate_raw: 原始估计值
        # E = alpha * m^2 / sum(2^(-register[i]))
        estimate_raw = self.alpha * self.m * self.m / sum_inv
        
        # 小基数修正：当估计值小于2.5*m时使用线性计数
        if estimate_raw <= 2.5 * self.m:
            # zero_registers: 空桶的数量
            zero_registers = self.registers.count(0)
            
            if zero_registers > 0:
                # small_raw_estimate: 基于空桶的估计
                # V = m - number of empty registers
                # small_estimate = m * log(m / V)
                v = self.m - zero_registers
                if v == 0:
                    return 0
                estimate_raw = self.m * math.log(self.m / v)
        
        return estimate_raw
    
    def merge(self, other: 'HyperLogLog') -> None:
        """
        合并另一个HyperLogLog到当前结构
        
        对于每个桶，取两个sketch中更大的寄存器值。
        两个HyperLogLog必须具有相同的error_rate。
        
        参数:
            other: 要合并的另一个HyperLogLog
        
        异常:
            ValueError: 当参数不匹配时抛出
        """
        # 参数检查
        if self.m != other.m:
            raise ValueError("Cannot merge HyperLogLogs with different sizes")
        
        # 合并寄存器：取每个位置的最大值
        for i in range(self.m):
            if other.registers[i] > self.registers[i]:
                self.registers[i] = other.registers[i]
        
        # count: 合并计数（不准确，仅供参考）
        self.count += other.count
    
    def reset(self) -> None:
        """
        重置所有寄存器为空状态
        """
        # registers: 全部重置为0
        self.registers = [0] * self.m
        
        # count: 重置为0
        self.count = 0
    
    def get_memory_usage(self) -> int:
        """
        获取当前内存使用量估计（字节）
        
        返回:
            int: 估计的内存使用量
        """
        # 每个寄存器使用一个字节（存储0-64的值）
        register_size = 1
        
        # total_size: 总内存使用
        total_size = self.m * register_size
        
        return total_size
    
    def get_register_distribution(self) -> Dict[int, int]:
        """
        获取寄存器的值分布
        
        统计每个秩值对应的桶数量。
        
        返回:
            Dict[int, int]: 键是秩值，值是该秩的桶数量
        """
        # dist: 分布字典
        dist = {}
        
        for reg_val in self.registers:
            dist[reg_val] = dist.get(reg_val, 0) + 1
        
        return dist
    
    def __repr__(self) -> str:
        """返回HyperLogLog的字符串表示"""
        return f"HyperLogLog(m={self.m}, count={self.count}, estimate={self.estimate():.2f})"


class HyperLogLogPlus(HyperLogLog):
    """
    HyperLogLog++ 算法实现
    
    HyperLogLog的改进版本，具有更好的小基数估计精度。
    主要改进：
    1. 使用64位哈希而非32位，支持更大的基数估计
    2. 使用稀疏列表存储来减少小基数时的内存使用
    3. 使用更好的修正公式
    
    参数:
        error_rate: 相对误差率
        seed: 随机种子
        sparse_threshold: 稀疏模式切换阈值
    """
    
    def __init__(self, error_rate: float = 0.01, seed: int = 42, sparse_threshold: int = 10000):
        # 调用父类构造函数
        super().__init__(error_rate, seed)
        
        # hash_bits: 扩展到64位
        self.hash_bits = 64
        
        # sparse_threshold: 稀疏模式阈值
        # 当count < sparse_threshold时使用稀疏列表存储
        self.sparse_threshold = sparse_threshold
        
        # sparse_list: 稀疏列表，用于存储非零寄存器的更新
        self.sparse_list = set()
        
        # use_sparse: 是否使用稀疏模式
        self.use_sparse = True
        
        # register_version: 用于追踪稀疏列表转换为寄存器的版本
        self.register_version = 0
    
    def add(self, item: Any) -> None:
        """
        添加元素（支持稀疏模式）
        
        在稀疏模式下，将更新记录到稀疏列表中。
        当稀疏列表超过阈值时，合并到寄存器数组。
        
        参数:
            item: 要添加的元素
        """
        # hash_val: 元素的哈希值
        hash_val = self._hash(item)
        
        # bucket: 桶索引
        # rank: 秩
        bucket, rank = self._get_bucket_and_rank(hash_val)
        
        if self.use_sparse:
            # sparse_key: 稀疏列表中的键（桶索引）
            sparse_key = (bucket, rank)
            self.sparse_list.add(sparse_key)
            
            # count: 更新元素计数
            self.count += 1
            
            # 检查是否需要转换为密集模式
            if len(self.sparse_list) > self.sparse_threshold:
                self._convert_to_dense()
        else:
            # 密集模式：直接更新寄存器
            if rank > self.registers[bucket]:
                self.registers[bucket] = rank
            self.count += 1
    
    def _convert_to_dense(self) -> None:
        """
        将稀疏列表转换为密集寄存器数组
        
        遍历稀疏列表，对每个桶保留最大的秩值。
        """
        # 清空寄存器
        self.registers = [0] * self.m
        
        # 合并稀疏列表到寄存器
        for bucket, rank in self.sparse_list:
            if rank > self.registers[bucket]:
                self.registers[bucket] = rank
        
        # 切换到密集模式
        self.use_sparse = False
        self.sparse_list = set()
        self.register_version += 1
    
    def estimate(self) -> float:
        """
        估计基数（HyperLogLog++改进版本）
        
        使用改进的修正公式，特别是对于小基数。
        
        返回:
            float: 基数估计值
        """
        if self.use_sparse and len(self.sparse_list) > 0:
            # 稀疏模式下，先合并到临时寄存器
            temp_registers = [0] * self.m
            for bucket, rank in self.sparse_list:
                if rank > temp_registers[bucket]:
                    temp_registers[bucket] = rank
            
            # 使用临时寄存器计算
            sum_inv = sum(1.0 / (1 << reg) for reg in temp_registers)
            estimate_raw = self.alpha * self.m * self.m / sum_inv
        else:
            # 密集模式：使用父类的估计方法
            return super().estimate()
        
        # 小基数修正（HyperLogLog++使用不同的阈值）
        raw_bias_correction = 0
        if estimate_raw <= 5 * self.m:
            # register_zero_count: 零寄存器的数量
            if self.use_sparse:
                register_zero_count = self.m - len(set(bucket for bucket, _ in self.sparse_list))
            else:
                register_zero_count = self.registers.count(0)
            
            if register_zero_count > 0:
                # v: 非空寄存器的数量
                v = self.m - register_zero_count
                raw_bias_correction = self.m * math.log(self.m / v) - estimate_raw
        
        return max(0, estimate_raw + raw_bias_correction)
    
    def get_raw_estimate(self) -> float:
        """
        获取未修正的原始估计值
        
        返回:
            float: 原始估计值（未经偏置修正）
        """
        if self.use_sparse and len(self.sparse_list) > 0:
            temp_registers = [0] * self.m
            for bucket, rank in self.sparse_list:
                if rank > temp_registers[bucket]:
                    temp_registers[bucket] = rank
            
            sum_inv = sum(1.0 / (1 << reg) for reg in temp_registers)
            return self.alpha * self.m * self.m / sum_inv
        else:
            return super().estimate()


class HyperLogLogWithCounter(HyperLogLog):
    """
    带计数器的HyperLogLog变体
    
    在标准HyperLogLog基础上增加了对特定元素计数的追踪。
    可以快速查询某个元素是否已经见过，以及估计其出现次数。
    
    参数:
        error_rate: 相对误差率
        seed: 随机种子
        track_count_threshold: 开始追踪计数的元素阈值
    """
    
    def __init__(self, error_rate: float = 0.01, seed: int = 42, track_count_threshold: int = 100):
        # 调用父类构造函数
        super().__init__(error_rate, seed)
        
        # track_threshold: 开始追踪计数的阈值
        # 当唯一元素数超过此值时，开始追踪高频元素
        self.track_count_threshold = track_count_threshold
        
        # counter_dict: 元素计数器字典
        self.counter_dict = {}
        
        # use_counter: 是否启用计数器追踪
        self.use_counter = False
    
    def add(self, item: Any) -> None:
        """
        添加元素并更新计数器
        
        参数:
            item: 要添加的元素
        """
        # 调用父类的add方法
        super().add(item)
        
        # 如果启用计数器，更新计数
        if self.use_counter:
            self.counter_dict[item] = self.counter_dict.get(item, 0) + 1
    
    def _should_track(self) -> bool:
        """
        判断是否应该开始追踪计数器
        
        当估计的基数超过阈值时启用追踪。
        
        返回:
            bool: 是否应该追踪
        """
        # estimated_unique: 当前估计的唯一元素数
        estimated_unique = self.estimate()
        
        return estimated_unique > self.track_count_threshold
    
    def get_count(self, item: Any) -> int:
        """
        获取某个元素的估计出现次数
        
        注意：这只是一个非常粗略的估计，
        主要适用于高频元素。
        
        参数:
            item: 要查询的元素
        
        返回:
            int: 估计的出现次数
        """
        # 检查是否在追踪字典中
        if item in self.counter_dict:
            return self.counter_dict[item]
        
        # 否则返回1（表示该元素存在但频率低）
        return 0


if __name__ == "__main__":
    print("=" * 60)
    print("HyperLogLog 测试")
    print("=" * 60)
    
    # 创建HyperLogLog实例
    # error_rate=0.01 表示1%相对误差
    hll = HyperLogLog(error_rate=0.01, seed=42)
    
    print(f"\n[初始化] HyperLogLog 创建成功")
    print(f"  - 桶数量 (m): {hll.m}")
    print(f"  - 修正因子 (alpha): {hll.alpha:.6f}")
    print(f"  - 内存使用: {hll.get_memory_usage()} bytes")
    
    # 测试1: 基本功能测试
    print("\n[测试1] 基本功能测试")
    print("-" * 60)
    
    # 添加元素
    test_elements = ["item_1", "item_2", "item_3", "item_1", "item_2", "item_1"]
    
    print(f"添加元素: {test_elements}")
    for item in test_elements:
        hll.add(item)
    
    # 估计基数
    unique_count = hll.estimate()
    print(f"真实唯一元素数: {len(set(test_elements))}")
    print(f"估计的唯一元素数: {unique_count:.2f}")
    print(f"相对误差: {abs(unique_count - len(set(test_elements))) / len(set(test_elements)) * 100:.2f}%")
    
    # 测试2: 大规模数据流测试
    print("\n[测试2] 大规模数据流测试")
    print("-" * 60)
    
    import random
    
    # 设置随机种子
    random.seed(42)
    
    # 创建新的HyperLogLog
    hll_large = HyperLogLog(error_rate=0.01, seed=42)
    
    # 模拟数据流参数
    total_elements = 1000000  # 总元素数
    unique_elements = 50000   # 唯一元素数
    
    print(f"总元素数: {total_elements}")
    print(f"唯一元素数: {unique_elements}")
    
    # 生成数据流
    data_stream = [f"element_{random.randint(0, unique_elements-1)}" for _ in range(total_elements)]
    
    # 更新HyperLogLog
    print("开始添加元素...")
    for i, item in enumerate(data_stream):
        hll_large.add(item)
        if (i + 1) % 200000 == 0:
            print(f"  已添加 {i+1} 个元素，当前估计基数: {hll_large.estimate():.2f}")
    
    # 最终估计
    final_estimate = hll_large.estimate()
    actual_unique = len(set(data_stream))
    error_pct = abs(final_estimate - actual_unique) / actual_unique * 100
    
    print(f"\n真实唯一元素数: {actual_unique}")
    print(f"估计的唯一元素数: {final_estimate:.2f}")
    print(f"相对误差: {error_pct:.2f}%")
    
    # 测试3: 寄存器分布
    print("\n[测试3] 寄存器分布")
    print("-" * 60)
    
    dist = hll_large.get_register_distribution()
    print(f"寄存器分布（前10个秩值）:")
    sorted_ranks = sorted(dist.keys())
    for rank in sorted_ranks[:10]:
        count = dist[rank]
        bar = '*' * (count // 10)
        print(f"  秩 {rank}: {count:4d} 个桶 {bar}")
    
    # 测试4: 合并操作
    print("\n[测试4] 合并操作测试")
    print("-" * 60)
    
    hll1 = HyperLogLog(error_rate=0.01, seed=100)
    hll2 = HyperLogLog(error_rate=0.01, seed=200)
    
    # 分别添加不同的元素
    elements1 = [f"user_{i}" for i in range(10000)]
    elements2 = [f"user_{i}" for i in range(5000, 15000)]
    
    print(f"第一个HyperLogLog添加 {len(elements1)} 个元素")
    print(f"第二个HyperLogLog添加 {len(elements2)} 个元素")
    
    for item in elements1:
        hll1.add(item)
    
    for item in elements2:
        hll2.add(item)
    
    estimate1 = hll1.estimate()
    estimate2 = hll2.estimate()
    
    print(f"第一个估计基数: {estimate1:.2f}")
    print(f"第二个估计基数: {estimate2:.2f}")
    
    # 合并
    hll1.merge(hll2)
    merged_estimate = hll1.estimate()
    
    # 真实唯一数
    true_unique = len(set(elements1) | set(elements2))
    
    print(f"合并后估计基数: {merged_estimate:.2f}")
    print(f"真实唯一元素数: {true_unique}")
    print(f"合并相对误差: {abs(merged_estimate - true_unique) / true_unique * 100:.2f}%")
    
    # 测试5: HyperLogLog++
    print("\n[测试5] HyperLogLog++ 测试")
    print("-" * 60)
    
    hll_plus = HyperLogLogPlus(error_rate=0.01, seed=42)
    
    # 添加少量元素测试小基数估计
    small_elements = [f"item_{i}" for i in range(100)]
    
    for item in small_elements:
        hll_plus.add(item)
    
    small_estimate = hll_plus.estimate()
    print(f"添加100个唯一元素")
    print(f"真实唯一元素数: 100")
    print(f"HyperLogLog++ 估计: {small_estimate:.2f}")
    
    # 测试6: 重置操作
    print("\n[测试6] 重置操作测试")
    print("-" * 60)
    
    hll_test = HyperLogLog(error_rate=0.01, seed=42)
    for i in range(10000):
        hll_test.add(f"item_{i}")
    
    print(f"重置前估计: {hll_test.estimate():.2f}")
    print(f"重置前计数: {hll_test.count}")
    
    hll_test.reset()
    
    print(f"重置后估计: {hll_test.estimate():.2f}")
    print(f"重置后计数: {hll_test.count}")
    
    # 测试7: 与set对比
    print("\n[测试7] 与Python set对比")
    print("-" * 60)
    
    sizes = [1000, 10000, 50000, 100000]
    error_rates = []
    
    for size in sizes:
        test_hll = HyperLogLog(error_rate=0.01, seed=42)
        random.seed(123)
        
        stream = [f"elem_{random.randint(0, size*2)}" for _ in range(size)]
        
        for item in stream:
            test_hll.add(item)
        
        estimate = test_hll.estimate()
        actual = len(set(stream))
        error = abs(estimate - actual) / actual
        error_rates.append(error)
        
        print(f"规模={size:6d}: 真实={actual:6d}, 估计={estimate:8.2f}, 误差={error*100:5.2f}%")
    
    print(f"\n平均相对误差: {sum(error_rates)/len(error_rates)*100:.2f}%")
    print(f"最大相对误差: {max(error_rates)*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("HyperLogLog 测试完成")
    print("=" * 60)

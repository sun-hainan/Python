"""
HyperLogLog 算法模块

一种用于基数估计（Cardinality Estimation）的概率算法，
能够在极小的空间内（O(log log n) bits）估计大规模数据集的
不同元素数量。

核心思想：
- 使用哈希函数将元素映射到二进制表示
- 观察哈希值中连续0的最大数量R
- 2^R 与不同元素的数量成正比
- 使用调和平均减少异常值影响

空间效率：
- 传统计数需要 O(n) 空间
- HyperLogLog 仅需 O(1/ε²) 空间，标准误差约 1.04/√m

参考文献：Flajolet, P., et al. (2007).
"HyperLogLog: The analysis of a near-optimal cardinality estimation algorithm."
"""

import hashlib
import math
from typing import List


class HyperLogLog:
    """
    HyperLogLog 基数估计器

    通过分桶和调和平均实现高效的基数估计。
    适合用于大规模数据场景，如UV统计、日活用户计数等。

    Attributes:
        register_size: 2^p，寄存器的数量（通常取2^p = 2^10到2^16）
        p: 位数，决定寄存器数量
        registers: 存储每个桶的最大零计数
        m: 寄存器数量 = 2^p
        alpha: 偏差校正因子
    """

    # α_m 的预计算值，用于不同寄存器数量的偏差校正
    ALPHA_M = {
        16: 0.673,
        32: 0.697,
        64: 0.709,
        128: 0.715,
        256: 0.718,
        512: 0.719,
        1024: 0.720,
        2048: 0.720,
        4096: 0.720,
    }

    def __init__(self, p: int = 10):
        """
        初始化HyperLogLog

        Args:
            p: 桶数量的指数，即 m = 2^p
                 p=10: m=1024, 标准误差 ≈ 3.3%
                 p=12: m=4096, 标准误差 ≈ 1.6%
                 p=14: m=16384, 标准误差 ≈ 0.8%
        """
        if p < 4 or p > 16:
            raise ValueError("p must be between 4 and 16")

        self.p: int = p
        self.m: int = 2 ** p  # 寄存器数量
        self.registers: List[int] = [0] * self.m  # 每个桶的最大零计数

        # 获取偏差校正因子，如果没有则使用近似公式
        self.alpha: float = self.ALPHA_M.get(
            self.m,
            0.7213 / (1 + 1.079 / self.m)  # 通用近似公式
        )

    def _hash(self, element: str) -> int:
        """
        计算元素的64位哈希值

        使用MD5哈希的前8字节转成大整数

        Args:
            element: 要哈希的元素

        Returns:
            64位哈希整数
        """
        hash_bytes: bytes = hashlib.md5(element.encode()).digest()
        return int.from_bytes(hash_bytes[:8], byteorder='big')

    def _rho(self, hashed_value: int) -> int:
        """
        计算哈希值二进制表示中前导零的数量 + 1

        这是HyperLogLog的核心：前导零数量R反映了
        元素被哈希到"小值区间"的程度。

        Args:
            hashed_value: 哈希后的整数值（64位）

        Returns:
            前导零数量 + 1，范围[1, 65]
        """
        # 64位哈希，最多65种可能值
        # 使用内置函数计算前导零
        return (hashed_value.bit_length() - 1) ^ 63 + 1 if hashed_value > 0 else 65

    def add(self, element: str) -> None:
        """
        向数据流中添加一个元素

        Args:
            element: 元素标识（字符串）
        """
        # 计算64位哈希
        hashed: int = self._hash(element)

        # 提取前p位作为桶索引
        bucket_index: int = hashed >> (64 - self.p)

        # 提取剩余位，计算前导零数量
        remaining_bits: int = hashed & ((1 << (64 - self.p)) - 1)
        zero_count: int = self._rho(remaining_bits)

        # 更新寄存器：取最大值
        if zero_count > self.registers[bucket_index]:
            self.registers[bucket_index] = zero_count

    def estimate(self) -> float:
        """
        估计数据流中不同元素的数量

        使用调和平均公式：
        E ≈ α_m * m² * (1 / Σ 2^{-R_i})

        Returns:
            估计的不同元素基数
        """
        # 计算调和平均的倒数
        inverse_sum: float = 0.0
        for register in self.registers:
            inverse_sum += 2 ** (-register)

        # 如果调和和为0，返回0
        if inverse_sum == 0:
            return 0.0

        # 应用估计公式
        raw_estimate: float = self.alpha * self.m * self.m / inverse_sum

        # 小基数校正（当基数远小于m时）
        if raw_estimate <= 2.5 * self.m:
            # 使用线性计数法
            zero_count: int = sum(1 for r in self.registers if r == 0)
            if zero_count > 0:
                return self.m * math.log(self.m / zero_count)

        # 大基数校正（当基数远大于m时）
        if raw_estimate > (1 << 61) / 30:
            return -(1 << 61) * math.log(1 - raw_estimate / ((1 << 61) / 30))

        return raw_estimate

    def merge(self, other: 'HyperLogLog') -> None:
        """
        合并另一个HyperLogLog实例

        用于分布式场景：多台机器分别统计后合并

        Args:
            other: 要合并的另一个HyperLogLog

        Raises:
            ValueError: 当两个实例的p值不同时
        """
        if self.p != other.p:
            raise ValueError("Cannot merge HyperLogLogs with different p values")

        for i in range(self.m):
            # 取各寄存器的最大值
            self.registers[i] = max(self.registers[i], other.registers[i])

    def get_register_stats(self) -> dict:
        """
        获取寄存器的统计信息

        Returns:
            包含寄存器统计数据的字典
        """
        nonzero_registers: List[int] = [r for r in self.registers if r > 0]
        return {
            "m": self.m,
            "p": self.p,
            "nonzero_count": len(nonzero_registers),
            "max_register": max(self.registers) if self.registers else 0,
            "min_register": min(r for r in self.registers if r > 0) if nonzero_registers else 0,
            "avg_register": sum(nonzero_registers) / len(nonzero_registers) if nonzero_registers else 0,
        }


# -------------------- 测试代码 --------------------
if __name__ == "__main__":
    print("=" * 60)
    print("HyperLogLog 基数估计测试")
    print("=" * 60)

    # 测试场景1：已知基数的精确测试
    print("\n【场景1】小规模精确测试")
    print("-" * 40)

    hll: HyperLogLog = HyperLogLog(p=10)  # m=1024

    # 生成10000个不同的字符串
    import random
    random.seed(42)

    unique_elements: List[str] = [f"element_{i}" for i in range(10000)]

    print(f"输入: 10000个唯一元素")
    print(f"真实基数: {len(set(unique_elements))}")

    for elem in unique_elements:
        hll.add(elem)

    estimated: float = hll.estimate()
    error: float = abs(estimated - 10000) / 10000 * 100

    print(f"估计基数: {estimated:.2f}")
    print(f"相对误差: {error:.2f}%")
    print(f"寄存器统计: {hll.get_register_stats()}")

    # 测试场景2：重复元素的场景
    print("\n【场景2】有大量重复元素的数据流")
    print("-" * 40)

    hll2: HyperLogLog = HyperLogLog(p=12)  # m=4096

    # 100个不同元素，每个平均出现100次
    stream_with_repeats: List[str] = []
    for i in range(100):
        stream_with_repeats.extend([f"user_{i}"] * 100)

    print(f"输入: 100种元素，每种出现100次，共{len(stream_with_repeats)}次")
    print(f"真实基数: 100")

    for elem in stream_with_repeats:
        hll2.add(elem)

    estimated2: float = hll2.estimate()
    error2: float = abs(estimated2 - 100) / 100 * 100

    print(f"估计基数: {estimated2:.2f}")
    print(f"相对误差: {error2:.2f}%")

    # 测试场景3：分布式合并
    print("\n【场景3】分布式合并测试")
    print("-" * 40)

    # 模拟3台机器分别统计
    hll_shards: List[HyperLogLog] = [HyperLogLog(p=10) for _ in range(3)]
    shard_elements: List[List[str]] = [
        [f"elem_{i}" for i in range(0, 5000)],
        [f"elem_{i}" for i in range(5000, 8000)],
        [f"elem_{i}" for i in range(5000, 10000)],
    ]

    for i, elements in enumerate(shard_elements):
        for elem in elements:
            hll_shards[i].add(elem)

    # 合并所有分片
    merged_hll: HyperLogLog = hll_shards[0]
    for i in range(1, len(hll_shards)):
        merged_hll.merge(hll_shards[i])

    print(f"3个分片分别统计后合并:")
    print(f"  分片1估计: {hll_shards[0].estimate():.2f} (5000个唯一)")
    print(f"  分片2估计: {hll_shards[1].estimate():.2f} (3000个唯一)")
    print(f"  分片3估计: {hll_shards[2].estimate():.2f} (5000个唯一)")
    print(f"  合并后估计: {merged_hll.estimate():.2f} (预期10000)")
    print(f"  真实基数: 10000")
    print(f"  相对误差: {abs(merged_hll.estimate() - 10000) / 10000 * 100:.2f}%")

    # 测试场景4：不同p值的精度对比
    print("\n【场景4】不同p值的精度对比")
    print("-" * 40)

    p_values: List[int] = [8, 10, 12, 14]
    true_cardinality: int = 50000
    test_elements: List[str] = [f"item_{i}" for i in range(true_cardinality)]

    print(f"真实基数: {true_cardinality}")
    print(f"\n{'p值':<8} {'m':<10} {'估计值':<15} {'误差%':<10}")
    print("-" * 43)

    for p in p_values:
        hll_test: HyperLogLog = HyperLogLog(p=p)
        for elem in test_elements:
            hll_test.add(elem)
        est: float = hll_test.estimate()
        err: float = abs(est - true_cardinality) / true_cardinality * 100
        print(f"{p:<8} {2**p:<10} {est:<15.2f} {err:<10.2f}")

    print("\n结论: p值越大，精度越高，但内存消耗也越大")
    print("      标准误差 ≈ 1.04 / √m = 1.04 / √(2^p)")

    print("\n测试完成 ✓")

"""
HyperLogLog
==========================================

【算法原理】
利用概率统计估计集合的基数（不同元素数）。
核心思想：如果前导0的最多出现k次，则基数约为2^k。

【时间复杂度】
- 添加元素: O(1)
- 估计基数: O(1)

【空间复杂度】O(1)（只需几个KB）

【应用场景】
- 大数据去重统计
- UV计数
- 数据库查询优化
- 实时流处理
"""

import math
import hashlib
import struct
from typing import List


class HyperLogLog:
    """
    HyperLogLog: 近似基数估计

    【核心思想】
    - 使用m个桶（寄存器）
    - 每个桶存储落入该桶的元素的最大前导零数
    - 利用调和平均减少异常值影响
    - 最终估计: cardinality ≈ 2^k * m * α

    【参数】
    - m: 桶数（通常2^p，p=10-16）
    - p: 位数（决定m=2^p）
    - α: 修正因子
    """

    # α_m values for different m
    ALPHA = {
        16: 0.673,
        32: 0.697,
        64: 0.709,
        128: 0.7203,
        256: 0.7293,
        512: 0.7345,
        1024: 0.7385,
        2048: 0.7410,
        4096: 0.7427,
    }

    def __init__(self, p: int = 10):
        """
        初始化HyperLogLog

        【参数】
        - p: 精度参数（默认10，m=1024桶）
          p越大，精度越高，空间越大
          p=10: m=1024, 标准误差≈1.6%
          p=12: m=4096, 标准误差≈0.8%
          p=14: m=16384, 标准误差≈0.4%
        """
        self.p = p
        self.m = 1 << p  # 2^p

        # α修正因子
        if self.m in self.ALPHA:
            self.alpha = self.ALPHA[self.m]
        else:
            # 近似公式: α = (m * 0.5) / (1 + 1.079/m)
            self.alpha = (0.5 * self.m) / (1 + 1.079 / self.m)

        # 寄存器数组，存储每个桶的最大前导零+1
        self.registers = [0] * self.m

    def _hash(self, item) -> int:
        """计算哈希值（64位）"""
        data = str(item).encode()
        return int(hashlib.sha256(data).hexdigest(), 16) % (1 << 64)

    def _get_bucket_and_leading_zeros(self, h: int) -> tuple:
        """
        获取桶索引和前导零数+1

        【原理】
        - 前p位用于桶索引
        - 剩余位用于计算前导零
        """
        bucket_idx = h & (self.m - 1)  # 前p位
        remaining = h >> self.p  # 剩余位

        # 计算前导零（从最高位开始）
        # 如果remaining是0，则返回64-p+1
        if remaining == 0:
            leading_zeros = 64 - self.p
        else:
            leading_zeros = (remaining & 0xFFFFFFFFFFFFFFFF).bit_length()
            # 反转位顺序
            remaining_rev = int(format(remaining, '064b')[::-1], 2)
            leading_zeros = (remaining & 0xFFFFFFFFFFFFFFFF).bit_length()

        # 实际前导零数+1（0表示全是0）
        rho = 1
        temp = remaining
        while temp > 0 and rho < 64 - self.p:
            rho += 1
            temp >>= 1

        return bucket_idx, rho

    def add(self, item) -> None:
        """添加一个元素"""
        h = self._hash(item)
        bucket, rho = self._get_bucket_and_leading_zeros(h)

        # 更新寄存器（取最大值）
        if rho > self.registers[bucket]:
            self.registers[bucket] = rho

    def add_batch(self, items: List) -> None:
        """批量添加元素"""
        for item in items:
            self.add(item)

    def _raw_estimate(self) -> float:
        """
        计算原始估计值

        【公式】
        E = α * m^2 / Σ(2^(-M[i]))

        其中M[i]是第i个寄存器的值
        """
        # 调和平均
        inverse_sum = 0.0
        for m_i in self.registers:
            inverse_sum += 2 ** (-m_i)

        # 估计
        estimate = self.alpha * self.m * self.m / inverse_sum
        return estimate

    def estimate(self) -> int:
        """
        返回基数估计

        【包含修正】
        - 小基数修正（0到5m/2之间）
        - 大基数修正（使用线性计数）
        """
        raw = self._raw_estimate()

        # 小基数修正
        if raw <= 2.5 * self.m:
            # 使用线性计数
            zeros = self.registers.count(0)
            if zeros == 0:
                return int(raw)
            else:
                return int(-self.m * math.log(zeros / self.m))

        # 大基数修正
        if raw > (1 << 32) * 30.0:
            return -1  # 超过范围

        return int(raw)

    def merge(self, other: 'HyperLogLog') -> 'HyperLogLog':
        """
        合并两个HyperLogLog（按元素取最大）

        【条件】p必须相同
        """
        if self.p != other.p:
            raise ValueError("无法合并不同精度的HyperLogLog")

        result = HyperLogLog(self.p)
        for i in range(self.m):
            result.registers[i] = max(self.registers[i], other.registers[i])
        return result


class HyperLogLogPlusPlus(HyperLogLog):
    """
    HyperLogLog++

    【改进】
    1. 使用稀疏存储（减少内存）
    2. 更好的偏差修正
    3. 更好的小基数处理
    """

    def __init__(self, p: int = 14):
        super().__init__(p)
        self.sparse = True
        self.sparse_registers = {}  # 只存储非零位置

    def add(self, item) -> None:
        """添加元素（使用稀疏存储）"""
        h = self._hash(item)
        bucket, rho = self._get_bucket_and_leading_zeros(h)

        if self.sparse:
            if bucket in self.sparse_registers:
                self.sparse_registers[bucket] = max(
                    self.sparse_registers[bucket], rho)
            else:
                self.sparse_registers[bucket] = rho

            # 如果稀疏存储太大，转为密集存储
            if len(self.sparse_registers) > self.m * 0.5:
                self._to_dense()
        else:
            if rho > self.registers[bucket]:
                self.registers[bucket] = rho

    def _to_dense(self) -> None:
        """从稀疏转为密集存储"""
        for bucket, rho in self.sparse_registers.items():
            if rho > self.registers[bucket]:
                self.registers[bucket] = rho
        self.sparse_registers = {}
        self.sparse = False

    def estimate(self) -> int:
        """估计基数（使用HyperLogLog++的改进）"""
        if self.sparse:
            for i in range(self.m):
                if i not in self.sparse_registers:
                    self.registers[i] = 0
                else:
                    self.registers[i] = self.sparse_registers[i]
            self.sparse = False
            self.sparse_registers = {}

        return super().estimate()


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("HyperLogLog - 测试")
    print("=" * 50)

    # 测试1：基本功能
    print("\n【测试1】基本功能")
    hll = HyperLogLog(p=10)  # 1024桶
    print(f"  桶数: {hll.m}")

    # 插入10000个不同元素
    for i in range(10000):
        hll.add(f"item_{i}")

    estimate = hll.estimate()
    print(f"  插入10000个元素")
    print(f"  估计基数: {estimate}")
    print(f"  相对误差: {abs(estimate - 10000)/10000:.2%}")

    # 测试2：重复插入
    print("\n【测试2】重复插入")
    hll2 = HyperLogLog(p=10)
    items = [f"item_{i % 1000}" for i in range(10000)]  # 只有1000个不同
    hll2.add_batch(items)

    estimate2 = hll2.estimate()
    print(f"  插入10000次但只有1000个不同")
    print(f"  估计基数: {estimate2}")
    print(f"  相对误差: {abs(estimate2 - 1000)/1000:.2%}")

    # 测试3：合并
    print("\n【测试3】合并")
    hll_a = HyperLogLog(p=10)
    hll_b = HyperLogLog(p=10)

    for i in range(5000):
        hll_a.add(f"set_a_{i}")
    for i in range(5000, 10000):
        hll_b.add(f"set_b_{i}")

    merged = hll_a.merge(hll_b)
    merged_estimate = merged.estimate()
    print(f"  合并两个各5000不同元素的HLL")
    print(f"  估计基数: {merged_estimate}")
    print(f"  相对误差: {abs(merged_estimate - 10000)/10000:.2%}")

    # 测试4：不同精度
    print("\n【测试4】不同精度对比")
    for p in [8, 10, 12, 14]:
        hll_p = HyperLogLog(p=p)
        for i in range(50000):
            hll_p.add(f"item_{i}")
        est = hll_p.estimate()
        print(f"  p={p} ({1<<p}桶): 估计={est}, 误差={abs(est-50000)/50000:.2%}")

    # 测试5：HyperLogLog++
    print("\n【测试5】HyperLogLog++")
    hllpp = HyperLogLogPlusPlus(p=14)
    for i in range(100000):
        hllpp.add(f"item_{i}")
    est_pp = hllpp.estimate()
    print(f"  插入100000个不同元素")
    print(f"  HLL++估计: {est_pp}")
    print(f"  相对误差: {abs(est_pp - 100000)/100000:.2%}")

    # 测试6：空间效率
    print("\n【测试6】空间效率")
    print(f"  HyperLogLog(p=10): {1<<10} 寄存器 = {1<<10} 字节")
    print(f"  HyperLogLog(p=14): {1<<14} 寄存器 = {1<<14} 字节")
    print(f"  相比存储100万ID: 节省99.9%+空间")

    print("\n" + "=" * 50)
    print("HyperLogLog测试完成！")
    print("=" * 50)

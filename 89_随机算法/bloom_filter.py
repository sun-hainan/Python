"""
布隆过滤器
==========================================

【算法原理】
使用k个哈希函数，将元素映射到位数组的k个位置。
查询时，检查所有k个位置是否都为1。

【特点】
- 可能误报（False Positive）：不存在的元素可能判断为存在
- 不会漏报（False Negative）：存在的元素一定判断为存在
- 空间效率高

【时间复杂度】O(k) 插入和查询

【应用场景】
- 网页爬虫去重
- 垃圾邮件过滤
- 缓存穿透防护
- 数据库快速查询
"""

import math
import hashlib
from typing import List, Set


class BloomFilter:
    """
    布隆过滤器

    【参数计算】
    - n: 预期插入元素数
    - p: 期望误报率
    - m: 位数组大小
    - k: 哈希函数个数

    【最优公式】
    - m = -n * ln(p) / (ln(2)^2)
    - k = m/n * ln(2)
    """

    def __init__(self, expected_elements: int = 1000,
                 false_positive_rate: float = 0.01):
        """
        初始化布隆过滤器

        【参数】
        - expected_elements: 预期插入元素数 n
        - false_positive_rate: 目标误报率 p
        """
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate

        # 计算最优参数
        self.size = self._get_size(expected_elements, false_positive_rate)
        self.num_hashes = self._get_num_hashes(self.size, expected_elements)

        # 位数组
        self.bit_array = [0] * self.size

    @staticmethod
    def _get_size(n: int, p: float) -> int:
        """
        计算位数组大小

        m = -n * ln(p) / (ln(2)^2)
        """
        m = -n * math.log(p) / (math.log(2) ** 2)
        return int(math.ceil(m))

    @staticmethod
    def _get_num_hashes(m: int, n: int) -> int:
        """
        计算哈希函数个数

        k = m/n * ln(2)
        """
        k = (m / n) * math.log(2)
        return int(math.ceil(k))

    def _hash(self, item, seed: int) -> int:
        """
        计算哈希值

        使用两个哈希函数模拟k个哈希
        h(i) = h1 + i * h2
        """
        # 两个基础哈希
        data = str(item).encode()
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)

        # 组合成k个哈希
        return (h1 + seed * h2) % self.size

    def add(self, item) -> None:
        """添加元素"""
        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            self.bit_array[pos] = 1

    def contains(self, item) -> bool:
        """检查元素是否存在（可能误报）"""
        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            if self.bit_array[pos] == 0:
                return False
        return True

    def __contains__(self, item) -> bool:
        return self.contains(item)

    def __add__(self, item) -> None:
        self.add(item)

    def get_false_positive_rate(self) -> float:
        """
        实际误报率估计

        P(FP) ≈ (1 - e^(-kn/m))^k
        """
        k = self.num_hashes
        n = self.expected_elements
        m = self.size
        return (1 - math.exp(-k * n / m)) ** k

    def union(self, other: 'BloomFilter') -> 'BloomFilter':
        """并集（OR操作）"""
        if self.size != other.size or self.num_hashes != other.num_hashes:
            raise ValueError("无法对不同参数的布隆过滤器做并集")

        result = BloomFilter(self.expected_elements, self.false_positive_rate)
        result.size = self.size
        result.num_hashes = self.num_hashes
        result.bit_array = [a | b for a, b in
                          zip(self.bit_array, other.bit_array)]
        return result

    def intersection(self, other: 'BloomFilter') -> 'BloomFilter':
        """交集（AND操作）"""
        if self.size != other.size or self.num_hashes != other.num_hashes:
            raise ValueError("无法对不同参数的布隆过滤器做交集")

        result = BloomFilter(self.expected_elements, self.false_positive_rate)
        result.size = self.size
        result.num_hashes = self.num_hashes
        result.bit_array = [a & b for a, b in
                          zip(self.bit_array, other.bit_array)]
        return result


class CountableBloomFilter:
    """
    可计数布隆过滤器

    【改进】每个位置存储计数器而非0/1
    支持删除操作
    """

    def __init__(self, expected_elements: int = 1000,
                 false_positive_rate: float = 0.01):
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate

        self.size = BloomFilter._get_size(expected_elements, false_positive_rate)
        self.num_hashes = BloomFilter._get_num_hashes(self.size, expected_elements)

        # 计数器数组
        self.counters = [0] * self.size

    def _hash(self, item, seed: int) -> int:
        data = str(item).encode()
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)
        return (h1 + seed * h2) % self.size

    def add(self, item) -> None:
        """添加元素（计数+1）"""
        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            self.counters[pos] += 1

    def remove(self, item) -> bool:
        """删除元素（计数-1）"""
        if not self.contains(item):
            return False

        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            if self.counters[pos] > 0:
                self.counters[pos] -= 1
        return True

    def contains(self, item) -> bool:
        """检查元素是否存在"""
        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            if self.counters[pos] == 0:
                return False
        return True

    def get_count(self, item) -> int:
        """获取元素计数（近似值）"""
        counts = []
        for seed in range(self.num_hashes):
            pos = self._hash(item, seed)
            counts.append(self.counters[pos])
        return min(counts)  # 取最小值（保守估计）


class ScalableBloomFilter:
    """
    可扩展布隆过滤器

    【改进】当负载过高时，添加新的子过滤器
    """

    def __init__(self, initial_size: int = 1000,
                 false_positive_rate: float = 0.01,
                 scale_factor: float = 2.0):
        """
        初始化可扩展布隆过滤器

        【参数】
        - initial_size: 初始子过滤器大小
        - false_positive_rate: 目标误报率
        - scale_factor: 扩展倍数
        """
        self.initial_size = initial_size
        self.false_positive_rate = false_positive_rate
        self.scale_factor = scale_factor

        # 当前的子过滤器
        self.filters = [BloomFilter(initial_size, false_positive_rate)]
        self.current_filter = 0

    def add(self, item) -> None:
        """添加元素"""
        # 尝试插入当前过滤器
        if not self.filters[self.current_filter].contains(item):
            # 如果当前过滤器已满或元素已存在，创建新过滤器
            if self.filters[self.current_filter].get_false_positive_rate() > \
               self.false_positive_rate * 0.5:
                self.filters.append(
                    BloomFilter(
                        int(self.filters[-1].size * self.scale_factor),
                        self.false_positive_rate
                    )
                )
                self.current_filter += 1

            self.filters[self.current_filter].add(item)

    def contains(self, item) -> bool:
        """检查所有子过滤器"""
        for f in self.filters:
            if f.contains(item):
                return True
        return False

    def __contains__(self, item) -> bool:
        return self.contains(item)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("布隆过滤器 - 测试")
    print("=" * 50)

    # 测试1：基本布隆过滤器
    print("\n【测试1】基本布隆过滤器")
    bf = BloomFilter(1000, 0.01)
    print(f"  位数组大小: {bf.size}")
    print(f"  哈希函数个数: {bf.num_hashes}")

    # 插入一些元素
    items = [f"item_{i}" for i in range(500)]
    for item in items:
        bf.add(item)

    # 检查存在的元素
    print(f"  查找 'item_100': {'item_100' in bf}")
    print(f"  查找 'item_499': {'item_499' in bf}")

    # 检查不存在的元素（误报）
    false_positives = sum(1 for i in range(500, 1000)
                        if f"item_{i}" in bf)
    print(f"  500个未插入元素中误报: {false_positives}")
    print(f"  实际误报率: {false_positives/500:.2%}")

    # 测试2：可计数布隆过滤器
    print("\n【测试2】可计数布隆过滤器")
    cbf = CountableBloomFilter(1000, 0.01)

    for item in ["apple", "banana", "apple", "cherry"]:
        cbf.add(item)

    print(f"  'apple'计数: {cbf.get_count('apple')}")
    print(f"  'banana'计数: {cbf.get_count('banana')}")

    cbf.remove("apple")
    print(f"  删除apple后计数: {cbf.get_count('apple')}")

    # 测试3：可扩展布隆过滤器
    print("\n【测试3】可扩展布隆过滤器")
    sbf = ScalableBloomFilter(100, 0.1)
    for i in range(1000):
        sbf.add(f"key_{i}")

    print(f"  子过滤器数量: {len(sbf.filters)}")
    print(f"  查找 'key_500': {'key_500' in sbf}")
    print(f"  查找 'key_999': {'key_999' in sbf}")

    # 测试4：并集和交集
    print("\n【测试4】并集和交集")
    bf1 = BloomFilter(100, 0.01)
    bf2 = BloomFilter(100, 0.01)

    for i in range(50):
        bf1.add(f"set1_{i}")
    for i in range(50):
        bf2.add(f"set2_{i}")

    union = bf1.union(bf2)
    intersection = bf1.intersection(bf2)

    print(f"  union包含'set1_25': {'set1_25' in union}")
    print(f"  union包含'set2_25': {'set2_25' in union}")
    print(f"  intersection包含'set1_25': {'set1_25' in intersection}")
    print(f"  intersection包含'set2_25': {'set2_25' in intersection}")

    # 测试5：参数计算验证
    print("\n【测试5】参数计算")
    for n, p in [(1000, 0.01), (10000, 0.001), (100000, 0.0001)]:
        m = BloomFilter._get_size(n, p)
        k = BloomFilter._get_num_hashes(m, n)
        bf = BloomFilter(n, p)
        print(f"  n={n}, p={p}: m={m}, k={k}, 实际FP率={bf.get_false_positive_rate():.4%}")

    print("\n" + "=" * 50)
    print("布隆过滤器测试完成！")
    print("=" * 50)

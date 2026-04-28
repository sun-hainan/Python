"""
Count-Min Sketch
==========================================

【算法原理】
使用d个哈希函数，每个函数将元素映射到位数组的一个计数器。
查询时，返回所有相关计数器的最小值（避免高估）。

【时间复杂度】
- 添加: O(d)
- 查询: O(d)

【空间复杂度】O(w × d)，w为桶数，d为哈希函数数

【特点】
- 不会低估：实际频率 ≤ 估计频率
- 可能高估：估计频率 = min(c_i) ≥ 实际频率
- 误差界：以概率1-δ保证 error ≤ ε × N

【应用场景】
- 流数据频率统计
- 热门话题追踪
- 网络流量监控
- 推荐系统去重
"""

import math
import hashlib
from typing import List, Tuple


class CountMinSketch:
    """
    Count-Min Sketch

    【参数】
    - width w: 每个哈希表的桶数
    - depth d: 哈希函数个数
    - ε: 误差参数（通常0.01-0.0001）
    - δ: 失败概率参数

    【最优参数】
    - w = e / ε
    - d = ln(1/δ)

    【原理】
    - table[d][w] 二维计数器数组
    - h_i(x): 第i个哈希函数
    - count[x] = min_i table[i][h_i(x)]
    """

    def __init__(self, width: int = None, depth: int = None,
                 epsilon: float = 0.01, delta: float = 0.01):
        """
        初始化Count-Min Sketch

        【参数】
        - epsilon: 误差上界（相对于总计数N）
        - delta: 失败概率
        """
        self.epsilon = epsilon
        self.delta = delta

        # 计算最优参数
        if width is None:
            self.width = int(math.ceil(math.e / epsilon))
        else:
            self.width = width

        if depth is None:
            self.depth = int(math.ceil(math.log(1 / delta)))
        else:
            self.depth = depth

        # 计数器表
        self.table = [[0] * self.width for _ in range(self.depth)]

        # 使用的随机种子
        self.seeds = [i * 12345 for i in range(self.depth)]

    def _hash(self, item, table_idx: int) -> int:
        """
        计算哈希值

        使用多个不同的哈希函数
        """
        data = f"{self.seeds[table_idx]}:{item}".encode()
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)
        # 组合哈希
        return (h1 ^ h2) % self.width

    def add(self, item, count: int = 1) -> None:
        """
        添加元素的计数

        【原理】
        对于每个哈希表i，增加 table[i][h_i(item)]++
        """
        for i in range(self.depth):
            pos = self._hash(item, i)
            self.table[i][pos] += count

    def estimate(self, item) -> int:
        """
        估计元素的频率

        【原理】
        返回所有相关计数器的最小值
        因为高估不会发生（最多等于真实值）
        """
        min_count = float('inf')
        for i in range(self.depth):
            pos = self._hash(item, i)
            min_count = min(min_count, self.table[i][pos])
        return min_count if min_count != float('inf') else 0

    def __getitem__(self, item) -> int:
        return self.estimate(item)

    def __contains__(self, item) -> bool:
        """检查元素是否被添加过"""
        return self.estimate(item) > 0

    def get_error_bound(self, total_count: int) -> Tuple[int, int]:
        """
        获取误差上界

        【返回】(lower_bound, upper_bound)
        其中 lower_bound = estimate - ε*N
              upper_bound = estimate（保守）
        """
        error = int(math.ceil(self.epsilon * total_count))
        return error

    def merge(self, other: 'CountMinSketch') -> 'CountMinSketch':
        """
        合并两个Count-Min Sketch

        【条件】参数必须相同
        """
        if self.width != other.width or self.depth != other.depth:
            raise ValueError("无法合并不同参数的Count-Min Sketch")

        result = CountMinSketch(self.width, self.depth)
        for i in range(self.depth):
            for j in range(self.width):
                result.table[i][j] = self.table[i][j] + other.table[i][j]
        return result


class CountMinSketchWithHeavyHitters(CountMinSketch):
    """
    支持Heavy Hitter检测的Count-Min Sketch

    【Heavy Hitter】
    出现频率超过总阈值比例θ的元素
    例如：θ=1%，则出现超过1%次的元素为heavy hitter
    """

    def __init__(self, epsilon: float = 0.01, delta: float = 0.01,
                 phi: float = 0.01):
        """
        初始化

        【参数】
        - phi: Heavy hitter阈值（比例）
        """
        super().__init__(epsilon, delta)
        self.phi = phi

    def find_heavy_hitters(self, total_count: int,
                          threshold: float = None) -> List[Tuple[str, int]]:
        """
        找出所有Heavy Hitter

        【参数】
        - total_count: 所有元素的总计数
        - threshold: 可选的覆盖阈值（覆盖阈值以上的元素）
        """
        threshold = threshold or total_count * self.phi
        # 这个方法需要维护一个候选列表
        # 简化版：返回估计频率超过阈值的元素
        # 注意：需要外部传入所有可能的元素
        raise NotImplementedError("需要外部提供候选列表")

    def top_k(self, candidates: List[str], k: int) -> List[Tuple[str, int]]:
        """
        返回top-k频繁元素

        【参数】
        - candidates: 候选元素列表
        - k: 返回前k个
        """
        estimates = [(item, self.estimate(item)) for item in candidates]
        estimates.sort(key=lambda x: x[1], reverse=True)
        return estimates[:k]


class CountSketch(CountMinSketch):
    """
    Count Sketch

    【与Count-Min的区别】
    - 使用随机符号（+1/-1）而非直接加1
    - 返回中位数而非最小值
    - 估计更准确但实现更复杂
    """

    def __init__(self, width: int = None, depth: int = None,
                 epsilon: float = 0.01, delta: float = 0.01):
        super().__init__(epsilon, delta)
        # Count Sketch使用sign数组
        self.signs = [[1 if j % 2 == 0 else -1
                      for j in range(self.width)]
                     for i in range(self.depth)]

    def add(self, item, count: int = 1) -> None:
        """添加元素（使用随机符号）"""
        for i in range(self.depth):
            pos = self._hash(item, i)
            sign = self.signs[i][pos]
            self.table[i][pos] += sign * count

    def estimate(self, item) -> int:
        """
        估计频率（使用中位数）

        【原理】
        由于使用符号，某些计数器可能被抵消
        使用中位数来减少方差
        """
        values = []
        for i in range(self.depth):
            pos = self._hash(item, i)
            sign = self.signs[i][pos]
            values.append(sign * self.table[i][pos])

        # 返回中位数
        values.sort()
        return values[self.depth // 2] if self.depth % 2 == 1 else \
            int((values[self.depth // 2 - 1] + values[self.depth // 2]) / 2)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Count-Min Sketch - 测试")
    print("=" * 50)

    # 测试1：基本功能
    print("\n【测试1】基本功能")
    cms = CountMinSketch(epsilon=0.01, delta=0.01)
    print(f"  宽度w={cms.width}, 深度d={cms.depth}")

    # 添加一些元素
    words = ["apple"] * 100 + ["banana"] * 50 + ["cherry"] * 25
    for w in words:
        cms.add(w)

    print(f"  apple估计: {cms.estimate('apple')}, 实际: 100")
    print(f"  banana估计: {cms.estimate('banana')}, 实际: 50")
    print(f"  cherry估计: {cms.estimate('cherry')}, 实际: 25")
    print(f"  grape估计: {cms.estimate('grape')}, 实际: 0")

    # 测试2：大规模数据
    print("\n【测试2】大规模流数据模拟")
    import random
    random.seed(42)

    cms2 = CountMinSketch(epsilon=0.001, delta=0.001)
    n = 1000000
    freq = {}

    for i in range(n):
        # 90%的流量来自1%的元素
        if random.random() < 0.01:
            item = f"popular_{random.randint(1, 100)}"
        else:
            item = f"normal_{random.randint(1, 100000)}"

        cms2.add(item)
        freq[item] = freq.get(item, 0) + 1

    # 检查popular元素的估计
    print(f"  插入{n}个元素")
    for i in range(1, 4):
        item = f"popular_{i}"
        actual = freq.get(item, 0)
        estimated = cms2.estimate(item)
        error = abs(estimated - actual)
        print(f"  {item}: 实际={actual}, 估计={estimated}, 误差={error}")

    # 测试3：Top-k查询
    print("\n【测试3】Top-k查询")
    cms3 = CountMinSketch(epsilon=0.01, delta=0.01)

    # 模拟文本流
    text = "the apple apple apple banana cherry cherry date"
    for word in text.split():
        cms3.add(word)

    # 获取top-3
    all_words = list(set(text.split()))
    top3 = cms3.top_k(all_words, 3)
    print(f"  文本: '{text}'")
    print(f"  Top-3频繁词: {top3}")

    # 测试4：合并
    print("\n【测试4】合并两个CMS")
    cms_a = CountMinSketch(epsilon=0.01, delta=0.01)
    cms_b = CountMinSketch(epsilon=0.01, delta=0.01)

    for _ in range(100):
        cms_a.add("apple")
        cms_b.add("banana")

    merged = cms_a.merge(cms_b)
    print(f"  CMS A: apple={cms_a.estimate('apple')}")
    print(f"  CMS B: banana={cms_b.estimate('banana')}")
    print(f"  合并后: apple={merged.estimate('apple')}, "
          f"banana={merged.estimate('banana')}")

    # 测试5：Count Sketch对比
    print("\n【测试5】Count Sketch vs Count-Min Sketch")
    items = ["a"] * 100 + ["b"] * 90 + ["c"] * 80

    cms_c = CountMinSketch(epsilon=0.1, delta=0.1)
    cs = CountSketch(epsilon=0.1, delta=0.1)

    for item in items:
        cms_c.add(item)
        cs.add(item)

    print(f"  实际: a=100, b=90, c=80")
    print(f"  CMS:  a={cms_c.estimate('a')}, b={cms_c.estimate('b')}, "
          f"c={cms_c.estimate('c')}")
    print(f"  CS:   a={cs.estimate('a')}, b={cs.estimate('b')}, "
          f"c={cs.estimate('c')}")

    # 测试6：误差界
    print("\n【测试6】误差界")
    cms6 = CountMinSketch(epsilon=0.01, delta=0.01)
    for _ in range(10000):
        cms6.add("test_item")
    est = cms6.estimate("test_item")
    error = cms6.get_error_bound(10000)
    print(f"  估计: {est}, 误差上界: ±{error}")
    print(f"  真实值在 [{est - error}, {est}] 范围内（概率>=99%）")

    print("\n" + "=" * 50)
    print("Count-Min Sketch测试完成！")
    print("=" * 50)

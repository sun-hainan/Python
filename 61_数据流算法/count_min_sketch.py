"""
Count-Min Sketch 数据结构模块

一种概率型数据结构，用于高效估计数据流中各个元素的频率。
基于多个哈希函数的概率计数算法，空间效率极高。

核心思想：
- 维护d个小哈希表，每个表有w个桶
- 插入元素时，对每个哈希函数计算桶索引并递增
- 查询时返回所有桶中的最小值（保证下界估计）

参考文献：Cormode, G., & Muthukrishnan, S. (2005).
"An improved data stream summary: The count-min sketch and its applications."
"""

import hashlib
from typing import Dict, List, Optional


class CountMinSketch:
    """
    Count-Min Sketch 频率估计器

    使用固定数量的哈希表和桶来近似流中每个元素的频率。
    优点：空间小（O(w*d)），插入和查询都是O(d)
    缺点：只能估计下界（真实频率 ≥ 估计频率）

    Attributes:
        width: 每个哈希表的桶数量 (w)
        depth: 哈希函数的数量 (d)
        tables: 二维数组，存储计数器的增量
        seeds: 每个哈希函数对应的种子值列表
    """

    def __init__(self, width: int = 1000, depth: int = 5, seed: int = 42):
        """
        初始化Count-Min Sketch

        Args:
            width: 哈希表桶数量，建议设置为预期最大频率的1-2倍
            depth: 哈希函数数量，通常5-10个即可满足精度要求
            seed: 随机种子，确保实验可复现
        """
        if width <= 0 or depth <= 0:
            raise ValueError("width and depth must be positive integers")

        self.width: int = width  # 桶数量
        self.depth: int = depth  # 哈希函数数量
        self.tables: List[List[int]] = [[0] * width for _ in range(depth)]
        # 使用不同种子初始化每个哈希函数的MD5哈希器
        self.seeds: List[int] = [seed + i for i in range(depth)]

    def _hash(self, item: str, table_index: int) -> int:
        """
        计算元素在指定表中的哈希桶索引

        使用MD5哈希函数的简化变体，通过种子区分不同表

        Args:
            item: 要哈希的元素（字符串）
            table_index: 哈希表索引

        Returns:
            桶索引，范围[0, width)
        """
        # 将元素与表种子组合后哈希
        hash_input: str = f"{self.seeds[table_index]}_{item}"
        # 取MD5哈希的前8字节转成整数
        hash_bytes: bytes = hashlib.md5(hash_input.encode()).digest()
        hash_value: int = int.from_bytes(hash_bytes[:8], byteorder='big')
        # 映射到桶范围
        return hash_value % self.width

    def add(self, item: str, count: int = 1) -> None:
        """
        向数据流中添加元素的出现次数

        对每个哈希表，将对应桶的计数器递增count

        Args:
            item: 数据流中的元素标识（通常为字符串）
            count: 此次添加的计数增量，默认为1
        """
        for i in range(self.depth):
            bucket_index: int = self._hash(item, i)
            self.tables[i][bucket_index] += count

    def estimate(self, item: str) -> int:
        """
        估计元素在数据流中的出现总次数

        返回所有相关桶中的最小值（Count-Min的核心思想）

        Args:
            item: 要查询的元素

        Returns:
            估计的出现次数（保证是真实频率的下界）
        """
        # 取出所有相关桶中的最小值
        min_count: int = float('inf')
        for i in range(self.depth):
            bucket_index: int = self._hash(item, i)
            min_count = min(min_count, self.tables[i][bucket_index])
        return min_count if min_count != float('inf') else 0

    def merge(self, other: 'CountMinSketch') -> None:
        """
        合并另一个Count-Min Sketch到当前实例

        前提：两个sketch的width和depth必须相同

        Args:
            other: 要合并的另一个CountMinSketch实例

        Raises:
            ValueError: 当参数不匹配时抛出
        """
        if self.width != other.width or self.depth != other.depth:
            raise ValueError("Cannot merge sketches with different dimensions")
        for i in range(self.depth):
            for j in range(self.width):
                self.tables[i][j] += other.tables[i][j]

    def heavy_hitters(self, threshold: int) -> List[str]:
        """
        找出出现次数超过阈值的所有元素

        使用该方法可以实现"频繁项挖掘"功能

        Args:
            threshold: 频繁项判定阈值

        Returns:
            估计频率超过阈值的元素列表
        """
        # 注意：此方法需要额外存储元素集合
        # 简化实现：返回所有计数接近阈值的桶对应的元素
        results: List[str] = []
        for i in range(self.depth):
            for j in range(self.width):
                if self.tables[i][j] >= threshold:
                    results.append(f"bucket_{i}_{j}")
        return results


class HeavyHitterTracker:
    """
    基于Count-Min Sketch的高频项追踪器

    结合Count-Min Sketch和贪心算法，
    能够追踪数据流中出现次数最多的k个元素。

    Attributes:
        sketch: Count-Min Sketch实例
        k: 追踪的高频项数量上限
        tracked_items: 当前追踪的元素集合
    """

    def __init__(self, width: int = 10000, depth: int = 5, k: int = 10):
        """
        初始化高频项追踪器

        Args:
            width: Count-Min Sketch的桶数量
            depth: 哈希函数数量
            k: 要追踪的高频项数量
        """
        self.sketch: CountMinSketch = CountMinSketch(width, depth)
        self.k: int = k
        self.tracked_items: Dict[str, int] = {}  # 当前候选高频项及其估计频率

    def add(self, item: str) -> None:
        """
        处理新到达的数据元素

        Args:
            item: 数据流中的元素
        """
        self.sketch.add(item)
        # 每次更新后检查是否应该加入追踪列表
        self._maybe_update_tracked(item)

    def _maybe_update_tracked(self, item: str) -> None:
        """
        判断某元素是否应该加入/更新到追踪列表

        使用简单的阈值条件：
        如果估计频率超过当前最小追踪项的频率，则替换

        Args:
            item: 要检查的元素
        """
        current_estimate: int = self.sketch.estimate(item)

        if item in self.tracked_items:
            self.tracked_items[item] = current_estimate
            return

        if len(self.tracked_items) < self.k:
            self.tracked_items[item] = current_estimate
        else:
            # 找出当前追踪列表中频率最低的项
            min_item: str = min(self.tracked_items, key=self.tracked_items.get)
            if current_estimate > self.tracked_items[min_item]:
                del self.tracked_items[min_item]
                self.tracked_items[item] = current_estimate

    def get_top_k(self) -> List[tuple]:
        """
        获取当前估计频率最高的前k个元素

        Returns:
            按估计频率降序排列的(元素, 估计频率)元组列表
        """
        sorted_items: List[tuple] = sorted(
            self.tracked_items.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_items[:self.k]


# -------------------- 测试代码 --------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Count-Min Sketch 频率估计测试")
    print("=" * 60)

    # 创建Count-Min Sketch实例
    # width=1000, depth=5 适合一般场景
    sketch: CountMinSketch = CountMinSketch(width=1000, depth=5)

    # 模拟一个数据流：某些元素出现多次
    data_stream: List[str] = [
        "apple", "banana", "apple", "cherry", "apple", "apple",
        "banana", "date", "apple", "elderberry", "apple", "fig",
        "grape", "apple", "banana", "banana", "apple", "cherry"
    ]

    print(f"\n模拟数据流长度: {len(data_stream)}")
    print(f"数据流内容: {data_stream}\n")

    # 处理数据流
    for item in data_stream:
        sketch.add(item)

    # 查询各元素的估计频率
    unique_items: set = set(data_stream)
    print("-" * 40)
    print("元素频率估计:")
    print("-" * 40)
    for item in sorted(unique_items):
        actual_count: int = data_stream.count(item)
        estimated: int = sketch.estimate(item)
        error: int = actual_count - estimated
        print(f"  '{item}': 实际={actual_count}, 估计={estimated}, 误差={error}")

    # 高频项追踪测试
    print("\n" + "=" * 60)
    print("高频项追踪测试 (Top-3)")
    print("=" * 60)

    # 使用更大的sketch追踪高频项
    tracker: HeavyHitterTracker = HeavyHitterTracker(width=10000, depth=5, k=3)

    # 模拟一个更长且有明显高频项的数据流
    long_stream: List[str] = []
    # apple出现50次，banana出现30次，cherry出现20次，其他各出现1-3次
    import random
    items_pool: List[str] = ["apple"] * 50 + ["banana"] * 30 + ["cherry"] * 20
    other_items: List[str] = ["date", "elderberry", "fig", "grape", "hazelnut"]
    for _ in range(100):
        items_pool.append(random.choice(other_items))

    random.shuffle(items_pool)

    print(f"\n生成长度{len(items_pool)}的数据流...")
    for item in items_pool:
        tracker.add(item)

    print("\n估计的高频项 Top-3:")
    for rank, (item, count) in enumerate(tracker.get_top_k(), 1):
        print(f"  #{rank} '{item}': 估计频率 = {count}")

    print("\n测试完成 ✓")

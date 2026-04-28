"""
有损计数（Lossy Counting）算法模块

一种用于在数据流中发现频繁项（Heavy Hitters）的算法。
通过有策略地"丢弃"低频候选来保证空间效率。

算法特点:
- 保证找到频率超过 s * N 的所有元素（s 为阈值比例）
- 空间复杂度 O(1/ε)，其中ε是近似误差
- 能够识别"老鼠流"（低频但存在）和"大象流"（高频）

变体:
1. Lossy Counting (Manku & Motwani, 2002) - 经典版本
2. Space Saving - 更节省空间的变体

参考文献：Manku, G. S., & Motwani, R. (2002).
"Approximate frequency counts over data streams."
"""

import collections
from typing import Dict, List, Optional, Tuple


class LossyCounting:
    """
    有损计数频繁项挖掘器

    核心思想：
    1. 将数据流划分为多个"桶"（bucket）
    2. 每个桶结束时，减少所有计数器的值（等价于删除"过期"数据）
    3. 插入新元素时，从最小计数开始"挤压"

    空间复杂度：O(1/ε) 个计数器

    Attributes:
        epsilon: 近似误差参数，0 < epsilon < 1
        bucket_width: 桶宽度 N * epsilon
        current_bucket: 当前处理的桶编号
        counters: 元素频率计数器字典
        deleted_counts: 被删除但尚未从计数器中减去的累计值
    """

    def __init__(self, epsilon: float = 0.01, n: Optional[int] = None):
        """
        初始化有损计数器

        Args:
            epsilon: 近似误差参数，越小精度越高
                   例如 epsilon=0.01 意味着可以找到频率>1%的频繁项
            n: 数据流预期总长度，如果未知可传None
        """
        if not 0 < epsilon < 1:
            raise ValueError("epsilon must be in (0, 1)")

        self.epsilon: float = epsilon
        self.bucket_width: int = max(1, int(1 / epsilon)) if n is None else max(1, int(n * epsilon))
        self.current_bucket: int = 0
        self.counters: Dict[str, int] = {}
        self.deleted_counts: int = 0  # 累积删除值
        self.total_processed: int = 0  # 已处理的元素总数

    def add(self, element: str) -> None:
        """
        处理数据流中的新元素

        Args:
            element: 数据流元素标识
        """
        self.total_processed += 1

        # 每处理bucket_width个元素，结束当前桶
        if self.total_processed % self.bucket_width == 0:
            self._end_bucket()

        # 如果元素已在计数器中，增加计数
        if element in self.counters:
            self.counters[element] += 1
        else:
            # 检查是否需要删除低频项来腾出空间
            if len(self.counters) >= 2 / self.epsilon:
                self._prune()
            # 插入新计数器，初始值为deleted_counts（考虑已删除的"水印"）
            self.counters[element] = self.deleted_counts + 1

    def _end_bucket(self) -> None:
        """
        结束当前桶的处理

        将所有计数器的值减去一个"水印"值，
        相当于删除了"肯定不是频繁项"的计数部分
        """
        self.current_bucket += 1
        # 当前水印 = 已删除计数
        # 频率小于当前桶编号的元素肯定不是频繁项
        self.deleted_counts += 1

        # 找出并删除计数 <= deleted_counts 的项
        to_delete: List[str] = [
            elem for elem, count in self.counters.items()
            if count <= self.deleted_counts
        ]
        for elem in to_delete:
            del self.counters[elem]

    def _prune(self) -> None:
        """
        剪枝操作：当计数器数量过多时，删除最小计数的项

        这是有损计数"有损"特性的核心——丢弃可能的低频项
        """
        if not self.counters:
            return

        # 找出最小计数
        min_count: int = min(self.counters.values())
        # 删除所有计数等于最小值的项
        to_delete: List[str] = [
            elem for elem, count in self.counters.items()
            if count == min_count
        ]
        for elem in to_delete:
            del self.counters[elem]

    def get_estimate(self, element: str) -> int:
        """
        获取元素的估计频率

        Args:
            element: 要查询的元素

        Returns:
            估计的出现次数（下界）
        """
        return self.counters.get(element, 0)

    def get_estimate_with_error(self, element: str) -> Tuple[int, int]:
        """
        获取元素的估计频率及误差范围

        有损计数的估计是真实频率的下界，
        真实频率 <= estimate + epsilon * N

        Args:
            element: 要查询的元素

        Returns:
            Tuple[估计值, 最大误差]
        """
        estimate: int = self.counters.get(element, 0)
        error: int = self.bucket_width
        return estimate, error

    def get_frequent_items(self, threshold: float) -> List[Tuple[str, int]]:
        """
        获取所有估计频率超过阈值的元素

        Args:
            threshold: 频率阈值，0到1之间

        Returns:
            按估计频率降序排列的 (元素, 估计频率) 列表
        """
        min_count: int = int(threshold * self.total_processed)

        # 过滤并排序
        frequent: List[Tuple[str, int]] = [
            (elem, count)
            for elem, count in self.counters.items()
            if count >= min_count
        ]

        return sorted(frequent, key=lambda x: x[1], reverse=True)

    def get_all_items_sorted(self) -> List[Tuple[str, int]]:
        """
        获取所有被追踪元素的估计频率（按频率降序）

        Returns:
            按估计频率降序排列的列表
        """
        return sorted(self.counters.items(), key=lambda x: x[1], reverse=True)


class SpaceSaving:
    """
    Space Saving 算法 - 有损计数的改进版本

    与有损计数的区别：
    1. 使用固定大小的哈希表，不主动删除计数器
    2. 当表满时，替换计数最小的元素
    3. 继承被替换元素的计数值（最少加1）

    优点：更简单，保证 O(1/ε) 空间
    缺点：无法区分从未见过的元素和被替换掉的元素

    Attributes:
        epsilon: 误差参数
        k: 追踪的候选数量，约等于 1/epsilon
        counters: 固定大小的 (element, count) 列表
    """

    def __init__(self, epsilon: float = 0.01):
        """
        初始化Space Saving

        Args:
            epsilon: 近似误差参数
        """
        if not 0 < epsilon < 1:
            raise ValueError("epsilon must be in (0, 1)")

        self.epsilon: float = epsilon
        self.k: int = int(1 / epsilon)
        self.counters: List[Tuple[str, int]] = []  # (element, count) 列表
        self.counter_dict: Dict[str, int] = {}  # 快速查找

    def add(self, element: str) -> None:
        """
        添加新元素到数据流

        Args:
            element: 数据流元素
        """
        # 如果元素已在计数器中
        if element in self.counter_dict:
            self.counter_dict[element] += 1
            return

        # 如果计数器未满，直接添加
        if len(self.counters) < self.k:
            self.counters.append((element, 1))
            self.counter_dict[element] = 1
            return

        # 否则，替换计数最小的元素
        # 找出最小计数的位置
        min_pos: int = 0
        min_count: int = self.counters[0][1]
        for i, (elem, count) in enumerate(self.counters):
            if count < min_count:
                min_count = count
                min_pos = i

        # 移除最小计数的元素
        old_elem: str = self.counters[min_pos][0]
        del self.counter_dict[old_elem]

        # 用新元素替换，继承最小计数+1
        self.counters[min_pos] = (element, min_count + 1)
        self.counter_dict[element] = min_count + 1

    def estimate(self, element: str) -> int:
        """
        估计元素的频率

        Args:
            element: 元素标识

        Returns:
            估计的出现次数
        """
        return self.counter_dict.get(element, 0)

    def get_top_k(self, k: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        获取频率最高的k个元素

        Args:
            k: 返回数量，如果为None则返回所有

        Returns:
            按频率降序排列的列表
        """
        sorted_items: List[Tuple[str, int]] = sorted(
            self.counters,
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_items[:k] if k else sorted_items


# -------------------- 测试代码 --------------------
if __name__ == "__main__":
    print("=" * 60)
    print("有损计数算法测试")
    print("=" * 60)

    import random

    # 模拟一个有明显频繁项的数据流
    # 10个高频元素，各出现500次
    # 90个低频元素，各出现5次
    # 总计 10*500 + 90*5 = 5450 个元素

    print("\n【场景】频繁项挖掘测试")
    print("-" * 40)

    stream: List[str] = []
    for i in range(10):
        stream.extend([f"frequent_{i}"] * 500)
    for i in range(90):
        stream.extend([f"rare_{i}"] * 5)

    random.shuffle(stream)
    print(f"数据流: 10个频繁项(各500次) + 90个稀有项(各5次)")
    print(f"总长度: {len(stream)}")
    print(f"阈值: 1% -> 应返回频率>54的元素")

    # 测试有损计数
    print("\n--- Lossy Counting ---")
    lc: LossyCounting = LossyCounting(epsilon=0.01)
    for elem in stream:
        lc.add(elem)

    frequent_lc: List[Tuple[str, int]] = lc.get_frequent_items(threshold=0.01)
    print(f"找到的频繁项数量: {len(frequent_lc)}")
    print("Top-10:")
    for i, (elem, count) in enumerate(frequent_lc[:10], 1):
        print(f"  #{i} {elem}: {count}")

    # 测试Space Saving
    print("\n--- Space Saving ---")
    ss: SpaceSaving = SpaceSaving(epsilon=0.01)
    for elem in stream:
        ss.add(elem)

    top_ss: List[Tuple[str, int]] = ss.get_top_k(10)
    print("Top-10:")
    for i, (elem, count) in enumerate(top_ss, 1):
        print(f"  #{i} {elem}: {count}")

    # 误差分析
    print("\n【误差分析】")
    print("-" * 40)
    test_elem: str = "frequent_0"
    true_count: int = 500
    lc_est, lc_err = lc.get_estimate_with_error(test_elem)
    ss_est: int = ss.estimate(test_elem)

    print(f"元素: {test_elem}")
    print(f"真实频率: {true_count}")
    print(f"Lossy Counting 估计: {lc_est}, 误差范围: ±{lc_err}")
    print(f"Space Saving 估计: {ss_est}")
    print(f"LC相对误差: {abs(lc_est - true_count) / true_count * 100:.2f}%")

    # 内存使用对比
    print("\n【空间效率对比】")
    print("-" * 40)
    print(f"Lossy Counting 追踪项目数: {len(lc.counters)}")
    print(f"Space Saving 追踪项目数: {len(ss.counters)}")
    print(f"理论值 1/epsilon = {int(1/0.01)}")

    print("\n测试完成 ✓")

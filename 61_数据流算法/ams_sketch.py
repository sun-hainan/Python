"""
AMS Sketch 数据结构模块

AMS (Alon-Matias-Szegedy) Sketch 是一种用于估计数据流二阶矩
(F₂ = Σ a_i²) 和其他频率矩的经典算法。

核心功能:
- F₀估计：不同元素的数量（基数估计）
- F₂估计：二阶矩，即频率平方和
- 方差估计：用于检测数据分布变化

算法特点:
- 空间复杂度 O(1/ε²)，其中ε是近似误差
- 使用随机采样和线性投影技术
- 可扩展到高阶矩估计

参考文献：Alon, N., Matias, Y., & Szegedy, M. (1996).
"The space complexity of approximating the frequency moments."
"""

import hashlib
import math
import random
from typing import Dict, List, Optional, Set


class AMSSketch:
    """
    AMS Sketch 二阶矩估计器

    通过维护多个独立的随机变量X_i来估计F₂。
    每个X_i是流中元素的线性组合，其期望值为0，方差与F₂成正比。

    算法步骤：
    1. 选择一个随机哈希函数将元素映射到{-1, +1}
    2. 维护累加和 S = Σ h(element)
    3. F₂ ≈ E[S²] = n + Σ (c_i² - c_i)，其中c_i是频率

    Attributes:
        width: 哈希桶数组的宽度
        counters: 存储S值的计数器数组
        seed: 随机种子
    """

    def __init__(self, width: int = 1000, seed: int = 42):
        """
        初始化AMS Sketch

        Args:
            width: 哈希桶数量，决定空间精度trade-off
            seed: 随机种子，确保可复现
        """
        self.width: int = width
        self.seed: int = seed
        self.counters: List[int] = [0] * width  # 每个桶的累加器
        self.element_counts: Dict[str, int] = {}  # 当前流中各元素的频率
        self.total_count: int = 0  # 流中元素总数

        # 初始化随机哈希函数种子
        random.seed(seed)
        self.hash_coeffs: List[int] = [
            random.randint(1, 2**31 - 1) for _ in range(8)
        ]

    def _hash(self, element: str) -> int:
        """
        将元素哈希到{-1, +1}域

        使用一个简单的哈希函数，将任意字符串映射到±1

        Args:
            element: 要哈希的元素

        Returns:
            -1 或 +1
        """
        hash_bytes: bytes = hashlib.md5(element.encode()).digest()
        hash_int: int = int.from_bytes(hash_bytes[:4], byteorder='big')
        return 1 if (hash_int & 1) else -1

    def add(self, element: str, count: int = 1) -> None:
        """
        向数据流中添加元素

        Args:
            element: 元素标识符
            count: 添加次数
        """
        sign: int = self._hash(element)
        bucket_index: int = hash(element) % self.width

        # 线性投影：累加带符号的计数
        self.counters[bucket_index] += sign * count

        # 更新元素频率统计
        if element not in self.element_counts:
            self.element_counts[element] = 0
        self.element_counts[element] += count
        self.total_count += count

    def estimate_f2(self) -> float:
        """
        估计数据流的二阶矩 F₂

        F₂ = Σ (frequency_i)²，表示频率平方和
        这个值反映了数据分布的"倾斜程度"：
        - 均匀分布时 F₂ ≈ n（接近元素数量的平方）
        - 重尾分布时 F₂ 会很大（少数高频项主导）

        Returns:
            估计的F₂值
        """
        # S²是F₂的无偏估计量
        s_squared: float = sum(c * c for c in self.counters)
        # 取绝对值（数值稳定性考虑）
        return abs(s_squared)

    def estimate_f0(self) -> int:
        """
        估计数据流的不同元素数量（基数）

        也称为F₀估计，使用AMS的方法需要额外维护更多信息。
        此处使用简单的计数器方法作为近似。

        Returns:
            估计的不同元素数量
        """
        return len(self.element_counts)

    def estimate_f1(self) -> int:
        """
        估计数据流的元素总数（F₁矩）

        Returns:
            流中元素的总数
        """
        return self.total_count

    def estimate_entropy(self) -> float:
        """
        估计数据流的香农熵

        H = -Σ p_i * log₂(p_i)，其中p_i是归一化频率

        Returns:
            估计的香农熵值
        """
        if self.total_count == 0:
            return 0.0

        entropy: float = 0.0
        for count in self.element_counts.values():
            if count > 0:
                p: float = count / self.total_count
                entropy -= p * math.log2(p)
        return entropy

    def estimate_variance(self) -> float:
        """
        估计频率分布的方差

        这个指标可以用于检测数据流分布是否发生变化

        Returns:
            频率分布的方差
        """
        if not self.element_counts:
            return 0.0

        frequencies: List[int] = list(self.element_counts.values())
        n: int = len(frequencies)
        mean_freq: float = sum(frequencies) / n
        variance: float = sum((f - mean_freq) ** 2 for f in frequencies) / n
        return variance

    def get_distribution_info(self) -> Dict:
        """
        获取当前数据流分布的完整统计信息

        Returns:
            包含各种矩估计的字典
        """
        return {
            "F0 (distinct elements)": self.estimate_f0(),
            "F1 (total count)": self.estimate_f1(),
            "F2 (second moment)": round(self.estimate_f2(), 2),
            "entropy": round(self.estimate_entropy(), 4),
            "variance": round(self.estimate_variance(), 2),
            "max_frequency": max(self.element_counts.values()) if self.element_counts else 0,
            "min_frequency": min(self.element_counts.values()) if self.element_counts else 0,
        }


class StreamingF2Estimator:
    """
    流式F₂估计器（简化版AMS）

    使用单个计数器S = Σ h(element)，其中h将元素映射到{-1,+1}
    维护S²的无偏估计量来近似F₂。

    优点：空间极小（仅需一个计数器）
    缺点：方差较大，需要多次独立运行取平均
    """

    def __init__(self, seed: int = 42):
        """
        初始化流式F₂估计器

        Args:
            seed: 随机种子
        """
        self.seed: int = seed
        self.counter: int = 0  # S = Σ h(element)
        random.seed(seed)

    def _hash(self, element: str) -> int:
        """将元素映射到{-1, +1}"""
        hash_val: int = hashlib.md5(element.encode()).digest()[0]
        return 1 if (hash_val & 1) else -1

    def add(self, element: str) -> None:
        """
        添加元素到流中

        Args:
            element: 元素标识
        """
        self.counter += self._hash(element)

    def estimate(self) -> float:
        """
        估计F₂值

        根据算法理论：E[S²] = F₂

        Returns:
            F₂的估计值
        """
        return self.counter ** 2


# -------------------- 测试代码 --------------------
if __name__ == "__main__":
    print("=" * 60)
    print("AMS Sketch 频率矩估计测试")
    print("=" * 60)

    # 测试场景1：均匀分布
    print("\n【场景1】均匀分布数据流")
    print("-" * 40)

    uniform_sketch: AMSSketch = AMSSketch(width=1000, seed=100)
    uniform_elements: List[str] = [f"item_{i % 20}" for i in range(1000)]

    for element in uniform_elements:
        uniform_sketch.add(element)

    print(f"输入: 1000个元素，20种类型，每种约50次")
    print(f"分布信息:")
    for key, value in uniform_sketch.get_distribution_info().items():
        print(f"  {key}: {value}")

    # 测试场景2：重尾分布（Zipf分布）
    print("\n【场景2】重尾分布数据流 (Zipf)")
    print("-" * 40)

    zipf_sketch: AMSSketch = AMSSketch(width=1000, seed=100)
    # 模拟Zipf分布：少数元素占据大部分出现次数
    zipf_elements: List[str] = []
    for rank in range(1, 21):  # 20种元素
        frequency: int = int(1000 / rank ** 1.5)  # Zipf指数1.5
        zipf_elements.extend([f"item_{rank}"] * frequency)

    print(f"输入: 约{len(zipf_elements)}个元素，频率呈Zipf分布")
    for element in zipf_elements:
        zipf_sketch.add(element)

    print(f"分布信息:")
    for key, value in zipf_sketch.get_distribution_info().items():
        print(f"  {key}: {value}")

    # 场景3：对比分析
    print("\n【场景3】F₂值的深入对比")
    print("-" * 40)

    print(f"{'指标':<25} {'均匀分布':<15} {'重尾分布':<15}")
    print("-" * 55)

    uniform_info: Dict = uniform_sketch.get_distribution_info()
    zipf_info: Dict = zipf_sketch.get_distribution_info()

    for key in ["F2 (second moment)", "entropy", "variance"]:
        u_val = uniform_info[key]
        z_val = zipf_info[key]
        print(f"{key:<25} {str(u_val):<15} {str(z_val):<15}")

    # 解释F₂的含义
    print("\n【F₂解释】")
    print(f"均匀分布 F₂ ≈ n×(1/n)²×n = n = {len(uniform_elements)}")
    print(f"重尾分布 F₂ 更大，因为高频项主导 (少数项出现很多次)")

    # 流式F₂估计器测试
    print("\n" + "=" * 60)
    print("流式F₂估计器（单计数器）测试")
    print("=" * 60)

    # 多次独立运行取平均
    estimates: List[float] = []
    num_trials: int = 100

    for trial in range(num_trials):
        estimator: StreamingF2Estimator = StreamingF2Estimator(seed=trial)
        test_stream: List[str] = ["a", "b", "a", "c", "b", "a", "d", "a"]
        for elem in test_stream:
            estimator.add(elem)
        estimates.append(estimator.estimate())

    avg_estimate: float = sum(estimates) / len(estimates)
    variance: float = sum((e - avg_estimate) ** 2 for e in estimates) / len(estimates)

    print(f"\n测试流: ['a','b','a','c','b','a','d','a']")
    print(f"真实频率: a=4, b=2, c=1, d=1")
    print(f"真实F₂ = 4² + 2² + 1² + 1² = 22")
    print(f"\n{num_trials}次独立估计:")
    print(f"  平均估计: {avg_estimate:.2f}")
    print(f"  估计方差: {variance:.2f}")
    print(f"  标准差: {math.sqrt(variance):.2f}")

    print("\n测试完成 ✓")

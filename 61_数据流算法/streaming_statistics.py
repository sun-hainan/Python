"""
流式统计数据结构模块

提供滑动窗口模式下的均值、方差和高峰检测功能。
适用于实时数据流分析场景，如监控系统、网络流量分析等。

算法复杂度:
- 均值/方差: O(1) per element (使用Welford在线算法)
- 高峰检测: O(log n) per window slide
"""

import collections
import math
from typing import Deque, List, Optional, Tuple


class SlidingWindowStatistics:
    """
    滑动窗口统计计算器

    使用Welford在线算法维护窗口内的均值和方差，
    避免传统算法中的两遍扫描问题。

    Attributes:
        window_size: 滑动窗口的容量大小
        window: 存储窗口内数据的双端队列
        count: 当前窗口内元素个数
        mean: 当前均值（由Welford算法维护）
        m2: 二阶中心矩的累积值
    """

    def __init__(self, window_size: int):
        """
        初始化滑动窗口统计器

        Args:
            window_size: 滑动窗口的最大容量，必须大于0
        """
        self.window_size: int = window_size  # 窗口容量
        self.window: Deque[float] = collections.deque()  # 存储窗口元素
        self.count: int = 0  # 已处理元素总数
        self.mean: float = 0.0  # 当前均值
        self.m2: float = 0.0  # 二阶中心矩 (∑(x - mean)²)

    def add(self, value: float) -> None:
        """
        添加新数据点到流中，并更新统计量

        使用Welford在线算法的增量更新公式：
        delta = x - mean
        mean += delta / n
        m2 += delta * (x - new_mean)

        Args:
            value: 新进入数据流的数值
        """
        # 计算新值与当前均值的偏差
        delta: float = value - self.mean
        # 更新元素计数
        self.count += 1
        # 增量更新均值
        self.mean += delta / self.count
        # 增量更新二阶中心矩
        self.m2 += delta * (value - self.mean)
        # 将新值加入窗口
        self.window.append(value)
        # 如果窗口超出容量，移除最旧的值并调整统计量
        if len(self.window) > self.window_size:
            old_value: float = self.window.popleft()
            self._remove_old_value(old_value)

    def _remove_old_value(self, old_value: float) -> None:
        """
        从统计量中移除最旧的值（窗口滑动时调用）

        使用Welford算法的逆向更新公式，
        确保均值和方差在窗口滑动后仍然准确。

        Args:
            old_value: 被移除的最旧数据点
        """
        # 当窗口大小小于总数时才进行移除调整
        if self.count > self.window_size:
            # 计算旧值与当前均值的偏差
            delta: float = old_value - self.mean
            # 减少元素计数
            self.count -= 1
            # 调整均值（移除影响）
            self.mean += delta / self.count
            # 调整二阶中心矩
            self.m2 -= delta * (old_value - self.mean)

    def get_mean(self) -> float:
        """
        获取当前滑动窗口内的均值

        Returns:
            窗口内所有数据的算术平均值，如果窗口为空返回0.0
        """
        if not self.window:
            return 0.0
        return self.mean

    def get_variance(self) -> float:
        """
        获取当前滑动窗口内的样本方差

        使用贝塞尔校正（除以n-1）计算无偏样本方差

        Returns:
            窗口内数据的方差，如果窗口元素少于2个返回0.0
        """
        if len(self.window) < 2:
            return 0.0
        # 样本方差 = 二阶中心矩 / (n-1)
        return self.m2 / (self.count - 1)

    def get_std_dev(self) -> float:
        """
        获取当前滑动窗口内的标准差

        Returns:
            窗口内数据的标准差
        """
        return math.sqrt(self.get_variance())

    def get_peak_value(self) -> Optional[float]:
        """
        获取当前滑动窗口内的最大值（高峰检测）

        Returns:
            窗口内的最大值，如果窗口为空返回None
        """
        if not self.window:
            return None
        return max(self.window)

    def detect_spike(self, threshold_std: float = 2.0) -> Tuple[bool, float]:
        """
        检测是否存在异常高峰

        判断当前均值距离初始均值是否超过指定倍数的标准差

        Args:
            threshold_std: 判断高峰的阈值（以标准差为单位）

        Returns:
            Tuple[是否存在高峰, 当前值与均值的偏差]
        """
        if len(self.window) < 10:
            return False, 0.0
        std_dev: float = self.get_std_dev()
        if std_dev == 0:
            return False, 0.0
        # 使用最后几个值判断是否有突然跳变
        recent_values: List[float] = list(self.window)[-5:]
        avg_recent: float = sum(recent_values) / len(recent_values)
        deviation: float = abs(avg_recent - self.mean) / std_dev
        return deviation > threshold_std, deviation

    def get_summary(self) -> dict:
        """
        获取当前窗口的完整统计摘要

        Returns:
            包含均值、标准差、方差、最大值等统计量的字典
        """
        return {
            "count": len(self.window),
            "mean": round(self.get_mean(), 4),
            "variance": round(self.get_variance(), 4),
            "std_dev": round(self.get_std_dev(), 4),
            "max": round(self.get_peak_value(), 4) if self.get_peak_value() else None,
            "min": round(min(self.window), 4) if self.window else None,
        }


class ExponentialMovingAverage:
    """
    指数移动平均计算器

    与滑动窗口均值不同，EMA给予最近数据更高的权重，
    通过指数衰减因子α控制新旧数据的重要性比例。

    Attributes:
        alpha: 平滑因子，取值(0,1)，值越大对近期数据越敏感
        current_ema: 当前计算的指数移动平均值
        initialized: 是否已收到第一个数据点
    """

    def __init__(self, alpha: float = 0.3):
        """
        初始化EMA计算器

        Args:
            alpha: 平滑因子，建议取值0.1~0.3，越大越敏感
        """
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha: float = alpha
        self.current_ema: Optional[float] = None
        self.initialized: bool = False

    def add(self, value: float) -> float:
        """
        添加新数据点并更新EMA

        公式: EMA_t = α * x_t + (1-α) * EMA_{t-1}

        Args:
            value: 新数据点

        Returns:
            更新后的EMA值
        """
        if not self.initialized:
            self.current_ema = value
            self.initialized = True
        else:
            # 指数加权更新
            self.current_ema = self.alpha * value + (1 - self.alpha) * self.current_ema
        return self.current_ema

    def get_ema(self) -> Optional[float]:
        """
        获取当前EMA值

        Returns:
            当前EMA值，如果尚未初始化返回None
        """
        return self.current_ema


# -------------------- 测试代码 --------------------
if __name__ == "__main__":
    import random

    print("=" * 60)
    print("滑动窗口统计测试")
    print("=" * 60)

    # 创建窗口大小为10的滑动窗口统计器
    stats: SlidingWindowStatistics = SlidingWindowStatistics(window_size=10)

    # 模拟数据流：前5个正常值，后5个逐渐上升
    data_stream: List[float] = [10.0, 11.0, 10.5, 10.8, 11.2, 12.0, 13.5, 15.0, 18.0, 25.0]
    print(f"\n输入数据流: {data_stream}\n")

    for i, value in enumerate(data_stream):
        stats.add(value)
        print(f"步骤 {i + 1}: 值={value:.1f}, 均值={stats.get_mean():.4f}, "
              f"标准差={stats.get_std_dev():.4f}, 峰值={stats.get_peak_value()}")

    print(f"\n最终统计摘要: {stats.get_summary()}")

    # 高峰检测测试
    print("\n" + "-" * 40)
    print("高峰检测测试")
    print("-" * 40)

    stats2: SlidingWindowStatistics = SlidingWindowStatistics(window_size=20)
    normal_values: List[float] = [random.gauss(100, 5) for _ in range(15)]
    for val in normal_values:
        stats2.add(val)

    spike_value: float = 200.0  # 模拟异常高峰
    stats2.add(spike_value)
    is_spike, deviation = stats2.detect_spike(threshold_std=2.0)
    print(f"添加高峰值 {spike_value} 后:")
    print(f"  均值: {stats2.get_mean():.2f}")
    print(f"  检测到高峰: {is_spike}")
    print(f"  偏差倍数: {deviation:.2f}σ")

    # EMA测试
    print("\n" + "=" * 60)
    print("指数移动平均测试")
    print("=" * 60)

    ema: ExponentialMovingAverage = ExponentialMovingAverage(alpha=0.3)
    test_values: List[float] = [10, 12, 15, 11, 13, 10, 12]
    print(f"\n输入数据: {test_values}")
    print(f"Alpha: 0.3 (较敏感)\n")

    for val in test_values:
        current = ema.add(val)
        print(f"值={val}, EMA={current:.4f}")

    print("\n测试完成 ✓")

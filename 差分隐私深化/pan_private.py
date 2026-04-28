# -*- coding: utf-8 -*-
"""
Pan-隐私保护模块 (pan_private.py)
====================================

算法原理
--------
Pan-privacy 是差分隐私在流数据（Stream Processing）场景下的扩展，
由 Dwork, Naor, Pitassi, Rothblum 和 Vadhan (2010) 首次提出。
核心目标是：在数据持续到达的流场景中，在线地维护一个差分隐私的聚合状态，
同时限制信息泄漏的上界。

关键概念：
1. 持续性隐私 (Perpetual Privacy)：在无限时间窗口内，
   每个个体贡献的数据点在整个流生命周期中始终受到隐私保护。
2. 泄漏上界 (Leakage Bound)：Pan-private 算法允许的累积信息泄漏量
   有明确的上界，不随时间无限增长。
3. Pan-private 流算法：对滑动窗口（Sliding Window）内的数据
   维护一个满足差分隐私的状态，窗口内的查询始终得到隐私保护。
4. 滑动窗口 (Sliding Window)：只考虑最近 W 个数据点的窗口模型，
   随时间前向移动，旧数据自动过期。

Pan-private 的核心技术挑战是在线噪声注入和状态维护的平衡：
- 直接对每个数据点添加噪声会导致噪声累积过多
- 延迟聚合再添加噪声会破坏持续性隐私保证

时间复杂度：O(n) ~ O(n log W)，与流长度和窗口大小相关
空间复杂度：O(W) ~ O(log W)，只需维护窗口状态

应用场景
--------
- 网络入侵检测中的持续流监控
- 金融交易欺诈检测
- IoT 传感器数据流隐私保护
- 实时用户行为分析
"""

import math
import random
import sys
from typing import List, Callable, Optional, Any
from collections import deque


# =============================================================================
# 工具函数：差分隐私噪声
# =============================================================================

def laplace_noise(scale: float) -> float:
    """
    生成拉普拉斯分布噪声。

    参数:
        scale (float): 拉普拉斯分布尺度参数 b = 1/epsilon（敏感度已归一化）。

    返回:
        float: 拉普拉斯噪声样本。
    """
    u = random.random() - 0.5
    noise = -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))
    return noise


def exponential_mechanism(quality_scores: List[float], epsilon: float) -> int:
    """
    指数机制（Exponential Mechanism）：从候选集合中依概率选择输出。

    参数:
        quality_scores (List[float]): 各候选输出的质量分数（越高越好）。
        epsilon (float): 隐私预算。

    返回:
        int: 选中的候选索引。
    """
    # 将质量分数转换为概率权重
    max_score = max(quality_scores)
    adjusted = [math.exp((s - max_score) * epsilon / 2.0) for s in quality_scores]
    total = sum(adjusted)
    # 轮盘赌选择
    threshold = random.random() * total
    cumulative = 0.0
    for i, w in enumerate(adjusted):
        cumulative += w
        if cumulative >= threshold:
            return i
    return len(adjusted) - 1


# =============================================================================
# 1. 持续性隐私 (Perpetual Privacy) 概念与泄漏上界
# =============================================================================

class LeakageBoundCalculator:
    """
    泄漏上界计算器：分析 Pan-private 算法的累积信息泄漏。

    泄漏来源：
    - 每次状态更新时的即时泄漏（查询响应中的信息）
    - 状态中历史数据的间接泄漏
    - 窗口滑动时的过期数据处理
    """

    def __init__(self, epsilon: float, window_size: int, total_steps: int):
        """
        初始化泄漏上界计算器。

        参数:
            epsilon (float): 每次操作的隐私预算。
            window_size (int): 滑动窗口大小 W。
            total_steps (int): 总操作步数 T。
        """
        self.epsilon = epsilon
        self.window_size = window_size
        self.total_steps = total_steps
        # 累积即时泄漏（每次查询响应的累积隐私损失）
        self.instant_leakage = 0.0
        # 泄漏上界理论值
        self.leakage_upper_bound = epsilon * total_steps
        # 实际累积泄漏记录
        self.actual_leakage_history = []

    def record_query(self, query_result: Any, true_value: Any) -> float:
        """
        记录一次查询的即时泄漏量（用KL散度近似）。

        参数:
            query_result: 加入噪声后的查询结果。
            true_value: 真实值。

        返回:
            float: 此次查询的即时泄漏估计。
        """
        # 即时泄漏 = 噪声方差（或用MSE近似）
        delta = abs(query_result - true_value) if isinstance(
            query_result, (int, float)) and isinstance(true_value, (int, float)) else 0
        self.instant_leakage += delta * epsilon
        self.actual_leakage_history.append(self.instant_leakage)
        return self.instant_leakage

    def get_leakage_bound(self) -> float:
        """
        返回理论泄漏上界。

        返回:
            float: epsilon * T（每次操作累积上界）。
        """
        return self.leakage_upper_bound

    def get_composition_bound(self, delta: float = 1e-5) -> float:
        """
        返回高级组合定理（Advanced Composition）下的泄漏上界。

        参数:
            delta (float): 失败概率参数。

        返回:
            float: 组合后泄漏上界（比 naive 乘积更紧）。
        """
        # 高级组合定理：(epsilon', delta') 满足
        # epsilon' = 2*epsilon*sqrt(2*T*log(1/delta)) / T
        # 这里简化为泄漏上界收紧
        T = len(self.actual_leakage_history) if self.actual_leakage_history else self.total_steps
        eps_prime = 2 * self.epsilon * math.sqrt(2 * T * math.log(1.0 / delta))
        return eps_prime

    def report(self) -> dict:
        """
        生成泄漏上界报告。

        返回:
            dict: 包含各项泄漏指标的字典。
        """
        return {
            "epsilon_per_step": self.epsilon,
            "total_steps": self.total_steps,
            "window_size": self.window_size,
            "naive_leakage_bound": self.leakage_upper_bound,
            "current_actual_leakage": self.instant_leakage,
            "advanced_composition_bound": self.get_composition_bound(),
        }


# =============================================================================
# 2. Pan-private 流算法基础：Count-Mean-Sketch DP
# =============================================================================

class PanPrivateCountMeanSketch:
    """
    Pan-private Count-Mean-Sketch：流数据频率估计的 Pan-private 实现。

    算法原理：
    - Count-Mean-Sketch 是一种哈希表结构，用于估计流中各元素的频率。
    - 对每个到达的元素，累加到对应计数中。
    - 在活跃窗口上添加拉普拉斯噪声，以实现 Pan-private 保证。
    - 当窗口滑动导致数据过期时，显式减去过期计数并重新添加噪声。

    参数:
        num_counters (int): 哈希桶数量（空间复杂度 O(num_counters)）。
        num_hashes (int): 哈希函数数量（通常为 2~3）。
        epsilon (float): 隐私预算。
        window_size (int): 滑动窗口大小。
    """

    def __init__(self,
                 num_counters: int,
                 num_hashes: int,
                 epsilon: float,
                 window_size: int):
        self.num_counters = num_counters
        self.num_hashes = num_hashes
        self.epsilon = epsilon
        self.window_size = window_size
        # 活跃计数数组（带噪声）
        self.counters = [0.0] * num_counters
        # 历史记录：用于窗口滑动时恢复
        self.history = deque()  # 存储 (timestamp, item)
        self.timestamp = 0
        # 哈希函数种子
        self.hash_seeds = [random.randint(0, 1 << 30) for _ in range(num_hashes)]

    def _hash(self, item: Any, seed: int) -> int:
        """
        简单的哈希函数。

        参数:
            item (Any): 要哈希的元素。
            seed (int): 哈希种子。

        返回:
            int: 桶索引。
        """
        h = hash((item, seed))
        return abs(h) % self.num_counters

    def _get_bucket_indices(self, item: Any) -> List[int]:
        """
        获取元素对应的所有桶索引。

        参数:
            item (Any): 元素。

        返回:
            List[int]: 桶索引列表。
        """
        return [self._hash(item, seed) for seed in self.hash_seeds]

    def process(self, item: Any) -> None:
        """
        处理一个新到达的元素。

        参数:
            item (Any): 新到达的元素。
        """
        indices = self._get_bucket_indices(item)
        # 对每个相关计数器添加拉普拉斯噪声并累加
        for idx in indices:
            noise = laplace_noise(1.0 / (self.epsilon * self.num_hashes))
            self.counters[idx] += 1.0 + noise
        # 记录到历史队列
        self.history.append((self.timestamp, item))
        self.timestamp += 1
        # 滑动窗口过期处理
        self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        """
        检查并处理过期数据：当历史长度超过窗口大小时，
        从历史队列中移除最老的数据，并调整计数器。
        """
        while len(self.history) > self.window_size:
            old_timestamp, old_item = self.history.popleft()
            # 对过期元素的计数器减去贡献
            indices = self._get_bucket_indices(old_item)
            for idx in indices:
                self.counters[idx] -= 1.0

    def estimate(self, item: Any) -> float:
        """
        估计某个元素的频率。

        参数:
            item (Any): 待估计元素。

        返回:
            float: 带噪声的频率估计。
        """
        indices = self._get_bucket_indices(item)
        # Count-Mean：取中位数（减少哈希冲突偏差）
        estimates = [self.counters[idx] for idx in indices]
        estimates.sort()
        return estimates[len(estimates) // 2]

    def query(self, items: List[Any]) -> dict:
        """
        批量查询多个元素的频率。

        参数:
            items (List[Any]): 待查询元素列表。

        返回:
            dict: {item: estimated_count} 频率估计。
        """
        return {item: max(0.0, self.estimate(item)) for item in items}


# =============================================================================
# 3. 滑动窗口差分隐私计数器
# =============================================================================

class SlidingWindowDP:
    """
    滑动窗口差分隐私计数器：维护最近 W 个数据点的计数差分隐私。

    算法原理：
    - 维护一个长度为 W 的滑动窗口，只对窗口内的数据计数。
    - 对每个查询响应添加拉普拉斯噪声。
    - 当窗口滑动时（收到新数据），重新评估是否添加额外噪声。
    - 通过"重置"（reset）机制在窗口边界处刷新隐私状态，防止历史累积泄漏。

    参数:
        epsilon (float): 隐私预算。
        window_size (int): 滑动窗口大小。
        sensitivity (float): 计数敏感度（通常为 1）。
    """

    def __init__(self, epsilon: float, window_size: int, sensitivity: float = 1.0):
        self.epsilon = epsilon
        self.window_size = window_size
        self.sensitivity = sensitivity
        # 窗口内的原始计数（不含噪声，用于计算）
        self.raw_count = 0
        # 扰动后的计数（用于输出）
        self.noisy_count = 0.0
        # 滑动窗口历史
        self.window = deque()
        # 总处理元素数（用于跟踪重置时机）
        self.total_processed = 0
        # 上次重置后的步数
        self.steps_since_reset = 0
        # 重置阈值（每 W 步重置一次）
        self.reset_threshold = window_size

    def add(self, item: int) -> float:
        """
        添加一个新数据点到窗口中。

        参数:
            item (int): 新数据点值（通常为 1）。

        返回:
            float: 当前扰动后的计数。
        """
        # 滑动窗口：移除过期数据
        if len(self.window) >= self.window_size:
            self.window.popleft()
        # 添加新数据
        self.window.append(item)
        self.raw_count = sum(self.window)
        self.total_processed += 1
        self.steps_since_reset += 1
        # 定期重置隐私状态（防止累积泄漏超过上界）
        if self.steps_since_reset >= self.reset_threshold:
            self._reset()
        # 添加拉普拉斯噪声
        self.noisy_count = self.raw_count + laplace_noise(self.sensitivity / self.epsilon)
        return self.noisy_count

    def _reset(self) -> None:
        """
        重置隐私状态：清空窗口，重新开始计数。
        这是 Pan-private 持续性隐私的关键机制。
        """
        self.window.clear()
        self.raw_count = 0
        self.noisy_count = 0.0
        self.steps_since_reset = 0
        # 重置后添加新的随机种子噪声以刷新状态
        refresh_noise = laplace_noise(self.sensitivity / self.epsilon)
        self.noisy_count = refresh_noise

    def query(self) -> float:
        """
        查询当前窗口内的计数（带差分隐私保护）。

        返回:
            float: 扰动后的计数。
        """
        # 确保计数是最新的
        self.noisy_count = self.raw_count + laplace_noise(self.sensitivity / self.epsilon)
        return max(0.0, self.noisy_count)


# =============================================================================
# 4. Pan-private 敏感值追踪
# =============================================================================

class PanPrivateRunningMax:
    """
    Pan-private 运行时最大值追踪器：流中持续追踪最大值，
    同时满足持续性隐私保证。

    算法原理：
    - 维护当前最大值估计。
    - 每次新数据到达时，用指数机制决定是否更新最大值。
    - 在窗口边界通过重置机制刷新隐私状态。
    - 通过跟踪最大值变化而非精确值来降低敏感度。

    参数:
        epsilon (float): 隐私预算。
        window_size (int): 滑动窗口大小。
    """

    def __init__(self, epsilon: float, window_size: int):
        self.epsilon = epsilon
        self.window_size = window_size
        self.window = deque()
        self.current_max = 0.0
        self.noisy_max = 0.0
        self.leakage_tracker = LeakageBoundCalculator(
            epsilon, window_size, window_size
        )

    def add(self, value: float) -> float:
        """
        添加一个新值并更新最大值。

        参数:
            value (float): 新到达的值。

        返回:
            float: 扰动后的最大值估计。
        """
        # 窗口滑动
        if len(self.window) >= self.window_size:
            self.window.popleft()
        self.window.append(value)
        # 记录真实最大值
        true_max = max(self.window)
        # 指数机制决策：是否更新最大值
        candidates = [self.current_max, value]
        candidate_scores = [self.current_max, value]
        chosen_idx = exponential_mechanism(candidate_scores, self.epsilon)
        self.current_max = candidates[chosen_idx]
        # 添加噪声
        self.noisy_max = self.current_max + laplace_noise(1.0 / self.epsilon)
        # 记录泄漏
        self.leakage_tracker.record_query(self.noisy_max, true_max)
        return self.noisy_max

    def query(self) -> float:
        """
        查询当前最大值。

        返回:
            float: 扰动后的最大值。
        """
        return max(0.0, self.noisy_max)

    def get_leakage_report(self) -> dict:
        """
        获取当前累积泄漏报告。

        返回:
            dict: 泄漏上界信息。
        """
        return self.leakage_tracker.report()


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Pan-隐私保护模块 测试")
    print("=" * 60)

    # 测试 1：泄漏上界计算
    print("\n[测试1] 泄漏上界 (Leakage Bound) 计算")
    print("-" * 40)
    calculator = LeakageBoundCalculator(epsilon=0.1, window_size=100, total_steps=500)
    for i in range(50):
        true_val = i * 2
        noisy_val = true_val + laplace_noise(1.0 / 0.1)
        calculator.record_query(noisy_val, true_val)
    report = calculator.report()
    print(f"  单步 epsilon: {report['epsilon_per_step']}")
    print(f"  总步数: {report['total_steps']}")
    print(f"  Naive 泄漏上界: {report['naive_leakage_bound']:.4f}")
    print(f"  当前实际泄漏: {report['current_actual_leakage']:.4f}")
    print(f"  高级组合上界: {report['advanced_composition_bound']:.4f}")

    # 测试 2：Pan-private Count-Mean-Sketch
    print("\n[测试2] Pan-private Count-Mean-Sketch 流算法")
    print("-" * 40)
    sketch = PanPrivateCountMeanSketch(
        num_counters=100,
        num_hashes=2,
        epsilon=0.5,
        window_size=50
    )
    # 模拟流数据
    random.seed(42)
    stream = [random.choice(["A", "B", "C", "D"]) for _ in range(100)]
    for item in stream[:50]:
        sketch.process(item)
    # 查询频率
    query_items = ["A", "B", "C", "D"]
    estimates = sketch.query(query_items)
    print(f"  窗口大小: {sketch.window_size}")
    print(f"  已处理元素数: {sketch.timestamp}")
    print("  频率估计（扰动后）:")
    for item, est in estimates.items():
        true_count = stream[:sketch.timestamp].count(item)
        print(f"    {item}: 真实={true_count}, 估计={est:.2f}")

    # 测试 3：滑动窗口差分隐私计数器
    print("\n[测试3] 滑动窗口差分隐私计数器")
    print("-" * 40)
    sw_counter = SlidingWindowDP(epsilon=0.5, window_size=10)
    stream_values = [1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1]
    print(f"  窗口大小: {sw_counter.window_size}")
    print("  数据流 -> 查询结果（扰动计数）:")
    for i, val in enumerate(stream_values):
        noisy = sw_counter.add(val)
        raw = sw_counter.raw_count
        print(f"    步骤{i+1}: 输入={val}, 原始窗口计数={raw}, 扰动计数={noisy:.2f}")

    # 测试 4：Pan-private 运行时最大值追踪
    print("\n[测试4] Pan-private 运行时最大值追踪")
    print("-" * 40)
    running_max = PanPrivateRunningMax(epsilon=0.3, window_size=20)
    values = [5, 12, 8, 15, 10, 18, 14, 20, 17, 22, 19]
    print(f"  窗口大小: {running_max.window_size}")
    print("  数据流 -> 扰动最大值:")
    for i, val in enumerate(values):
        noisy = running_max.add(val)
        true_val = max(running_max.window)
        print(f"    步骤{i+1}: 输入={val:2d}, 当前窗口最大值={true_val:2d}, "
              f"扰动最大值={noisy:.2f}")
    leakage = running_max.get_leakage_report()
    print(f"\n  累积泄漏上界: {leakage['naive_leakage_bound']:.4f}")
    print(f"  当前实际泄漏: {leakage['current_actual_leakage']:.4f}")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

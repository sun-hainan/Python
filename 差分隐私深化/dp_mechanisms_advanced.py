# -*- coding: utf-8 -*-
"""
差分隐私高级机制模块

本模块实现差分隐私中的高级机制，包括：
- 指数机制（Exponential Mechanism）：用于选择输出的离散选择
- 拉斯蒂涅机制（Rappaport's Mechanism）：历史机制，用于有序统计

这些机制扩展了基本的拉普拉斯/高斯机制，支持更复杂的隐私保护场景。

作者：算法实现
版本：1.0
"""

import numpy as np  # 数值计算库
from typing import List, Callable, Tuple, Optional  # 类型提示
from scipy import stats  # 统计分布


def exponential_mechanism(scores: np.ndarray, epsilon: float, 
                           sensitivity: float = 1.0) -> Tuple[int, np.ndarray]:
    """
    实现指数机制（Exponential Mechanism）

    指数机制由McSherry和Talwar于2007年提出，用于从一组离散候选中
    选择最优输出。机制以与分数成比例的概率选择每个候选。

    核心原理：
        P(output = r) ∝ exp(ε * score(r) / (2 * Δ))

    参数:
        scores: 各候选的分数数组（越高越好）
        epsilon: 隐私预算ε
        sensitivity: 分数函数的敏感度Δ

    返回:
        (选择的索引, 概率分布)

    示例:
        >>> scores = np.array([10.0, 20.0, 30.0, 40.0])
        >>> idx, probs = exponential_mechanism(scores, epsilon=1.0)
        >>> print(f"选择索引: {idx}, 对应分数: {scores[idx]}")
    """
    n_candidates = len(scores)  # 候选数量
    # 计算权重：使用指数函数，权重与分数成正比
    # 注意：除以2是因为L1敏感度的定义
    weights = np.exp(epsilon * scores / (2 * sensitivity))
    # 归一化得到概率分布
    probabilities = weights / np.sum(weights)

    # 根据概率分布采样
    selected_idx = np.random.choice(n_candidates, p=probabilities)

    return selected_idx, probabilities


def exponential_mechanism_top_k(scores: np.ndarray, epsilon: float,
                                  k: int = 1, sensitivity: float = 1.0) -> List[int]:
    """
    使用指数机制选择top-k候选

    参数:
        scores: 候选分数数组
        epsilon: 隐私预算
        k: 需要选择的候选数量
        sensitivity: 敏感度

    返回:
        选中的k个候选索引列表（按概率降序）
    """
    selected = []  # 已选中的候选索引
    remaining_indices = list(range(len(scores)))  # 剩余候选
    remaining_scores = scores.copy()  # 剩余分数

    for _ in range(k):
        # 对剩余候选应用指数机制
        idx, _ = exponential_mechanism(remaining_scores, epsilon, sensitivity)
        actual_idx = remaining_indices[idx]
        selected.append(actual_idx)

        # 移除已选候选（将其分数设为负无穷）
        remaining_indices.pop(idx)
        remaining_scores = np.delete(remaining_scores, idx)
        if len(remaining_scores) == 0:
            break

    return selected


def rappaport_mechanism(values: np.ndarray, epsilon: float,
                         order_stat: int = 1) -> float:
    """
    拉斯蒂涅机制（Rappaport's Mechanism）

    一种历史机制，用于在有序统计场景下提供差分隐私保护。
    通过对有序数据进行扰动来实现隐私保护。

    参数:
        values: 输入数据数组
        epsilon: 隐私预算
        order_stat: 选择第几阶统计量（1为最小值，len为最大值）

    返回:
        扰动后的统计量值

    注意:
        拉斯蒂涅机制的核心思想是对第k阶顺序统计量添加拉普拉斯噪声，
        噪声规模与数据量n成反比。
    """
    n = len(values)  # 数据量
    # 对数据进行排序
    sorted_values = np.sort(values)
    # 获取指定的阶统计量
    order_value = sorted_values[order_stat - 1] if order_stat <= n else sorted_values[-1]

    # 计算敏感度：对于阶统计量，敏感度为1
    sensitivity = 1.0
    # 添加拉普拉斯噪声
    noise = np.random.laplace(0, sensitivity / epsilon)
    # 返回扰动后的值
    return order_value + noise


def geometric_mechanism(values: np.ndarray, epsilon: float) -> np.ndarray:
    """
    几何机制（Geometric Mechanism）

    一种专门为整数数据设计的差分隐私机制。
    其实质是在拉普拉斯机制基础上对离散数据进行适配。

    参数:
        values: 整数数组输入
        epsilon: 隐私预算

    返回:
        扰动后的整数数组
    """
    # 对每个值添加离散拉普拉斯噪声（几何分布噪声）
    noise_scale = 1.0 / epsilon  # 噪声尺度参数
    # 从几何分布采样并随机添加正负号
    noise = np.random.geometric(p=1 - np.exp(-epsilon), size=len(values))
    signs = np.random.choice([-1, 1], size=len(values))  # 随机符号
    perturbed = values + signs * (noise - 1)

    return perturbed


def staircase_mechanism(values: np.ndarray, epsilon: float, 
                         delta: float = 1e-5) -> np.ndarray:
    """
    楼梯机制（Staircase Mechanism）

    一种比纯拉普拉斯机制更省隐私预算的机制，在相同的ε下提供更好的效用。
    通过将隐私损失分布近似为高斯分布来实现。

    参数:
        values: 输入数组
        epsilon: 隐私预算ε
        delta: 失败概率δ

    返回:
        扰动后的数组
    """
    # 计算高斯机制所需的标准差
    # 基于 RDP 转 GDP 的标准转换
    sigma = np.sqrt(2 * np.log(1.25 / delta)) / epsilon

    # 应用高斯噪声
    perturbed = values + np.random.normal(0, sigma, size=len(values))

    return perturbed


def propose_test(output1: float, output2: float, epsilon: float) -> bool:
    """
    指数机制中的提议测试（Propose-Test）

    用于在两个候选之间进行选择的隐私保护方法。
    核心思想是：给定两个候选项，以特定概率接受更好的那个。

    参数:
        output1: 第一个候选的分数
        output2: 第二个候选的分数
        epsilon: 隐私预算

    返回:
        True表示选择第一个候选，False表示选择第二个
    """
    # 计算接受概率
    diff = output1 - output2
    prob_accept = np.exp(epsilon * diff / 2)
    prob_accept = min(1.0, prob_accept)  # 概率上界为1

    return np.random.random() < prob_accept


def exponential_with_sufficient_statistics(sufficient_stats: np.ndarray,
                                            epsilon: float,
                                            base_distribution: str = "laplace"
                                            ) -> np.ndarray:
    """
    基于充分统计量的指数机制

    当查询可以分解为充分统计量时，可以更高效地应用指数机制。

    参数:
        sufficient_stats: 充分统计量数组
        epsilon: 隐私预算
        base_distribution: 基础噪声分布 ("laplace" 或 "gaussian")

    返回:
        扰动后的统计量
    """
    if base_distribution == "laplace":
        # 使用拉普拉斯噪声
        scale = 1.0 / epsilon
        noise = np.random.laplace(0, scale, size=sufficient_stats.shape)
    else:
        # 使用高斯噪声
        sigma = 1.0 / epsilon
        noise = np.random.normal(0, sigma, size=sufficient_stats.shape)

    return sufficient_stats + noise


def permute_and_rank(scores: np.ndarray, epsilon: float, 
                      sensitivity: float = 1.0) -> np.ndarray:
    """
    指数机制实现：基于分数的随机排序

    使用指数机制对候选进行随机排序，排序概率与分数成正比。

    参数:
        scores: 候选分数数组
        epsilon: 隐私预算
        sensitivity: 敏感度

    返回:
        排序后的索引数组（随机排列）
    """
    n = len(scores)  # 候选数量
    ranked_indices = []  # 初始化排名列表
    remaining = list(range(n))  # 剩余未排名候选
    remaining_scores = scores.copy()  # 剩余分数

    # 逐个选择当前位置的候选
    for _ in range(n):
        # 找到剩余候选中的最优者（使用指数机制）
        if len(remaining) == 1:
            ranked_indices.append(remaining[0])
            break

        idx, _ = exponential_mechanism(remaining_scores, epsilon, sensitivity)
        ranked_indices.append(remaining[idx])

        # 移除已选候选
        remaining.pop(idx)
        remaining_scores = np.delete(remaining_scores, idx)

    return np.array(ranked_indices)


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私高级机制测试")
    print("=" * 60)

    # 测试1：基本指数机制
    print("\n【测试1】指数机制 - 候选选择")
    np.random.seed(42)  # 设置随机种子以确保可复现性
    scores = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    for i in range(3):
        idx, probs = exponential_mechanism(scores, epsilon=1.0)
        print(f"  第{i+1}次选择: 索引={idx}, 分数={scores[idx]}, 概率分布={probs.round(3)}")

    # 测试2：指数机制验证
    print("\n【测试2】指数机制 - 概率分布验证")
    np.random.seed(100)
    n_trials = 10000  # 蒙特卡洛次数
    test_scores = np.array([10.0, 20.0, 30.0])
    chosen = np.zeros(len(test_scores))
    for _ in range(n_trials):
        idx, _ = exponential_mechanism(test_scores, epsilon=1.0)
        chosen[idx] += 1

    empirical_probs = chosen / n_trials
    _, theoretical_probs = exponential_mechanism(test_scores, epsilon=1.0)
    print(f"  理论概率: {theoretical_probs.round(3)}")
    print(f"  经验概率: {empirical_probs.round(3)}")
    print(f"  (两者应接近，约±0.03)")

    # 测试3：Top-k选择
    print("\n【测试3】指数机制Top-3选择")
    np.random.seed(42)
    scores_topk = np.array([15.0, 85.0, 30.0, 60.0, 45.0])
    selected = exponential_mechanism_top_k(scores_topk, epsilon=0.5, k=3)
    print(f"  原始分数: {scores_topk}")
    print(f"  选择索引: {selected}")
    print(f"  对应分数: {scores_topk[selected]}")

    # 测试4：拉斯蒂涅机制
    print("\n【测试4】拉斯蒂涅机制 - 有序统计扰动")
    np.random.seed(42)
    test_data = np.array([3.2, 5.7, 2.1, 8.9, 4.5, 7.3, 1.8, 6.4])
    print(f"  原始数据: {test_data}")
    print(f"  有序统计 (k=1 最小值): {np.sort(test_data)[0]}")
    perturbed_min = rappaport_mechanism(test_data, epsilon=1.0, order_stat=1)
    print(f"  扰动后最小值: {perturbed_min:.4f}")

    # 测试5：几何机制
    print("\n【测试5】几何机制 - 离散数据扰动")
    np.random.seed(42)
    integer_data = np.array([10, 20, 30, 40, 50])
    perturbed_int = geometric_mechanism(integer_data, epsilon=1.0)
    print(f"  原始数据: {integer_data}")
    print(f"  扰动数据: {perturbed_int}")

    # 测试6：楼梯机制
    print("\n【测试6】楼梯机制 - GDP近似")
    np.random.seed(42)
    test_values = np.array([100.0, 200.0, 300.0])
    perturbed_stair = staircase_mechanism(test_values, epsilon=1.0, delta=1e-5)
    print(f"  原始数据: {test_values}")
    print(f"  扰动数据: {perturbed_stair.round(2)}")

    # 测试7：提议测试机制
    print("\n【测试7】提议测试 - 二选一")
    np.random.seed(42)
    n_choice = 1000
    accept_count = 0
    for _ in range(n_choice):
        if propose_test(100.0, 50.0, epsilon=1.0):
            accept_count += 1
    print(f"  选项1分数=100, 选项2分数=50")
    print(f"  选择选项1的比例: {accept_count/n_choice:.3f}")
    print(f"  理论概率: {min(1.0, np.exp(0.5)):.3f}")

    # 测试8：随机排序
    print("\n【测试8】指数机制 - 随机排序")
    np.random.seed(42)
    ranking_scores = np.array([30.0, 10.0, 50.0, 20.0, 40.0])
    ranked = permute_and_rank(ranking_scores, epsilon=1.0)
    print(f"  原始分数: {ranking_scores}")
    print(f"  随机排名索引: {ranked}")
    print(f"  对应分数序列: {ranking_scores[ranked]}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

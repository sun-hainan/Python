# -*- coding: utf-8 -*-
"""
报告噪声最大值 (Report Noisy Max, RM)
=====================================

算法原理:
报告噪声最大值是差分隐私中选择最大值(如 argmax)的基本技术。
核心思想: 不直接计算真正的最大值，而是在每个候选上添加噪声，
然后报告噪声最大值的索引。

变体:
1. 标准RM: 在每个候选分数上添加Laplace噪声
2. 指数机制变体(RM-EM): 当输出空间很大时使用指数机制
3. 阈值RM: 只报告超过某个阈值的最优值
4. 证书RM: 提供额外的隐私保证

隐私分析:
- 机制满足(ε, 0)-差分隐私
- 敏感性: Δ = max |f_i(D) - f_i(D')| 对于相邻数据集D, D'

与指数机制的关系:
RM等价于输出空间为{1,...,k}、效用函数为f_i(D)的指数机制。
这因为: P(i) ∝ exp(ε·f_i(D)/2Δ) 与Laplace噪声后取最大值渐近等价。

时间复杂度: O(k) 其中k是候选数量
空间复杂度: O(1) 仅需存储当前最大值

应用场景:
- 选择最频繁项
- 特征重要性排序
- 数据库中的top-k查询
- 机器学习中的模型选择
- 强化学习中的探索
"""

import math
import numpy as np


def laplace_sample(scale):
    """
    从Laplace分布采样
    
    参数:
        scale: 尺度参数b
    
    返回:
        从Lap(0, b)采样的值
    """
    u = np.random.uniform(-0.5, 0.5)
    return -scale * np.sign(u) * np.log(1 - 2 * abs(u))


def report_noisy_max(scores, epsilon, sensitivity):
    """
    标准报告噪声最大值机制
    
    参数:
        scores: 各候选的原始分数列表
        epsilon: 隐私预算
        sensitivity: 分数函数的敏感性
    
    返回:
        噪声最大值对应的索引
    """
    k = len(scores)
    scale = sensitivity / epsilon
    
    # 为每个候选添加Laplace噪声
    noisy_scores = [score + laplace_sample(scale) for score in scores]
    
    # 返回最大值索引
    return np.argmax(noisy_scores)


def report_noisy_max_with_value(scores, epsilon, sensitivity):
    """
    RM机制，返回最大值及其索引
    
    参数:
        scores: 原始分数
        epsilon: 隐私参数
        sensitivity: 敏感性
    
    返回:
        (max_index, max_value)
    """
    k = len(scores)
    scale = sensitivity / epsilon
    
    noisy_scores = [score + laplace_sample(scale) for score in scores]
    max_idx = np.argmax(noisy_scores)
    
    return max_idx, noisy_scores[max_idx]


def report_noisy_top_k(scores, epsilon, sensitivity, k=1):
    """
    报告噪声最大的前k个 (Top-k RM)
    
    参数:
        scores: 原始分数列表
        epsilon: 隐私预算
        sensitivity: 敏感性
        k: 返回前k个
    
    返回:
        前k个索引列表
    """
    n = len(scores)
    scale = sensitivity / epsilon
    
    # 为每个分数添加噪声
    noisy_scores = [score + laplace_sample(scale) for score in scores]
    
    # 排序并返回前k个
    sorted_indices = np.argsort(noisy_scores)[::-1]
    
    return sorted_indices[:k].tolist()


def threshold_report_noisy_max(scores, epsilon, sensitivity, threshold):
    """
    阈值报告噪声最大值
    
    仅当噪声最大值超过阈值时才报告，否则报告"无"
    
    参数:
        scores: 原始分数
        epsilon: 隐私参数
        sensitivity: 敏感性
        threshold: 阈值
    
    返回:
        (index, value) 或 (None, None)
    """
    k = len(scores)
    scale = sensitivity / epsilon
    
    noisy_scores = [score + laplace_sample(scale) for score in scores]
    max_idx = np.argmax(noisy_scores)
    max_value = noisy_scores[max_idx]
    
    # 如果最大值低于阈值，不报告
    if max_value < threshold:
        return None, None
    
    return max_idx, max_value


class ReportNoisyMax:
    """
    RM机制的面向对象封装
    
    支持多次调用并自动追踪隐私消耗。
    """
    
    def __init__(self, epsilon, sensitivity):
        """
        初始化
        
        参数:
            epsilon: 隐私预算
            sensitivity: 敏感性
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.scale = sensitivity / epsilon
        self.call_count = 0
    
    def argmax(self, scores):
        """
        返回噪声最大值的索引
        
        参数:
            scores: 分数列表
        
        返回:
            索引
        """
        self.call_count += 1
        return report_noisy_max(scores, self.epsilon, self.sensitivity)
    
    def top_k(self, scores, k):
        """
        返回噪声最大的前k个
        
        参数:
            scores: 分数列表
            k: 数量
        
        返回:
            索引列表
        """
        self.call_count += 1
        return report_noisy_top_k(scores, self.epsilon, self.sensitivity, k)


class ComposeRM:
    """
    组合多个RM机制进行序列查询
    
    每次调用消耗部分隐私预算。
    """
    
    def __init__(self, total_epsilon, total_delta, n_expected_calls):
        """
        初始化
        
        参数:
            total_epsilon: 总ε预算
            total_delta: 总δ预算
            n_expected_calls: 预期调用次数
        """
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.n_expected_calls = n_expected_calls
        self.epsilon_per_call = total_epsilon / n_expected_calls
        self.delta_per_call = total_delta / n_expected_calls
        self.call_count = 0
    
    def query(self, scores, sensitivity):
        """
        执行一次RM查询
        
        参数:
            scores: 分数列表
            sensitivity: 敏感性
        
        返回:
            选中的索引
        """
        if self.call_count >= self.n_expected_calls:
            raise RuntimeError("超过预期调用次数")
        
        return report_noisy_max(scores, self.epsilon_per_call, sensitivity)


def rm_privacy_analysis(epsilon, sensitivity, scores):
    """
    分析RM机制的隐私保证
    
    参数:
        epsilon: 隐私参数
        sensitivity: 敏感性
        scores: 分数列表
    
    返回:
        隐私分析报告
    """
    k = len(scores)
    
    # 计算真实最大值的概率
    true_max_idx = np.argmax(scores)
    
    # 概率上界(UCB)
    # P(输出=i) ≤ exp(-ε(|score_i - score_max| - Δ)/2) + δ
    prob_bounds = {}
    max_score = max(scores)
    
    for i, s in enumerate(scores):
        gap = max_score - s
        if gap > 0:
            # P(选中i) ≤ exp(-ε·gap/2)
            upper_bound = math.exp(-epsilon * gap / (2 * sensitivity))
        else:
            upper_bound = 1.0
        prob_bounds[i] = min(upper_bound, 1.0)
    
    return prob_bounds


if __name__ == "__main__":
    # 测试报告噪声最大值
    
    print("=" * 60)
    print("报告噪声最大值 (Report Noisy Max) 测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1: 基本RM
    print("\n[测试1] 标准RM机制")
    
    scores = [10, 25, 15, 30, 20]  # 分数列表，真实最大值为索引3
    epsilon = 1.0
    sensitivity = 1.0
    
    true_max_idx = np.argmax(scores)
    print(f"  真实分数: {scores}")
    print(f"  真实最大值索引: {true_max_idx} (分数={scores[true_max_idx]})")
    print(f"  ε={epsilon}, Δ={sensitivity}")
    
    # 多次实验看分布
    results = {i: 0 for i in range(len(scores))}
    n_trials = 10000
    
    for _ in range(n_trials):
        selected = report_noisy_max(scores, epsilon, sensitivity)
        results[selected] += 1
    
    print(f"\n  采样{n_trials}次的结果分布:")
    for idx, count in results.items():
        pct = count / n_trials * 100
        bar = "█" * int(pct / 2)
        print(f"    索引{idx} (分数={scores[idx]:>2}): {count:>5}次 {bar} {pct:.1f}%")
    
    # 测试2: Top-k RM
    print("\n[测试2] Top-k RM机制")
    
    scores = [10, 25, 15, 30, 20, 35, 12, 28]
    epsilon = 1.0
    sensitivity = 1.0
    
    true_top3 = np.argsort(scores)[::-1][:3].tolist()
    print(f"  真实Top-3: 索引{true_top3} (分数={[scores[i] for i in true_top3]})")
    
    k = 3
    topk_results = {tuple(range(len(scores))): 0}
    
    for _ in range(5000):
        topk = report_noisy_top_k(scores, epsilon, sensitivity, k)
        topk_results[tuple(topk)] = topk_results.get(tuple(topk), 0) + 1
    
    # 显示前5个最常见结果
    sorted_results = sorted(topk_results.items(), key=lambda x: -x[1])[:5]
    print(f"  Top-3采样结果(前5常见):")
    for topk, count in sorted_results:
        correct = sum(1 for i in topk if i in true_top3)
        print(f"    {topk}: {count}次 ({correct}/3正确)")
    
    # 测试3: 阈值RM
    print("\n[测试3] 阈值RM机制")
    
    threshold = 28
    print(f"  阈值: {threshold}")
    
    n_trials = 5000
    reported_count = 0
    reported_indices = []
    
    for _ in range(n_trials):
        idx, val = threshold_report_noisy_max(scores, epsilon, sensitivity, threshold)
        if idx is not None:
            reported_count += 1
            reported_indices.append(idx)
    
    print(f"  {n_trials}次实验中报告次数: {reported_count} ({reported_count/n_trials:.1%})")
    if reported_indices:
        print(f"  报告最多的索引: {max(set(reported_indices), key=reported_indices.count)}")
    
    # 测试4: ε影响实验
    print("\n[测试4] 不同ε值的选择性")
    
    true_max_idx = np.argmax(scores)
    print(f"  真实最大索引: {true_max_idx}")
    print(f"  {'ε':>8} | {'正确率':>10} | {'置信度分布':>30}")
    print("  " + "-" * 55)
    
    for eps in [0.01, 0.1, 0.5, 1.0, 2.0, 5.0]:
        correct = 0
        for _ in range(1000):
            if report_noisy_max(scores, eps, sensitivity) == true_max_idx:
                correct += 1
        
        # 计算分布的集中程度
        rm = ReportNoisyMax(eps, sensitivity)
        counts = {i: 0 for i in range(len(scores))}
        for _ in range(500):
            counts[rm.argmax(scores)] += 1
        
        max_pct = max(counts.values()) / 500 * 100
        print(f"  {eps:>8.2f} | {correct/1000:>9.1%} | max占比{max_pct:>5.1f}%")
    
    # 测试5: 隐私分析
    print("\n[测试5] RM隐私概率上界分析")
    
    scores = [10, 25, 15, 30, 20]
    epsilon = 1.0
    sensitivity = 1.0
    
    prob_bounds = rm_privacy_analysis(epsilon, sensitivity, scores)
    max_score = max(scores)
    
    print(f"  ε={epsilon}, Δ={sensitivity}")
    print(f"  分数分布: {scores}")
    print(f"  各索引被选中的概率上界:")
    for idx, bound in prob_bounds.items():
        score_gap = max_score - scores[idx]
        print(f"    索引{idx} (分数={scores[idx]}, gap={score_gap}): P≤{bound:.4f}")
    
    # 实际观察概率对比
    actual_probs = {i: 0 for i in range(len(scores))}
    for _ in range(10000):
        actual_probs[report_noisy_max(scores, epsilon, sensitivity)] += 1
    
    print(f"  实际观察概率:")
    for idx, count in actual_probs.items():
        print(f"    索引{idx}: 观察={count/10000:.4f}, 上界={prob_bounds[idx]:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成 - ε越大，选择真实最大值的概率越高")
    print("=" * 60)

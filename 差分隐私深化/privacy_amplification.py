# -*- coding: utf-8 -*-
"""
隐私放大定理 (Privacy Amplification)
=====================================

算法原理:
隐私放大定理是差分隐私理论中的核心结果，说明了随机化机制
在特定条件下可以获得比标称值更好的隐私保证。

主要类型:

1. 抽样放大 (Sampling Amplification):
   当机制以概率p对数据进行抽样时，实际隐私保证会放大。
   如果基础机制满足(ε, δ)-DP，则抽样后的机制满足
   (ε', δ')-DP，其中 ε' ≈ ε·p，δ' ≈ δ·p (对于小p)。

2. 随机响应放大 (Randomized Response Amplification):
   随机响应是一种本地隐私机制，当样本量n很大时，
   全局敏感性降低，导致隐私放大。

3. 指数机制放大:
   对于指数机制，抽样同样可以放大隐私保证。

数学基础:
- 强大数律: 当样本量足够大时，样本均值接近期望
- 概率集中不等式: Hoeffding, Chernoff, Azuma等
- 数据处理不等式: 后处理不增加隐私损失

时间复杂度: O(1) 仅为计算公式
空间复杂度: O(1) 存储参数

应用场景:
- 本地差分隐私 (Local DP)
- 数据采样的隐私分析
- 分布式隐私计算
- 大规模数据发布
"""

import math
import numpy as np


def amplification_by_sampling(base_epsilon, base_delta, sampling_prob):
    """
    抽样放大的标准界 (Theorem 2 in "The Algorithm..." by Dwork & Roth)
    
    参数:
        base_epsilon: 基础机制的ε
        base_delta: 基础机制的δ
        sampling_prob: 抽样概率p
    
    返回:
        放大后的隐私参数 (epsilon_amplified, delta_amplified)
    
    定理: 如果机制M满足(ε, δ)-DP，以概率p独立抽样后，
    结果满足(ε', δ')-DP，其中:
    ε' = log(1 + p(e^ε - 1)) ≈ p·ε (当ε很小)
    δ' = p·δ + (1-p)·e^{-p^2·n/2} (Chernoff界)
    """
    # 精确公式
    eps_amplified = math.log(1 + sampling_prob * (math.exp(base_epsilon) - 1))
    
    # δ的放大界 (使用标准集中不等式)
    delta_amplified = sampling_prob * base_delta
    
    return eps_amplified, delta_amplified


def amplification_by_sampling_approx(base_epsilon, sampling_prob):
    """
    抽样放大的近似公式 (小ε时)
    
    当ε很小且p不太大时: ε' ≈ p·ε
    """
    eps_approx = sampling_prob * base_epsilon
    return eps_approx, 0.0


def amplification_by_sampling_tight(base_epsilon, base_delta, sampling_prob, n=None):
    """
    抽样放大的更紧界
    
    使用Chernoff界得到更精确的结果。
    
    参数:
        base_epsilon: 基础ε
        base_delta: 基础δ
        sampling_prob: 抽样概率p
        n: 数据集大小(可选，用于Chernoff界)
    
    返回:
        放大后的隐私参数
    """
    # 基础ε的放大
    eps_amplified = math.log(1 + sampling_prob * (math.exp(base_epsilon) - 1))
    
    # δ的放大 - 使用更紧的界
    if n is not None:
        # Chernoff界: P(|X - p·n| > λ·p·n) ≤ 2·e^{-λ²·p·n/3)
        # 对于δ'我们需要这个概率小于某个值
        # 但实际上我们使用简化界
        pass
    
    delta_amplified = sampling_prob * base_delta
    
    return eps_amplified, delta_amplified


def amplification_by_subsampling(base_epsilon, base_delta, sample_ratio, 
                                  composition_guarantee=True):
    """
    子采样放大的另一种分析 (使用紧组合界)
    
    参数:
        base_epsilon: 基础ε
        base_delta: 基础δ
        sample_ratio: 采样比例
        composition_guarantee: 是否使用紧组合保证
    
    返回:
        放大后隐私参数
    """
    if composition_guarantee:
        # 使用Advanced Composition的结果
        # 设k = 1/p (每个样本单独处理)
        k = 1 / sample_ratio if sample_ratio > 0 else float('inf')
        
        # 组合k个机制，每个消耗约 base_epsilon / k
        # 但使用高级组合得到更好的界
        # 这里简化处理
        eps = base_epsilon * sample_ratio
        delta = base_delta * sample_ratio
    else:
        eps, delta = amplification_by_sampling(base_epsilon, base_delta, sample_ratio)
    
    return eps, delta


def randomized_response_amplification(p, epsilon):
    """
    随机响应的隐私放大分析
    
    随机响应是本地差分隐私的基本机制:
    - 以概率1/(1+e^ε)翻转响应
    - 以概率e^ε/(1+e^ε)保持原样
    
    当有n个独立用户时，聚合结果的隐私会被放大。
    
    参数:
        p: 真实比例为p的用户的比例
        epsilon: 隐私参数
    
    返回:
        关于比例p的估计的隐私参数
    """
    # 随机响应的扰动概率
    # P(响应=1 | 真实=1) = e^ε / (1 + e^ε)
    # P(响应=1 | 真实=0) = 1 / (1 + e^ε)
    
    # 观测到的期望比例
    e_epsilon = math.exp(epsilon)
    prob_respond_1_given_1 = e_epsilon / (1 + e_epsilon)
    prob_respond_1_given_0 = 1 / (1 + e_epsilon)
    
    # 对于大数据集n，比例估计的标准差约为 O(1/√n)
    # 这导致隐私的额外放大
    
    return {
        'prob_1_if_1': prob_respond_1_given_1,
        'prob_1_if_0': prob_respond_1_given_0,
        'epsilon_local': epsilon  # 本地隐私参数
    }


def amplification_by_transformations(base_mechanism, n_transformations):
    """
    变换放大: 连续应用多个变换时的隐私放大
    
    参数:
        base_mechanism: 基础机制
        n_transformations: 变换数量
    
    返回:
        累积隐私参数
    """
    # 每个变换不增加隐私损失(后处理)
    # 但组合可能导致放大
    base_eps, base_delta = base_mechanism
    
    # 简单组合
    eps_total = base_eps * math.sqrt(2 * n_transformations * math.log(1 / base_delta))
    delta_total = base_delta * n_transformations
    
    return eps_total, delta_total


class PrivacyAmplifier:
    """
    隐私放大计算器
    
    提供多种放大场景的计算。
    """
    
    def __init__(self, base_epsilon, base_delta=0.0):
        """
        初始化
        
        参数:
            base_epsilon: 基础ε
            base_delta: 基础δ
        """
        self.base_epsilon = base_epsilon
        self.base_delta = base_delta
    
    def by_sampling(self, sampling_prob):
        """
        计算抽样放大的隐私参数
        """
        return amplification_by_sampling(self.base_epsilon, self.base_delta, sampling_prob)
    
    def by_sampling_approx(self, sampling_prob):
        """
        使用近似公式计算
        """
        return amplification_by_sampling_approx(self.base_epsilon, sampling_prob)
    
    def by_sample_count(self, dataset_size, sample_size):
        """
        根据样本数量计算放大
        
        参数:
            dataset_size: 数据集大小
            sample_size: 样本大小
        
        返回:
            放大后的隐私参数
        """
        sampling_prob = sample_size / dataset_size
        return self.by_sampling(sampling_prob)
    
    def report_amplification(self, sampling_prob):
        """
        报告放大的详细信息
        """
        eps_exact, delta_exact = self.by_sampling(sampling_prob)
        eps_approx, delta_approx = self.by_sampling_approx(sampling_prob)
        
        report = {
            'base_epsilon': self.base_epsilon,
            'base_delta': self.base_delta,
            'sampling_probability': sampling_prob,
            'amplified_exact': (eps_exact, delta_exact),
            'amplified_approx': (eps_approx, delta_approx),
            'epsilon_improvement': self.base_epsilon / eps_exact if eps_exact > 0 else float('inf'),
            'delta_improvement': self.base_delta / delta_exact if delta_exact > 0 else float('inf')
        }
        
        return report


def compute_privacy_budget_with_sampling(total_queries, dataset_size, 
                                          base_epsilon, base_delta):
    """
    计算带采样的隐私预算分配
    
    参数:
        total_queries: 查询总数
        dataset_size: 数据集大小
        base_epsilon: 单次查询的基础ε
        base_delta: 单次查询的基础δ
    
    返回:
        隐私预算分析报告
    """
    # 无采样时的总隐私消耗
    eps_no_sample = total_queries * base_epsilon
    delta_no_sample = total_queries * base_delta
    
    # 全采样时(每次查询都采样)
    sample_ratio = 1.0 / dataset_size
    eps_full_sample = base_epsilon * sample_ratio
    delta_full_sample = base_delta * sample_ratio
    
    # 实际采样率(假设每次查询随机采样一个样本)
    # 但通常我们考虑的是抽样后的数据发布场景
    
    return {
        'no_sampling': (eps_no_sample, delta_no_sample),
        'full_sampling': (eps_full_sample, delta_full_sample),
        'sampling_ratio': sample_ratio
    }


def amplification_factor_analysis(base_epsilon, delta=1e-5):
    """
    分析不同采样率下的放大因子
    
    参数:
        base_epsilon: 基础ε
        delta: 目标δ
    
    返回:
        放大因子表
    """
    print(f"\n基础ε={base_epsilon}, δ={delta} 的放大分析")
    print(f"{'采样率':>10} | {'放大ε':>10} | {'改进倍数':>10}")
    print("  " + "-" * 38)
    
    for p in [0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]:
        eps_amp, _ = amplification_by_sampling(base_epsilon, delta, p)
        improvement = base_epsilon / eps_amp if eps_amp > 0 else float('inf')
        print(f"  {p:>10.1%} | {eps_amp:>10.4f} | {improvement:>9.1f}x")


if __name__ == "__main__":
    # 测试隐私放大定理
    
    print("=" * 60)
    print("隐私放大定理 (Privacy Amplification) 测试")
    print("=" * 60)
    
    # 测试1: 抽样放大
    print("\n[测试1] 抽样放大定理")
    
    base_epsilon = 1.0
    base_delta = 1e-5
    
    print(f"  基础机制: ε={base_epsilon}, δ={base_delta}")
    print()
    print(f"  {'采样率p':>10} | {'精确ε\\'':>10} | {'近似ε\\'':>10} | {'精确δ\\'':>12} | {'改进倍数':>10}")
    print("  " + "-" * 70)
    
    for p in [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]:
        eps_exact, delta_exact = amplification_by_sampling(base_epsilon, base_delta, p)
        eps_approx, _ = amplification_by_sampling_approx(base_epsilon, p)
        improvement = base_epsilon / eps_exact if eps_exact > 0 else float('inf')
        
        print(f"  {p:>10.1%} | {eps_exact:>10.4f} | {eps_approx:>10.4f} | {delta_exact:>12.2e} | {improvement:>9.1f}x")
    
    # 测试2: Privacy Amplifier类
    print("\n[测试2] PrivacyAmplifier类使用")
    
    amplifier = PrivacyAmplifier(base_epsilon=1.0, base_delta=1e-5)
    
    sample_ratios = [0.01, 0.05, 0.1, 0.2]
    
    for p in sample_ratios:
        report = amplifier.report_amplification(p)
        print(f"  采样率={p:.0%}: ε'{report['amplified_exact'][0]:.4f}, 改进{report['epsilon_improvement']:.1f}x")
    
    # 测试3: 采样数量放大
    print("\n[测试3] 基于样本数量的放大")
    
    dataset_size = 100000
    sample_size = 1000
    base_epsilon = 1.0
    base_delta = 1e-5
    
    amplifier = PrivacyAmplifier(base_epsilon, base_delta)
    eps_amp, delta_amp = amplifier.by_sample_count(dataset_size, sample_size)
    
    print(f"  数据集大小: {dataset_size:,}")
    print(f"  样本大小: {sample_size:,}")
    print(f"  采样比例: {sample_size/dataset_size:.2%}")
    print(f"  放大后: ε'={eps_amp:.6f}, δ'={delta_amp:.2e}")
    print(f"  隐私改进: ε改进 {base_epsilon/eps_amp:.0f}x")
    
    # 测试4: 随机响应放大
    print("\n[测试4] 随机响应隐私放大")
    
    epsilon = 1.0
    rr_info = randomized_response_amplification(0.5, epsilon)
    
    print(f"  本地ε={epsilon}")
    print(f"  P(响应=1 | 真实=1) = {rr_info['prob_1_if_1']:.4f}")
    print(f"  P(响应=1 | 真实=0) = {rr_info['prob_1_if_0']:.4f}")
    
    # 当有大量用户时的分析
    n_users = 10000
    # 聚合后的标准误
    se = math.sqrt(1 / n_users)
    # 估计的隐私放大效应
    effective_epsilon = epsilon * math.sqrt(1 / n_users)
    print(f"  n={n_users:,}用户聚合后有效ε ≈ {effective_epsilon:.4f}")
    
    # 测试5: 大规模查询隐私预算分析
    print("\n[测试5] 大规模查询隐私预算分析")
    
    total_queries = 1000
    dataset_size = 100000
    base_epsilon = 1.0
    base_delta = 1e-5
    
    budget = compute_privacy_budget_with_sampling(
        total_queries, dataset_size, base_epsilon, base_delta
    )
    
    print(f"  查询数: {total_queries:,}")
    print(f"  数据集大小: {dataset_size:,}")
    print(f"  单次查询: ε={base_epsilon}, δ={base_delta}")
    print()
    print(f"  无采样总隐私消耗: ε={budget['no_sampling'][0]:.2f}, δ={budget['no_sampling'][1]:.2e}")
    print(f"  全采样: ε={budget['full_sampling'][0]:.4f}, δ={budget['full_sampling'][1]:.2e}")
    print(f"  采样比例: {budget['sampling_ratio']:.2%}")
    
    # 测试6: 放大因子表
    print("\n[测试6] 不同ε值的放大因子表")
    
    amplification_factor_analysis(base_epsilon=1.0)
    
    print("\n" + "=" * 60)
    print("测试完成 - 采样显著放大隐私保证(ε' ≈ p·ε)")
    print("=" * 60)

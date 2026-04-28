# -*- coding: utf-8 -*-
"""
差分隐私验证与隐私审计模块

本模块实现差分隐私的验证技术，包括：
- 隐私损失跟踪（Privacy Loss Tracking）
- 攻击实验（Ablation Study）
- 基于模拟的验证（Simulation-based Verification）

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import List, Tuple, Callable


def privacy_loss_tracking(neighbor_d1: np.ndarray, neighbor_d2: np.ndarray,
                          mechanism_fn: Callable,
                          epsilon: float, n_trials: int = 10000) -> dict:
    """
    隐私损失跟踪验证

    通过实验测量隐私损失是否在预设范围内。

    参数:
        neighbor_d1: 相邻数据集1
        neighbor_d2: 相邻数据集2
        mechanism_fn: 差分隐私机制函数
        epsilon: 目标ε
        n_trials: 试验次数

    返回:
        验证结果字典
    """
    log_ratio_d1 = []
    log_ratio_d2 = []

    for _ in range(n_trials):
        output1 = mechanism_fn(neighbor_d1)
        output2 = mechanism_fn(neighbor_d2)

        # 计算似然比
        # 这里简化处理，假设输出是连续的
        diff1 = -np.sum(output1**2) / 2  # 简化似然计算
        diff2 = -np.sum(output2**2) / 2
        log_ratio_d1.append(diff1)
        log_ratio_d2.append(diff2)

    # 计算经验隐私损失
    avg_log_ratio = np.mean(log_ratio_d1) - np.mean(log_ratio_d2)
    max_log_ratio = max(np.max(log_ratio_d1) - np.min(log_ratio_d2), 0)

    return {
        'epsilon': epsilon,
        'empirical_eps': max_log_ratio,
        'is_verified': max_log_ratio <= epsilon,
        'avg_log_ratio': avg_log_ratio
    }


def gaussian_noise_calibration_verification(epsilon: float, delta: float,
                                             sensitivity: float = 1.0,
                                             n_samples: int = 10000) -> dict:
    """
    验证高斯机制校准的正确性

    通过模拟验证σ是否正确校准。

    参数:
        epsilon: 目标ε
        delta: 目标δ
        sensitivity: 敏感度
        n_samples: 样本数

    返回:
        验证结果
    """
    sigma = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / epsilon
    true_val = 0.0

    count_violations = 0
    max_epsilon_seen = 0.0

    for _ in range(n_samples):
        noisy_val = np.random.normal(true_val, sigma)
        # 检测是否违反隐私
        # 简化的检测方法
        log_ratio = (noisy_val**2) / (2 * sigma**2)
        if log_ratio > epsilon:
            count_violations += 1
            max_epsilon_seen = max(max_epsilon_seen, log_ratio)

    empirical_delta = count_violations / n_samples

    return {
        'target_epsilon': epsilon,
        'target_delta': delta,
        'sigma_used': sigma,
        'empirical_delta': empirical_delta,
        'is_verified': empirical_delta <= delta,
        'max_epsilon_seen': max_epsilon_seen
    }


def privacy_audit_membership_attack(dataset: np.ndarray,
                                      target_idx: int,
                                      mechanism_fn: Callable,
                                      epsilon: float,
                                      n_trials: int = 1000) -> dict:
    """
    成员关系攻击审计

    模拟攻击者尝试推断目标记录是否在数据集中。

    参数:
        dataset: 完整数据集
        target_idx: 目标记录索引
        mechanism_fn: 隐私机制
        epsilon: 隐私预算
        n_trials: 试验次数

    返回:
        攻击成功率等统计
    """
    target_record = dataset[target_idx]
    dataset_without = np.delete(dataset, target_idx)

    success_count = 0
    predictions = []

    for _ in range(n_trials):
        # 包含目标记录的输出
        output_with = mechanism_fn(dataset)

        # 不包含目标记录的输出
        output_without = mechanism_fn(dataset_without)

        # 攻击者决策（这里简化为比较）
        if abs(output_with.mean()) > abs(output_without.mean()):
            predictions.append(1)
            success_count += 1
        else:
            predictions.append(0)

    attack_success_rate = success_count / n_trials

    return {
        'epsilon': epsilon,
        'n_trials': n_trials,
        'attack_success_rate': attack_success_rate,
        'baseline_rate': 0.5,
        'advantage': attack_success_rate - 0.5,
        'is_secure': attack_success_rate < 0.51
    }


def sensitivity_verification(query_fn: Callable, d: int,
                              true_sensitivity: float,
                              n_tests: int = 1000) -> dict:
    """
    验证敏感度计算的正确性

    参数:
        query_fn: 查询函数
        d: 数据维度
        true_sensitivity: 真实敏感度
        n_tests: 测试次数

    返回:
        验证结果
    """
    max_diff = 0.0
    violations = 0

    for _ in range(n_tests):
        dataset = np.random.randint(0, 2, size=d)
        for i in range(d):
            neighbor = dataset.copy()
            neighbor[i] = 1 - neighbor[i]
            diff = abs(query_fn(dataset) - query_fn(neighbor))
            max_diff = max(max_diff, diff)
            if diff > true_sensitivity:
                violations += 1

    return {
        'true_sensitivity': true_sensitivity,
        'max_observed_diff': max_diff,
        'violation_rate': violations / (n_tests * d),
        'is_correct': max_diff <= true_sensitivity
    }


def compose_mechanism_verification(base_epsilon: float, n_compositions: int,
                                    delta: float = 1e-5,
                                    n_samples: int = 5000) -> dict:
    """
    验证组合机制的实际隐私损失

    参数:
        base_epsilon: 单次机制ε
        n_compositions: 组合次数
        delta: 目标δ
        n_samples: 样本数

    返回:
        验证结果
    """
    # 计算理论边界
    theoretical_eps = base_epsilon * n_compositions

    # 实际测量
    sigma = np.sqrt(2 * np.log(1.25 / delta)) / base_epsilon
    true_val = 0.0

    violations = 0
    for _ in range(n_samples):
        outputs = [np.random.normal(true_val, sigma) for _ in range(n_compositions)]
        composed = np.sum(outputs)
        # 检测隐私违反
        log_ratio = (composed**2) / (2 * sigma**2 * n_compositions)
        if log_ratio > theoretical_eps:
            violations += 1

    empirical_delta = violations / n_samples

    return {
        'base_epsilon': base_epsilon,
        'n_compositions': n_compositions,
        'theoretical_eps': theoretical_eps,
        'empirical_delta': empirical_delta,
        'is_verified': empirical_delta <= delta
    }


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私验证与审计测试")
    print("=" * 60)

    # 测试1：敏感度验证
    print("\n【测试1】敏感度验证")
    def test_query(x):
        return np.sum(x)

    result = sensitivity_verification(test_query, d=10, true_sensitivity=1.0, n_tests=500)
    print(f"  查询: sum(x)")
    print(f"  声明敏感度: {result['true_sensitivity']}")
    print(f"  最大观测差异: {result['max_observed_diff']:.1f}")
    print(f"  违规率: {result['violation_rate']:.4f}")
    print(f"  验证通过: {result['is_correct']}")

    # 测试2：高斯校准验证
    print("\n【测试2】高斯机制校准验证")
    result = gaussian_noise_calibration_verification(epsilon=2.0, delta=1e-5, n_samples=10000)
    print(f"  目标: ε=2.0, δ=1e-5")
    print(f"  使用σ: {result['sigma_used']:.4f}")
    print(f"  经验δ: {result['empirical_delta']:.6f}")
    print(f"  验证通过: {result['is_verified']}")

    # 测试3：组合验证
    print("\n【测试3】组合机制验证")
    for n_comp in [1, 5, 10, 20]:
        result = compose_mechanism_verification(base_epsilon=1.0, n_compositions=n_comp)
        print(f"  k={n_comp:2d}: 理论ε={result['theoretical_eps']:.2f}, "
              f"经验δ={result['empirical_delta']:.4f}, "
              f"通过={result['is_verified']}")

    # 测试4：成员攻击审计
    print("\n【测试4】成员关系攻击审计")
    dataset = np.random.randint(0, 100, size=100)
    target_idx = 50
    sigma = 2.0

    def simple_mechanism(data):
        return np.mean(data) + np.random.normal(0, sigma)

    result = privacy_audit_membership_attack(dataset, target_idx, simple_mechanism,
                                             epsilon=1.0, n_trials=500)
    print(f"  攻击成功率: {result['attack_success_rate']:.2%}")
    print(f"  基线成功率: {result['baseline_rate']:.2%}")
    print(f"  优势: {result['advantage']:.2%}")
    print(f"  安全: {result['is_secure']}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

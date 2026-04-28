# -*- coding: utf-8 -*-
"""
高斯机制校准模块

本模块实现高斯机制的噪声校准，包括：
- 标准差σ的精确选择
- 基于RDP的σ计算
- ZCDP下的σ选择
- 不同δ值对应的σ曲线

高斯机制是差分隐私中最常用的机制之一。

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import Tuple, Dict, Optional


def calibrate_gaussian_mechanism(epsilon: float, delta: float,
                                  sensitivity: float = 1.0,
                                  method: str = "rdp") -> float:
    """
    校准高斯机制的标准差σ

    参数:
        epsilon: 隐私预算ε
        delta: 失败概率δ
        sensitivity: 查询敏感度Δ
        method: 校准方法 ("rdp", "zcdp", "basic")

    返回:
        所需的高斯噪声标准差σ

    注意:
        - RDP方法提供最紧的边界
        - ZCDP方法介于RDP和基本方法之间
        - 基本方法使用标准转换但边界较松
    """
    if method == "rdp":
        # RDP到高斯的标准转换
        # σ = √(2 * log(1.25/δ)) * Δ / ε
        sigma = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / epsilon

    elif method == "zcdp":
        # ZCDP方法
        # ρ = ε²/2, then σ = Δ / √(2ρ)
        rho = epsilon**2 / 2
        sigma = sensitivity / np.sqrt(2 * rho)

    elif method == "basic":
        # 基本方法：使用标准高斯机制转换
        # ε(δ) = √(2σ² ln(1.25/δ)) / Δ
        # 解得 σ = ε * Δ / √(2 ln(1.25/δ))
        sigma = epsilon * sensitivity / np.sqrt(2 * np.log(1.25 / delta))

    else:
        raise ValueError(f"未知方法: {method}")

    return sigma


def gaussian_mechanism_sigma_curve(epsilon_range: np.ndarray,
                                    delta: float,
                                    sensitivity: float = 1.0) -> Dict[str, np.ndarray]:
    """
    计算ε-σ曲线（用于可视化权衡）

    参数:
        epsilon_range: ε值数组
        delta: 固定δ值
        sensitivity: 敏感度

    返回:
        包含各方法σ值的字典
    """
    sigma_rdp = []
    sigma_zcdp = []
    sigma_basic = []

    for eps in epsilon_range:
        sigma_rdp.append(calibrate_gaussian_mechanism(eps, delta, sensitivity, "rdp"))
        sigma_zcdp.append(calibrate_gaussian_mechanism(eps, delta, sensitivity, "zcdp"))
        sigma_basic.append(calibrate_gaussian_mechanism(eps, delta, sensitivity, "basic"))

    return {
        'epsilon': epsilon_range,
        'sigma_rdp': np.array(sigma_rdp),
        'sigma_zcdp': np.array(sigma_zcdp),
        'sigma_basic': np.array(sigma_basic)
    }


def sigma_for_target_utility(target_std: float,
                               sensitivity: float = 1.0,
                               confidence: float = 0.95) -> float:
    """
    根据目标效用（噪声标准差）反推所需隐私参数

    参数:
        target_std: 目标噪声标准差
        sensitivity: 敏感度
        confidence: 置信度（对应δ）

    返回:
        可达成的ε值
    """
    delta = 1 - confidence
    eps = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / target_std
    return eps


def compose_gaussian_noise(sigma1: float, sigma2: float) -> float:
    """
    组合两个高斯噪声源

    组合方差等于各方差之和。

    参数:
        sigma1: 第一个噪声的标准差
        sigma2: 第二个噪声的标准差

    返回:
        组合后的标准差
    """
    variance_sum = sigma1**2 + sigma2**2
    return np.sqrt(variance_sum)


def compose_k_gaussian_mechanisms(k: int, epsilon_k: float,
                                   delta: float,
                                   sensitivity: float = 1.0) -> float:
    """
    计算k次组合后保持目标ε所需的单次σ

    参数:
        k: 组合次数
        epsilon_k: 目标总ε
        delta: 失败概率
        sensitivity: 敏感度

    返回:
        单次机制所需的σ
    """
    # 使用RDP组合的反向计算
    # 总RDP = k * (1/(2σ²)) 对于α=2
    # 从DP边界反推
    eps_per_step = epsilon_k / np.sqrt(k)
    sigma_per_step = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / eps_per_step
    return sigma_per_step


def privacy_loss_from_sigma(sigma: float,
                             sensitivity: float = 1.0,
                             delta: float = 1e-5) -> Dict[str, float]:
    """
    从σ值反推隐私参数

    参数:
        sigma: 高斯噪声标准差
        sensitivity: 敏感度
        delta: 失败概率

    返回:
        包含隐私参数的字典
    """
    eps = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / sigma
    rho = sensitivity**2 / (2 * sigma**2)

    return {
        'epsilon': eps,
        'delta': delta,
        'zcdp_rho': rho,
        'sigma': sigma,
        'snr': sensitivity / sigma  # 信噪比
    }


if __name__ == "__main__":
    print("=" * 60)
    print("高斯机制校准测试")
    print("=" * 60)

    # 测试1：基本校准
    print("\n【测试1】高斯机制σ校准")
    epsilon = 2.0
    delta = 1e-5
    for method in ["rdp", "zcdp", "basic"]:
        sigma = calibrate_gaussian_mechanism(epsilon, delta, method=method)
        print(f"  ε={epsilon}, δ={delta}, 方法={method:6s} → σ={sigma:.4f}")

    # 测试2：ε-σ曲线数据
    print("\n【测试2】ε-σ曲线（部分）")
    eps_range = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    delta = 1e-5
    print(f"  δ={delta}")
    print(f"  {'ε':<8} {'σ(rdp)':<12} {'σ(zcdp)':<12} {'σ(basic)':<12}")
    print(f"  {'-'*45}")
    for eps in eps_range:
        sigma_rdp = calibrate_gaussian_mechanism(eps, delta, method="rdp")
        sigma_zcdp = calibrate_gaussian_mechanism(eps, delta, method="zcdp")
        sigma_basic = calibrate_gaussian_mechanism(eps, delta, method="basic")
        print(f"  {eps:<8.2f} {sigma_rdp:<12.4f} {sigma_zcdp:<12.4f} {sigma_basic:<12.4f}")

    # 测试3：从效用反推隐私
    print("\n【测试3】从目标效用反推ε")
    for target_std in [0.1, 0.5, 1.0, 2.0, 5.0]:
        eps = sigma_for_target_utility(target_std, 1.0, 0.95)
        print(f"  目标σ={target_std:.1f} → 可达ε={eps:.4f}")

    # 测试4：噪声组合
    print("\n【测试4】高斯噪声组合")
    sigma1 = 1.0
    sigma2 = 2.0
    sigma_combined = compose_gaussian_noise(sigma1, sigma2)
    print(f"  σ1={sigma1}, σ2={sigma2} → 组合σ={sigma_combined:.4f}")

    # 测试5：k次组合
    print("\n【测试5】k次组合所需的单次σ")
    epsilon_total = 8.0
    delta = 1e-5
    k_values = [1, 10, 50, 100, 500, 1000]
    print(f"  目标总ε={epsilon_total}, δ={delta}")
    print(f"  {'k':<8} {'单次σ':<12} {'等效单次ε':<12}")
    print(f"  {'-'*35}")
    for k in k_values:
        sigma = compose_k_gaussian_mechanisms(k, epsilon_total, delta)
        eps_single = np.sqrt(2 * np.log(1.25/delta)) / sigma
        print(f"  {k:<8} {sigma:<12.4f} {eps_single:<12.4f}")

    # 测试6：从σ反推隐私
    print("\n【测试6】从σ反推隐私参数")
    print(f"  {'σ':<10} {'ε':<12} {'ZCDP ρ':<12} {'信噪比':<10}")
    print(f"  {'-'*45}")
    for sigma in [0.5, 1.0, 2.0, 5.0, 10.0]:
        info = privacy_loss_from_sigma(sigma, 1.0, 1e-5)
        print(f"  {sigma:<10.2f} {info['epsilon']:<12.4f} {info['zcdp_rho']:<12.4f} {info['snr']:<10.4f}")

    # 测试7：不同δ对σ的影响
    print("\n【测试7】δ对σ的影响")
    epsilon = 2.0
    print(f"  ε={epsilon}")
    print(f"  {'δ':<12} {'σ':<12}")
    print(f"  {'-'*25}")
    for delta in [1e-3, 1e-5, 1e-7, 1e-9, 1e-11]:
        sigma = calibrate_gaussian_mechanism(epsilon, delta, method="rdp")
        print(f"  {delta:<12.1e} {sigma:<12.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

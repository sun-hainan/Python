# -*- coding: utf-8 -*-
"""
Rényi差分隐私（RDP）模块

本模块实现Rényi差分隐私的详细计算和转换。
RDP是一种更精细的隐私度量，比标准(ε,δ)-DP提供更紧的组合界。

核心概念：
- Rényi散度：一种广义的KL散度
- Rényi差分隐私：(α, ε)-RDP表示α阶Rényi散度
- RDP到(ε,δ)-DP的转换

作者：算法实现
版本：1.0
"""

import numpy as np
from scipy import special
from typing import List, Tuple, Optional


def rdp_gaussian_mechanism(alpha: float, sigma: float, sensitivity: float = 1.0) -> float:
    """
    高斯机制的Rényi差分隐私计算

    对于高斯机制 M(x) = f(x) + N(0, σ²)，RDP为：
    RDP(α || M(D), M(D')) = α * Δ² / (2σ²)  （近似）

    参数:
        alpha: Rényi阶数（α > 1）
        sigma: 高斯噪声标准差
        sensitivity: 函数敏感度Δ

    返回:
        RDP的ε值
    """
    if alpha < 1:
        raise ValueError("α必须 ≥ 1")
    if alpha == 1:
        # α=1时的极限（对应KL散度）
        return sensitivity**2 / (2 * sigma**2)
    else:
        # 标准RDP公式
        return alpha * sensitivity**2 / (2 * (alpha - 1) * sigma**2)


def rdp_laplace_mechanism(alpha: float, b: float, sensitivity: float = 1.0) -> float:
    """
    拉普拉斯机制的RDP计算

    参数:
        alpha: Rényi阶数
        b: 拉普拉斯尺度参数
        sensitivity: 敏感度

    返回:
        RDP的ε值
    """
    if alpha == 1:
        return sensitivity / b
    else:
        # 拉普拉斯机制的RDP闭式解
        term1 = (alpha / (alpha - 1)) * np.log(alpha / (2 * b + alpha))
        term2 = np.log(2 * b + alpha) - np.log(2 * b)
        return (term1 + term2) / (alpha - 1)


def compose_rdp(rdp_list: List[Tuple[float, float]]) -> float:
    """
    RDP组合：k个RDP机制的组合

    参数:
        rdp_list: RDP列表，每项为(α, ε)元组

    返回:
        组合后的RDP ε（假设相同α）
    """
    return sum(eps for _, eps in rdp_list)


def rdp_to_dp_convert(rdp_alpha: float, rdp_eps: float, delta: float) -> float:
    """
    将RDP转换为(ε,δ)-DP

    使用标准转换：ε = √(2ρ log(1/δ))，其中ρ = RDP(α) * α / (α-1)

    参数:
        rdp_alpha: RDP的α值
        rdp_eps: RDP的ε值
        delta: 目标δ

    返回:
        等效的ε值
    """
    # ZCDP的ρ值
    rho = rdp_eps * rdp_alpha / (2 * (rdp_alpha - 1))
    eps = np.sqrt(2 * rho * np.log(1.25 / delta))
    return eps


def optimal_alpha_selection(rdp_list: List[Tuple[float, float]],
                            delta: float) -> Tuple[float, float]:
    """
    选择最优α以获得最紧的DP边界

    参数:
        rdp_list: RDP列表
        delta: 目标δ

    返回:
        (最优α, 对应的ε值)
    """
    best_eps = float('inf')
    best_alpha = 2.0

    for alpha in np.linspace(1.1, 100, 100):
        total_rdp = sum(eps for a, eps in rdp_list if abs(a - alpha) < 0.1)
        eps_dp = rdp_to_dp_convert(alpha, total_rdp, delta)
        if eps_dp < best_eps:
            best_eps = eps_dp
            best_alpha = alpha

    return best_alpha, best_eps


def rdp_accountant_step(sigma: float, sensitivity: float = 1.0,
                        q: float = 1.0) -> List[Tuple[float, float]]:
    """
    单步RDP会计计算（用于DP-SGD）

    参数:
        sigma: 噪声标准差
        sensitivity: 敏感度
        q: 采样率（batch_size / dataset_size）

    返回:
        RDP列表 [(α, ε), ...]
    """
    rdp_results = []
    for alpha in [2, 4, 8, 16, 32, 64, float('inf')]:
        if alpha == float('inf'):
            eps = q**2 * sensitivity**2 / (2 * sigma**2)
        else:
            eps = rdp_gaussian_mechanism(alpha, sigma, sensitivity) * q**2
        rdp_results.append((alpha, eps))

    return rdp_results


def privacy_budget_from_rdp(total_rdp: Tuple[float, float],
                             delta: float,
                             method: str = "tight") -> dict:
    """
    从RDP计算隐私预算

    参数:
        total_rdp: 总RDP (α, ε)
        delta: 目标δ
        method: 转换方法

    返回:
        隐私参数字典
    """
    alpha, eps = total_rdp

    if method == "tight":
        eps_dp = rdp_to_dp_convert(alpha, eps, delta)
    else:
        # 松弛转换
        eps_dp = eps

    return {
        'alpha': alpha,
        'rdp_eps': eps,
        'epsilon': eps_dp,
        'delta': delta,
        'sigma_equiv': np.sqrt(alpha * eps / (2 * (alpha - 1))) if alpha > 1 else float('inf')
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Rényi差分隐私（RDP）测试")
    print("=" * 60)

    # 测试1：高斯机制RDP
    print("\n【测试1】高斯机制RDP")
    sigma = 2.0
    for alpha in [2, 4, 8, 16, 32]:
        eps = rdp_gaussian_mechanism(alpha, sigma)
        print(f"  α={alpha:3d}: RDP ε={eps:.4f}")

    # 测试2：RDP到DP转换
    print("\n【测试2】RDP到(ε,δ)-DP转换")
    delta = 1e-5
    print(f"  目标δ={delta}")
    print(f"  {'α':<8} {'RDP ε':<10} {'DP ε':<10}")
    print(f"  {'-'*30}")
    for alpha in [2, 4, 8, 16]:
        rdp_eps = rdp_gaussian_mechanism(alpha, sigma=2.0)
        dp_eps = rdp_to_dp_convert(alpha, rdp_eps, delta)
        print(f"  {alpha:<8} {rdp_eps:<10.4f} {dp_eps:<10.4f}")

    # 测试3：RDP组合
    print("\n【测试3】RDP组合")
    sigma_list = [1.0, 1.5, 2.0, 2.5, 3.0]
    alpha = 2.0
    total_rdp = sum(rdp_gaussian_mechanism(alpha, s) for s in sigma_list)
    print(f"  组合5个高斯机制:")
    print(f"  总RDP(α={alpha}): {total_rdp:.4f}")
    print(f"  等效(ε,δ=1e-5): ε={rdp_to_dp_convert(alpha, total_rdp, 1e-5):.4f}")

    # 测试4：最优α选择
    print("\n【测试4】最优α选择")
    rdp_list = [(2, 0.5), (4, 0.3), (8, 0.2), (16, 0.15)]
    best_alpha, best_eps = optimal_alpha_selection(rdp_list, 1e-5)
    print(f"  RDP列表: {rdp_list}")
    print(f"  最优α={best_alpha:.1f}, 对应ε={best_eps:.4f}")

    # 测试5：DP-SGD RDP会计
    print("\n【测试5】DP-SGD单步RDP")
    sigma = 1.0
    q = 0.01
    rdp_results = rdp_accountant_step(sigma, q=q)
    print(f"  σ={sigma}, q={q}")
    print(f"  {'α':<10} {'RDP ε':<12}")
    print(f"  {'-'*25}")
    for alpha, eps in rdp_results:
        alpha_str = "∞" if alpha == float('inf') else str(alpha)
        print(f"  {alpha_str:<10} {eps:<12.6f}")

    # 测试6：100步训练隐私会计
    print("\n【测试6】100步DP-SGD训练隐私会计")
    n_steps = 100
    sigma = 1.0
    q = 0.01

    total_rdp_alpha2 = 0.0
    for step in range(n_steps):
        rdp = rdp_gaussian_mechanism(2.0, sigma) * q**2
        total_rdp_alpha2 += rdp

    print(f"  总RDP(α=2): {total_rdp_alpha2:.4f}")
    print(f"  等效(ε,δ=1e-5): ε={rdp_to_dp_convert(2.0, total_rdp_alpha2, 1e-5):.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

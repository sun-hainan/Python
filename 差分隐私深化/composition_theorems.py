# -*- coding: utf-8 -*-
"""
差分隐私组合定理模块

本模块实现差分隐私的组合定理，用于：
- 基本组合定理：k次查询后总隐私损失为kε
- 高级组合定理：更严格的多查询组合界
- 强组合定理：用于序列查询的最强保证

组合定理是隐私会计的核心基础。

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import List, Tuple, Dict


def basic_composition(eps_list: List[float], delta_list: List[float]) -> Tuple[float, float]:
    """
    基本组合定理（Basic Composition）

    对于k个独立的(ε_i, δ_i)-DP机制，组合后仍是差分隐私：
    (Σ ε_i, Σ δ_i)

    参数:
        eps_list: 各机制的ε值列表
        delta_list: 各机制的δ值列表

    返回:
        (组合ε, 组合δ)
    """
    total_eps = sum(eps_list)
    total_delta = sum(delta_list)
    return total_eps, total_delta


def advanced_composition(eps_list: List[float], delta: float = 1e-5,
                          delta_decay: float = 0.0) -> Tuple[float, float]:
    """
    高级组合定理（Advanced Composition）

    使用RDP或ZCDP实现比基本组合更严格的上界。
    隐私损失的增长速度从O(kε)降到O(√k ε)。

    参数:
        eps_list: 各机制的ε值列表
        delta: 目标失败概率δ
        delta_decay: δ的衰减参数（高级选项）

    返回:
        (组合ε, 实际δ)
    """
    k = len(eps_list)  # 查询次数

    # 计算总隐私损失
    # 使用ZCDP组合：ρ = Σ ρ_i，ε ≤ √(2ρ log(1/δ))
    total_rho = sum(eps_i**2 / 2 for eps_i in eps_list)
    eps_composed = np.sqrt(2 * total_rho * np.log(1.0 / delta))

    # 调整δ（考虑衰减）
    if delta_decay > 0:
        actual_delta = delta + k * delta_decay
    else:
        actual_delta = delta

    return eps_composed, actual_delta


def strong_composition(eps_list: List[float], delta: float,
                         k: int = None) -> Tuple[float, float]:
    """
    强组合定理（Strong Composition）

    用于处理k次自适应查询的最强组合界。
    隐私损失增长为O(log(k) ε)。

    参数:
        eps_list: 各机制的ε值列表
        delta: 目标失败概率
        k: 查询次数（如果为None则使用len(eps_list)）

    返回:
        (组合ε, 组合δ)
    """
    if k is None:
        k = len(eps_list)

    # 强组合上界
    eps_i = eps_list[0] if eps_list else 0.0
    eps_composed = (k * eps_i + eps_i**2 * np.log(k) / (2 * np.log(1.0 / delta)))**0.5
    eps_composed = eps_i * np.sqrt(k) + eps_i * np.sqrt(np.log(1.0 / delta)) / 2

    return eps_composed, delta * k


def rdp_composition(rdp_list: List[Tuple[float, float]]) -> float:
    """
    RDP组合定理

    直接在Rényi差分隐私域进行组合，无需转换回DP域。

    参数:
        rdp_list: RDP列表，每项为(α, ε)元组

    返回:
        组合后的RDP ε值（假设相同α）
    """
    if not rdp_list:
        return 0.0

    alpha = rdp_list[0][0]
    total_rdp = sum(eps for _, eps in rdp_list)

    return total_rdp


def zcdp_composition(rho_list: List[float]) -> float:
    """
    ZCDP组合定理

    在零集中差分隐私域进行组合，组合后ρ = Σ ρ_i。

    参数:
        rho_list: 各机制的ZCDP ρ值列表

    返回:
        组合后的ZCDP ρ值
    """
    return sum(rho_list)


def convert_zcdp_to_dp(rho: float, delta: float) -> float:
    """
    将ZCDP参数转换为标准(ε, δ)-DP参数

    参数:
        rho: ZCDP的ρ值
        delta: 目标失败概率δ

    返回:
        等效的ε值
    """
    eps = np.sqrt(2 * rho * np.log(1.25 / delta))
    return eps


def convert_rdp_to_zcdp(alpha: float, eps: float) -> float:
    """
    将RDP参数转换为ZCDP参数

    参数:
        alpha: Rényi阶数
        eps: RDP的ε值

    返回:
        ZCDP的ρ值
    """
    return eps**2 / (2 * alpha)


def optimal_eps_selection(target_delta: float, n_queries: int,
                            base_eps: float = 1.0,
                            method: str = "advanced") -> Dict[str, float]:
    """
    最优ε选择：根据查询次数和目标δ选择最优隐私参数

    参数:
        target_delta: 目标失败概率δ
        n_queries: 查询次数k
        base_eps: 基础ε值
        method: 组合方法 ("basic", "advanced", "strong")

    返回:
        包含参数的字典
    """
    if method == "basic":
        per_query_eps = target_delta / n_queries
        total_eps = sum([base_eps] * n_queries)
    elif method == "advanced":
        total_rho = 0.0
        per_query_rho = base_eps**2 / 2
        total_rho = n_queries * per_query_rho
        total_eps = np.sqrt(2 * total_rho * np.log(1.0 / target_delta))
        per_query_eps = total_eps / np.sqrt(n_queries)
    else:
        total_eps = base_eps * np.sqrt(n_queries)
        per_query_eps = base_eps

    return {
        'total_eps': total_eps,
        'per_query_eps': per_query_eps,
        'n_queries': n_queries,
        'delta': target_delta,
        'method': method
    }


def composition_bound_compare(n_queries: int, per_query_eps: float,
                               delta: float = 1e-5) -> Dict[str, float]:
    """
    比较三种组合定理的边界

    参数:
        n_queries: 查询次数k
        per_query_eps: 每次查询的ε值
        delta: 失败概率δ

    返回:
        各方法组合ε的字典
    """
    eps_list = [per_query_eps] * n_queries

    basic_eps, _ = basic_composition(eps_list, [delta] * n_queries)
    advanced_eps, _ = advanced_composition(eps_list, delta)
    strong_eps, _ = strong_composition(eps_list, delta, n_queries)

    return {
        'basic': basic_eps,
        'advanced': advanced_eps,
        'strong': strong_eps,
        'ratio_advanced_vs_basic': advanced_eps / basic_eps,
        'ratio_strong_vs_basic': strong_eps / basic_eps
    }


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私组合定理测试")
    print("=" * 60)

    # 测试1：基本组合
    print("\n【测试1】基本组合定理")
    eps_list = [1.0, 1.0, 1.0, 1.0, 1.0]
    delta_list = [1e-5] * 5
    total_eps, total_delta = basic_composition(eps_list, delta_list)
    print(f"  5次ε=1.0查询:")
    print(f"  组合后 (ε={total_eps}, δ={total_delta})")

    # 测试2：高级组合
    print("\n【测试2】高级组合定理")
    advanced_eps, _ = advanced_composition(eps_list, delta=1e-5)
    print(f"  5次ε=1.0查询:")
    print(f"  高级组合后 ε={advanced_eps:.4f}")
    print(f"  节省比例: {(1 - advanced_eps/5.0)*100:.1f}%")

    # 测试3：不同查询次数下的组合比较
    print("\n【测试3】不同查询次数的组合比较")
    print(f"  {'k':<5} {'基本组合':<12} {'高级组合':<12} {'强组合':<12}")
    print(f"  {'-'*45}")
    for k in [1, 5, 10, 20, 50, 100]:
        eps_l = [1.0] * k
        basic_e, _ = basic_composition(eps_l, [1e-5]*k)
        advanced_e, _ = advanced_composition(eps_l, 1e-5)
        strong_e, _ = strong_composition(eps_l, 1e-5, k)
        print(f"  {k:<5} {basic_e:<12.2f} {advanced_e:<12.2f} {strong_e:<12.2f}")

    # 测试4：最优ε选择
    print("\n【测试4】最优ε选择")
    for method in ["basic", "advanced", "strong"]:
        result = optimal_eps_selection(target_delta=1e-5, n_queries=100,
                                       base_eps=1.0, method=method)
        print(f"  {method:8s}: 总ε={result['total_eps']:.4f}, "
              f"单次ε={result['per_query_eps']:.4f}")

    # 测试5：ZCDP转换
    print("\n【测试5】ZCDP与DP转换")
    rho = 2.0
    delta = 1e-5
    eps_from_zcdp = convert_zcdp_to_dp(rho, delta)
    print(f"  ZCDP ρ={rho} → (ε={eps_from_zcdp:.4f}, δ={delta})")

    # 测试6：RDP转换
    print("\n【测试6】RDP与ZCDP转换")
    alpha = 10.0
    eps_rdp = 1.0
    rho_from_rdp = convert_rdp_to_zcdp(alpha, eps_rdp)
    print(f"  RDP(α={alpha}, ε={eps_rdp}) → ZCDP ρ={rho_from_rdp:.4f}")

    # 测试7：组合边界对比
    print("\n【测试7】组合定理对比（k=100, ε=1.0）")
    compare = composition_bound_compare(100, 1.0, 1e-5)
    print(f"  基本组合 ε: {compare['basic']:.2f}")
    print(f"  高级组合 ε: {compare['advanced']:.4f} (节省{compare['ratio_advanced_vs_basic']*100:.1f}%)")
    print(f"  强组合 ε: {compare['strong']:.4f} (节省{compare['ratio_strong_vs_basic']*100:.1f}%)")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

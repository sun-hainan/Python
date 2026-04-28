# -*- coding: utf-8 -*-
"""
差分隐私隐私会计模块

本模块实现差分隐私中的隐私会计（Privacy Accounting）机制，用于：
- 跟踪复合查询的累积隐私损失
- 计算Rényi差分隐私（RDP）
- 零集中差分隐私（ZCDP）
- 隐私损失单参数表示

隐私会计是实际部署差分隐私系统的核心组件。

作者：算法实现
版本：1.0
"""

import numpy as np  # 数值计算库
from typing import List, Tuple, Optional  # 类型提示
from scipy import special  # 特殊数学函数


def rdp_to_gaussian_mechanism(rdp_eps: float, delta: float) -> float:
    """
    将Rényi差分隐私(RDP)参数转换为纯高斯机制参数

    基于高斯机制的标准差σ，使得组合RDP实现(ε,δ)-DP。

    参数:
        rdp_eps: RDP的ε值
        delta: 目标失败概率δ

    返回:
        所需高斯噪声标准差σ（相对于敏感度）

    公式: σ = √(2 * log(1.25/δ)) * (Δ² / RDP_ε)
    """
    if rdp_eps <= 0:
        raise ValueError("RDP ε 必须为正数")
    if delta <= 0 or delta >= 1:
        raise ValueError("δ 必须满足 0 < δ < 1")

    # 标准转换公式：σ = √(2 * log(1.25/δ)) / ε
    # 对于单位敏感度的情况
    sigma = np.sqrt(2 * np.log(1.25 / delta)) / rdp_eps
    return sigma


def compose_rdp_basic(queries_info: List[Tuple[float, float]]) -> float:
    """
    基本RDP组合定理

    对于k个独立查询的组合，总RDP等于各个RDP之和。

    参数:
        queries_info: 查询列表，每个元素为(α, ε)元组
                     其中α是Rényi阶数，ε是对应的隐私参数

    返回:
        组合后的总RDP ε值（针对给定的α）

    注意:
        组合定理假设所有查询使用相同的α进行组合。
        如果α不同，需要分别处理或取上界。
    """
    total_eps = 0.0
    for alpha, eps in queries_info:
        total_eps += eps
    return total_eps


def compose_rdp_advanced(alpha: float, 
                          mechanism_params: List[Tuple[str, float, float]]) -> float:
    """
    高级RDP组合定理

    支持不同机制（高斯、拉普拉斯等）的RDP组合。

    参数:
        alpha: Rényi阶数
        mechanism_params: 机制参数列表，每项为(机制名, 参数1, 参数2)
                         - ("gaussian", σ, q): q是采样率（对于AMP）
                         - ("laplace", b, ): 拉普拉斯尺度参数b

    返回:
        组合后的RDP ε值
    """
    total_rdp = 0.0

    for mech_type, *params in mechanism_params:
        if mech_type == "gaussian":
            sigma, q = params[0], params[1]
            # 高斯机制的RDP计算
            # RDP(α) = (1/(α-1)) * log(∑_z exp(α*(μ(x,z)-1) + (α-1)*σ²*μ(x,z)²))
            # 简化版本假设输出分布
            if alpha == 1:
                # α=1时的极限情况
                rdp = params[0]  # 需要特殊处理
            else:
                # 高斯机制RDP上界
                rdp = alpha * q**2 * sigma**2 / (2 * (alpha - 1))
            total_rdp += rdp

        elif mech_type == "laplace":
            b = params[0]
            # 拉普拉斯机制的RDP
            # 对于α阶Rényi散度
            if alpha == 1:
                rdp = 1.0 / b
            else:
                rdp = (alpha / b - np.log(alpha / (2 * b + alpha))) / (alpha - 1)
            total_rdp += rdp

    return total_rdp


def zcdp_from_rdp(rdp_alpha: float, rdp_eps: float) -> float:
    """
    从RDP参数计算零集中差分隐私(ZCDP)参数

    ZCDP使用集中差分隐私的变种，通过限制高阶 моментов 来实现。
    RDP可以直接转换为ZCDP。

    参数:
        rdp_alpha: Rényi阶数α
        rdp_eps: 对应的RDP ε值

    返回:
        ZCDP的ρ值（集中差分隐私参数）

    关系:
        ZCDP的ρ等价于在α→∞时的RDP
        实际使用中，取α足够大时的RDP作为ZCDP上界
    """
    # ZCDP ρ ≈ (ε²) / (2 * log(1/δ)) 在某些转换下
    # 简化：使用α足够大时的估计
    zcdp_rho = (rdp_eps ** 2) / (2 * rdp_alpha)
    return zcdp_rho


def privacy_loss_single_parameter(eps: float, delta: float,
                                  mechanism: str = "gaussian") -> dict:
    """
    计算隐私损失单参数表示

    将差分隐私参数统一为单个可比较的度量。
    支持不同机制间的效用比较。

    参数:
        eps: (ε, δ)-DP的ε值
        delta: (ε, δ)-DP的δ值
        mechanism: 机制类型 ("gaussian", "laplace", "exponential")

    返回:
        包含各种隐私参数的字典

    返回值结构:
        {
            'epsilon': eps,           # 原始ε
            'delta': delta,            # 原始δ
            'sigma_equiv': sigma,      # 等效高斯σ
            'rdp_alpha': alpha_opt,    # 最优RDP阶数α*
            'rdp_eps': rdp_opt,        # 最优RDP ε
            'zcdp_rho': zcdp_rho,      # ZCDP ρ
            'privacy_budget_used': budget  # 隐私预算消耗
        }
    """
    result = {
        'epsilon': eps,
        'delta': delta,
        'mechanism': mechanism
    }

    # 计算等效高斯噪声标准差
    if mechanism == "gaussian":
        sigma = rdp_to_gaussian_mechanism(eps, delta)
        result['sigma_equiv'] = sigma
    else:
        # 简化处理
        result['sigma_equiv'] = 1.0 / eps

    # 计算最优RDP（这里简化为eps本身作为上界）
    alpha_opt = 2.0  # 默认使用α=2
    rdp_opt = eps
    result['rdp_alpha'] = alpha_opt
    result['rdp_eps'] = rdp_opt

    # 计算ZCDP
    zcdp_rho = zcdp_from_rdp(alpha_opt, rdp_opt)
    result['zcdp_rho'] = zcdp_rho

    # 隐私预算消耗（归一化度量）
    budget = eps * np.sqrt(-np.log(delta))
    result['privacy_budget_used'] = budget

    return result


def compose_gaussian_mechanisms(sigma_list: List[float],
                                 delta: float = 1e-5) -> Tuple[float, float]:
    """
    高斯机制组合：计算k个高斯机制组合后的(ε, δ)参数

    参数:
        sigma_list: 各机制的高斯噪声标准差列表
        delta: 目标失败概率δ

    返回:
        (组合ε, 实际δ)
    """
    # 使用RDP组合定理
    alpha = 2  # 使用α=2进行组合（常见选择）
    total_rdp = 0.0

    for sigma in sigma_list:
        # α=2时的高斯机制RDP
        rdp_i = 1.0 / (2 * sigma**2)
        total_rdp += rdp_i

    # 计算ZCDP ρ
    rho = total_rdp

    # 从ZCDP转换回(ε, δ)-DP
    # 使用标准转换：ε = √(2ρ * log(1/δ))
    eps_composed = np.sqrt(2 * rho * np.log(1.0 / delta))

    return eps_composed, delta


def advanced_accounting(queries: List[dict],
                        target_delta: float = 1e-5) -> dict:
    """
    高级隐私会计：同时追踪多种隐私度量

    参数:
        queries: 查询列表，每个查询包含:
                - 'type': 机制类型 ("gaussian", "laplace", etc.)
                - 'params': 机制参数
                - 'count': 查询次数
        target_delta: 目标失败概率δ

    返回:
        包含所有隐私度量的字典
    """
    # 初始化累积隐私损失
    total_rdp_alpha2 = 0.0  # α=2时的RDP累积
    total_rdp_alpha_inf = 0.0  # α→∞时的RDP（ZCDP）

    for query in queries:
        mech_type = query['type']
        params = query['params']
        count = query.get('count', 1)

        for _ in range(count):
            if mech_type == "gaussian":
                sigma = params['sigma']
                # α=2时的RDP
                rdp_alpha2 = 1.0 / (2 * sigma**2)
                # α→∞时的RDP（ZCDP ρ）
                rdp_alpha_inf = 1.0 / (2 * sigma**2)
                total_rdp_alpha2 += rdp_alpha2
                total_rdp_alpha_inf += rdp_alpha_inf

            elif mech_type == "laplace":
                b = params['b']
                # 拉普拉斯机制的RDP
                rdp_alpha2 = (2 / b - np.log(2 / (2*b + 2)))  # α=2特例
                total_rdp_alpha2 += rdp_alpha2
                total_rdp_alpha_inf += rdp_alpha2

    # 计算最终隐私参数
    eps_from_rdp = np.sqrt(2 * total_rdp_alpha2 * np.log(1.0 / target_delta))
    rho = total_rdp_alpha_inf

    return {
        'total_rdp_alpha2': total_rdp_alpha2,
        'total_rdp_alpha_inf': total_rdp_alpha_inf,
        'eps_equiv': eps_from_rdp,
        'zcdp_rho': rho,
        'delta': target_delta,
        'compose_count': sum(q['count'] for q in queries)
    }


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私隐私会计测试")
    print("=" * 60)

    # 测试1：RDP转高斯机制
    print("\n【测试1】RDP转高斯机制参数")
    rdp_eps = 2.0
    delta = 1e-5
    sigma = rdp_to_gaussian_mechanism(rdp_eps, delta)
    print(f"  RDP ε = {rdp_eps}")
    print(f"  目标 δ = {delta}")
    print(f"  等效高斯 σ = {sigma:.4f}")

    # 测试2：基本RDP组合
    print("\n【测试2】基本RDP组合")
    queries_info = [(2, 0.5), (2, 0.3), (2, 0.8)]
    total_rdp = compose_rdp_basic(queries_info)
    print(f"  查询列表: {queries_info}")
    print(f"  组合后 RDP ε: {total_rdp}")

    # 测试3：高级RDP组合
    print("\n【测试3】高级RDP组合（多机制）")
    mechanism_params = [
        ("gaussian", 2.0, 0.01),  # (σ, q)
        ("gaussian", 3.0, 0.02),
        ("laplace", 1.0),
    ]
    total_rdp_advanced = compose_rdp_advanced(alpha=2.0, mechanism_params=mechanism_params)
    print(f"  机制参数: {mechanism_params}")
    print(f"  组合后 RDP ε: {total_rdp_advanced:.4f}")

    # 测试4：ZCDP转换
    print("\n【测试4】RDP转ZCDP")
    rdp_alpha = 10.0
    rdp_eps_val = 1.0
    zcdp_rho = zcdp_from_rdp(rdp_alpha, rdp_eps_val)
    print(f"  RDP (α={rdp_alpha}, ε={rdp_eps_val})")
    print(f"  ZCDP ρ = {zcdp_rho:.4f}")

    # 测试5：隐私损失单参数
    print("\n【测试5】隐私损失单参数表示")
    params_list = [
        (1.0, 1e-5, "gaussian"),
        (2.0, 1e-5, "laplace"),
        (3.0, 1e-5, "gaussian"),
    ]
    for eps, delta, mech in params_list:
        result = privacy_loss_single_parameter(eps, delta, mech)
        print(f"  {mech:8s} (ε={eps}, δ={delta}): σ等效={result['sigma_equiv']:.4f}, "
              f"预算={result['privacy_budget_used']:.4f}")

    # 测试6：高斯机制组合
    print("\n【测试6】高斯机制组合")
    sigma_list = [1.0, 1.5, 2.0, 2.5]
    delta_target = 1e-5
    eps_composed, delta_actual = compose_gaussian_mechanisms(sigma_list, delta_target)
    print(f"  σ列表: {sigma_list}")
    print(f"  组合后 (ε={eps_composed:.4f}, δ={delta_actual})")

    # 测试7：高级隐私会计
    print("\n【测试7】高级隐私会计")
    queries = [
        {'type': 'gaussian', 'params': {'sigma': 2.0}, 'count': 5},
        {'type': 'laplace', 'params': {'b': 1.0}, 'count': 3},
        {'type': 'gaussian', 'params': {'sigma': 1.5}, 'count': 2},
    ]
    accounting = advanced_accounting(queries, target_delta=1e-5)
    print(f"  查询统计: {sum(q['count'] for q in queries)}次查询")
    print(f"  RDP(α=2)累积: {accounting['total_rdp_alpha2']:.4f}")
    print(f"  ZCDP ρ累积: {accounting['total_rdp_alpha_inf']:.4f}")
    print(f"  等效ε: {accounting['eps_equiv']:.4f}")

    # 测试8：隐私预算消耗对比
    print("\n【测试8】隐私预算消耗对比")
    budgets = []
    for i in range(1, 11):
        sigma = i * 0.5
        result = privacy_loss_single_parameter(1.0/sigma, 1e-5, "gaussian")
        budgets.append(result['privacy_budget_used'])

    print(f"  {'σ':<8} {'ε':<8} {'预算消耗':<12}")
    print(f"  {'-'*30}")
    for i, sigma in enumerate([i*0.5 for i in range(1, 11)]):
        print(f"  {sigma:<8.1f} {1.0/sigma:<8.2f} {budgets[i]:<12.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

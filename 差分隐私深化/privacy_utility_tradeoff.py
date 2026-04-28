# -*- coding: utf-8 -*-
"""
差分隐私隐私-效用权衡分析模块

本模块分析和可视化差分隐私中的核心权衡：
- 隐私保护程度（ε, δ）与数据效用（准确性）之间的矛盾
- 噪声规模对统计估计精度的影响
- 最优隐私参数选择策略

核心概念：
- 效用函数：衡量发布结果有用程度的函数
- 隐私损失：攻击者可区分相邻数据集的能力度量
- 权衡曲线：Pareto最优前沿

作者：算法实现
版本：1.0
"""

import numpy as np  # 数值计算库
from typing import Callable, List, Tuple, Dict  # 类型提示
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt  # 绑定绘图库


def compute_utility_loss(noisy_value: float, true_value: float,
                          metric: str = "mse") -> float:
    """
    计算隐私发布结果的效用损失

    参数:
        noisy_value: 带噪声的发布值
        true_value: 真实值（ground truth）
        metric: 损失度量类型 ("mse", "mae", "relative")

    返回:
        效用损失值（越低越好）
    """
    diff = noisy_value - true_value  # 差值

    if metric == "mse":
        loss = diff ** 2  # 均方误差
    elif metric == "mae":
        loss = abs(diff)  # 平均绝对误差
    elif metric == "relative":
        loss = abs(diff) / (abs(true_value) + 1e-10)  # 相对误差
    else:
        raise ValueError(f"未知的度量类型: {metric}")

    return loss


def privacy_utility_curve(epsilon_range: np.ndarray,
                           sensitivity: float,
                           sample_size: int,
                           mechanism: str = "laplace") -> Tuple[np.ndarray, np.ndarray]:
    """
    计算隐私-效用权衡曲线

    参数:
        epsilon_range: ε值范围数组
        sensitivity: 查询敏感度Δ
        sample_size: 样本数量n
        mechanism: 噪声机制 ("laplace", "gaussian")

    返回:
        (隐私值数组, 效用损失数组)
    """
    utility_losses = []  # 效用损失列表

    for eps in epsilon_range:
        # 计算噪声标准差
        if mechanism == "laplace":
            scale = sensitivity / eps  # 拉普拉斯参数b
            expected_noise_variance = 2 * scale ** 2  # 拉普拉斯方差
        else:  # gaussian
            sigma = sensitivity * np.sqrt(2 * np.log(1.25 / 1e-5)) / eps
            expected_noise_variance = sigma ** 2

        # 效用损失与噪声方差成正比
        # 对于均值查询，损失 ≈ 噪声方差 / n
        loss = expected_noise_variance / sample_size
        utility_losses.append(loss)

    return epsilon_range, np.array(utility_losses)


def optimal_epsilon_for_budget(utility_budget: float,
                                sensitivity: float,
                                sample_size: int,
                                delta: float = 1e-5) -> float:
    """
    在给定效用预算下计算最优隐私参数ε

    参数:
        utility_budget: 可容忍的最大效用损失
        sensitivity: 查询敏感度
        sample_size: 样本数量
        delta: 失败概率

    返回:
        最优ε值
    """
    # 从效用约束反推ε
    # 效用损失 = (Δ² * σ²) / n，σ = Δ * √(2log(1.25/δ)) / ε
    # 损失 = Δ² * (Δ² * 2log(1.25/δ) / ε²) / n

    log_term = 2 * np.log(1.25 / delta)
    epsilon = sensitivity * np.sqrt(log_term / (sample_size * utility_budget))
    return epsilon


def pareto_front_tradeoff(epsilon_range: np.ndarray,
                           utility_losses: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    提取Pareto最优前沿

    参数:
        epsilon_range: ε值数组
        utility_losses: 对应的效用损失数组

    返回:
        (Pareto最优ε, Pareto最优损失)
    """
    pareto_eps = []  # Pareto最优ε
    pareto_losses = []  # Pareto最优损失

    min_loss = float('inf')
    for eps, loss in zip(epsilon_range, utility_losses):
        # 寻找Pareto前沿点（不被其他点支配）
        if loss < min_loss:
            pareto_eps.append(eps)
            pareto_losses.append(loss)
            min_loss = loss

    return np.array(pareto_eps), np.array(pareto_losses)


def compose_utility_degradation(base_utility: float,
                                 n_queries: int,
                                 composition_method: str = "basic") -> float:
    """
    计算多查询组合对效用的影响

    参数:
        base_utility: 单次查询的基础效用（0-1）
        n_queries: 查询数量
        composition_method: 组合方法 ("basic", "advanced", "strong")

    返回:
        组合后的效用值
    """
    if composition_method == "basic":
        # 基本组合：效用线性下降
        degraded_utility = base_utility / n_queries

    elif composition_method == "advanced":
        # 高级组合：使用RDP，比基本组合更紧
        # 效用下降与√k成正比（高斯机制）
        degraded_utility = base_utility / np.sqrt(n_queries)

    elif composition_method == "strong":
        # 强组合：效用下降与log(k)成正比
        degraded_utility = base_utility / np.log(n_queries + 1)

    else:
        raise ValueError(f"未知的组合方法: {composition_method}")

    return degraded_utility


def privacy_utility_ratio(epsilon: float, utility_score: float) -> float:
    """
    计算隐私-效用比（Privacy-Utility Ratio）

    用于衡量单位隐私损失对应的效用收益。

    参数:
        epsilon: 隐私预算ε
        utility_score: 效用分数（0-1，越高越好）

    返回:
        隐私-效用比（越高越差）
    """
    if utility_score <= 0:
        return float('inf')
    return epsilon / utility_score


def monte_carlo_utility_estimation(true_value: float,
                                    sensitivity: float,
                                    epsilon: float,
                                    n_trials: int = 10000,
                                    mechanism: str = "laplace") -> Dict[str, float]:
    """
    蒙特卡洛估计效用分布

    通过多次采样噪声来估计效用分布的统计量。

    参数:
        true_value: 真实查询值
        sensitivity: 查询敏感度
        epsilon: 隐私预算
        n_trials: 蒙特卡洛试验次数
        mechanism: 噪声机制

    返回:
        包含统计量的字典
    """
    noisy_values = []  # 噪声发布值列表

    if mechanism == "laplace":
        scale = sensitivity / epsilon
        for _ in range(n_trials):
            noise = np.random.laplace(0, scale)
            noisy_values.append(true_value + noise)
    else:
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / 1e-5)) / epsilon
        for _ in range(n_trials):
            noise = np.random.normal(0, sigma)
            noisy_values.append(true_value + noise)

    noisy_values = np.array(noisy_values)

    return {
        'mean': np.mean(noisy_values),  # 均值（期望无偏）
        'std': np.std(noisy_values),  # 标准差
        'mse': np.mean((noisy_values - true_value) ** 2),  # 均方误差
        'mae': np.mean(np.abs(noisy_values - true_value)),  # 平均绝对误差
        'bias': np.mean(noisy_values - true_value),  # 偏置
        'median_mse': np.median((noisy_values - true_value) ** 2),  # 中位数MSE
    }


def trade_off_analysis_report(epsilons: np.ndarray,
                              sensitivity: float,
                              sample_size: int,
                              true_values: np.ndarray) -> str:
    """
    生成隐私-效用权衡分析报告

    参数:
        epsilons: ε值数组
        sensitivity: 敏感度
        sample_size: 样本量
        true_values: 真实值数组

    返回:
        格式化报告字符串
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("隐私-效用权衡分析报告")
    report_lines.append("=" * 60)

    report_lines.append(f"\n基础参数:")
    report_lines.append(f"  敏感度 Δ = {sensitivity}")
    report_lines.append(f"  样本量 n = {sample_size}")
    report_lines.append(f"  查询数量 m = {len(true_values)}")

    report_lines.append(f"\n{'ε':<10} {'噪声σ':<10} {'MSE':<12} {'RMSE':<10} {'效用分数':<10}")
    report_lines.append("-" * 55)

    for eps in epsilons:
        scale = sensitivity / eps
        sigma = scale * np.sqrt(2)
        mse_expected = sigma ** 2 / sample_size
        rmse = np.sqrt(mse_expected)
        utility_score = 1.0 / (1.0 + rmse)

        report_lines.append(f"{eps:<10.2f} {sigma:<10.3f} {mse_expected:<12.6f} "
                           f"{rmse:<10.4f} {utility_score:<10.4f}")

    report_lines.append("\n" + "=" * 60)

    return "\n".join(report_lines)


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私隐私-效用权衡分析测试")
    print("=" * 60)

    # 测试1：基本权衡曲线
    print("\n【测试1】隐私-效用权衡曲线")
    epsilon_range = np.linspace(0.1, 5.0, 50)
    sensitivity = 1.0  # 敏感度Δ=1
    sample_size = 1000  # 样本量n=1000

    eps_lap, losses_lap = privacy_utility_curve(epsilon_range, sensitivity,
                                                  sample_size, "laplace")
    eps_gau, losses_gau = privacy_utility_curve(epsilon_range, sensitivity,
                                                  sample_size, "gaussian")

    print(f"  ε范围: [{epsilon_range.min():.1f}, {epsilon_range.max():.1f}]")
    print(f"  拉普拉斯机制效用损失范围: [{losses_lap.min():.6f}, {losses_lap.max():.6f}]")
    print(f"  高斯机制效用损失范围: [{losses_gau.min():.6f}, {losses_gau.max():.6f}]")

    # 测试2：Pareto前沿
    print("\n【测试2】Pareto最优前沿提取")
    pareto_eps, pareto_losses = pareto_front_tradeoff(eps_lap, losses_lap)
    print(f"  Pareto前沿点数: {len(pareto_eps)}")
    print(f"  Pareto前沿点示例:")
    for i in range(0, len(pareto_eps), max(1, len(pareto_eps)//5)):
        print(f"    ε={pareto_eps[i]:.2f}, 损失={pareto_losses[i]:.6f}")

    # 测试3：最优ε计算
    print("\n【测试3】效用预算约束下的最优ε")
    for utility_budget in [0.01, 0.05, 0.1, 0.5]:
        opt_eps = optimal_epsilon_for_budget(utility_budget, sensitivity=1.0,
                                              sample_size=1000, delta=1e-5)
        print(f"  效用预算={utility_budget:.2f} → 最优ε={opt_eps:.4f}")

    # 测试4：蒙特卡洛效用估计
    print("\n【测试4】蒙特卡洛效用估计")
    true_val = 100.0
    mc_stats = monte_carlo_utility_estimation(true_val, sensitivity=1.0,
                                                epsilon=1.0, n_trials=10000,
                                                mechanism="laplace")
    print(f"  真实值: {true_val}")
    print(f"  估计均值: {mc_stats['mean']:.4f} (偏置={mc_stats['bias']:.4f})")
    print(f"  标准差: {mc_stats['std']:.4f}")
    print(f"  MSE: {mc_stats['mse']:.4f}")
    print(f"  MAE: {mc_stats['mae']:.4f}")

    # 测试5：多查询组合效用降解
    print("\n【测试5】多查询组合效用降解")
    base_utility = 1.0
    query_counts = [1, 5, 10, 20, 50, 100]
    print(f"  基础效用: {base_utility}")
    print(f"  {'查询数':<10} {'基本组合':<15} {'高级组合':<15} {'强组合':<15}")
    print(f"  {'-'*50}")
    for n_q in query_counts:
        basic = compose_utility_degradation(base_utility, n_q, "basic")
        advanced = compose_utility_degradation(base_utility, n_q, "advanced")
        strong = compose_utility_degradation(base_utility, n_q, "strong")
        print(f"  {n_q:<10} {basic:<15.4f} {advanced:<15.4f} {strong:<15.4f}")

    # 测试6：隐私-效用比分析
    print("\n【测试6】隐私-效用比分析")
    print(f"  {'ε':<10} {'效用分数':<12} {'PUR比值':<12}")
    print(f"  {'-'*35}")
    for eps in [0.5, 1.0, 2.0, 5.0]:
        scale = sensitivity / eps
        mse = (2 * scale**2) / sample_size
        rmse = np.sqrt(mse)
        utility_score = 1.0 / (1.0 + rmse)
        pur = privacy_utility_ratio(eps, utility_score)
        print(f"  {eps:<10.2f} {utility_score:<12.4f} {pur:<12.4f}")

    # 测试7：生成分析报告
    print("\n【测试7】生成权衡分析报告")
    eps_to_analyze = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    true_vals = np.array([100.0, 200.0, 150.0])  # 假设3个查询
    report = trade_off_analysis_report(eps_to_analyze, sensitivity=1.0,
                                        sample_size=1000, true_values=true_vals)
    print(report)

    # 测试8：综合权衡可视化数据
    print("\n【测试8】权衡数据汇总")
    print(f"  {'场景':<20} {'ε':<8} {'效用':<10} {'推荐':<8}")
    print(f"  {'-'*50}")
    scenarios = [
        ("极强隐私", 0.1, 0.05),
        ("强隐私", 0.5, 0.3),
        ("中等隐私", 1.0, 0.6),
        ("弱隐私", 2.0, 0.85),
        ("最小隐私", 5.0, 0.95),
    ]
    for name, eps, expected_util in scenarios:
        scale = sensitivity / eps
        mse = (2 * scale**2) / sample_size
        rmse = np.sqrt(mse)
        actual_util = 1.0 / (1.0 + rmse)
        match = "✓" if actual_util >= expected_util else "✗"
        print(f"  {name:<20} {eps:<8.1f} {actual_util:<10.2f} {match:<8}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

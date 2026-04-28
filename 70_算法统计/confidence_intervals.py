"""
置信区间模块 / Confidence Intervals Module
===========================================
本模块实现多种置信区间的计算方法：
- 正态分布置信区间（已知方差）：使用Z分数
- Student-t 置信区间（未知方差）：使用t分布
- Bootstrap置信区间：通过重抽样估计
- 配对样本均值差的置信区间
- 两组均值差的置信区间

置信区间公式：x̄ ± t_{α/2, n-1} × SE
其中 SE = s / √n 为标准误。

Author: AI Assistant
"""

import math
import random
from typing import Tuple, List, Optional


# ============ 正态分布置信区间 / Normal CI ============

def normal_ci(
    sample_mean: float,
    pop_std: float,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    使用正态分布计算置信区间（已知总体方差）。

    公式：x̄ ± Z_{α/2} × (σ / √n)

    适用条件：已知总体标准差，或样本量足够大（n>30）。

    Args:
        sample_mean: 样本均值。
        pop_std: 已知总体标准差。
        n: 样本大小。
        confidence: 置信水平，默认0.95（95%）。

    Returns:
        (lower_bound, upper_bound) 置信区间下界和上界。

    Example:
        >>> normal_ci(100, 15, 50, 0.95)
        (95.85, 104.15)
    """
    alpha = 1 - confidence  # 显著性水平
    # 正态分布临界值（Z分数）
    z_critical = normal_quantile(1 - alpha / 2)
    # 计算标准误
    se = pop_std / math.sqrt(n)
    # 计算置信区间
    margin = z_critical * se
    lower = sample_mean - margin
    upper = sample_mean + margin
    return lower, upper


def normal_quantile(p: float) -> float:
    """
    标准正态分布分位数（逆CDF）的近似。

    使用近似公式计算标准正态分布的逆累积分布函数。
    精确值应使用 scipy.stats.norm.ppf。

    Args:
        p: 累积概率，范围(0, 1)。

    Returns:
        对应的分位数（Z值）。
    """
    # 使用Rational Chebyshev近似
    if p <= 0:
        return -float('inf')
    if p >= 1:
        return float('inf')
    # 将p转换为z值（粗略近似）
    if p < 0.5:
        sign = -1
        p_transform = 1 - 2 * p
    else:
        sign = 1
        p_transform = 2 * p - 1
    # Abramowitz-Stegun近似公式 26.2.23
    t = math.sqrt(-2 * math.log(p_transform))
    z = t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / \
        (1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t)
    return sign * z


# ============ Student-t 置信区间 / T-Distribution CI ============

def t_ci(
    sample_data: List[float],
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """
    使用Student-t分布计算置信区间（未知总体方差）。

    公式：x̄ ± t_{α/2, n-1} × (s / √n)

    适用条件：总体标准差未知，样本量较小（n≤30）。

    Args:
        sample_data: 样本数据列表。
        confidence: 置信水平，默认0.95（95%）。

    Returns:
        (lower_bound, upper_bound, t_critical) 置信区间及t临界值。
    """
    n = len(sample_data)
    if n < 2:
        raise ValueError("样本量至少需要2")

    # 计算样本均值
    mean_val = sum(sample_data) / n
    # 计算样本标准差
    variance_val = sum((x - mean_val) ** 2 for x in sample_data) / (n - 1)
    std_val = math.sqrt(variance_val)
    # 计算标准误
    se = std_val / math.sqrt(n)
    # 计算自由度
    df = n - 1
    # 获取t分布临界值
    t_crit = t_quantile(confidence, df)
    # 计算置信区间
    margin = t_crit * se
    lower = mean_val - margin
    upper = mean_val + margin
    return lower, upper, t_crit


def t_quantile(confidence: float, df: int) -> float:
    """
    计算t分布的分位数（临界值）。

    使用近似公式：
        t_{α, ν} ≈ z_{α} + (z³ + z)/(4ν) + (5z⁵ + 16z³ + 3z)/(96ν²)
    其中 z 为正态分布分位数。

    Args:
        confidence: 置信水平。
        df: 自由度。

    Returns:
        t分布临界值。
    """
    alpha = 1 - confidence
    # 正态分布分位数
    z = normal_quantile(1 - alpha / 2)
    # 自由度倒数
    inv_df = 1 / df
    # 近似公式
    t = z + (z ** 3 + z) * inv_df / 4
    t += (5 * z ** 5 + 16 * z ** 3 + 3 * z) * inv_df ** 2 / 96
    return t


# ============ Bootstrap 置信区间 / Bootstrap CI ============

def bootstrap_ci(
    sample_data: List[float],
    statistic_func,
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    method: str = "percentile"
) -> Tuple[float, float]:
    """
    使用Bootstrap方法计算置信区间。

    Bootstrap通过有放回抽样，从原始样本中生成大量重样本，
    然后计算统计量的分布，从而得到置信区间。

    支持三种方法：
    - "percentile"：百分位数法，直接取Bootstrap分布的百分位数
    - "basic"：基本Bootstrap，用原始统计量±(Bootstrap分位数-原始统计量)
    - "normal"：正态法，用原始统计量±Z×SE

    Args:
        sample_data: 原始样本数据。
        statistic_func: 计算统计量的函数，接受列表返回数值。
        confidence: 置信水平。
        n_bootstrap: Bootstrap重抽样次数。
        method: Bootstrap方法，"percentile"、"basic"或"normal"。

    Returns:
        (lower_bound, upper_bound) Bootstrap置信区间。
    """
    n = len(sample_data)
    # 计算原始样本的统计量
    original_stat = statistic_func(sample_data)

    # 存储Bootstrap统计量
    bootstrap_stats = []

    for _ in range(n_bootstrap):
        # 有放回地随机抽取n个样本（重抽样）
        resample = random.choices(sample_data, k=n)
        # 计算重样本的统计量
        resample_stat = statistic_func(resample)
        bootstrap_stats.append(resample_stat)

    # 按从小到大排序
    bootstrap_stats.sort()

    alpha = 1 - confidence
    # 计算百分位数索引
    lower_idx = int(n_bootstrap * alpha / 2)
    upper_idx = int(n_bootstrap * (1 - alpha / 2))

    if method == "percentile":
        # 百分位数法：直接取Bootstrap分布的百分位数
        lower = bootstrap_stats[lower_idx]
        upper = bootstrap_stats[upper_idx]

    elif method == "basic":
        # 基本Bootstrap
        lower = 2 * original_stat - bootstrap_stats[upper_idx]
        upper = 2 * original_stat - bootstrap_stats[lower_idx]

    else:  # "normal"
        # 正态法
        se = math.sqrt(sum((s - original_stat) ** 2 for s in bootstrap_stats) / n_bootstrap)
        z_crit = normal_quantile(1 - alpha / 2)
        lower = original_stat - z_crit * se
        upper = original_stat + z_crit * se

    return lower, upper


def bootstrap_standard_error(
    sample_data: List[float],
    statistic_func,
    n_bootstrap: int = 10000
) -> float:
    """
    使用Bootstrap方法估计统计量的标准误。

    Bootstrap标准误公式：
        SE_boot = sqrt( Σ(θ*_b - θ̄*)² / (B-1) )
    其中 θ*_b 是第b次Bootstrap重抽样的统计量。

    Args:
        sample_data: 原始样本数据。
        statistic_func: 统计量函数。
        n_bootstrap: 重抽样次数。

    Returns:
        Bootstrap标准误估计。
    """
    bootstrap_stats = []
    n = len(sample_data)

    for _ in range(n_bootstrap):
        # 有放回重抽样
        resample = random.choices(sample_data, k=n)
        bootstrap_stats.append(statistic_func(resample))

    # 计算Bootstrap统计量的均值
    mean_boot = sum(bootstrap_stats) / n_bootstrap
    # 计算标准差
    variance_boot = sum((s - mean_boot) ** 2 for s in bootstrap_stats) / (n_bootstrap - 1)
    return math.sqrt(variance_boot)


# ============ 两组均值差置信区间 / Two-Sample Mean Difference CI ============

def two_sample_t_ci(
    sample1: List[float],
    sample2: List[float],
    confidence: float = 0.95,
    equal_variance: bool = False
) -> Tuple[float, float]:
    """
    计算两组独立样本均值之差的置信区间。

    使用Welch's t分布（不假设方差相等）或 Student's t分布。

    Args:
        sample1: 第一组样本。
        sample2: 第二组样本。
        confidence: 置信水平。
        equal_variance: 是否假设方差相等。

    Returns:
        (lower_bound, upper_bound) 均值差置信区间。
    """
    n1 = len(sample1)
    n2 = len(sample2)
    mean1 = sum(sample1) / n1
    mean2 = sum(sample2) / n2
    var1 = sum((x - mean1) ** 2 for x in sample1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in sample2) / (n2 - 1)

    if equal_variance:
        # 合并方差
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        se = math.sqrt(pooled_var * (1 / n1 + 1 / n2))
        df = n1 + n2 - 2
    else:
        # Welch's t检验
        se = math.sqrt(var1 / n1 + var2 / n2)
        # Welch-Satterthwaite 自由度
        df = (var1 / n1 + var2 / n2) ** 2 / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )

    # 均值差
    mean_diff = mean1 - mean2
    # 临界值
    t_crit = t_quantile(confidence, int(df))
    # 置信区间
    margin = t_crit * se
    return mean_diff - margin, mean_diff + margin


def paired_mean_diff_ci(
    sample_before: List[float],
    sample_after: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    计算配对样本均值差的置信区间。

    Args:
        sample_before: 干预前样本。
        sample_after: 干预后样本。
        confidence: 置信水平。

    Returns:
        (lower_bound, upper_bound) 均值差置信区间。
    """
    n = len(sample_before)
    if n != len(sample_after):
        raise ValueError("配对样本长度必须相等")

    # 计算差值
    diffs = [sample_after[i] - sample_before[i] for i in range(n)]
    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var_diff / n)
    df = n - 1
    t_crit = t_quantile(confidence, df)
    margin = t_crit * se
    return mean_diff - margin, mean_diff + margin


# ============ 主程序入口 / Main Entry Point ============

if __name__ == "__main__":
    print("=" * 60)
    print("置信区间演示 / Confidence Intervals Demo")
    print("=" * 60)

    # 示例1：正态分布置信区间（已知σ）
    print("\n【示例1】正态置信区间（已知总体标准差）")
    print("-" * 60)
    sample_mean = 100.5
    pop_std = 15.0
    n = 50
    ci_95 = normal_ci(sample_mean, pop_std, n, 0.95)
    ci_99 = normal_ci(sample_mean, pop_std, n, 0.99)
    print(f"样本均值: {sample_mean}")
    print(f"已知总体标准差: {pop_std}, 样本量: {n}")
    print(f"95% CI: [{ci_95[0]:.4f}, {ci_95[1]:.4f}]")
    print(f"99% CI: [{ci_99[0]:.4f}, {ci_99[1]:.4f}]")

    # 示例2：T分布置信区间（未知σ）
    print("\n【示例2】Student-t 置信区间（未知总体标准差）")
    print("-" * 60)
    exam_scores = [78, 82, 75, 88, 91, 73, 85, 80, 77, 84, 79, 86]
    mean_score = sum(exam_scores) / len(exam_scores)
    var_score = sum((x - mean_score) ** 2 for x in exam_scores) / (len(exam_scores) - 1)
    std_score = math.sqrt(var_score)
    t_lower, t_upper, t_crit = t_ci(exam_scores, 0.95)
    print(f"样本: {exam_scores}")
    print(f"样本均值: {mean_score:.2f}, 样本标准差: {std_score:.2f}")
    print(f"95% CI: [{t_lower:.4f}, {t_upper:.4f}]")
    print(f"t临界值: {t_crit:.4f}")

    # 示例3：Bootstrap置信区间
    print("\n【示例3】Bootstrap置信区间（均值）")
    print("-" * 60)
    random.seed(42)  # 设置随机种子以便复现
    salary_data = [45, 52, 48, 55, 60, 42, 58, 49, 53, 47, 61, 44, 56, 50, 59]
    print(f"原始样本均值: {sum(salary_data)/len(salary_data):.2f}")

    # 定义均值统计量函数
    def sample_mean_func(data):
        return sum(data) / len(data)

    for method in ["percentile", "basic", "normal"]:
        bci = bootstrap_ci(
            salary_data, sample_mean_func,
            confidence=0.95, n_bootstrap=5000, method=method
        )
        print(f"Bootstrap {method:10s} 95% CI: [{bci[0]:.2f}, {bci[1]:.2f}]")

    # Bootstrap标准误
    bse = bootstrap_standard_error(salary_data, sample_mean_func, n_bootstrap=5000)
    print(f"Bootstrap 标准误 (SE): {bse:.4f}")

    # 示例4：两组均值差置信区间
    print("\n【示例4】两组均值差置信区间")
    print("-" * 60)
    drug_group = [120, 122, 118, 125, 121, 119, 123, 117, 124, 126]
    placebo_group = [130, 135, 128, 140, 132, 138, 125, 142, 136, 129]
    ci_diff = two_sample_t_ci(drug_group, placebo_group, 0.95, equal_variance=False)
    mean_drug = sum(drug_group) / len(drug_group)
    mean_placebo = sum(placebo_group) / len(placebo_group)
    print(f"药物组均值: {mean_drug:.2f}, 安慰剂组均值: {mean_placebo:.2f}")
    print(f"均值差: {mean_drug - mean_placebo:.2f}")
    print(f"95% CI: [{ci_diff[0]:.4f}, {ci_diff[1]:.4f}]")
    if ci_diff[0] < 0 < ci_diff[1]:
        print("结论：置信区间包含0，两组差异不显著")
    else:
        print("结论：置信区间不包含0，两组差异显著")

    # 示例5：配对均值差置信区间
    print("\n【示例5】配对样本均值差置信区间")
    print("-" * 60)
    before = [80, 85, 78, 92, 88, 76, 83, 90, 79, 84]
    after = [78, 83, 77, 89, 85, 74, 81, 87, 77, 82]
    ci_paired = paired_mean_diff_ci(before, after, 0.95)
    mean_b = sum(before) / len(before)
    mean_a = sum(after) / len(after)
    print(f"干预前均值: {mean_b:.2f}, 干预后均值: {mean_a:.2f}")
    print(f"平均变化: {mean_a - mean_b:.2f}")
    print(f"95% CI: [{ci_paired[0]:.4f}, {ci_paired[1]:.4f}]")

    print("\n" + "=" * 60)
    print("测试完成 / Test Complete")
    print("=" * 60)

"""
假设检验模块 / Hypothesis Testing Module
=========================================
本模块实现经典的参数假设检验方法，包括：
- Z检验（Z-Test）：已知总体方差时，检验样本均值
- 单样本T检验（One-Sample T-Test）：未知总体方差
- 独立双样本T检验（Two-Sample Independent T-Test）：两组独立样本比较
- 配对T检验（Paired T-Test）：配对样本的前后比较
- 效应量（Effect Size）：衡量实际显著性

所有函数返回检验统计量和p值，支持单尾和双尾检验。

Author: AI Assistant
"""

import math
from typing import Tuple, Optional, List


# ============ T分布临界值表（近似）/ T-Distribution Critical Values ============

def t_critical(alpha: float, df: int, two_tailed: bool = True) -> float:
    """
    返回T分布的临界值（近似，使用插值公式）。

    这是 Welch-Satterthwaite 近似的简化实现。
    对于精确值，建议使用 scipy.stats.t.ppf。

    Args:
        alpha: 显著性水平（如0.05）。
        df: 自由度。
        two_tailed: True为双尾检验，False为单尾。

    Returns:
        T分布临界值。
    """
    # 使用近似公式：t ≈ z + (z³ + z)/(4df) 
    # 其中 z 为正态分布临界值
    if two_tailed:
        alpha = alpha / 2
    # 标准正态逆CDF近似（非常粗糙，用于演示）
    z = math.sqrt(2) * self_inverse_erf(1 - 2 * alpha)
    # 校正项
    correction = (z ** 3 + z) / (4 * df)
    return z + correction


def self_inverse_erf(p: float) -> float:
    """误差函数逆的近似（用于正态分布临界值计算）。"""
    # 使用近似公式
    if p <= 0:
        return -10
    if p >= 1:
        return 10
    # 简单的数值近似
    return 2.5 * (p - 0.5)  # 粗略近似


# ============ 核心检验函数 / Core Testing Functions ============

def compute_standard_error(sample_std: float, n: int) -> float:
    """
    计算标准误（Standard Error）。

    标准误公式：SE = s / √n
    反映样本均值估计的精确度。

    Args:
        sample_std: 样本标准差。
        n: 样本大小。

    Returns:
        标准误值。
    """
    return sample_std / math.sqrt(n)


def z_test(
    sample_mean: float,
    pop_mean: float,
    pop_std: float,
    n: int,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    单样本Z检验。

    用于已知总体标准差时，检验样本均值是否显著不同于总体均值。

    公式：Z = (x̄ - μ₀) / (σ / √n)

    Args:
        sample_mean: 样本均值。
        pop_mean: 假设的总体均值（零假设中的μ₀）。
        pop_std: 已知总体标准差。
        n: 样本大小。
        alternative: 备择假设类型，
            "two-sided"（双尾）、"less"（左侧）、"greater"（右侧）。

    Returns:
        (z_statistic, p_value) 元组。
    """
    # 计算标准误
    se = pop_std / math.sqrt(n)
    # 计算Z统计量
    z_stat = (sample_mean - pop_mean) / se

    # 计算p值（使用正态分布近似）
    p_value = normal_p_value(z_stat, alternative)

    return z_stat, p_value


def one_sample_t_test(
    sample_data: List[float],
    pop_mean: float,
    alternative: str = "two-sided"
) -> Tuple[float, float, float]:
    """
    单样本T检验。

    用于未知总体方差时，检验样本均值是否显著不同于假设的总体均值。

    公式：t = (x̄ - μ₀) / (s / √n)
    自由度：df = n - 1

    Args:
        sample_data: 样本数据列表。
        pop_mean: 假设的总体均值（零假设中的μ₀）。
        alternative: 备择假设类型。

    Returns:
        (t_statistic, p_value, df) 元组。
    """
    n = len(sample_data)
    if n < 2:
        raise ValueError("样本量至少需要2个数据点")

    # 计算样本均值和标准差
    mean_val = sum(sample_data) / n
    variance_val = sum((x - mean_val) ** 2 for x in sample_data) / (n - 1)
    std_val = math.sqrt(variance_val)

    # 计算标准误
    se = std_val / math.sqrt(n)
    # 计算t统计量
    t_stat = (mean_val - pop_mean) / se

    # 自由度
    df = n - 1

    # 计算p值（使用近似）
    p_value = t_p_value_approx(t_stat, df, alternative)

    return t_stat, p_value, df


def two_sample_t_test_independent(
    sample1: List[float],
    sample2: List[float],
    equal_variance: bool = True,
    alternative: str = "two-sided"
) -> Tuple[float, float, float]:
    """
    独立双样本T检验（Independent Two-Sample T-Test）。

    检验两组独立样本的均值是否存在显著差异。
    - equal_variance=True：使用 pooled variance（Student's t-test）
    - equal_variance=False：使用 Welch's t-test（不假设方差相等）

    Args:
        sample1: 第一组样本数据。
        sample2: 第二组样本数据。
        equal_variance: 是否假设两组方差相等。
        alternative: 备择假设类型。

    Returns:
        (t_statistic, p_value, df) 元组。
    """
    n1 = len(sample1)
    n2 = len(sample2)
    if n1 < 2 or n2 < 2:
        raise ValueError("每组样本至少需要2个数据点")

    # 计算两组样本的均值
    mean1 = sum(sample1) / n1
    mean2 = sum(sample2) / n2

    # 计算两组样本的方差
    var1 = sum((x - mean1) ** 2 for x in sample1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in sample2) / (n2 - 1)

    if equal_variance:
        # 合并方差（假设两组方差相等）
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        se = math.sqrt(pooled_var * (1 / n1 + 1 / n2))
        df = n1 + n2 - 2
    else:
        # Welch's t-test：不假设方差相等
        se = math.sqrt(var1 / n1 + var2 / n2)
        # Welch-Satterthwaite 近似计算自由度
        df = (var1 / n1 + var2 / n2) ** 2 / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )

    # 计算t统计量
    t_stat = (mean1 - mean2) / se

    # 计算p值
    p_value = t_p_value_approx(t_stat, df, alternative)

    return t_stat, p_value, df


def paired_t_test(
    sample_before: List[float],
    sample_after: List[float],
    alternative: str = "two-sided"
) -> Tuple[float, float, float]:
    """
    配对T检验（Paired T-Test）。

    用于配对样本（如同一组受试者的治疗前后的比较）。

    公式：t = d̄ / (s_d / √n)
    其中 dᵢ = afterᵢ - beforeᵢ（差值）

    Args:
        sample_before: 干预前的测量值列表。
        sample_after: 干预后的测量值列表。
        alternative: 备择假设类型。

    Returns:
        (t_statistic, p_value, df) 元组。
    """
    n = len(sample_before)
    if n != len(sample_after):
        raise ValueError("配对样本的长度必须相等")
    if n < 2:
        raise ValueError("样本量至少需要2对数据")

    # 计算每对样本的差值
    differences = [sample_after[i] - sample_before[i] for i in range(n)]

    # 计算差值的均值
    mean_diff = sum(differences) / n

    # 计算差值的标准差
    var_diff = sum((d - mean_diff) ** 2 for d in differences) / (n - 1)
    std_diff = math.sqrt(var_diff)

    # 计算标准误
    se = std_diff / math.sqrt(n)

    # 计算t统计量
    t_stat = mean_diff / se

    # 自由度
    df = n - 1

    # 计算p值
    p_value = t_p_value_approx(t_stat, df, alternative)

    return t_stat, p_value, df


def compute_effect_size_t(
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n1: int,
    n2: int
) -> float:
    """
    计算Cohen's d 效应量（用于两组比较）。

    Cohen's d 解释标准：
    - |d| < 0.2：微小效应
    - 0.2 ≤ |d| < 0.5：小效应
    - 0.5 ≤ |d| < 0.8：中等效应
    - |d| ≥ 0.8：大效应

    Args:
        mean1: 第一组均值。
        mean2: 第二组均值。
        std1: 第一组标准差。
        std2: 第二组标准差。
        n1: 第一组样本量。
        n2: 第二组样本量。

    Returns:
        Cohen's d 效应量。
    """
    # 合并标准差
    pooled_std = math.sqrt(
        ((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2)
    )
    return (mean1 - mean2) / pooled_std


# ============ 辅助函数 / Helper Functions ============

def normal_p_value(z: float, alternative: str = "two-sided") -> float:
    """
    计算正态分布的p值（近似）。

    Args:
        z: Z统计量。
        alternative: 检验类型。

    Returns:
        p值。
    """
    # 使用标准正态分布的尾概率近似
    p_right = 0.5 * (1 + math.erf(-z / math.sqrt(2)))  # P(Z > z)
    if alternative == "two-sided":
        return 2 * min(p_right, 1 - p_right)
    elif alternative == "less":
        return p_right  # P(Z < z)
    else:  # "greater"
        return 1 - p_right  # P(Z > z)


def t_p_value_approx(t: float, df: int, alternative: str = "two-sided") -> float:
    """
    使用正态分布近似T分布的p值（仅用于演示）。

    当 df 较大（>30）时，T分布趋近于正态分布。
    精确计算应使用 scipy.stats.t.cdf。

    Args:
        t: t统计量。
        df: 自由度。
        alternative: 检验类型。

    Returns:
        近似p值。
    """
    # 使用正态近似（df大时效果较好）
    return normal_p_value(t, alternative)


def interpret_p_value(p: float, alpha: float = 0.05) -> str:
    """
    解释p值并给出结论。

    Args:
        p: p值。
        alpha: 显著性水平。

    Returns:
        检验结论字符串。
    """
    if p < alpha:
        return f"拒绝零假设 (p={p:.4f} < α={alpha})"
    else:
        return f"无法拒绝零假设 (p={p:.4f} >= α={alpha})"


# ============ 主程序入口 / Main Entry Point ============

if __name__ == "__main__":
    print("=" * 60)
    print("假设检验演示 / Hypothesis Testing Demo")
    print("=" * 60)

    # 示例1：单样本T检验
    # 某品牌声称其薯片平均重量为50g，随机抽取10袋
    print("\n【示例1】单样本T检验：薯片重量检验")
    print("-" * 60)
    chip_weights = [49, 51, 50, 48, 52, 50, 49, 51, 50, 50]
    claimed_mean = 50.0
    t_stat, p_val, df = one_sample_t_test(chip_weights, claimed_mean)
    print(f"样本均值: {sum(chip_weights)/len(chip_weights):.2f}g")
    print(f"假设总体均值: {claimed_mean}g")
    print(f"t统计量: {t_stat:.4f}, 自由度: {df}, p值: {p_val:.4f}")
    print(f"结论: {interpret_p_value(p_val)}")

    # 示例2：独立双样本T检验
    # 比较两种教学方法的效果
    print("\n【示例2】独立双样本T检验：教学方法比较")
    print("-" * 60)
    method_a_scores = [78, 82, 75, 88, 91, 73, 85, 80]
    method_b_scores = [72, 80, 68, 75, 78, 70, 82, 74]
    t_stat2, p_val2, df2 = two_sample_t_test_independent(
        method_a_scores, method_b_scores, equal_variance=False
    )
    mean_a = sum(method_a_scores) / len(method_a_scores)
    mean_b = sum(method_b_scores) / len(method_b_scores)
    print(f"方法A均值: {mean_a:.2f}, 方法B均值: {mean_b:.2f}")
    print(f"t统计量: {t_stat2:.4f}, 自由度(df≈{df2:.1f}), p值: {p_val2:.4f}")
    print(f"结论: {interpret_p_value(p_val2)}")

    # 计算效应量
    std_a = math.sqrt(sum((x - mean_a) ** 2 for x in method_a_scores) / (len(method_a_scores) - 1))
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in method_b_scores) / (len(method_b_scores) - 1))
    effect = compute_effect_size_t(mean_a, mean_b, std_a, std_b, len(method_a_scores), len(method_b_scores))
    print(f"Cohen's d效应量: {effect:.4f}")

    # 示例3：配对T检验
    # 检验减肥药效果（服药前后体重对比）
    print("\n【示例3】配对T检验：减肥药效果")
    print("-" * 60)
    before_weights = [80, 85, 78, 92, 88, 76, 83, 90, 79, 84]
    after_weights =  [78, 83, 77, 89, 85, 74, 81, 87, 77, 82]
    t_stat3, p_val3, df3 = paired_t_test(before_weights, after_weights)
    mean_before = sum(before_weights) / len(before_weights)
    mean_after = sum(after_weights) / len(after_weights)
    print(f"服药前平均体重: {mean_before:.2f}kg")
    print(f"服药后平均体重: {mean_after:.2f}kg")
    print(f"平均减重: {mean_before - mean_after:.2f}kg")
    print(f"t统计量: {t_stat3:.4f}, 自由度: {df3}, p值: {p_val3:.4f}")
    print(f"结论: {interpret_p_value(p_val3)}")

    # 示例4：Z检验（已知总体标准差）
    print("\n【示例4】Z检验：已知σ的均值检验")
    print("-" * 60)
    sample_mean = 105
    pop_mean = 100
    pop_std = 15
    n = 50
    z_stat, z_p = z_test(sample_mean, pop_mean, pop_std, n)
    print(f"样本均值: {sample_mean}, 假设总体均值: {pop_mean}")
    print(f"已知总体标准差: {pop_std}, 样本量: {n}")
    print(f"Z统计量: {z_stat:.4f}, p值: {z_p:.4f}")
    print(f"结论: {interpret_p_value(z_p)}")

    print("\n" + "=" * 60)
    print("测试完成 / Test Complete")
    print("=" * 60)

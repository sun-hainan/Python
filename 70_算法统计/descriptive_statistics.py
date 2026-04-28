"""
描述性统计模块 / Descriptive Statistics Module
================================================
本模块提供常用的描述性统计量计算函数，包括：
- 均值（Mean）：数据的算术平均值
- 方差（Variance）：数据离散程度的度量
- 标准差（Standard Deviation）：方差的平方根
- 中位数（Median）：排序后位于中间的数值
- 众数（Mode）：出现频率最高的数值
- 分位数（Quantile）：数据分布的百分位点
- 偏度（Skewness）：数据分布的对称性
- 峰度（Kurtosis）：数据分布的尾部厚度

Author: AI Assistant
"""

import math
from collections import Counter
from typing import List


# ============ 辅助函数 / Helper Functions ============

def sort_data(data: List[float]) -> List[float]:
    """
    对数据进行排序（升序）。

    Args:
        data: 待排序的数值列表。

    Returns:
        升序排列的数值列表。

    Example:
        >>> sort_data([3, 1, 2])
        [1, 2, 3]
    """
    return sorted(data)


def compute_mean(data: List[float]) -> float:
    """
    计算数据的算术均值。

    均值公式：x̄ = (Σxᵢ) / n
    其中 n 为数据点数量。

    Args:
        data: 数值列表，不能为空。

    Returns:
        数据的算术平均值。

    Raises:
        ValueError: 当数据列表为空时抛出。
    """
    n = len(data)
    if n == 0:
        raise ValueError("数据列表不能为空")
    # 求和后除以数据点数量
    return sum(data) / n


def compute_variance(data: List[float], ddof: int = 0) -> float:
    """
    计算数据的方差。

    方差公式（总体方差，ddof=0）：
        σ² = Σ(xᵢ - x̄)² / n
    方差公式（样本方差，ddof=1）：
        s² = Σ(xᵢ - x̄)² / (n-1)

    Args:
        data: 数值列表。
        ddof: 自由度调整，0为总体方差，1为样本方差。

    Returns:
        方差值。
    """
    n = len(data)
    if n <= ddof:
        raise ValueError("数据点数量必须大于自由度调整值")
    mean_val = compute_mean(data)  # 先计算均值
    # 计算每个数据点与均值的差的平方并求和
    squared_diff_sum = sum((x - mean_val) ** 2 for x in data)
    # 除以 n 或 (n-1)
    return squared_diff_sum / (n - ddof) if ddof > 0 else squared_diff_sum / n


def compute_std(data: List[float], ddof: int = 0) -> float:
    """
    计算数据的标准差。

    标准差是方差的平方根，与原始数据单位相同，更易解释。

    Args:
        data: 数值列表。
        ddof: 自由度调整，0为总体标准差，1为样本标准差。

    Returns:
        标准差值。
    """
    variance_val = compute_variance(data, ddof)
    return math.sqrt(variance_val)


def compute_median(data: List[float]) -> float:
    """
    计算数据的中位数。

    中位数将数据分为上下两半，对异常值具有鲁棒性。
    - 若 n 为奇数，返回中间那个数
    - 若 n 为偶数，返回中间两个数的均值

    Args:
        data: 数值列表。

    Returns:
        中位数。
    """
    sorted_data = sort_data(data)
    n = len(sorted_data)
    mid = n // 2  # 中间位置
    if n % 2 == 1:
        # 奇数个数据点，直接返回中间值
        return sorted_data[mid]
    else:
        # 偶数个数据点，返回中间两数的均值
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2


def compute_mode(data: List[float]) -> List[float]:
    """
    计算数据的众数（出现频率最高的值）。

    支持多众数情况（即多个值出现频率相同且最高）。

    Args:
        data: 数值列表。

    Returns:
        众数列表（可能包含多个值）。
    """
    counter = Counter(data)  # 统计每个值出现的次数
    max_freq = max(counter.values())  # 找出最高频率
    # 收集所有出现次数等于最高频率的值
    modes = [val for val, count in counter.items() if count == max_freq]
    return sorted(modes)


def compute_quantile(data: List[float], quantile: float) -> float:
    """
    计算数据的指定分位数。

    分位数公式（线性插值法）：
        先对数据排序，找到位置 p = (n-1) * q
        若 p 为整数，直接取值；若为小数，则线性插值。

    Args:
        data: 数值列表。
        quantile: 分位数，范围 [0, 1]，如 0.25 表示第25百分位数。

    Returns:
        对应的分位数值。

    Raises:
        ValueError: 当 quantile 不在 [0,1] 范围内时抛出。
    """
    if not (0 <= quantile <= 1):
        raise ValueError("分位数必须在0到1之间")
    sorted_data = sort_data(data)
    n = len(sorted_data)
    # 计算分位数在排序数组中的位置
    index = quantile * (n - 1)
    lower = int(math.floor(index))  # 下界索引
    upper = int(math.ceil(index))   # 上界索引
    if lower == upper:
        # 位置恰好是整数，直接返回
        return sorted_data[lower]
    # 否则在上下界之间进行线性插值
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def compute_skewness(data: List[float]) -> float:
    """
    计算数据的偏度（衡量分布对称性）。

    偏度公式：Skew = n / ((n-1)(n-2)) * Σ[(xᵢ-x̄)/s]³
    - Skew > 0：右偏（正偏），右侧尾部较长
    - Skew = 0：完全对称
    - Skew < 0：左偏（负偏），左侧尾部较长

    Args:
        data: 数值列表，至少需要3个数据点。

    Returns:
        偏度值。
    """
    n = len(data)
    if n < 3:
        raise ValueError("偏度计算至少需要3个数据点")
    mean_val = compute_mean(data)
    std_val = compute_std(data, ddof=1)  # 使用样本标准差
    if std_val == 0:
        raise ValueError("标准差为零，无法计算偏度")
    # 计算标准化偏差的立方和
    skew_sum = sum(((x - mean_val) / std_val) ** 3 for x in data)
    return (n / ((n - 1) * (n - 2))) * skew_sum


def compute_kurtosis(data: List[float]) -> float:
    """
    计算数据的峰度（衡量分布尾部厚度）。

    峰度公式（超额峰度）：Kurt = [n(n+1)/((n-1)(n-2)(n-3))]
                              * Σ[(xᵢ-x̄)/s]⁴ - 3(n-1)²/((n-2)(n-3))
    - Kurt > 0：尖峰分布（比正态分布更尖锐）
    - Kurt = 0：接近正态分布
    - Kurt < 0：扁平分布（比正态分布更平坦）

    Args:
        data: 数值列表，至少需要4个数据点。

    Returns:
        超额峰度值。
    """
    n = len(data)
    if n < 4:
        raise ValueError("峰度计算至少需要4个数据点")
    mean_val = compute_mean(data)
    std_val = compute_std(data, ddof=1)  # 使用样本标准差
    if std_val == 0:
        raise ValueError("标准差为零，无法计算峰度")
    # 计算标准化偏差的四次方和
    kurt_sum = sum(((x - mean_val) / std_val) ** 4 for x in data)
    # 使用Fisher定义（正态分布超额峰度为0）
    term1 = n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
    term2 = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return term1 * kurt_sum - term2


def compute_range(data: List[float]) -> float:
    """
    计算数据的极差（最大值与最小值之差）。

    极差是最简单的离散程度度量，但对异常值敏感。

    Args:
        data: 数值列表。

    Returns:
        极差值。
    """
    sorted_data = sort_data(data)
    return sorted_data[-1] - sorted_data[0]


def compute_iqr(data: List[float]) -> float:
    """
    计算数据的四分位距（IQR）。

    IQR = Q3 - Q1，是鲁棒的离散程度度量，不受异常值影响。
    常用于构建箱线图和检测异常值。

    Args:
        data: 数值列表。

    Returns:
        四分位距值。
    """
    q1 = compute_quantile(data, 0.25)  # 第25百分位数
    q3 = compute_quantile(data, 0.75)  # 第75百分位数
    return q3 - q1


# ============ 主程序入口 / Main Entry Point ============

if __name__ == "__main__":
    # 使用示例数据测试所有统计函数
    sample_data = [12, 15, 14, 10, 13, 17, 16, 11, 14, 15, 18, 10, 13, 16, 17]

    print("=" * 50)
    print("描述性统计量计算结果 / Descriptive Statistics")
    print("=" * 50)
    print(f"数据样本: {sample_data}")
    print("-" * 50)

    # 均值
    mean_val = compute_mean(sample_data)
    print(f"均值 (Mean):              {mean_val:.4f}")

    # 方差（样本方差）
    variance_val = compute_variance(sample_data, ddof=1)
    print(f"样本方差 (Sample Var):    {variance_val:.4f}")

    # 标准差（样本标准差）
    std_val = compute_std(sample_data, ddof=1)
    print(f"样本标准差 (Sample Std):  {std_val:.4f}")

    # 中位数
    median_val = compute_median(sample_data)
    print(f"中位数 (Median):          {median_val:.4f}")

    # 众数
    mode_val = compute_mode(sample_data)
    print(f"众数 (Mode):              {mode_val}")

    # 分位数
    print("-" * 50)
    print("分位数 (Quantiles):")
    for q in [0.0, 0.25, 0.50, 0.75, 1.0]:
        print(f"  Q{int(q*100):02d} ({q*100:5.1f}%):           {compute_quantile(sample_data, q):.4f}")

    # 极差
    range_val = compute_range(sample_data)
    print(f"\n极差 (Range):             {range_val:.4f}")

    # 四分位距
    iqr_val = compute_iqr(sample_data)
    print(f"四分位距 (IQR):           {iqr_val:.4f}")

    # 偏度
    skewness_val = compute_skewness(sample_data)
    print(f"偏度 (Skewness):          {skewness_val:.4f}")

    # 峰度
    kurtosis_val = compute_kurtosis(sample_data)
    print(f"峰度 (Kurtosis):          {kurtosis_val:.4f}")

    print("=" * 50)
    print("测试完成 / Test Complete")

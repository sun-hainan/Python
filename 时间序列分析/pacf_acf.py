# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / pacf_acf

本文件实现 pacf_acf 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional


def acf(y: np.ndarray, max_lag: int) -> np.ndarray:
    """
    计算自相关函数（ACF）
    
    ACF(k) = Cov(y_t, y_{t-k}) / Var(y_t)
    
    参数:
        y: 时间序列
        max_lag: 最大滞后期数
    
    返回:
        ACF数组
    """
    n = len(y)
    y_centered = y - np.mean(y)
    variance = np.var(y)
    
    if variance < 1e-10:
        return np.zeros(max_lag + 1)
    
    acf_values = np.zeros(max_lag + 1)
    acf_values[0] = 1.0  # lag=0时自相关为1
    
    for k in range(1, max_lag + 1):
        if k >= n:
            acf_values[k] = 0
        else:
            # 计算滞后k的自相关
            cov = np.mean(y_centered[k:] * y_centered[:-k])
            acf_values[k] = cov / variance
    
    return acf_values


def pacf(y: np.ndarray, max_lag: int) -> np.ndarray:
    """
    计算偏自相关函数（PACF）
    
    使用Yule-Walker方程递归计算
    
    参数:
        y: 时间序列
        max_lag: 最大滞后期数
    
    返回:
        PACF数组
    """
    n = len(y)
    y_centered = y - np.mean(y)
    
    # 先计算ACF
    acf_values = acf(y, max_lag)
    
    # PACF递归计算
    pacf_values = np.zeros(max_lag + 1)
    pacf_values[0] = 1.0
    
    # Yule-Walker方程求解
    # 对于AR(p): Cov(k) = sum(phi_i * Cov(k-i)), k >= 1
    for k in range(1, max_lag + 1):
        if k > n - 1:
            pacf_values[k] = 0
            continue
        
        # 构建Toeplitz矩阵
        # [acf[0] acf[1] ... acf[k-1]]
        # [acf[1] acf[0] ... acf[k-2]]
        # ...
        # [acf[k-1] ... acf[0]]
        
        r = acf_values[:k]
        T = np.zeros((k, k))
        for i in range(k):
            T[i, :k - i] = r[:k - i]
            if i > 0:
                T[i, k - i:] = r[1:i + 1]
        
        b = acf_values[1:k + 1]
        
        try:
            phi = np.linalg.solve(T, b)
            pacf_values[k] = phi[-1]  # PACF(k)是最后一个系数
        except np.linalg.LinAlgError:
            pacf_values[k] = 0
    
    return pacf_values


def acf_confidence_interval(n: int, alpha: float = 0.05) -> float:
    """
    计算ACF置信区间边界
    
    参数:
        n: 样本数量
        alpha: 显著性水平（默认95%置信区间）
    
    返回:
        置信区间边界
    """
    # 对于白噪声，ACF近似N(0, 1/n)
    z_critical = 1.96  # 近似正态分布
    return z_critical / np.sqrt(n)


def pacf_confidence_interval(n: int, alpha: float = 0.05) -> float:
    """
    计算PACF置信区间边界
    
    参数:
        n: 样本数量
        alpha: 显著性水平
    
    返回:
        置信区间边界
    """
    # PACF的方差约为1/n
    return 1.96 / np.sqrt(n)


class ACFPACFPlot:
    """ACF/PACF可视化辅助类"""
    
    def __init__(self, y: np.ndarray, max_lag: int = 40):
        """
        参数:
            y: 时间序列
            max_lag: 最大滞后期
        """
        self.y = y
        self.max_lag = max_lag
        self.n = len(y)
        
        self.acf_values = acf(y, max_lag)
        self.pacf_values = pacf(y, max_lag)
        
        self.acf_ci = acf_confidence_interval(self.n)
        self.pacf_ci = pacf_confidence_interval(self.n)
    
    def significant_lags(self, which: str = 'acf') -> np.ndarray:
        """
        返回显著的滞后位置
        
        参数:
            which: 'acf' 或 'pacf'
        
        返回:
            显著滞后期索引数组
        """
        if which == 'acf':
            values = self.acf_values
            ci = self.acf_ci
        else:
            values = self.pacf_values
            ci = self.pacf_ci
        
        return np.where(np.abs(values) > ci)[0]
    
    def suggest_ar_order(self) -> int:
        """
        根据PACF建议AR阶数
        
        策略：找到PACF截断的位置（即最后一个显著的滞后）
        
        返回:
            建议的AR阶数
        """
        significant = self.significant_lags('pacf')
        
        if len(significant) == 0:
            return 0
        
        # 找到连续显著的滞后
        for i in range(len(significant) - 1):
            if significant[i + 1] - significant[i] > 1:
                return significant[i]
        
        return significant[-1]
    
    def suggest_ma_order(self) -> int:
        """
        根据ACF建议MA阶数
        
        策略：找到ACF截断的位置
        
        返回:
            建议的MA阶数
        """
        significant = self.significant_lags('acf')
        
        if len(significant) == 0:
            return 0
        
        # 找到ACF从显著变为不显著的位置
        for i in range(1, len(significant)):
            if significant[i] - significant[i - 1] > 1:
                return significant[i - 1]
        
        return significant[-1]
    
    def suggest_arima_orders(self) -> Tuple[int, int, int]:
        """
        综合ACF/PACF建议ARIMA参数
        
        返回:
            (p, d, q) 元组
        """
        # PACF给出AR阶数建议
        p = min(self.suggest_ar_order(), 10)
        
        # ACF给出MA阶数建议
        q = min(self.suggest_ma_order(), 10)
        
        # 简单使用d=1作为默认
        d = 1
        
        return p, d, q
    
    def print_summary(self):
        """打印ACF/PACF分析摘要"""
        print("=" * 50)
        print("ACF/PACF分析摘要")
        print("=" * 50)
        print(f"样本数: {self.n}")
        print(f"最大滞后期: {self.max_lag}")
        print(f"\nACF 95%置信区间: ±{self.acf_ci:.4f}")
        print(f"PACF 95%置信区间: ±{self.pacf_ci:.4f}")
        
        print(f"\n显著ACF滞后: {list(self.significant_lags('acf')[:10])}")
        print(f"显著PACF滞后: {list(self.significant_lags('pacf')[:10])}")
        
        p, d, q = self.suggest_arima_orders()
        print(f"\n建议ARIMA参数: p={p}, d={d}, q={q}")
        
        print("\n前10个ACF/PACF值:")
        print("  Lag   ACF    PACF")
        for i in range(10):
            acf_sig = "*" if np.abs(self.acf_values[i]) > self.acf_ci else " "
            pacf_sig = "*" if np.abs(self.pacf_values[i]) > self.pacf_ci else " "
            print(f"  {i:3d}  {self.acf_values[i]:6.4f}{acf_sig}  {self.pacf_values[i]:6.4f}{pacf_sig}")


def ljung_box_test(y: np.ndarray, lag: int = 10) -> Tuple[float, float]:
    """
    Ljung-Box检验 - 检验序列是否为白噪声
    
    H0: 序列是白噪声（ACF全为0）
    H1: 序列存在自相关
    
    参数:
        y: 时间序列
        lag: 滞后期数
    
    返回:
        (Q统计量, p值)
    """
    n = len(y)
    acf_values = acf(y, lag)
    
    # Q统计量
    Q = n * (n + 2) * np.sum([acf_values[k] ** 2 / (n - k) for k in range(1, lag + 1)])
    
    # p值（卡方分布）
    from scipy import stats
    p_value = 1 - stats.chi2.cdf(Q, lag)
    
    return Q, p_value


def portmanteau_test(y: np.ndarray, lag: int = 10) -> Tuple[float, float]:
    """
    Portmanteau检验（Box-Pierce检验的改进版本）
    
    参数:
        y: 时间序列
        lag: 滞后期数
    
    返回:
        (Q*统计量, p值)
    """
    n = len(y)
    acf_values = acf(y, lag)
    
    # Portmanteau统计量
    Q_star = n * np.sum([acf_values[k] ** 2 for k in range(1, lag + 1)])
    
    from scipy import stats
    p_value = 1 - stats.chi2.cdf(Q_star, lag)
    
    return Q_star, p_value


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("ACF/PACF分析测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 生成测试数据
    n = 200
    
    # 1. 白噪声
    white_noise = np.random.randn(n)
    
    # 2. AR(1)过程
    ar1 = np.zeros(n)
    phi = 0.7
    for t in range(1, n):
        ar1[t] = phi * ar1[t - 1] + np.random.randn()
    
    # 3. MA(1)过程
    ma1 = np.zeros(n)
    theta = 0.5
    for t in range(n):
        ma1[t] = np.random.randn() + theta * np.random.randn()
    
    # 4. 周期性信号
    periodic = np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.randn(n) * 0.1
    
    print("\n--- 白噪声 ---")
    plot1 = ACFPACFPlot(white_noise, max_lag=30)
    plot1.print_summary()
    Q, p = ljung_box_test(white_noise)
    print(f"\nLjung-Box检验: Q={Q:.2f}, p={p:.4f}")
    print(f"结论: {'是白噪声' if p > 0.05 else '不是白噪声'}")
    
    print("\n--- AR(1)过程 ---")
    plot2 = ACFPACFPlot(ar1, max_lag=30)
    plot2.print_summary()
    p, d, q = plot2.suggest_arima_orders()
    print(f"\n建议ARIMA阶数: ({p}, {d}, {q})")
    
    print("\n--- MA(1)过程 ---")
    plot3 = ACFPACFPlot(ma1, max_lag=30)
    plot3.print_summary()
    p, d, q = plot3.suggest_arima_orders()
    print(f"\n建议ARIMA阶数: ({p}, {d}, {q})")
    
    print("\n--- 周期性信号 ---")
    plot4 = ACFPACFPlot(periodic, max_lag=40)
    plot4.print_summary()
    
    print("\n" + "=" * 50)
    print("测试完成")

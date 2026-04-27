# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / temporal_causal_discovery

本文件实现 temporal_causal_discovery 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import math


class TemporalCausalModel:
    """
    时序因果模型基类
    """
    
    def __init__(self, max_lag: int = 10):
        self.max_lag = max_lag
        self.causal_graph: Dict[str, List[str]] = {}
        self.time_series: Dict[str, np.ndarray] = {}
    
    def fit(self, data: Dict[str, np.ndarray]):
        """
        拟合数据
        
        Args:
            data: {变量名: 时间序列}
        """
        raise NotImplementedError
    
    def predict_causes(self, variable: str) -> List[str]:
        """预测变量的原因"""
        raise NotImplementedError
    
    def predict_effects(self, variable: str) -> List[str]:
        """预测变量的结果"""
        raise NotImplementedError


class GrangerCausality(TemporalCausalModel):
    """
    Granger因果检验
    
    如果X帮助预测Y（在Y自身的过去之上），
    则X是Y的Granger原因
    """
    
    def __init__(self, max_lag: int = 10, alpha: float = 0.05):
        super().__init__(max_lag)
        self.alpha = alpha
        self.p_values: Dict[Tuple[str, str], float] = {}
        self.causal_matrix: Dict[Tuple[str, str], bool] = {}
    
    def fit(self, data: Dict[str, np.ndarray]):
        """
        拟合数据并进行Granger因果检验
        """
        self.time_series = data
        variables = list(data.keys())
        
        # 初始化因果图
        self.causal_graph = {v: [] for v in variables}
        
        for target in variables:
            for cause in variables:
                if cause == target:
                    continue
                
                # 进行Granger因果检验
                p_value = self._granger_test(cause, target)
                self.p_values[(cause, target)] = p_value
                
                # 判断是否显著
                if p_value < self.alpha:
                    self.causal_graph[target].append(cause)
                    self.causal_matrix[(cause, target)] = True
                else:
                    self.causal_matrix[(cause, target)] = False
    
    def _granger_test(self, cause: str, target: str) -> float:
        """
        Granger因果检验
        
        H0: cause 不是 target 的原因
        
        Returns:
            p值
        """
        y = self.time_series[target]
        x = self.time_series[cause]
        
        n = len(y)
        
        if n < self.max_lag * 2:
            return 1.0
        
        # 限制数据长度
        max_len = min(len(y), len(x)) - self.max_lag
        y = y[:max_len]
        x = x[:max_len]
        
        # 构建回归矩阵
        # Restricted: Y ~ Y_lags
        # Full: Y ~ Y_lags + X_lags
        
        n_obs = len(y) - self.max_lag
        
        # Restricted回归
        y_restricted = y[self.max_lag:]
        X_restricted = self._build_lag_matrix(y, self.max_lag)
        
        # Full回归
        X_full = self._build_full_matrix(y, x, self.max_lag)
        
        # 计算RSS
        rss_r = self._ols_rss(y_restricted, X_restricted)
        rss_f = self._ols_rss(y[self.max_lag:], X_full)
        
        # F检验统计量
        k = self.max_lag
        df = n_obs - 2 * k - 1
        
        if df <= 0:
            return 1.0
        
        F = (rss_r - rss_f) / (2 * k) / (rss_f / df)
        
        # 转换为p值 (F分布)
        p_value = 1 - self._f_cdf(F, 2 * k, df)
        
        return max(0.0, min(1.0, p_value))
    
    def _build_lag_matrix(self, series: np.ndarray, lag: int) -> np.ndarray:
        """构建滞后矩阵"""
        n = len(series) - lag
        X = np.zeros((n, lag))
        
        for i in range(lag):
            X[:, i] = series[lag - 1 - i:n - 1 - i]
        
        return X
    
    def _build_full_matrix(self, y: np.ndarray, x: np.ndarray, lag: int) -> np.ndarray:
        """构建完整矩阵（含Y和X的滞后）"""
        n = len(y) - lag
        k = 2 * lag
        X = np.zeros((n, k))
        
        # Y的滞后
        for i in range(lag):
            X[:, i] = y[lag - 1 - i:n - 1 - i]
        
        # X的滞后
        for i in range(lag):
            X[:, lag + i] = x[lag - 1 - i:n - 1 - i]
        
        return X
    
    def _ols_rss(self, y: np.ndarray, X: np.ndarray) -> float:
        """普通最小二乘残差平方和"""
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            residual = y - X @ beta
            return np.sum(residual ** 2)
        except:
            return float('inf')
    
    def _f_cdf(self, x: float, d1: int, d2: int) -> float:
        """F分布CDF近似"""
        # 简化：使用一些近似
        if x <= 0:
            return 0.0
        
        # Wilson-Hilferty近似
        z = (x ** (1/3) - (1 - 2/(9*d1)) / (1 - 2/(9*d2))) / \
            math.sqrt(2/(9*d1) + x * 2/(9*d2))
        
        # 标准正态CDF
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


class PCMCI(TemporalCausalModel):
    """
    PCMCI (Peter-Clark MCI for Time Series)
    
    时序因果发现的先进算法
    """
    
    def __init__(self, max_lag: int = 10, alpha: float = 0.05):
        super().__init__(max_lag)
        self.alpha = alpha
        self.lagged_causes: Dict[str, Dict[int, List[str]]] = {}
    
    def fit(self, data: Dict[str, np.ndarray]):
        """
        拟合数据
        """
        self.time_series = data
        variables = list(data.keys())
        
        # 初始化
        for v in variables:
            self.lagged_causes[v] = {}
            for tau in range(1, self.max_lag + 1):
                self.lagged_causes[v][tau] = []
        
        # PC1阶段：条件独立性检验
        pc_results = self._pc_conditioning(data, variables)
        
        # MCI阶段：瞬时和滞后因果
        self._mci_conditioning(data, pc_results)
    
    def _pc_conditioning(self, data: Dict, variables: List[str]) -> Dict:
        """PC1阶段：逐对条件独立性检验"""
        results = {}
        
        for target in variables:
            for cause in variables:
                if cause == target:
                    continue
                
                # 测试不同滞后
                for tau in range(1, self.max_lag + 1):
                    # 简化的条件独立性检验
                    ci_stat, p_value = self._cond_indep_test(
                        cause, target, tau, [], data
                    )
                    
                    key = (cause, target, tau)
                    results[key] = p_value
        
        return results
    
    def _mci_conditioning(self, data: Dict, pc_results: Dict):
        """MCI阶段：滞后因果"""
        variables = list(data.keys())
        
        for target in variables:
            for cause in variables:
                if cause == target:
                    continue
                
                for tau in range(1, self.max_lag + 1):
                    # 构建条件集
                    cond_set = []
                    
                    # 简化的MCI
                    ci_stat, p_value = self._cond_indep_test(
                        cause, target, tau, cond_set, data
                    )
                    
                    if p_value < self.alpha:
                        self.lagged_causes[target][tau].append(cause)
                        self.causal_graph.setdefault(target, []).append(f"{cause}(τ={tau})")
    
    def _cond_indep_test(self, x: str, y: str, tau: int, 
                        z: List, data: Dict) -> Tuple[float, float]:
        """条件独立性检验（偏相关）"""
        # 简化的实现
        # 实际应使用RCOT或GPDC
        
        x_series = data[x]
        y_series = data[y]
        
        # 滞后
        y_lagged = y_series[tau:]
        x_lagged = x_series[:-tau] if tau > 0 else x_series
        
        n = min(len(x_lagged), len(y_lagged))
        x_lagged = x_lagged[:n]
        y_lagged = y_lagged[:n]
        
        # 计算偏相关
        corr = np.corrcoef(x_lagged, y_lagged)[0, 1]
        
        # Fisher z变换
        if abs(corr) >= 0.9999:
            return 0.0, 0.0
        
        z_stat = 0.5 * math.log((1 + corr) / (1 - corr))
        se = 1 / math.sqrt(n - len(z) - 3)
        z_stat_norm = z_stat / se
        
        # p值
        p_value = 2 * (1 - self._normal_cdf(abs(z_stat_norm)))
        
        return abs(corr), max(0.0, min(1.0, p_value))
    
    def _normal_cdf(self, x: float) -> float:
        """标准正态CDF"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def demo_granger_causality():
    """演示Granger因果"""
    print("=== Granger因果检验演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 500
    t = np.linspace(0, 10 * np.pi, n)
    
    # X是随机游走
    X = np.cumsum(np.random.randn(n))
    
    # Y = X的滞后 + 噪声
    Y = 0.8 * np.roll(X, 5) + np.random.randn(n) * 0.5
    Y[:5] = X[:5] * 0.8  # 处理边界
    
    # Z与Y无关
    Z = np.random.randn(n) * 2
    
    data = {'X': X, 'Y': Y, 'Z': Z}
    
    print("时间序列:")
    print("  X: 随机游走")
    print("  Y: 0.8 * X滞后5步 + 噪声")
    print("  Z: 独立噪声")
    
    # Granger检验
    gc = GrangerCausality(max_lag=10, alpha=0.05)
    gc.fit(data)
    
    print("\nGranger因果检验结果 (α=0.05):")
    print("| 原因 | 结果 | p值     | 显著 |")
    print("|------|------|---------|------|")
    
    for (cause, result), pval in gc.p_values.items():
        significant = "是" if pval < 0.05 else "否"
        print(f"| {cause:4s} | {result:4s} | {pval:.6f} | {significant:4s} |")
    
    print("\n因果图:")
    for target, causes in gc.causal_graph.items():
        if causes:
            print(f"  {target} <- {causes}")


def demo_lagged_causation():
    """演示滞后因果"""
    print("\n=== 滞后因果演示 ===\n")
    
    np.random.seed(42)
    
    n = 300
    
    # 生成有滞后因果的数据
    X = np.sin(np.linspace(0, 4*np.pi, n)) + np.random.randn(n) * 0.2
    Y = np.zeros(n)
    
    # Y依赖于X的过去值 (τ=3)
    for t in range(3, n):
        Y[t] = 0.6 * X[t-3] + 0.3 * X[t-5] + np.random.randn() * 0.2
    
    data = {'X': X, 'Y': Y}
    
    print("数据生成:")
    print("  X: 正弦波 + 噪声")
    print("  Y[t] = 0.6*X[t-3] + 0.3*X[t-5] + 噪声")
    
    # PCMCI分析
    pcmci = PCMCI(max_lag=10, alpha=0.05)
    pcmci.fit(data)
    
    print("\n滞后因果发现:")
    print("| τ (滞后) | X对Y的因果 |")
    print("|----------|------------|")
    
    for tau, causes in pcmci.lagged_causes.get('Y', {}).items():
        cause_str = ", ".join(causes) if causes else "无"
        print(f"| {tau:8d} | {cause_str:10s} |")


def demo_causal_graph():
    """演示因果图构建"""
    print("\n=== 因果图构建 ===\n")
    
    print("从时序数据构建因果图:")
    print()
    
    print("1. 变量识别")
    print("   - 从数据中提取变量")
    print("   - 处理缺失值和噪声")
    
    print("\n2. 滞后范围确定")
    print("   - 选择最大滞 后")
    print("   - 考虑因果传递性")
    
    print("\n3. 因果检验")
    print("   - Granger因果")
    print("   - PCMCI")
    print("   - CCU (Convergent Cross Mapping)")
    
    print("\n4. 图后处理")
    print("   - 移除虚假因果")
    print("   - 简化因果路径")


def demo_vs_correlation():
    """演示因果vs相关"""
    print("\n=== 因果 vs 相关 ===\n")
    
    print("例子:")
    print()
    
    print("1. 相关但不因果:")
    print("   - 冰淇淋销量 ↑ 与 溺水人数 ↑ 相关")
    print("   - 共同原因: 夏天/气温")
    print("   - 冰淇淋不导致溺水")
    
    print("\n2. 因果但不立即相关:")
    print("   - X → Y with lag")
    print("   - 需要时序分析才能发现")
    
    print("\n3. 直接因果 vs 间接因果:")
    print("   - X → Y → Z")
    print("   - X → Z (间接)")
    print("   - 需要控制变量才能区分")


if __name__ == "__main__":
    print("=" * 60)
    print("时序因果发现 (Temporal Causal Discovery)")
    print("=" * 60)
    
    # Granger因果
    demo_granger_causality()
    
    # 滞后因果
    demo_lagged_causation()
    
    # 因果图构建
    demo_causal_graph()
    
    # 因果vs相关
    demo_vs_correlation()
    
    print("\n" + "=" * 60)
    print("核心算法:")
    print("=" * 60)
    print("""
1. Granger因果:
   - 基于预测的因果定义
   - X帮助预测Y -> X是Y的原因
   - 需要时序数据

2. PCMCI:
   - PC阶段: 逐对条件独立性
   - MCI阶段: 多变量条件
   - 处理confounding和selection bias

3. CCU (Convergent Cross Mapping):
   - 基于动态系统的因果
   - X导致Y -> Y的历史可以预测X
   - 适合非线性系统

4. 注意事项:
   - 因果 ≠ 相关
   - 时序信息是关键
   - 需要处理滞后
""")

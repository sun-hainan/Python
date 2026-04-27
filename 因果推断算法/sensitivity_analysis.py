# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / sensitivity_analysis

本文件实现 sensitivity_analysis 相关的算法功能。
"""

import numpy as np
from typing import Tuple, List, Optional
import math


class RosenbaumBounds:
    """
    Rosenbaum界限
    
    在未观测混杂下评估因果效应的敏感度
    """
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
    
    def compute_bounds(self, Y: np.ndarray, T: np.ndarray, 
                      gamma: float) -> Tuple[float, float]:
        """
        计算Rosenbaum界限
        
        Args:
            Y: 结果
            T: 处理指示
            gamma: 混杂强度（处理组vs对照组优势比）
        
        Returns:
            (lower_bound, upper_bound)
        """
        n1 = T.sum()
        n0 = (1 - T).sum()
        
        # 处理组和对照组结果排序
        Y1 = Y[T == 1]
        Y0 = Y[T == 0]
        
        # 计算上界（假设gamma=1）
        upper = np.mean(Y1) - np.percentile(Y0, 100 - 100 * n1 / n0)
        
        # 计算下界（假设gamma>1）
        lower = np.percentile(Y1, 100 * n1 / n0) - np.mean(Y0)
        
        return lower, upper


class EValue:
    """
    E值 (Sensitivity Analysis)
    
    评估因果效应敏感度的现代方法
    """
    
    def __init__(self):
        pass
    
    def compute(self, rr: float) -> float:
        """
        计算E值
        
        Args:
            rr: 相对风险（处理效应）
        
        Returns:
            E值
        """
        if rr <= 1:
            return 1.0
        
        # E = RR + sqrt(RR * (RR - 1))
        e_value = rr + math.sqrt(rr * (rr - 1))
        
        return e_value
    
    def interpret(self, e_value: float) -> str:
        """
        解释E值
        
        Returns:
            解释文本
        """
        if e_value < 1.25:
            return "高度敏感：任何中等强度的混杂都可能解释因果效应"
        elif e_value < 2:
            return "中度敏感：需要相当强的混杂才能解释"
        elif e_value < 3:
            return "轻度敏感：需要强混杂"
        else:
            return "不敏感：需要非常强的未观测混杂"
    
    def confidence_interval(self, rr_lower: float, rr_upper: float) -> Tuple[float, float]:
        """
        计算E值的置信区间
        
        Returns:
            (lower_e, upper_e)
        """
        lower_e = self.compute(rr_lower)
        upper_e = self.compute(rr_upper)
        
        return lower_e, upper_e


class ConfoundingStrength:
    """
    混杂强度分析
    
    评估需要多强的混杂才能解释因果效应
    """
    
    def __init__(self):
        pass
    
    def required_confounding(self, ate: float, sigma_y: float, 
                           sigma_x: float) -> float:
        """
        计算需要解释效应的混杂强度
        
        Args:
            ate: 平均处理效应
            sigma_y: 结果标准差
            sigma_x: 协变量标准差
        
        Returns:
            需要的相关系数
        """
        # 简化公式
        # |ATE| <= 2 * rho * sigma_y / sigma_x
        
        rho = abs(ate) * sigma_x / (2 * sigma_y)
        
        return rho
    
    def sensitivity_region(self, ate: float, ate_se: float,
                          sigma_y: float, sigma_x: float) -> Tuple[float, float]:
        """
        计算敏感度区域
        
        Returns:
            (lower_rho, upper_rho)
        """
        ate_lower = ate - 1.96 * ate_se
        ate_upper = ate + 1.96 * ate_se
        
        rho_lower = self.required_confounding(ate_lower, sigma_y, sigma_x)
        rho_upper = self.required_confounding(ate_upper, sigma_y, sigma_x)
        
        return max(0, rho_lower), max(0, rho_upper)


class IVStrengthSensitivity:
    """
    工具变量强度敏感度
    
    评估弱工具变量对IV估计的影响
    """
    
    def __init__(self):
        pass
    
    def weak_iv_threshold(self, f_stat: float, n: int, 
                          k: int) -> bool:
        """
        检查是否为弱工具变量
        
        使用Stock-Yogo检验规则
        
        Args:
            f_stat: 第一阶段F统计量
            n: 样本量
            k: 工具变量数量
        
        Returns:
            True表示弱工具变量
        """
        # 简化规则：F < 10 为弱工具变量
        return f_stat < 10
    
    def bias_approximation(self, f_stat: float, 
                          rho: float) -> float:
        """
        近似弱工具变量导致的偏差
        
        Args:
            f_stat: F统计量
            rho: 工具变量相关性
        
        Returns:
            偏差近似
        """
        # 简化偏差公式
        bias = rho / (f_stat + 1)
        
        return bias


class BenchmarkingSensitivity:
    """
    基准敏感度分析
    
    使用已知因果关系作为基准
    """
    
    def __init__(self, benchmark_effects: dict):
        """
        Args:
            benchmark_effects: 基准效应 {变量名: 效应值}
        """
        self.benchmark_effects = benchmark_effects
    
    def compare(self, estimated_effect: float, 
               target_var: str) -> Tuple[float, str]:
        """
        比较估计效应与基准
        
        Returns:
            (ratio, interpretation)
        """
        if target_var not in self.benchmark_effects:
            return None, "无基准可比"
        
        benchmark = self.benchmark_effects[target_var]
        ratio = estimated_effect / benchmark if benchmark != 0 else 0
        
        if abs(ratio) < 0.5:
            interp = "显著小于基准"
        elif abs(ratio) < 1.5:
            interp = "与基准相近"
        else:
            interp = "显著大于基准"
        
        return ratio, interp


def demo_rosenbaum():
    """演示Rosenbaum界限"""
    print("=== Rosenbaum界限演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 100
    T = np.random.binomial(1, 0.5, n)
    Y = 0.5 * T + np.random.randn(n)
    
    rb = RosenbaumBounds()
    
    # 不同混杂强度下的界限
    print("不同混杂强度下的效应界限:")
    print("| Gamma | 下界 | 上界 |")
    
    for gamma in [1.0, 1.2, 1.5, 2.0]:
        lower, upper = rb.compute_bounds(Y, T, gamma)
        print(f"| {gamma:.1f}   | {lower:.3f} | {upper:.3f} |")
    
    print("\n解释:")
    print("  Gamma=1: 无混杂")
    print("  Gamma>1: 存在未观测混杂")


def demo_evalue():
    """演示E值"""
    print("\n=== E值演示 ===\n")
    
    ev = EValue()
    
    print("E值计算:")
    print("| 相对风险 | E值   | 解释 |")
    
    rr_values = [1.0, 1.2, 1.5, 2.0, 3.0, 5.0]
    
    for rr in rr_values:
        e_val = ev.compute(rr)
        interp = ev.interpret(e_val)[:15]
        print(f"| {rr:.1f}      | {e_val:.2f}  | {interp} |")


def demo_confounding_strength():
    """演示混杂强度分析"""
    print("\n=== 混杂强度分析 ===\n")
    
    cs = ConfoundingStrength()
    
    # 参数
    ate = 1.5
    ate_se = 0.3
    sigma_y = 2.0
    sigma_x = 1.0
    
    rho = cs.required_confounding(ate, sigma_y, sigma_x)
    
    print(f"平均处理效应: {ate:.2f}")
    print(f"需要的相关系数: {rho:.3f}")
    
    if rho < 0.3:
        print("  解释：需要相当强的混杂才能解释效应")
    elif rho < 0.5:
        print("  解释：需要中等强度的混杂")


def demo_weak_iv():
    """演示弱工具变量敏感度"""
    print("\n=== 弱工具变量敏感度 ===\n")
    
    ivs = IVStrengthSensitivity()
    
    print("Stock-Yogo检验规则:")
    print("  F < 10: 弱工具变量")
    print("  F >= 10: 可接受的工具变量")
    
    print("\n偏差近似:")
    for f_stat in [5, 10, 20, 50]:
        for rho in [0.5, 1.0, 2.0]:
            bias = ivs.bias_approximation(f_stat, rho)
            print(f"  F={f_stat:2d}, rho={rho:.1f}: bias≈{bias:.3f}")


def demo_benchmarking():
    """演示基准敏感度分析"""
    print("\n=== 基准敏感度分析 ===\n")
    
    benchmarks = {
        'treatment_effect': 2.0,
        'dose_response': 1.5
    }
    
    bs = BenchmarkingSensitivity(benchmarks)
    
    estimated = 2.3
    ratio, interp = bs.compare(estimated, 'treatment_effect')
    
    print(f"估计效应: {estimated:.2f}")
    print(f"基准效应: {benchmarks['treatment_effect']:.2f}")
    print(f"比率: {ratio:.2f}")
    print(f"解释: {interp}")


if __name__ == "__main__":
    print("=" * 60)
    print("因果推断敏感度分析")
    print("=" * 60)
    
    # Rosenbaum界限
    demo_rosenbaum()
    
    # E值
    demo_evalue()
    
    # 混杂强度
    demo_confounding_strength()
    
    # 弱工具变量
    demo_weak_iv()
    
    # 基准
    demo_benchmarking()
    
    print("\n" + "=" * 60)
    print("敏感度分析方法总结:")
    print("=" * 60)
    print("""
1. Rosenbaum界限:
   - 无分布假设
   - 评估未观测混杂的极端影响
   - 给出效应可能范围

2. E值:
   - 现代方法
   - 直观解释
   - 评估需要多强的混杂

3. 混杂强度分析:
   - 定量评估
   - 相关系数表示
   - 明确假设

4. 弱工具变量:
   - F统计量检验
   - 偏差近似
   - 偏差-方差权衡

5. 最佳实践:
   - 多种方法综合
   - 透明报告假设
   - 保守解释
""")

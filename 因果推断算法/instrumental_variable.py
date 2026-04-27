# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / instrumental_variable

本文件实现 instrumental_variable 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import math


class InstrumentalVariable:
    """
    工具变量估计器
    """
    
    def __init__(self):
        self.instruments: List[str] = []
        self.treatment: str = None
        self.outcome: str = None
        self.covariates: List[str] = []
        
        # 估计结果
        self.causal_effect = None
        self.standard_error = None
    
    def fit(self, data: Dict[str, np.ndarray]):
        """
        拟合IV模型
        
        Args:
            data: 数据字典
        """
        if len(self.instruments) == 0:
            raise ValueError("需要至少一个工具变量")
        
        # 2SLS简化版本
        self._two_stage_least_squares(data)
    
    def _two_stage_least_squares(self, data: Dict[str, np.ndarray]):
        """
        两阶段最小二乘
        
        第一阶段: X = α + πZ + 控制变量 + ε
        第二阶段: Y = β + τX̂ + 控制变量 + ε
        """
        Z = np.column_stack([data[iv] for iv in self.instruments])
        X = data[self.treatment]
        Y = data[self.outcome]
        
        n = len(Y)
        k = Z.shape[1]
        
        # 添加截距
        Z_with_const = np.column_stack([np.ones(n), Z])
        X_with_const = np.column_stack([np.ones(n), X])
        
        # 第一阶段: X̂ = Z @ Π
        # 使用控制变量简化
        X_hat = Z @ np.linalg.lstsq(Z, X, rcond=None)[0]
        
        # 第二阶段
        tau, _, _, _ = np.linalg.lstsq(X_hat.reshape(-1, 1), Y, rcond=None)
        
        self.causal_effect = tau[0]
        
        # 计算标准误（简化）
        residuals = Y - tau[0] * X_hat
        sigma2 = np.var(residuals)
        
        # 简化标准误
        self.standard_error = math.sqrt(sigma2 / n)


class IVEstimator:
    """
    工具变量估计器（多种方法）
    """
    
    def __init__(self, instruments: List[str], treatment: str, outcome: str):
        self.instruments = instruments
        self.treatment = treatment
        self.outcome = outcome
    
    def wald_iv(self, data: Dict[str, np.ndarray]) -> Tuple[float, float]:
        """
        Wald工具变量估计
        
        IV = Cov(Y, Z) / Cov(X, Z)
        
        Returns:
            (估计值, 标准误)
        """
        Z = data[self.instruments[0]]
        X = data[self.treatment]
        Y = data[self.outcome]
        
        # 计算协方差
        cov_yz = np.cov(Y, Z)[0, 1]
        cov_xz = np.cov(X, Z)[0, 1]
        
        # IV估计
        iv_estimate = cov_yz / cov_xz
        
        # 标准误
        n = len(Y)
        residuals = Y - iv_estimate * X
        sigma2 = np.var(residuals)
        se = math.sqrt(sigma2 / (n * cov_xz ** 2))
        
        return iv_estimate, se
    
    def twosls(self, data: Dict[str, np.ndarray]) -> Tuple[float, float]:
        """
        两阶段最小二乘
        """
        Z = np.column_stack([data[iv] for iv in self.instruments])
        X = data[self.treatment]
        Y = data[self.outcome]
        
        n = len(Y)
        k = Z.shape[1]
        
        # 第一阶段
        pi_hat = np.linalg.lstsq(Z, X, rcond=None)[0]
        X_hat = Z @ pi_hat
        
        # 第二阶段
        tau_hat = np.linalg.lstsq(X_hat, Y, rcond=None)[0]
        
        # 残差
        residuals = Y - tau_hat[0] * X_hat
        
        # 标准误
        sigma2 = np.sum(residuals ** 2) / (n - k - 1)
        se = math.sqrt(sigma2 / (n * np.var(X_hat)))
        
        return tau_hat[0], se
    
    def liml(self, data: Dict[str, np.ndarray]) -> Tuple[float, float]:
        """
        有限信息最大似然 (LIML)
        """
        Z = np.column_stack([data[iv] for iv in self.instruments])
        X = data[self.treatment]
        Y = data[self.outcome]
        
        n = len(Y)
        k = Z.shape[1]
        
        # 构建矩阵
        W = np.column_stack([Y, X])
        
        # LIML估计（简化实现）
        # 需要更复杂的实现
        
        return self.twosls(data)


class IVStrength:
    """
    工具变量强度检验
    """
    
    def __init__(self):
        self.first_stage_f = None
    
    def first_stage_f_statistic(self, data: Dict, treatment: str, 
                                instruments: List[str]) -> float:
        """
        第一阶段F统计量
        
        F > 10 通常认为工具变量足够强
        """
        Z = np.column_stack([data[iv] for iv in instruments])
        X = data[treatment]
        
        n = len(X)
        k = Z.shape[1]
        
        # 第一阶段回归
        X_hat = Z @ np.linalg.lstsq(Z, X, rcond=None)[0]
        
        # SSE和SSR
        sse = np.sum((X - X_hat) ** 2)
        ssr = np.sum((X_hat - np.mean(X)) ** 2)
        
        # F统计量
        f_stat = (ssr / k) / (sse / (n - k - 1))
        
        self.first_stage_f = f_stat
        return f_stat


def demo_iv_assumptions():
    """演示IV假设"""
    print("=== 工具变量假设 ===\n")
    
    print("工具变量三个核心假设:")
    print()
    
    print("1. 相关性 (Relevance):")
    print("   Cov(Z, X) ≠ 0")
    print("   工具变量与处理变量相关")
    print()
    
    print("2. 排除性限制 (Exclusion Restriction):")
    print("   Cov(Z, U) = 0")
    print("   Z只通过X影响Y")
    print()
    
    print("3. 排他性 (Excludability):")
    print("   Z与混杂因素无关")
    print()


def demo_weak_iv():
    """演示弱工具变量"""
    print("\n=== 弱工具变量问题 ===\n")
    
    print("弱工具变量定义:")
    print("  F统计量 < 10")
    print()
    
    print("后果:")
    print("  - 估计量偏差大")
    print("  - 标准误膨胀")
    print("  - t检验失效")
    print()
    
    print("诊断:")
    print("  - 第一阶段F统计量")
    print("  - Cragg-Donald统计量")
    print()


def demo_iv_application():
    """演示IV应用"""
    print("\n=== IV应用场景 ===\n")
    
    print("1. 经济学:")
    print("   - 随机实验无法执行")
    print("   - 工具变量来自自然实验")
    print()
    
    print("2. 医学:")
    print("   - 基因变异作为工具变量 (Mendelian Randomization)")
    print("   - 药物副作用因果推断")
    print()
    
    print("3. 社会学:")
    print("   - 出生季节作为教育工具")
    print("   - 征兵抽签作为收入工具")


def demo_iv_simulation():
    """演示IV估计"""
    print("\n=== IV估计演示 ===\n")
    
    np.random.seed(42)
    
    # 生成IV数据
    n = 1000
    
    # 混杂 U
    U = np.random.randn(n)
    
    # 工具变量 Z (只影响X)
    Z = np.random.randn(n)
    
    # 处理变量 X = f(Z) + U
    X = 0.5 * Z + 0.3 * U + np.random.randn(n) * 0.1
    
    # 结果 Y = τX + U + noise
    true_effect = 2.0
    Y = true_effect * X + 0.5 * U + np.random.randn(n) * 0.1
    
    data = {'Z': Z, 'X': X, 'Y': Y}
    
    print("数据生成:")
    print(f"  真实因果效应: {true_effect}")
    print(f"  Z -> X -> Y")
    print(f"  U是混杂因素")
    
    # Wald IV估计
    iv = IVEstimator(['Z'], 'X', 'Y')
    estimate, se = iv.wald_iv(data)
    
    print(f"\nWald IV估计:")
    print(f"  估计值: {estimate:.4f}")
    print(f"  标准误: {se:.4f}")
    
    # 检验强度
    strength = IVStrength()
    f_stat = strength.first_stage_f_statistic(data, 'X', ['Z'])
    print(f"\n第一阶段F统计量: {f_stat:.2f}")
    
    if f_stat < 10:
        print("  (弱工具变量警告!)")
    else:
        print("  (工具变量强度足够)")


if __name__ == "__main__":
    print("=" * 60)
    print("工具变量估计")
    print("=" * 60)
    
    # IV假设
    demo_iv_assumptions()
    
    # 弱工具变量
    demo_weak_iv()
    
    # 应用
    demo_iv_application()
    
    # 模拟
    demo_iv_simulation()
    
    print("\n" + "=" * 60)
    print("工具变量方法总结:")
    print("=" * 60)
    print("""
1. IV估计方法:
   - Wald IV: 单工具变量
   - 2SLS: 多工具变量
   - LIML: 适合弱工具变量

2. 检验:
   - 第一阶段F > 10
   - Sargan过度识别检验
   - Hausman内生性检验

3. 局限性:
   - 需要有效工具变量
   - 排除性限制无法验证
   - 弱工具变量导致问题

4. 应用场景:
   - 随机实验不可行
   - 存在混杂
   - 自然实验可用
""")

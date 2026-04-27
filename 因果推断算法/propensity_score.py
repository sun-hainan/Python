# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / propensity_score

本文件实现 propensity_score 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
import math


class PropensityScore:
    """
    倾向得分估计
    """
    
    def __init__(self):
        self.model = LogisticRegression()
        self.pscore = None
    
    def fit(self, X: np.ndarray, T: np.ndarray):
        """
        拟合倾向得分模型
        
        Args:
            X: 协变量
            T: 处理指示变量
        """
        self.model.fit(X, T)
        self.pscore = self.model.predict_proba(X)[:, 1]
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测倾向得分"""
        return self.model.predict_proba(X)[:, 1]


class PropensityScoreMatching:
    """
    倾向得分匹配
    """
    
    def __init__(self, matching: str = 'nearest', caliper: float = 0.1):
        """
        初始化
        
        Args:
            matching: 匹配方法 ('nearest', 'radius', 'stratification')
            caliper: 卡尺（最大倾向得分差异）
        """
        self.matching = matching
        self.caliper = caliper
        self.pscore_model = PropensityScore()
        
        # 估计结果
        self.ate = None
        self.att = None
        self.atc = None
        self.matched_pairs = None
    
    def fit(self, data: Dict[str, np.ndarray], treatment: str, 
            outcome: str, covariates: List[str]) -> Tuple[float, float]:
        """
        拟合PSM
        
        Args:
            data: 数据字典
            treatment: 处理变量名
            outcome: 结果变量名
            covariates: 协变量名列表
        
        Returns:
            (ATT估计, 标准误)
        """
        # 准备数据
        X = np.column_stack([data[cov] for cov in covariates])
        T = data[treatment]
        Y = data[outcome]
        
        # 估计倾向得分
        self.pscore_model.fit(X, T)
        pscore = self.pscore_model.pscore
        
        # 匹配
        self._matching(pscore, T, Y)
        
        # 计算ATT
        self._compute_att(T, Y, pscore)
        
        # 计算标准误
        se = self._compute_standard_error(T, Y, pscore)
        
        return self.att, se
    
    def _matching(self, pscore: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """执行匹配"""
        treated_idx = np.where(T == 1)[0]
        control_idx = np.where(T == 0)[0]
        
        treated_pscore = pscore[treated_idx]
        control_pscore = pscore[control_idx]
        
        self.matched_pairs = []
        
        for i, t_idx in enumerate(treated_idx):
            # 找最近的对照
            distances = np.abs(treated_pscore[i] - control_pscore)
            
            # 卡尺约束
            if self.matching == 'nearest':
                min_idx = np.argmin(distances)
                if distances[min_idx] <= self.caliper:
                    c_idx = control_idx[min_idx]
                    self.matched_pairs.append((t_idx, c_idx))
        
        # 简化：只保留匹配成功的
        matched_treated = [p[0] for p in self.matched_pairs]
        matched_control = [p[1] for p in self.matched_pairs]
        
        # ATT计算
        att = np.mean(Y[matched_treated]) - np.mean(Y[matched_control])
        self.att = att
    
    def _compute_att(self, T: np.ndarray, Y: np.ndarray, pscore: np.ndarray):
        """计算ATT"""
        if self.att is None:
            self._matching(pscore, T, Y)
    
    def _compute_standard_error(self, T: np.ndarray, Y: np.ndarray, 
                               pscore: np.ndarray) -> float:
        """计算ATT的标准误"""
        treated_idx = np.where(T == 1)[0]
        
        if len(self.matched_pairs) == 0:
            return 0.0
        
        # 简化标准误计算
        effects = []
        for t_idx, c_idx in self.matched_pairs:
            effects.append(Y[t_idx] - Y[c_idx])
        
        se = np.std(effects) / np.sqrt(len(effects))
        return se


class InverseProbabilityWeighting:
    """
    逆概率加权 (IPW)
    
    ATT = E[Y1|T=1] - E[Y0|T=0] * P(T=1)/P(T=0)
    """
    
    def __init__(self):
        self.pscore_model = PropensityScore()
    
    def fit(self, data: Dict[str, np.ndarray], treatment: str,
            outcome: str, covariates: List[str]) -> Tuple[float, float]:
        """
        拟合IPW
        
        Returns:
            (ATE估计, 标准误)
        """
        X = np.column_stack([data[cov] for cov in covariates])
        T = data[treatment]
        Y = data[outcome]
        
        # 倾向得分
        self.pscore_model.fit(X, T)
        pscore = self.pscore_model.pscore
        
        # IPW估计
        # ATT估计
        treated = T == 1
        control = T == 0
        
        # 处理组权重
        weight_treated = np.ones(treated.sum())
        
        # 对照组权重
        weight_control = pscore[control] / (1 - pscore[control])
        
        # ATT
        att = (Y[treated].mean() - 
               (weight_control * Y[control]).sum() / weight_control.sum())
        
        # ATE
        # IPTW
        iptw = T * Y / pscore - (1 - T) * Y / (1 - pscore)
        ate = iptw.mean()
        se = np.std(iptw) / np.sqrt(len(iptw))
        
        self.ate = ate
        return ate, se


class CovariateBalancingPropensityScore:
    """
    协变量平衡倾向得分 (CBPS)
    """
    
    def __init__(self):
        self.weights = None
    
    def fit(self, X: np.ndarray, T: np.ndarray) -> np.ndarray:
        """
        拟合CBPS
        
        Returns:
            权重
        """
        n = len(T)
        
        # 简化：使用倾向得分的倒数
        ps = PropensityScore()
        ps.fit(X, T)
        pscore = ps.pscore
        
        # 权重
        weights = np.zeros(n)
        weights[T == 1] = 1.0 / pscore[T == 1]
        weights[T == 0] = 1.0 / (1 - pscore[T == 0])
        
        self.weights = weights
        return weights


def demo_psm():
    """演示PSM"""
    print("=== 倾向得分匹配演示 ===\n")
    
    np.random.seed(42)
    
    # 生成数据
    n = 1000
    
    # 协变量
    X1 = np.random.randn(n)
    X2 = np.random.randn(n)
    X = np.column_stack([X1, X2])
    
    # 混杂
    confounder = 0.5 * X1 + 0.3 * X2 + np.random.randn(n) * 0.2
    
    # 倾向得分（混杂影响处理选择）
    logit_p = -0.5 + 0.5 * X1 + 0.3 * X2 + 0.8 * confounder
    pscore_true = 1 / (1 + np.exp(-logit_p))
    T = (np.random.rand(n) < pscore_true).astype(int)
    
    # 结果（处理效应 = 2）
    true_effect = 2.0
    Y0 = confounder + np.random.randn(n) * 0.5
    Y1 = Y0 + true_effect + np.random.randn(n) * 0.5
    Y = T * Y1 + (1 - T) * Y0
    
    data = {'T': T, 'Y': Y, 'X1': X1, 'X2': X2}
    
    print(f"样本量: {n}")
    print(f"处理组: {T.sum()}")
    print(f"对照组: {(1-T).sum()}")
    print(f"真实处理效应: {true_effect}")
    
    # PSM
    psm = PropensityScoreMatching(matching='nearest', caliper=0.1)
    att, se = psm.fit(data, 'T', 'Y', ['X1', 'X2'])
    
    print(f"\nPSM结果:")
    print(f"  ATT估计: {att:.4f}")
    print(f"  标准误: {se:.4f}")
    print(f"  95%CI: [{att - 1.96*se:.4f}, {att + 1.96*se:.4f}]")
    
    # IPW
    ipw = InverseProbabilityWeighting()
    ate, se_ate = ipw.fit(data, 'T', 'Y', ['X1', 'X2'])
    
    print(f"\nIPW结果:")
    print(f"  ATE估计: {ate:.4f}")
    print(f"  标准误: {se_ate:.4f}")


def demo_covariate_balance():
    """演示协变量平衡"""
    print("\n=== 协变量平衡检查 ===\n")
    
    print("协变量平衡的重要性:")
    print("  - 匹配后，处理组和对照组在协变量上应该相似")
    print("  - 标准化均值差应该接近0")
    print()
    
    print("标准化均值差 (SMD):")
    print("  SMD = (mean_treated - mean_control) / std_pooled")
    print()
    
    print("判断标准:")
    print("  - SMD < 0.1: 良好平衡")
    print("  - SMD < 0.2: 可接受")
    print("  - SMD > 0.2: 需要改进")


def demo_matching_methods():
    """演示匹配方法"""
    print("\n=== 匹配方法 ===\n")
    
    print("1. 最近邻匹配:")
    print("   - 找倾向得分最近的对照")
    print("   - 简单直观")
    print()
    
    print("2. 卡尺匹配:")
    print("   - 只匹配卡尺内的对照")
    print("   - 提高匹配质量")
    print()
    
    print("3. 分层匹配:")
    print("   - 按倾向得分分层")
    print("   - 每层内计算效应")
    print()
    
    print("4. 半径匹配:")
    print("   - 匹配半径内的所有对照")
    print("   - 更稳定但可能稀释效应")


def demo_ipw_vs_psm():
    """对比IPW和PSM"""
    print("\n=== IPW vs PSM 对比 ===\n")
    
    print("| 特性       | PSM      | IPW       |")
    print("|------------|----------|-----------|")
    print("| 方法       | 匹配     | 加权      |")
    print("| 效率       | 较低     | 较高      |")
    print("| 稳健性     | 较高     | 较低      |")
    print("| 假设       | SUTVA    | 强可忽略性|")
    print("| 大样本性能 | 好       | 依赖模型  |")


if __name__ == "__main__":
    print("=" * 60)
    print("倾向得分匹配")
    print("=" * 60)
    
    # PSM演示
    demo_psm()
    
    # 协变量平衡
    demo_covariate_balance()
    
    # 匹配方法
    demo_matching_methods()
    
    # IPW vs PSM
    demo_ipw_vs_psm()
    
    print("\n" + "=" * 60)
    print("PSM核心:")
    print("=" * 60)
    print("""
1. 倾向得分:
   - P(T=1|X) = 处理倾向
   - 控制了X后，T与Y独立
   
2. 匹配:
   - 基于倾向得分匹配
   - 减少选择偏差
   
3. 估计:
   - ATT: 处理组的平均效应
   - ATE: 平均处理效应
   
4. 假设:
   - 条件独立假设 (CIA)
   - SUTVA
   - 共同支持假设
   
5. 局限性:
   - 需要正确指定倾向得分模型
   - 高维协变量问题
   - 无法处理未观测混杂
""")

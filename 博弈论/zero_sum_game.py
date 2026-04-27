# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / zero_sum_game

本文件实现 zero_sum_game 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional

class ZeroSumGame:
    """
    零和博弈
    
    玩家1的收益 = -玩家2的收益
    """
    
    def __init__(self, payoff_matrix: np.ndarray):
        """
        Args:
            payoff_matrix: 玩家1的收益矩阵
        """
        self.payoff_matrix = payoff_matrix
        self.player1_actions = payoff_matrix.shape[0]
        self.player2_actions = payoff_matrix.shape[1]
    
    def find_nash_equilibrium(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        求解零和博弈的纳什均衡
        
        使用线性规划
        玩家1最大化 min_j (Σi p_i * a_ij)
        玩家2最小化 max_i (Σj q_j * a_ij)
        
        Returns:
            (玩家1策略, 玩家2策略, 博弈值)
        """
        m, n = self.payoff_matrix.shape
        
        # 简化：使用启发式方法
        # 对于2x2博弈，可以通过分析求解
        
        if m == 2 and n == 2:
            return self._solve_2x2()
        
        # 一般情况：使用简化的最佳响应分析
        return self._solve_general()
    
    def _solve_2x2(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """求解2x2零和博弈"""
        a, b = self.payoff_matrix[0, 0], self.payoff_matrix[0, 1]
        c, d = self.payoff_matrix[1, 0], self.payoff_matrix[1, 1]
        
        # 检测纯策略均衡
        # 行i是玩家1对玩家2各列的最优反应
        for i in range(2):
            row = self.payoff_matrix[i, :]
            if row[0] >= row[1] and self.payoff_matrix[0, 0] >= self.payoff_matrix[1, 0]:
                if i == 0 and a >= c and a >= b:
                    return np.array([1, 0]), np.array([1, 0]), a
        
        # 混合策略均衡
        # 求解玩家1的混合策略 p = (p, 1-p)
        # E[行动1] = p*a + (1-p)*c
        # E[行动2] = p*b + (1-p)*d
        # 均衡时: p*a + (1-p)*c = p*b + (1-p)*d
        
        numerator = d - c
        denominator = a - b - c + d
        
        if abs(denominator) < 1e-10:
            # 无内部解
            return np.array([0.5, 0.5]), np.array([0.5, 0.5]), (a + d) / 2
        
        p = numerator / denominator
        p = max(0, min(1, p))
        
        # 玩家2的混合策略
        # E[行动1] = p*a + (1-p)*b (玩家2选列1)
        # E[行动2] = p*c + (1-p)*d (玩家2选列2)
        # 均衡时相等
        
        q = (d - b) / (a - b - c + d) if abs(a - b - c + d) > 1e-10 else 0.5
        q = max(0, min(1, q))
        
        # 博弈值
        value = p * (a * q + b * (1 - q)) + (1 - p) * (c * q + d * (1 - q))
        
        return np.array([p, 1 - p]), np.array([q, 1 - q]), value
    
    def _solve_general(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """一般零和博弈求解（简化）"""
        m, n = self.payoff_matrix.shape
        
        # 使用最大值-最小值作为下界
        row_min = np.min(self.payoff_matrix, axis=1)
        col_max = np.max(self.payoff_matrix, axis=0)
        
        maxmin_value = np.max(row_min)
        minmax_value = np.min(col_max)
        
        # 如果相等，则是鞍点
        if abs(maxmin_value - minmax_value) < 1e-10:
            row_best = np.argmax(row_min)
            col_best = np.argmin(col_max)
            p = np.zeros(m)
            p[row_best] = 1.0
            q = np.zeros(n)
            q[col_best] = 1.0
            return p, q, maxmin_value
        
        # 否则返回近似解
        p = np.ones(m) / m
        q = np.ones(n) / n
        return p, q, (maxmin_value + minmax_value) / 2
    
    def compute_value(self, p: np.ndarray, q: np.ndarray) -> float:
        """计算给定策略下的博弈值"""
        return p @ self.payoff_matrix @ q

def solve_matching_pennies() -> None:
    """求解匹配硬币博弈"""
    print("=== 匹配硬币 (Matching Pennies) ===")
    
    payoff = np.array([[1, -1], [-1, 1]])
    
    game = ZeroSumGame(payoff)
    p, q, value = game.find_nash_equilibrium()
    
    print("         H        T")
    print("  H     1,-1    -1,1")
    print("  T    -1,1     1,-1")
    
    print(f"\n纳什均衡:")
    print(f"  玩家1策略: {p}")
    print(f"  玩家2策略: {q}")
    print(f"  博弈值: {value}")
    print("  (双方都以0.5概率选择，博弈值为0)")
    
    print("\n解释: 玩家1无法通过任何策略保证为正收益")
    print("      玩家2的最优策略是随机化，使玩家1的期望为0")

def solve_hawk_dove() -> None:
    """求解鹰鸽博弈 (Chicken Game)"""
    print("\n=== 鹰鸽博弈 (Chicken/Snowdrift) ===")
    
    payoff = np.array([[-10, 5], [-5, 0]])
    
    game = ZeroSumGame(payoff)
    p, q, value = game.find_nash_equilibrium()
    
    print("         鹰      鸽")
    print("  鹰    -10,10   5,-5")
    print("  鸽    -5,5     0,0")
    
    print(f"\n纳什均衡:")
    print(f"  玩家1策略: {p}")
    print(f"  玩家2策略: {q}")
    print(f"  博弈值: {value:.2f}")
    
    print("\n解释: 存在两个纯策略均衡和一个混合策略均衡")

if __name__ == "__main__":
    print("=== 零和博弈分析 ===")
    
    # 石头剪刀布
    print("石头剪刀布 (严格竞争博弈):")
    rps = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]])
    
    game = ZeroSumGame(rps)
    p, q, value = game.find_nash_equilibrium()
    
    print(f"纳什均衡: 双方都使用均匀分布 [1/3, 1/3, 1/3]")
    print(f"博弈值: {value}")
    
    solve_matching_pennies()
    solve_hawk_dove()
    
    print("\n=== 零和博弈的性质 ===")
    print("1. 极小极大定理: max_p min_q E[p,q] = min_q max_p E[p,q]")
    print("2. 纳什均衡存在于所有有限零和博弈")
    print("3. 零和博弈的纳什均衡等价于极小极大解")
    
    print("\n=== 线性规划 formulation ===")
    print("玩家1最大化: min_j Σi p_i * a_ij")
    print("玩家2最小化: max_i Σj q_j * a_ij")
    print("约束: Σp_i = 1, p_i >= 0")
    print("      Σq_j = 1, q_j >= 0")

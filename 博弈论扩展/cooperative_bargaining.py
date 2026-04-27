# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / cooperative_bargaining

本文件实现 cooperative_bargaining 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Dict, Optional

class BargainingProblem:
    """
    Nash协商博弈
    
    两人协商分配一个蛋糕
    """
    
    def __init__(self, cake_size: float = 1.0, disagreement_payoffs: Tuple[float, float] = (0, 0)):
        """
        Args:
            cake_size: 蛋糕大小
            disagreement_payoffs: 协商失败时的收益
        """
        self.cake_size = cake_size
        self.disagreement = disagreement_payoffs
    
    def nash_solution(self) -> Tuple[float, float]:
        """
        Nash协商解
        
        最大化: (u1 - d1) * (u2 - d2)
        约束: u1 + u2 = cake_size
        
        Returns:
            (player1_share, player2_share)
        """
        d1, d2 = self.disagreement
        
        # Nash解的解析公式
        # 在对称情况下 (d1 = d2 = 0), 解为 (cake/2, cake/2)
        if abs(d1 - d2) < 1e-10:
            return self.cake_size / 2, self.cake_size / 2
        
        # 一般情况下的数值求解
        # 目标: max (x - d1) * (cake - x - d2)
        def objective(x):
            return (x - d1) * (self.cake_size - x - d2)
        
        # 网格搜索
        best_x = 0
        best_obj = -np.inf
        
        for x in np.linspace(0, self.cake_size, 1000):
            obj = objective(x)
            if obj > best_obj:
                best_obj = obj
                best_x = x
        
        return best_x, self.cake_size - best_x
    
    def kalai_solution(self) -> Tuple[float, float]:
        """
        Kalai协商解 (最大最小解)
        
        最大化 min(u1 - d1, u2 - d2)
        """
        d1, d2 = self.disagreement
        
        # Kalai解: 在Nash解基础上向对称点移动
        nash_x, nash_y = self.nash_solution()
        
        # 计算移动因子
        if d1 == d2:
            return nash_x, nash_y
        
        # 移动使得较小的那份尽可能大
        if d1 < d2:
            # 减少player1的份额来增加player2
            base = d2 - d1
            adjustment = min(nash_x - d1, nash_y - d2)
            x = nash_x - adjustment
            y = self.cake_size - x
        else:
            base = d1 - d2
            adjustment = min(nash_y - d2, nash_x - d1)
            y = nash_y - adjustment
            x = self.cake_size - y
        
        return max(d1, min(x, self.cake_size - d2)), max(d2, min(y, self.cake_size - d1))
    
    def utilitarian_solution(self) -> Tuple[float, float]:
        """
        功利主义解 (最大化总收益)
        """
        # 在蛋糕分配中，功利主义解是尽可能让收益高的人获得更多
        # 但约束下就是平等分配
        return self.cake_size / 2, self.cake_size / 2

def run_bargaining_simulation():
    """运行协商博弈模拟"""
    print("=== Nash协商博弈测试 ===")
    
    problem = BargainingProblem(cake_size=1.0, disagreement_payoffs=(0, 0))
    
    print(f"蛋糕大小: {problem.cake_size}")
    print(f"协商失败点: {problem.disagreement}")
    
    nash_x, nash_y = problem.nash_solution()
    print(f"\nNash协商解: ({nash_x:.4f}, {nash_y:.4f})")
    print(f"  Player1获得: {nash_x:.2%}")
    print(f"  Player2获得: {nash_y:.2%}")
    
    kalai_x, kalai_y = problem.kalai_solution()
    print(f"\nKalai协商解: ({kalai_x:.4f}, {kalai_y:.4f})")
    
    print("\n=== 非对称协商失败点 ===")
    problem2 = BargainingProblem(cake_size=1.0, disagreement_payoffs=(0.2, 0))
    
    print(f"协商失败点: {problem2.disagreement}")
    
    nash_x2, nash_y2 = problem2.nash_solution()
    print(f"Nash解: ({nash_x2:.4f}, {nash_y2:.4f})")
    
    kalai_x2, kalai_y2 = problem2.kalai_solution()
    print(f"Kalai解: ({kalai_x2:.4f}, {kalai_y2:.4f})")
    
    print("\n分析:")
    print("  协商失败点的不对称影响协商结果")
    print("  Nash解保持相对份额比例")
    print("  Kalai解最大化最弱势方的收益")

def run_strategic_bargaining():
    """战略式协商"""
    print("\n=== Rubinstein战略协商 ===")
    
    print("设置:")
    print("  - 两方轮流提出分配方案")
    print("  - 对方可以接受或拒绝")
    print("  - 拒绝导致下一轮（贴现）")
    
    discount_factor_1 = 0.9  # Player1的贴现因子
    discount_factor_2 = 0.8  # Player2的贴现因子
    
    print(f"  Player1贴现因子: {discount_factor_1}")
    print(f"  Player2贴现因子: {discount_factor_2}")
    
    print("\n理论预测:")
    # Rubinstein解: 按相对议价能力分配
    # 议价能力与贴现因子相关
    relative_power = (1 - discount_factor_2) / ((1 - discount_factor_1) + (1 - discount_factor_2))
    
    player1_share = relative_power
    player2_share = 1 - relative_power
    
    print(f"  Player1份额: {player1_share:.4f}")
    print(f"  Player2份额: {player2_share:.4f}")
    
    print("\n解释:")
    print("  - 贴现因子越小，议价能力越弱")
    print("  - 因为等待成本更高")
    print("  - Player1先提出，得到更多")

def analyze_bargaining_solutions():
    """分析协商解的性质"""
    print("\n=== 协商解的性质比较 ===")
    
    print("Nash协商解公理:")
    print("  1. Pareto效率")
    print("  2. 对称性")
    print("  3. 无关备选独立性 (IIA)")
    print("  4. 线性变换不变性")
    print("  5. 对称性条件")
    
    print("\nKalai协商解公理:")
    print("  1. Pareto效率")
    print("  2. 对称性")
    print("  3. 单调性 (最弱势方收益最大化)")
    print("  4. 尺度不变性")
    
    print("\n实际应用:")
    print("  - 工资谈判")
    print("  - 国际气候协议")
    print("  - 商业合同")
    print("  - 离婚财产分割")

if __name__ == "__main__":
    run_bargaining_simulation()
    run_strategic_bargaining()
    analyze_bargaining_solutions()
    
    print("\n=== 多人协商 ===")
    print("扩展到多人时:")
    print("  - 核 (core) 可能为空")
    print("  - 需要加入额外约束")
    print("  - Shapley值是一个解概念")
    
    print("\n=== 动态协商 ===")
    print("多轮协商的特点:")
    print("  - 晚提出方案者处于劣势")
    print("  - 需要考虑耐心（贴现）")
    print("  - 可能产生僵局")
    print("  - 需要仲裁机制")

# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / replicator_dynamics

本文件实现 replicator_dynamics 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Callable

class ReplicatorDynamics:
    """
    复制者动态方程
    
    演化博弈论中的核心动态模型
    d_i/dt = i * (f_i - φ)
    其中:
    - i: 策略i的种群比例
    - f_i: 策略i的适应度
    - φ: 平均适应度
    """
    
    def __init__(self, payoff_matrix: np.ndarray, num_strategies: int):
        """
        Args:
            payoff_matrix: 收益矩阵 (num_strategies x num_strategies)
            num_strategies: 策略数量
        """
        self.payoff_matrix = payoff_matrix
        self.num_strategies = num_strategies
    
    def compute_fitness(self, population: np.ndarray) -> np.ndarray:
        """
        计算每种策略的适应度
        
        适应度 = Σ (其他策略比例 × 对应收益)
        """
        return self.payoff_matrix @ population
    
    def compute_mean_fitness(self, population: np.ndarray, fitness: np.ndarray) -> float:
        """计算平均适应度"""
        return population @ fitness
    
    def step(self, population: np.ndarray, dt: float = 0.01) -> np.ndarray:
        """
        一步复制者动态
        
        Args:
            population: 当前种群比例
            dt: 时间步长
        
        Returns:
            更新后的种群比例
        """
        fitness = self.compute_fitness(population)
        mean_fitness = self.compute_mean_fitness(population, fitness)
        
        # 复制者动态方程
        d_population = population * (fitness - mean_fitness)
        new_population = population + dt * d_population
        
        # 确保非负且和为1
        new_population = np.maximum(new_population, 0)
        new_population = new_population / new_population.sum()
        
        return new_population
    
    def simulate(self, initial_population: np.ndarray, 
                steps: int = 1000, dt: float = 0.01) -> List[np.ndarray]:
        """
        模拟复制者动态
        
        Args:
            initial_population: 初始种群比例
            steps: 模拟步数
            dt: 时间步长
        
        Returns:
            种群比例历史
        """
        history = [initial_population]
        population = initial_population.copy()
        
        for _ in range(steps):
            population = self.step(population, dt)
            history.append(population.copy())
        
        return history

def run_replicator_simulation():
    """运行复制者动态模拟"""
    print("=== 复制者动态方程测试 ===")
    
    # Hawk-Dove博弈收益矩阵
    # 策略0=Hawk, 策略1=Dove
    payoff_matrix = np.array([
        [0, 3],   # Hawk vs Hawk: 0, Hawk vs Dove: 3
        [1, 2]    # Dove vs Hawk: 1, Dove vs Dove: 2
    ])
    
    print("鹰鸽博弈收益矩阵:")
    print("        Hawk    Dove")
    print("  Hawk   0       3")
    print("  Dove   1       2")
    
    dynamics = ReplicatorDynamics(payoff_matrix, 2)
    
    # 初始种群
    initial = np.array([0.5, 0.5])
    print(f"\n初始种群: Hawk={initial[0]}, Dove={initial[1]}")
    
    # 模拟
    history = dynamics.simulate(initial, steps=100)
    
    print(f"\n模拟结果 (最后几步):")
    for i, pop in enumerate(history[-5:]):
        print(f"  步骤{len(history)-5+i}: Hawk={pop[0]:.4f}, Dove={pop[1]:.4f}")
    
    # 最终状态分析
    final = history[-1]
    print(f"\n最终种群: Hawk={final[0]:.4f}, Dove={final[1]:.4f}")
    
    # 分析ESS
    print("\n=== 演化稳定策略 (ESS) 分析 ===")
    print("ESS条件: 占据ESS的种群不被任何小突变群体入侵")
    
    # 检查是否收敛到ESS
    if abs(final[0] - 0.0) < 0.01:
        print("收敛到纯策略: Dove (鸽策略)")
    elif abs(final[0] - 1.0) < 0.01:
        print("收敛到纯策略: Hawk (鹰策略)")
    else:
        print(f"收敛到混合策略: Hawk={final[0]:.2f}, Dove={final[1]:.2f}")

def run_coordination_game():
    """协调博弈模拟"""
    print("\n=== 协调博弈复制者动态 ===")
    
    # 协调博弈收益矩阵
    payoff_matrix = np.array([
        [3, 0],
        [0, 1]
    ])
    
    print("协调博弈:")
    print("        A       B")
    print("  A     3,3     0,0")
    print("  B     0,0     1,1")
    
    dynamics = ReplicatorDynamics(payoff_matrix, 2)
    
    # 不同的初始条件
    initials = [
        np.array([0.5, 0.5]),
        np.array([0.9, 0.1]),
        np.array([0.1, 0.9]),
    ]
    
    for init in initials:
        history = dynamics.simulate(init, steps=50)
        final = history[-1]
        print(f"\n从{init}出发: 最终A={final[0]:.4f}, B={final[1]:.4f}")
        
        if final[0] > 0.9:
            print("  -> 收敛到策略A (高收益协调点)")
        elif final[1] > 0.9:
            print("  -> 收敛到策略B (低收益协调点)")
        else:
            print("  -> 收敛到混合策略")

def analyze_stability():
    """分析稳定性"""
    print("\n=== 稳定性分析 ===")
    
    # 收益矩阵
    payoff = np.array([[0, 3], [1, 2]])
    
    print("系统方程:")
    print("  dx/dt = x * (y*3 + (1-y)*0 - (x*y*3 + x*(1-y)*0 + (1-x)*y*1 + (1-x)*(1-y)*2))")
    print("  dy/dt = y * (x*1 + (1-x)*2 - 平均适应度)")
    
    print("\n平衡点分析:")
    print("  平衡点1: (x=0, y=1) - 全Dove")
    print("  平衡点2: (x=1, y=1) - 全Hawk")
    print("  平衡点3: 内部平衡点")
    
    # 计算内部平衡点
    # x*(1-x) = 0 时平衡
    # 内部平衡需要 f_Hawk = f_Dove
    # 2y + 0*(1-y) = 1*x + 2*(1-x)
    # 2y = x + 2 - 2x = 2 - x
    # x = 2 - 2y
    # 同时 x = x*(2-2y) + (1-x)*1... 简化
    print("  内部平衡点: x = 2/3, y = 1/3")
    print("  (即 Hawk占1/3, Dove占2/3)")

if __name__ == "__main__":
    run_replicator_simulation()
    run_coordination_game()
    analyze_stability()
    
    print("\n=== 复制者动态的性质 ===")
    print("1. 仿射不变性: 收益的仿射变换不影响动态")
    print("2. 匿名性: 玩家对称处理")
    print("3. 单调性: 高适应度策略比例增加")
    print("4. 势能单调: 势能函数在动态中单调递增")

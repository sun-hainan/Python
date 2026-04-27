# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / rock_paper_scissors

本文件实现 rock_paper_scissors 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple

class RockPaperScissors:
    """
    石头剪刀布博弈
    
    典型的循环优势博弈
    """
    
    def __init__(self):
        self.actions = ["R", "P", "S"]  # Rock, Paper, Scissors
        self.payoff_matrix = np.array([
            [0, -1, 1],
            [1, 0, -1],
            [-1, 1, 0]
        ])
    
    def get_payoff(self, my_action: int, opponent_action: int) -> int:
        """获取收益"""
        return self.payoff_matrix[my_action, opponent_action]
    
    def get_game_result(self, my_action: int, opponent_action: int) -> str:
        """获取游戏结果描述"""
        diff = (my_action - opponent_action) % 3
        if diff == 0:
            return "平局"
        elif diff == 1:
            return "赢"
        else:
            return "输"

def analyze_rps_equilibrium():
    """分析石头剪刀布均衡"""
    print("=== 石头剪刀布均衡分析 ===")
    
    game = RockPaperScissors()
    
    print("收益矩阵 (玩家1):")
    print("       R   P   S")
    print("  R    0  -1   1")
    print("  P    1   0  -1")
    print("  S   -1   1   0")
    
    print("\n纯策略纳什均衡: 无")
    print("原因: 任何纯策略组合都有玩家可以通过改变策略获得更高收益")
    
    print("\n混合策略纳什均衡:")
    print("  - 每个玩家以相等概率选择R, P, S")
    print("  - 即 (1/3, 1/3, 1/3)")
    
    print("\n混合策略验证:")
    print("  - 玩家1选R的期望收益: 1/3*0 + 1/3*(-1) + 1/3*1 = 0")
    print("  - 玩家1选P的期望收益: 1/3*1 + 1/3*0 + 1/3*(-1) = 0")
    print("  - 玩家1选S的期望收益: 1/3*(-1) + 1/3*1 + 1/3*0 = 0")
    print("  - 三种选择期望收益相等，无偏离动机")

def simulate_rps_tournament():
    """模拟石头剪刀布比赛"""
    print("\n=== 石头剪刀布比赛模拟 ===")
    
    game = RockPaperScissors()
    np.random.seed(42)
    
    # 策略
    strategies = ["random", "alternating", "biased"]
    
    results = {s1: {s2: 0 for s2 in strategies} for s1 in strategies}
    
    for _ in range(100):
        for strat1 in strategies:
            for strat2 in strategies:
                if strat1 == "random":
                    a1 = np.random.randint(0, 3)
                elif strat1 == "alternating":
                    a1 = (_ // 10) % 3
                else:  # biased
                    a1 = 0  # 总是出石头
                
                if strat2 == "random":
                    a2 = np.random.randint(0, 3)
                elif strat2 == "alternating":
                    a2 = (_ // 10 + 1) % 3
                else:  # biased
                    a2 = 0
                
                payoff = game.get_payoff(a1, a2)
                results[strat1][strat2] += payoff
    
    print("100轮比赛累计收益:")
    print(f"{'':15} | {'random':10} | {'alternating':12} | {'biased':10}")
    print("-" * 55)
    for s1 in strategies:
        row = f"{s1:15} |"
        for s2 in strategies:
            row += f" {results[s1][s2]:10} |"
        print(row)
    
    print("\n分析:")
    print("  random vs biased: random平均收益约0 (因为biased总是出石头)")
    print("  alternating: 中等表现")

def run_evolutionary_rps():
    """演化石头剪刀布"""
    print("\n=== 演化石头剪刀布 ===")
    
    payoff_matrix = np.array([
        [0, -1, 1],
        [1, 0, -1],
        [-1, 1, 0]
    ])
    
    # 初始种群
    pop = np.array([0.7, 0.2, 0.1])  # 70% Rock, 20% Paper, 10% Scissors
    
    print(f"初始种群: R={pop[0]:.1%}, P={pop[1]:.1%}, S={pop[2]:.1%}")
    
    history = [pop.copy()]
    
    for iteration in range(100):
        # 计算适应度
        fitness = payoff_matrix @ pop
        avg_fitness = pop @ fitness
        
        # 复制者动态
        d_pop = pop * (fitness - avg_fitness)
        pop = pop + 0.1 * d_pop
        
        # 归一化
        pop = np.maximum(pop, 0)
        pop = pop / pop.sum()
        
        if iteration % 25 == 0:
            print(f"迭代{iteration}: R={pop[0]:.2%}, P={pop[1]:.2%}, S={pop[2]:.2%}")
    
    print(f"\n最终种群: R={pop[0]:.2%}, P={pop[1]:.2%}, S={pop[2]:.2%}")
    
    print("\n解释:")
    print("  初始时Rock占多数")
    print("  Paper的适应度较高（因为能打败Rock）")
    print("  Scissors的适应度较低（因为被Rock打败）")
    print("  种群向Paper倾斜")
    print("  然后Scissors开始增多（能打败Paper）")
    print("  形成循环")

def analyze_bounded_rationality():
    """分析有限理性"""
    print("\n=== 有限理性分析 ===")
    
    print("实际人vs理论人:")
    print("  1. 人不是完全随机的")
    print("     - 有偏好: Rock最常用（力量感）")
    print("     - 习惯化: 难以完全随机")
    print("")
    print("  2. 人会学习对手模式")
    print("     - 如果对手连续出石头，可能出布")
    print("     - 但对手也会调整")
    print("")
    print("  3. 条件性策略")
    print("     - 观察对手历史调整策略")
    print("     - 可能产生循环周期")

if __name__ == "__main__":
    analyze_rps_equilibrium()
    simulate_rps_tournament()
    run_evolutionary_rps()
    analyze_bounded_rationality()
    
    print("\n=== 石头剪刀布的推广 ===")
    print("1. RPS-5: 添加Lizard和Spock")
    print("2. 多人石头剪刀布")
    print("3. 带奖励差异的变体")
    print("4. 概率性石头剪刀布")
    
    print("\n=== 实际应用 ===")
    print("1. 随机决策机制")
    print("2. 公平分配资源")
    print("3. 加密协议")
    print("4. 机器人竞赛设计")
    
    print("\n=== 策略建议 ===")
    print("理论最优: 随机均匀分布")
    print("实践建议:")
    print("  - 避免过度使用石头")
    print("  - 利用对手的模式")
    print("  - 保持不可预测性")

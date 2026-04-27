# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / distributed_game

本文件实现 distributed_game 相关的算法功能。
"""

import numpy as np
import random
from typing import List, Tuple, Dict
from collections import defaultdict

class DistributedGame:
    """
    分布式博弈
    
    多个智能体在分布式环境中进行博弈
    """
    
    def __init__(self, num_agents: int, num_strategies: int):
        self.num_agents = num_agents
        self.num_strategies = num_strategies
        self.payoff_matrix = self._init_payoff_matrix()
    
    def _init_payoff_matrix(self) -> np.ndarray:
        """初始化收益矩阵（简化：所有智能体对称）"""
        return np.random.rand(self.num_strategies, self.num_strategies) * 10
    
    def get_payoff(self, agent_idx: int, strategy_profile: Tuple[int, ...]) -> float:
        """获取智能体的收益"""
        # 简化为对称博弈
        strategies = list(strategy_profile)
        count = defaultdict(int)
        for s in strategies:
            count[s] += 1
        # 基于策略频率计算收益
        return self.payoff_matrix[strategies[agent_idx], strategies[agent_idx]]

class DistributedGameSolver:
    """
    分布式博弈求解器
    
    使用分布式算法寻找纳什均衡
    """
    
    def __init__(self, game: DistributedGame):
        self.game = game
        self.current_strategies = self._init_strategies()
    
    def _init_strategies(self) -> List[int]:
        """初始化策略（随机）"""
        return [random.randint(0, self.game.num_strategies - 1) 
                for _ in range(self.game.num_agents)]
    
    def local_best_response(self, agent_idx: int) -> int:
        """计算局部最优响应"""
        current = self.current_strategies.copy()
        best_payoff = float('-inf')
        best_strategy = current[agent_idx]
        
        for strategy in range(self.game.num_strategies):
            current[agent_idx] = strategy
            payoff = self.game.get_payoff(agent_idx, tuple(current))
            
            if payoff > best_payoff:
                best_payoff = payoff
                best_strategy = strategy
        
        return best_strategy
    
    def best_response_dynamics(self, max_iterations: int = 100) -> Tuple[List[int], int]:
        """
        最佳响应动态
        
        Returns:
            (均衡策略, 迭代次数)
        """
        for iteration in range(max_iterations):
            # 选择一个随机智能体进行最佳响应
            agent_idx = random.randint(0, self.game.num_agents - 1)
            new_strategy = self.local_best_response(agent_idx)
            
            if new_strategy != self.current_strategies[agent_idx]:
                self.current_strategies[agent_idx] = new_strategy
            else:
                # 收敛
                return self.current_strategies, iteration + 1
        
        return self.current_strategies, max_iterations
    
    def fictitious_play(self, max_iterations: int = 100) -> Tuple[List[int], int]:
        """
        虚拟对弈
        
        每个智能体基于历史对手行为频率做最佳响应
        
        Returns:
            (均衡策略, 迭代次数)
        """
        # 初始化历史频率
        history = {i: np.zeros(self.game.num_strategies) 
                  for i in range(self.game.num_agents)}
        
        for iteration in range(max_iterations):
            # 计算每个智能体的信念（对手的混合策略）
            beliefs = []
            for i in range(self.game.num_agents):
                total = history[i].sum()
                if total > 0:
                    belief = history[i] / total
                else:
                    belief = np.ones(self.game.num_strategies) / self.game.num_strategies
                beliefs.append(belief)
            
            # 每个智能体做最佳响应
            new_strategies = []
            for i in range(self.game.num_agents):
                best_payoff = float('-inf')
                best_strategy = 0
                
                for strategy in range(self.game.num_strategies):
                    payoff = 0
                    for j in range(self.game.num_agents):
                        if i != j:
                            payoff += np.dot(beliefs[j], self.game.payoff_matrix[strategy, :])
                    
                    if payoff > best_payoff:
                        best_payoff = payoff
                        best_strategy = strategy
                
                new_strategies.append(best_strategy)
                history[i][best_strategy] += 1
            
            self.current_strategies = new_strategies
            
            # 检查收敛
            if iteration > 0 and self.current_strategies == new_strategies:
                return self.current_strategies, iteration + 1
        
        return self.current_strategies, max_iterations

def run_distributed_game_simulation():
    """分布式博弈模拟"""
    print("=== 分布式博弈测试 ===")
    
    # 创建博弈
    random.seed(42)
    game = DistributedGame(num_agents=5, num_strategies=3)
    
    print(f"智能体数量: {game.num_agents}")
    print(f"策略数量: {game.num_strategies}")
    print(f"收益矩阵:\n{game.payoff_matrix}")
    
    # 创建求解器
    solver = DistributedGameSolver(game)
    
    print("\n=== 最佳响应动态 ===")
    eq1, iters1 = solver.best_response_dynamics()
    print(f"收敛到: {eq1}")
    print(f"迭代次数: {iters1}")
    
    # 重置
    solver = DistributedGameSolver(game)
    
    print("\n=== 虚拟对弈 ===")
    eq2, iters2 = solver.fictitious_play()
    print(f"收敛到: {eq2}")
    print(f"迭代次数: {iters2}")
    
    print("\n=== 多次运行统计 ===")
    results = {"converged": 0, "total_iterations": 0}
    
    for _ in range(10):
        solver = DistributedGameSolver(game)
        _, iters = solver.best_response_dynamics()
        results["total_iterations"] += iters
        if iters < 100:
            results["converged"] += 1
    
    print(f"收敛率: {results['converged']}/10")
    print(f"平均迭代次数: {results['total_iterations'] / 10:.1f}")

def run_network_game():
    """网络博弈"""
    print("\n=== 网络博弈 ===")
    
    # 假设一个社交网络上的博弈
    # 每个节点的收益取决于自己的策略和邻居的策略
    
    num_nodes = 6
    edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,0), (0,2), (1,4)]  # 环形+对角线
    
    print(f"网络: {num_nodes}个节点")
    print(f"边: {edges}")
    
    print("\n协调博弈在网络上的应用:")
    print("  - 每个节点选择策略A或B")
    print("  - 收益 = 与邻居相同策略的奖励 + 与邻居不同策略的惩罚")
    
    print("\n网络效应:")
    print("  - 策略采用具有传染性")
    print("  - 可能收敛到聚类均衡")

if __name__ == "__main__":
    run_distributed_game_simulation()
    run_network_game()
    
    print("\n=== 分布式博弈的应用 ===")
    print("1. 传感器网络: 分布式资源分配")
    print("2. 智能电网: 需求响应协调")
    print("3. 交通网络: 路由优化")
    print("4. 云计算: 资源调度")
    
    print("\n=== 收敛性分析 ===")
    print("1. 最佳响应动态: 不保证收敛到纳什均衡")
    print("2. 虚拟对弈: 在协调博弈中收敛")
    print("3. 势博弈: 总是收敛到纯策略纳什均衡")
    print("4. 超模博弈: 存在纯策略纳什均衡且可收敛")
    
    print("\n=== 算法复杂度 ===")
    print("1. 最佳响应动态: O(T * n * m)")
    print("   T=迭代次数, n=智能体数, m=策略数")
    print("2. 虚拟对弈: O(T * n^2 * m)")
    print("3. 分布式实现: 通信复杂度为O(log n) per round")

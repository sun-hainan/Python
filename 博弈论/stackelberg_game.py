# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / stackelberg_game

本文件实现 stackelberg_game 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional

class StackelbergGame:
    """
    Stackelberg博弈 - 领导者-追随者博弈
    
    领导者先选择策略，追随者观察到领导者的选择后进行响应
    """
    
    def __init__(self, leader_strategies: List[str], follower_strategies: List[str],
                 leader_payoffs: np.ndarray, follower_payoffs: np.ndarray):
        self.leader_strategies = leader_strategies
        self.follower_strategies = follower_strategies
        self.leader_payoffs = leader_payoffs
        self.follower_payoffs = follower_payoffs
    
    def follower_best_response(self, leader_action: int) -> int:
        """
        追随者对领导者的最优响应
        
        Args:
            leader_action: 领导者的行动索引
        
        Returns:
            追随者的最优行动索引
        """
        # 追随者选择使其收益最大化的策略
        follower_payoffs_for_leader_action = self.follower_payoffs[:, leader_action]
        return int(np.argmax(follower_payoffs_for_leader_action))
    
    def leader_best_action(self) -> Tuple[int, List[int]]:
        """
        领导者的最优行动
        
        Returns:
            (领导者行动, 追随者的响应动作列表)
        """
        leader_values = []
        follower_responses = []
        
        for leader_action in range(len(self.leader_strategies)):
            # 追随者的响应
            follower_response = self.follower_best_response(leader_action)
            follower_responses.append(follower_response)
            
            # 领导者在追随者响应下的收益
            leader_value = self.leader_payoffs[follower_response, leader_action]
            leader_values.append(leader_value)
        
        # 领导者选择使自身收益最大化的行动
        best_action = int(np.argmax(leader_values))
        return best_action, follower_responses
    
    def solve_stackelberg_equilibrium(self) -> Dict:
        """
        求解Stackelberg均衡
        
        Returns:
            均衡结果
        """
        leader_action, follower_responses = self.leader_best_action()
        follower_action = follower_responses[leader_action]
        
        leader_payoff = self.leader_payoffs[follower_action, leader_action]
        follower_payoff = self.follower_payoffs[follower_action, leader_action]
        
        return {
            "leader_action": self.leader_strategies[leader_action],
            "follower_action": self.follower_strategies[follower_action],
            "leader_payoff": leader_payoff,
            "follower_payoff": follower_payoff,
            "leader_action_idx": leader_action,
            "follower_action_idx": follower_action
        }

def solve_stackelberg_with_mixed_strategies(
    leader_strategies: List[str],
    follower_strategies: List[str],
    leader_payoffs: np.ndarray,
    follower_payoffs: np.ndarray,
    leader_beliefs: np.ndarray = None
) -> Dict:
    """
    求解混合策略Stackelberg均衡（简化版）
    
    Args:
        leader_strategies: 领导者策略列表
        follower_strategies: 追随者策略列表
        leader_payoffs: 领导者收益矩阵 (follower_actions x leader_actions)
        follower_payoffs: 追随者收益矩阵 (follower_actions x leader_actions)
        leader_beliefs: 领导者对追随者类型的信念
    
    Returns:
        均衡结果
    """
    n_leader = len(leader_strategies)
    n_follower = len(follower_strategies)
    
    # 如果没有提供信念，使用均匀分布
    if leader_beliefs is None:
        leader_beliefs = np.ones(n_follower) / n_follower
    
    # 计算每种领导者行动的期望追随者收益
    expected_follower_payoffs = np.dot(leader_beliefs, follower_payoffs.T)
    
    # 追随者会选择使期望收益最大的行动
    follower_best = np.argmax(expected_follower_payoffs)
    
    # 领导者在追随者响应下的最优行动
    # 考虑追随者会响应领导者的行动
    leader_values = np.array([
        leader_payoffs[follower_best, a] if a == follower_best else 
        np.min(leader_payoffs[:, a])  # 最坏情况
        for a in range(n_leader)
    ])
    
    best_leader_action = np.argmax(leader_values)
    
    return {
        "leader_action": leader_strategies[best_leader_action],
        "follower_action": follower_strategies[follower_best],
        "leader_expected_payoff": float(leader_values[best_leader_action]),
        "follower_expected_payoff": float(expected_follower_payoffs[follower_best])
    }

if __name__ == "__main__":
    print("=== Stackelberg博弈测试 ===")
    
    # 简单价格竞争博弈
    leader_strategies = ["高价", "低价"]
    follower_strategies = ["配合", "降价"]
    
    # 领导者收益矩阵
    leader_payoffs = np.array([
        [10, 5],   # 追随者配合时：高价=10, 低价=5
        [8, 3]     # 追随者降价时：高价=8, 低价=3
    ])
    
    # 追随者收益矩阵
    follower_payoffs = np.array([
        [10, 2],   # 追随者配合时：高价=10, 低价=2
        [5, 3]     # 追随者降价时：高价=5, 低价=3
    ])
    
    print("价格竞争博弈:")
    print("领导者(厂商1)/追随者(厂商2) | 配合 | 降价")
    print("  高价/配合: 领导10, 追随10")
    print("  高价/降价: 领导8, 追随5")
    print("  低价/配合: 领导5, 追随2")
    print("  低价/降价: 领导3, 追随3")
    
    game = StackelbergGame(leader_strategies, follower_strategies, 
                          leader_payoffs, follower_payoffs)
    
    print("\n=== 纯策略Stackelberg均衡 ===")
    equilibrium = game.solve_stackelberg_equilibrium()
    print(f"领导者选择: {equilibrium['leader_action']}")
    print(f"追随者响应: {equilibrium['follower_action']}")
    print(f"领导者收益: {equilibrium['leader_payoff']}")
    print(f"追随者收益: {equilibrium['follower_payoff']}")
    
    print("\n=== 追随者响应函数 ===")
    for i, leader_action in enumerate(leader_strategies):
        response = game.follower_best_response(i)
        print(f"如果领导者选择'{leader_action}': 追随者选择'{follower_strategies[response]}'")
    
    print("\n=== 对比Nash均衡 ===")
    # 囚徒困境类型的Stackelberg
    pd_leader = ["坦白", "抵赖"]
    pd_follower = ["坦白", "抵赖"]
    pd_leader_payoffs = np.array([
        [-5, 0],
        [-10, -1]
    ])
    pd_follower_payoffs = np.array([
        [-5, -10],
        [0, -1]
    ])
    
    pd_game = StackelbergGame(pd_leader, pd_follower, 
                             pd_leader_payoffs, pd_follower_payoffs)
    pd_eq = pd_game.solve_stackelberg_equilibrium()
    print(f"囚徒困境 Stackelberg均衡:")
    print(f"  领导者: {pd_eq['leader_action']}")
    print(f"  追随者: {pd_eq['follower_action']}")
    print(f"  (Nash均衡是 坦白/坦白, Stackelberg会导致领导者选择坦白)")
    
    print("\n=== 混合策略测试 ===")
    mixed_eq = solve_stackelberg_with_mixed_strategies(
        leader_strategies, follower_strategies,
        leader_payoffs, follower_payoffs
    )
    print(f"混合策略均衡:")
    print(f"  领导者: {mixed_eq['leader_action']}")
    print(f"  追随者: {mixed_eq['follower_action']}")
    print(f"  领导者期望收益: {mixed_eq['leader_expected_payoff']:.2f}")
    print(f"  追随者期望收益: {mixed_eq['follower_expected_payoff']:.2f}")

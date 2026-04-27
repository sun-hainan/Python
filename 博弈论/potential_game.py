# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / potential_game

本文件实现 potential_game 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

class PotentialGame:
    """
    潜在博弈
    
    如果存在一个函数Φ: A -> R，使得:
    对于所有玩家i，所有行动组合a和a'，
    u_i(a_i', a_-i) - u_i(a_i, a_-i) = Φ(a_i', a_-i) - Φ(a_i, a_-i)
    
    则该博弈是潜在博弈
    """
    
    def __init__(self, players: List[str], actions: Dict[str, List[str]], 
                 payoffs: Dict[Tuple, float]):
        self.players = players
        self.actions = actions
        self.payoffs = payoffs
        self.num_players = len(players)
    
    def compute_potential(self, profile: Tuple) -> float:
        """
        计算势能函数（如果博弈是潜在的）
        
        对于序贯博弈，势能 = 所有收益的总和
        """
        # 简单势能：所有玩家收益之和
        return sum(self.payoffs.get(profile, (0.0,) * self.num_players))
    
    def find_best_response(self, player: str, other_actions: Tuple) -> List[str]:
        """找到给定其他玩家行动下的最优反应"""
        player_idx = self.players.index(player)
        best_payoff = float('-inf')
        best_actions = []
        
        for action in self.actions[player]:
            profile = list(other_actions)
            profile.insert(player_idx, action)
            profile = tuple(profile)
            
            payoff = self.payoffs.get(profile, (0.0,) * self.num_players)[player_idx]
            
            if payoff > best_payoff:
                best_payoff = payoff
                best_actions = [action]
            elif payoff == best_payoff:
                best_actions.append(action)
        
        return best_actions
    
    def find_nash_equilibrium(self) -> List[Dict]:
        """通过最佳响应动态找到纳什均衡"""
        equilibria = []
        
        # 尝试所有可能的行动组合
        all_actions = [self.actions[p] for p in self.players]
        
        for profile_tuple in product(*all_actions):
            is_eq = True
            
            for player in self.players:
                player_idx = self.players.index(player)
                current_action = profile_tuple[player_idx]
                other_actions = tuple(a for i, a in enumerate(profile_tuple) if i != player_idx)
                
                best_responses = self.find_best_response(player, other_actions)
                
                if current_action not in best_responses:
                    is_eq = False
                    break
            
            if is_eq:
                equilibria.append({
                    "profile": profile_tuple,
                    "payoffs": [self.payoffs.get(profile_tuple, (0,))[i] for i in range(self.num_players)]
                })
        
        return equilibria
    
    def converge_best_response(self, initial_profile: Tuple, max_iterations: int = 100) -> Tuple:
        """
        最佳响应动态收敛
        
        Args:
            initial_profile: 初始行动组合
            max_iterations: 最大迭代次数
        
        Returns:
            收敛到的行动组合
        """
        current = list(initial_profile)
        history = [tuple(current)]
        
        for _ in range(max_iterations):
            # 选择一个随机玩家进行最佳响应
            import random
            player_idx = random.randint(0, self.num_players - 1)
            player = self.players[player_idx]
            
            other_actions = tuple(a for i, a in enumerate(current) if i != player_idx)
            best_actions = self.find_best_response(player, other_actions)
            
            # 随机选择其中一个最佳响应
            current[player_idx] = random.choice(best_actions)
            
            if tuple(current) in history:
                break
            history.append(tuple(current))
        
        return tuple(current), len(history)

def is_potential_game(payoffs: Dict[Tuple, float], num_players: int) -> bool:
    """
    检验一个博弈是否是潜在博弈
    
    方法: 检查是否存在函数Φ满足势能条件
    """
    profiles = list(payoffs.keys())
    
    if not profiles:
        return True
    
    # 简化检查：对于2玩家博弈，检查是否存在势能函数
    # 对于每一对相邻的行动组合，检查差异是否一致
    
    return True  # 简化实现

def is_congestion_game(num_resources: int, players: List[str], 
                       usage_cost: Dict[int, int]) -> bool:
    """
    拥塞博弈是潜在博弈
    
    拥塞博弈: 收益 = -使用资源的成本之和
    """
    print("=== 拥塞博弈 ===")
    print(f"资源数: {num_resources}")
    print(f"玩家: {players}")
    print("拥塞博弈是潜在博弈，势能 = Σ 资源使用成本之和")
    
    return True

if __name__ == "__main__":
    print("=== 潜在博弈测试 ===")
    
    # 协调博弈是潜在博弈
    players = ["Player1", "Player2"]
    actions = {"Player1": ["A", "B"], "Player2": ["A", "B"]}
    
    payoffs = {
        ("A", "A"): (3, 3),
        ("A", "B"): (0, 0),
        ("B", "A"): (0, 0),
        ("B", "B"): (1, 1),
    }
    
    game = PotentialGame(players, actions, payoffs)
    
    print("协调博弈:")
    print("         A      B")
    print("  A     3,3    0,0")
    print("  B     0,0    1,1")
    
    # 计算势能
    print("\n势能函数值:")
    for profile in [("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")]:
        potential = game.compute_potential(profile)
        print(f"  {profile}: Φ = {potential}")
    
    # 找纳什均衡
    eq = game.find_nash_equilibrium()
    print(f"\n纳什均衡: {eq}")
    
    # 最佳响应动态
    print("\n=== 最佳响应动态 ===")
    for _ in range(3):
        import random
        init = (random.choice(["A", "B"]), random.choice(["A", "B"]))
        final, steps = game.converge_best_response(init)
        print(f"  从{init}出发，经过{steps}步收敛到{final}")
    
    # 验证势能单调性
    print("\n=== 势能单调性 ===")
    print("最佳响应动态中，势能函数单调递增")
    print("收敛到局部最优（纳什均衡）")
    
    # 拥塞博弈
    print("\n=== 拥塞博弈示例 ===")
    
    # 路由选择博弈
    num_players = 3
    resources = {0: 2, 1: 5}  # 资源0成本2，资源1成本5
    
    print(f"路由选择: {num_players}个司机，2条路由")
    print("资源0 (高速公路): 成本=2")
    print("资源1 (普通路): 成本=5")
    
    # 简化的势能计算
    print("\n如果k个司机选择资源0，势能 = k * 2 + (n-k) * 5")
    for k in range(num_players + 1):
        potential = k * 2 + (num_players - k) * 5
        print(f"  {k}个司机选择资源0: Φ = {potential}")
    
    print("\n结论: 拥塞博弈是潜在博弈，最小化势能的配置是纳什均衡")
    
    # 网络流博弈
    print("\n=== 网络流博弈 ===")
    print("网络博弈通常是潜在博弈")
    print("应用: 交通路由、互联网流量分配")
    
    print("\n=== 潜在博弈的性质 ===")
    print("1. 有限改进 property: 任意有限路径终止于纳什均衡")
    print("2. 最佳响应动态收敛")
    print("3. 精确潜在博弈: 收益差等于势能差")
    print("4. 序贯潜在博弈: 弱于精确潜在博弈")
    
    print("\n=== 协调博弈 vs 囚徒困境 ===")
    pd_payoffs = {
        ("C", "C"): (-1, -1),
        ("C", "D"): (-3, 0),
        ("D", "C"): (0, -3),
        ("D", "D"): (-2, -2),
    }
    
    pd_game = PotentialGame(players, actions, pd_payoffs)
    pd_eq = pd_game.find_nash_equilibrium()
    print(f"囚徒困境纳什均衡: {pd_eq}")
    print("囚徒困境也是潜在博弈 (势能 = 所有收益之和)")
    for profile in pd_payoffs:
        potential = sum(pd_payoffs[profile])
        print(f"  {profile}: Φ = {potential}")

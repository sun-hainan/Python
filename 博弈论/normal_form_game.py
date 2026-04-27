# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / normal_form_game

本文件实现 normal_form_game 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from itertools import product

class NormalFormGame:
    """
    标准形式博弈分析
    
    标准形式博弈 G = (N, A, u) 其中:
    - N: 玩家集合
    - A: 行动空间
    - u: 收益函数
    """
    
    def __init__(self, players: List[str], payoffs: Dict[Tuple, Tuple[float, ...]]):
        self.players = players
        self.payoffs = payoffs
        self.num_players = len(players)
    
    def get_payoffs(self, profile: Tuple[str, ...]) -> Tuple[float, ...]:
        """获取策略组合的收益"""
        return self.payoffs.get(profile, (0.0,) * self.num_players)
    
    def find_nash_eq_pure(self) -> List[Dict]:
        """
        寻找纯策略纳什均衡
        
        Returns:
            纳什均衡列表
        """
        equilibria = []
        
        # 获取每个玩家的行动数
        player_actions = {}
        all_actions = set()
        for profile in self.payoffs.keys():
            for i, action in enumerate(profile):
                if self.players[i] not in player_actions:
                    player_actions[self.players[i]] = set()
                player_actions[self.players[i]].add(action)
        
        # 检查每个策略组合是否是均衡
        for profile in self.payoffs.keys():
            is_eq = True
            payoffs = self.get_payoffs(profile)
            
            for i, player in enumerate(self.players):
                current_action = profile[i]
                current_payoff = payoffs[i]
                
                # 检查是否存在严格更好的行动
                for other_action in player_actions[player]:
                    if other_action == current_action:
                        continue
                    
                    # 构造新的策略组合
                    new_profile_list = list(profile)
                    new_profile_list[i] = other_action
                    new_profile = tuple(new_profile_list)
                    
                    new_payoffs = self.get_payoffs(new_profile)
                    new_payoff = new_payoffs[i]
                    
                    if new_payoff > current_payoff:
                        is_eq = False
                        break
                
                if not is_eq:
                    break
            
            if is_eq:
                equilibria.append({
                    "profile": profile,
                    "payoffs": payoffs
                })
        
        return equilibria
    
    def find_dominated_strategies(self, player: str) -> List[str]:
        """
        找出被支配的策略
        
        Args:
            player: 玩家名称
        
        Returns:
            被支配的策略列表
        """
        dominated = []
        player_idx = self.players.index(player)
        
        # 获取该玩家的所有策略
        player_strategies = set()
        for profile in self.payoffs.keys():
            player_strategies.add(profile[player_idx])
        
        strategies = list(player_strategies)
        
        for i, strategy in enumerate(strategies):
            for j, other_strategy in enumerate(strategies):
                if i == j:
                    continue
                
                # 检查other_strategy是否支配strategy
                is_dominated = True
                
                for profile in self.payoffs.keys():
                    if profile[player_idx] != strategy:
                        continue
                    
                    # 获取当前策略组合的收益
                    current_payoff = self.get_payoffs(profile)[player_idx]
                    
                    # 获取替换后的收益
                    new_profile_list = list(profile)
                    new_profile_list[player_idx] = other_strategy
                    new_profile = tuple(new_profile_list)
                    new_payoff = self.get_payoffs(new_profile)[player_idx]
                    
                    if current_payoff >= new_payoff:
                        is_dominated = False
                        break
                
                if is_dominated:
                    dominated.append(strategy)
        
        return list(set(dominated))

def create_game_from_matrix(player1_payoffs: np.ndarray, 
                           player2_payoffs: np.ndarray,
                           player1_actions: List[str] = None,
                           player2_actions: List[str] = None) -> NormalFormGame:
    """从收益矩阵创建博弈"""
    if player1_actions is None:
        player1_actions = [f"R{i}" for i in range(player1_payoffs.shape[0])]
    if player2_actions is None:
        player2_actions = [f"C{i}" for i in range(player1_payoffs.shape[1])]
    
    players = ["Player1", "Player2"]
    payoffs = {}
    
    for i, r in enumerate(player1_actions):
        for j, c in enumerate(player2_actions):
            profile = (r, c)
            payoffs[profile] = (player1_payoffs[i, j], player2_payoffs[i, j])
    
    return NormalFormGame(players, payoffs)

if __name__ == "__main__":
    print("=== 标准形式博弈分析 ===")
    
    # 协调博弈
    coordination_payoffs = np.array([
        [4, 0],
        [0, 2]
    ])
    
    game = create_game_from_matrix(coordination_payoffs, coordination_payoffs,
                                  ["合作", "背叛"], ["合作", "背叛"])
    
    print("协调博弈:")
    print("         合作    背叛")
    print("  合作   4,4    0,0")
    print("  背叛   0,0    2,2")
    
    eq = game.find_nash_eq_pure()
    print(f"\n纯策略纳什均衡: {eq}")
    
    # 性别之战
    print("\n=== 性别之战 ===")
    bos_p1 = np.array([[2, 0], [0, 1]])
    bos_p2 = np.array([[1, 0], [0, 2]])
    
    bos_game = create_game_from_matrix(bos_p1, bos_p2,
                                      ["足球", "歌剧"], ["足球", "歌剧"])
    
    print("         足球    歌剧")
    print("  足球   2,1    0,0")
    print("  歌剧   0,0    1,2")
    
    bos_eq = bos_game.find_nash_eq_pure()
    print(f"\n纳什均衡: {bos_eq}")
    
    # 囚徒困境
    print("\n=== 囚徒困境 ===")
    pd_p1 = np.array([[-5, 0], [-10, -1]])
    pd_p2 = np.array([[-5, -10], [0, -1]])
    
    pd_game = create_game_from_matrix(pd_p1, pd_p2,
                                     ["坦白", "抵赖"], ["坦白", "抵赖"])
    
    print("         坦白    抵赖")
    print("  坦白   -5,-5   0,-10")
    print("  抵赖   -10,0  -1,-1")
    
    pd_eq = pd_game.find_nash_eq_pure()
    print(f"\n纳什均衡: {pd_eq}")
    
    dominated = pd_game.find_dominated_strategies("Player1")
    print(f"Player1的被支配策略: {dominated}")
    
    # 石头剪刀布
    print("\n=== 石头剪刀布 ===")
    rps_p1 = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]])
    rps_p2 = np.array([[0, 1, -1], [-1, 0, 1], [1, -1, 0]])
    
    rps_game = create_game_from_matrix(rps_p1, rps_p2,
                                       ["石头", "剪刀", "布"],
                                       ["石头", "剪刀", "布"])
    
    print("         石头    剪刀    布")
    print("  石头   0,0    -1,1    1,-1")
    print("  剪刀   1,-1   0,0     -1,1")
    print("  布     -1,1   1,-1    0,0")
    
    rps_eq = rps_game.find_nash_eq_pure()
    print(f"\n纯策略纳什均衡: {rps_eq}")
    print("(石头剪刀布没有纯策略均衡，只有混合策略均衡)")

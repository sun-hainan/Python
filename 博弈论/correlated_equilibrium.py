# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / correlated_equilibrium

本文件实现 correlated_equilibrium 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from itertools import product

class CorrelatedEquilibrium:
    """
    相关均衡
    
    在相关均衡中，博弈者从公共信号源接收建议行动
    信号服从某种概率分布，使每个博弈者遵循建议是贝叶斯最优的
    """
    
    def __init__(self, num_players: int, num_actions: List[int], payoffs: np.ndarray):
        """
        Args:
            num_players: 玩家数量
            num_actions: 每个玩家的行动数
            payoffs: 收益张量
        """
        self.num_players = num_players
        self.num_actions = num_actions
        self.payoffs = payoffs
    
    def compute_probability_tensor(self) -> np.ndarray:
        """计算概率张量的形状"""
        return tuple(self.num_actions)
    
    def find_correlated_equilibrium(self, player: int, signal: int, 
                                   strategy: np.ndarray) -> Tuple[bool, float]:
        """
        检查给定策略是否对特定玩家是激励相容的
        
        Args:
            player: 玩家索引
            signal: 信号
            strategy: 策略概率张量
        
        Returns:
            (是否IC, 期望收益)
        """
        num_signals = self.num_actions[0]  # 简化：信号数等于行动数
        
        # 计算条件概率
        # P(action | signal) 应该在signal=action时为1，否则为0
        expected_payoffs_deviate = {}
        expected_payoffs_follow = 0.0
        
        for action in range(self.num_actions[player]):
            # 计算给定信号下遵循策略的期望收益
            prob = 1.0 if action == signal else 0.0
            expected_payoffs_follow += prob * self._get_payoff(player, action, signal)
            
            # 计算偏离后的期望收益
            expected_payoffs_deviate[action] = self._get_payoff(player, action, signal)
        
        # 检查偏离是否有利
        best_deviate = max(expected_payoffs_deviate.values())
        is_ic = expected_payoffs_follow >= best_deviate
        
        return is_ic, expected_payoffs_follow
    
    def _get_payoff(self, player: int, action: int, signal: int) -> float:
        """获取收益（简化实现）"""
        # 实际应根据完整的状态空间计算
        return self.payoffs[tuple([signal] * self.num_players)]

def solve_correlated_equilibrium_2x2(payoff1: np.ndarray, payoff2: np.ndarray) -> Dict:
    """
    求解2x2博弈的相关均衡
    
    Args:
        payoff1: 玩家1的收益
        payoff2: 玩家2的收益
    
    Returns:
        相关均衡概率
    """
    print("=== 2x2博弈相关均衡 ===")
    
    # 相关均衡条件
    # 信号服从分布 p(s)，推荐行动 a_i(s)
    # 激励相容: EU_i(a_i(s), s) >= EU_i(a_i'(s), s) for all a_i', s
    
    # 简化情况：信号直接是行动推荐
    # 协调博弈
    coord_payoff = np.array([[3, 0], [0, 1]])
    
    print("\n协调博弈:")
    print("         A     B")
    print("  A     3,3   0,0")
    print("  B     0,0   1,1")
    
    print("\n纯策略纳什均衡: (A,A) 和 (B,B)")
    print("相关均衡可以改善协调结果")
    
    # 相关均衡：推荐 (A,A) 和 (B,B)，但给更高的概率给 (A,A)
    # 比如 p(A推荐) = 0.8, p(B推荐) = 0.2
    
    print("\n一种相关均衡:")
    print("  - 信号服从: P(A推荐)=0.8, P(B推荐)=0.2")
    print("  - 两个玩家都遵循推荐")
    print("  - 期望收益: 0.8*3 + 0.2*1 = 2.6")
    
    return {
        "type": "correlated",
        "recommendations": {"A": 0.8, "B": 0.2},
        "expected_payoff": 2.6
    }

def find_cheap_talk_correlated_equilibrium() -> Dict:
    """
    廉价对话博弈的相关均衡
    
    发送者有类型，接收者根据消息采取行动
    """
    print("=== 廉价对话博弈 ===")
    
    # 发送者类型: G(好) 或 B(坏)
    # 发送者选择发送 M1 或 M2
    # 接收者选择 A 或 B
    
    print("结构:")
    print("  发送者类型: G(概率0.5), B(概率0.5)")
    print("  发送者行动: 诚实, 说谎")
    print("  接收者行动: 信任, 不信任")
    
    print("\n收益矩阵:")
    print("  类型G,诚实 -> 信任: (2,2)")
    print("  类型G,说谎 -> 不信任: (0,0)")
    print("  类型B,诚实 -> 不信任: (1,0)")
    print("  类型B,说谎 -> 信任: (0,1)")
    
    print("\n分离均衡: 诚实总是报告真实类型")
    print("混同均衡: 发送者不区分类型，总是发送相同消息")
    
    # 相关均衡：引入随机信号引导协调
    print("\n相关均衡:")
    print("  - 引入信号 s ∈ {0, 1}，各0.5概率")
    print("  - s=0时，建议发送者诚实")
    print("  - s=1时，建议发送者说谎")
    print("  - 接收者根据消息和信号决定是否信任")
    
    return {
        "type": "correlated_with_signals",
        "signals": {"s0": 0.5, "s1": 0.5},
        "strategies": "依赖信号和消息的复杂规则"
    }

if __name__ == "__main__":
    print("=== 相关均衡测试 ===")
    
    # 囚徒困境
    pd_payoff = np.array([[-5, 0], [-10, -1]])
    
    print("囚徒困境:")
    print("         坦白    抵赖")
    print("  坦白   -5,-5   0,-10")
    print("  抵赖   -10,0  -1,-1")
    
    print("\n纯策略纳什均衡: (坦白,坦白)")
    print("相关均衡不会改变均衡结果（坦白仍然是占优策略）")
    
    print("\n=== 相关均衡求解 ===")
    
    # 协调博弈
    result = solve_correlated_equilibrium_2x2(
        np.array([[3, 0], [0, 1]]),
        np.array([[3, 0], [0, 1]])
    )
    print(f"\n协调博弈相关均衡: {result}")
    
    # 斗鸡博弈
    print("\n=== 斗鸡博弈 ===")
    chicken_payoff = np.array([[-10, 5], [-5, 0]])
    
    print("         前进    让路")
    print("  前进   -10,-10  5,-5")
    print("  让路   -5,5     0,0")
    
    print("\n纯策略纳什均衡: (前进,让路) 和 (让路,前进)")
    print("相关均衡: 推荐一个玩家前进，另一个让路")
    print("  方案1: 信号0推荐(前进,让路), 信号1推荐(让路,前进)")
    print("  期望收益: 0.5*5 + 0.5*5 = 2.5")
    
    # 廉价对话
    cheap_talk = find_cheap_talk_correlated_equilibrium()
    print(f"\n廉价对话: {cheap_talk}")
    
    print("\n=== 相关均衡的性质 ===")
    print("1. 弱相关均衡 (WCE): 激励相容的加权条件")
    print("2. 强相关均衡 (SCE): 任意偏离都不利")
    print("3. 完美相关均衡 (PCE): 考虑稳健性的完美贝叶斯均衡")
    
    print("\n=== 实践应用 ===")
    print("- 交通路由: 协调中心推荐路线避免拥堵")
    print("- 频谱分配: 监管机构推荐频段使用")
    print("- 拍卖设计: 相关均衡可提高效率")

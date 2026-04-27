# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / repeated_game

本文件实现 repeated_game 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict

class RepeatedGame:
    """
    重复博弈
    
    基础博弈重复T次
    玩家可以看到历史
    """
    
    def __init__(self, base_payoff_matrix: np.ndarray, num_players: int, 
                 discount_factor: float = 1.0, horizon: int = None):
        """
        Args:
            base_payoff_matrix: 基础博弈的收益矩阵
            num_players: 玩家数量
            discount_factor: 贴现因子
            horizon: 重复次数 (None表示无限)
        """
        self.base_payoff = base_payoff_matrix
        self.num_players = num_players
        self.discount = discount_factor
        self.horizon = horizon
    
    def trigger_strategy_payoff(self, cooperative_payoff: float, 
                                defection_payoff: float) -> float:
        """
        计算触发策略下的收益
        
        策略: 首先合作，如果对方背叛则永久背叛
        """
        if self.horizon is None:
            # 无限重复
            if self.discount < 1:
                return cooperative_payoff / (1 - self.discount)
            else:
                return float('inf') if cooperative_payoff > defection_payoff else defection_payoff
        else:
            # 有限重复
            return cooperative_payoff * self.horizon
    
    def grim_trigger_equilibrium(self, cooperation_payoff: float, 
                                 defection_payoff: float) -> Dict:
        """
        Grim Trigger策略均衡
        
        永远合作直到有人背叛，然后永远背叛
        """
        if self.horizon is None or self.horizon == float('inf'):
            # 无限重复囚徒困境
            if self.discount > 0.5:
                return {
                    "strategy": "grim_trigger",
                    "cooperative": True,
                    "payoff": cooperation_payoff / (1 - self.discount),
                    "sustainable": True
                }
            else:
                return {
                    "strategy": "grim_trigger",
                    "cooperative": False,
                    "payoff": defection_payoff,
                    "sustainable": False
                }
        else:
            # 有限重复
            return {
                "strategy": "grim_trigger",
                "cooperative": True,
                "payoff": cooperation_payoff * self.horizon,
                "sustainable": self.horizon > 1
            }

def run_repeated_prisoners_dilemma():
    """重复囚徒困境"""
    print("=== 重复囚徒困境 ===")
    
    # 基础博弈收益
    #              坦白   抵赖
    # 坦白        (-5,-5) (0,-10)
    # 抵赖        (-10,0) (-1,-1)
    
    payoff_matrix = np.array([[-5, 0], [-10, -1]])
    
    game = RepeatedGame(payoff_matrix, 2, discount_factor=0.9, horizon=None)
    
    print("基础博弈:")
    print("         坦白    抵赖")
    print("  坦白   -5,-5   0,-10")
    print("  抵赖   -10,0  -1,-1")
    
    print(f"\n贴现因子: {game.discount}")
    
    # 单次博弈的均衡
    print("\n单次博弈纳什均衡: (坦白,坦白) = (-5,-5)")
    
    # 重复博弈
    print("\n重复博弈分析:")
    
    # Grim Trigger分析
    cooperation_payoff = -1  # (抵赖,抵赖)
    defection_payoff = -5    # (坦白,坦白)
    
    grim_result = game.grim_trigger_equilibrium(cooperation_payoff, defection_payoff)
    print(f"Grim Trigger策略: {grim_result}")
    
    print("\n无名氏定理 (Folk Theorem):")
    print("  在足够长的重复博弈中，")
    print("  任何个体理性收益都可以作为均衡结果")
    print("  只要满足: 收益 >= 单次博弈均衡收益")
    
    # 可持续收益范围
    print("\n可持续的收益范围:")
    print(f"  最低: {defection_payoff} (坦白均衡)")
    print(f"  最高: {cooperation_payoff} (合作)")
    print(f"  所有在这之间的收益都可能")

def run_folk_theorem():
    """无名氏定理"""
    print("\n=== 无名氏定理 (Folk Theorem) ===")
    
    print("无名氏定理表明:")
    print("  1. 在无限重复博弈中，任何个体理性收益都可以达成")
    print("  2. 只要每个玩家的长期平均收益不低于单次博弈均衡")
    
    print("\n条件:")
    print("  - 贴现因子足够接近1 (耐心)")
    print("  - 或重复次数足够长")
    
    # 囚徒困境的例子
    print("\n囚徒困境中的可持续合作:")
    
    def check_cooperation_sustainable(T: int, delta: float) -> bool:
        """检查合作是否可持续"""
        # 合作收益
        coop_payoff = -1
        # 背叛收益
        defect_payoff = -5
        # 背叛后单期收益
        one_shot_deviation = 0
        
        # 合作T期的收益
        coop_total = sum(coop_payoff * (delta ** t) for t in range(T))
        
        # 背叛的诱惑
        # 在t=0背叛，然后回到均衡
        deviate_total = one_shot_deviation + defect_payoff * sum(delta ** t for t in range(1, T))
        
        return coop_total >= deviate_total
    
    for T in [2, 5, 10, 100]:
        for delta in [0.5, 0.8, 0.9, 0.95, 0.99]:
            if check_cooperation_sustainable(T, delta):
                print(f"  T={T}, δ={delta}: 合作可持续")
            else:
                print(f"  T={T}, δ={delta}: 合作不可持续")

def run_trigger_strategies():
    """触发策略分析"""
    print("\n=== 触发策略分类 ===")
    
    strategies = [
        ("Grim Trigger", "一旦背叛，永远背叛"),
        ("Tit-for-Tat", "合作直到被背叛，然后背叛一次"),
        ("Tit-for-Tat with forgiveness", "合作直到被背叛，然后原谅"),
        ("Pavlov", "如果双方都合作，继续；如果一方背叛，下次反转"),
        ("Suspicious Tit-for-Tat", "从背叛开始，然后模仿对手"),
    ]
    
    print("常见触发策略:")
    for name, desc in strategies:
        print(f"  {name}: {desc}")
    
    print("\n=== 策略比较 ===")
    print("Tit-for-Tat:")
    print("  - 简单明了")
    print("  - 容易激发合作")
    print("  - 对噪声敏感（可能陷入循环报复）")
    
    print("\nGrim Trigger:")
    print("  - 强硬策略")
    print("  - 合作稳定性高")
    print("  - 但一旦触发就不可逆")
    
    print("\nPavlov:")
    print("  - 在确定性环境下表现好")
    print("  - 在噪声环境下可能不稳定")

if __name__ == "__main__":
    run_repeated_prisoners_dilemma()
    run_folk_theorem()
    run_trigger_strategies()
    
    print("\n=== 实际应用 ===")
    print("1. 商业合同: 长期合作关系")
    print("2. 国际关系: 条约遵守")
    print("3. 团队生产: 激励机制设计")
    print("4. 劳资谈判: 工资协议")
    
    print("\n=== 有限重复的特殊性 ===")
    print("在有限重复博弈中:")
    print("  - 最后一期没有未来，所以均衡是单期均衡")
    print("  - 倒推法: 最后一期背叛，前面都合作")
    print("  - 但如果引入不确定性，可能改变结果")
    
    print("\n=== 无限重复的直觉 ===")
    print("无限重复博弈中:")
    print("  - 未来合作的价值可以抵消眼前背叛的诱惑")
    print("  - 贴现因子越大（越耐心），合作越容易维持")
    print("  - 触发策略可以维持合作均衡")

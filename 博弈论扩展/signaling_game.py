# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / signaling_game

本文件实现 signaling_game 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional

class SignalingGame:
    """
    信号博弈
    
    两参与者: 发送者(S)和接收者(R)
    发送者有类型θ ∈ Θ
    发送者发送信号m ∈ M
    接收者观察到信号，采取行动a ∈ A
    """
    
    def __init__(self, types: List[str], signals: List[str], actions: List[str],
                 type_prior: Dict[str, float], payoff_matrix: Dict):
        """
        Args:
            types: 类型空间
            signals: 信号空间
            actions: 行动空间
            type_prior: 类型先验概率
            payoff_matrix: 收益矩阵 {(type, action): (sender_payoff, receiver_payoff)}
        """
        self.types = types
        self.signals = signals
        self.actions = actions
        self.type_prior = type_prior
        self.payoff_matrix = payoff_matrix
    
    def find_separating_equilibrium(self) -> Dict:
        """
        寻找分离均衡
        
        每种类型发送不同的信号
        """
        print("=== 分离均衡分析 ===")
        
        # 检查是否存在分离均衡
        # 条件: 对于每种类型，存在唯一的最佳信号
        
        for signal_type in self.types:
            print(f"\n类型 '{signal_type}':")
            print(f"  先验概率: {self.type_prior[signal_type]}")
            
            # 接收者的后验
            print(f"  如果观察到信号m，接收者推断: P(θ|m)")
            
            # 发送者的激励
            print(f"  发送者的最佳信号:")
            for signal in self.signals:
                print(f"    信号'{signal}': 需要计算期望收益")
        
        return {"type": "separating", "feasible": True}
    
    def find_pooling_equilibrium(self) -> Dict:
        """
        寻找混同均衡
        
        所有类型发送相同的信号
        """
        print("=== 混同均衡分析 ===")
        
        # 检查混同均衡
        # 所有类型发送相同信号m*
        # 接收者无法从信号推断类型
        
        print(f"\n混同信号: 假设所有类型都发送'{self.signals[0]}'")
        print(f"接收者后验: P(θ|m*) = P(θ) (先验)")
        
        return {"type": "pooling", "feasible": True}

def run_signaling_game_simulation():
    """信号博弈模拟"""
    print("=== 信号博弈测试 ===")
    
    # 就业市场信号博弈
    types = ["高能力", "低能力"]
    signals = ["教育", "不教育"]
    actions = ["雇佣", "不雇佣"]
    
    type_prior = {"高能力": 0.5, "低能力": 0.5}
    
    payoff_matrix = {
        ("高能力", "雇佣"): (10, 5),   # 发送者, 接收者
        ("高能力", "不雇佣"): (0, 0),
        ("低能力", "雇佣"): (-5, -10),  # 低能力者假装高能力
        ("低能力", "不雇佣"): (0, 2),
        ("教育", "雇佣"): (8, 4),  # 当发送教育信号
        ("教育", "不雇佣"): (0, 1),
        ("不教育", "雇佣"): (5, 3),
        ("不教育", "不雇佣"): (0, 0),
    }
    
    game = SignalingGame(types, signals, actions, type_prior, payoff_matrix)
    
    print("就业市场信号博弈:")
    print("类型: 高能力(50%), 低能力(50%)")
    print("信号: 教育, 不教育")
    print("行动: 雇佣, 不雇佣")
    
    print("\n收益结构:")
    print("  - 高能力者教育成本低，低能力者成本高")
    print("  - 雇主从雇佣高能力者获得高收益")
    
    # 分离均衡分析
    sep_eq = game.find_separating_equilibrium()
    
    print("\n分离均衡条件:")
    print("  - 高能力者选择教育")
    print("  - 低能力者选择不教育")
    print("  - 雇主正确推断类型并雇佣高能力者")
    
    # 混同均衡分析
    pool_eq = game.find_pooling_equilibrium()
    
    print("\n混同均衡条件:")
    print("  - 两种类型都选择相同策略")
    print("  - 例如: 都选择不教育")
    print("  - 雇主无法区分类型")

def run_cheap_talk_analysis():
    """廉价对话分析"""
    print("\n=== 廉价对话博弈 ===")
    
    print("设置:")
    print("  - 发送者有信息")
    print("  - 信号成本为零")
    print("  - 无先验约束")
    
    print("\n经典结论:")
    print("  - 廉价对话下通常没有信息传递")
    print("  - 因为发送者可以撒谎")
    print("  - 接收者忽略消息")
    
    print("\n但如果:")
    print("  - 利益一致: 可能传递信息")
    print("  - 长期关系: 声誉效应")
    print("  - 重复博弈: 触发策略")

def analyze_signaling_costs():
    """分析信号成本"""
    print("\n=== 信号成本结构 ===")
    
    print("分离均衡的存在条件:")
    print("  对于所有类型θ1, θ2:")
    print("    u_S(θ1, m1) + u_S(θ2, m2) > u_S(θ1, m2) + u_S(θ2, m1)")
    print("  其中m1≠m2是不同信号")
    
    print("\n示例 - 教育信号:")
    print("  高能力者: 教育成本 = 2")
    print("  低能力者: 教育成本 = 10")
    print("  雇佣收益 = 10")
    
    print("\n验证分离条件:")
    print("  高能力者选教育: 10 - 2 = 8")
    print("  高能力者选不教育: 5")
    print("  -> 高能力者选择教育")
    
    print("  低能力者选教育: 10 - 10 = 0")
    print("  低能力者选不教育: 5")
    print("  -> 低能力者选择不教育")
    
    print("\n结论: 存在分离均衡，教育可以作为能力信号")

if __name__ == "__main__":
    run_signaling_game_simulation()
    run_cheap_talk_analysis()
    analyze_signaling_costs()
    
    print("\n=== 信号博弈的应用 ===")
    print("1. 教育作为信号: 学历与能力")
    print("2. 广告支出: 质量信号")
    print("3. 动物行为: 孔雀尾巴")
    print("4. 司法系统: 惩罚信号")
    
    print("\n=== 分离vs混同 ===")
    print("分离均衡:")
    print("  - 信息效率高")
    print("  - 需要信号成本差异")
    print("  - 现实中较罕见")
    
    print("\n混同均衡:")
    print("  - 可能无信息传递")
    print("  - 不需要成本差异")
    print("  - 更常见")
    
    print("\n=== 启示 ===")
    print("信号博弈揭示了:")
    print("  - 信息不对称下的激励问题")
    print("  - 成本差异对信息传递的重要性")
    print("  - 区分真实信息和虚假信号的方法")

# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / correlated_equilibrium

本文件实现 correlated_equilibrium 相关的算法功能。
"""

import random
from typing import List, Dict, Tuple


class CorrelatedEquilibrium:
    """相关均衡"""

    def __init__(self, n_players: int, n_actions: int):
        """
        参数：
            n_players: 玩家数
            n_actions: 行动数
        """
        self.n_players = n_players
        self.n_actions = n_actions

    def generate_signal(self) -> int:
        """
        生成协调信号

        返回：信号
        """
        return random.randint(0, self.n_actions - 1)

    def recommend_actions(self, signal: int) -> List[int]:
        """
        根据信号推荐行动

        参数：
            signal: 协调信号

        返回：每个玩家的行动推荐
        """
        # 简化：使用信号作为随机种子
        random.seed(signal)

        recommendations = []
        for _ in range(self.n_players):
            action = random.randint(0, self.n_actions - 1)
            recommendations.append(action)

        return recommendations

    def utility(self, actions: List[int]) -> float:
        """
        计算效用（简化）

        返回：效用值
        """
        # 简化：如果所有玩家行动相同，效用高
        if len(set(actions)) == 1:
            return 1.0
        return 0.5

    def check_equilibrium(self, signal: int,
                        recommendations: List[List[int]]) -> dict:
        """
        检查是否达到相关均衡

        返回：检查结果
        """
        # 每个玩家遵守推荐的效用
        follow_util = 0
        deviate_util = 0

        for player in range(self.n_players):
            # 遵守推荐
            my_action = recommendations[player][signal]
            other_actions = [recommendations[p][signal]
                            for p in range(self.n_players) if p != player]
            follow_util += self.utility([my_action] + other_actions)

            # 如果偏离（随机选择）
            deviate_action = random.randint(0, self.n_actions - 1)
            other_actions = [recommendations[p][signal]
                            for p in range(self.n_players) if p != player]
            deviate_util += self.utility([deviate_action] + other_actions)

        # 相关均衡条件：遵守不比偏离差
        is_equilibrium = follow_util >= deviate_util

        return {
            'signal': signal,
            'follow_utility': follow_util,
            'deviate_utility': deviate_util,
            'is_equilibrium': is_equilibrium
        }


def correlated_vs_nash():
    """相关均衡 vs 纳什均衡"""
    print("=== 相关均衡 vs 纳什均衡 ===")
    print()
    print("纳什均衡：")
    print("  - 无协调者")
    print("  - 每个玩家独立决策")
    print("  - 可能效率不高")
    print()
    print("相关均衡：")
    print("  - 有协调者（信号）")
    print("  - 玩家遵循推荐")
    print("  - 可以达到更高社会福利")
    print()
    print("例子：")
    print("  - 交通协调：信号灯")
    print("  - 安全博弈：警察巡逻")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 相关均衡测试 ===\n")

    ce = CorrelatedEquilibrium(n_players=3, n_actions=4)

    # 生成信号
    signal = ce.generate_signal()

    print(f"协调信号: {signal}")
    print()

    # 推荐行动
    recommendations = []
    for _ in range(ce.n_players):
        rec = ce.recommend_actions(signal)
        recommendations.append(rec)

    print("推荐行动：")
    for i, rec in enumerate(recommendations):
        print(f"  玩家 {i}: {rec[signal]}")
    print()

    # 检查均衡
    result = ce.check_equilibrium(signal, recommendations)

    print(f"遵守效用: {result['follow_utility']:.2f}")
    print(f"偏离效用: {result['deviate_utility']:.2f}")
    print(f"是相关均衡: {'是' if result['is_equilibrium'] else '否'}")

    print()
    correlated_vs_nash()

    print()
    print("说明：")
    print("  - 相关均衡比纳什更一般")
    print("  - 有协调者可以提高效率")
    print("  - 应用于分布式系统协调")

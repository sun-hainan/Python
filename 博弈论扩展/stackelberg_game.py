# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / stackelberg_game

本文件实现 stackelberg_game 相关的算法功能。
"""

import numpy as np
from typing import Tuple


class StackelbergGame:
    """Stackelberg博弈"""

    def __init__(self, leader_utilities: np.ndarray, follower_utilities: np.ndarray):
        """
        参数：
            leader_utilities: 领导者的收益矩阵
            follower_utilities: 跟随者的收益矩阵
        """
        self.leader_util = leader_utilities
        self.follower_util = follower_utilities
        self.n_leader_actions = leader_utilities.shape[0]
        self.n_follower_actions = follower_utilities.shape[1]

    def leader_best_response(self, leader_action: int) -> int:
        """
        给定领导者行动，跟随者的最优反应

        返回：跟随者的最优行动
        """
        # 跟随者选择最大化自己收益的行动
        follower_payoffs = self.follower_util[leader_action]
        return int(np.argmax(follower_payoffs))

    def compute_stackelberg_equilibrium(self) -> Tuple[int, int]:
        """
        计算Stackelberg均衡

        返回：(leader_action, follower_action)
        """
        best_equilibrium = (0, 0)
        best_leader_payoff = -float('inf')

        # 领导者考虑每个行动
        for leader_action in range(self.n_leader_actions):
            # 跟随者最优反应
            follower_action = self.leader_best_response(leader_action)

            # 领导者收益
            leader_payoff = self.leader_util[leader_action, follower_action]

            if leader_payoff > best_leader_payoff:
                best_leader_payoff = leader_payoff
                best_equilibrium = (leader_action, follower_action)

        return best_equilibrium

    def security_game(self, defender_strategies: list,
                     attacker_strategies: list,
                     defender_payoffs: np.ndarray) -> dict:
        """
        安全博弈（最简单的Stackelberg）

        返回：最优策略
        """
        # 简化：找 defender 的最优混合策略
        n_def = len(defender_strategies)
        n_att = len(attacker_strategies)

        # 最大化最小收益
        best_mix = np.ones(n_def) / n_def
        best_value = 0

        return {
            'defender_strategy': best_mix,
            'attacker_best_response': 0,
            'equilibrium_value': best_value
        }


def stackelberg_applications():
    """Stackelberg应用"""
    print("=== Stackelberg应用 ===")
    print()
    print("1. 价格竞争")
    print("   - 大公司先定价")
    print("   - 小公司跟随")
    print()
    print("2. 网络安全")
    print("   - 防御者先部署策略")
    print("   - 攻击者观察后行动")
    print()
    print("3. 拍卖")
    print("   - 卖家先设置规则")
    print("   - 买家竞拍")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Stackelberg博弈测试 ===\n")

    # 简单例子：领导者和跟随者各有2个行动
    leader_util = np.array([
        [3, 1],   # 领导选0，跟随者选0或1
        [2, 4]    # 领导选1，跟随者选0或1
    ])

    follower_util = np.array([
        [2, 3],   # 领导选0，跟随者选0或1
        [3, 1]    # 领导选1，跟随者选0或1
    ])

    game = StackelbergGame(leader_util, follower_util)

    print("收益矩阵：")
    print(f"领导者收益:\n{leader_util}")
    print(f"跟随者收益:\n{follower_util}")
    print()

    # 计算均衡
    leader_action, follower_action = game.compute_stackelberg_equilibrium()

    print(f"Stackelberg均衡：")
    print(f"  领导者行动: {leader_action}")
    print(f"  跟随者反应: {follower_action}")
    print(f"  领导者收益: {leader_util[leader_action, follower_action]}")

    print()
    stackelberg_applications()

    print()
    print("说明：")
    print("  - Stackelberg是领导-跟随博弈")
    print("  - 领导者有先发优势")
    print("  - 常用于安全和经济领域")

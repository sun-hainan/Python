# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / mechanism_design

本文件实现 mechanism_design 相关的算法功能。
"""

import random
from typing import List, Tuple


class MechanismDesign:
    """机制设计"""

    def __init__(self, n_players: int):
        """
        参数：
            n_players: 玩家数
        """
        self.n_players = n_players

    def vcg_allocation(self, valuations: List[List[float]],
                      items: List[str]) -> Tuple[List[int], List[float]]:
        """
        VCG (Vickrey-Clarke-Groves) 机制

        参数：
            valuations: 每个玩家对每个物品的价值矩阵
            items: 物品列表

        返回：(分配结果, 支付价格)
        """
        n_items = len(items)
        allocation = [-1] * n_items
        payments = [0.0] * self.n_players

        # 贪心分配
        for j, item in enumerate(items):
            best_player = -1
            best_value = -1

            for i in range(self.n_players):
                if valuations[i][j] > best_value:
                    best_value = valuations[i][j]
                    best_player = i

            allocation[j] = best_player

        # 计算支付
        for i in range(self.n_players):
            allocated_items = [j for j in range(n_items) if allocation[j] == i]

            # 没有分配不支付
            if not allocated_items:
                continue

            # 计算其他人的总价值（没有这个玩家时）
            # 简化：用第二高的总和
            other_total = 0
            for j in allocated_items:
                other_values = [valuations[k][j] for k in range(self.n_players) if k != i]
                if other_values:
                    other_total += max(other_values) if other_values else 0

            # 支付 = 其他人在没有i的情况下的总价值
            my_value = sum(valuations[i][j] for j in allocated_items)
            payments[i] = other_total  # 简化

        return allocation, payments

    def second_price_auction(self, bids: List[float]) -> Tuple[int, float]:
        """
        第二价格拍卖（Vickrey）

        参数：
            bids: 出价列表

        返回：(赢家索引, 支付价格)
        """
        # 排序出价
        sorted_bids = sorted(enumerate(bids), key=lambda x: x[1], reverse=True)

        winner = sorted_bids[0][0]
        winning_bid = sorted_bids[0][1]
        second_price = sorted_bids[1][1] if len(sorted_bids) > 1 else 0

        return winner, second_price

    def simulate_bidding(self, true_values: List[float]) -> dict:
        """
        模拟拍卖（真实价值 vs 说谎）

        参数：
            true_values: 真实价值

        返回：结果
        """
        # 参与者真实出价
        result = {
            'true_report': self.second_price_auction(true_values),
        }

        # 参与者一半说谎
        distorted = true_values.copy()
        for i in range(len(distorted)):
            if random.random() > 0.5:
                distorted[i] = distorted[i] * 0.8

        result['distorted_report'] = self.second_price_auction(distorted)

        return result


def mechanism_design_principles():
    """机制设计原则"""
    print("=== 机制设计原则 ===")
    print()
    print("激励相容（IC）：")
    print("  - 说实话是最优策略")
    print("  - 不会因为说谎而获益")
    print()
    print("个体理性（IR）：")
    print("  - 参与比不参与好")
    print("  - 不会亏损")
    print()
    print("社会福利最大化：")
    print("  - 分配给评价最高的人")
    print("  - 但需要计算")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 机制设计测试 ===\n")

    md = MechanismDesign(n_players=3)

    # 拍卖
    bids = [100.0, 80.0, 65.0]
    winner, price = md.second_price_auction(bids)

    print(f"出价: {bids}")
    print(f"赢家: 玩家 {winner}")
    print(f"支付: ${price:.2f}")
    print()

    # 多物品分配
    valuations = [
        [10, 20, 15],  # 玩家0
        [5, 25, 10],   # 玩家1
        [15, 10, 20],  # 玩家2
    ]
    items = ['A', 'B', 'C']

    allocation, payments = md.vcg_allocation(valuations, items)

    print("VCG多物品分配：")
    print(f"  物品分配: {allocation}")
    print(f"  支付: {[f'{p:.1f}' for p in payments]}")

    print()
    mechanism_design_principles()

    print()
    print("说明：")
    print("  - 机制设计是经济学的算法")
    print("  - 拍卖、匹配市场中重要")
    print("  - 区块链的DeFi大量使用")

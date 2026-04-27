# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / vickrey_clarke_groves

本文件实现 vickrey_clarke_groves 相关的算法功能。
"""

from typing import List, Tuple


class VickreyAuction:
    """Vickrey拍卖（第二价格拍卖）"""

    def __init__(self, reserve_price: float = 0.0):
        """
        参数：
            reserve_price: 保留价
        """
        self.reserve_price = reserve_price
        self.bids = []

    def submit_bid(self, bidder_id: str, bid: float):
        """提交出价"""
        if bid >= self.reserve_price:
            self.bids.append((bidder_id, bid))

    def determine_winner(self) -> Tuple[str, float]:
        """
        确定胜者和第二价格

        返回：(胜者ID, 支付价格)
        """
        if not self.bids:
            return None, 0.0

        # 按出价降序排列
        sorted_bids = sorted(self.bids, key=lambda x: x[1], reverse=True)

        winner = sorted_bids[0][0]
        winning_bid = sorted_bids[0][1]

        # 第二高出价
        if len(sorted_bids) > 1:
            second_price = sorted_bids[1][1]
        else:
            second_price = self.reserve_price

        return winner, max(second_price, self.reserve_price)


class GrovesMechanism:
    """Groves机制"""

    def __init__(self, n_agents: int, valuation_function):
        """
        参数：
            n_agents: 参与者数量
            valuation_function: 价值函数 v_i(x)
        """
        self.n_agents = n_agents
        self.valuation = valuation_function

    def calculate_payment(self, agent_id: int, allocation: int, others_bids: List[float]) -> float:
        """
        计算支付

        参数：
            agent_id: 参与者ID
            allocation: 分配结果
            others_bids: 其他人的出价

        返回：需要支付的金额
        """
        # v_i(x_-i) - v_i(最优分配 without i)
        # 简化实现
        return others_bids[agent_id] if agent_id < len(others_bids) else 0.0


def vcg_example():
    """VCG机制示例"""
    print("=== VCG机制示例 ===\n")

    # 假设3个参与者竞争一个物品
    bids = [
        ("Alice", 100),
        ("Bob", 80),
        ("Charlie", 60),
    ]

    print("出价:")
    for name, bid in bids:
        print(f"  {name}: ${bid}")

    # Vickrey拍卖
    auction = VickreyAuction()

    for name, bid in bids:
        auction.submit_bid(name, bid)

    winner, price = auction.determine_winner()

    print()
    print(f"胜者: {winner}")
    print(f"支付: ${price}")
    print()
    print("分析:")
    print("  - Alice出价最高，但她只需要付第二高的$80")
    print("  - 这激励所有人如实出价（说实话是最优策略）")


def strategy_proofness():
    """激励相容性证明思路"""
    print()
    print("=== 激励相容性 ===")
    print()
    print("定理：Vickrey拍卖是激励相容的")
    print()
    print("证明思路：")
    print("  - 设真实价值为v，出价为b")
    print("  - 如果b >= 第二高价：得到物品，效用 = v - 第二高价")
    print("  - 如果b < 第二高价：得不到物品，效用 = 0")
    print("  - 由于出价不影响第二高价（如实出价不会改变结果）")
    print("  - 所以说实话是最优策略")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    vcg_example()
    strategy_proofness()

    print("\n说明：")
    print("  - VCG是经典的社会选择机制")
    print("  - 满足激励相容、无亏欠等性质")
    print("  - 缺点：计算复杂、可能产生赤字")

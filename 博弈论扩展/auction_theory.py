# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / auction_theory

本文件实现 auction_theory 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod

class Bidder(ABC):
    """投标人抽象类"""
    
    @abstractmethod
    def bid(self, valuation: float) -> float:
        """给出投标"""
        pass
    
    @abstractmethod
    def update(self, won: bool, payment: float, actual_value: float):
        """根据结果更新"""
        pass

class TruthfulBidder(Bidder):
    """真实价值投标人"""
    
    def bid(self, valuation: float) -> float:
        return valuation
    
    def update(self, won: bool, payment: float, actual_value: float):
        pass

class FirstPriceBidder(Bidder):
    """第一价格拍卖投标人"""
    
    def __init__(self, risk_aversion: float = 0.5):
        self.risk_aversion = risk_aversion
    
    def bid(self, valuation: float) -> float:
        # 风险厌恶下的出价
        return valuation * (1 - self.risk_aversion * 0.3)
    
    def update(self, won: bool, payment: float, actual_value: float):
        # 可以根据结果调整风险厌恶参数
        pass

class SecondPriceBidder(Bidder):
    """第二价格拍卖投标人（总是真实出价）"""
    
    def bid(self, valuation: float) -> float:
        return valuation
    
    def update(self, won: bool, payment: float, actual_value: float):
        pass

def simulate_auction(num_bidders: int, auction_type: str, 
                    valuations: List[float]) -> Dict:
    """
    模拟拍卖
    
    Args:
        num_bidders: 投标人数量
        auction_type: 拍卖类型
        valuations: 真实估值
    
    Returns:
        拍卖结果
    """
    print(f"=== {auction_type}拍卖模拟 ===")
    print(f"投标人数量: {num_bidders}")
    print(f"估值: {valuations}")
    
    if auction_type == "first_price":
        # 第一价格拍卖
        bidders = [FirstPriceBidder() for _ in range(num_bidders)]
        bids = [b.bid(v) for b, v in zip(bidders, valuations)]
        
        winner_idx = np.argmax(bids)
        winner_bid = bids[winner_idx]
        
        print(f"投标: {bids}")
        print(f"胜者: 投标人{winner_idx + 1}")
        print(f"支付: {winner_bid:.2f}")
        print(f"利润: {valuations[winner_idx] - winner_bid:.2f}")
        
        return {
            "winner": winner_idx,
            "payment": winner_bid,
            "profit": valuations[winner_idx] - winner_bid
        }
    
    elif auction_type == "second_price":
        # 第二价格拍卖
        bidders = [TruthfulBidder() for _ in range(num_bidders)]
        bids = [b.bid(v) for b, v in zip(bidders, valuations)]
        
        winner_idx = np.argmax(bids)
        second_bid = sorted(bids, reverse=True)[1]
        
        print(f"投标: {bids}")
        print(f"胜者: 投标人{winner_idx + 1}")
        print(f"第二高出价: {second_bid:.2f}")
        print(f"支付: {second_bid:.2f}")
        print(f"利润: {valuations[winner_idx] - second_bid:.2f}")
        
        return {
            "winner": winner_idx,
            "payment": second_bid,
            "profit": valuations[winner_idx] - second_bid
        }

def compare_auctions():
    """比较不同拍卖机制"""
    print("\n=== 拍卖机制比较 ===")
    
    valuations = [100, 80, 60, 40]
    
    # 第一价格拍卖
    fp_result = simulate_auction(4, "first_price", valuations)
    
    print()
    
    # 第二价格拍卖
    sp_result = simulate_auction(4, "second_price", valuations)
    
    print("\n=== 比较结果 ===")
    print(f"第一价格: 胜者支付{fp_result['payment']:.2f}, 社会福利损失")
    print(f"第二价格: 胜者支付{sp_result['payment']:.2f}, 效率最优")
    
    print("\n=== 激励分析 ===")
    print("第一价格拍卖:")
    print("  - 投标人有压低出价的动机")
    print("  - 最佳出价取决于对其他投标人的估计")
    print("  - 激励不相容")
    
    print("\n第二价格拍卖:")
    print("  - 真实出价是占优策略")
    print("  - 简单且有效")
    print("  - 激励相容")

def run_ipv_model():
    """独立私有价值模型分析"""
    print("\n=== 独立私有价值 (IPV) 模型 ===")
    
    print("假设:")
    print("  - 每个投标人有私有估值")
    print("  - 估值相互独立")
    print("  - 估值服从已知分布")
    
    valuations = np.random.normal(100, 20, 10)
    valuations = np.maximum(valuations, 0)  # 确保非负
    
    print(f"模拟估值 (正态分布, μ=100, σ=20):")
    for i, v in enumerate(valuations[:5]):
        print(f"  投标人{i+1}: {v:.2f}")
    
    print("\n最优投标策略:")
    print("  - 第一价格: b* = v - (N-1)/N * (v - F(v))")
    print("    其中F是估值分布函数")
    print("  - 第二价格: b* = v")
    
    print("\n期望收益分析:")
    print("  在第二价格拍卖中:")
    expected_revenue = np.mean(sorted(valuations, reverse=True)[1])
    print(f"  期望收入: {expected_revenue:.2f}")

if __name__ == "__main__":
    compare_auctions()
    run_ipv_model()
    
    print("\n=== 拍卖类型总结 ===")
    print("1. 英式拍卖: 公开升价")
    print("2. 荷式拍卖: 公开降价")
    print("3. 第一价格密封投标")
    print("4. 第二价格密封投标 (Vickrey)")
    
    print("\n=== 机制设计原则 ===")
    print("1. 激励相容: 真实报告是占优策略")
    print("2. 个人理性: 参与不会导致负效用")
    print("3. 预算可行性: 机制不亏损")
    print("4. 社会福利最大化: 物品给最高估值者")
    
    print("\n=== 应用场景 ===")
    print("1. 在线广告: Google AdWords")
    print("2. 频谱拍卖: 政府频段分配")
    print("3. 碳排放权: 排污权交易")
    print("4. 艺术品: 佳士得、苏富比")

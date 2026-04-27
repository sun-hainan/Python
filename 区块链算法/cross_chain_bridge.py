# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / cross_chain_bridge

本文件实现 cross_chain_bridge 相关的算法功能。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class Token:
    """跨链代币"""
    symbol: str
    source_chain: str
    dest_chain: str
    locked_amount: int
    total_supply: int

class CrossChainBridge:
    """
    跨链桥
    
    允许资产在不同区块链之间转移
    """
    
    def __init__(self):
        self.chains: Dict[str, int] = {}  # chain_id -> 链上资产总额
        self.locks: Dict[str, int] = {}  # 用户地址 -> 锁定金额
        self.pending_swaps: Dict[str, dict] = {}  # swap_id -> 交换信息
        self.swap_count = 0
    
    def register_chain(self, chain_id: str):
        """注册区块链"""
        if chain_id not in self.chains:
            self.chains[chain_id] = 0
    
    def lock_tokens(self, user: str, amount: int, source_chain: str) -> str:
        """
        锁定代币（源链操作）
        
        Args:
            user: 用户地址
            amount: 金额
            source_chain: 源链ID
        
        Returns:
            交换ID
        """
        self.register_chain(source_chain)
        
        # 创建交换请求
        self.swap_count += 1
        swap_id = hashlib.sha256(f"{user}{self.swap_count}".encode()).hexdigest()[:16]
        
        self.pending_swaps[swap_id] = {
            "user": user,
            "amount": amount,
            "source_chain": source_chain,
            "dest_chain": None,
            "status": "locked",
            "nonce": self.swap_count
        }
        
        self.chains[source_chain] += amount
        self.locks[user] = self.locks.get(user, 0) + amount
        
        return swap_id
    
    def initiate_swap(self, swap_id: str, dest_chain: str) -> bool:
        """
        发起跨链交换
        
        Args:
            swap_id: 交换ID
            dest_chain: 目标链ID
        
        Returns:
            是否成功
        """
        if swap_id not in self.pending_swaps:
            return False
        
        swap = self.pending_swaps[swap_id]
        if swap["status"] != "locked":
            return False
        
        self.register_chain(dest_chain)
        
        swap["dest_chain"] = dest_chain
        swap["status"] = "swapping"
        
        return True
    
    def complete_swap(self, swap_id: str, dest_address: str) -> bool:
        """
        完成交换（目标链操作）
        
        Args:
            swap_id: 交换ID
            dest_address: 目标链地址
        
        Returns:
            是否成功
        """
        if swap_id not in self.pending_swaps:
            return False
        
        swap = self.pending_swaps[swap_id]
        if swap["status"] != "swapping":
            return False
        
        # 在目标链铸造代币
        self.chains[swap["dest_chain"]] += swap["amount"]
        
        swap["status"] = "completed"
        swap["dest_address"] = dest_address
        
        # 从源链锁定金额中扣除
        self.locks[swap["user"]] -= swap["amount"]
        
        return True
    
    def get_swap_status(self, swap_id: str) -> Optional[dict]:
        """获取交换状态"""
        return self.pending_swaps.get(swap_id)
    
    def get_total_locked(self) -> int:
        """获取总锁定金额"""
        return sum(self.locks.values())
    
    def get_chain_balance(self, chain_id: str) -> int:
        """获取链上资产余额"""
        return self.chains.get(chain_id, 0)

if __name__ == "__main__":
    print("=== 跨链桥测试 ===")
    
    bridge = CrossChainBridge()
    
    # 注册链
    bridge.register_chain("ethereum")
    bridge.register_chain("polygon")
    bridge.register_chain("bsc")
    
    print("注册链: ethereum, polygon, bsc")
    
    # 用户锁定代币
    swap_id1 = bridge.lock_tokens("0xAlice...", 1000, "ethereum")
    swap_id2 = bridge.lock_tokens("0xBob...", 500, "ethereum")
    
    print(f"\nAlice锁定1000 ETH -> swap_id={swap_id1}")
    print(f"Bob锁定500 ETH -> swap_id={swap_id2}")
    
    print(f"\n以太坊链总资产: {bridge.get_chain_balance('ethereum')}")
    
    # 发起跨链交换
    print("\n=== 跨链交换 ===")
    bridge.initiate_swap(swap_id1, "polygon")
    print(f"Alice发起: swap_id={swap_id1} -> polygon")
    
    # 完成交换
    bridge.complete_swap(swap_id1, "0xAlicePolygon...")
    print(f"Alice完成交换到Polygon")
    
    status = bridge.get_swap_status(swap_id1)
    print(f"交换状态: {status}")
    
    print(f"\nPolygon链总资产: {bridge.get_chain_balance('polygon')}")
    print(f"总锁定金额: {bridge.get_total_locked()}")
    
    # 模拟攻击场景
    print("\n=== 安全检查 ===")
    print(f"以太坊余额: {bridge.get_chain_balance('ethereum')}")
    print(f"Polygon余额: {bridge.get_chain_balance('polygon')}")
    print(f"总锁定: {bridge.get_total_locked()}")
    print(f"一致性检查: {bridge.get_chain_balance('ethereum') + bridge.get_chain_balance('polygon') >= bridge.get_total_locked()}")

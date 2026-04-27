# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / bloom_chain

本文件实现 bloom_chain 相关的算法功能。
"""

import hashlib
from typing import List, Optional
import time


class Block:
    """区块"""

    def __init__(self, transactions: List[str], prev_hash: str):
        """
        参数：
            transactions: 交易列表
            prev_hash: 前一个区块的哈希
        """
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.timestamp = time.time()
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        计算区块哈希

        返回：哈希字符串
        """
        content = (str(self.transactions) +
                   self.prev_hash +
                   str(self.timestamp) +
                   str(self.nonce))

        return hashlib.sha256(content.encode()).hexdigest()

    def mine(self, difficulty: int = 4) -> None:
        """
        挖矿（工作量证明）

        参数：
            difficulty: 难度（前导0的数量）
        """
        target = '0' * difficulty

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    """区块链"""

    def __init__(self):
        self.chain = [self.create_genesis()]

    def create_genesis(self) -> Block:
        """创建创世区块"""
        return Block(["Genesis Block"], "0" * 64)

    def add_block(self, transactions: List[str]) -> Block:
        """
        添加区块

        参数：
            transactions: 交易列表

        返回：新区块
        """
        prev_block = self.chain[-1]
        new_block = Block(transactions, prev_block.hash)
        new_block.mine()

        self.chain.append(new_block)
        return new_block

    def is_valid(self) -> bool:
        """
        验证链的有效性

        返回：是否有效
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # 检查当前区块的哈希
            if current.hash != current.compute_hash():
                return False

            # 检查与前一区块的链接
            if current.prev_hash != previous.hash:
                return False

        return True


def consensus_mechanisms():
    """共识机制比较"""
    print("=== 共识机制 ===")
    print()
    print("工作量证明（PoW）：")
    print("  - 挖矿竞争")
    print("  - 消耗能源")
    print("  - Bitcoin使用")
    print()
    print("权益证明（PoS）：")
    print("  - 按 stake 投票")
    print("  - 更节能")
    print("  - Ethereum 2.0使用")
    print()
    print("其他机制：")
    print("  - DPoS（委托权益证明）")
    print("  - PBFT（拜占庭容错）")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Bloom链测试 ===\n")

    # 创建区块链
    chain = Blockchain()

    # 添加交易
    print("添加交易...")
    tx1 = ["Alice -> Bob: 1 BTC"]
    block1 = chain.add_block(tx1)
    print(f"  区块 1: {block1.hash[:16]}... 非ces={block1.nonce}")

    tx2 = ["Bob -> Charlie: 0.5 BTC", "Charlie -> Dave: 0.3 BTC"]
    block2 = chain.add_block(tx2)
    print(f"  区块 2: {block2.hash[:16]}... nonce={block2.nonce}")

    print()
    print(f"链长度: {len(chain.chain)}")
    print(f"链有效: {chain.is_valid()}")

    # 显示区块
    print("\n区块内容：")
    for i, block in enumerate(chain.chain):
        print(f"\n区块 {i}:")
        print(f"  交易: {block.transactions}")
        print(f"  哈希: {block.hash[:20]}...")
        print(f"  前向: {block.prev_hash[:20]}...")

    print()
    consensus_mechanisms()

    print()
    print("说明：")
    print("  - 区块链是分布式账本")
    print("  - 工作量证明保证安全")
    print("  - 应用于加密货币和智能合约")

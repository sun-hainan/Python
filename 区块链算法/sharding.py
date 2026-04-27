# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / sharding

本文件实现 sharding 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple
import random


class BlockchainSharding:
    """区块链分片系统"""

    def __init__(self, n_shards: int, nodes_per_shard: int):
        """
        参数：
            n_shards: 分片数量
            nodes_per_shard: 每个分片的节点数
        """
        self.n_shards = n_shards
        self.nodes_per_shard = nodes_per_shard

        # 分片成员
        self.shards = [[] for _ in range(n_shards)]

        # 分片账本
        self.ledgers = [{} for _ in range(n_shards)]

    def assign_node(self, node_id: str) -> int:
        """
        分配节点到分片

        参数：
            node_id: 节点ID

        返回：分片ID
        """
        shard_id = hash(node_id) % self.n_shards

        if node_id not in self.shards[shard_id]:
            self.shards[shard_id].append(node_id)

        return shard_id

    def assign_transaction(self, tx_id: str, sender: str, receiver: str) -> int:
        """
        分配交易到分片

        参数：
            tx_id: 交易ID
            sender: 发送者
            receiver: 接收者

        返回：分片ID
        """
        # 基于发送者地址分配（保证同一发送者的交易在同分片）
        shard_id = hash(sender) % self.n_shards

        return shard_id

    def process_transaction(self, tx: Dict) -> bool:
        """
        处理交易

        返回：是否成功
        """
        tx_id = tx['id']
        sender = tx['sender']
        receiver = tx['receiver']
        amount = tx['amount']

        shard_id = self.assign_transaction(tx_id, sender, receiver)

        ledger = self.ledgers[shard_id]

        if sender not in ledger:
            ledger[sender] = 100  # 初始余额

        if ledger.get(sender, 0) >= amount:
            ledger[sender] -= amount
            ledger[receiver] = ledger.get(receiver, 0) + amount
            return True

        return False

    def cross_shard_transfer(self, sender: str, receiver: str,
                           amount: float) -> Dict:
        """
        跨分片转账

        返回：处理结果
        """
        sender_shard = hash(sender) % self.n_shards
        receiver_shard = hash(receiver) % self.n_shards

        if sender_shard == receiver_shard:
            return {'type': 'same_shard', 'shard': sender_shard}

        return {
            'type': 'cross_shard',
            'sender_shard': sender_shard,
            'receiver_shard': receiver_shard,
            'status': 'pending',
            'message': '需要跨分片协议'
        }

    def get_shard_size(self, shard_id: int) -> int:
        """
        获取分片节点数

        返回：节点数
        """
        return len(self.shards[shard_id])

    def get_balance(self, address: str) -> float:
        """
        获取地址余额

        返回：余额
        """
        shard_id = hash(address) % self.n_shards
        return self.ledgers[shard_id].get(address, 0)


def sharding_challenges():
    """分片挑战"""
    print("=== 分片技术挑战 ===")
    print()
    print("1. 跨分片交易")
    print("   - 需要协调多个分片")
    print("   - 引入延迟和复杂性")
    print()
    print("2. 单分片攻击")
    print("   - 只需控制1/n的分片")
    print("   - 需要随机重新分片")
    print()
    print("3. 数据可用性")
    print("   - 分片节点可能离线")
    print("   - 需要确保数据可用")
    print()
    print("4. 状态一致性")
    print("   - 跨分片状态同步")
    print("   - 避免双重支付")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 区块链分片测试 ===\n")

    # 创建分片系统
    n_shards = 4
    nodes_per_shard = 10

    sharding = BlockchainSharding(n_shards, nodes_per_shard)

    print(f"分片数: {n_shards}")
    print(f"每分片节点数: {nodes_per_shard}")
    print()

    # 分配节点
    print("节点分配：")
    for i in range(8):
        node_id = f"node_{i}"
        shard = sharding.assign_node(node_id)
        print(f"  {node_id} -> 分片 {shard}")

    print()

    # 处理交易
    print("交易处理：")
    transactions = [
        {'id': 'tx1', 'sender': 'Alice', 'receiver': 'Bob', 'amount': 10},
        {'id': 'tx2', 'sender': 'Bob', 'receiver': 'Charlie', 'amount': 5},
        {'id': 'tx3', 'sender': 'Alice', 'receiver': 'David', 'amount': 15}
    ]

    for tx in transactions:
        success = sharding.process_transaction(tx)
        shard = sharding.assign_transaction(tx['id'], tx['sender'], tx['receiver'])
        print(f"  {tx['id']}: {tx['sender']} -> {tx['receiver']}, 分片{shard}, {'✅' if success else '❌'}")

    print()

    # 跨分片转账
    print("跨分片转账：")
    result = sharding.cross_shard_transfer("Alice", "Eve", 20)
    print(f"  Alice -> Eve: {result}")

    print()
    sharding_challenges()

    print()
    print("说明：")
    print("  - 分片是区块链扩容的主要方案")
    print("  - Ethereum 2.0 采用分片")
    print("  - 平衡安全性、去中心化和性能")

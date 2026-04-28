"""
拜占庭共识
==========================================

【算法原理】
在可能存在恶意节点的情况下，达成一致的协议。
经典问题是将军问题：n个将军中f个可能是叛徒，
如何让loyal将军达成一致？

【时间复杂度】O(n²) for PBFT, O(f log n) for newer
【应用场景】- 区块链共识（PBFT, Tendermint）
- 分布式数据库
- 无人机编队
"""

import random
from typing import List, Dict, Set, Optional
import hashlib


class ByzantineGeneral:
    """
    拜占庭将军问题

    【条件】
    - n ≥ 3f + 1（至少3f+1个将军才能容忍f个叛徒）
    - 消息可以伪造但不可篡改
    """

    def __init__(self, n: int, f: int):
        self.n = n  # 总将军数
        self.f = f  # 叛徒数

    def majority(self, values: List[int]) -> int:
        """获取多数值"""
        if not values:
            return 0
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts.items(), key=lambda x: x[1])[0]


class PBFT:
    """
    Practical Byzantine Fault Tolerance (PBFT)

    【协议阶段】
    1. Client Request: 客户端发送请求
    2. Pre-prepare: 主节点广播预准备
    3. Prepare: 所有节点互相广播准备
    4. Commit: 节点广播提交
    5. Reply: 节点回复客户端

    【安全性】
    - 需要2f+1个正常节点
    - View Change处理主节点故障
    """

    def __init__(self, n: int, f: int):
        if n < 3 * f + 1:
            raise ValueError("n must be >= 3f+1")
        self.n = n
        self.f = f
        self.view = 0
        self.sequence = 0
        self.state = "normal"
        self.messages = {
            "pre_prepare": [],
            "prepare": [],
            "commit": []
        }

    def handle_request(self, operation: str, client_id: int) -> Dict:
        """处理客户端请求"""
        self.sequence += 1
        seq = self.sequence

        # Pre-prepare阶段
        msg = {
            "view": self.view,
            "sequence": seq,
            "operation": operation,
            "client": client_id
        }
        self.messages["pre_prepare"].append(msg)

        # Prepare阶段
        self._broadcast("prepare", msg)

        # 检查是否收到足够的prepare消息
        if self._check_quorum("prepare", seq):
            # Commit阶段
            self._broadcast("commit", msg)

        return {"status": "processing", "sequence": seq}

    def _broadcast(self, msg_type: str, message: Dict):
        """广播消息"""
        self.messages[msg_type].append(message)

    def _check_quorum(self, msg_type: str, sequence: int) -> bool:
        """检查是否收到quorum个消息"""
        count = sum(1 for m in self.messages[msg_type]
                   if m["sequence"] == sequence)
        return count >= self.f + 1


class RandomCoin:
    """
    随机掷币协议

    【用于】
    - 异步BFT共识
    - 避免确定性攻击
    - common coin实现

    【方法】
    - 每个节点掷币并公布
    - 硬币正面数≥f+1则取majority
    - 否则使用预设值
    """

    def __init__(self, n: int, f: int):
        self.n = n
        self.f = f
        self.coins = {}

    def toss(self, round_num: int, node_id: int) -> int:
        """节点掷币"""
        seed = f"{round_num}:{node_id}:secret".encode()
        coin = int(hashlib.sha256(seed).hexdigest(), 16) % 2
        self.coins[(round_num, node_id)] = coin
        return coin

    def get_common_coin(self, round_num: int) -> int:
        """获取共同硬币"""
        coins = [(node_id, self.coins[(round_num, node_id)])
                for node_id in range(self.n)
                if (round_num, node_id) in self.coins]

        # 如果有足够硬币，取majority
        if len(coins) >= self.f + 1:
            values = [c for _, c in coins]
            return self._majority(values)

        # 否则返回默认值
        return 0

    def _majority(self, values: List[int]) -> int:
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts.items(), key=lambda x: x[1])[0]


# ========================================
# 测试
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("拜占庭共识 - 测试")
    print("=" * 50)

    # PBFT
    print("\n【测试1】PBFT")
    n, f = 4, 1  # n >= 3f+1
    pbft = PBFT(n, f)
    result = pbft.handle_request("transfer 100", client_id=1)
    print(f"  请求处理: {result}")
    print(f"  Pre-prepare消息数: {len(pbft.messages['pre_prepare'])}")
    print(f"  Prepare消息数: {len(pbft.messages['prepare'])}")

    # 随机掷币
    print("\n【测试2】随机掷币")
    coin = RandomCoin(n, f)
    round1 = 1
    results = [coin.toss(round1, i) for i in range(n)]
    print(f"  第{round1}轮掷币结果: {results}")
    common = coin.get_common_coin(round1)
    print(f"  共同硬币值: {common}")

    print("\n" + "=" * 50)

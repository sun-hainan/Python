# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / lightning_network

本文件实现 lightning_network 相关的算法功能。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class Channel:
    """闪电网络通道"""
    channel_id: str
    participant_a: str
    participant_b: str
    balance_a: int  # 聪（Satoshi）
    balance_b: int
    capacity: int

class LightningNode:
    """闪电网络节点"""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.channels: Dict[str, Channel] = {}
        self.pending_htlcs: List[dict] = []
    
    def create_channel(self, other_node: str, capacity: int) -> Channel:
        """创建通道"""
        channel_id = hashlib.sha256(f"{self.node_id}{other_node}".encode()).hexdigest()[:16]
        channel = Channel(
            channel_id=channel_id,
            participant_a=self.node_id,
            participant_b=other_node,
            balance_a=capacity,
            balance_b=0
        )
        self.channels[channel_id] = channel
        return channel
    
    def update_balance(self, channel_id: str, amount: int, direction: str) -> bool:
        """更新通道余额"""
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        
        if direction == "a_to_b":
            if channel.balance_a >= amount:
                channel.balance_a -= amount
                channel.balance_b += amount
            else:
                return False
        else:
            if channel.balance_b >= amount:
                channel.balance_b -= amount
                channel.balance_a += amount
            else:
                return False
        
        return True

class LightningNetwork:
    """闪电网络"""
    def __init__(self):
        self.nodes: Dict[str, LightningNode] = {}
    
    def add_node(self, node_id: str) -> LightningNode:
        """添加节点"""
        node = LightningNode(node_id)
        self.nodes[node_id] = node
        return node
    
    def find_path(self, source: str, dest: str) -> List[str]:
        """使用BFS找到从source到dest的路径"""
        if source not in self.nodes or dest not in self.nodes:
            return []
        
        visited = {source}
        queue = [[source]]
        
        while queue:
            path = queue.pop(0)
            current = path[-1]
            
            if current == dest:
                return path
            
            for channel in self.nodes[current].channels.values():
                other = channel.participant_b if current == channel.participant_a else channel.participant_a
                
                if other not in visited:
                    visited.add(other)
                    new_path = path + [other]
                    queue.append(new_path)
        
        return []
    
    def send_payment(self, source: str, dest: str, amount: int) -> bool:
        """发送支付"""
        path = self.find_path(source, dest)
        
        if not path:
            print(f"找不到从{source}到{dest}的路径")
            return False
        
        print(f"支付路径: {' -> '.join(path)}")
        
        # 模拟沿途更新余额
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            
            # 找到对应通道
            channel = None
            for ch in self.nodes[from_node].channels.values():
                if to_node in [ch.participant_a, ch.participant_b]:
                    channel = ch
                    break
            
            if channel:
                direction = "a_to_b" if from_node == channel.participant_a else "b_to_a"
                self.nodes[from_node].update_balance(channel.channel_id, amount, direction)
        
        return True

if __name__ == "__main__":
    print("=== 闪电网络测试 ===")
    
    # 创建网络
    network = LightningNetwork()
    
    # 添加节点
    alice = network.add_node("alice")
    bob = network.add_node("bob")
    charlie = network.add_node("charlie")
    dave = network.add_node("dave")
    
    print("创建节点: alice, bob, charlie, dave")
    
    # 创建通道
    alice.create_channel("bob", 100000)
    bob.create_channel("charlie", 100000)
    charlie.create_channel("dave", 100000)
    alice.create_channel("charlie", 50000)
    
    print("创建通道: alice<->bob, bob<->charlie, charlie<->dave, alice<->charlie")
    
    # 查找路径
    print("\n=== 路径查找 ===")
    path = network.find_path("alice", "dave")
    print(f"alice到dave的路径: {path if path else '无路径'}")
    
    path2 = network.find_path("dave", "alice")
    print(f"dave到alice的路径: {path2 if path2 else '无路径'}")
    
    # 发送支付
    print("\n=== 发送支付 ===")
    success = network.send_payment("alice", "dave", 10000)
    print(f"支付结果: {'成功' if success else '失败'}")
    
    # 检查通道余额
    print("\n=== 通道余额 ===")
    for node_id, node in network.nodes.items():
        for channel in node.channels.values():
            print(f"通道{channel.channel_id}: {channel.participant_a}={channel.balance_a}, "
                  f"{channel.participant_b}={channel.balance_b}")

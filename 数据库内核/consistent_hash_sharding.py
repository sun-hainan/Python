# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / consistent_hash_sharding

本文件实现 consistent_hash_sharding 相关的算法功能。
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Callable


@dataclass
class Node:
    """分片节点"""
    node_id: str  # 节点唯一标识
    ip: str  # 节点IP
    port: int  # 端口
    weight: int = 1  # 权重(用于虚拟节点)
    virtual_nodes: Set[int] = field(default_factory=set)  # 虚拟节点环上的位置


@dataclass
class Shard:
    """数据分片"""
    shard_id: int  # 分片ID
    node: Node  # 所属节点
    key_range: Tuple[int, int] = (0, 2**32 - 1)  # 键范围


class ConsistentHashRing:
    """
    一致性哈希环

    特性:
    1. 虚拟节点: 解决负载不均问题
    2. 最小化迁移: 扩缩容时只迁移部分数据
    3. 单调性: 新增节点不会破坏现有映射
    """

    def __init__(self, virtual_nodes_per_node: int = 150):
        self.ring: Dict[int, str] = {}  # 哈希环: hash值 -> 节点ID
        self.sorted_keys: List[int] = []  # 排序后的哈希值列表
        self.nodes: Dict[str, Node] = {}  # 物理节点: node_id -> Node
        self.virtual_nodes_per_node = virtual_nodes_per_node  # 每物理节点虚拟节点数

    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def _get_vnode_key(self, node_id: str, vnode_index: int) -> str:
        """生成虚拟节点键"""
        return f"{node_id}#VN{vnode_index}"

    def add_node(self, node: Node):
        """
        添加物理节点
        创建虚拟节点并分布到环上
        """
        self.nodes[node.node_id] = node

        # 根据权重创建虚拟节点
        total_vnodes = self.virtual_nodes_per_node * node.weight

        for i in range(total_vnodes):
            vnode_key = self._get_vnode_key(node.node_id, i)
            hash_value = self._hash(vnode_key)
            self.ring[hash_value] = node.node_id
            node.virtual_nodes.add(hash_value)

        self._rebuild_sorted_keys()

    def remove_node(self, node_id: str):
        """
        移除物理节点
        删除所有虚拟节点
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # 移除虚拟节点
        for hash_value in node.virtual_nodes:
            del self.ring[hash_value]

        node.virtual_nodes.clear()
        del self.nodes[node_id]
        self._rebuild_sorted_keys()

    def _rebuild_sorted_keys(self):
        """重建排序后的哈希值列表"""
        self.sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> Optional[Node]:
        """
        获取key对应的节点
        使用二分查找找到顺时针方向的第一个虚拟节点
        """
        if not self.ring:
            return None

        hash_value = self._hash(key)

        # 二分查找第一个 >= hash_value 的位置
        pos = self._binary_search(hash_value)
        if pos >= len(self.sorted_keys):
            pos = 0  # 环回起点

        selected_hash = self.sorted_keys[pos]
        node_id = self.ring[selected_hash]
        return self.nodes.get(node_id)

    def _binary_search(self, target: int) -> int:
        """二分查找第一个 >= target 的位置"""
        left, right = 0, len(self.sorted_keys)

        while left < right:
            mid = (left + right) // 2
            if self.sorted_keys[mid] < target:
                left = mid + 1
            else:
                right = mid

        return left

    def get_replicas(self, key: str, replica_count: int = 3) -> List[Node]:
        """
        获取key的多个副本节点(用于数据冗余)
        跳过相同物理节点的后续副本
        """
        if not self.ring:
            return []

        hash_value = self._hash(key)
        result: List[Node] = []
        seen_physical_nodes: Set[str] = set()
        pos = self._binary_search(hash_value)

        attempts = 0
        max_attempts = len(self.nodes) * self.virtual_nodes_per_node

        while len(result) < replica_count and attempts < max_attempts:
            if pos >= len(self.sorted_keys):
                pos = 0

            node_id = self.ring[self.sorted_keys[pos]]

            if node_id not in seen_physical_nodes:
                seen_physical_nodes.add(node_id)
                node = self.nodes.get(node_id)
                if node:
                    result.append(node)

            pos += 1
            attempts += 1

        return result

    def recalculate_migration(self, old_ring: Dict[int, str],
                              new_ring: Dict[int, str]) -> Dict[str, List[str]]:
        """
        计算扩缩容后的数据迁移

        返回:
            Dict[目标节点ID, [需要迁移的key列表]]
        """
        migration: Dict[str, List[str]] = {node.node_id: [] for node in self.nodes.values()}

        # 简化: 假设测试key空间
        test_keys = [f"key_{i}" for i in range(10000)]

        for key in test_keys:
            old_node = self._find_node_in_ring(old_ring, key)
            new_node = self.get_node(key)

            if old_node != new_node:
                if new_node and new_node.node_id in migration:
                    migration[new_node.node_id].append(key)

        return migration

    def _find_node_in_ring(self, ring: Dict[int, str], key: str) -> Optional[str]:
        """在指定环中查找key对应的节点"""
        if not ring:
            return None

        hash_value = self._hash(key)
        sorted_keys = sorted(ring.keys())

        pos = 0
        for i, h in enumerate(sorted_keys):
            if h >= hash_value:
                pos = i
                break
        else:
            pos = 0

        return ring.get(sorted_keys[pos])


class ShardingManager:
    """
    分片管理器

    管理多个一致性哈希环(用于不同用途)
    支持按业务分片
    """

    def __init__(self, virtual_nodes: int = 150):
        self.rings: Dict[str, ConsistentHashRing] = {}  # 业务 -> 哈希环
        self.virtual_nodes = virtual_nodes
        self.key_patterns: Dict[str, str] = {}  # key前缀 -> 业务标识

    def create_ring(self, ring_name: str) -> ConsistentHashRing:
        """创建新的哈希环"""
        ring = ConsistentHashRing(virtual_nodes_per_node=self.virtual_nodes)
        self.rings[ring_name] = ring
        return ring

    def register_key_pattern(self, pattern: str, ring_name: str):
        """注册key模式到业务环的映射"""
        self.key_patterns[pattern] = ring_name

    def _get_ring_for_key(self, key: str) -> ConsistentHashRing:
        """根据key确定使用哪个环"""
        # 检查是否有匹配的pattern
        for pattern, ring_name in self.key_patterns.items():
            if key.startswith(pattern):
                return self.rings.get(ring_name)

        # 默认返回第一个环
        return next(iter(self.rings.values())) if self.rings else None

    def put(self, key: str, value: str) -> bool:
        """写入数据"""
        ring = self._get_ring_for_key(key)
        if not ring:
            return False

        node = ring.get_node(key)
        if node:
            print(f"写入 {key} -> 节点 {node.node_id}({node.ip}:{node.port})")
            return True
        return False

    def get(self, key: str) -> Optional[Node]:
        """读取数据对应的节点"""
        ring = self._get_ring_for_key(key)
        if not ring:
            return None
        return ring.get_node(key)

    def get_with_replication(self, key: str,
                             replica_count: int = 3) -> List[Node]:
        """获取数据副本所在节点"""
        ring = self._get_ring_for_key(key)
        if not ring:
            return []
        return ring.get_replicas(key, replica_count)


def print_ring_stats(ring: ConsistentHashRing):
    """打印环统计信息"""
    print(f"物理节点数: {len(ring.nodes)}")
    print(f"虚拟节点总数: {len(ring.ring)}")
    for node_id, node in ring.nodes.items():
        print(f"  {node_id}: {len(node.virtual_nodes)} 虚拟节点")


if __name__ == "__main__":
    # 创建分片管理器
    manager = ShardingManager(virtual_nodes=100)

    # 创建用户分片环
    user_ring = manager.create_ring("users")
    manager.register_key_pattern("user:", "users")

    # 添加节点
    nodes = [
        Node("node1", "192.168.1.101", 6379, weight=1),
        Node("node2", "192.168.1.102", 6379, weight=1),
        Node("node3", "192.168.1.103", 6379, weight=2),  # 权重2,更多虚拟节点
    ]

    print("=== 添加节点 ===")
    for node in nodes:
        user_ring.add_node(node)
        print(f"添加节点: {node.node_id} ({node.ip}:{node.port})")

    print_ring_stats(user_ring)

    # 测试数据分布
    print("\n=== 数据分布测试 ===")
    key_distribution: Dict[str, int] = {}

    for i in range(1000):
        key = f"user:{i}"
        node = user_ring.get_node(key)
        if node:
            key_distribution[node.node_id] = key_distribution.get(node.node_id, 0) + 1

    for node_id, count in key_distribution.items():
        print(f"  {node_id}: {count} keys ({count/10:.1f}%)")

    # 测试副本
    print("\n=== 副本测试 ===")
    replicas = user_ring.get_replicas("user:123", replica_count=3)
    print(f"user:123 副本节点:")
    for r in replicas:
        print(f"  {r.node_id} ({r.ip}:{r.port})")

    # 测试新增节点
    print("\n=== 新增节点node4 ===")
    node4 = Node("node4", "192.168.1.104", 6379, weight=1)
    user_ring.add_node(node4)
    print_ring_stats(user_ring)

    # 重新统计分布
    key_distribution.clear()
    for i in range(1000):
        key = f"user:{i}"
        node = user_ring.get_node(key)
        if node:
            key_distribution[node.node_id] = key_distribution.get(node.node_id, 0) + 1

    print("\n新增节点后分布:")
    for node_id, count in key_distribution.items():
        print(f"  {node_id}: {count} keys ({count/10:.1f}%)")

    # 模拟迁移计算
    print("\n=== 数据迁移估算 ===")
    print("注: 扩缩容时只影响部分key,无需全量迁移")

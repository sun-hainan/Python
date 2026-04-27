# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / consistent_hashing

本文件实现 consistent_hashing 相关的算法功能。
"""

import hashlib
import bisect
import random


class ConsistentHash:
    """一致性哈希环"""

    def __init__(self, nodes=None, virtual_nodes=150, hash_fn=None):
        """
        初始化一致性哈希环
        
        参数:
            nodes: 初始节点列表
            virtual_nodes: 每个物理节点的虚拟节点数
            hash_fn: 哈希函数（默认使用 MD5）
        """
        # 虚拟节点数
        self.virtual_nodes = virtual_nodes
        # 哈希函数
        self.hash_fn = hash_fn or self._default_hash
        # 哈希环：有序的 (hash_value, node_name) 列表
        self.ring = []
        # 节点到虚拟节点的映射
        self.node_to_vnodes = {}
        # 虚拟节点到物理节点的映射
        self.vnode_to_node = {}
        
        # 添加初始节点
        if nodes:
            for node in nodes:
                self.add_node(node)

    @staticmethod
    def _default_hash(key):
        """
        默认哈希函数：使用 MD5 取前 4 字节作为 32 位整数
        
        参数:
            key: 要哈希的键（字符串或字节）
        返回:
            hash_value: 32 位无符号整数
        """
        if isinstance(key, str):
            key = key.encode('utf-8')
        # MD5 摘要
        digest = hashlib.md5(key).digest()
        # 取前 4 字节作为 32 位整数
        return int.from_bytes(digest[:4], byteorder='big')

    def _get_all_hashes(self, node):
        """
        获取一个节点对应的所有虚拟节点哈希值
        
        参数:
            node: 物理节点标识
        返回:
            hashes: 哈希值列表
        """
        hashes = []
        # 每个虚拟节点有一个唯一的后缀
        for i in range(self.virtual_nodes):
            vnode_name = f"{node}#VN{i}"
            hash_val = self.hash_fn(vnode_name)
            hashes.append(hash_val)
        return hashes

    def add_node(self, node):
        """
        添加物理节点到环上
        
        参数:
            node: 物理节点标识
        """
        if node in self.node_to_vnodes:
            return  # 已存在
        
        # 获取所有虚拟节点的哈希值
        hashes = self._get_all_hashes(node)
        self.node_to_vnodes[node] = hashes
        
        # 添加到环
        for h in hashes:
            # ring 存储 (hash, node_name)
            bisect.insort(self.ring, (h, node))
            self.vnode_to_node[h] = node

    def remove_node(self, node):
        """
        从环上移除物理节点
        
        参数:
            node: 物理节点标识
        """
        if node not in self.node_to_vnodes:
            return  # 不存在
        
        # 移除所有虚拟节点
        hashes = self.node_to_vnodes[node]
        for h in hashes:
            # 找到环中的位置并删除
            idx = bisect.bisect_left(self.ring, (h, node))
            if idx < len(self.ring) and self.ring[idx][0] == h:
                del self.ring[idx]
            del self.vnode_to_node[h]
        
        del self.node_to_vnodes[node]

    def get_node(self, key):
        """
        根据 key 获取负责的节点
        
        参数:
            key: 数据键
        返回:
            node: 物理节点标识
        """
        if not self.ring:
            return None
        
        # 计算 key 的哈希值
        hash_val = self.hash_fn(key)
        
        # 二分查找：找到第一个 >= hash_val 的位置
        idx = bisect.bisect_left(self.ring, (hash_val, ''))
        
        # 如果超过环尾，循环到环首
        if idx >= len(self.ring):
            idx = 0
        
        # 返回该位置的节点
        return self.ring[idx][1] if self.ring else None

    def get_nodes(self, key, n=2):
        """
        根据 key 获取多个节点（用于复制场景）
        
        参数:
            key: 数据键
            n: 返回的节点数
        返回:
            nodes: 节点列表
        """
        if not self.ring:
            return []
        
        hash_val = self.hash_fn(key)
        idx = bisect.bisect_left(self.ring, (hash_val, ''))
        
        nodes = []
        seen = set()
        attempts = 0
        max_attempts = len(self.ring) * 2  # 防止无限循环
        
        while len(nodes) < n and attempts < max_attempts:
            if idx >= len(self.ring):
                idx = 0
            
            node = self.ring[idx][1]
            if node not in seen:
                nodes.append(node)
                seen.add(node)
            
            idx += 1
            attempts += 1
        
        return nodes

    def get_distribution(self):
        """
        获取节点的虚拟节点分布（用于调试/监控）
        
        返回:
            distribution: {node: vnode_count} 字典
        """
        distribution = {node: len(vnodes) for node, vnodes in self.node_to_vnodes.items()}
        return distribution

    def get_ring_representation(self, num_segments=100):
        """
        获取环的文本表示（分段显示节点分布）
        
        参数:
            num_segments: 分段数
        返回:
            representation: 字符串
        """
        if not self.ring:
            return "Empty ring"
        
        # 计算每段的节点
        segment_size = 2**32 // num_segments
        segments = []
        
        for i in range(num_segments):
            start = i * segment_size
            end = (i + 1) * segment_size
            
            # 找该段覆盖的节点
            nodes_in_segment = set()
            for h, node in self.ring:
                if start <= h < end:
                    nodes_in_segment.add(node)
            
            if nodes_in_segment:
                segments.append(f"{i%10}" if nodes_in_segment else ".")
            else:
                segments.append(".")
        
        return ''.join(segments)


class DistributedCache:
    """基于一致性哈希的分布式缓存示例"""

    def __init__(self, nodes=None, virtual_nodes=150):
        """
        初始化分布式缓存
        
        参数:
            nodes: 初始节点列表
            virtual_nodes: 每个节点的虚拟节点数
        """
        self.hash_ring = ConsistentHash(nodes, virtual_nodes)
        # 模拟每个节点的数据存储
        self.storage = {node: {} for node in (nodes or [])}

    def add_node(self, node):
        """添加缓存节点"""
        self.hash_ring.add_node(node)
        self.storage[node] = {}

    def remove_node(self, node):
        """移除缓存节点"""
        self.hash_ring.remove_node(node)
        if node in self.storage:
            del self.storage[node]

    def set(self, key, value):
        """
        设置键值对（自动路由到正确节点）
        
        参数:
            key: 键
            value: 值
        """
        node = self.hash_ring.get_node(key)
        if node and node in self.storage:
            self.storage[node][key] = value

    def get(self, key):
        """
        获取键对应的值
        
        参数:
            key: 键
        返回:
            value: 值，如果不存在返回 None
        """
        node = self.hash_ring.get_node(key)
        if node and node in self.storage:
            return self.storage[node].get(key)
        return None

    def get_node_for_key(self, key):
        """获取 key 对应的节点"""
        return self.hash_ring.get_node(key)


if __name__ == "__main__":
    # 测试一致性哈希
    print("=== 一致性哈希测试 ===")
    
    # 创建环，初始有3个节点
    nodes = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
    ch = ConsistentHash(nodes, virtual_nodes=100)
    
    print(f"初始节点: {nodes}")
    print(f"环表示: {ch.get_ring_representation()}")
    
    # 测试 key 分布
    keys = [f"user:{i}" for i in range(1000)]
    distribution = {}
    for key in keys:
        node = ch.get_node(key)
        distribution[node] = distribution.get(node, 0) + 1
    
    print("\n初始分布:")
    for node, count in sorted(distribution.items()):
        print(f"  {node}: {count} keys ({count/len(keys)*100:.1f}%)")
    
    # 添加新节点
    print("\n--- 添加节点 192.168.1.4 ---")
    ch.add_node("192.168.1.4")
    print(f"环表示: {ch.get_ring_representation()}")
    
    # 重新计算分布
    new_distribution = {}
    for key in keys:
        node = ch.get_node(key)
        new_distribution[node] = new_distribution.get(node, 0) + 1
    
    print("\n添加节点后分布:")
    for node, count in sorted(new_distribution.items()):
        print(f"  {node}: {count} keys ({count/len(keys)*100:.1f}%)")
    
    # 计算迁移量
    migrated = sum(1 for key in keys if distribution.get(ch.get_node(key)) != new_distribution.get(ch.get_node(key)))
    print(f"\n需要迁移的 key 数: {migrated} ({migrated/len(keys)*100:.1f}%)")
    
    # 测试分布式缓存
    print("\n=== 分布式缓存测试 ===")
    cache = DistributedCache(["cache-1", "cache-2", "cache-3"])
    
    for i in range(10):
        cache.set(f"key-{i}", f"value-{i}")
    
    print("存储一些数据后:")
    for i in range(10):
        node = cache.get_node_for_key(f"key-{i}")
        value = cache.get(f"key-{i}")
        print(f"  key-{i} -> {node}: {value}")
    
    # 测试获取多个节点（复制场景）
    print("\n--- 复制测试 ---")
    for i in range(3):
        nodes = ch.get_nodes(f"replicated-key-{i}", n=2)
        print(f"replicated-key-{i} 的副本节点: {nodes}")

# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / distributed_db

本文件实现 distributed_db 相关的算法功能。
"""

from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import hashlib
import random

# ========== 一致性哈希 ==========

@dataclass
class VirtualNode:
    """虚拟节点"""
    physical_node: str       # 物理节点ID
    vnode_id: int            # 虚拟节点ID
    hash_value: int          # 哈希值
    
    def __repr__(self):
        return f"VN({self.physical_node}:vnode{self.vnode_id})"


@dataclass 
class PhysicalNode:
    """物理节点"""
    node_id: str
    host: str
    port: int
    weight: float = 1.0      # 权重（用于负载均衡）
    is_healthy: bool = True
    vnode_count: int = 150   # 每个物理节点的虚拟节点数
    
    def __repr__(self):
        return f"PhysicalNode({self.node_id}, {self.host}:{self.port})"


class ConsistentHash:
    """
    一致性哈希
    用于数据分片，支持节点动态扩缩容
    """
    
    def __init__(self, vnode_count_per_physical: int = 150):
        self.vnode_count = vnode_count_per_physical
        self.ring: Dict[int, VirtualNode] = {}  # hash -> vnode
        self.sorted_keys: List[int] = []        # 有序的哈希值列表
        self.physical_nodes: Dict[str, PhysicalNode] = {}
    
    def add_physical_node(self, node: PhysicalNode) -> int:
        """
        添加物理节点
        返回: 添加的虚拟节点数
        """
        self.physical_nodes[node.node_id] = node
        
        # 创建虚拟节点
        vnodes_added = 0
        for i in range(node.vnode_count):
            vnode_key = f"{node.node_id}#vnode{i}"
            hash_val = self._hash(vnode_key)
            
            vnode = VirtualNode(
                physical_node=node.node_id,
                vnode_id=i,
                hash_value=hash_val
            )
            
            self.ring[hash_val] = vnode
            vnodes_added += 1
        
        # 重建有序哈希列表
        self.sorted_keys = sorted(self.ring.keys())
        
        return vnodes_added
    
    def remove_physical_node(self, node_id: str) -> int:
        """
        移除物理节点
        返回: 移除的虚拟节点数
        """
        if node_id not in self.physical_nodes:
            return 0
        
        node = self.physical_nodes[node_id]
        removed = 0
        
        # 找到并移除该物理节点的所有虚拟节点
        keys_to_remove = [
            h for h, v in self.ring.items() 
            if v.physical_node == node_id
        ]
        
        for h in keys_to_remove:
            del self.ring[h]
            removed += 1
        
        self.physical_nodes.pop(node_id, None)
        self.sorted_keys = sorted(self.ring.keys())
        
        return removed
    
    def _hash(self, key: str) -> int:
        """计算哈希值（使用MD5保证分布均匀）"""
        md5 = hashlib.md5(key.encode('utf-8')).digest()
        return int.from_bytes(md5[:4], 'big', signed=True)
    
    def find_node(self, key: str) -> Optional[str]:
        """
        查找key应该存储的物理节点
        使用二分查找找到第一个大于等于key哈希值的节点
        """
        if not self.ring:
            return None
        
        hash_val = self._hash(key)
        
        # 二分查找
        left, right = 0, len(self.sorted_keys) - 1
        
        if hash_val <= self.sorted_keys[0] or hash_val > self.sorted_keys[-1]:
            # 绕回环形结构
            return self.ring[self.sorted_keys[0]].physical_node
        
        while left <= right:
            mid = (left + right) // 2
            
            if self.sorted_keys[mid] < hash_val:
                left = mid + 1
            else:
                right = mid - 1
        
        target_idx = min(left, len(self.sorted_keys) - 1)
        return self.ring[self.sorted_keys[target_idx]].physical_node
    
    def get_replica_nodes(self, key: str, replica_count: int = 3) -> List[str]:
        """
        获取key的多个副本节点（用于数据备份）
        """
        if not self.ring:
            return []
        
        hash_val = self._hash(key)
        result = []
        seen_physical = set()
        
        # 找到起始位置
        start_idx = 0
        for i, h in enumerate(self.sorted_keys):
            if h >= hash_val:
                start_idx = i
                break
        
        # 顺时针遍历获取不同物理节点
        idx = start_idx
        while len(result) < replica_count and len(result) < len(self.physical_nodes):
            vnode = self.ring[self.sorted_keys[idx]]
            
            if vnode.physical_node not in seen_physical:
                result.append(vnode.physical_node)
                seen_physical.add(vnode.physical_node)
            
            idx = (idx + 1) % len(self.sorted_keys)
        
        return result
    
    def get_distribution_stats(self) -> Dict[str, int]:
        """获取节点分布统计"""
        stats = {node_id: 0 for node_id in self.physical_nodes}
        
        # 采样测试
        test_keys = [f"key_{i}" for i in range(10000)]
        
        for key in test_keys:
            node = self.find_node(key)
            if node:
                stats[node] += 1
        
        return stats


# ========== 两阶段提交 (2PC) ==========

class CoordinatorState(IntEnum):
    """协调者状态"""
    INIT = 1
    VOTING = 2
    PRECOMMITTED = 3
    COMMITTED = 4
    ABORTED = 5


@dataclass
class Participant:
    """参与者"""
    node_id: str
    endpoint: str  # host:port
    vote: Optional[str] = None  # "yes" / "no"
    prepared_lsn: Optional[int] = None  # 预提交日志LSN


@dataclass
class TransactionContext:
    """分布式事务上下文"""
    gtxid: str            # 全局事务ID
    coordinator: str      # 协调者节点
    participants: List[Participant]
    state: CoordinatorState = CoordinatorState.INIT
    created_at: float = field(default_factory=time.time)


class TwoPhaseCommit:
    """
    两阶段提交协议 (2PC)
    Phase 1: 投票阶段 (Voting) - 询问参与者是否可以提交
    Phase 2: 决定阶段 (Decision) - 根据投票结果提交或回滚
    """
    
    def __init__(self, coordinator_id: str):
        self.coordinator_id = coordinator_id
        self.active_transactions: Dict[str, TransactionContext] = {}
    
    def begin_transaction(self, gtxid: str, participants: List[Participant]) -> TransactionContext:
        """开始分布式事务"""
        ctx = TransactionContext(
            gtxid=gtxid,
            coordinator=self.coordinator_id,
            participants=participants
        )
        self.active_transactions[gtxid] = ctx
        return ctx
    
    def phase1_vote(self, ctx: TransactionContext) -> bool:
        """
        阶段1: 发送PREPARE到所有参与者
        返回: 是否所有参与者都投票YES
        """
        ctx.state = CoordinatorState.VOTING
        
        all_voted_yes = True
        
        for participant in ctx.participants:
            # 模拟发送PREPARE消息
            vote = self._send_prepare(participant)
            participant.vote = vote
            
            if vote != "yes":
                all_voted_yes = False
        
        return all_voted_yes
    
    def _send_prepare(self, participant: Participant) -> str:
        """
        向参与者发送PREPARE请求
        实际实现需要RPC调用
        """
        # 模拟：90%概率投票YES
        return "yes" if random.random() < 0.9 else "no"
    
    def phase2_commit(self, ctx: TransactionContext) -> bool:
        """
        阶段2: 提交事务
        所有参与者都投了YES，执行COMMIT
        """
        ctx.state = CoordinatorState.COMMITTED
        
        commit_success = True
        
        for participant in ctx.participants:
            success = self._send_commit(participant)
            if not success:
                commit_success = False
        
        return commit_success
    
    def phase2_abort(self, ctx: TransactionContext):
        """
        阶段2: 回滚事务
        任一参与者投票NO，或协调者超时，全部回滚
        """
        ctx.state = CoordinatorState.ABORTED
        
        for participant in ctx.participants:
            self._send_abort(participant)
    
    def _send_commit(self, participant: Participant) -> bool:
        """发送COMMIT到参与者"""
        # 模拟
        return True
    
    def _send_abort(self, participant: Participant):
        """发送ABORT到参与者"""
        pass
    
    def execute_transaction(self, gtxid: str) -> bool:
        """
        执行完整的2PC事务
        """
        ctx = self.active_transactions.get(gtxid)
        if not ctx:
            return False
        
        # 阶段1: 投票
        if not self.phase1_vote(ctx):
            # 有参与者投了NO，回滚
            print(f"[2PC] 事务 {gtxid} 有参与者投票NO，回滚")
            self.phase2_abort(ctx)
            return False
        
        # 阶段2: 提交
        print(f"[2PC] 事务 {gtxid} 所有参与者投票YES，提交")
        return self.phase2_commit(ctx)


# ========== 分布式事务处理 ==========

class DistributedTransactionManager:
    """
    分布式事务管理器
    支持2PC和TCC模式
    """
    
    def __init__(self):
        self.ch = ConsistentHash()
        self.two_pc = TwoPhaseCommit("coordinator-001")
        self.transaction_log: Dict[str, Any] = {}
    
    def shard_key(self, key: str) -> Optional[str]:
        """确定key的分片节点"""
        return self.ch.find_node(key)
    
    def execute_distributed_query(self, query: str, 
                                 涉及的_keys: List[str]) -> Dict[str, Any]:
        """
        执行分布式查询
        1. 确定涉及的节点
        2. 生成执行计划
        3. 收集结果
        """
        involved_nodes = set()
        
        for key in 涉及的_keys:
            node = self.shard_key(key)
            if node:
                involved_nodes.add(node)
        
        results = {}
        for node in involved_nodes:
            # 模拟在节点上执行查询
            results[node] = {"status": "ok", "rows_affected": 1}
        
        return results


if __name__ == "__main__":
    print("=" * 60)
    print("分布式数据库演示")
    print("=" * 60)
    
    # 1. 一致性哈希
    print("\n--- 一致性哈希 ---")
    ch = ConsistentHash(vnode_count_per_physical=50)
    
    # 添加节点
    nodes = [
        PhysicalNode("node1", "192.168.1.1", 3306),
        PhysicalNode("node2", "192.168.1.2", 3306),
        PhysicalNode("node3", "192.168.1.3", 3306),
    ]
    
    total_vnodes = 0
    for node in nodes:
        added = ch.add_physical_node(node)
        total_vnodes += added
        print(f"添加节点 {node.node_id}: {added} 虚拟节点")
    
    print(f"总计虚拟节点: {total_vnodes}")
    
    # 查找key的节点
    test_keys = ["user:100", "order:500", "product:1000"]
    
    for key in test_keys:
        node = ch.find_node(key)
        replicas = ch.get_replica_nodes(key, 3)
        print(f"Key '{key}' -> 节点 {node}, 副本: {replicas}")
    
    # 统计分布
    print("\n节点分布统计（10000个key采样）:")
    stats = ch.get_distribution_stats()
    for node_id, count in stats.items():
        print(f"  {node_id}: {count} 个key ({count / 100:.1f}%)")
    
    # 节点扩缩容
    print("\n--- 节点扩缩容 ---")
    
    # 添加新节点
    new_node = PhysicalNode("node4", "192.168.1.4", 3306)
    added = ch.add_physical_node(new_node)
    print(f"添加 node4: {added} 虚拟节点")
    
    stats = ch.get_distribution_stats()
    print("添加后分布:", stats)
    
    # 移除节点
    removed = ch.remove_physical_node("node1")
    print(f"移除 node1: {removed} 虚拟节点")
    
    # 2. 两阶段提交
    print("\n--- 两阶段提交 (2PC) ---")
    tpc = TwoPhaseCommit("coordinator-001")
    
    # 准备参与者
    participants = [
        Participant("node1", "192.168.1.1:3306"),
        Participant("node2", "192.168.1.2:3306"),
        Participant("node3", "192.168.1.3:3306"),
    ]
    
    # 开始事务
    ctx = tpc.begin_transaction("gtx-12345", participants)
    print(f"开始分布式事务: {ctx.gtxid}, 参与者: {[p.node_id for p in ctx.participants]}")
    
    # 执行2PC
    success = tpc.execute_transaction(ctx.gtxid)
    print(f"事务结果: {'成功' if success else '失败'}")
    
    print("\n2PC注意事项:")
    print("  - 协调者崩溃时参与者可能一直等待（阻塞问题）")
    print("  - 解决方案：参与者设置超时，超时后自行回滚")
    print("  - 更好的方案：使用3PC（添加PreCommit阶段）")

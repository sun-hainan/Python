# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / consensus_raft

本文件实现 consensus_raft 相关的算法功能。
"""

import random
from typing import List, Optional


class RaftNode:
    """Raft节点"""

    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

    def __init__(self, node_id: int):
        """
        参数：
            node_id: 节点ID
        """
        self.node_id = node_id
        self.state = self.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []  # 日志条目列表
        self.commit_index = 0

    def become_leader(self) -> None:
        """成为Leader"""
        self.state = self.LEADER
        print(f"节点 {self.node_id} 成为 Leader")

    def become_candidate(self) -> None:
        """成为Candidate"""
        self.state = self.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        print(f"节点 {self.node_id} 成为 Candidate (term={self.current_term})")

    def become_follower(self) -> None:
        """成为Follower"""
        self.state = self.FOLLOWER


class RaftConsensus:
    """Raft共识协议"""

    def __init__(self, n_nodes: int):
        """
        参数：
            n_nodes: 节点数
        """
        self.nodes = [RaftNode(i) for i in range(n_nodes)]
        self.leader_id = None

    def election(self) -> int:
        """
        领导选举

        返回：选出的leader的ID
        """
        print("\n开始选举...")

        candidates = []
        votes = {}

        # 节点转为Candidate
        for node in self.nodes:
            if random.random() > 0.3:  # 简化：部分节点发起选举
                node.become_candidate()
                candidates.append(node)
                votes[node.node_id] = 1  # 投给自己

        # 收集选票
        for candidate in candidates:
            for node in self.nodes:
                if node.node_id != candidate.node_id and node.state == self.FOLLOWER:
                    if random.random() > 0.2:  # 简化：随机投票
                        votes[candidate.node_id] += 1

        # 找到获得多数票的
        max_votes = 0
        leader = None

        for node_id, count in votes.items():
            if count > max_votes:
                max_votes = count
                leader = node_id

        # 成为Leader
        if leader is not None:
            for node in self.nodes:
                if node.node_id == leader:
                    node.become_leader()
                    self.leader_id = leader
                    break

        return leader if leader is not None else -1

    def replicate_log(self, command: str) -> bool:
        """
        日志复制

        参数：
            command: 命令

        返回：是否成功
        """
        if self.leader_id is None:
            return False

        print(f"\n日志复制: {command}")

        # Leader追加日志
        leader = self.nodes[self.leader_id]
        log_entry = {
            'term': leader.current_term,
            'command': command
        }
        leader.log.append(log_entry)

        # 简化：假设复制成功
        print(f"  复制到所有节点...")
        return True


def raft_vs_paxos():
    """Raft vs Paxos"""
    print("=== Raft vs Paxos ===")
    print()
    print("Paxos：")
    print("  - 理论性更强")
    print("  - 难以理解和实现")
    print("  - Leslie Lamport 发明")
    print()
    print("Raft：")
    print("  - 易于理解和实现")
    print("  - 被很多系统采用")
    print("  - Diego Ongaro 设计")
    print()
    print("对比：")
    print("  - Raft更模块化")
    print("  - Paxos更通用")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Raft共识协议测试 ===\n")

    # 创建Raft集群
    n_nodes = 5
    raft = RaftConsensus(n_nodes)

    print(f"Raft集群: {n_nodes} 个节点")
    print()

    # 选举
    leader_id = raft.election()

    if leader_id >= 0:
        print(f"\n选举完成，Leader是节点 {leader_id}")

        # 模拟日志复制
        commands = ["SET x = 1", "SET y = 2", "ADD x y"]
        for cmd in commands:
            success = raft.replicate_log(cmd)
            print(f"  复制 {'成功' if success else '失败'}")

    print()
    raft_vs_paxos()

    print()
    print("说明：")
    print("  - Raft是分布式共识算法")
    print("  - 用于复制状态机")
    print("  - etcd, Consul 等使用")

# -*- coding: utf-8 -*-
"""
算法实现：分布式算法 / raft_consensus

本文件实现 raft_consensus 相关的算法功能。
"""

import time
import random
from typing import Optional, List, Dict, Any


class RaftNode:
    """Raft 节点"""
    # 节点状态枚举
    STATE_FOLLOWER = "Follower"
    STATE_CANDIDATE = "Candidate"
    STATE_LEADER = "Leader"

    def __init__(self, node_id: str, all_nodes: list):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.majority = (len(all_nodes) // 2) + 1

        # 持久状态（简化：存储在内存）
        self.current_term: int = 0                      # 当前任期
        self.voted_for: Optional[str] = None            # 本任期投票给了谁
        self.log: List[Dict] = []                       # 日志条目列表

        # -volatile 状态
        self.state = self.STATE_FOLLOWER
        self.commit_index: int = -1                     # 已提交的日志索引
        self.last_applied: int = -1                     # 已应用到状态机的日志索引

        # Leader 专属 volatile 状态
        self.next_index: Dict[str, int] = {}            # 下一个要发送的日志索引
        self.match_index: Dict[str, int] = {}           # 已复制给 Follower 的最高日志索引

        # 计时器
        self.election_timeout: float = 0.15             # 选举超时（秒）
        self.last_heartbeat: float = time.time()

    def reset_election_timer(self) -> None:
        """重置选举计时器（当收到 Leader 心跳时调用）"""
        self.last_heartbeat = time.time()

    def is_election_timeout(self) -> bool:
        """检查是否选举超时"""
        return (time.time() - self.last_heartbeat) > self.election_timeout

    def become_candidate(self) -> None:
        """转换为 Candidate 状态：增加 Term，自选为投票"""
        self.state = self.STATE_CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id  # 给自己投票
        self.reset_election_timer()

    def become_follower(self, term: int) -> None:
        """转换为 Follower 状态：更新 Term"""
        self.state = self.STATE_FOLLOWER
        self.current_term = term
        self.reset_election_timer()

    def become_leader(self) -> None:
        """转换为 Leader 状态：初始化 next_index 和 match_index"""
        self.state = self.STATE_LEADER
        # 初始化：next_index 设为 leader 最新日志索引 + 1
        last_log_index = len(self.log) - 1
        for node_id in self.all_nodes:
            self.next_index[node_id] = last_log_index + 1
            self.match_index[node_id] = 0

    def request_vote(self, term: int, candidate_id: str,
                     last_log_index: int, last_log_term: int) -> dict:
        """
        处理请求投票（RequestVote RPC）
        返回：{vote_granted: bool}
        投票规则：
        1. Term < current_term → 拒绝
        2. 若 voted_for 为空或为 candidate，且 candidate 日志至少与自己一样新 → 投票
        """
        # 规则 1：Term 必须 >= current_term（否则拒绝）
        if term < self.current_term:
            return {"term": self.current_term, "vote_granted": False}

        # 若收到更高 Term，转为 Follower
        if term > self.current_term:
            self.become_follower(term)

        # 规则 2：检查是否已投票
        if self.voted_for is not None and self.voted_for != candidate_id:
            return {"term": self.current_term, "vote_granted": False}

        # 规则 3：检查日志新颖度（Up-to-date 规则）
        # 条件：candidate 的 lastLogTerm > 我的 lastLogTerm
        #      或 candidate 的 lastLogTerm == 我的 lastLogTerm 且 lastLogIndex >= 我的 lastLogIndex
        my_last_log_index = len(self.log) - 1
        my_last_log_term = self.log[my_last_log_index]["term"] if self.log else 0

        if last_log_term > my_last_log_term:
            pass  # candidate 日志更新
        elif last_log_term == my_last_log_term and last_log_index < my_last_log_index:
            return {"term": self.current_term, "vote_granted": False}  # candidate 日志较旧

        # 满足所有条件，投票给 candidate
        self.voted_for = candidate_id
        self.reset_election_timer()
        return {"term": self.current_term, "vote_granted": True}

    def append_entries(self, term: int, leader_id: str,
                      prev_log_index: int, prev_log_term: int,
                      entries: List[Dict], leader_commit: int) -> dict:
        """
        处理日志追加请求（AppendEntries RPC）
        包含心跳和日志复制两种功能
        """
        # Term 检查
        if term < self.current_term:
            return {"term": self.current_term, "success": False}

        self.become_follower(term)
        self.reset_election_timer()

        # 一致性检查：prevLogIndex 处的日志条目必须匹配
        if prev_log_index >= 0:
            if prev_log_index >= len(self.log):
                return {"term": self.current_term, "success": False}
            if self.log[prev_log_index]["term"] != prev_log_term:
                # 不匹配：删除冲突日志
                self.log = self.log[:prev_log_index]
                return {"term": self.current_term, "success": False}

        # 追加新条目
        for i, entry in enumerate(entries):
            idx = prev_log_index + 1 + i
            if idx < len(self.log):
                if self.log[idx]["term"] != entry["term"]:
                    self.log[idx] = entry  # 替换冲突条目
            else:
                self.log.append(entry)  # 追加新条目

        # 更新 commit_index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)

        return {"term": self.current_term, "success": True}


class RaftConsensus:
    """Raft 共识管理器：负责选举和日志复制"""
    def __init__(self, nodes: Dict[str, RaftNode]):
        self.nodes = nodes

    def start_election(self, candidate_node_id: str) -> bool:
        """模拟选举过程"""
        candidate = self.nodes[candidate_node_id]
        candidate.become_candidate()

        votes = 1  # 自己的一票
        last_log_index = len(candidate.log) - 1
        last_log_term = candidate.log[last_log_index]["term"] if candidate.log else 0

        for node_id, node in self.nodes.items():
            if node_id == candidate_node_id:
                continue
            result = node.request_vote(
                candidate.current_term,
                candidate_node_id,
                last_log_index,
                last_log_term
            )
            if result.get("vote_granted"):
                votes += 1

        if votes >= candidate.majority:
            candidate.become_leader()
            return True
        else:
            candidate.become_follower(candidate.current_term)
            return False

    def replicate_log(self, leader_id: str, entry: Dict) -> bool:
        """Leader 复制日志条目到 Followers"""
        leader = self.nodes[leader_id]
        if leader.state != leader.STATE_LEADER:
            return False

        success_count = 1  # Leader 自身
        for node_id, node in self.nodes.items():
            if node_id == leader_id:
                continue

            prev_log_index = leader.next_index[node_id] - 1
            prev_log_term = leader.log[prev_log_index]["term"] if prev_log_index >= 0 else 0

            result = node.append_entries(
                leader.current_term, leader_id,
                prev_log_index, prev_log_term,
                [entry], leader.commit_index
            )

            if result.get("success"):
                success_count += 1
                leader.match_index[node_id] = leader.next_index[node_id]
                leader.next_index[node_id] += 1

        # 多数派复制成功则提交
        if success_count >= leader.majority:
            leader.log.append(entry)
            leader.commit_index = len(leader.log) - 1
            return True
        return False


# ============================ 测试代码 ============================
if __name__ == "__main__":
    node_ids = ["N1", "N2", "N3"]
    nodes = {nid: RaftNode(nid, node_ids) for nid in node_ids}
    raft = RaftConsensus(nodes)

    # 模拟选举：N1 先发起选举
    election_won = raft.start_election("N1")
    print(f"N1 选举结果: {'成功成为 Leader' if election_won else '失败'}")

    if election_won:
        # 模拟日志追加
        entry = {"term": 1, "command": "SET x 100"}
        committed = raft.replicate_log("N1", entry)
        print(f"日志复制结果: {'已提交' if committed else '未提交'}")

        # 验证状态
        for nid, node in nodes.items():
            print(f"节点 {nid}: state={node.state}, commit_index={node.commit_index}")

    # 验证至少有一个 Leader
    leaders = [n for n in nodes.values() if n.state == RaftNode.STATE_LEADER]
    assert len(leaders) == 1, "应该恰好有一个 Leader"
    print("✅ Raft 共识达成！")

    # 时间复杂度：选举 O(N)，日志复制 O(N)
    # 空间复杂度：O(N·L) 日志存储

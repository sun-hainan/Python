# -*- coding: utf-8 -*-
"""
算法实现：分布式算法 / paxos

本文件实现 paxos 相关的算法功能。
"""

from typing import Optional, Dict, Any


class PaxosNode:
    """Paxos 节点：可以扮演提议者、接受者、学习者角色"""
    def __init__(self, node_id: str, all_nodes: list):
        self.node_id = node_id                          # 节点唯一标识
        self.all_nodes = all_nodes                      # 所有节点列表（用于判断多数派）
        self.majority = (len(all_nodes) // 2) + 1       # 多数派数量

        # 状态
        self.highest_proposal_seen: int = 0             # 已见过的最高提案编号
        self.promised_proposal: Optional[int] = None    # 本节点已承诺的提案编号
        self.accepted_proposal: Optional[int] = None     # 本节点已接受的提案编号
        self.accepted_value: Optional[Any] = None       # 本节点已接受的值

        self.messages: list = []                        # 模拟的消息日志

    def send_message(self, target: str, msg_type: str, content: dict) -> None:
        """模拟消息发送（实际分布式系统中会通过网络）"""
        self.messages.append({
            "from": self.node_id,
            "to": target,
            "type": msg_type,
            "content": content
        })

    def receive_prepare(self, proposal_num: int, from_node: str) -> dict:
        """接收 PREPARE 请求：接受者检查是否承诺更高编号的提案"""
        if proposal_num > self.highest_proposal_seen:
            self.highest_proposal_seen = proposal_num
            # 若已有已接受的提案，返回它（用于保证一致性）
            if self.accepted_proposal is not None:
                return {
                    "type": "PROMISE",
                    "ok": True,
                    "accepted_proposal": self.accepted_proposal,
                    "accepted_value": self.accepted_value
                }
            else:
                return {"type": "PROMISE", "ok": True, "accepted_proposal": None, "accepted_value": None}
        else:
            return {"type": "PROMISE", "ok": False}  # 拒绝：编号太低

    def receive_accept_request(self, proposal_num: int, value: Any, from_node: str) -> dict:
        """接收 ACCEPT 请求：接受者检查是否已承诺更高编号"""
        if proposal_num >= self.highest_proposal_seen:
            self.promised_proposal = proposal_num
            self.accepted_proposal = proposal_num
            self.accepted_value = value
            return {"type": "ACCEPTED", "ok": True}
        else:
            return {"type": "ACCEPTED", "ok": False}  # 拒绝

    def receive_learn(self, proposal_num: int, value: Any) -> None:
        """接收 LEARN 消息：学习者记录最终达成一致的值"""
        self.accepted_proposal = proposal_num
        self.accepted_value = value


class Proposer:
    """提议者：发起提案"""
    def __init__(self, node: PaxosNode):
        self.node = node
        self.current_proposal_num = 0                  # 当前提案编号（单调递增）

    def generate_proposal_num(self) -> int:
        """生成唯一且单调递增的提案编号 = node_id.hash + counter"""
        self.current_proposal_num += 1
        return int(f"{self.node.node_id}{self.current_proposal_num}")

    def run_paxos(self, value: Any, acceptors: list) -> tuple:
        """
        运行完整的 Paxos 流程，返回 (success: bool, chosen_value: Any)
        1. PREPARE 阶段：向所有接受者发送提案请求
        2. PROMISE 收集：若多数派返回承诺，则进入 ACCEPT 阶段
        3. ACCEPT 阶段：向所有接受者发送接受请求
        4. 统计 ACCEPTED 回复，若多数派接受则值被选定
        """
        proposal_num = self.generate_proposal_num()

        # ===== PREPARE 阶段 =====
        promises_collected = []
        for acceptor in acceptors:
            response = acceptor.receive_prepare(proposal_num, self.node.node_id)
            if response.get("ok"):
                promises_collected.append(response)

        # 检查是否获得多数派承诺
        if len(promises_collected) < self.node.majority:
            return False, None  # PREPARE 失败

        # ===== 选取值阶段 =====
        # 若任何承诺中包含已接受的值，优先使用编号最大的值（保证一致性）
        accepted_values = [
            (p["accepted_proposal"], p["accepted_value"])
            for p in promises_collected
            if p.get("accepted_proposal") is not None
        ]
        if accepted_values:
            # 选择编号最大的已接受值
            accepted_values.sort(key=lambda x: x[0], reverse=True)
            chosen_value = accepted_values[0][1]
        else:
            chosen_value = value  # 无历史值，使用新值

        # ===== ACCEPT 阶段 =====
        accept_count = 0
        for acceptor in acceptors:
            response = acceptor.receive_accept_request(proposal_num, chosen_value, self.node.node_id)
            if response.get("ok"):
                accept_count += 1

        # 检查是否获得多数派接受
        if accept_count >= self.node.majority:
            # 通知所有学习者（这里简单地在所有节点学习）
            for acceptor in acceptors:
                acceptor.receive_learn(proposal_num, chosen_value)
            return True, chosen_value
        else:
            return False, None  # ACCEPT 失败


# ============================ 测试代码 ============================
if __name__ == "__main__":
    # 构建 3 节点 Paxos 系统
    node_ids = ["Node1", "Node2", "Node3"]
    nodes: Dict[str, PaxosNode] = {nid: PaxosNode(nid, node_ids) for nid in node_ids}
    node_list = list(nodes.values())

    # Node1 作为提议者发起提案
    proposer = Proposer(nodes["Node1"])
    success, value = proposer.run_paxos("prepare_data", node_list)

    print(f"Paxos 提案结果: success={success}, value={value}")

    # 验证：至少多数派节点接受了相同的值
    accepted_nodes = [n for n in node_list if n.accepted_value == value]
    print(f"接受该值的节点数: {len(accepted_nodes)} / {len(node_list)}")
    assert success and len(accepted_nodes) >= 2
    print("✅ Paxos 一致性达成！")

    # 时间复杂度：O(N) — 需要 2 轮通信（PREPARE + ACCEPT）
    # 空间复杂度：O(N) — 每个节点存储提案状态

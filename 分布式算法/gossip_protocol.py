# -*- coding: utf-8 -*-
"""
算法实现：分布式算法 / gossip_protocol

本文件实现 gossip_protocol 相关的算法功能。
"""

import random
import time
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class MemberInfo:
    """成员节点信息"""
    member_id: str
    incarnation: int = 0                 # 代号（每次自举/重启时递增，用于区分新旧）
    is_alive: bool = True                # 是否存活
    last_update: float = 0.0             # 上次更新时间


class GossipNode:
    """Gossip 节点"""
    def __init__(self, node_id: str, all_nodes: List[str],
                 fanout: int = 3, interval: float = 0.1):
        self.node_id = node_id
        self.all_nodes = all_nodes         # 所有已知节点列表（模拟成员列表）
        self.fanout = fanout               # 每次 gossip 传播的目标数
        self.interval = interval           # gossip 周期（秒）

        # 成员状态表（MemberList）：key 为 member_id
        self.member_list: Dict[str, MemberInfo] = {}
        self.initialize_member_list()

        self.message_log: List[Dict] = []  # 模拟消息历史

    def initialize_member_list(self) -> None:
        """初始化成员列表：将所有已知节点标记为存活"""
        for mid in self.all_nodes:
            self.member_list[mid] = MemberInfo(mid, incarnation=1, is_alive=True, last_update=time.time())

    def get_alive_members(self) -> List[str]:
        """获取当前活跃成员列表（排除自己）"""
        return [mid for mid in self.all_nodes if mid != self.node_id and
                self.member_list[mid].is_alive]

    def select_gossip_targets(self) -> List[str]:
        """随机选择 fanout 个节点作为 gossip 目标"""
        alive = self.get_alive_members()
        if len(alive) <= self.fanout:
            return alive
        return random.sample(alive, self.fanout)

    def create_gossip_message(self) -> Dict:
        """
        创建 gossip 消息：携带本节点的成员列表摘要
        消息格式：{sender, incarnation, member_deltas}
        """
        # 简化：携带完整成员列表的快照
        # 真实协议中通常只携带 delta（增量更新）
        return {
            "type": "GOSSIP",
            "sender": self.node_id,
            "incarnation": self.member_list[self.node_id].incarnation,
            "member_list": {
                mid: {"incarnation": info.incarnation, "is_alive": info.is_alive}
                for mid, info in self.member_list.items()
            }
        }

    def receive_gossip(self, message: Dict) -> None:
        """
        接收并处理 gossip 消息：合并成员状态
        合并规则（SWIM 风格）：
        - 若收到的 incarnation > 本地记录的 incarnation，更新为新的
        - 若收到节点标记为 dead，但本地 incarnation 更高，则忽略
        """
        sender = message["sender"]
        remote_list = message["member_list"]

        # 更新 sender 的活跃状态（每次收到活着节点的消息就认为它活着）
        if sender in self.member_list:
            self.member_list[sender].is_alive = True
            self.member_list[sender].last_update = time.time()

        # 合并远程成员列表
        for mid, remote_info in remote_list.items():
            if mid not in self.member_list:
                # 新发现的节点
                self.member_list[mid] = MemberInfo(
                    mid,
                    incarnation=remote_info["incarnation"],
                    is_alive=remote_info["is_alive"],
                    last_update=time.time()
                )
            else:
                local = self.member_list[mid]
                remote_inc = remote_info["incarnation"]

                # incarnation 更高者获胜
                if remote_inc > local.incarnation:
                    local.incarnation = remote_inc
                    local.is_alive = remote_info["is_alive"]
                    local.last_update = time.time()
                elif remote_inc == local.incarnation and remote_info["is_alive"] and not local.is_alive:
                    # incarnation 相同，但远程说活着 -> 更新为活着
                    local.is_alive = True
                    local.last_update = time.time()

    def mark_suspected_dead(self, member_id: str) -> None:
        """将节点标记为疑似死亡（SWIM 中的间接探测）"""
        if member_id in self.member_list:
            self.member_list[member_id].is_alive = False

    def gossip_cycle(self, other_node: "GossipNode") -> None:
        """执行一轮 gossip：选择目标、发送、接收"""
        targets = self.select_gossip_targets()
        if not targets:
            return

        msg = self.create_gossip_message()
        self.message_log.append(msg)

        # 模拟：只向第一个目标发送（实际中是广播到所有目标）
        if other_node.node_id in targets:
            other_node.receive_gossip(msg)

    def run_gossip_rounds(self, rounds: int, all_nodes: List["GossipNode"]) -> None:
        """运行多轮 gossip 模拟"""
        for r in range(rounds):
            # 随机选择一个邻居进行 gossip
            others = [n for n in all_nodes if n.node_id != self.node_id]
            if others:
                target = random.choice(others)
                self.gossip_cycle(target)
            time.sleep(self.interval * 0.1)  # 加速模拟

    def get_cluster_view(self) -> Dict[str, bool]:
        """获取本节点视角的集群成员存活状态"""
        return {mid: info.is_alive for mid, info in self.member_list.items()}


# ============================ 测试代码 ============================
if __name__ == "__main__":
    # 创建 5 个节点组成的集群
    node_ids = [f"Node{i}" for i in range(5)]
    nodes = {nid: GossipNode(nid, node_ids, fanout=2) for nid in node_ids}
    node_list = list(nodes.values())

    print("=== Gossip 协议演示 ===")
    print(f"集群规模: {len(node_ids)} 个节点")

    # 模拟 Node0 标记 Node3 为死亡
    nodes["Node0"].mark_suspected_dead("Node3")
    print("Node0 将 Node3 标记为死亡")

    # 运行 10 轮 gossip
    print("\n运行 10 轮 gossip...")
    for r in range(10):
        for node in node_list:
            others = [n for n in node_list if n.node_id != node.node_id]
            if others:
                target = random.choice(others)
                node.gossip_cycle(target)

    # 检查最终视图
    print("\n=== 各节点视角的集群状态 ===")
    for nid, node in nodes.items():
        view = node.get_cluster_view()
        alive = [mid for mid, alive in view.items() if alive]
        dead = [mid for mid, alive in view.items() if not alive]
        print(f"{nid}: 存活={alive}, 死亡={dead}")

    # 验证：至少多数节点对 Node3 状态达成一致
    node3_views = [nodes[n].member_list.get("Node3", MemberInfo("Node3")).is_alive for n in node_ids]
    consistent = len(set(node3_views)) == 1
    print(f"\nNode3 状态一致性: {'✅ 一致' if consistent else '⚠️ 不一致（正常，最终会收敛）'}")

    # 时间复杂度：O(log N) — 每轮 gossip 覆盖 O(log N) 节点
    # 空间复杂度：O(N) — 每个节点维护 N 个成员信息

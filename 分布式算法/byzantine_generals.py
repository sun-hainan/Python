# -*- coding: utf-8 -*-
"""
算法实现：分布式算法 / byzantine_generals

本文件实现 byzantine_generals 相关的算法功能。
"""

from typing import List, Optional, Dict, Any
from collections import defaultdict
import random


class ByzantineGeneral:
    """拜占庭将军节点"""
    def __init__(self, general_id: str, is_byzantine: bool = False):
        self.general_id = general_id
        self.is_byzantine = is_byzantine    # 是否为恶意节点
        self.received_orders: Dict[int, Any] = {}  # 存储各轮收到的命令 {round: order}
        self.decision: Optional[str] = None  # 最终决定（OM 算法结果）

    def send_order(self, order: str) -> str:
        """
        发送命令：若为拜占庭节点，随机发送错误命令
        模拟：拜占庭将军可以撒谎
        """
        if self.is_byzantine:
            # 拜占庭节点发送随机命令（模拟恶意行为）
            return random.choice(["ATTACK", "RETREAT", "WAIT"])
        return order  # 忠诚节点如实转发


class ByzantineConsensus:
    """拜占庭共识管理器（口信消息算法 OM）"""

    def __init__(self, generals: List[ByzantineGeneral], commander: ByzantineGeneral):
        self.generals = generals              # 所有将军（包括副官）
        self.commander = commander            # 主将（发起命令）
        self.f = self._calc_max_byzantine()   # 可容忍的拜占庭节点数

    def _calc_max_byzantine(self) -> int:
        """计算可容忍的最大拜占庭节点数：f < N/3"""
        n = len(self.generals)
        return (n - 1) // 3

    def om(self, sender: ByzantineGeneral, round_num: int, order: Any,
           generals_except_sender: List[ByzantineGeneral]) -> Any:
        """
        OM(f) 算法：递归的口信消息协议
        round_num: 当前轮数（从 f 递减到 0）
        order: 发送者声称的命令
        generals_except_sender: 除发送者外的将军列表
        """
        if round_num == 0:
            # 基础情况 OM(0)：副官直接使用收到的命令
            return order

        # 获取下一个发令者（递归的源）
        # OM(f) 中，其他将军会将命令传递给下一层
        # 实际实现中，这里简化：每个将军执行自己的 OM(f-1)
        if len(generals_except_sender) == 0:
            return order

        # 模拟：副官将命令告知其他将军（排除 sender）
        # 下一轮：每个将军作为新的发送者调用 OM(round-1)
        # 简化：用投票决定：若多数派收到相同的命令，则采纳
        orders_received = []
        for g in generals_except_sender:
            if g.is_byzantine:
                # 拜占庭将军可能发送错误命令
                orders_received.append(g.send_order(order))
            else:
                orders_received.append(order)  # 忠诚将军如实转发

        # 多数裁决
        from collections import Counter
        if orders_received:
            majority_order, count = Counter(orders_received).most_common(1)[0]
            if count > len(orders_received) // 2:
                return majority_order
        return order  # 默认采纳原始命令

    def run_consensus(self, initial_order: str) -> Dict[str, str]:
        """
        运行拜占庭共识：主将发送命令，所有忠诚将军达成一致
        返回：{general_id: decision}
        """
        result = {}
        loyal_generals = [g for g in self.generals if not g.is_byzantine]

        for general in loyal_generals:
            # 发送者（commander）发送给其他所有将军
            generals_except_commander = [g for g in self.generals if g.general_id != self.commander.general_id]

            # 若 general 是 commander 本身（主将自己做决定）
            if general.general_id == self.commander.general_id:
                result[general.general_id] = initial_order
                general.decision = initial_order
            else:
                # 执行 OM(f) 协议
                final_order = self.om(self.commander, self.f, initial_order, generals_except_commander)
                result[general.general_id] = final_order
                general.decision = final_order

        return result


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=== 拜占庭将军问题演示 ===")

    n = 7  # 总节点数
    f = (n - 1) // 3  # 可容忍拜占庭节点数
    print(f"总将军数: {n}, 可容忍拜占庭节点数: {f}, 要求: n >= 3f+1 = {3*f+1}")

    # 创建将军
    general_ids = [f"G{i}" for i in range(n)]
    is_byzantine_list = [False] * (n - f) + [True] * f  # 前 n-f 个忠诚，后 f 个恶意
    random.seed(42)
    random.shuffle(is_byzantine_list)  # 随机分配哪些是拜占庭

    generals = [ByzantineGeneral(gid, is_byzantine_list[i]) for i, gid in enumerate(general_ids)]
    commander = generals[0]

    print(f"主将: {commander.general_id} (忠诚={not commander.is_byzantine})")
    byzantine = [g.general_id for g in generals if g.is_byzantine]
    loyal = [g.general_id for g in generals if not g.is_byzantine]
    print(f"拜占庭将军: {byzantine}")
    print(f"忠诚将军: {loyal}")

    # 运行共识
    consensus = ByzantineConsensus(generals, commander)
    decisions = consensus.run_consensus("ATTACK")

    print("\n=== 决策结果 ===")
    for gid, decision in decisions.items():
        status = "拜占庭" if gid in byzantine else "忠诚"
        marker = "✓" if decision == "ATTACK" else "✗"
        print(f"  {gid} ({status}): {decision} {marker}")

    # 验证：所有忠诚将军必须达成相同决定
    loyal_decisions = [decisions[g.general_id] for g in generals if not g.is_byzantine]
    consistent = len(set(loyal_decisions)) == 1
    print(f"\n忠诚将军一致性: {'✅ 达成共识' if consistent else '❌ 未达成共识'}")

    # 时间复杂度：O(N^(f+1)) — 每轮所有节点互相通信
    # 空间复杂度：O(N^f) — 存储各轮消息
    print(f"\n通信复杂度: O(N^(f+1)) = O({n}^({f+1}))")

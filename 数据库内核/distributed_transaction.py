# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / distributed_transaction

本文件实现 distributed_transaction 相关的算法功能。
"""

from typing import List, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import time
import random


# =============================================================================
# 枚举定义
# =============================================================================

class CoordinatorState(Enum):
    """协调者状态"""
    INIT = "init"  # 初始状态
    PREPARING = "preparing"  # 正在 Prepare 阶段
    COMMITTED = "committed"  # 已提交
    ABORTED = "aborted"  # 已回滚


class ParticipantState(Enum):
    """参与者状态"""
    INITIAL = "initial"  # 初始状态
    PREPARED = "prepared"  # 已 Prepared（投票Yes）
    COMMITTED = "committed"  # 已提交
    ABORTED = "aborted"  # 已回滚


# =============================================================================
# 数据结构定义
# =============================================================================

@dataclass
class TransactionContext:
    """事务上下文：记录全局事务信息"""
    transaction_id: str  # 全局事务ID
    coordinator_id: str  # 协调者ID
    participants: List[str]  # 参与者列表
    created_at: float  # 创建时间

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class VoteMessage:
    """投票消息：参与者对事务的投票"""
    participant_id: str  # 参与者ID
    transaction_id: str  # 事务ID
    vote: bool  # True=同意提交，False=选择回滚
    reason: Optional[str] = None  # 拒绝原因（如果有）


@dataclass
class DecisionMessage:
    """决策消息：协调者发送给参与者的最终决策"""
    transaction_id: str  # 事务ID
    decision: str  # "commit" 或 "abort"
    timestamp: float


# =============================================================================
# 两阶段提交（2PC）实现
# =============================================================================

class TwoPhaseCommit:
    """
    两阶段提交协议（2PC）
    ======================

    阶段1（Prepare）：
        协调者向所有参与者发送 Prepare 消息
        参与者执行本地事务（但不提交），然后投票

    阶段2（Commit/Rollback）：
        协调者收到所有投票后：
            - 全是Yes：发送 Commit 消息，所有参与者提交
            - 有No或超时：发送 Abort 消息，所有参与者回滚

    问题：
        - 协调者单点故障可能导致参与者阻塞
        - 参与者在收到决策前必须锁定资源
    """

    def __init__(self, coordinator_id: str):
        self.coordinator_id = coordinator_id  # 协调者ID
        self.transactions: Dict[str, TransactionContext] = {}  # 活跃事务
        self.votes: Dict[str, List[VoteMessage]] = {}  # 事务ID -> 投票列表
        self.participant_states: Dict[str, Dict[str, ParticipantState]] = {}  # participant_id -> {tx_id -> state}

    def begin_transaction(self, transaction_id: str, participant_ids: List[str]) -> TransactionContext:
        """
        开始一个新事务

        参数:
            transaction_id: 全局唯一事务ID
            participant_ids: 参与的节点ID列表

        返回:
            事务上下文对象
        """
        ctx = TransactionContext(
            transaction_id=transaction_id,
            coordinator_id=self.coordinator_id,
            participants=participant_ids,
            created_at=time.time()
        )
        self.transactions[transaction_id] = ctx
        self.votes[transaction_id] = []
        return ctx

    def send_prepare(self, transaction_id: str) -> bool:
        """
        发送 Prepare 消息给所有参与者

        参数:
            transaction_id: 事务ID

        返回:
            是否成功发送
        """
        if transaction_id not in self.transactions:
            raise ValueError(f"事务 {transaction_id} 不存在")

        ctx = self.transactions[transaction_id]
        print(f"[协调者 {self.coordinator_id}] 发送 Prepare 到 {ctx.participants}")

        # 模拟所有参与者收到 Prepare 并响应
        for participant_id in ctx.participants:
            response = self._participant_receive_prepare(participant_id, transaction_id)
            print(f"  参与者 {participant_id} 响应: {'Yes' if response.vote else 'No'}"
                  + (f" ({response.reason})" if response.reason else ""))
            self.votes[transaction_id].append(response)

        return True

    def _participant_receive_prepare(self, participant_id: str, transaction_id: str) -> VoteMessage:
        """
        模拟参与者接收 Prepare 消息

        实际实现中，这个函数会在参与者节点上执行
        """
        # 初始化参与者状态
        if participant_id not in self.participant_states:
            self.participant_states[participant_id] = {}
        self.participant_states[participant_id][transaction_id] = ParticipantState.PREPARED

        # 模拟投票：90%概率同意，10%概率拒绝（模拟锁冲突等）
        vote = random.random() > 0.1
        reason = None if vote else "本地锁冲突，无法 Prepare"

        return VoteMessage(
            participant_id=participant_id,
            transaction_id=transaction_id,
            vote=vote,
            reason=reason
        )

    def collect_votes(self, transaction_id: str) -> bool:
        """
        收集所有投票，判断是否可以提交

        参数:
            transaction_id: 事务ID

        返回:
            True=全部同意，可以提交；False=有拒绝，需要回滚
        """
        if transaction_id not in self.votes:
            raise ValueError(f"事务 {transaction_id} 的投票不存在")

        votes = self.votes[transaction_id]
        all_yes = all(v.vote for v in votes)
        return all_yes

    def send_decision(self, transaction_id: str) -> str:
        """
        向所有参与者发送最终决策

        参数:
            transaction_id: 事务ID

        返回:
            决策结果："commit" 或 "abort"
        """
        can_commit = self.collect_votes(transaction_id)
        decision = "commit" if can_commit else "abort"

        ctx = self.transactions[transaction_id]
        decision_msg = DecisionMessage(
            transaction_id=transaction_id,
            decision=decision,
            timestamp=time.time()
        )

        print(f"[协调者 {self.coordinator_id}] 决策: {decision.upper()}")
        print(f"[协调者 {self.coordinator_id}] 发送 {decision.upper()} 到 {ctx.participants}")

        # 通知所有参与者
        for participant_id in ctx.participants:
            self._participant_receive_decision(participant_id, decision_msg)

        return decision

    def _participant_receive_decision(self, participant_id: str, msg: DecisionMessage):
        """模拟参与者接收决策消息"""
        if participant_id in self.participant_states:
            state = self.participant_states[participant_id].get(msg.transaction_id)
            if state == ParticipantState.PREPARED:
                if msg.decision == "commit":
                    self.participant_states[participant_id][msg.transaction_id] = ParticipantState.COMMITTED
                    print(f"  参与者 {participant_id} 提交本地事务")
                else:
                    self.participant_states[participant_id][msg.transaction_id] = ParticipantState.ABORTED
                    print(f"  参与者 {participant_id} 回滚本地事务")

    def execute_transaction(self, transaction_id: str, participant_ids: List[str]) -> str:
        """
        执行完整的两阶段提交

        参数:
            transaction_id: 事务ID
            participant_ids: 参与者ID列表

        返回:
            事务结果："committed" 或 "aborted"
        """
        print(f"\n{'=' * 50}")
        print(f"开始执行事务 {transaction_id}")
        print(f"{'=' * 50}")

        # 阶段1：开始事务并发送 Prepare
        self.begin_transaction(transaction_id, participant_ids)
        self.send_prepare(transaction_id)

        # 阶段2：收集投票并发送决策
        result = self.send_decision(transaction_id)

        print(f"\n事务 {transaction_id} 结果: {result.upper()}")
        return result


# =============================================================================
# 三阶段提交（3PC）实现
# =============================================================================

class ThreePhaseCommit:
    """
    三阶段提交协议（3PC）
    ======================

    改进点：解决了2PC的协调者单点故障时的阻塞问题

    阶段1（CanCommit）：
        协调者询问所有参与者是否可以提交（不执行）
        参与者返回 Yes/No

    阶段2（PreCommit）：
        如果全部 Yes，协调者发送 PreCommit
        参与者锁定资源并返回 Ack

    阶段3（DoCommit）：
        协调者发送 DoCommit，参与者真正提交
        如果有任何超时或异常，参与者自行提交（基于 PreCommit 的承诺）
    """

    def __init__(self, coordinator_id: str):
        self.coordinator_id = coordinator_id
        self.transactions: Dict[str, TransactionContext] = {}
        self.can_commit_responses: Dict[str, List[bool]] = {}

    def phase1_can_commit(self, transaction_id: str, participant_ids: List[str]) -> bool:
        """
        阶段1：CanCommit 询问

        返回:
            True=所有参与者都可以提交
        """
        print(f"[3PC] 阶段1: 发送 CanCommit 询问")
        responses = []
        for pid in participant_ids:
            # 模拟参与者响应：95%可以，5%不可以
            can = random.random() > 0.05
            responses.append(can)
            print(f"  参与者 {pid}: {'Yes' if can else 'No'}")

        self.can_commit_responses[transaction_id] = responses
        return all(responses)

    def phase2_precommit(self, transaction_id: str, participant_ids: List[str]) -> bool:
        """
        阶段2：PreCommit

        返回:
            True=所有参与者确认 PreCommit
        """
        print(f"[3PC] 阶段2: 发送 PreCommit")

        # 在真实系统中，参与者会在此阶段锁定资源
        # 这里模拟所有都成功
        return True

    def phase3_docommit(self, transaction_id: str, participant_ids: List[str]):
        """阶段3：DoCommit，执行真正的提交"""
        print(f"[3PC] 阶段3: 发送 DoCommit")
        for pid in participant_ids:
            print(f"  参与者 {pid} 提交事务")

    def execute(self, transaction_id: str, participant_ids: List[str]) -> str:
        """执行完整的三阶段提交"""
        print(f"\n{'=' * 50}")
        print(f"[3PC] 开始执行事务 {transaction_id}")
        print(f"{'=' * 50}")

        # 阶段1
        if not self.phase1_can_commit(transaction_id, participant_ids):
            print(f"[3PC] 事务 {transaction_id} 被中止（有参与者无法提交）")
            return "aborted"

        # 阶段2
        if not self.phase2_precommit(transaction_id, participant_ids):
            print(f"[3PC] 事务 {transaction_id} PreCommit 失败")
            return "aborted"

        # 阶段3
        self.phase3_docommit(transaction_id, participant_ids)
        return "committed"


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("分布式事务协议测试")
    print("=" * 60)

    # 测试1：两阶段提交
    print("\n【测试1：两阶段提交（2PC）】")
    coordinator = TwoPhaseCommit("coordinator_1")
    result = coordinator.execute_transaction(
        transaction_id="tx_001",
        participant_ids=["node_A", "node_B", "node_C"]
    )
    print(f"最终结果: {result}")

    # 测试2：三阶段提交
    print("\n【测试2：三阶段提交（3PC）】")
    coordinator_3pc = ThreePhaseCommit("coordinator_1")
    result = coordinator_3pc.execute(
        transaction_id="tx_002",
        participant_ids=["node_A", "node_B", "node_C"]
    )
    print(f"最终结果: {result}")

    # 测试3：2PC 回滚场景
    print("\n【测试3：2PC 回滚场景（模拟有参与者拒绝）】")
    print("（多次运行以观察不同结果）")
    for i in range(3):
        coord = TwoPhaseCommit(f"coord_{i}")
        coord.execute_transaction(f"tx_test_{i}", ["node_A", "node_B"])
        time.sleep(0.1)

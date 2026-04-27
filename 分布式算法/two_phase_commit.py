# -*- coding: utf-8 -*-

"""

算法实现：分布式算法 / two_phase_commit



本文件实现 two_phase_commit 相关的算法功能。

"""



from typing import List, Optional, Dict, Any

from enum import Enum





class Vote(Enum):

    """参与者投票结果"""

    YES = "YES"   # 可以提交

    NO = "NO"    # 必须中止





class Coordinator:

    """事务协调者（Transaction Coordinator）"""

    def __init__(self, transaction_id: str):

        self.transaction_id = transaction_id          # 事务唯一标识

        self.participants: List["Participant"] = []   # 参与者列表

        self.state: str = "INIT"                     # 协调者状态

        self.votes: Dict[str, Vote] = {}              # 收集的投票



    def add_participant(self, participant: "Participant") -> None:

        """注册参与者"""

        self.participants.append(participant)



    def phase1_prepare(self) -> bool:

        """

        Phase 1：准备阶段

        向所有参与者发送 VOTE_REQUEST，等待 YES/NO 投票

        """

        self.state = "VOTING"

        self.votes = {}



        print(f"[{self.transaction_id}] Phase 1: 协调者发送 VOTE_REQUEST")

        for p in self.participants:

            vote = p.vote_request(self.transaction_id)

            self.votes[p.participant_id] = vote

            print(f"  参与者 {p.participant_id} 投票: {vote.value}")



        # 所有参与者都投 YES 才进入 Phase 2

        all_yes = all(v == Vote.YES for v in self.votes.values())

        return all_yes



    def phase2_commit(self) -> bool:

        """

        Phase 2：提交阶段

        若全部 YES，发送 COMMIT；若任何 NO，发送 ABORT

        """

        all_yes = all(v == Vote.YES for v in self.votes.values())



        if all_yes:

            print(f"[{self.transaction_id}] Phase 2: 协调者发送 COMMIT")

            self.state = "COMMITTED"

            for p in self.participants:

                p.global_commit(self.transaction_id)

            return True

        else:

            print(f"[{self.transaction_id}] Phase 2: 协调者发送 ABORT")

            self.state = "ABORTED"

            for p in self.participants:

                p.global_abort(self.transaction_id)

            return False



    def run_2pc(self) -> bool:

        """执行完整的 2PC 流程"""

        if not self.phase1_prepare():

            self.phase2_commit()  # 触发 ABORT

            return False

        return self.phase2_commit()





class Participant:

    """事务参与者（Transaction Participant）"""

    def __init__(self, participant_id: str):

        self.participant_id = participant_id         # 参与者唯一标识

        self.state: str = "INIT"                     # 参与者状态

        self.can_commit: bool = False                # 是否可以提交



    def vote_request(self, transaction_id: str) -> Vote:

        """

        处理协调者的投票请求

        模拟：若本地资源准备就绪则投 YES，否则投 NO

        """

        # 模拟：90%概率可以提交

        import random

        self.can_commit = random.random() > 0.1

        self.state = "VOTING"

        return Vote.YES if self.can_commit else Vote.NO



    def global_commit(self, transaction_id: str) -> None:

        """收到全局 COMMIT：提交本地事务"""

        if self.state == "COMMITTED":

            return  # 防止重复提交

        self.state = "COMMITTED"

        print(f"  参与者 {self.participant_id}: 本地事务已提交")



    def global_abort(self, transaction_id: str) -> None:

        """收到全局 ABORT：回滚本地事务"""

        self.state = "ABORTED"

        print(f"  参与者 {self.participant_id}: 本地事务已回滚")





# ============================ 测试代码 ============================

if __name__ == "__main__":

    # 创建协调者

    coordinator = Coordinator("TX-001")



    # 创建多个参与者

    participants = [Participant(f"P{i}") for i in range(3)]

    for p in participants:

        coordinator.add_participant(p)



    # 手动设置部分参与者可提交（模拟确定性测试）

    # 重新创建以确保测试稳定

    coordinator2 = Coordinator("TX-002")

    participants2 = []

    for i in range(3):

        p = Participant(f"P{i}_2")

        p.can_commit = True  # 强制全部可提交

        p.state = "INIT"

        participants2.append(p)

        coordinator2.add_participant(p)



    print("=== 测试场景：全部 YES ===")

    success = coordinator2.run_2pc()

    print(f"事务结果: {'提交成功' if success else '已回滚'}")



    # 验证所有参与者状态一致

    committed = all(p.state == "COMMITTED" for p in participants2)

    print(f"所有参与者一致性: {'✅' if committed else '❌'}")



    print("\n=== 测试场景：部分 NO ===")

    coordinator3 = Coordinator("TX-003")

    participants3 = []

    for i in range(3):

        p = Participant(f"P{i}_3")

        p.can_commit = (i != 1)  # P1_3 不可提交

        participants3.append(p)

        coordinator3.add_participant(p)



    success3 = coordinator3.run_2pc()

    print(f"事务结果: {'提交成功' if success3 else '已回滚'}")



    aborted = all(p.state == "ABORTED" for p in participants3)

    print(f"所有参与者一致性: {'✅' if aborted else '❌'}")



    # 时间复杂度：O(N) — 2 轮通信（VOTE_REQUEST + COMMIT/ABORT）

    # 空间复杂度：O(N) — 协调者存储参与者投票状态


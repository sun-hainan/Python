# -*- coding: utf-8 -*-

"""

算法实现：分布式算法 / vector_clocks



本文件实现 vector_clocks 相关的算法功能。

"""



from typing import Dict, List, Tuple





class VectorClock:

    """向量时钟"""

    def __init__(self, node_ids: List[str]):

        # 初始化：每个节点的分量从 0 开始

        self.clock: Dict[str, int] = {node_id: 0 for node_id in node_ids}

        self.node_ids = node_ids



    def increment(self, node_id: str) -> None:

        """节点 node_id 发生一个事件，本地计数器 +1"""

        if node_id not in self.clock:

            raise ValueError(f"Unknown node: {node_id}")

        self.clock[node_id] += 1



    def get(self, node_id: str) -> int:

        """获取指定节点的逻辑时钟值"""

        return self.clock.get(node_id, 0)



    def merge(self, other: "VectorClock") -> None:

        """

        与另一个向量时钟合并（取 max）

        用于：收到远程消息时，更新本地对其他节点的认知

        """

        for node_id in self.node_ids:

            self.clock[node_id] = max(self.clock[node_id], other.clock[node_id])



    def update_on_send(self, node_id: str) -> None:

        """节点 node_id 发送消息时：先递增本地分量"""

        self.increment(node_id)



    def update_on_receive(self, node_id: str, received_clock: Dict[str, int]) -> None:

        """

        节点 node_id 收到消息时：

        1. 递增本地分量

        2. 与收到的向量合并（取 max）

        """

        self.increment(node_id)

        for nid, val in received_clock.items():

            if nid in self.clock:

                self.clock[nid] = max(self.clock[nid], val)



    @staticmethod

    def compare(vc1: Dict[str, int], vc2: Dict[str, int]) -> Tuple[bool, bool]:

        """

        比较两个向量时钟的因果关系

        返回：(vc1 <= vc2, vc2 <= vc1)

        - (True, False)  => vc1 < vc2（vc1 在 vc2 之前）

        - (False, True)  => vc2 < vc1（vc2 在 vc1 之前）

        - (False, False)  => 并发（不可比较）

        - (True, True)    => 相等

        """

        leq_1_2 = all(vc1[n] <= vc2[n] for n in vc1)

        leq_2_1 = all(vc2[n] <= vc1[n] for n in vc1)

        return leq_1_2, leq_2_1



    def is_concurrent_with(self, other: "VectorClock") -> bool:

        """判断是否与另一个向量时钟并发（无因果顺序）"""

        leq_1_2, leq_2_1 = self.compare(self.clock, other.clock)

        return not (leq_1_2 or leq_2_1)



    def __repr__(self) -> str:

        return f"VC({self.clock})"





class Process:

    """模拟分布式进程"""

    def __init__(self, process_id: str, all_process_ids: List[str]):

        self.process_id = process_id

        self.vector_clock = VectorClock(all_process_ids)

        self.event_history: List[Dict] = []  # 事件历史（用于调试/验证）



    def local_event(self, event_name: str) -> None:

        """本地事件：节点内部发生的事件（如计算）"""

        self.vector_clock.update_on_send(self.process_id)

        self.event_history.append({

            "type": "LOCAL",

            "name": event_name,

            "clock": dict(self.vector_clock.clock)

        })



    def send_message(self, target: "Process", message: str) -> None:

        """发送消息：更新本地时钟 + 发送带时间戳的消息"""

        self.vector_clock.update_on_send(self.process_id)

        event = {

            "type": "SEND",

            "name": message,

            "clock": dict(self.vector_clock.clock)

        }

        self.event_history.append(event)

        # 返回带时间戳的消息

        return {"content": message, "clock": dict(self.vector_clock.clock)}



    def receive_message(self, received: dict) -> None:

        """接收消息：合并远程向量时钟"""

        self.vector_clock.update_on_receive(self.process_id, received["clock"])

        self.event_history.append({

            "type": "RECEIVE",

            "name": received["content"],

            "clock": dict(self.vector_clock.clock)

        })





# ============================ 测试代码 ============================

if __name__ == "__main__":

    # 模拟 3 个进程：A, B, C

    process_ids = ["A", "B", "C"]

    proc_a = Process("A", process_ids)

    proc_b = Process("B", process_ids)

    proc_c = Process("C", process_ids)



    print("=== 向量时钟演示 ===")

    # 事件序列：

    # 1. A 本地计算

    proc_a.local_event("compute_1")

    print(f"A 本地事件后: {proc_a.vector_clock}")



    # 2. A 发送消息给 B

    msg = proc_a.send_message(proc_b, "result_from_A")

    print(f"A 发送消息后: {proc_a.vector_clock}")



    # 3. B 收到消息

    proc_b.receive_message(msg)

    print(f"B 收到消息后: {proc_b.vector_clock}")



    # 4. B 本地事件

    proc_b.local_event("compute_2")

    print(f"B 本地事件后: {proc_b.vector_clock}")



    # 5. B 发送消息给 C

    msg2 = proc_b.send_message(proc_c, "result_from_B")

    print(f"B 发送消息后: {proc_b.vector_clock}")



    # 6. C 收到消息

    proc_c.receive_message(msg2)

    print(f"C 收到消息后: {proc_c.vector_clock}")



    # 因果顺序验证

    print("\n=== 因果顺序验证 ===")

    # A 的初始事件 早于 B 收到消息

    leq_a_b, leq_b_a = VectorClock.compare(proc_a.event_history[0]["clock"],

                                           proc_b.event_history[0]["clock"])

    print(f"A_event1 <= B_received_A: {leq_a_b} (应该是 True)")

    assert leq_a_b, "A 的事件应该在 B 收到消息之前（因果）"



    # C 收到消息 晚于 B 发送

    leq_b_c, leq_c_b = VectorClock.compare(

        proc_b.event_history[2]["clock"],  # B 发送

        proc_c.event_history[0]["clock"]   # C 接收

    )

    print(f"B_send <= C_received: {leq_b_c} (应该是 True)")

    assert leq_b_c, "B 的发送应该在 C 收到消息之前（因果）"



    print("✅ 向量时钟因果顺序验证通过！")

    print(f"A 初始时钟: {proc_a.vector_clock.clock}")

    print(f"C 最终时钟: {proc_c.vector_clock.clock}")



    # 时间复杂度：O(N) — 比较或合并

    # 空间复杂度：O(N) — 每个进程存储长度为 N 的向量


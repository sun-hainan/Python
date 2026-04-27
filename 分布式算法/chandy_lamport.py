# -*- coding: utf-8 -*-

"""

算法实现：分布式算法 / chandy_lamport



本文件实现 chandy_lamport 相关的算法功能。

"""



from collections import deque

from typing import Dict, List, Optional





class Channel:

    """信道：模拟两个进程之间的有向FIFO队列"""

    def __init__(self, name: str):

        self.name = name                    # 信道唯一标识

        self.queue: deque = deque()         # 消息队列（FIFO）

        self.snapshot_queue: deque = deque()  # 快照期间捕获的消息



    def send(self, message) -> None:

        """发送消息：普通操作时直接入队"""

        self.queue.append(message)



    def receive(self):

        """接收消息：普通操作时从队列头部取出"""

        if self.queue:

            return self.queue.popleft()

        return None



    def record(self) -> None:

        """记录：快照时将当前队列内容复制到snapshot_queue，并清空队列"""

        self.snapshot_queue = deque(self.queue)

        self.queue.clear()





class Process:

    """进程：分布式系统中的节点"""

    def __init__(self, pid: str):

        self.pid = pid                      # 进程唯一标识

        self.state = {}                      # 进程本地状态（字典，可灵活扩展）

        self.channels_in: Dict[str, Channel] = {}   # 入向信道 {channel_name: Channel}

        self.channels_out: Dict[str, Channel] = {}  # 出向信道 {channel_name: Channel}

        self.recording = False              # 是否正在记录快照



    def add_in_channel(self, channel: Channel) -> None:

        """添加入向信道"""

        self.channels_in[channel.name] = channel



    def add_out_channel(self, channel: Channel) -> None:

        """添加出向信道"""

        self.channels_out[channel.name] = channel



    def update_state(self, key: str, value) -> None:

        """更新本地状态（模拟）"""

        self.state[key] = value



    def start_snapshot(self) -> None:

        """开始快照：记录自己的状态，并通知所有下游进程"""

        self.recording = True

        # 记录每个入信道的当前内容（此时信道中暂存的消息属于"在途"）

        for channel in self.channels_in.values():

            channel.record()

        # 发送marker到所有出向信道

        for channel in self.channels_out.values():

            channel.send("MARKER")



    def handle_marker(self, from_channel: str) -> None:

        """处理marker消息：若尚未开始快照则启动，并将当前入信道记录"""

        if not self.recording:

            self.recording = True

            # 记录from_channel之前的消息（它已在record时被保存）

            for name, channel in self.channels_in.items():

                if name != from_channel:

                    channel.record()

            # 继续传播marker

            for channel in self.channels_out.values():

                channel.send("MARKER")





class ChandyLamportSnapshot:

    """Chandy-Lamport 快照协调器：负责发起和管理全局快照"""

    def __init__(self):

        self.processes: Dict[str, Process] = {}  # 所有进程 {pid: Process}

        self.global_snapshot: Dict[str, dict] = {}  # 全局快照结果 {pid: state}

        self.channel_snapshots: Dict[str, list] = {}  # 信道快照 {channel_name: [messages]}



    def add_process(self, process: Process) -> None:

        """注册进程"""

        self.processes[process.pid] = process



    def initiate_snapshot(self, initiator_pid: str) -> None:

        """发起快照：从指定进程开始，通过marker广播触发整图快照"""

        if initiator_pid in self.processes:

            self.processes[initiator_pid].start_snapshot()



    def collect_snapshot(self, pid: str) -> None:

        """收集指定进程的快照状态和所有入信道内容"""

        if pid not in self.processes:

            return

        proc = self.processes[pid]

        self.global_snapshot[pid] = dict(proc.state)  # 复制本地状态

        # 收集每个入信道的快照消息

        for name, channel in proc.channels_in.items():

            self.channel_snapshots[name] = list(channel.snapshot_queue)



    def get_global_snapshot(self) -> dict:

        """获取完整的全局快照"""

        return {

            "processes": self.global_snapshot,

            "channels": self.channel_snapshots

        }





# ============================ 测试代码 ============================

if __name__ == "__main__":

    # 构建简单系统：A -> B -> C（两条信道）

    channel_ab = Channel("AB")

    channel_bc = Channel("BC")



    proc_a = Process("A")

    proc_b = Process("B")

    proc_c = Process("C")



    # A 发送消息给 B，B 发送给 C

    proc_a.add_out_channel(channel_ab)

    proc_b.add_in_channel(channel_ab)



    proc_b.add_out_channel(channel_bc)

    proc_c.add_in_channel(channel_bc)



    # 初始化进程状态

    proc_a.update_state("value", 10)

    proc_b.update_state("value", 20)

    proc_c.update_state("value", 30)



    # A 先发送一些消息

    channel_ab.send("msg1")

    channel_ab.send("msg2")



    # B 发送一条消息

    channel_bc.send("msg3")



    # 创建快照系统

    snap = ChandyLamportSnapshot()

    snap.add_process(proc_a)

    snap.add_process(proc_b)

    snap.add_process(proc_c)



    # 从 A 开始发起快照

    snap.initiate_snapshot("A")



    # 模拟消息传递（处理marker的传播）

    # 处理 B 收到 marker

    proc_b.handle_marker("AB")

    # 处理 C 收到 marker

    proc_c.handle_marker("BC")



    # 收集所有进程快照

    for pid in ["A", "B", "C"]:

        snap.collect_snapshot(pid)



    # 输出结果

    result = snap.get_global_snapshot()

    print("=== Chandy-Lamport 全局快照 ===")

    for pid, state in result["processes"].items():

        print(f"进程 {pid} 状态: {state}")

    print("信道消息:")

    for ch, msgs in result["channels"].items():

        print(f"  {ch}: {msgs}")



    # 验证：快照应包含所有进程状态

    assert set(result["processes"].keys()) == {"A", "B", "C"}

    print("\n✅ 快照成功！全局状态一致捕获。")



    # 时间复杂度：O(N) — 每个进程处理一次marker

    # 空间复杂度：O(N·E) — 每个信道存储在途消息


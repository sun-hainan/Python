# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / process_state_machine



本文件实现 process_state_machine 相关的算法功能。

"""



from enum import Enum, auto

from dataclasses import dataclass, field

from typing import Optional, Callable

import time





class ProcessState(Enum):

    """进程状态枚举（标准POSIX状态）"""

    NEW = auto()           # 创建中

    READY = auto()         # 就绪（等待CPU）

    RUNNING = auto()       # 运行中

    BLOCKED = auto()       # 阻塞（等待I/O/事件）

    SUSPENDED = auto()     # 挂起（换出到磁盘）

    TERMINATED = auto()    # 终止

    ZOMBIE = auto()        # 僵尸（父未回收）





@dataclass

class StateTransition:

    """状态转换记录"""

    timestamp: float

    from_state: ProcessState

    to_state: ProcessState

    reason: str

    pid: int





class ProcessControlBlock:

    """进程控制块（PCB）"""



    pid_counter = 1  # 全局PID分配器



    def __init__(self, name: str = ""):

        self.pid = ProcessControlBlock.pid_counter

        ProcessControlBlock.pid_counter += 1



        self.name = name or f"Process-{self.pid}"

        self.state = ProcessState.NEW

        self.parent_pid: Optional[int] = None

        self.children: list[int] = []



        self.program_counter: int = 0

        self.cpu_registers: dict[str, int] = {}

        self.memory_info: dict = {}



        self.priority: int = 0  # 调度优先级

        self.nice_value: int = 0



        self.state_history: list[StateTransition] = []

        self.creation_time: float = time.time()

        self.cpu_time_used: float = 0.0

        self.start_time: Optional[float] = None



    def transition_to(self, new_state: ProcessState, reason: str = ""):

        """状态转换"""

        ts = time.time()

        trans = StateTransition(

            timestamp=ts,

            from_state=self.state,

            to_state=new_state,

            reason=reason,

            pid=self.pid

        )

        self.state_history.append(trans)

        self.state = new_state



        if new_state == ProcessState.RUNNING and self.start_time is None:

            self.start_time = ts



    def block(self, reason: str = "I/O wait"):

        """阻塞当前进程"""

        if self.state == ProcessState.RUNNING:

            self.transition_to(ProcessState.BLOCKED, reason)



    def unblock(self, reason: str = "I/O complete"):

        """解除阻塞"""

        if self.state == ProcessState.BLOCKED:

            self.transition_to(ProcessState.READY, reason)



    def terminate(self):

        """终止进程"""

        self.transition_to(ProcessState.TERMINATED, "exit syscall")



    def zombie(self):

        """转为僵尸状态"""

        self.transition_to(ProcessState.ZOMBIE, "parent not waiting")





class ProcessStateMachine:

    """

    进程状态机模拟器

    管理一组进程的状态转换

    """



    def __init__(self):

        self.processes: dict[int, ProcessControlBlock] = {}

        self.ready_queue: list[int] = []      # READY状态进程

        self.blocked_queue: list[int] = []    # BLOCKED状态进程

        self.running: Optional[int] = None     # 当前运行进程PID



    def create_process(self, name: str = "", parent: Optional[int] = None) -> ProcessControlBlock:

        """创建新进程（fork）"""

        pcb = ProcessControlBlock(name)

        pcb.parent_pid = parent

        pcb.transition_to(ProcessState.READY, "fork")



        self.processes[pcb.pid] = pcb

        self.ready_queue.append(pcb.pid)



        if parent and parent in self.processes:

            self.processes[parent].children.append(pcb.pid)



        return pcb



    def schedule(self) -> Optional[int]:

        """

        调度决策：选择下一个运行的进程

        简化策略：FIFO就绪队列

        """

        if not self.ready_queue:

            return None



        if self.running is not None:

            # 抢占当前进程（简化：每个时间片后重调度）

            running_pcb = self.processes[self.running]

            if running_pcb.state == ProcessState.RUNNING:

                running_pcb.transition_to(ProcessState.READY, "preempt")

                self.ready_queue.append(self.running)



        next_pid = self.ready_queue.pop(0)

        self.running = next_pid



        pcb = self.processes[next_pid]

        pcb.transition_to(ProcessState.RUNNING, "scheduled")

        return next_pid



    def block_running(self, reason: str):

        """阻塞当前运行进程"""

        if self.running is not None:

            pcb = self.processes[self.running]

            pcb.block(reason)

            self.blocked_queue.append(self.running)

            self.running = None



    def unblock_one(self) -> Optional[int]:

        """唤醒一个阻塞进程"""

        if not self.blocked_queue:

            return None



        pid = self.blocked_queue.pop(0)

        pcb = self.processes[pid]

        pcb.unblock("I/O complete")

        self.ready_queue.append(pid)

        return pid



    def terminate_pid(self, pid: int):

        """终止指定进程"""

        if pid in self.processes:

            pcb = self.processes[pid]

            pcb.terminate()

            if self.running == pid:

                self.running = None



    def wait_on_child(self, pid: int) -> Optional[int]:

        """

        父进程等待子进程（wait）

        返回已终止子进程的PID，若无则阻塞

        """

        for child_pid in self.processes[pid].children:

            child = self.processes[child_pid]

            if child.state == ProcessState.ZOMBIE:

                # 回收僵尸进程

                child.transition_to(ProcessState.TERMINATED, "wait collected")

                return child_pid



        # 无僵尸子进程，父进程阻塞

        return None



    def get_state_summary(self) -> dict[ProcessState, int]:

        """获取各状态进程数统计"""

        summary = {state: 0 for state in ProcessState}

        for pcb in self.processes.values():

            summary[pcb.state] += 1

        return summary





if __name__ == "__main__":

    print("=== 进程状态机模拟 ===")



    sm = ProcessStateMachine()



    # 创建进程树

    p1 = sm.create_process("init")

    p2 = sm.create_process("bash", parent=p1.pid)

    p3 = sm.create_process("python", parent=p2.pid)



    print(f"创建进程: P{p1.pid}({p1.name}), P{p2.pid}({p2.name}), P{p3.pid}({p3.name})")

    print(f"状态: {sm.get_state_summary()}")



    # 调度运行

    print("\n--- 调度循环 ---")

    for i in range(5):

        next_pid = sm.schedule()

        if next_pid:

            print(f"调度: P{next_pid} 进入 RUNNING")

        else:

            print("无就绪进程")



        if i == 1:

            # 模拟I/O阻塞

            print(f"  -> P{next_pid} 阻塞（I/O）")

            sm.block_running("I/O wait")

            sm.unblock_one()  # 假设I/O完成



    # 终止子进程

    print("\n--- 终止进程 ---")

    sm.terminate_pid(p3.pid)

    p3_zombie = sm.processes[p3.pid]

    p3_zombie.zombie()

    print(f"P{p3.pid} 进入 ZOMBIE")



    # 父进程回收

    ret = sm.wait_on_child(p2.pid)

    print(f"父进程P{p2.pid}回收了P{ret}")



    # 最终状态

    print(f"\n最终状态: {sm.get_state_summary()}")

    print("状态历史:")

    for pid, pcb in sm.processes.items():

        print(f"  P{pid}:")

        for trans in pcb.state_history:

            print(f"    {trans.from_state.name} -> {trans.to_state.name} ({trans.reason})")


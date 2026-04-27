# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / context_switch



本文件实现 context_switch 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass, field

import time





@dataclass

class CPUContext:

    """CPU上下文（保存到进程结构）"""

    # 通用寄存器

    eax: int = 0

    ebx: int = 0

    ecx: int = 0

    edx: int = 0

    esi: int = 0

    edi: int = 0

    ebp: int = 0

    esp: int = 0  # 栈指针



    # 特殊寄存器

    eip: int = 0   # 程序计数器

    eflags: int = 0



    # 段寄存器

    cs: int = 0

    ds: int = 0

    es: int = 0

    fs: int = 0

    gs: int = 0

    ss: int = 0



    # FPU/AVX状态（简化）

    fpu_state: bytes = field(default_factory=lambda: b'\x00' * 512)





class ProcessControlBlock:

    """进程控制块 (PCB)"""



    def __init__(self, pid: int, name: str):

        self.pid = pid

        self.name = name



        # 调度信息

        self.state: str = "RUNNING"  # RUNNING, READY, BLOCKED, ZOMBIE

        self.priority: int = 0

        self.nice: int = 0

        self.time_slice: int = 0

        self.remaining_slice: int = 0



        # 上下文

        self.ctx: CPUContext = CPUContext()



        # 内存信息

        self.cr3: int = 0  # 页表基址

        self.vm_area: List['VMArea'] = []



        # 统计

        self.utime: int = 0  # 用户态时间

        self.stime: int = 0  # 内核态时间

        self.start_time: int = int(time.time())

        self.total_time: int = 0



        # 父子关系

        self.parent: Optional['ProcessControlBlock'] = None

        self.children: List['ProcessControlBlock'] = []



        # 文件描述符表

        self.files: Dict[int, any] = {0: None, 1: None, 2: None}



        # 信号处理

        self.pending_signals: Set[int] = set()



    def save_context(self, ctx: CPUContext):

        """保存当前CPU上下文到PCB"""

        self.ctx = ctx

        self.state = "READY"



    def restore_context(self) -> CPUContext:

        """从PCB恢复上下文"""

        self.state = "RUNNING"

        return self.ctx



    def switch_to(self):

        """切换到该进程"""

        self.state = "RUNNING"



    def switch_away(self):

        """从该进程切换走"""

        self.state = "READY"





class Scheduler:

    """调度器"""



    def __init__(self):

        # 运行队列

        self.running: List[ProcessControlBlock] = []

        self.ready: List[ProcessControlBlock] = []

        self.blocked: List[ProcessControlBlock] = []

        self.zombies: List[ProcessControlBlock] = []



        # 当前运行的进程

        self.current: Optional[ProcessControlBlock] = None



        # 统计

        self.context_switches = 0

        self.cpu_time = 0



    def add_process(self, process: ProcessControlBlock):

        """添加进程"""

        self.ready.append(process)



    def enqueue(self, process: ProcessControlBlock):

        """入队"""

        if process.state == "RUNNING":

            self.running.append(process)

        elif process.state == "READY":

            self.ready.append(process)

        elif process.state == "BLOCKED":

            self.blocked.append(process)



    def dequeue(self, process: ProcessControlBlock):

        """出队"""

        for queue in [self.running, self.ready, self.blocked]:

            if process in queue:

                queue.remove(process)

                break



    def schedule(self) -> Optional[ProcessControlBlock]:

        """

        选择下一个要运行的进程

        简单的轮转调度

        """

        if self.ready:

            # 简单的轮转

            next_process = self.ready.pop(0)

            return next_process

        return None



    def context_switch(self, from_proc: ProcessControlBlock, to_proc: ProcessControlBlock):

        """

        执行上下文切换

        """

        print(f"  [调度] 切换: {from_proc.name} -> {to_proc.name}")



        # 1. 保存当前进程上下文

        # 在实际CPU上，这是硬件自动完成的

        from_proc.save_context(CPUContext())



        # 2. 更新运行队列

        self.dequeue(from_proc)

        self.enqueue(from_proc)



        # 3. 恢复新进程上下文

        to_proc.restore_context()



        # 4. 更新当前进程

        self.current = to_proc



        self.context_switches += 1



        print(f"  [调度] 当前: {to_proc.name} (PID={to_proc.pid})")





class ContextSwitchSimulator:

    """上下文切换模拟器"""



    def __init__(self):

        self.scheduler = Scheduler()

        self.current_pid = 0



    def create_process(self, name: str, priority: int = 0) -> ProcessControlBlock:

        """创建进程"""

        self.current_pid += 1

        proc = ProcessControlBlock(self.current_pid, name)

        proc.priority = priority

        proc.cr3 = 0x1000 + self.current_pid * 0x1000  # 模拟页表地址

        return proc



    def run(self, num_slices: int = 5):

        """运行调度模拟"""

        print("=" * 60)

        print("进程调度上下文切换")

        print("=" * 60)



        # 创建进程

        proc1 = self.create_process("init", priority=0)

        proc2 = self.create_process("bash", priority=0)

        proc3 = self.create_process("vim", priority=-5)  # 高优先级

        proc4 = self.create_process("make", priority=5)   # 低优先级



        # 设置时间片

        for proc in [proc1, proc2, proc3, proc4]:

            proc.time_slice = 10

            proc.remaining_slice = proc.time_slice



        # 添加到调度器

        for proc in [proc1, proc2, proc3, proc4]:

            self.scheduler.add_process(proc)



        print(f"\n已创建 {self.scheduler.ready.__len__()} 个进程:")

        for proc in self.scheduler.ready:

            print(f"  PID={proc.pid}: {proc.name} (priority={proc.priority})")



        # 运行调度

        print("\n" + "-" * 50)

        print("调度模拟")

        print("-" * 50)



        for slice_num in range(1, num_slices + 1):

            print(f"\n时间片 {slice_num}:")



            # 选择下一个进程

            next_proc = self.scheduler.schedule()

            if next_proc is None:

                print("  没有可运行进程")

                break



            # 获取当前进程

            current = self.scheduler.current



            if current:

                # 上下文切换

                self.scheduler.context_switch(current, next_proc)

            else:

                # 首次运行

                self.scheduler.current = next_proc

                next_proc.state = "RUNNING"

                print(f"  首次运行: {next_proc.name} (PID={next_proc.pid})")



            # 模拟执行

            next_proc.remaining_slice -= 1

            next_proc.utime += 1

            self.scheduler.cpu_time += 1



            # 时间片耗尽，切换

            if next_proc.remaining_slice <= 0:

                next_proc.remaining_slice = next_proc.time_slice

                # 当前进程放回ready队列

                next_proc.state = "READY"

                self.scheduler.ready.append(next_proc)



        # 显示统计

        print("\n" + "-" * 50)

        print("调度统计")

        print("-" * 50)



        all_procs = [proc1, proc2, proc3, proc4]

        for proc in all_procs:

            print(f"\n{proc.name} (PID={proc.pid}):")

            print(f"  用户态时间: {proc.utime}")

            print(f"  内核态时间: {proc.stime}")

            print(f"  总时间: {proc.utime + proc.stime}")



        print(f"\n上下文切换次数: {self.scheduler.context_switches}")

        print(f"总CPU时间: {self.scheduler.cpu_time}")



    def simulate_blocked_switch(self):

        """

        模拟阻塞导致的切换

        """

        print("\n" + "=" * 60)

        print("阻塞导致的上下文切换")

        print("=" * 60)



        proc1 = self.create_process("reader", priority=0)

        proc2 = self.create_process("writer", priority=0)



        proc1.state = "RUNNING"

        proc2.state = "READY"

        self.scheduler.current = proc1

        self.scheduler.ready.append(proc2)



        print(f"\n初始状态:")

        print(f"  运行: {proc1.name}")

        print(f"  就绪: {proc2.name}")



        # proc1执行时需要I/O

        print(f"\n{proc1.name} 执行时发生I/O请求，进入阻塞状态")

        proc1.state = "BLOCKED"

        self.scheduler.blocked.append(proc1)



        # 切换到proc2

        print(f"\n触发上下文切换:")

        self.scheduler.context_switch(proc1, proc2)



        print(f"\n切换后状态:")

        print(f"  运行: {self.scheduler.current.name if self.scheduler.current else 'None'}")

        print(f"  阻塞: {[p.name for p in self.scheduler.blocked]}")

        print(f"  就绪: {[p.name for p in self.scheduler.ready]}")



        # I/O完成，proc1唤醒

        print(f"\nI/O完成，唤醒 {proc1.name}")

        self.scheduler.blocked.remove(proc1)

        proc1.state = "READY"

        self.scheduler.ready.append(proc1)





if __name__ == "__main__":

    sim = ContextSwitchSimulator()

    sim.run(num_slices=8)

    sim.simulate_blocked_switch()


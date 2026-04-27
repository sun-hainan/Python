# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / mlfq_scheduler



本文件实现 mlfq_scheduler 相关的算法功能。

"""



from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

import time





@dataclass

class MLFQTask:

    """MLFQ任务"""

    pid: int

    name: str

    arrival_time: float

    burst_time: int  # CPU突发时间

    remaining_time: int

    priority: int = 0  # 0=最高, 4=最低

    state: str = "READY"



    # 调度统计

    wait_time: float = 0

    turnaround_time: float = 0

    first_run: float = -1





class MLFQScheduler:

    """

    多级反馈队列调度器



    参数：

    - num_queues: 队列数量

    - base_slice: 基础时间片

    """



    def __init__(self, num_queues: int = 5, base_slice: int = 10):

        self.num_queues = num_queues

        self.base_slice = base_slice



        # 队列：priority -> [tasks]

        self.queues: Dict[int, List[MLFQTask]] = {i: [] for i in range(num_queues)}



        # 所有任务

        self.tasks: Dict[int, MLFQTask] = {}



        # 当前时间

        self.current_time: float = 0



        # 统计

        self.context_switches = 0



    def _get_time_slice(self, priority: int) -> int:

        """获取时间片"""

        # 高优先级队列时间片短

        return self.base_slice * (2 ** priority)



    def add_task(self, pid: int, name: str, burst_time: int, priority: int = 0):

        """添加任务"""

        task = MLFQTask(

            pid=pid,

            name=name,

            arrival_time=self.current_time,

            burst_time=burst_time,

            remaining_time=burst_time

        )

        self.tasks[pid] = task

        self.queues[priority].append(task)



    def promote_task(self, task: MLFQTask):

        """提升任务优先级（当它被I/O阻塞后）"""

        if task.priority > 0:

            # 从当前队列移除

            self.queues[task.priority].remove(task)

            # 提升到高优先级队列

            task.priority -= 1

            self.queues[task.priority].append(task)



    def demote_task(self, task: MLFQTask):

        """降级任务（当时间片用完）"""

        if task.priority < self.num_queues - 1:

            self.queues[task.priority].remove(task)

            task.priority += 1

            self.queues[task.priority].append(task)



    def schedule(self) -> List[Tuple[str, float, int]]:

        """

        执行调度

        return: (task_name, start_time, duration)

        """

        schedule_log = []



        while self.tasks:

            # 找到最高优先级非空队列

            selected_task = None

            selected_priority = -1



            for p in range(self.num_queues):

                if self.queues[p]:

                    selected_task = self.queues[p][0]

                    selected_priority = p

                    break



            if selected_task is None:

                break



            # 获取时间片

            time_slice = self._get_time_slice(selected_priority)



            # 计算实际运行时间

            run_time = min(time_slice, selected_task.remaining_time)



            # 记录首次运行时间

            if selected_task.first_run < 0:

                selected_task.first_run = self.current_time



            # 模拟运行

            print(f"  时间 {self.current_time:.0f}-{self.current_time + run_time:.0f}: "

                  f"运行 {selected_task.name} (P={selected_priority}, 剩余={selected_task.remaining_time - run_time})")



            schedule_log.append((selected_task.name, self.current_time, run_time))



            # 更新时间

            self.current_time += run_time

            selected_task.remaining_time -= run_time

            self.context_switches += 1



            # 检查是否完成

            if selected_task.remaining_time <= 0:

                # 任务完成

                self.queues[selected_priority].remove(selected_task)

                selected_task.state = "COMPLETED"

                selected_task.turnaround_time = self.current_time - selected_task.arrival_time

                print(f"    完成! 周转时间={selected_task.turnaround_time:.0f}")

            else:

                # 时间片用完，降级

                print(f"    时间片用完，降级到队列{selected_priority + 1}")

                self.demote_task(selected_task)



        return schedule_log



    def simulate_io_block(self, pid: int, block_duration: int):

        """

        模拟I/O阻塞

        任务被I/O阻塞后会提升优先级

        """

        if pid in self.tasks:

            task = self.tasks[pid]

            print(f"  任务 {task.name} 被I/O阻塞 {block_duration}ms")

            task.state = "BLOCKED"



            # 模拟阻塞时间

            self.current_time += block_duration

            task.state = "READY"



            # 提升优先级（奖励I/O密集型任务）

            self.promote_task(task)





def simulate_mlfq():

    """

    模拟MLFQ调度器

    """

    print("=" * 60)

    print("多级反馈队列 (MLFQ) 调度")

    print("=" * 60)



    scheduler = MLFQScheduler(num_queues=5, base_slice=10)



    # 添加任务

    print("\n添加任务:")

    print("-" * 50)



    # 任务1: 短任务

    scheduler.add_task(1, "short_job", burst_time=20, priority=0)



    # 任务2: 长任务

    scheduler.add_task(2, "long_job", burst_time=100, priority=0)



    # 任务3: 中等任务

    scheduler.add_task(3, "medium_job", burst_time=50, priority=0)



    # 任务4: I/O密集型

    scheduler.add_task(4, "io_job", burst_time=30, priority=0)



    print(f"\n任务配置:")

    for pid, task in scheduler.tasks.items():

        print(f"  PID={pid}: {task.name}, burst={task.burst_time}ms")



    # 模拟I/O阻塞

    print("\n模拟I/O阻塞:")

    print("-" * 50)



    # 任务4运行一段时间后需要I/O

    print("\n任务4运行10ms后需要I/O:")

    scheduler.current_time = 10

    if 4 in scheduler.tasks:

        task4 = scheduler.tasks[4]

        task4.remaining_time = 20  # 已运行10ms

        scheduler.simulate_io_block(4, 5)



    # 执行调度

    print("\n调度过程:")

    print("-" * 50)



    scheduler.schedule()



    # 统计

    print("\n调度统计:")

    print("-" * 50)

    print(f"{'任务':<15} {'周转时间':<12} {'等待时间':<12}")

    print("-" * 40)



    for pid, task in scheduler.tasks.items():

        wait_time = task.turnaround_time - task.burst_time

        print(f"{task.name:<15} {task.turnaround_time:<12.0f} {wait_time:<12.0f}")



    # MLFQ特性总结

    print("\n" + "=" * 60)

    print("MLFQ 特点")

    print("=" * 60)

    print("""

    优点:

    - 自动适应长时间运行的任务

    - I/O密集型任务获得高优先级

    - 对交互任务响应快



    缺点:

    - 可能产生饥饿（长时间任务永远在低优先级）

    - 需要调优参数（队列数、时间片）

    - 实现复杂



    关键机制:

    1. 时间片用完 -> 降级到低优先级队列

    2. I/O阻塞 -> 提升到高优先级队列

    3. 高优先级队列时间片短，低优先级时间长

    """)





if __name__ == "__main__":

    simulate_mlfq()


# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / realtime_scheduler_detail



本文件实现 realtime_scheduler_detail 相关的算法功能。

"""



from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

from collections import deque

import time





@dataclass

class RTSchedTask:

    """实时调度任务"""

    pid: int

    name: str

    policy: str  # SCHED_FIFO or SCHED_RR

    priority: int  # 1-99 (RT priority)

    budget: int = 0  # RR时间片

    remaining: int = 0

    state: str = "READY"





class RTScheduler:

    """

    实时调度器



    特点：

    - 优先级范围 1-99 (越高越先)

    - SCHED_FIFO: 同优先级按FIFO，无时间片

    - SCHED_RR: 同优先级轮转，有时间片

    - 任何时刻只运行最高优先级任务

    """



    def __init__(self):

        # 按优先级组织的队列

        # priority -> deque of tasks

        self.queues: Dict[int, deque] = {i: deque() for i in range(1, 100)}

        self.tasks: Dict[int, RTSchedTask] = {}



        # 当前运行任务

        self.current: Optional[RTSchedTask] = None



        # 时间片配置

        self.time_slice_ms = 100



        # 统计

        self.context_switches = 0



    def add_task(self, pid: int, name: str, policy: str, priority: int, budget: int = 0):

        """添加实时任务"""

        task = RTSchedTask(

            pid=pid,

            name=name,

            policy=policy,

            priority=priority,

            budget=budget if policy == "SCHED_RR" else 0,

            remaining=budget if policy == "SCHED_RR" else 0

        )

        self.tasks[pid] = task

        self.queues[priority].append(task)



    def _find_highest_priority_task(self) -> Optional[RTSchedTask]:

        """找最高优先级任务"""

        for prio in range(99, 0, -1):

            if self.queues[prio]:

                return self.queues[prio][0]

        return None



    def schedule(self) -> List[Tuple[str, int, int]]:

        """

        执行调度

        return: (task_name, start_time, duration)

        """

        schedule_log = []

        current_time = 0



        while self.tasks:

            # 找最高优先级任务

            task = self._find_highest_priority_task()

            if task is None:

                break



            # 确定运行时间

            if task.policy == "SCHED_FIFO":

                # FIFO: 运行直到任务完成或主动让出

                duration = task.remaining if task.remaining > 0 else 10

            else:  # SCHED_RR

                duration = min(task.remaining, self.time_slice_ms)



            print(f"  时间 {current_time}-{current_time + duration}: "

                  f"运行 {task.name} (prio={task.priority}, policy={task.policy}, "

                  f"remaining={task.remaining - duration})")



            schedule_log.append((task.name, current_time, duration))

            current_time += duration

            self.context_switches += 1



            # 更新任务

            task.remaining -= duration



            # 检查是否完成

            if task.remaining <= 0:

                self.queues[task.priority].popleft()

                task.state = "DONE"

                del self.tasks[task.pid]

            else:

                # SCHED_RR: 时间片用完，移到队列末尾

                if task.policy == "SCHED_RR" and task.remaining <= 0:

                    self.queues[task.priority].rotate(-1)

                    task.remaining = self.time_slice_ms



        return schedule_log





def simulate_rt_scheduler():

    """

    模拟实时调度器

    """

    print("=" * 60)

    print("实时调度：SCHED_FIFO / SCHED_RR")

    print("=" * 60)



    scheduler = RTScheduler()



    # 添加实时任务

    print("\n添加实时任务:")

    print("-" * 50)



    # 高优先级FIFO任务

    scheduler.add_task(1, "RT_HIGH_FIFO", "SCHED_FIFO", priority=90, budget=0)



    # 中优先级RR任务

    scheduler.add_task(2, "RT_MID_RR", "SCHED_RR", priority=50, budget=50)



    # 低优先级FIFO任务

    scheduler.add_task(3, "RT_LOW_FIFO", "SCHED_FIFO", priority=10, budget=0)



    # 另一个中优先级RR

    scheduler.add_task(4, "RT_MID2_RR", "SCHED_RR", priority=50, budget=30)



    print("\n任务配置:")

    print(f"{'PID':<6} {'名称':<15} {'策略':<12} {'优先级':<10} {'预算':<8}")

    print("-" * 60)

    for pid, task in scheduler.tasks.items():

        print(f"{pid:<6} {task.name:<15} {task.policy:<12} {task.priority:<10} {task.budget:<8}")



    # 执行调度

    print("\n调度过程:")

    print("-" * 50)



    scheduler.schedule()



    # 实时调度特性

    print("\n" + "=" * 60)

    print("实时调度特性")

    print("=" * 60)

    print("""

    ┌──────────────┬────────────────────────────────────────┐

    │ 特性          │ 说明                                    │

    ├──────────────┼────────────────────────────────────────┤

    │ 优先级        │ 1-99，数字越大优先级越高               │

    │ 抢占          │ 高优先级任务立即抢占低优先级           │

    │ SCHED_FIFO   │ 无时间片，同优先级按FIFO               │

    │ SCHED_RR     │ 有时间片，同优先级轮转                 │

    │ 饥饿          │ 高优先级任务可能饿死低优先级           │

    └──────────────┴────────────────────────────────────────┘



    与CFS的区别:

    - CFS是公平调度，RT是优先级调度

    - RT没有vruntime概念

    - RT任务可以无限制运行（SCHED_FIFO）

    - CFS适合桌面，RT适合实时应用

    """)





if __name__ == "__main__":

    simulate_rt_scheduler()


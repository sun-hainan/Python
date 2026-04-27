# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / o1_scheduler



本文件实现 o1_scheduler 相关的算法功能。

"""



from typing import List, Dict, Optional

from dataclasses import dataclass

import sys





# 最大优先级

MAX_PRIO = 140

DEFAULT_PRIO = 120

NICE_TO_PRIO_OFFSET = 20





@dataclass

class Task_O1:

    """O(1)调度器中的任务"""

    pid: int

    name: str

    static_prio: int       # 静态优先级（120-nice）

    dynamic_prio: int      # 动态优先级

    priority: int          # 实际调度优先级

    time_slice: int        # 时间片

    first_time_slice: bool # 是否是第一个时间片



    # 队列链表

    run_list: 'list' = None

    queue_list: 'list' = None



    # 状态

    state: str = 'R'

    on_rq: bool = False





class PriorityArray:

    """

    优先级数组



    包含按优先级组织的所有可运行任务。

    使用位图快速找到最高优先级非空队列。

    """



    def __init__(self):

        # 优先级队列数组（每个优先级一个队列）

        self.queues: List[List[Task_O1]] = [[] for _ in range(MAX_PRIO)]



        # 位图：标记哪些优先级有任务

        # 每一位代表一个优先级

        self.bitmap: List[int] = [0] * 4  # 140位，4个64位整数



        # 最高和最低优先级

        self.highest_prio = 0

        self.lowest_prio = MAX_PRIO - 1



        # 任务数量

        self.nr_active = 0



    def _set_bit(self, prio: int):

        """设置位图中某位"""

            idx = prio // 64

            bit = prio % 64

            self.bitmap[idx] |= (1 << bit)



    def _clear_bit(self, prio: int):

        """清除位图中的位"""

        idx = prio // 64

            bit = prio % 64

            self.bitmap[idx] &= ~(1 << bit)

    

    def _is_bit_set(self, prio: int) -> bool:

        """检查位是否设置"""

        idx = prio // 64

        bit = prio % 64

        return (self.bitmap[idx] & (1 << bit)) != 0



    def _find_highest_bit(self) -> int:

        """找到最高位（最高优先级）"""

        for idx in range(len(self.bitmap) - 1, -1, -1):

            if self.bitmap[idx]:

                # 找到最左边第一个1

                bit = self.bitmap[idx].bit_length() - 1

                return idx * 64 + bit

        return -1  # 没有任务



    def enqueue_task(self, task: Task_O1):

        """将任务加入优先级队列"""

        prio = task.priority



        if task.on_rq:

            return  # 已经在队列中



        self.queues[prio].append(task)

        self._set_bit(prio)

        task.on_rq = True

        self.nr_active += 1



    def dequeue_task(self, task: Task_O1):

        """将任务从优先级队列移除"""

        prio = task.priority



        if not task.on_rq:

            return



        if task in self.queues[prio]:

            self.queues[prio].remove(task)



        if not self.queues[prio]:

            self._clear_bit(prio)



        task.on_rq = False

        self.nr_active -= 1



    def pick_next_task(self) -> Optional[Task_O1]:

        """选择下一个要运行的任务"""

        idx = self._find_highest_bit()

        if idx < 0:

            return None



        # 从该优先级的队列中选择任务（FIFO）

        queue = self.queues[idx]

        if queue:

            return queue[0]

        return None



    def requeue_task(self, task: Task_O1):

        """重新入队任务"""

        # 从当前位置移除，再加入队首

        prio = task.priority

        queue = self.queues[prio]

        if task in queue:

            queue.remove(task)

            queue.insert(0, task)





class Runqueue:

    """CPU运行队列"""



    def __init__(self, cpu_id: int):

        self.cpu_id = cpu_id

        self.active = PriorityArray()

        self.expired = PriorityArray()



        # 当前运行任务

        self.curr: Optional[Task_O1] = None



        # 统计

        self.nr_running = 0

        self.nr_switches = 0

        self.expired_timestamp = 0

        self. youngest_timestamp = 0



    def enqueue_task(self, task: Task_O1):

        """入队任务"""

        self.active.enqueue_task(task)

        self.nr_running += 1



    def dequeue_task(self, task: Task_O1):

        """出队任务"""

        if task.on_rq:

            self.active.dequeue_task(task)

            self.nr_running -= 1





class O1_Scheduler:

    """

    O(1)调度器



    算法：

    1. 每个时间片结束时，时间片耗尽的任务被移到expired队列

    2. 如果expired队列为空，交换active和expired指针

    3. 选择最高优先级队列中的第一个任务运行

    """



    # 时间片配置（毫秒）

    sysctl_sched_min_granularity = 4

    sysctl_sched_latency = 20



    def __init__(self, num_cpus: int = 1):

        self.num_cpus = num_cpus

        self.runqueues: List[Runqueue] = [Runqueue(i) for i in range(num_cpus)]



        # 所有任务

        self.tasks: Dict[int, Task_O1] = {}



    def nice_to_prio(self, nice: int) -> int:

        """将nice值转换为优先级"""

        return NICE_TO_PRIO_OFFSET + nice + DEFAULT_PRIO // 2



    def calculate_time_slice(self, task: Task_O1) -> int:

        """计算任务的时间片"""

        # 基于优先级的 时间片

        base_slice = self.sysctl_sched_latency

        # 简化：所有任务获得相同时间片

        return base_slice // max(1, self.runqueues[0].nr_running)



    def add_task(self, pid: int, name: str, nice: int = 0):

        """添加新任务"""

        # 计算优先级

        static_prio = self.nice_to_prio(nice)



        task = Task_O1(

            pid=pid,

            name=name,

            static_prio=static_prio,

            dynamic_prio=static_prio,

            priority=static_prio,

            time_slice=self.calculate_time_slice(None),

            first_time_slice=True,

            state='R',

            on_rq=False

        )



        self.tasks[pid] = task



        # 入队

        rq = self.runqueues[0]

        rq.enqueue_task(task)



        print(f"  添加任务: {name} (PID={pid}, nice={nice}, prio={static_prio}, time_slice={task.time_slice}ms)")



    def remove_task(self, pid: int):

        """移除任务"""

        if pid in self.tasks:

            task = self.tasks[pid]

            rq = self.runqueues[0]

            rq.dequeue_task(task)

            del self.tasks[pid]



    def schedule(self, cpu_id: int = 0) -> Optional[Task_O1]:

        """

        调度函数

        O(1)复杂度：始终选择active队列中最高优先级的第一个任务

        """

        rq = self.runqueues[cpu_id]



        # 选择下一个任务

        next_task = rq.active.pick_next_task()



        if next_task is None:

            # active队列空，交换

            rq.active, rq.expired = rq.expired, rq.active

            next_task = rq.active.pick_next_task()



        if next_task:

            if rq.curr and rq.curr != next_task:

                rq.nr_switches += 1

            rq.curr = next_task



        return next_task



    def task_tick(self, task: Task_O1, rq: Runqueue):

        """

        时间片递减

        每个tick调用一次

        """

        if not task.on_rq:

            return



        task.time_slice -= 1



        if task.time_slice <= 0:

            # 时间片耗尽

            task.first_time_slice = False



            # 重新计算时间片

            task.time_slice = self.calculate_time_slice(task)



            # 重新计算优先级（惩罚交互任务）

            self._recalc_task_prio(task)



            # 移动到expired队列或active队列

            if task.dynamic_prio < task.static_prio:

                # 降低优先级，移到active（奖励交互任务）

                task.priority = task.dynamic_prio

                rq.active.enqueue_task(task)

            else:

                # 移到expired

                rq.expired.enqueue_task(task)



    def _recalc_task_prio(self, task: Task_O1):

        """

        重新计算动态优先级

        简化版本：实际上O(1)调度器有复杂的交互任务检测机制

        """

        # 简化：保持静态优先级

        task.dynamic_prio = task.static_prio





def simulate_o1_scheduler():

    """

    模拟O(1)调度器

    """

    print("=" * 60)

    print("O(1)调度器（早期Linux）模拟")

    print("=" * 60)



    scheduler = O1_Scheduler(num_cpus=1)



    # 添加任务

    print("\n添加任务:")

    print("-" * 50)

    scheduler.add_task(1, "init", nice=0)

    scheduler.add_task(2, "bash", nice=0)

    scheduler.add_task(3, "vim", nice=-5)

    scheduler.add_task(4, "top", nice=5)

    scheduler.add_task(5, "make", nice=0)



    rq = scheduler.runqueues[0]

    print(f"\n运行队列状态:")

    print(f"  活跃任务数: {rq.active.nr_active}")

    print(f"  当前任务: {rq.curr.name if rq.curr else 'None'}")



    # 模拟调度

    print("\n调度序列:")

    print("-" * 50)



    for i in range(1, 11):

        task = scheduler.schedule()

        if task:

            print(f"  时间片 {i}: {task.name} (prio={task.priority}, time_slice={task.time_slice}ms)")



            # 模拟时间片耗尽

            task.time_slice = 0

            scheduler.task_tick(task, rq)



            # 重新入队（简化）

            rq.active.enqueue_task(task)



    print(f"\n总上下文切换: {rq.nr_switches}")



    # 演示位图查找

    print("\n" + "=" * 60)

    print("优先级位图查找演示")

    print("=" * 60)



    pa = PriorityArray()



    # 添加一些任务到不同优先级

    tasks = [

        Task_O1(10, "p1", 100, 100, 100, 10, False),

        Task_O1(11, "p2", 105, 105, 105, 10, False),

        Task_O1(12, "p3", 102, 102, 102, 10, False),

        Task_O1(13, "p4", 108, 108, 108, 10, False),

    ]



    for task in tasks:

        pa.enqueue_task(task)



    print(f"\n位图状态: {pa.bitmap}")

    print(f"最高优先级: {pa._find_highest_bit()}")



    next_task = pa.pick_next_task()

    print(f"下一个任务: {next_task.name if next_task else 'None'}")





if __name__ == "__main__":

    simulate_o1_scheduler()


# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / realtime_scheduler

本文件实现 realtime_scheduler 相关的算法功能。
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
import threading


class SchedulingPolicy(Enum):
    """调度策略"""
    SCHED_FIFO = "SCHED_FIFO"
    SCHED_RR = "SCHED_RR"
    SCHED_OTHER = "SCHED_OTHER"


class TaskState:
    """任务状态"""
    RUNNING = "RUNNING"
    READY = "READY"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"


@dataclass
class RT_Task:
    """实时任务"""
    pid: int
    name: str
    policy: SchedulingPolicy
    priority: int           # 1-99（实时），0（CFS）
    time_slice: int = 0     # RR时间片（仅RR）
    remaining_slice: int = 0

    # 状态
    state: str = TaskState.READY
    on_rq: bool = False

    # 资源等待（用于优先级继承）
    waiting_for_resource: Optional[str] = None
    owned_resources: Set[str] = set()

    # 继承优先级（用于优先级继承）
    inherited_priority: int = 0


class PriorityInheritanceMutex:
    """
    优先级继承互斥锁

    解决优先级反转问题。
    当高优先级任务等待低优先级任务持有的锁时，
    临时提升低优先级任务的优先级。
    """

    def __init__(self, name: str):
        self.name = name
        self.owner: Optional[RT_Task] = None
        self.wait_queue: List[RT_Task] = []

        # 记录原始优先级（用于恢复）
        self.original_priorities: Dict[int, int] = {}

    def acquire(self, task: RT_Task) -> bool:
        """
        获取锁
        param task: 请求锁的任务
        return: 是否成功获取
        """
        if self.owner is None:
            self.owner = task
            task.owned_resources.add(self.name)
            return True

        # 锁已被持有，加入等待队列
        if task not in self.wait_queue:
            self.wait_queue.append(task)

        # 优先级继承：如果高优先级任务在等待，提升当前持有者优先级
        self._inherit_priority(task)

        return False

    def release(self, task: RT_Task):
        """释放锁"""
        if self.owner == task:
            task.owned_resources.discard(self.name)
            self.owner = None

            # 恢复持有者的原始优先级
            self._restore_priority()

            # 将等待队列中的下一个任务设为所有者
            if self.wait_queue:
                next_task = self.wait_queue.pop(0)
                self.acquire(next_task)

    def _inherit_priority(self, waiting_task: RT_Task):
        """
        优先级继承
        临时提升锁持有者的优先级到等待者的优先级
        """
        if self.owner is None:
            return

        # 如果等待者优先级更高，提升持有者
        effective_owner_priority = self.owner.inherited_priority or self.owner.priority
        effective_waiter_priority = waiting_task.inherited_priority or waiting_task.priority

        if effective_waiter_priority > effective_owner_priority:
            # 保存原始优先级
            if self.owner.priority not in self.original_priorities:
                self.original_priorities[self.owner.priority] = self.owner.priority

            # 提升优先级
            inherited_prio = effective_waiter_priority
            self.owner.inherited_priority = inherited_prio
            print(f"  [优先级继承] {self.owner.name} 优先级 {self.owner.priority} -> {inherited_prio}")

    def _restore_priority(self):
        """恢复原始优先级"""
        if self.owner and self.owner.inherited_priority:
            orig_prio = self.owner.priority
            self.owner.inherited_priority = 0
            print(f"  [优先级恢复] {self.owner.name} 恢复到优先级 {orig_prio}")


class RT_Scheduler:
    """
    实时调度器

    支持SCHED_FIFO和SCHED_RR。
    """

    # 优先级范围
    RT_PRIO_MIN = 1
    RT_PRIO_MAX = 99

    def __init__(self):
        # 优先级队列（每个优先级一个列表）
        self.rq: Dict[int, List[RT_Task]] = {i: [] for i in range(1, 100)}
        self.rt_tasks: Dict[int, RT_Task] = {}

        # 当前运行任务
        self.curr: Optional[RT_Task] = None

        # 时间片配置
        self.timeslice_rr = 100  # RR时间片（ms）

        # 统计
        self.nr_switches = 0

    def add_task(self, pid: int, name: str, policy: SchedulingPolicy, priority: int):
        """添加实时任务"""
        task = RT_Task(
            pid=pid,
            name=name,
            policy=policy,
            priority=priority,
            time_slice=self.timeslice_rr,
            remaining_slice=self.timeslice_rr
        )
        self.rt_tasks[pid] = task
        self._enqueue_task(task)
        print(f"  添加RT任务: {name} (PID={pid}, policy={policy.value}, prio={priority})")

    def _enqueue_task(self, task: RT_Task):
        """任务入队"""
        self.rq[task.priority].append(task)
        task.on_rq = True

    def _dequeue_task(self, task: RT_Task):
        """任务出队"""
        if task.on_rq:
            self.rq[task.priority].remove(task)
            task.on_rq = False

    def _pick_next_task(self) -> Optional[RT_Task]:
        """选择下一个任务（O(1)复杂度）"""
        # 从最高优先级开始找
        for prio in range(self.RT_PRIO_MAX, self.RT_PRIO_MIN - 1, -1):
            queue = self.rq[prio]
            if queue:
                return queue[0]
        return None

    def schedule(self) -> Optional[RT_Task]:
        """调度函数"""
        next_task = self._pick_next_task()

        if next_task and next_task != self.curr:
            if self.curr:
                self.nr_switches += 1
            self.curr = next_task

        return next_task

    def task_yield(self, task: RT_Task):
        """任务主动让出CPU"""
        self._dequeue_task(task)
        self._enqueue_task(task)

    def task_block(self, task: RT_Task):
        """任务阻塞"""
        task.state = TaskState.WAITING
        self._dequeue_task(task)

    def task_wakeup(self, task: RT_Task):
        """任务唤醒"""
        task.state = TaskState.READY
        self._enqueue_task(task)

    def rr_time_slice_expired(self, task: RT_Task):
        """RR时间片耗尽"""
        if task.policy == SchedulingPolicy.SCHED_RR:
            # 移到同优先级的队尾
            self._dequeue_task(task)
            self._enqueue_task(task)
            task.remaining_slice = task.time_slice

    def get_highest_rtprio(self) -> int:
        """获取最高实时优先级"""
        for prio in range(self.RT_PRIO_MAX, self.RT_PRIO_MIN - 1, -1):
            if self.rq[prio]:
                return prio
        return 0


def simulate_realtime_scheduler():
    """
    模拟实时调度器
    """
    print("=" * 60)
    print("实时调度：SCHED_FIFO / SCHED_RR")
    print("=" * 60)

    scheduler = RT_Scheduler()

    # 添加实时任务
    print("\n添加实时任务:")
    print("-" * 50)
    scheduler.add_task(1, "RT_high", SchedulingPolicy.SCHED_FIFO, priority=90)
    scheduler.add_task(2, "RT_mid", SchedulingPolicy.SCHED_FIFO, priority=50)
    scheduler.add_task(3, "RT_low", SchedulingPolicy.SCHED_FIFO, priority=10)
    scheduler.add_task(4, "RT_rr", SchedulingPolicy.SCHED_RR, priority=70)

    # 模拟调度
    print("\n调度序列 (FIFO):")
    print("-" * 50)

    for i in range(5):
        task = scheduler.schedule()
        if task:
            print(f"  调度: {task.name} (prio={task.priority}, policy={task.policy.value})")

            if task.policy == SchedulingPolicy.SCHED_FIFO:
                # FIFO：主动让出才切换
                scheduler.task_yield(task)
            elif task.policy == SchedulingPolicy.SCHED_RR:
                # RR：时间片耗尽切换
                task.remaining_slice -= 20
                if task.remaining_slice <= 0:
                    scheduler.rr_time_slice_expired(task)

    # 优先级继承演示
    print("\n" + "=" * 60)
    print("优先级继承 (Priority Inheritance)")
    print("=" * 60)

    print("\n场景: 高优先级任务等待低优先级任务释放锁")
    print("-" * 50)

    # 创建互斥锁
    mutex = PriorityInheritanceMutex("resource_A")

    # 创建任务
    task_low = RT_Task(10, "LowPrio", SchedulingPolicy.SCHED_FIFO, 10)
    task_mid = RT_Task(11, "MidPrio", SchedulingPolicy.SCHED_FIFO, 50)
    task_high = RT_Task(12, "HighPrio", SchedulingPolicy.SCHED_FIFO, 90)

    print("\n初始状态:")
    print(f"  {task_low.name}: prio={task_low.priority}")
    print(f"  {task_mid.name}: prio={task_mid.priority}")
    print(f"  {task_high.name}: prio={task_high.priority}")

    # LowPrio获取锁
    print(f"\n{LowPrio.name} 获取锁 resource_A")
    mutex.acquire(task_low)
    print(f"  锁持有者: {mutex.owner.name if mutex.owner else 'None'}")

    # HighPrio尝试获取锁（阻塞）
    print(f"\n{HighPrio.name} 尝试获取锁 resource_A")
    result = mutex.acquire(task_high)
    if not result:
        print(f"  {task_high.name} 被阻塞，等待锁释放")

    # MidPrio运行（比LowPrio高但比HighPrio低）
    print(f"\n{MidPrio.name} 尝试运行（但优先级低于HighPrio继承后的优先级）")
    print(f"  因为优先级继承，LowPrio的优先级已提升到 {task_low.inherited_priority or task_low.priority}")

    # LowPrio释放锁
    print(f"\n{LowPrio.name} 释放锁 resource_A")
    mutex.release(task_low)
    print(f"  锁现在被 {mutex.owner.name if mutex.owner else 'None'} 持有")

    # HighPrio获取锁
    if mutex.owner == task_high:
        print(f"\n{HighPrio.name} 成功获取锁！")


if __name__ == "__main__":
    simulate_realtime_scheduler()

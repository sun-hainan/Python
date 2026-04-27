# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / preempt_scheduling

本文件实现 preempt_scheduling 相关的算法功能。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time
import heapq


class SchedulerType(Enum):
    """调度器类型"""
    PREEMPTIVE_RT = "preemptive_rt"      # 实时抢占
    PREEMPTIVE_FIFO = "preemptive_fifo"  # 先到先服务（可抢占）
    NON_PREEMPTIVE = "non_preemptive"   # 合作式


@dataclass
class SchedulableTask:
    """可调度任务"""
    tid: int
    name: str
    priority: int             # 优先级（数值越小优先级越高）
    burst_time: float        # 总CPU时间需求
    remaining_time: float    # 剩余时间
    arrival_time: float      # 到达时间
    is_periodic: bool = False
    period: float = 0.0
    deadline: float = 0.0

    def __lt__(self, other: "SchedulableTask"):
        # 优先级队列：优先级高的先出
        return self.priority < other.priority


class PreemptiveScheduler:
    """
    抢占式调度器
    每次事件（任务到达、时间片用完、更高优先级任务到达）都重新调度
    """

    def __init__(self, scheduler_type: SchedulerType = SchedulerType.PREEMPTIVE_RT):
        self.scheduler_type = scheduler_type
        self.ready_queue: list[SchedulableTask] = []
        self.current_task: Optional[SchedulableTask] = None
        self.current_time: float = 0.0
        self.schedule_events: list[dict] = []
        self.tick_duration: float = 0.1  # 时间片长度

    def add_task(self, task: SchedulableTask):
        """添加任务到就绪队列"""
        task.remaining_time = task.burst_time
        heapq.heappush(self.ready_queue, task)

    def _reschedule(self, reason: str = ""):
        """
        重新调度
        检查当前任务是否需要被抢占
        """
        if not self.ready_queue:
            self.current_task = None
            return

        # 找到最高优先级任务
        highest = self.ready_queue[0]

        # 如果有当前任务且新任务优先级更高，发生抢占
        if self.current_task:
            if highest.priority < self.current_task.priority:
                # 抢占：当前任务放回就绪队列
                self.ready_queue.append(self.current_task)
                heapq.heapify(self.ready_queue)
                self.current_task = heapq.heappop(self.ready_queue)
                self.schedule_events.append({
                    "time": self.current_time,
                    "type": "preempt",
                    "victim_tid": self.current_task.tid if self.current_task else None,
                    "reason": reason
                })
            elif self.scheduler_type == SchedulerType.NON_PREEMPTIVE:
                # 非抢占式：继续执行当前任务
                return
        else:
            self.current_task = heapq.heappop(self.ready_queue)

    def run_tick(self) -> Optional[int]:
        """
        执行一个时间片
        返回当前运行的任务ID
        """
        if self.current_task is None:
            self._reschedule("no_running_task")
            if self.current_task is None:
                return None

        # 执行一个时间片
        self.current_task.remaining_time -= self.tick_duration
        self.current_time += self.tick_duration

        # 时间片用完
        if self.current_task.remaining_time <= 0:
            self.schedule_events.append({
                "time": self.current_time,
                "type": "complete",
                "tid": self.current_task.tid
            })
            self.current_task = None
            self._reschedule("task_completed")

        # 检查是否有更高优先级任务到达（简化：随机触发）
        if self.ready_queue and self.ready_queue[0].priority < (self.current_task.priority if self.current_task else 999):
            self._reschedule("higher_priority_arrival")

        return self.current_task.tid if self.current_task else None

    def simulate(self, duration: float) -> list[dict]:
        """
        模拟调度器运行
        返回调度事件序列
        """
        steps = int(duration / self.tick_duration)
        for _ in range(steps):
            self.run_tick()

        return self.schedule_events


class PriorityInheritance:
    """
    优先级继承协议
    解决优先级反转问题：低优先级任务持有锁，高优先级任务被阻塞
    解决方案：临时提升低优先级任务的优先级到阻塞者的级别
    """

    def __init__(self):
        self.locks_held_by: dict[int, list[int]] = {}  # lock_id -> [holder_tids]
        self.task_priority: dict[int, int] = {}  # tid -> priority
        self.original_priority: dict[int, int] = {}  # tid -> original_priority

    def acquire_lock(self, tid: int, lock_id: int, lock_holder_priority: int):
        """
        任务获取锁
        如果锁被低优先级任务持有，考虑提升持有者优先级
        """
        if lock_id not in self.locks_held_by:
            self.locks_held_by[lock_id] = []

        # 检查是否有其他任务持有此锁
        for holder_tid in self.locks_held_by[lock_id]:
            holder_priority = self.task_priority.get(holder_tid, 50)
            requestor_priority = self.task_priority.get(tid, 50)

            # 如果请求者优先级更高，提升持有者
            if requestor_priority < holder_priority:
                self._boost_priority(holder_tid, requestor_priority)

        self.locks_held_by[lock_id].append(tid)

    def release_lock(self, tid: int, lock_id: int):
        """释放锁，恢复原始优先级"""
        if lock_id in self.locks_held_by:
            if tid in self.locks_held_by[lock_id]:
                self.locks_held_by[lock_id].remove(tid)

        self._restore_priority(tid)

    def _boost_priority(self, tid: int, boost_to: int):
        """提升优先级"""
        if tid not in self.original_priority:
            self.original_priority[tid] = self.task_priority.get(tid, 50)
        self.task_priority[tid] = min(self.task_priority.get(tid, 999), boost_to)
        print(f"优先级继承: T{tid} 优先级从 {self.original_priority[tid]} 提升到 {boost_to}")

    def _restore_priority(self, tid: int):
        """恢复原始优先级"""
        if tid in self.original_priority:
            self.task_priority[tid] = self.original_priority[tid]
            print(f"优先级恢复: T{tid} 恢复到 {self.original_priority[tid]}")


if __name__ == "__main__":
    print("=== 抢占式调度演示 ===")

    scheduler = PreemptiveScheduler(SchedulerType.PREEMPTIVE_RT)

    # 创建任务（优先级：数值越小越高）
    tasks = [
        SchedulableTask(tid=1, name="HighPri", priority=10, burst_time=2.0, arrival_time=0.0),
        SchedulableTask(tid=2, name="LowPri", priority=50, burst_time=3.0, arrival_time=0.0),
        SchedulableTask(tid=3, name="MedPri", priority=30, burst_time=1.5, arrival_time=0.0),
    ]

    for t in tasks:
        scheduler.add_task(t)

    print("\n任务列表:")
    for t in tasks:
        print(f"  T{t.tid} ({t.name}): priority={t.priority}, burst={t.burst_time}")

    print("\n调度模拟（前20个时间片）:")
    for i in range(20):
        tid = scheduler.run_tick()
        if tid:
            print(f"t={scheduler.current_time:.1f}: 运行 T{tid}")
        else:
            print(f"t={scheduler.current_time:.1f}: idle")

    print("\n--- 优先级继承演示 ---")
    pi = PriorityInheritance()

    # 模拟场景：低优先级任务持有锁，高优先级任务等待
    pi.task_priority = {100: 50, 200: 10}  # T100低优先级，T200高优先级

    print("场景：T200（高优先级）需要T100持有的锁")
    print(f"初始: T100 priority={pi.task_priority[100]}, T200 priority={pi.task_priority[200]}")

    # T200等待T100持有的锁
    print("\nT200尝试获取锁...")
    pi.acquire_lock(200, lock_id=1, lock_holder_priority=pi.task_priority[200])

    print(f"结果: T100 priority={pi.task_priority[100]}（提升以避免优先级反转）")

    print("\nT100释放锁后...")
    pi.release_lock(100, lock_id=1)
    print(f"结果: T100 priority={pi.task_priority[100]}（恢复原始）")

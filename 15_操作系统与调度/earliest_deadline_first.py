# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / earliest_deadline_first

本文件实现 earliest_deadline_first 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Optional
import heapq
import math


@dataclass
class RTJob:
    """实时作业"""
    job_id: int
    tid: int
    release_time: float      # 释放时间
    absolute_deadline: float  # 绝对截止时间（= release + relative_deadline）
    execution_time: float    # 执行时间
    remaining_time: float = 0.0
    priority: float = 0.0    # EDF中 priority = earliest_deadline

    def __lt__(self, other: "RTJob"):
        # 优先队列按截止时间排序（越小越先）
        return self.absolute_deadline < other.absolute_deadline


class EDFScheduler:
    """EDF调度器：总是执行截止时间最近的作业"""

    def __init__(self):
        self.ready_queue: list[RTJob] = []  # 优先队列（按deadline排序）
        self.current_job: Optional[RTJob] = None
        self.current_time: float = 0.0
        self.completed_jobs: list[RTJob] = []
        self.missed_deadlines: list[RTJob] = []

    def release_job(self, job: RTJob):
        """释放新作业"""
        job.remaining_time = job.execution_time
        job.priority = job.absolute_deadline  # 优先级=截止时间
        heapq.heappush(self.ready_queue, job)

    def release_jobs_at_time(self, jobs: list[RTJob]):
        """批量释放作业"""
        for job in jobs:
            self.release_job(job)

    def check_deadlines(self):
        """检查是否有作业错过截止时间"""
        missed = []
        while self.ready_queue:
            job = heapq.heappop(self.ready_queue)
            if job.absolute_deadline < self.current_time:
                missed.append(job)
            else:
                # 放回队列（因为是按deadline排序的最小堆）
                heapq.heappush(self.ready_queue, job)
                break
        return missed

    def schedule(self) -> Optional[RTJob]:
        """调度决策：选择截止时间最近的作业"""
        if not self.ready_queue:
            return None

        # 弹出截止时间最早的作业
        job = heapq.heappop(self.ready_queue)

        # 再次检查deadline
        if job.absolute_deadline < self.current_time:
            self.missed_deadlines.append(job)
            return self.schedule()  # 递归找下一个

        self.current_job = job
        return job

    def run_for(self, duration: float) -> list[tuple[float, int, float]]:
        """
        运行EDF调度器duration时间
        返回事件序列: [(start_time, tid, duration), ...]
        """
        events = []
        end_time = self.current_time + duration

        while self.current_time < end_time and (self.ready_queue or self.current_job):
            # 调度
            job = self.schedule()
            if job is None:
                # 空闲
                idle_time = min(
                    (self.ready_queue[0].release_time if self.ready_queue else end_time),
                    end_time
                ) - self.current_time
                self.current_time += idle_time
                continue

            # 计算执行时间：到下一个作业释放或deadline
            next_release = self.ready_queue[0].release_time if self.ready_queue else float('inf')
            next_deadline = min(job.absolute_deadline, next_release)

            exec_time = min(job.remaining_time, next_deadline - self.current_time)
            exec_time = min(exec_time, end_time - self.current_time)

            events.append((self.current_time, job.job_id, exec_time))
            self.current_time += exec_time
            job.remaining_time -= exec_time

            # 作业完成
            if job.remaining_time <= 1e-9:
                self.completed_jobs.append(job)
            elif self.current_time >= job.absolute_deadline:
                self.missed_deadlines.append(job)
            else:
                # 放回就绪队列
                heapq.heappush(self.ready_queue, job)

        return events

    def get_utilization(self, horizon: float) -> float:
        """计算时间范围内的CPU利用率"""
        total_exec = sum(j.execution_time for j in self.completed_jobs)
        return total_exec / horizon if horizon > 0 else 0.0


def edf_schedulability_test(tasks: list[tuple[float, float]]) -> tuple[bool, float]:
    """
    EDF可调度性测试
    tasks: [(execution_time, period), ...]
    定理：总利用率 ≤ 1 则可调度（充分条件）
    """
    total_util = sum(e / p for e, p in tasks)
    return total_util <= 1.0, total_util


if __name__ == "__main__":
    print("=== EDF调度器测试 ===")

    scheduler = EDFScheduler()

    # 创建作业：job_id, tid, release, deadline, exec_time
    jobs = [
        RTJob(job_id=1, tid=1, release_time=0.0, absolute_deadline=5.0, execution_time=2.0),
        RTJob(job_id=2, tid=1, release_time=0.0, absolute_deadline=8.0, execution_time=3.0),
        RTJob(job_id=3, tid=2, release_time=2.0, absolute_deadline=6.0, execution_time=1.5),
        RTJob(job_id=4, tid=1, release_time=4.0, absolute_deadline=10.0, execution_time=2.0),
    ]

    print("作业集:")
    for j in jobs:
        print(f"  J{j.job_id}: release={j.release_time}, deadline={j.absolute_deadline}, exec={j.execution_time}")

    # 释放作业
    for j in jobs:
        scheduler.release_job(j)

    print("\n调度事件:")
    events = scheduler.run_for(12.0)
    for start, jid, dur in events:
        print(f"  [{start:.1f}-{start+dur:.1f}] 运行 J{jid} ({dur:.1f}时间)")

    print(f"\n完成作业数: {len(scheduler.completed_jobs)}")
    print(f"错过截止时间: {len(scheduler.missed_deadlines)}")
    if scheduler.missed_deadlines:
        print(f"  错过: {[j.job_id for j in scheduler.missed_deadlines]}")

    # EDF可调度性测试
    print("\n=== EDF可调度性测试 ===")
    test_cases = [
        [(2, 5), (3, 10), (1.5, 15)],  # 总利用率 0.4+0.3+0.1=0.8 < 1
        [(4, 5), (4, 10)],              # 总利用率 0.8+0.4=1.2 > 1
        [(1, 3), (1, 3), (1, 3)],      # 总利用率 3*0.333=1.0 = 边界
    ]

    for i, tasks in enumerate(test_cases):
        ok, util = edf_schedulability_test(tasks)
        print(f"案例{i + 1}: 利用率={util:.4f} -> {'✓ 可调度' if ok else '✗ 不可调度'}")

    # 周期任务示例
    print("\n=== 周期任务模拟 ===")
    scheduler2 = EDFScheduler()
    periodic_jobs = [
        RTJob(job_id=10, tid=1, release_time=0.0, absolute_deadline=10.0, execution_time=3.0),
        RTJob(job_id=11, tid=1, release_time=10.0, absolute_deadline=20.0, execution_time=3.0),
        RTJob(job_id=12, tid=2, release_time=0.0, absolute_deadline=15.0, execution_time=4.0),
        RTJob(job_id=13, tid=2, release_time=15.0, absolute_deadline=30.0, execution_time=4.0),
    ]
    for j in periodic_jobs:
        scheduler2.release_job(j)

    events2 = scheduler2.run_for(30.0)
    print(f"30时间单位内执行了{len(events2)}个时间片")
    print(f"完成作业: {[j.job_id for j in scheduler2.completed_jobs]}")
    print(f"CPU利用率: {scheduler2.get_utilization(30.0):.2%}")

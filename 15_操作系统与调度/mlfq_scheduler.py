# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / mlfq_scheduler

本文件实现 mlfq_scheduler 相关的算法功能。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time

class ProcessState(Enum):
    """进程状态枚举"""
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    TERMINATED = "terminated"


@dataclass
class Process:
    """进程控制块（PCB）"""
    pid: int
    arrival_time: float  # 到达时间
    burst_time: float     # CPU burst总时长
    remaining_time: float  # 剩余CPU时间
    priority: int = 0      # 初始优先级（0最高）
    state: ProcessState = ProcessState.NEW
    current_queue: int = 0  # 当前所在队列层级
    total_cpu_time: float = 0  # 累计CPU占用时间
    context_switches: int = 0


class MLFQScheduler:
    """
    多级反馈队列调度器
    层级数：5（可配置）
    时间片：Q1=1ms, Q2=2ms, Q4=4ms, Q8=8ms, Q16=16ms
    提升策略：每等待S秒提升到更高优先级
    降级策略：进程用完时间片降级，用完则返回就绪队列
    """

    def __init__(self, num_queues: int = 5, boost_interval: float = 1.0):
        self.num_queues = num_queues
        self.queues: list[list[Process]] = [[] for _ in range(num_queues)]
        self.time_slice = [2 ** i for i in range(num_queues)]  # 1,2,4,8,16ms
        self.boost_interval = boost_interval
        self.current_time = 0.0
        self.current_pid = None
        self.current_remaining = 0.0

    def add_process(self, proc: Process):
        """添加新进程"""
        proc.state = ProcessState.READY
        proc.current_queue = 0
        self.queues[0].append(proc)

    def _boost_all(self):
        """提升所有进程优先级（防止饥饿）"""
        for q in self.queues:
            for p in q:
                if p.current_queue > 0:
                    p.current_queue -= 1

    def _select_next(self) -> Optional[Process]:
        """选择下一个运行的进程（最高优先级非空队列）"""
        for q_idx in range(self.num_queues):
            if self.queues[q_idx]:
                return self.queues[q_idx].pop(0)
        return None

    def schedule(self) -> Optional[Process]:
        """
        执行一次调度决策
        返回即将运行的进程，或None（如果idle）
        """
        self._boost_all()

        proc = self._select_next()
        if proc:
            proc.state = ProcessState.RUNNING
            proc.current_queue = min(proc.current_queue, self.num_queues - 1)
            self.current_pid = proc.pid
            self.current_remaining = self.time_slice[proc.current_queue]
        return proc

    def tick(self, elapsed: float):
        """模拟时间流逝"""
        self.current_time += elapsed

    def on_time_slice_expired(self, proc: Process):
        """时间片用完回调"""
        proc.context_switches += 1
        proc.state = ProcessState.READY
        if proc.remaining_time > 0:
            # 降级到更低优先级队列（用完时间片）
            proc.current_queue = min(proc.current_queue + 1, self.num_queues - 1)
            self.queues[proc.current_queue].append(proc)

    def on_io_complete(self, proc: Process):
        """I/O完成回调，优先级提升"""
        proc.state = ProcessState.READY
        # I/O密集型进程保持较高优先级
        proc.current_queue = max(0, proc.current_queue - 1)
        self.queues[proc.current_queue].append(proc)


def simulate_mlfq(arrivals: list[tuple], time_slice: float = 1.0) -> list[dict]:
    """
    模拟MLFQ调度
    arrivals: [(arrival_time, pid, burst_time), ...]
    返回调度事件序列
    """
    scheduler = MLFQScheduler()
    events = []
    current_time = 0.0
    processes = {}

    # 创建进程
    for arrival, pid, burst in arrivals:
        proc = Process(pid=pid, arrival_time=arrival, burst_time=burst, remaining_time=burst)
        processes[pid] = proc
        if arrival == 0:
            scheduler.add_process(proc)

    pending = [a for a, _, _ in arrivals[1:]]

    while any(p.remaining_time > 0 for p in processes.values()):
        proc = scheduler.schedule()
        if proc is None:
            current_time += time_slice
            continue

        exec_time = min(time_slice, proc.remaining_time)
        events.append({
            "time": current_time,
            "pid": proc.pid,
            "duration": exec_time,
            "action": "run"
        })

        proc.remaining_time -= exec_time
        current_time += exec_time

        if proc.remaining_time > 0:
            scheduler.on_time_slice_expired(proc)
        else:
            proc.state = ProcessState.TERMINATED

    return events


if __name__ == "__main__":
    # 创建测试进程
    procs = [
        Process(pid=1, arrival_time=0.0, burst_time=5.0),
        Process(pid=2, arrival_time=1.0, burst_time=3.0),
        Process(pid=3, arrival_time=2.0, burst_time=8.0),
    ]

    scheduler = MLFQScheduler()
    for p in procs:
        scheduler.add_process(p)

    print("=== MLFQ调度模拟 ===")
    print(f"队列数: {scheduler.num_queues}")
    print(f"时间片: {scheduler.time_slice}")
    print()

    # 模拟调度
    while True:
        proc = scheduler.schedule()
        if proc is None:
            break

        ts = scheduler.time_slice[proc.current_queue]
        print(f"时间 {scheduler.current_time:.2f}: 运行 P{proc.pid} (队列{proc.current_queue}, 片{ts}ms)")
        exec_t = min(ts, proc.remaining_time)
        proc.remaining_time -= exec_t
        scheduler.tick(exec_t)

        if proc.remaining_time > 0:
            scheduler.on_time_slice_expired(proc)
        else:
            proc.state = ProcessState.TERMINATED
            print(f"  -> P{proc.pid} 完成")

    # 批量模拟测试
    print("\n=== 批量调度测试 ===")
    arrivals = [(0, 1, 10), (0, 2, 5), (3, 3, 8), (5, 4, 3)]
    events = simulate_mlfq(arrivals)
    print(f"共 {len(events)} 个调度事件")

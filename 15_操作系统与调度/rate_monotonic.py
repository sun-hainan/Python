# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / rate_monotonic



本文件实现 rate_monotonic 相关的算法功能。

"""



from dataclasses import dataclass

from typing import Optional

import math





@dataclass

class PeriodicTask:

    """周期任务描述"""

    tid: int

    execution_time: float  # 执行时间(C)

    period: float            # 周期(T)

    deadline: float = 0.0    # 相对截止时间

    priority: int = 0         # 静态优先级（越小越高）

    remaining_time: float = 0.0

    next_release: float = 0.0





def calc_rms_utilization_bound(num_tasks: int) -> float:

    """计算RMS可调度的利用率上界（n*(2^(1/n)-1)）"""

    return num_tasks * (2 ** (1.0 / num_tasks) - 1)





def calc_task_utilization(task: PeriodicTask) -> float:

    """计算单个任务的利用率 Ui = Ci/Ti"""

    return task.execution_time / task.period





def check_rms_schedulable(tasks: list[PeriodicTask]) -> tuple[bool, float]:

    """

    检查任务集是否满足RMS可调度性

    1. 检查总利用率是否低于上界

    2. （可选）精确分析法：模拟时间轴

    返回：(可调度?, 总利用率)

    """

    n = len(tasks)

    bound = calc_rms_utilization_bound(n)

    total_util = sum(calc_task_utilization(t) for t in tasks)



    return total_util <= bound, total_util





def rms_assign_priorities(tasks: list[PeriodicTask]) -> list[PeriodicTask]:

    """

    RMS优先级分配：周期越短优先级越高

    """

    # 按周期排序（升序）

    sorted_tasks = sorted(tasks, key=lambda t: t.period)

    for priority, task in enumerate(sorted_tasks):

        task.priority = priority

    return sorted_tasks





def simulate_rms(tasks: list[PeriodicTask], horizon: float = 100.0) -> list[tuple[float, int]]:

    """

    模拟RMS调度，返回调度事件序列

    [(time, tid), ...]

    """

    events = []

    active_tasks: list[PeriodicTask] = []

    current_time = 0.0



    # 初始化任务

    for task in tasks:

        task.remaining_time = task.execution_time

        task.next_release = 0.0



    def get_highest_priority_task() -> Optional[PeriodicTask]:

        if not active_tasks:

            return None

        return min(active_tasks, key=lambda t: t.priority)



    while current_time < horizon:

        # 释放新任务

        for task in tasks:

            if abs(task.next_release - current_time) < 1e-9:

                active_tasks.append(task)

                task.remaining_time = task.execution_time

                task.next_release += task.period



        # 选择最高优先级任务

        proc = get_highest_priority_task()

        if proc is None:

            # 空闲，跳到下一个任务释放

            next_release = min(t.next_release for t in tasks)

            current_time = next_release

            continue



        # 计算最小截止时间

        min_next_event = min([

            proc.next_release,

            *[t.next_release for t in active_tasks if t != proc]

        ]) if active_tasks else current_time + proc.period



        exec_time = min(proc.remaining_time, min_next_event - current_time)



        events.append((current_time, proc.tid, exec_time))

        current_time += exec_time

        proc.remaining_time -= exec_time



        # 任务完成

        if proc.remaining_time <= 1e-9:

            active_tasks.remove(proc)

            if abs(proc.remaining_time) < 1e-9:

                proc.remaining_time = 0.0



    return events





if __name__ == "__main__":

    # 测试案例：3个周期任务

    tasks = [

        PeriodicTask(tid=1, execution_time=1.0, period=5.0),

        PeriodicTask(tid=2, execution_time=2.0, period=10.0),

        PeriodicTask(tid=3, execution_time=1.5, period=15.0),

    ]



    print("=== 单调速率调度(RMS)分析 ===")

    print(f"任务数: {len(tasks)}")

    print(f"利用率上界: {calc_rms_utilization_bound(len(tasks)):.4f}")



    # 分配优先级

    tasks = rms_assign_priorities(tasks)

    print("\n优先级分配（周期越短优先级越高）:")

    for t in tasks:

        util = calc_task_utilization(t)

        print(f"  T{t.tid}: period={t.period}, exec={t.execution_time}, prio={t.priority}, Ui={util:.4f}")



    # 可调度性检查

    schedulable, total_util = check_rms_schedulable(tasks)

    print(f"\n可调度性: {'✓ 可调度' if schedulable else '✗ 不可调度'}")

    print(f"总利用率: {total_util:.4f} / {calc_rms_utilization_bound(len(tasks)):.4f}")



    # 模拟调度

    print("\n=== 调度模拟（前30时间单位）===")

    events = simulate_rms(tasks, horizon=30.0)

    current_tid = None

    for time, tid, dur in events:

        if tid != current_tid:

            print(f"\nt={time:.1f}: 运行 T{tid} (执行{ dur:.1f})")

            current_tid = tid



    # 验证deadline

    print("\n=== Deadline满足检查 ===")

    deadline_misses = 0

    for task in tasks:

        # 简化检查：最大响应时间不超过周期

        resp_time = sum(e[2] for e in events if e[1] == task.tid)

        miss = resp_time > task.period

        if miss:

            deadline_misses += 1

        print(f"T{task.tid}: 响应时间={resp_time:.2f}, 周期={task.period} -> {'✓' if not miss else '✗错过deadline'}")


# -*- coding: utf-8 -*-
"""
算法实现：近似算法 / lpt_schedule

本文件实现 lpt_schedule 相关的算法功能。
"""

from typing import List, Tuple


def lpt_schedule(tasks: List[float], num_machines: int) -> Tuple[List[List[float]], float]:
    """
    LPT调度算法

    参数：
        tasks: 任务处理时间列表
        num_machines: 机器数量

    返回：(调度方案, makespan)
    """
    if num_machines <= 0:
        return [], 0

    # 按处理时间降序排列
    sorted_tasks = sorted(tasks, reverse=True)

    # 每台机器的负载
    loads = [0.0] * num_machines
    schedule = [[] for _ in range(num_machines)]

    # 贪心分配
    for task in sorted_tasks:
        # 找负载最小的机器
        min_machine = min(range(num_machines), key=lambda i: loads[i])
        schedule[min_machine].append(task)
        loads[min_machine] += task

    makespan = max(loads)

    return schedule, makespan


def optimal_makespan_lower_bound(tasks: List[float]) -> float:
    """最优 makespan 的下界"""
    max_task = max(tasks)
    avg_load = sum(tasks) / len(tasks)  # 假设1台机器
    return max(max_task, sum(tasks) / len(tasks))


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LPT调度测试 ===\n")

    import random
    random.seed(42)

    # 生成随机任务
    tasks = [random.uniform(1, 10) for _ in range(15)]
    num_machines = 4

    print(f"任务数: {len(tasks)}")
    print(f"机器数: {num_machines}")
    print(f"任务时间: {[f'{t:.1f}' for t in tasks]}")

    schedule, makespan = lpt_schedule(tasks, num_machines)

    print(f"\n调度方案:")
    for i, machine_tasks in enumerate(schedule):
        total = sum(machine_tasks)
        print(f"  机器{i}: {[f'{t:.1f}' for t in machine_tasks]} = {total:.1f}")

    print(f"\nMakespan: {makespan:.2f}")

    # 计算下界
    avg = sum(tasks) / num_machines
    print(f"LPT / 最优下界: {makespan / avg:.2f}")

    print("\n说明：")
    print("  - LPT是最简单的调度近似算法")
    print("  - 近似比: 4/3 - 1/(3m) ≈ 1.33 (当m大时)")
    print("  - 应用：云计算任务调度、生产线排程")

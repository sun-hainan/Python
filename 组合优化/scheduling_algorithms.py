# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / scheduling_algorithms

本文件实现 scheduling_algorithms 相关的算法功能。
"""

from typing import List, Tuple, Optional
import random


class FlowShopSolver:
    """
    两台机器流水车间调度问题求解器
    使用Johnson规则求解最小化makespan
    """
    
    def __init__(self, jobs: List[Tuple[float, float]]):
        """
        初始化求解器
        
        Args:
            jobs: 每个任务在两台机器上的处理时间 [(t1, t2), ...]
                  t1是机器1的处理时间,t2是机器2的处理时间
        """
        self.jobs = jobs
        self.n = len(jobs)
    
    def johnson_rule(self) -> Tuple[List[int], float]:
        """
        Johnson规则求解两台机器流水车间问题
        
        Returns:
            (最优作业顺序, makespan)
        """
        # 将作业分成两组
        group1 = []  # t1 <= t2的作业
        group2 = []  # t1 > t2的作业
        
        for i, (t1, t2) in enumerate(self.jobs):
            if t1 <= t2:
                group1.append((i, t1, t2))
            else:
                group2.append((i, t1, t2))
        
        # 组1按t1升序排列
        group1.sort(key=lambda x: x[1])
        # 组2按t2降序排列
        group2.sort(key=lambda x: x[2], reverse=True)
        
        # 合并
        order = [x[0] for x in group1] + [x[0] for x in group2]
        
        # 计算makespan
        makespan = self.calculate_makespan(order)
        
        return order, makespan
    
    def calculate_makespan(self, order: List[int]) -> float:
        """
        计算给定顺序的makespan
        
        Args:
            order: 作业顺序
        
        Returns:
            makespan
        """
        if not order:
            return 0
        
        # 机器1完成第一个作业的时间
        t1 = self.jobs[order[0]][0]
        # 机器2完成第一个作业的时间
        t2 = t1 + self.jobs[order[0]][1]
        
        for i in range(1, len(order)):
            # 机器1必须等待上一个作业在机器1上完成
            t1 += self.jobs[order[i]][0]
            # 机器2必须等待: 上一个作业在机器2完成 或 当前作业在机器1完成
            t2 = max(t2, t1) + self.jobs[order[i]][1]
        
        return t2
    
    def calculate_flow_time(self, order: List[int]) -> float:
        """
        计算总流动时间
        
        Args:
            order: 作业顺序
        
        Returns:
            总流动时间
        """
        flow_times = []
        completion = [0.0] * self.n
        
        # 机器1完成时间
        t1 = 0
        for i in order:
            t1 += self.jobs[i][0]
            completion[i] = t1
        
        # 机器2完成时间
        t2 = 0
        for i in order:
            t2 = max(t2, completion[i]) + self.jobs[i][1]
            completion[i] = t2
        
        return sum(completion)
    
    def get_gantt_data(self, order: List[int]) -> List[Tuple[int, float, float, float]]:
        """
        获取甘特图数据
        
        Returns:
            [(作业ID, 开始时间, 机器1结束, 机器2结束), ...]
        """
        gantt = []
        t1 = 0
        t2 = 0
        
        for job_id in order:
            t1 += self.jobs[job_id][0]
            t2 = max(t2, t1) + self.jobs[job_id][1]
            gantt.append((job_id, t1 - self.jobs[job_id][0], t1, t2))
        
        return gantt


class ParallelMachineSolver:
    """
    并行机器调度问题求解器
    使用LPT(Longest Processing Time)算法
    """
    
    def __init__(self, num_machines: int):
        """
        初始化
        
        Args:
            num_machines: 机器数量
        """
        self.m = num_machines
        self.jobs: List[float] = []
    
    def add_job(self, processing_time: float):
        """添加作业"""
        self.jobs.append(processing_time)
    
    def lpt_schedule(self) -> Tuple[List[List[int]], float]:
        """
        LPT算法:按处理时间降序排列,贪心分配
        
        Returns:
            (每个机器的作业列表, makespan)
        """
        # 按处理时间降序
        sorted_jobs = sorted(enumerate(self.jobs), key=lambda x: x[1], reverse=True)
        
        # 每个机器的当前负载
        machine_loads = [0.0] * self.m
        # 每个机器的作业列表
        machine_jobs = [[] for _ in range(self.m)]
        
        for job_id, ptime in sorted_jobs:
            # 分配到负载最小的机器
            min_machine = min(range(self.m), key=lambda i: machine_loads[i])
            machine_jobs[min_machine].append(job_id)
            machine_loads[min_machine] += ptime
        
        makespan = max(machine_loads)
        
        return machine_jobs, makespan
    
    def lpt_optimal_ratio(self) -> float:
        """
        计算LPT的最优性比率(4/3 - 1)
        
        Returns:
            makespan / 最优makespan的上界
        """
        # 下界: max(max_job, total_time/m)
        max_job = max(self.jobs)
        total_time = sum(self.jobs)
        lower_bound = max(max_job, total_time / self.m)
        
        _, makespan = self.lpt_schedule()
        
        return makespan / lower_bound if lower_bound > 0 else 1


def solve_flow_shop(jobs: List[Tuple[float, float]]) -> Tuple[List[int], float]:
    """
    流水车间调度便捷函数
    
    Args:
        jobs: [(t1, t2), ...]
    
    Returns:
        (顺序, makespan)
    """
    solver = FlowShopSolver(jobs)
    return solver.johnson_rule()


def solve_parallel_machines(num_machines: int, 
                           processing_times: List[float]) -> Tuple[List[List[int]], float]:
    """
    并行机器调度便捷函数
    
    Args:
        num_machines: 机器数量
        processing_times: 每个作业的处理时间
    
    Returns:
        (分配方案, makespan)
    """
    solver = ParallelMachineSolver(num_machines)
    for pt in processing_times:
        solver.add_job(pt)
    return solver.lpt_schedule()


# 测试代码
if __name__ == "__main__":
    # 测试1: Johnson规则
    print("测试1 - 两台机器流水车间调度:")
    jobs = [(3, 2), (4, 3), (2, 5), (5, 1)]  # (机器1时间, 机器2时间)
    
    solver = FlowShopSolver(jobs)
    order, makespan = solver.johnson_rule()
    
    print(f"  作业处理时间: {jobs}")
    print(f"  最优顺序: {order}")
    print(f"  makespan: {makespan}")
    
    # 验证:计算甘特图数据
    gantt = solver.get_gantt_data(order)
    print(f"  甘特图:")
    print(f"    作业 | 机器1开始 | 机器1结束 | 机器2结束")
    for job_id, start1, end1, end2 in gantt:
        print(f"    {job_id} | {start1:.1f} | {end1:.1f} | {end2:.1f}")
    
    # 测试2: 比较不同顺序
    print("\n测试2 - 顺序比较:")
    import itertools
    
    best_order = None
    best_makespan = float('inf')
    
    for perm in itertools.permutations(range(len(jobs))):
        ms = solver.calculate_makespan(list(perm))
        if ms < best_makespan:
            best_makespan = ms
            best_order = list(perm)
    
    print(f"  枚举最优顺序: {best_order}, makespan={best_makespan}")
    print(f"  Johnson规则: {order}, makespan={makespan}")
    
    # 测试3: 并行机器调度
    print("\n测试3 - 并行机器调度(4机器):")
    processing_times = [6, 3, 8, 2, 5, 7, 1, 4, 9, 3]
    
    solver3 = ParallelMachineSolver(4)
    for pt in processing_times:
        solver3.add_job(pt)
    
    schedule, makespan3 = solver3.lpt_schedule()
    
    print(f"  作业处理时间: {processing_times}")
    print(f"  机器数量: 4")
    print(f"  LPT调度:")
    for i, jobs_assigned in enumerate(schedule):
        load = sum(processing_times[j] for j in jobs_assigned)
        print(f"    机器{i}: 作业={jobs_assigned}, 负载={load}")
    print(f"  makespan: {makespan3}")
    print(f"  最优性比率: {solver3.lpt_optimal_ratio():.4f}")
    
    # 测试4: 大规模实例
    print("\n测试4 - 大规模实例(20作业,3机器):")
    random.seed(42)
    times_large = [random.randint(1, 20) for _ in range(20)]
    
    solver4 = ParallelMachineSolver(3)
    for t in times_large:
        solver4.add_job(t)
    
    schedule4, makespan4 = solver4.lpt_schedule()
    
    print(f"  作业时间: {times_large}")
    print(f"  LPT调度:")
    for i, jobs_assigned in enumerate(schedule4):
        load = sum(times_large[j] for j in jobs_assigned)
        assigned_times = [times_large[j] for j in jobs_assigned]
        print(f"    机器{i}: 作业数={len(jobs_assigned)}, 负载={load}, 作业={assigned_times}")
    print(f"  makespan: {makespan4}")
    
    # 测试5: 多组测试
    print("\n测试5 - 随机实例测试:")
    for trial in range(3):
        times = [random.randint(1, 15) for _ in range(15)]
        solver = ParallelMachineSolver(3)
        for t in times:
            solver.add_job(t)
        
        schedule, ms = solver.lpt_schedule()
        ratio = solver.lpt_optimal_ratio()
        
        print(f"  试用{trial+1}: makespan={ms}, 最优性比率={ratio:.4f}")
    
    print("\n所有测试完成!")

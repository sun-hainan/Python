# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / scheduling_csp

本文件实现 scheduling_csp 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class ScheduleSolver:
    """
    调度问题求解器
    将调度问题建模为CSP并求解
    """
    
    def __init__(self, num_machines: int, time_horizon: int):
        """
        初始化调度器
        
        Args:
            num_machines: 机器数量
            time_horizon: 时间范围上限
        """
        self.num_machines = num_machines
        self.time_horizon = time_horizon
        self.tasks: List[Dict] = []  # 任务列表
        self.task_vars: Dict[int, str] = {}  # 任务ID -> 变量名
        
    def add_task(self, task_id: int, duration: int, resource_type: int = 0,
                 prerequisites: List[int] = None, latest_start: Optional[int] = None):
        """
        添加任务
        
        Args:
            task_id: 任务ID
            duration: 持续时间
            resource_type: 资源类型
            prerequisites: 前置任务列表
            latest_start: 最晚开始时间
        """
        self.tasks.append({
            'id': task_id,
            'duration': duration,
            'resource_type': resource_type,
            'prerequisites': prerequisites or [],
            'latest_start': latest_start
        })
        self.task_vars[task_id] = f't{task_id}'
    
    def solve(self) -> Optional[Dict[int, int]]:
        """
        求解调度问题
        
        Returns:
            每个任务开始时间的字典或None
        """
        if not self.tasks:
            return {}
        
        # 构建CSP
        variables = [f't{task["id"]}' for task in self.tasks]
        
        # 定义域:每个任务可以在[0, time_horizon - duration]开始
        domains = {}
        for task in self.tasks:
            var = f't{task["id"]}'
            max_start = self.time_horizon - task['duration']
            domains[var] = set(range(max_start + 1))
        
        constraints = []
        
        # 时序约束:前置任务必须先完成
        for task in self.tasks:
            for prereq in task['prerequisites']:
                prereq_task = self.tasks[prereq]
                # t_prereq + duration_prereq <= t_task
                min_start = prereq_task['duration']
                constraints.append(('constraint', f't{prereq}', f't{task["id"]}', 
                                  lambda sp, st, d=min_start: sp + d <= st, 
                                  f't{prereq} + {prereq_task["duration"]} <= t{task["id"]}'))
        
        # 资源约束:同一资源类型的任务不能重叠
        by_resource = defaultdict(list)
        for task in self.tasks:
            by_resource[task['resource_type']].append(task['id'])
        
        for resource_type, task_ids in by_resource.items():
            if len(task_ids) <= 1:
                continue
            
            for i, t1 in enumerate(task_ids):
                for t2 in task_ids[i+1:]:
                    task1 = self.tasks[t1]
                    task2 = self.tasks[t2]
                    
                    # 添加非重叠约束
                    # t1 + d1 <= t2 OR t2 + d2 <= t1
                    d1, d2 = task1['duration'], task2['duration']
                    
                    constraints.append(('or_constraint', 
                                      f't{t1}', f't{t2}', d1, d2,
                                      f't{t1}+{d1}<=t{t2} OR t{t2}+{d2}<=t{t1}'))
        
        # 最晚开始时间约束
        for task in self.tasks:
            if task['latest_start'] is not None:
                constraints.append(('ub', f't{task["id"]}', task['latest_start'],
                                  f't{task["id"]} <= {task["latest_start"]}'))
        
        # CSP求解(简化版,使用回溯)
        return self.backtrack_solve(variables, domains, constraints)
    
    def backtrack_solve(self, variables: List[str], 
                       domains: Dict[str, Set[int]],
                       constraints: List) -> Optional[Dict[int, int]]:
        """
        回溯求解
        
        Args:
            variables: 变量列表
            domains: 定义域
            constraints: 约束列表
        
        Returns:
            调度方案
        """
        assignment: Dict[str, int] = {}
        
        def is_consistent(var: str, value: int) -> bool:
            assignment[var] = value
            
            for constr in constraints:
                if constr[0] == 'constraint':
                    _, v1, v2, pred, _ = constr
                    if v1 in assignment and v2 in assignment:
                        if not pred(assignment[v1], assignment[v2]):
                            return False
                
                elif constr[0] == 'or_constraint':
                    _, v1, v2, d1, d2, _ = constr
                    if v1 in assignment and v2 in assignment:
                        cond1 = assignment[v1] + d1 <= assignment[v2]
                        cond2 = assignment[v2] + d2 <= assignment[v1]
                        if not (cond1 or cond2):
                            return False
                
                elif constr[0] == 'ub':
                    _, v, ub, _ = constr
                    if v in assignment and assignment[v] > ub:
                        return False
            
            return True
        
        def select_var() -> Optional[str]:
            unassigned = [v for v in variables if v not in assignment]
            if not unassigned:
                return None
            return min(unassigned, key=lambda v: len(domains[v]))
        
        def backtrack() -> bool:
            var = select_var()
            if var is None:
                return True
            
            for value in sorted(domains[var]):
                if is_consistent(var, value):
                    if backtrack():
                        return True
                    del assignment[var]
            
            return False
        
        if backtrack():
            # 转换结果为任务ID -> 开始时间
            result = {}
            for task in self.tasks:
                var = f't{task["id"]}'
                if var in assignment:
                    result[task['id']] = assignment[var]
            return result
        
        return None
    
    def makespan(self, schedule: Dict[int, int]) -> int:
        """
        计算总完工时间
        
        Args:
            schedule: 调度方案
        
        Returns:
            总完工时间
        """
        max_end = 0
        for task in self.tasks:
            start = schedule.get(task['id'], 0)
            end = start + task['duration']
            max_end = max(max_end, end)
        return max_end


def solve_job_shop(jobs: List[List[Tuple[int, int]]], num_machines: int) -> Optional[Dict[int, int]]:
    """
    作业车间调度问题(简化版)
    
    Args:
        jobs: 每个作业的任务列表,每任务为(机器ID, 持续时间)
        num_machines: 机器数量
    
    Returns:
        调度方案
    """
    solver = ScheduleSolver(num_machines, time_horizon=100)
    
    task_id = 0
    all_tasks = []
    
    for job_id, tasks in enumerate(jobs):
        prev_task = None
        for machine_id, duration in tasks:
            solver.add_task(task_id, duration, resource_type=machine_id,
                          prerequisites=[prev_task] if prev_task is not None else [])
            all_tasks.append({
                'id': task_id,
                'job': job_id,
                'machine': machine_id,
                'duration': duration
            })
            prev_task = task_id
            task_id += 1
    
    schedule = solver.solve()
    if schedule:
        return schedule, solver.makespan(schedule)
    return None


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单调度问题
    print("测试1 - 简单调度问题:")
    solver = ScheduleSolver(num_machines=2, time_horizon=20)
    
    # 任务0: 持续3, 资源0
    # 任务1: 持续4, 资源0, 依赖任务0
    # 任务2: 持续2, 资源1
    # 任务3: 持续3, 资源1, 依赖任务2
    solver.add_task(0, 3, resource_type=0)
    solver.add_task(1, 4, resource_type=0, prerequisites=[0])
    solver.add_task(2, 2, resource_type=1)
    solver.add_task(3, 3, resource_type=1, prerequisites=[2])
    
    schedule = solver.solve()
    print(f"  调度方案: {schedule}")
    print(f"  总完工时间: {solver.makespan(schedule)}")
    
    # 测试2: 复杂调度
    print("\n测试2 - 复杂调度:")
    solver2 = ScheduleSolver(num_machines=3, time_horizon=50)
    
    solver2.add_task(0, 5, resource_type=0)      # 任务0
    solver2.add_task(1, 3, resource_type=1)      # 任务1
    solver2.add_task(2, 4, resource_type=2)     # 任务2
    solver2.add_task(3, 2, resource_type=0, prerequisites=[0])  # 任务3,依赖0
    solver2.add_task(4, 3, resource_type=1, prerequisites=[1])  # 任务4,依赖1
    solver2.add_task(5, 4, resource_type=2, prerequisites=[2])  # 任务5,依赖2
    solver2.add_task(6, 2, resource_type=0, prerequisites=[3, 4])  # 任务6,依赖3,4
    solver2.add_task(7, 3, resource_type=1, prerequisites=[4, 5])  # 任务7,依赖4,5
    
    schedule2 = solver2.solve()
    print(f"  调度方案: {schedule2}")
    print(f"  总完工时间: {solver2.makespan(schedule2)}")
    
    # 验证约束
    print("\n  验证:")
    for task in solver2.tasks:
        if task['prerequisites']:
            for prereq in task['prerequisites']:
                start = schedule2[task['id']]
                prereq_end = schedule2[prereq] + solver2.tasks[prereq]['duration']
                print(f"    任务{prereq}结束={prereq_end}, 任务{task['id']}开始={start}, 满足={prereq_end <= start}")
    
    # 测试3: 作业车间调度
    print("\n测试3 - 作业车间调度:")
    # 作业1: 机器0(持续3) -> 机器1(持续4) -> 机器2(持续2)
    # 作业2: 机器1(持续3) -> 机器2(持续2) -> 机器0(持续4)
    # 作业3: 机器2(持续4) -> 机器0(持续3) -> 机器1(持续2)
    
    jobs = [
        [(0, 3), (1, 4), (2, 2)],
        [(1, 3), (2, 2), (0, 4)],
        [(2, 4), (0, 3), (1, 2)],
    ]
    
    result = solve_job_shop(jobs, num_machines=3)
    if result:
        schedule, makespan = result
        print(f"  调度方案: {schedule}")
        print(f"  总完工时间: {makespan}")
    
    print("\n所有测试完成!")

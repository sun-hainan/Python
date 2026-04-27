# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / resource_allocation



本文件实现 resource_allocation 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

import itertools





class ResourceAllocationSolver:

    """

    资源分配问题求解器

    给定任务和资源约束,找到最优分配方案

    """

    

    def __init__(self, num_resources: int):

        """

        初始化求解器

        

        Args:

            num_resources: 资源数量

        """

        self.num_resources = num_resources

        self.tasks: List[Dict] = []

        self.preferences: Dict[int, List[int]] = {}  # 任务ID -> 偏好资源列表

    

    def add_task(self, task_id: int, required_resources: List[int] = None,

                 skill_level: int = 1):

        """

        添加任务

        

        Args:

            task_id: 任务ID

            required_resources: 任务需要的资源类型列表

            skill_level: 需要的技能等级

        """

        self.tasks.append({

            'id': task_id,

            'required_resources': required_resources or [],

            'skill_level': skill_level

        })

    

    def set_preference(self, task_id: int, resource_list: List[int]):

        """设置任务对资源的偏好"""

        self.preferences[task_id] = resource_list

    

    def solve_greedy(self) -> Dict[int, int]:

        """

        贪心求解:为每个任务分配最偏好的可用资源

        

        Returns:

            分配方案 {任务ID: 资源ID}

        """

        allocation = {}

        resource_usage = [0] * self.num_resources

        

        # 按偏好优先级处理任务

        for task_id, pref in sorted(self.preferences.items(), 

                                   key=lambda x: len(x[1])):

            task = self.tasks[task_id]

            

            # 遍历偏好资源

            for resource_id in pref:

                # 检查资源是否可用(未被完全占用)

                # 这里简化:每个资源同一时间只能被一个任务使用

                if resource_usage[resource_id] == 0:

                    allocation[task_id] = resource_id

                    resource_usage[resource_id] = 1

                    break

        

        return allocation

    

    def solve_exhaustive(self) -> Optional[Dict[int, int]]:

        """

        穷举求解:尝试所有可能的分配

        

        Returns:

            最优分配方案

        """

        if len(self.tasks) > self.num_resources:

            return None  # 任务多于资源,不可能全部分配

        

        best_allocation = None

        best_score = -1

        

        # 遍历资源的所有排列

        resources = list(range(self.num_resources))

        

        for perm in itertools.permutations(resources, len(self.tasks)):

            allocation = {self.tasks[i]['id']: perm[i] for i in range(len(self.tasks))}

            

            # 检查约束

            if self.is_valid(allocation):

                score = self.calculate_score(allocation)

                if score > best_score:

                    best_score = score

                    best_allocation = allocation

        

        return best_allocation

    

    def is_valid(self, allocation: Dict[int, int]) -> bool:

        """检查分配是否有效"""

        used_resources = set()

        

        for task_id, resource_id in allocation.items():

            task = self.tasks[task_id]

            

            # 检查资源类型是否满足

            if task['required_resources']:

                if resource_id not in task['required_resources']:

                    return False

            

            # 检查资源冲突

            if resource_id in used_resources:

                return False

            used_resources.add(resource_id)

        

        return True

    

    def calculate_score(self, allocation: Dict[int, int]) -> int:

        """计算分配方案的分数"""

        score = 0

        

        for task_id, resource_id in allocation.items():

            pref = self.preferences.get(task_id, [])

            if pref:

                # 偏好越靠前分数越高

                if resource_id in pref:

                    score += len(pref) - pref.index(resource_id)

                else:

                    score -= 10  # 未使用偏好资源

        

        return score

    

    def solve_assignment(self) -> Optional[Dict[int, int]]:

        """

        求解最优分配问题

        使用匈牙利算法的思想(如果问题可以建模为二分图匹配)

        

        Returns:

            最优分配

        """

        # 检查是否为二分图匹配问题

        if len(self.tasks) > self.num_resources:

            return None

        

        # 简化为:每个任务只分配一个资源,每个资源最多分配给一个任务

        # 使用贪心+局部搜索

        

        best_allocation = None

        best_score = -1

        

        # 尝试不同的初始分配

        from itertools import permutations

        

        task_ids = [t['id'] for t in self.tasks]

        

        for perm in permutations(range(self.num_resources), len(task_ids)):

            allocation = dict(zip(task_ids, perm))

            

            if self.is_valid(allocation):

                score = self.calculate_score(allocation)

                if score > best_score:

                    best_score = score

                    best_allocation = allocation.copy()

        

        return best_allocation





class MultiPeriodAllocator:

    """

    多时段资源分配

    资源可以在不同时段分配给不同任务

    """

    

    def __init__(self, num_resources: int, num_periods: int):

        """

        初始化

        

        Args:

            num_resources: 资源数量

            num_periods: 时间段数量

        """

        self.num_resources = num_resources

        self.num_periods = num_periods

        self.assignments: List[Tuple[int, int, int]] = []  # (resource, period, task)

    

    def add_assignment(self, resource: int, period: int, task: int, duration: int):

        """添加资源分配"""

        self.assignments.append((resource, period, task, duration))

    

    def solve(self) -> List[Tuple[int, int, int, int]]:

        """

        求解多时段分配

        

        Returns:

            分配列表 (resource, period, task, duration)

        """

        # 简化为:每个资源在每个时段只能做一个任务

        # 使用回溯求解

        

        schedule = []

        resource_period_usage = {(r, p): None for r in range(self.num_resources) 

                                 for p in range(self.num_periods)}

        

        def backtrack(idx: int) -> bool:

            if idx == len(self.assignments):

                return True

            

            resource, period, task, duration = self.assignments[idx]

            

            # 尝试分配

            for d in range(duration):

                if period + d >= self.num_periods:

                    break

                if resource_period_usage.get((resource, period + d)) is not None:

                    break

            else:

                # 成功分配

                for d in range(duration):

                    resource_period_usage[(resource, period + d)] = task

                schedule.append((resource, period, task, duration))

                

                if backtrack(idx + 1):

                    return True

                

                # 回溯

                for d in range(duration):

                    resource_period_usage[(resource, period + d)] = None

                schedule.pop()

            

            return False

        

        if backtrack(0):

            return schedule

        return None





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单资源分配

    print("测试1 - 简单资源分配:")

    solver = ResourceAllocationSolver(num_resources=5)

    

    # 添加任务

    for i in range(4):

        solver.add_task(i, required_resources=[])

        solver.set_preference(i, [0, 1, 2])  # 所有任务都偏好资源0,1,2

    

    allocation = solver.solve_exhaustive()

    print(f"  最优分配: {allocation}")

    print(f"  分数: {solver.calculate_score(allocation) if allocation else 0}")

    

    # 测试2: 带约束的资源分配

    print("\n测试2 - 带约束的资源分配:")

    solver2 = ResourceAllocationSolver(num_resources=4)

    

    solver2.add_task(0, required_resources=[0, 1])  # 任务0需要资源0或1

    solver2.add_task(1, required_resources=[1, 2])  # 任务1需要资源1或2

    solver2.add_task(2, required_resources=[2, 3])  # 任务2需要资源2或3

    solver2.add_task(3, required_resources=[0, 3])  # 任务3需要资源0或3

    

    solver2.set_preference(0, [0, 1])

    solver2.set_preference(1, [1, 2])

    solver2.set_preference(2, [2, 3])

    solver2.set_preference(3, [3, 0])

    

    allocation2 = solver2.solve_exhaustive()

    print(f"  最优分配: {allocation2}")

    

    # 测试3: 多时段分配

    print("\n测试3 - 多时段资源分配:")

    multi_solver = MultiPeriodAllocator(num_resources=2, num_periods=5)

    

    # 任务1: 资源0,时段0,持续2

    multi_solver.add_assignment(0, 0, 1, 2)

    # 任务2: 资源0,时段1,持续2

    multi_solver.add_assignment(0, 1, 2, 2)

    # 任务3: 资源1,时段0,持续3

    multi_solver.add_assignment(1, 0, 3, 3)

    # 任务4: 资源1,时段2,持续2

    multi_solver.add_assignment(1, 2, 4, 2)

    

    schedule = multi_solver.solve()

    if schedule:

        print(f"  调度方案:")

        for res, period, task, dur in schedule:

            print(f"    资源{res}, 时段{period}-{period+dur}, 任务{task}")

    else:

        print("  无解")

    

    # 测试4: 使用贪心求解

    print("\n测试4 - 贪心 vs 穷举:")

    solver3 = ResourceAllocationSolver(num_resources=10)

    

    import random

    random.seed(42)

    

    for i in range(6):

        solver3.add_task(i)

        pref = list(range(10))

        random.shuffle(pref)

        solver3.set_preference(i, pref[:3])  # 每个任务有3个偏好

    

    greedy_alloc = solver3.solve_greedy()

    print(f"  贪心分配: {greedy_alloc}, 分数={solver3.calculate_score(greedy_alloc)}")

    

    exhaustive_alloc = solver3.solve_exhaustive()

    print(f"  穷举分配: {exhaustive_alloc}, 分数={solver3.calculate_score(exhaustive_alloc)}")

    

    print("\n所有测试完成!")


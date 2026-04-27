# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / hungarian_algorithm



本文件实现 hungarian_algorithm 相关的算法功能。

"""



import sys

from typing import List, Tuple, Optional





class HungarianSolver:

    """

    匈牙利算法求解器

    用于求解分配问题的最优解

    """

    

    def __init__(self, cost_matrix: List[List[float]], maximize: bool = False):

        """

        初始化求解器

        

        Args:

            cost_matrix: 成本矩阵,行列分别对应工人和任务

            maximize: True为最大化收益,False为最小化成本

        """

        self.n = len(cost_matrix)

        self.m = len(cost_matrix[0]) if cost_matrix else 0

        

        # 确保方阵

        size = max(self.n, self.m)

        self.size = size

        

        # 构建方阵(扩展到方阵)

        self.cost = [[0.0] * size for _ in range(size)]

        for i in range(size):

            for j in range(size):

                if i < self.n and j < self.m:

                    val = cost_matrix[i][j]

                    if maximize:

                        # 最大化转为最小化

                        self.cost[i][j] = -val

                    else:

                        self.cost[i][j] = val

                else:

                    self.cost[i][j] = 0  # 填充0作为dummy

        

        # 标记是否已匹配

        self.u = [0] * (size + 1)  # 顶标记

        self.v = [0] * (size + 1)  # 底标记

        self.p = [0] * (size + 1)  # 匹配结果

        self.way = [0] * (size + 1)

    

    def solve(self) -> Tuple[List[int], float]:

        """

        求解最优分配

        

        Returns:

            (匹配结果,p[i]表示将工人i分配给任务p[i]], 最小成本)

        """

        n = self.size

        

        # 匈牙利算法核心

        for i in range(1, n + 1):

            # 第i个工人开始找匹配

            self.p[0] = i

            

            # 初始距离

            minv = [float('inf')] * (n + 1)

            used = [False] * (n + 1)

            j0 = 0  # 上一次匹配的列

            

            while self.p[j0] != 0:

                used[j0] = True

                i0 = self.p[j0]  # 当前工人

                delta = float('inf')

                j1 = 0  # 下一个列

                

                for j in range(1, n + 1):

                    if not used[j]:

                        # 计算新的可行距离

                        cur = self.cost[i0 - 1][j - 1] - self.u[i0] - self.v[j]

                        

                        if cur < minv[j]:

                            minv[j] = cur

                            self.way[j] = j0

                        

                        if minv[j] < delta:

                            delta = minv[j]

                            j1 = j

                

                # 更新对偶变量

                for j in range(n + 1):

                    if used[j]:

                        self.u[self.p[j]] += delta

                        v[j] -= delta

                    else:

                        minv[j] -= delta

                

                j0 = j1

            

            # 回溯更新匹配

            while j0 != 0:

                j1 = self.way[j0]

                self.p[j0] = self.p[j1]

                j0 = j1

        

        # 提取结果

        assignment = [0] * n

        for j in range(1, n + 1):

            if self.p[j] != 0:

                assignment[self.p[j] - 1] = j - 1

        

        # 计算总成本

        total_cost = -self.v[0]

        

        # 还原为实际大小

        actual_assignment = assignment[:self.n]

        

        return actual_assignment, total_cost

    

    def get_cost(self) -> float:

        """获取最优解的成本"""

        assignment, cost = self.solve()

        return cost





def solve_assignment(cost_matrix: List[List[float]], 

                    maximize: bool = False) -> Tuple[List[int], float]:

    """

    分配问题求解便捷函数

    

    Args:

        cost_matrix: 成本矩阵

        maximize: True为最大化

    

    Returns:

        (最优分配, 成本/收益)

    """

    solver = HungarianSolver(cost_matrix, maximize)

    return solver.solve()





def solve_assignment_with_forbidden(cost_matrix: List[List[float]],

                                    forbidden: List[Tuple[int, int]],

                                    penalty: float = 1e9) -> Optional[Tuple[List[int], float]]:

    """

    带有禁止配对的分配问题

    

    Args:

        cost_matrix: 成本矩阵

        forbidden: 禁止配对的列表

        penalty: 惩罚值(一个大数)

    

    Returns:

        解或None

    """

    n = len(cost_matrix)

    m = len(cost_matrix[0])

    

    # 添加惩罚

    new_matrix = [row[:] for row in cost_matrix]

    for i, j in forbidden:

        new_matrix[i][j] += penalty

    

    solver = HungarianSolver(new_matrix)

    assignment, cost = solver.solve()

    

    # 检查是否使用了禁止配对

    for i, j in zip(range(n), assignment[:n]):

        if (i, j) in forbidden:

            return None

    

    return assignment[:n], cost





# 测试代码

if __name__ == "__main__":

    # 测试1: 最小成本分配

    print("测试1 - 最小成本分配:")

    cost_matrix = [

        [9, 2, 7, 8],

        [6, 4, 3, 7],

        [5, 8, 1, 8],

        [7, 6, 9, 4]

    ]

    

    assignment, cost = solve_assignment(cost_matrix)

    print(f"  成本矩阵:")

    for row in cost_matrix:

        print(f"    {row}")

    print(f"  最优分配: {assignment}")

    print(f"  最小成本: {cost}")

    

    # 验证

    total = sum(cost_matrix[i][assignment[i]] for i in range(len(assignment)))

    print(f"  验证成本: {total}")

    

    # 测试2: 最大收益分配

    print("\n测试2 - 最大收益分配:")

    profit_matrix = [

        [9, 2, 7, 8],

        [6, 4, 3, 7],

        [5, 8, 1, 8],

        [7, 6, 9, 4]

    ]

    

    assignment2, profit = solve_assignment(profit_matrix, maximize=True)

    print(f"  收益矩阵:")

    for row in profit_matrix:

        print(f"    {row}")

    print(f"  最优分配: {assignment2}")

    print(f"  最大收益: {profit}")

    

    # 测试3: 非方阵

    print("\n测试3 - 非方阵(3工人,4任务):")

    cost_matrix3 = [

        [9, 2, 7, 8],

        [6, 4, 3, 7],

        [5, 8, 1, 8]

    ]

    

    solver3 = HungarianSolver(cost_matrix3)

    assignment3, cost3 = solver3.solve()

    print(f"  分配: {assignment3[:3]}")  # 只取前3个有效结果

    print(f"  成本: {cost3}")

    

    # 测试4: 工人多于任务

    print("\n测试4 - 工人多于任务(4工人,2任务):")

    cost_matrix4 = [

        [9, 2],

        [6, 4],

        [5, 8],

        [7, 6]

    ]

    

    solver4 = HungarianSolver(cost_matrix4)

    assignment4, cost4 = solver4.solve()

    print(f"  分配: {assignment4[:4]}")

    print(f"  成本: {cost4}")

    

    # 测试5: 带有禁止配对

    print("\n测试5 - 带有禁止配对:")

    cost_matrix5 = [

        [9, 2, 7],

        [6, 4, 3],

        [5, 8, 1]

    ]

    forbidden = [(0, 0), (2, 1)]  # 工人0不能做任务0,工人2不能做任务1

    

    result = solve_assignment_with_forbidden(cost_matrix5, forbidden)

    if result:

        print(f"  分配: {result[0]}")

        print(f"  成本: {result[1]}")

    else:

        print("  无解(所有解都使用了禁止配对)")

    

    # 测试6: 实际应用 - 工作分配

    print("\n测试6 - 工作分配问题:")

    # 4个工人,4项工作,每工人每工作有成本

    workers = ['张三', '李四', '王五', '赵六']

    jobs = ['工作A', '工作B', '工作C', '工作D']

    

    worker_job_cost = [

        [15, 8, 12, 10],  # 张三

        [9, 12, 6, 14],   # 李四

        [10, 14, 8, 7],   # 王五

        [6, 7, 12, 11]    # 赵六

    ]

    

    assignment6, total_cost = solve_assignment(worker_job_cost)

    print(f"  工人-工作成本:")

    for i, row in enumerate(worker_job_cost):

        print(f"    {workers[i]}: {dict(zip(jobs, row))}")

    

    print(f"\n  最优分配:")

    for i, job_idx in enumerate(assignment6):

        print(f"    {workers[i]} -> {jobs[job_idx]}, 成本={worker_job_cost[i][job_idx]}")

    print(f"  总成本: {total_cost}")

    

    print("\n所有测试完成!")


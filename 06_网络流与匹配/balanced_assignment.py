# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / balanced_assignment

本文件实现 balanced_assignment 相关的算法功能。
"""

import sys


def hungarian_algorithm(cost_matrix):
    """
    匈牙利算法求解最小成本分配问题
    
    参数：
        cost_matrix: n×n 成本矩阵
    
    返回：
        (min_cost, assignment)
        其中 assignment[i] = j 表示将工人 i 分配给工作 j
    """
    n = len(cost_matrix)
    if n == 0:
        return 0, []
    
    # 复制矩阵避免修改原数据
    cost = [row[:] for row in cost_matrix]
    
    # u[i]: 行的势（潜在减量）
    u = [0] * (n + 1)
    # v[j]: 列的势（潜在增量）
    v = [0] * (n + 1)
    # p[j]: 匹配到列 j 的行号
    p = [0] * (n + 1)
    # way[j]: 列 j 的前驱用于重建路径
    way = [0] * (n + 1)
    
    for i in range(1, n + 1):
        # 为第 i 行找匹配
        p[0] = i
        
        minv = [float('inf')] * (n + 1)  # 各列到当前增广路的最小代价
        used = [False] * (n + 1)
        j0 = 0  # 当前列
        
        while p[j0] != 0:
            used[j0] = True
            i0 = p[j0]  # 当前行的工人
            delta = float('inf')
            j1 = 0  # 下一列
            
            for j in range(1, n + 1):
                if not used[j]:
                    # 计算通过当前增广路到列 j 的成本
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            
            # 更新势
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            
            j0 = j1
        
        # 增广：沿增广路修改匹配
        while j0 != 0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    
    # p[j] = i 表示列 j 匹配行 i（工人 i -> 工作 j）
    assignment = [0] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    
    min_cost = -v[0]  # 最小成本
    
    return min_cost, assignment


def build_example():
    """构建一个 4×4 的成本矩阵示例"""
    # 工人0-3，任务0-3
    # 成本矩阵：cost[i][j] = 工人 i 做任务 j 的成本
    cost_matrix = [
        [9, 2, 7, 8],   # 工人0
        [6, 4, 3, 7],   # 工人1
        [5, 8, 1, 8],   # 工人2
        [7, 6, 9, 4],   # 工人3
    ]
    return cost_matrix


def print_assignment(cost_matrix, assignment):
    """打印分配方案和成本明细"""
    n = len(assignment)
    print("\n分配方案：")
    total = 0
    for worker, task in enumerate(assignment):
        cost = cost_matrix[worker][task]
        total += cost
        print(f"  工人 {worker} -> 任务 {task}，成本 = {cost}")
    print(f"\n总成本 = {total}")


if __name__ == "__main__":
    print("=" * 55)
    print("平衡分配问题 - 匈牙利算法")
    print("=" * 55)
    
    cost_matrix = build_example()
    
    print("\n成本矩阵：")
    for i, row in enumerate(cost_matrix):
        print(f"  工人{i}: {row}")
    
    min_cost, assignment = hungarian_algorithm(cost_matrix)
    
    print_assignment(cost_matrix, assignment)
    print(f"最优成本 = {min_cost}")
    
    # 验证
    n = len(cost_matrix)
    assigned_tasks = set(assignment)
    print(f"\n验证：分配了 {len(assigned_tasks)} 个不同任务",
          "✓" if len(assigned_tasks) == n else "✗")

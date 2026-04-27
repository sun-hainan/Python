# -*- coding: utf-8 -*-
"""
算法实现：随机算法 / monte_carlo_np

本文件实现 monte_carlo_np 相关的算法功能。
"""

import random
import time
from typing import List, Tuple, Callable


class MonteCarloSolver:
    """Monte Carlo求解器"""

    def __init__(self, max_iterations: int = 10000):
        """
        参数：
            max_iterations: 最大迭代次数
        """
        self.max_iter = max_iterations

    def max_cut_approx(self, graph: List[List[int]]) -> Tuple[List[int], int]:
        """
        Max Cut问题的随机近似

        参数：
            graph: 邻接表

        返回：(分割, 边数)
        """
        n = len(graph)

        # 随机分割
        partition = [random.randint(0, 1) for _ in range(n)]

        # 计算割的大小
        cut_size = 0
        for i in range(n):
            for j in graph[i]:
                if j > i and partition[i] != partition[j]:
                    cut_size += 1

        return partition, cut_size

    def sat_solver(self, clauses: List[List[int]],
                  n_vars: int,
                  max_attempts: int = 1000) -> Tuple[bool, List[int]]:
        """
        SAT问题的随机求解

        参数：
            clauses: 子句列表
            n_vars: 变量数
            max_attempts: 最大尝试次数

        返回：(是否找到解, 赋值)
        """
        for _ in range(max_attempts):
            # 随机赋值
            assignment = [random.randint(0, 1) for _ in range(n_vars)]

            # 检查是否满足所有子句
            satisfied = True
            for clause in clauses:
                clause_satisfied = any(assignment[abs(lit)-1] == (lit > 0)
                                      for lit in clause)
                if not clause_satisfied:
                    satisfied = False
                    break

            if satisfied:
                return True, assignment

        return False, []

    def tsp_approx(self, distances: List[List[float]]) -> Tuple[List[int], float]:
        """
        TSP问题的随机近似（2-opt改进）

        参数：
            distances: 距离矩阵

        返回：(路径, 总距离)
        """
        n = len(distances)

        # 随机初始路径
        path = list(range(n))
        random.shuffle(path)

        current_distance = self._path_distance(path, distances)

        # 尝试改进
        for _ in range(self.max_iter):
            # 随机交换
            i, j = random.sample(range(n), 2)
            new_path = path.copy()
            new_path[i], new_path[j] = new_path[j], new_path[i]

            new_distance = self._path_distance(new_path, distances)

            if new_distance < current_distance:
                path = new_path
                current_distance = new_distance

        return path, current_distance

    def _path_distance(self, path: List[int], distances: List[List[float]]) -> float:
        """计算路径总距离"""
        total = 0
        for i in range(len(path)):
            total += distances[path[i]][path[(i+1) % len(path)]]
        return total


def monte_carlo_analysis():
    """Monte Carlo分析"""
    print("=== Monte Carlo分析 ===")
    print()
    print("特点：")
    print("  - 运行时间确定")
    print("  - 解的正确性有概率保证")
    print("  - 适合难以精确求解的问题")
    print()
    print("应用：")
    print("  - Max Cut: 0.5-近似")
    print("  - SAT: 指数时间但实用")
    print("  - TSP: 启发式改进")
    print()
    print("Las Vegas变体：")
    print("  - 保证正确但时间不确定")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Monte Carlo方法测试 ===\n")

    random.seed(42)

    mc = MonteCarloSolver(max_iterations=1000)

    # Max Cut
    print("Max Cut问题：")
    graph = [[1, 2], [0, 2], [0, 1, 3], [2, 4], [3]]  # 5个节点的图
    partition, cut = mc.max_cut_approx(graph)
    print(f"  图: {graph}")
    print(f"  分割: {partition}")
    print(f"  割大小: {cut}")
    print()

    # SAT
    print("SAT问题：")
    # (x1 OR x2) AND (NOT x1 OR x3)
    clauses = [[1, 2], [-1, 3]]
    n_vars = 3
    found, assignment = mc.sat_solver(clauses, n_vars, max_attempts=100)
    print(f"  子句: {clauses}")
    print(f"  找到解: {found}")
    if found:
        print(f"  赋值: {assignment}")
    print()

    # TSP
    print("TSP问题：")
    n_cities = 5
    distances = [[0, 10, 20, 30, 40],
                 [10, 0, 15, 25, 35],
                 [20, 15, 0, 30, 25],
                 [30, 25, 30, 0, 15],
                 [40, 35, 25, 15, 0]]
    path, dist = mc.tsp_approx(distances)
    print(f"  城市数: {n_cities}")
    print(f"  最优路径: {path}")
    print(f"  距离: {dist}")

    print()
    monte_carlo_analysis()

    print()
    print("说明：")
    print("  - Monte Carlo是重要的随机算法")
    print("  - 在优化和搜索中有广泛应用")
    print("  - 通常比确定性算法更简单")

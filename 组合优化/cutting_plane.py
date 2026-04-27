# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / cutting_plane

本文件实现 cutting_plane 相关的算法功能。
"""

from typing import List, Tuple
import math


class CuttingPlaneMethod:
    """割平面法"""

    def __init__(self):
        pass

    def solve_relaxation(self, objective: List[float],
                        constraints: List[List[float]]) -> Tuple[List[float], float]:
        """
        求解线性规划松弛

        参数：
            objective: 目标函数系数
            constraints: 约束矩阵

        返回：(最优解, 最优值)
        """
        # 简化：使用简单方法
        n = len(objective)

        # 初始解
        x = [0.0] * n
        for i in range(n):
            x[i] = 1.0 / n

        # 简化价值
        obj_value = sum(o * xi for o, xi in zip(objective, x))

        return x, obj_value

    def add_gomory_cut(self, solution: List[float],
                      constraint: List[float],
                      rhs: float) -> List[float]:
        """
        添加Gomory割

        参数：
            solution: 当前解
            constraint: 约束
            rhs: 约束右端

        返回：新的割平面
        """
        # Gomory割的简化版本
        cut = []
        fractional_part = []

        for coeff, xi in zip(constraint, solution):
            # 取小数部分
            frac = coeff - math.floor(coeff)
            fractional_part.append(frac)

        # 构建割
        for frac in fractional_part:
            cut.append(frac)

        return cut

    def iterative_cutting(self, objective: List[float],
                         constraints: List[List[float]],
                         max_iter: int = 20) -> Tuple[List[float], float]:
        """
        迭代割平面

        参数：
            objective: 目标函数
            constraints: 约束
            max_iter: 最大迭代次数

        返回：（解, 值）
        """
        current_constraints = constraints.copy()
        all_cuts = []

        for iteration in range(max_iter):
            # 求解当前LP
            sol, val = self.solve_relaxation(objective, current_constraints)

            # 检查是否整数
            is_integer = all(abs(s - round(s)) < 1e-6 for s in sol)

            if is_integer:
                return sol, val

            # 添加割平面
            # 简化：添加最接近的割
            for i, c in enumerate(current_constraints[:3]):
                cut = self.add_gomory_cut(sol, c, 1.0)
                all_cuts.append(cut)

            current_constraints.append(all_cuts[-1] if all_cuts else [])

        return sol, val


def gomory_cut():
    """Gomory割"""
    print("=== Gomory割 ===")
    print()
    print("整数规划：")
    print("  min c^T x")
    print("  s.t. Ax = b")
    print("       x ≥ 0, 整数")
    print()
    print("Gomory割：")
    print("  - 从LP松弛的最优表中提取")
    print("  - 消除分数解")
    print("  - 迭代直到找到整数解")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 割平面法测试 ===\n")

    cpm = CuttingPlaneMethod()

    # 简单问题
    objective = [1, 1]  # min x1 + x2
    constraints = [
        [2, 1],   # 2x1 + x2 ≥ 3
        [1, 2],   # x1 + 2x2 ≥ 3
    ]

    print(f"目标: min {objective[0]}x1 + {objective[1]}x2")
    print("约束:")
    for c in constraints:
        print(f"  {c[0]}x1 + {c[1]}x2 ≥ 3")

    print()

    # 求解
    sol, val = cpm.iterative_cutting(objective, constraints)

    print(f"解: x1={sol[0]:.2f}, x2={sol[1]:.2f}")
    print(f"值: {val:.2f}")

    print()
    gomory_cut()

    print()
    print("说明：")
    print("  - 割平面法是整数规划的核心方法")
    print("  - Branch and Cut结合了分支定界")
    print("  - CPLEX、Gurobi等求解器使用此技术")

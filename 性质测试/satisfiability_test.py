# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / satisfiability_test

本文件实现 satisfiability_test 相关的算法功能。
"""

import random
from typing import List, Tuple


class SATSolver:
    """SAT求解器（简化）"""

    def __init__(self, n_vars: int):
        """
        参数：
            n_vars: 变量数
        """
        self.n_vars = n_vars
        self.clauses = []

    def add_clause(self, clause: List[int]) -> None:
        """
        添加子句

        参数：
            clause: 文字列表，正数表示xi，负数表示NOT xi
        """
        self.clauses.append(clause)

    def evaluate(self, assignment: List[int]) -> bool:
        """
        评估赋值

        返回：公式是否为真
        """
        for clause in self.clauses:
            clause_true = False

            for literal in clause:
                if literal > 0:
                    if assignment[literal - 1] == 1:
                        clause_true = True
                        break
                else:
                    var = -literal
                    if assignment[var - 1] == 0:
                        clause_true = True
                        break

            if not clause_true:
                return False

        return True

    def random_walk_solve(self, max_attempts: int = 1000) -> Tuple[bool, List[int]]:
        """
        随机游走求解（概率算法）

        返回：(是否有解, 赋值)
        """
        for attempt in range(max_attempts):
            # 随机赋值
            assignment = [random.randint(0, 1) for _ in range(self.n_vars)]

            if self.evaluate(assignment):
                return True, assignment

            # GSAT风格：翻转导致最多假子句的变量
            best_var = 1
            best_satisfied = 0

            for var in range(1, self.n_vars + 1):
                # 尝试翻转
                test_assign = assignment.copy()
                test_assign[var - 1] ^= 1

                # 计算满足的子句数
                satisfied = sum(1 for c in self.clauses
                              if any((literal > 0 and test_assign[literal - 1] == 1) or
                                     (literal < 0 and test_assign[-literal - 1] == 0)
                                     for literal in c))

                if satisfied > best_satisfied:
                    best_satisfied = satisfied
                    best_var = var

            # 翻转最佳变量
            assignment[best_var - 1] ^= 1

        return False, []

    def brute_force_solve(self) -> Tuple[bool, List[int]]:
        """
        暴力求解（小规模）

        返回：(是否有解, 赋值)
        """
        from itertools import product

        n_assignments = 2 ** self.n_vars

        for assignment in product([0, 1], repeat=self.n_vars):
            if self.evaluate(list(assignment)):
                return True, list(assignment)

        return False, []


def sat_complexity():
    """SAT复杂度"""
    print("=== SAT复杂度 ===")
    print()
    print("问题：")
    print("  - 3-SAT是NP-完全")
    print("  - 变量数 n 指数级搜索空间")
    print()
    print("算法：")
    print("  - 暴力：O(2^n)")
    print("  - 随机游走：概率多项式")
    print("  - CDCL：现代SMT求解器")
    print()
    print("应用：")
    print("  - 计划调度")
    print("  - 硬件验证")
    print("  - 人工智能")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== SAT可满足性测试 ===\n")

    # 创建SAT实例：(x1 OR NOT x2) AND (x2 OR x3) AND (NOT x1 OR NOT x3)
    sat = SATSolver(3)

    sat.add_clause([1, -2])   # x1 OR NOT x2
    sat.add_clause([2, 3])    # x2 OR x3
    sat.add_clause([-1, -3]) # NOT x1 OR NOT x3

    print("公式:")
    print("  (x1 OR NOT x2) AND (x2 OR x3) AND (NOT x1 OR NOT x3)")
    print()

    # 暴力求解
    is_sat, assignment = sat.brute_force_solve()

    print(f"暴力求解:")
    print(f"  可满足: {'是' if is_sat else '否'}")
    if is_sat:
        print(f"  赋值: x1={assignment[0]}, x2={assignment[1]}, x3={assignment[2]}")

    print()

    # 随机游走
    is_sat, assignment = sat.random_walk_solve(max_attempts=100)

    print(f"随机游走:")
    print(f"  可满足: {'是' if is_sat else '否'}")
    if is_sat:
        print(f"  赋值: x1={assignment[0]}, x2={assignment[1]}, x3={assignment[2]}")

    print()
    sat_complexity()

    print()
    print("说明：")
    print("  - SAT是NP-完全问题")
    print("  - CDCL算法在实际中很高效")
    print("  - 验证SAT实例在计算机科学中很重要")

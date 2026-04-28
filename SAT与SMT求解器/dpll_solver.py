# -*- coding: utf-8 -*-
"""
DPLL算法完全实现：Davis-Putnam-Logemann-Loveland算法
功能：判定命题公式的可满足性（SAT），支持分裂、回溯、单元传播

核心思想：
1. 单元传播：若子句中存在单文字，则该文字必真，传播其影响
2. 纯文字消除：若文字仅以正/负形式出现，则可安全赋值为真
3. 分裂：选取未赋值文字，递归尝试两种真值

作者：SAT Solver Team
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict


class DPLLSolver:
    """DPLL SAT求解器实现"""

    def __init__(self, cnf: List[List[int]]):
        """
        初始化求解器
        
        Args:
            cnf: 合取范式，每个子句是文字列表（正数=正文字，负数=负文字）
                 例如 [[1, 2, -3], [-1, 3]] 表示 (x1 ∨ x2 ∨ ¬x3) ∧ (¬x1 ∨ x3)
        """
        self.cnf = cnf  # CNF公式
        self.n_vars = self._count_variables()  # 变量总数
        self.assignment: Dict[int, bool] = {}  # 当前赋值: {变量id: True/False}
        self.unit_clauses: List[List[int]] = []  # 单元子句队列

    def _count_variables(self) -> int:
        """统计公式中出现的最大变量编号"""
        max_var = 0
        for clause in self.cnf:
            for lit in clause:
                max_var = max(max_var, abs(lit))
        return max_var

    def solve(self) -> Optional[Dict[int, bool]]:
        """
        主求解入口
        
        Returns:
            若SAT则返回完整赋值字典，否则返回None
        """
        # 预处理：消除纯文字
        cnf = self._pure_literal_elimination(self.cnf)
        
        # 迭代DPLL主循环
        return self._dpll(cnf)

    def _dpll(self, cnf: List[List[int]]) -> Optional[Dict[int, bool]]:
        """
        DPLL递归主函数
        
        Args:
            cnf: 当前简化后的CNF公式
            
        Returns:
            SAT解或None
        """
        # 1. 检查空子句（矛盾）
        for clause in cnf:
            if not clause:
                return None
        
        # 2. 检查所有子句均已满足
        if not cnf:
            return self.assignment.copy()
        
        # 3. 单元传播
        cnf, conflict = self._unit_propagation(cnf)
        if conflict:
            return None
        
        # 4. 选取决策变量（最简单的启发式：第一个未赋值变量）
        decision_var = self._select_variable(cnf)
        if decision_var is None:
            return self.assignment.copy()
        
        # 5. 分裂尝试：先尝试True分支
        self.assignment[decision_var] = True
        result = self._dpll(self._apply_assignment(cnf, decision_var, True))
        if result is not None:
            return result
        
        # 6. 回溯，尝试False分支
        self.assignment[decision_var] = False
        return self._dpll(self._apply_assignment(cnf, decision_var, False))

    def _unit_propagation(self, cnf: List[List[int]]) -> Tuple[List[List[int]], bool]:
        """
        单元传播：反复应用单元子句规则
        
        单元子句规则：若子句仅有一个未赋值文字L，则L必须为真
        传播效果：将所有含¬L的子句删除，并从含L的子句中删除L
        
        Returns:
            (简化后的cnf, 是否发生冲突)
        """
        while True:
            # 查找单元子句（只有一个未赋值文字的子句）
            unit = None
            for clause in cnf:
                unassigned = [lit for lit in clause if abs(lit) not in self.assignment]
                if len(unassigned) == 1:
                    unit = unassigned[0]
                    break
            
            if unit is None:
                break  # 没有更多单元子句
            
            var = abs(unit)
            val = unit > 0  # 正文字为True
            
            # 防止循环：如果已经赋过相反值，则冲突
            if var in self.assignment and self.assignment[var] != val:
                return cnf, True
            
            self.assignment[var] = val
        
        # 应用所有单元传播后的赋值
        new_cnf = []
        for clause in cnf:
            new_clause = []
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in self.assignment:
                    if (self.assignment[var] and lit > 0) or (not self.assignment[var] and lit < 0):
                        satisfied = True
                        break
                    # 文字为False，跳过
                else:
                    new_clause.append(lit)
            if not satisfied:
                if not new_clause:
                    return [], True  # 空子句=冲突
                new_cnf.append(new_clause)
        
        return new_cnf, False

    def _pure_literal_elimination(self, cnf: List[List[int]]) -> List[List[int]]:
        """
        纯文字消除
        
        纯文字：在所有子句中仅以同一种形式出现（仅正或仅负）
        规则：可以将纯文字设为真并删除所有含它的子句（永不影响可满足性）
        """
        # 统计每个变量出现的文字极性
        occurrence: Dict[int, Set[int]] = defaultdict(set)
        for clause in cnf:
            for lit in clause:
                occurrence[abs(lit)].add(lit)
        
        # 找出纯文字
        pure_literals = set()
        for var, lits in occurrence.items():
            if all(l > 0 for l in lits) or all(l < 0 for l in lits):
                # 所有出现都是正的或都是负的 → 纯文字
                pure_literals.add(var)
        
        # 消除纯文字
        if not pure_literals:
            return cnf
        
        new_cnf = []
        for clause in cnf:
            new_clause = [lit for lit in clause if abs(lit) not in pure_literals]
            if new_clause:
                new_cnf.append(new_clause)
        
        return new_cnf

    def _select_variable(self, cnf: List[List[int]]) -> Optional[int]:
        """
        变量选择启发式：返回第一个未赋值变量
        可扩展为MOMS、DLIS等高级启发式
        """
        for clause in cnf:
            for lit in clause:
                var = abs(lit)
                if var not in self.assignment:
                    return var
        return None

    def _apply_assignment(self, cnf: List[List[int]], var: int, val: bool) -> List[List[int]]:
        """
        将变量赋值应用到CNF公式
        
        Args:
            cnf: 原公式
            var: 变量ID
            val: 赋值为True或False
            
        Returns:
            简化后的CNF
        """
        result = []
        for clause in cnf:
            new_clause = []
            satisfied = False
            for lit in clause:
                v = abs(lit)
                if v == var:
                    # 该文字涉及当前变量
                    if (val and lit > 0) or (not val and lit < 0):
                        satisfied = True
                        break
                    # 否则文字为False，跳过
                else:
                    new_clause.append(lit)
            if not satisfied:
                if not new_clause:
                    return [[]]  # 返回含空子句的公式表示冲突
                result.append(new_clause)
        return result


def parse_dimacs(cnf_str: str) -> List[List[int]]:
    """
    解析DIMACS CNF格式字符串
    
    DIMACS格式示例:
        c This is a comment
        p cnf 3 2
        1 2 -3 0
        -1 3 0
    
    Returns:
        CNF公式列表
    """
    cnf = []
    for line in cnf_str.splitlines():
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p'):
            continue
        literals = []
        for token in line.split():
            if token == '0':
                break
            literals.append(int(token))
        if literals:
            cnf.append(literals)
    return cnf


def example_basic():
    """基本示例：求解简单SAT问题"""
    # 例：(x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3) ∧ x1
    cnf = [
        [1, 2],
        [-1, 3],
        [-2, -3],
        [1]
    ]
    
    solver = DPLLSolver(cnf)
    result = solver.solve()
    
    if result:
        print("=== SAT ===")
        for var, val in sorted(result.items()):
            print(f"  x{var} = {val}")
    else:
        print("=== UNSAT ===")


def example_unsat():
    """UNSAT示例：(x ∨ y) ∧ (¬x) ∧ (¬y)"""
    cnf = [
        [1, 2],
        [-1],
        [-2]
    ]
    
    solver = DPLLSolver(cnf)
    result = solver.solve()
    print("UNSAT示例:" if result is None else f"SAT: {result}")


def example_dimacs():
    """DIMACS格式解析示例"""
    dimacs_str = """
    c Simple 3-SAT example
    p cnf 3 3
    1 2 -3 0
    -1 3 0
    2 3 0
    """
    cnf = parse_dimacs(dimacs_str)
    print(f"解析得到 {len(cnf)} 个子句")
    solver = DPLLSolver(cnf)
    result = solver.solve()
    if result:
        print("DIMACS格式 SAT解:", result)


if __name__ == "__main__":
    print("=" * 50)
    print("DPLL SAT求解器 测试")
    print("=" * 50)
    
    example_basic()
    print()
    example_unsat()
    print()
    example_dimacs()

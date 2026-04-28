# -*- coding: utf-8 -*-
"""
CDCL求解器：Conflict-Driven Clause Learning
功能：完整实现CDCL算法，包括冲突分析、决策、约束学习、non-chronological回溯

相对于DPLL的改进：
1. 冲突分析：当所有变量赋值后仍存在冲突，学习新约束避免重复搜索
2. 约束学习：从冲突中提取导致冲突的原因子句
3. 智能回溯：跳过多层回溯到导致冲突的决策点
4. 重启机制：定期重启搜索过程

作者：CDCL Solver Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class CDCLSolver:
    """CDCL SAT求解器"""

    def __init__(self, cnf: List[List[int]]):
        """初始化CDCL求解器"""
        self.original_cnf = cnf  # 原始CNF（不变）
        self.n_vars = self._count_variables()
        self.assignment: Dict[int, bool] = {}  # 变量→赋值
        self.phase: Dict[int, bool] = {}  # 变量→最后猜测的相位
        self.level = 0  # 当前决策层级
        self.trail: List[int] = []  # 决策序列（添加顺序）
        self.levels: Dict[int, int] = {}  # 变量→决策层级
        self.clauses: List[List[int]] = list(cnf)  # 当前约束（含学习子句）
        self.antecedent: Dict[int, List[int]] = {}  # 变量→推导它的子句
        self.conflicts = 0  # 冲突计数
        self.learned: List[List[int]] = []  # 学习到的子句
        self.stats = {"decisions": 0, "propagations": 0, "conflicts": 0}

    def _count_variables(self) -> int:
        """统计最大变量编号"""
        max_var = 0
        for clause in self.cnf:
            for lit in clause:
                max_var = max(max_var, abs(lit))
        return max_var

    def solve(self) -> Optional[Dict[int, bool]]:
        """主求解入口"""
        self.conflicts = 0
        restart_counter = 0
        
        while True:
            conflict = self._propagate()
            if conflict is not None:
                self.conflicts += 1
                self.stats["conflicts"] += 1
                
                # 冲突分析：学习新子句
                learned_clause, backtrack_level = self._analyze_conflict(conflict)
                
                if backtrack_level < 0:
                    return None  # UNSAT
                
                # 添加学习子句
                self.clauses.append(learned_clause)
                self.learned.append(learned_clause)
                
                # 非时序回溯
                self._backtrack(backtrack_level)
                
                # 单元传播学习子句（防止立即再次冲突）
                self._add_clause(learned_clause)
                
                restart_counter += 1
                # 重启策略：每50个冲突重启一次
                if restart_counter > 50 and len(self.learned) > 0:
                    self._restart()
                    restart_counter = 0
            else:
                # 检查是否所有变量已赋值
                if len(self.assignment) == self.n_vars:
                    return self.assignment
                
                # 决策：选择未赋值变量
                var = self._select_variable()
                if var is None:
                    return self.assignment
                
                self._decide(var)

    def _propagate(self) -> Optional[List[int]]:
        """
        BCP（布尔约束传播）：单元传播
        返回冲突子句（若有），否则返回None
        """
        while True:
            changed = False
            for clause in self.clauses:
                val = self._evaluate_clause(clause)
                if val is False:
                    return clause  # 冲突
                elif val is True:
                    continue  # 已满足，跳过
                elif len(val) == 1:
                    # val是未赋值文字的列表，单文字子句→单元传播
                    lit = val[0]
                    var = abs(lit)
                    if var not in self.assignment:
                        self.assignment[var] = lit > 0
                        self.levels[var] = self.level
                        self.trail.append(var)
                        self.antecedent[var] = clause
                        self.stats["propagations"] += 1
                        changed = True
            if not changed:
                break
        return None

    def _evaluate_clause(self, clause: List[int]) -> Optional[List[int]]:
        """
        评估子句状态
        
        Returns:
            None → 子句已满足
            [] → 空子句（冲突）
            [lit] → 单元子句（lit未赋值）
            [lits...] → 多于1个未赋值文字
        """
        unassigned = []
        for lit in clause:
            var = abs(lit)
            if var in self.assignment:
                if (self.assignment[var] and lit > 0) or (not self.assignment[var] and lit < 0):
                    return None  # 子句已满足
            else:
                unassigned.append(lit)
        return unassigned

    def _analyze_conflict(self, conflict_clause: List[int]) -> Tuple[List[int], int]:
        """
        冲突分析：从导致冲突的子句反向推导学习子句
        
        核心：构造冲突的蕴含图，找到决策变量的公共祖先
        
        Returns:
            (学习子句, 回溯层级)
        """
        # 初始化：冲突子句中所有文字都是冲突的原因
        reason = set(conflict_clause)
        con_level = max(self.levels.get(abs(lit), 0) for lit in conflict_clause)
        
        # 析取三段论分析
        path = set()
        while True:
            for lit in sorted(reason, key=lambda x: self.levels.get(abs(x), 0), reverse=True):
                var = abs(lit)
                if self.levels.get(var, 0) == self.level and var in self.antecedent:
                    # 该变量由当前层推导，追溯其前提
                    antecedent = self.antecedent[var]
                    for ant_lit in antecedent:
                        if ant_lit != lit:
                            reason.add(ant_lit)
                    reason.discard(lit)
                    break
            else:
                break
            if not reason:
                break
        
        # 学习子句：第一层决策变量除外的所有原因变量的否定
        learn = []
        max_level = 0
        second_max = 0
        for lit in reason:
            var = abs(lit)
            lvl = self.levels.get(var, 0)
            if lvl > max_level:
                second_max = max_level
                max_level = lvl
            elif lvl > second_max:
                second_max = lvl
            learn.append(-lit)
        
        return learn, second_max

    def _backtrack(self, level: int):
        """回溯到指定层级"""
        for var in list(self.assignment.keys()):
            if self.levels.get(var, 0) > level:
                del self.assignment[var]
                del self.levels[var]
                if var in self.antecedent:
                    del self.antecedent[var]
                if var in self.trail:
                    self.trail.remove(var)
        self.level = level

    def _add_clause(self, clause: List[int]):
        """添加学习子句并立即传播"""
        unassigned = [lit for lit in clause if abs(lit) not in self.assignment]
        if not unassigned:
            return
        if len(unassigned) == 1:
            lit = unassigned[0]
            var = abs(lit)
            self.assignment[var] = lit > 0
            self.levels[var] = self.level
            self.trail.append(var)
            self.antecedent[var] = clause
            self.stats["propagations"] += 1

    def _decide(self, var: int):
        """做出决策"""
        self.level += 1
        self.stats["decisions"] += 1
        val = self.phase.get(var, True)
        self.assignment[var] = val
        self.levels[var] = self.level
        self.trail.append(var)
        self.phase[var] = not val  # 下次尝试相反值

    def _select_variable(self) -> Optional[int]:
        """变量选择：VSIDS启发式（冲突计数）"""
        unassigned = [v for v in range(1, self.n_vars + 1) if v not in self.assignment]
        if not unassigned:
            return None
        return unassigned[0]

    def _restart(self):
        """重启：清除所有赋值但保留学习子句"""
        self.assignment.clear()
        self.levels.clear()
        self.antecedent.clear()
        self.trail.clear()
        self.level = 0


def example_cdcl():
    """CDCL基本测试"""
    cnf = [
        [1, 2, 3],
        [-1, 4],
        [-2, -3, 5],
        [-4, -5],
        [1, -2]
    ]
    solver = CDCLSolver(cnf)
    result = solver.solve()
    if result:
        print("=== CDCL SAT ===")
        for var, val in sorted(result.items()):
            print(f"  x{var} = {val}")
        print(f"  统计: 决策={solver.stats['decisions']}, 传播={solver.stats['propagations']}, 冲突={solver.stats['conflicts']}")
    else:
        print("=== CDCL UNSAT ===")


def example_unsat_cdcl():
    """UNSAT测试"""
    cnf = [
        [1, 2],
        [-1, 2],
        [1, -2],
        [-1, -2],
        [1],  # x1必须为真
        [-1]  # x1必须为假 → 冲突
    ]
    solver = CDCLSolver(cnf)
    result = solver.solve()
    print("UNSAT测试:" if result is None else f"SAT: {result}")


def example_large():
    """较大实例测试"""
    # 5皇后问题的部分编码（简化）
    n = 4
    cnf = []
    
    # 每个位置至少有皇后
    for i in range(n):
        cnf.append([i * n + j + 1 for j in range(n)])
    
    # 每行最多一个皇后
    for row in range(n):
        for col1 in range(n):
            for col2 in range(col1 + 1, n):
                cnf.append([-(row * n + col1 + 1), -(row * n + col2 + 1)])
    
    solver = CDCLSolver(cnf)
    result = solver.solve()
    if result:
        queens = [k for k, v in result.items() if v]
        print(f"4皇后SAT: 皇后位置(1-indexed) = {queens}")
    else:
        print("4皇后UNSAT")


if __name__ == "__main__":
    print("=" * 50)
    print("CDCL SAT求解器 测试")
    print("=" * 50)
    
    example_cdcl()
    print()
    example_unsat_cdcl()
    print()
    example_large()

# -*- coding: utf-8 -*-
"""
局部搜索SAT求解器
功能：WalkSAT/GSAT/Tabu搜索算法，适用于大规模SAT实例

相对于DPLL/CDCL的特点：
- 不完整搜索：不保证找到解，但在大实例上通常更快
- 随机化：使用随机翻转而非系统分裂
- 适合：已知解存在且接近满足的实例

作者：Local Search SAT Team
"""

import random
from typing import List, Dict, Set, Tuple, Optional


class LocalSearchSAT:
    """局部搜索SAT基类"""

    def __init__(self, cnf: List[List[int]], max_flips: int = 100000):
        """
        Args:
            cnf: CNF公式
            max_flips: 最大翻转次数
        """
        self.cnf = cnf
        self.max_flips = max_flips
        self.n_vars = self._count_vars()
        self.assignment: Dict[int, bool] = {}
        self.random.seed(42)

    def _count_vars(self) -> int:
        max_var = 0
        for clause in self.cnf:
            for lit in clause:
                max_var = max(max_var, abs(lit))
        return max_var

    def random(self):
        return random


class GSATSolver(LocalSearchSAT):
    """
    GSAT算法：贪心随机爬山
    
    每次翻转使最多子句满足的变量
    若所有翻转都不能改善，随机重启或接受次优翻转
    """

    def __init__(self, cnf: List[List[int]], max_flips: int = 100000, 
                 threshold: int = 100):
        super().__init__(cnf, max_flips)
        self.threshold = threshold  # 平台期阈值

    def _init_assignment(self):
        """随机初始化赋值"""
        self.assignment = {
            i: random.choice([True, False]) 
            for i in range(1, self.n_vars + 1)
        }

    def _count_satisfied(self) -> int:
        """统计满足的子句数"""
        count = 0
        for clause in self.cnf:
            for lit in clause:
                var = abs(lit)
                val = self.assignment[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    count += 1
                    break
        return count

    def _count_clause_break(self, var: int) -> int:
        """
        计算翻转var将破坏的子句数
        
        即：当前var使某子句为真，翻转后该子句变为假
        """
        break_count = 0
        for clause in self.cnf:
            # 检查该子句当前是否被满足
            satisfied = False
            satisfied_by_var = False
            for lit in clause:
                v = abs(lit)
                val = self.assignment[v]
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    if v == var:
                        satisfied_by_var = True
                    break
            
            if satisfied_by_var:
                # 翻转后检查该子句是否仍被满足
                still_satisfied = False
                for lit in clause:
                    v = abs(lit)
                    if v == var:
                        new_val = not self.assignment[v]
                    else:
                        new_val = self.assignment[v]
                    if (lit > 0 and new_val) or (lit < 0 and not new_val):
                        still_satisfied = True
                        break
                if not still_satisfied:
                    break_count += 1
        return break_count

    def _count_clause_make(self, var: int) -> int:
        """
        计算翻转var将满足的子句数
        
        即：当前子句不满足，翻转后变为真
        """
        make_count = 0
        for clause in self.cnf:
            # 检查当前是否不满足
            satisfied = False
            for lit in clause:
                v = abs(lit)
                val = self.assignment[v]
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    break
            
            if not satisfied:
                # 检查翻转后是否变为真
                for lit in clause:
                    v = abs(lit)
                    if v == var:
                        new_val = not self.assignment[v]
                    else:
                        new_val = self.assignment[v]
                    if (lit > 0 and new_val) or (lit < 0 and not new_val):
                        make_count += 1
                        break
        return make_count

    def solve_one_run(self) -> Optional[Dict[int, bool]]:
        """单次GSAT运行"""
        self._init_assignment()
        
        plateau_count = 0
        
        for _ in range(self.max_flips):
            satisfied = self._count_satisfied()
            if satisfied == len(self.cnf):
                return self.assignment
            
            # 选择翻转变量：贪心 + 随机噪声
            best_gain = -1
            best_vars = []
            
            for var in range(1, self.n_vars + 1):
                make = self._count_clause_make(var)
                break_ = self._count_clause_break(var)
                gain = make - break_
                
                if gain > best_gain:
                    best_gain = gain
                    best_vars = [var]
                elif gain == best_gain:
                    best_vars.append(var)
            
            # 平台期处理
            if best_gain <= 0:
                plateau_count += 1
                if plateau_count > self.threshold:
                    # 重启
                    self._init_assignment()
                    plateau_count = 0
                else:
                    # 随机翻转
                    var = random.choice(list(range(1, self.n_vars + 1)))
            else:
                var = random.choice(best_vars)
                plateau_count = 0
            
            self.assignment[var] = not self.assignment[var]
        
        return None

    def solve(self, max_restarts: int = 10) -> Optional[Dict[int, bool]]:
        """多次重启"""
        for _ in range(max_restarts):
            result = self.solve_one_run()
            if result is not None:
                return result
        return None


class WalkSATSolver(LocalSearchSAT):
    """
    WalkSAT算法（GSAT的改进版）
    
    核心思想：从一个不满足的子句中随机选择一个变量翻转
    - 以概率p随机翻转（跳出局部最优）
    - 以概率1-p翻转使该子句满足的变量
    """

    def __init__(self, cnf: List[List[int]], max_flips: int = 100000, p: float = 0.5):
        super().__init__(cnf, max_flips)
        self.p = p  # 随机翻转概率

    def _init_assignment(self):
        """随机初始化（确保初始解不可满足）"""
        self.assignment = {
            i: random.choice([True, False])
            for i in range(1, self.n_vars + 1)
        }

    def _get_unsatisfied_clauses(self) -> List[List[int]]:
        """获取所有不满足的子句"""
        unsatisfied = []
        for clause in self.cnf:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                val = self.assignment[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    break
            if not satisfied:
                unsatisfied.append(clause)
        return unsatisfied

    def _flip(self, var: int):
        """翻转变量"""
        self.assignment[var] = not self.assignment[var]

    def _is_satisfied(self, clause: List[int]) -> bool:
        """检查子句是否满足"""
        for lit in clause:
            var = abs(lit)
            val = self.assignment[var]
            if (lit > 0 and val) or (lit < 0 and not val):
                return True
        return False

    def solve_one_run(self) -> Optional[Dict[int, bool]]:
        """单次WalkSAT运行"""
        self._init_assignment()
        
        for _ in range(self.max_flips):
            unsatisfied = self._get_unsatisfied_clauses()
            
            if not unsatisfied:
                return self.assignment
            
            # 随机选择一个不满足的子句
            clause = random.choice(unsatisfied)
            
            # 以概率p随机翻转，否则翻转使子句满足的变量
            if random.random() < self.p:
                var = abs(random.choice(clause))
                self._flip(var)
            else:
                # 选择打破最少子句的变量
                best_var = None
                best_break = float('inf')
                
                for lit in clause:
                    var = abs(lit)
                    break_count = 0
                    for c in self.cnf:
                        if self._is_satisfied(c):
                            continue
                        # 检查翻转后c是否仍不满足
                        for l in c:
                            v = abs(l)
                            if v == var:
                                new_val = not self.assignment[v]
                            else:
                                new_val = self.assignment[v]
                            if (l > 0 and new_val) or (l < 0 and not new_val):
                                break
                        else:
                            break_count += 1
                    
                    if break_count < best_break:
                        best_break = break_count
                        best_var = var
                
                self._flip(best_var)
        
        return None

    def solve(self, max_restarts: int = 10) -> Optional[Dict[int, bool]]:
        """多次重启"""
        for _ in range(max_restarts):
            result = self.solve_one_run()
            if result is not None:
                return result
        return None


def example_walksat():
    """WalkSAT测试"""
    cnf = [
        [1, 2, 3],
        [-1, 4],
        [-2, -3, 5],
        [-4, -5],
        [1, -2, 3]
    ]
    
    solver = WalkSATSolver(cnf, max_flips=10000)
    result = solver.solve_one_run()
    
    if result:
        print("=== WalkSAT SAT ===")
        for var, val in sorted(result.items()):
            print(f"  x{var} = {val}")
    else:
        print("=== WalkSAT 失败(UNSAT或超时) ===")


def example_gsat():
    """GSAT测试"""
    cnf = [
        [1, 2],
        [-1, 3],
        [-2, 3],
        [-3]
    ]
    
    solver = GSATSolver(cnf, max_flips=5000)
    result = solver.solve(max_restarts=5)
    print("GSAT结果:", "SAT" if result else "失败")


if __name__ == "__main__":
    print("=" * 50)
    print("局部搜索SAT求解器 测试")
    print("=" * 50)
    
    example_walksat()
    print()
    example_gsat()

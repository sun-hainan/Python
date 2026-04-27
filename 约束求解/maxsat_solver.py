# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / maxsat_solver

本文件实现 maxsat_solver 相关的算法功能。
"""

import random
from typing import List, Set, Tuple, Optional, Dict
from collections import defaultdict


class MAXSATSolver:
    """
    MAX-SAT问题求解器
    使用局部搜索和模拟退火来近似求解最大化满足子句数的问题
    """
    
    def __init__(self, clauses: List[Set[int]], num_vars: int):
        """
        初始化求解器
        
        Args:
            clauses: 子句列表
            num_vars: 变量数量
        """
        self.clauses = clauses
        self.n = num_vars
        
        # 统计每个变量在每个真值下满足的子句数
        self.sat_count_pos: Dict[int, int] = defaultdict(int)  # 变量为True时满足的子句数
        self.sat_count_neg: Dict[int, int] = defaultdict(int)  # 变量为False时满足的子句数
        self.calc_clause_weights()
    
    def calc_clause_weights(self):
        """计算每个变量在每种真值下满足的子句数"""
        # 统计每个变量在正/负文字下满足多少子句
        for clause in self.clauses:
            for lit in clause:
                var = abs(lit)
                if lit > 0:
                    self.sat_count_pos[var] += 1
                else:
                    self.sat_count_neg[var] += 1
    
    def count_satisfied(self, assignment: Dict[int, bool]) -> int:
        """统计满足的子句数"""
        count = 0
        for clause in self.clauses:
            for lit in clause:
                var = abs(lit)
                if (lit > 0 and assignment.get(var, False)) or (lit < 0 and not assignment.get(var, True)):
                    count += 1
                    break
        return count
    
    def get_gain(self, var: int, current_value: bool, assignment: Dict[int, bool]) -> int:
        """
        计算翻转某变量的收益(满足子句数的变化)
        
        Args:
            var: 变量
            current_value: 当前值(翻转后的值)
            assignment: 当前赋值
        
        Returns:
            收益(增加满足的子句数减去减少的)
        """
        # 翻转后该变量满足的子句数
        if current_value:  # 翻转后为True
            gain_pos = self.sat_count_pos[var]
            gain_neg = 0
        else:  # 翻转后为False
            gain_pos = 0
            gain_neg = self.sat_count_neg[var]
        
        # 当前状态下该变量满足的子句数
        current_val = assignment.get(var, False)
        if current_val:  # 当前为True
            current_sat = self.sat_count_pos[var]
            new_sat = self.sat_count_neg[var] if not current_value else self.sat_count_pos[var]
        else:  # 当前为False
            current_sat = self.sat_count_neg[var]
            new_sat = self.sat_count_pos[var] if current_value else self.sat_count_neg[var]
        
        # 计算收益:翻转后满足的子句 - 当前满足的子句
        # 但要减去那些同时包含该变量的子句中被翻转影响的
        actual_gain = new_sat - current_sat
        return actual_gain
    
    def random_assignment(self) -> Dict[int, bool]:
        """生成随机赋值"""
        return {i: random.choice([True, False]) for i in range(1, self.n + 1)}
    
    def greedy_step(self, assignment: Dict[int, bool]) -> Optional[int]:
        """
        贪心步骤:选择翻转后收益最大的变量
        
        Returns:
            被翻转的变量或None(如果没有正向收益)
        """
        best_var = None
        best_gain = 0
        
        for var in range(1, self.n + 1):
            current_val = assignment[var]
            gain = self.get_gain(var, not current_val, assignment)
            
            if gain > best_gain:
                best_gain = gain
                best_var = var
        
        if best_var is not None and best_gain > 0:
            assignment[best_var] = not assignment[best_var]
            return best_var
        
        return None
    
    def random_step(self, assignment: Dict[int, bool]) -> int:
        """
        随机步骤:随机选择一个变量翻转
        
        Returns:
            被翻转的变量
        """
        var = random.randint(1, self.n)
        assignment[var] = not assignment[var]
        return var
    
    def unsatisfied_clauses(self, assignment: Dict[int, bool]) -> List[Set[int]]:
        """获取所有不满足的子句"""
        unsatisfied = []
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if (lit > 0 and assignment.get(var, False)) or (lit < 0 and not assignment.get(var, True)):
                    satisfied = True
                    break
            if not satisfied:
                unsatisfied.append(clause)
        return unsatisfied
    
    def random_flip_from_unsatisfied(self, assignment: Dict[int, bool]) -> int:
        """从不满足的子句中随机选择一个文字翻转"""
        unsatisfied = self.unsatisfied_clauses(assignment)
        if not unsatisfied:
            return self.random_step(assignment)
        
        clause = random.choice(unsatisfied)
        lit = random.choice(list(clause))
        var = abs(lit)
        assignment[var] = not assignment[var]
        return var
    
    def solve_greedy(self, max_iterations: int = 10000) -> Tuple[Dict[int, bool], int]:
        """
        贪心求解
        
        Returns:
            (最优赋值, 满足的子句数)
        """
        best_assignment = None
        best_count = 0
        
        for _ in range(100):  # 多次随机重启
            assignment = self.random_assignment()
            
            for _ in range(max_iterations):
                # 尝试贪心翻转
                flipped = self.greedy_step(assignment)
                
                if flipped is None:
                    # 没有正向收益,随机翻转尝试改进
                    self.random_flip_from_unsatisfied(assignment)
                
                current_count = self.count_satisfied(assignment)
                if current_count > best_count:
                    best_count = current_count
                    best_assignment = assignment.copy()
                
                if current_count == len(self.clauses):
                    return assignment, current_count
            
            # 随机重启
            assignment = self.random_assignment()
        
        return best_assignment if best_assignment else assignment, best_count
    
    def solve_simulated_annealing(self, initial_temp: float = 1.0,
                                   cooling_rate: float = 0.9995,
                                   min_temp: float = 0.001) -> Tuple[Dict[int, bool], int]:
        """
        模拟退火求解
        
        Args:
            initial_temp: 初始温度
            cooling_rate: 冷却率
            min_temp: 最低温度
        
        Returns:
            (最优赋值, 满足的子句数)
        """
        current = self.random_assignment()
        current_count = self.count_satisfied(current)
        
        best = current.copy()
        best_count = current_count
        
        temp = initial_temp
        
        while temp > min_temp:
            # 随机翻转一个变量
            var = random.randint(1, self.n)
            old_value = current[var]
            current[var] = not current[var]
            
            new_count = self.count_satisfied(current)
            delta = new_count - current_count
            
            # 以概率接受差解
            if delta < 0:
                prob = random.random()
                if prob > min(1.0, pow(2.718, delta / temp)):
                    # 拒绝:恢复原值
                    current[var] = old_value
                    new_count = current_count
            
            current_count = self.count_satisfied(current)
            
            if current_count > best_count:
                best = current.copy()
                best_count = current_count
            
            if current_count == len(self.clauses):
                return current, current_count
            
            temp *= cooling_rate
        
        return best, best_count
    
    def solve_walksat_style(self, max_iterations: int = 50000) -> Tuple[Dict[int, bool], int]:
        """
        WalkSAT风格求解
        
        Returns:
            (最优赋值, 满足的子句数)
        """
        best = None
        best_count = 0
        
        for _ in range(10):  # 多次重启
            assignment = self.random_assignment()
            
            for _ in range(max_iterations):
                unsatisfied = self.unsatisfied_clauses(assignment)
                
                if not unsatisfied:
                    return assignment, len(self.clauses)
                
                # 随机选择一个不满足的子句
                clause = random.choice(unsatisfied)
                
                # 如果随机值小于0.5,随机翻转;否则选择最优翻转
                if random.random() < 0.5:
                    lit = random.choice(list(clause))
                    var = abs(lit)
                else:
                    # 选择翻转后满足最多子句的变量
                    best_var = None
                    best_gain = -float('inf')
                    
                    for lit in clause:
                        var = abs(lit)
                        gain = self.get_gain(var, not assignment[var], assignment)
                        if gain > best_gain:
                            best_gain = gain
                            best_var = var
                    
                    var = best_var
                
                assignment[var] = not assignment[var]
                
                current_count = self.count_satisfied(assignment)
                if current_count > best_count:
                    best_count = current_count
                    best = assignment.copy()
            
            assignment = self.random_assignment()
        
        return best if best else self.random_assignment(), best_count
    
    def solve(self, method: str = 'hybrid') -> Tuple[Dict[int, bool], int]:
        """
        主求解函数
        
        Args:
            method: 'greedy', 'sa'(模拟退火), 'walksat', 'hybrid'
        
        Returns:
            (赋值, 满足的子句数)
        """
        if method == 'greedy':
            return self.solve_greedy()
        elif method == 'sa':
            return self.solve_simulated_annealing()
        elif method == 'walksat':
            return self.solve_walksat_style()
        else:  # hybrid
            # 先用贪心,再用SA改进
            assignment, count = self.solve_greedy()
            solver = MAXSATSolver(self.clauses, self.n)
            solver.clauses = self.clauses
            assignment2, count2 = solver.solve_simulated_annealing()
            if count2 > count:
                return assignment2, count2
            return assignment, count


def solve_max_sat(clauses: List[Set[int]], num_vars: int, 
                 method: str = 'hybrid') -> Tuple[Dict[int, bool], int]:
    """
    MAX-SAT求解便捷函数
    
    Args:
        clauses: 子句列表
        num_vars: 变量数量
        method: 求解方法
    
    Returns:
        (赋值, 满足的子句数)
    """
    solver = MAXSATSolver(clauses, num_vars)
    return solver.solve(method)


# 测试代码
if __name__ == "__main__":
    random.seed(42)
    
    # 测试1: 简单MAX-SAT
    print("测试1 - 简单MAX-SAT实例:")
    clauses = [
        {1, 2, 3},
        {-1, 2},
        {1, -2, 3},
        {-2, -3},
    ]
    
    solver = MAXSATSolver(clauses, 3)
    result, count = solver.solve('greedy')
    print(f"  贪心: 满足{count}/{len(clauses)}个子句, 赋值={result}")
    
    result, count = solver.solve('walksat')
    print(f"  WalkSAT: 满足{count}/{len(clauses)}个子句, 赋值={result}")
    
    # 测试2: 较大实例
    print("\n测试2 - 较大实例(20变量,50子句):")
    def generate_random_maxsat(num_vars: int, num_clauses: int, clause_size: int = 3) -> List[Set[int]]:
        clauses = []
        for _ in range(num_clauses):
            clause = set()
            while len(clause) < clause_size:
                var = random.randint(1, num_vars)
                sign = random.choice([1, -1])
                clause.add(sign * var)
            clauses.append(clause)
        return clauses
    
    random.seed(123)
    large_clauses = generate_random_maxsat(20, 50, 3)
    
    solver2 = MAXSATSolver(large_clauses, 20)
    
    result, count = solver2.solve('greedy')
    print(f"  贪心: 满足{count}/{len(large_clauses)}个子句 ({count/len(large_clauses)*100:.1f}%)")
    
    result, count = solver2.solve('sa')
    print(f"  模拟退火: 满足{count}/{len(large_clauses)}个子句 ({count/len(large_clauses)*100:.1f}%)")
    
    result, count = solver2.solve('walksat')
    print(f"  WalkSAT: 满足{count}/{len(large_clauses)}个子句 ({count/len(large_clauses)*100:.1f}%)")
    
    # 测试3: 验证解
    print("\n测试3 - 验证解的有效性:")
    def verify_maxsat(assignment: Dict[int, bool], clauses: List[Set[int]]) -> int:
        satisfied = 0
        for clause in clauses:
            for lit in clause:
                var = abs(lit)
                if (lit > 0 and assignment.get(var, False)) or (lit < 0 and not assignment.get(var, True)):
                    satisfied += 1
                    break
        return satisfied
    
    test_clauses = [
        {1, 2, 3},
        {-1, 4, 5},
        {2, -3, 6},
    ]
    
    solver3 = MAXSATSolver(test_clauses, 6)
    best_result = None
    best_count = 0
    
    # 枚举所有2^6=64种赋值找最优
    for bits in range(64):
        assignment = {i: bool((bits >> (i-1)) & 1) for i in range(1, 7)}
        count = verify_maxsat(assignment, test_clauses)
        if count > best_count:
            best_count = count
            best_result = assignment.copy()
    
    print(f"  最优解: 满足{best_count}/{len(test_clauses)}个子句")
    print(f"  最优赋值: {best_result}")
    
    # 用SA找近似解
    result, count = solver3.solve('sa')
    print(f"  SA近似: 满足{count}/{len(test_clauses)}个子句")
    
    print("\n所有测试完成!")

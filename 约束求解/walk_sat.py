# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / walk_sat

本文件实现 walk_sat 相关的算法功能。
"""

import random
from typing import List, Set, Dict, Optional


def initialize_assignment(num_vars: int) -> Dict[int, bool]:
    """
    随机初始化变量赋值
    
    参数:
        num_vars: 变量数量
    
    返回:
        赋值字典 {变量ID: True/False}
    """
    return {i: random.choice([True, False]) for i in range(1, num_vars + 1)}


def count_unsatisfied(clauses: List[Set[int]], assignment: Dict[int, bool]) -> int:
    """
    计算不满足的子句数量
    
    参数:
        clauses: 子句列表
        assignment: 当前赋值
    
    返回:
        不满足的子句数
    """
    count = 0
    for clause in clauses:
        satisfied = False
        for literal in clause:
            var = abs(literal)
            if (literal > 0 and assignment[var]) or (literal < 0 and not assignment[var]):
                satisfied = True
                break
        if not satisfied:
            count += 1
    return count


def find_unsatisfied_clauses(clauses: List[Set[int]], assignment: Dict[int, bool]) -> List[Set[int]]:
    """
    找出所有不满足的子句
    
    参数:
        clauses: 子句列表
        assignment: 当前赋值
    
    返回:
        不满足的子句列表
    """
    result = []
    for clause in clauses:
        satisfied = False
        for literal in clause:
            var = abs(literal)
            if (literal > 0 and assignment[var]) or (literal < 0 and not assignment[var]):
                satisfied = True
                break
        if not satisfied:
            result.append(clause)
    return result


def break_clause(clause: Set[int], assignment: Dict[int, bool], probability: float = 0.5) -> int:
    """
    选择子句中要翻转的变量
    
    参数:
        clause: 不满足的子句
        assignment: 当前赋值
        probability: 随机选择概率（用于跳出局部最优）
    
    返回:
        被选中的变量ID
    """
    literals = list(clause)
    
    # 概率接受：随机选择（跳出局部最优）
    if random.random() < probability:
        return abs(random.choice(literals))
    
    # 启发式：选择翻转后减少最多冲突的变量
    best_var = None
    best_break_count = float('inf')
    
    for literal in clause:
        var = abs(literal)
        
        # 模拟翻转后的冲突变化
        assignment[var] = not assignment[var]
        # 计算翻转后会产生的新冲突数（粗略估计）
        # 实际上我们只考虑翻转这个变量对当前子句的影响
        break_count = 0
        
        # 检查翻转后该变量参与的其他子句
        for other_clause in [clause]:  # 只考虑当前子句简化
            # 如果翻转后这个子句仍然不满足，则这是一个 break
            # 这里用简化的启发式：翻转后检查该子句
            pass
        
        assignment[var] = not assignment[var]  # 恢复
        
        # 对于 WalkSAT，我们简单随机选择
        # 真实实现中会计算 flip 后不满足子句减少的数量
        if best_var is None:
            best_var = var
    
    # 简化：直接随机选择
    return abs(random.choice(literals))


def walksat(clauses: List[Set[int]], num_vars: int, 
            max_flips: int = 10000, 
            probability: float = 0.5,
            random_seed: Optional[int] = None) -> Optional[Dict[int, bool]]:
    """
    WalkSAT 主算法
    
    参数:
        clauses: 子句列表（CNF 格式）
        num_vars: 变量数量
        max_flips: 最大翻转次数
        probability: 随机跳转概率（通常 0.5~0.7）
        random_seed: 随机种子（用于复现）
    
    返回:
        满足赋值或 None（超时）
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    # 初始化随机赋值
    assignment = initialize_assignment(num_vars)
    
    for iteration in range(max_flips):
        # 检查是否所有子句都满足
        unsatisfied = count_unsatisfied(clauses, assignment)
        if unsatisfied == 0:
            return assignment
        
        # 找出不满足的子句，随机选择一个
        unsatisfied_clauses = find_unsatisfied_clauses(clauses, assignment)
        clause = random.choice(unsatisfied_clauses)
        
        # 选择要翻转的变量
        literal = random.choice(list(clause))
        var = abs(literal)
        
        # 翻转变量
        assignment[var] = not assignment[var]
    
    # 超时，返回 None
    return None


def gsat(clauses: List[Set[int]], num_vars: int,
         max_flips: int = 10000,
         random_seed: Optional[int] = None) -> Optional[Dict[int, bool]]:
    """
    GSAT 算法（Greedy SAT）
    
    与 WalkSAT 的区别：GSAT 优先选择使最多子句满足的变量
    而 WalkSAT 随机选择一个不满足的子句并翻转其中的变量
    
    参数:
        clauses: 子句列表
        num_vars: 变量数量
        max_flips: 最大翻转次数
        random_seed: 随机种子
    
    返回:
        满足赋值或 None
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    assignment = initialize_assignment(num_vars)
    
    for iteration in range(max_flips):
        unsatisfied = count_unsatisfied(clauses, assignment)
        if unsatisfied == 0:
            return assignment
        
        # 选择翻转后使最多子句满足的变量
        best_var = None
        best_satisfied = count_unsatisfied(clauses, assignment)
        
        for var in range(1, num_vars + 1):
            # 模拟翻转
            assignment[var] = not assignment[var]
            satisfied = count_unsatisfied(clauses, assignment)
            
            if satisfied < best_satisfied:
                best_satisfied = satisfied
                best_var = var
            
            # 恢复
            assignment[var] = not assignment[var]
        
        # 如果找到更好的翻转，执行它；否则随机翻转
        if best_var is not None and best_satisfied < unsatisfied:
            assignment[best_var] = not assignment[best_var]
        else:
            var = random.randint(1, num_vars)
            assignment[var] = not assignment[var]
    
    return None


def parse_cnf(cnf_str: str) -> tuple[int, List[Set[int]]]:
    """
    解析 CNF 格式字符串
    
    参数:
        cnf_str: CNF 格式字符串
    
    返回:
        (变量数, 子句列表)
    """
    lines = cnf_str.strip().split('\n')
    num_vars = 0
    clauses = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        
        clause = set()
        for token in line.split():
            if token == '0':
                break
            literal = int(token)
            clause.add(literal)
            num_vars = max(num_vars, abs(literal))
        if clause:
            clauses.append(clause)
    
    return num_vars, clauses


def solve_sat_random(clauses: List[Set[int]], num_vars: int,
                     algorithm: str = "walksat",
                     max_flips: int = 10000,
                     probability: float = 0.5,
                     random_seed: int = 42) -> Optional[Dict[int, bool]]:
    """
    SAT 求解器入口（随机算法）
    
    参数:
        clauses: CNF 子句列表
        num_vars: 变量数量
        algorithm: "walksat" 或 "gsat"
        max_flips: 最大翻转次数
        probability: WalkSAT 的随机跳转概率
        random_seed: 随机种子
    
    返回:
        满足赋值或 None
    """
    if algorithm == "walksat":
        return walksat(clauses, num_vars, max_flips, probability, random_seed)
    elif algorithm == "gsat":
        return gsat(clauses, num_vars, max_flips, random_seed)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


if __name__ == "__main__":
    # 测试用例 1：简单可满足实例
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3)
    test_clauses = [
        {1, 2},
        {-1, 3},
        {-2, 3}
    ]
    num_vars = 3
    
    print("测试1 - WalkSAT 简单实例:")
    print(f"  公式: (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3)")
    
    for seed in [42, 123, 456]:
        result = walksat(test_clauses, num_vars, max_flips=1000, random_seed=seed)
        print(f"  随机种子 {seed}: {result}")
        if result:
            # 验证
            for clause in test_clauses:
                satisfied = any(
                    (lit > 0 and result[abs(lit)]) or (lit < 0 and not result[abs(lit)])
                    for lit in clause
                )
                print(f"    子句 {clause} 满足: {satisfied}")
    
    print()
    
    # 测试用例 2：使用 CNF 解析
    cnf_str = """
    c 这是一个简单的 CNF 实例
    p cnf 3 3
    1 2 0
    -1 3 0
    -2 -3 0
    """
    num_vars, clauses = parse_cnf(cnf_str)
    
    print("测试2 - 解析 CNF 字符串:")
    print(f"  变量数: {num_vars}, 子句数: {len(clauses)}")
    
    result = walksat(clauses, num_vars, max_flips=1000, random_seed=42)
    print(f"  结果: {result}")
    
    print()
    
    # 测试用例 3：比较 GSAT 和 WalkSAT
    print("测试3 - GSAT vs WalkSAT 比较:")
    
    for algo in ["gsat", "walksat"]:
        result = solve_sat_random(test_clauses, num_vars, algorithm=algo, random_seed=42)
        print(f"  {algo.upper()}: {result}")
    
    print()
    print("=" * 50)
    print("复杂度分析:")
    print("  时间复杂度: O(max_flips × n × m)")
    print("  空间复杂度: O(n + m)")
    print("  其中 n 为变量数，m 为子句数")

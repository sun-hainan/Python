# -*- coding: utf-8 -*-
"""
SAT求解器工具集
功能：CNF格式转换、变量分析、子句统计分析、求解结果验证等

包含工具：
1. DIMACS读写
2. CNF规范化
3. 子句监控和统计
4. 解的验证
5. 公式简化

作者：SAT Utils Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import random


# ============== DIMACS格式 ==============

def read_dimacs(path: str) -> Tuple[int, int, List[List[int]]]:
    """
    读取DIMACS CNF文件
    
    Returns:
        (变量数, 子句数, CNF公式)
    """
    cnf = []
    n_vars = 0
    n_clauses = 0
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                n_vars = int(parts[2])
                n_clauses = int(parts[3])
            else:
                lits = []
                for tok in line.split():
                    if tok == '0':
                        break
                    lits.append(int(tok))
                if lits:
                    cnf.append(lits)
    
    return n_vars, n_clauses, cnf


def write_dimacs(path: str, cnf: List[List[int]], n_vars: int = None):
    """写入DIMACS CNF文件"""
    if n_vars is None:
        n_vars = max(abs(lit) for clause in cnf for lit in clause) if cnf else 0
    
    with open(path, 'w') as f:
        f.write(f"p cnf {n_vars} {len(cnf)}\n")
        for clause in cnf:
            clause_str = " ".join(str(lit) for lit in clause) + " 0\n"
            f.write(clause_str)


def parse_dimacs_string(s: str) -> List[List[int]]:
    """解析DIMACS字符串为CNF"""
    cnf = []
    for line in s.splitlines():
        line = line.strip()
        if not line or line.startswith('c') or line.startswith('p'):
            continue
        lits = []
        for tok in line.split():
            if tok == '0':
                break
            lits.append(int(tok))
        if lits:
            cnf.append(lits)
    return cnf


# ============== CNF工具 ==============

def count_variables(cnf: List[List[int]]) -> int:
    """统计变量数"""
    max_var = 0
    for clause in cnf:
        for lit in clause:
            max_var = max(max_var, abs(lit))
    return max_var


def count_clauses(cnf: List[List[int]]) -> Tuple[int, int, int]:
    """
    统计子句信息
    
    Returns:
        (总子句数, 单文字子句数, 空子句数)
    """
    total = len(cnf)
    unit = sum(1 for c in cnf if len(c) == 1)
    empty = sum(1 for c in cnf if len(c) == 0)
    return total, unit, empty


def clause_literals(cnf: List[List[int]]) -> Tuple[int, int, float]:
    """
    文字统计
    
    Returns:
        (最小长度, 最大长度, 平均长度)
    """
    if not cnf:
        return 0, 0, 0.0
    
    lengths = [len(c) for c in cnf]
    return min(lengths), max(lengths), sum(lengths) / len(lengths)


def remove_tautologies(cnf: List[List[int]]) -> List[List[int]]:
    """
    删除重言式子句
    
    重言式：同时包含 x 和 ¬x 的子句（永真）
    """
    result = []
    for clause in cnf:
        # 检查是否包含互补文字对
        has_complement = False
        seen = set()
        for lit in clause:
            neg_lit = -lit
            if neg_lit in seen:
                has_complement = True
                break
            seen.add(lit)
        
        if not has_complement:
            result.append(clause)
    
    return result


def unit_propagate(cnf: List[List[int]], 
                   assignment: Dict[int, bool]) -> Tuple[List[List[int]], List[int]]:
    """
    单元传播
    
    Returns:
        (简化CNF, 传播得到的单元文字列表)
    """
    cnf = [list(c) for c in cnf]
    propagated = []
    
    while True:
        unit_lit = None
        for clause in cnf:
            unassigned = [l for l in clause if abs(l) not in assignment]
            if len(unassigned) == 1:
                unit_lit = unassigned[0]
                break
        
        if unit_lit is None:
            break
        
        var = abs(unit_lit)
        val = unit_lit > 0
        propagated.append(unit_lit)
        
        if var in assignment and assignment[var] != val:
            # 冲突
            return [[]], propagated
        
        assignment[var] = val
        
        # 应用赋值
        new_cnf = []
        for clause in cnf:
            new_clause = []
            satisfied = False
            for lit in clause:
                v = abs(lit)
                if v == var:
                    if (assignment[var] and lit > 0) or (not assignment[var] and lit < 0):
                        satisfied = True
                        break
                elif v in assignment:
                    if (assignment[v] and lit > 0) or (not assignment[v] and lit < 0):
                        satisfied = True
                        break
                else:
                    new_clause.append(lit)
            
            if not satisfied:
                if not new_clause:
                    return [[]], propagated
                new_cnf.append(new_clause)
        cnf = new_cnf
    
    return cnf, propagated


def verify_solution(cnf: List[List[int]], assignment: Dict[int, bool]) -> bool:
    """
    验证SAT解的正确性
    
    Returns:
        True if all clauses are satisfied
    """
    for clause in cnf:
        clause_satisfied = False
        for lit in clause:
            var = abs(lit)
            val = assignment.get(var)
            if val is None:
                continue
            if (lit > 0 and val) or (lit < 0 and not val):
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True


def count_solutions(cnf: List[List[int]], max_count: int = 100) -> int:
    """
    枚举解（最多max_count个）
    
    Returns:
        解的数量（可能截断）
    """
    from dpll_solver import DPLLSolver
    
    solutions = 0
    solver = DPLLSolver(cnf)
    
    while solutions < max_count:
        result = solver.solve()
        if result is None:
            break
        
        # 找到解，添加约束排除该解
        negation = []
        for var, val in result.items():
            negation.append(-var if val else var)
        cnf.append(negation)
        
        solver = DPLLSolver(cnf)
        solutions += 1
    
    return solutions


# ============== 随机CNF生成 ==============

def generate_random_cnf(n_vars: int, n_clauses: int, clause_size: int = 3,
                         seed: int = None) -> List[List[int]]:
    """
    生成随机k-SAT实例
    
    Args:
        n_vars: 变量数
        n_clauses: 子句数
        clause_size: 每个子句的文字数（k）
        seed: 随机种子
        
    Returns:
        CNF公式
    """
    if seed is not None:
        random.seed(seed)
    
    cnf = []
    for _ in range(n_clauses):
        clause = []
        seen = set()
        while len(clause) < clause_size:
            var = random.randint(1, n_vars)
            lit = var if random.random() > 0.5 else -var
            if var not in seen:
                clause.append(lit)
                seen.add(var)
        cnf.append(clause)
    
    return cnf


def generate_hard_cnf(n_vars: int, target_ratio: float = 4.24) -> List[List[int]]:
    """
    生成接近相变点的困难实例
    
    Args:
        n_vars: 变量数
        target_ratio: 子句数/变量数（4.24接近3-SAT相变）
    """
    n_clauses = int(n_vars * target_ratio)
    return generate_random_cnf(n_vars, n_clauses, clause_size=3)


# ============== 公式简化 ==============

def eliminate_pure(cnf: List[List[int]]) -> List[List[int]]:
    """消除纯文字（不改变可满足性）"""
    if not cnf:
        return cnf
    
    # 统计每个变量的出现极性
    pos_vars: Set[int] = set()
    neg_vars: Set[int] = set()
    
    for clause in cnf:
        for lit in clause:
            if lit > 0:
                pos_vars.add(lit)
            else:
                neg_vars.add(-lit)
    
    # 找出纯文字
    pure_pos = pos_vars - neg_vars
    pure_neg = neg_vars - pos_vars
    pure = pure_pos | {-v for v in pure_neg}
    
    # 删除包含纯文字的子句
    result = []
    for clause in cnf:
        if not any(abs(lit) in pure for lit in clause):
            new_clause = [lit for lit in clause if abs(lit) not in pure]
            if new_clause:
                result.append(new_clause)
    
    return result


def self_subsumption(cnf: List[List[int]]) -> List[List[int]]:
    """
    自我吸收简化
    
    若子句C包含子句D，则删除C（因为D→C）
    """
    result = list(cnf)
    changed = True
    
    while changed:
        changed = False
        new_result = []
        
        for i, c1 in enumerate(result):
            subsumed = False
            for j, c2 in enumerate(result):
                if i == j:
                    continue
                # 检查c2是否包含c1
                c1_set = set(c1)
                c2_set = set(c2)
                if c1_set <= c2_set:
                    subsumed = True
                    break
            
            if not subsumed:
                new_result.append(c1)
            else:
                changed = True
        
        result = new_result
    
    return result


def example_generate():
    """随机CNF生成示例"""
    cnf = generate_random_cnf(10, 50, seed=42)
    print(f"生成10变量50子句3-SAT:")
    print(f"  子句数: {len(cnf)}")
    print(f"  前3子句: {cnf[:3]}")


def example_verify():
    """解验证示例"""
    cnf = [[1, 2], [-1, 3], [-2, -3]]
    
    # 正确的解
    good = {1: True, 2: False, 3: True}
    print(f"解验证: {verify_solution(cnf, good)}")
    
    # 错误的解
    bad = {1: False, 2: False, 3: False}
    print(f"解验证: {verify_solution(cnf, bad)}")


def example_simplify():
    """公式简化示例"""
    cnf = [
        [1, 2, 3],
        [-1, 4],
        [-2],
        [2, 3],
        [1, -3, 4]
    ]
    
    print(f"原始子句数: {len(cnf)}")
    
    cnf = remove_tautologies(cnf)
    print(f"删除重言式后: {len(cnf)}")
    
    cnf = eliminate_pure(cnf)
    print(f"消除纯文字后: {len(cnf)}")


if __name__ == "__main__":
    print("=" * 50)
    print("SAT求解器工具集 测试")
    print("=" * 50)
    
    example_generate()
    print()
    example_verify()
    print()
    example_simplify()

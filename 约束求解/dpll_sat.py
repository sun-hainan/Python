# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / dpll_sat

本文件实现 dpll_sat 相关的算法功能。
"""

from typing import List, Dict, Set, Optional


def unit_propagate(clauses: List[Set[int]], assignment: Dict[int, bool]) -> List[Set[int]]:
    """
    单元传播 (Unit Propagation)
    
    参数:
        clauses: 子句列表，每个子句是文字集合（整数，正=正文字，负=负文字）
        assignment: 当前赋值字典 {变量ID: True/False}
    
    返回:
        传播后的子句集合
    
    算法：
    反复检查是否存在单元子句（只有一个未赋值文字的子句），
    如果存在则将其赋值并传播，更新所有子句。
    """
    changed = True
    while changed:
        changed = False
        # 存储本轮需要删除的子句和需要消除的文字
        to_remove = []
        
        for clause in clauses:
            # 计算该子句中尚未赋值的文字
            unassigned = []
            satisfied = False
            
            for literal in clause:
                var = abs(literal)
                if var not in assignment:
                    unassigned.append(literal)
                else:
                    # 检查子句是否已满足
                    if (literal > 0 and assignment[var]) or (literal < 0 and not assignment[var]):
                        satisfied = True
                        break
            
            if satisfied:
                continue
            
            # 单元子句：只有一个未赋值的文字
            if len(unassigned) == 1:
                literal = unassigned[0]
                var = abs(literal)
                val = literal > 0
                
                # 如果该变量的已有赋值与单元子句冲突，则失败
                if var in assignment and assignment[var] != val:
                    return []  # 冲突，返回空列表表示失败
                
                assignment[var] = val
                changed = True
        
        if changed:
            # 重新构建子句列表，移除已满足的子句
            new_clauses = []
            for clause in clauses:
                # 检查子句是否已被满足
                satisfied = False
                new_clause = set()
                
                for literal in clause:
                    var = abs(literal)
                    if var in assignment:
                        if (literal > 0 and assignment[var]) or (literal < 0 and not assignment[var]):
                            satisfied = True
                            break
                    else:
                        new_clause.add(literal)
                
                if not satisfied:
                    new_clauses.append(new_clause)
            
            clauses = new_clauses
    
    return clauses


def pure_literal_elimination(clauses: List[Set[int]], assignment: Dict[int, bool]) -> List[Set[int]]:
    """
    单子句消除 (Pure Literal Elimination)
    
    参数:
        clauses: 子句列表
        assignment: 当前赋值
    
    返回:
        消除纯文字后的子句列表
    
    算法：
    找出只出现正文字或只出现负文字的变量，将其固定为能消除子句的值。
    """
    # 统计每个变量的正负出现情况
    positive = set()
    negative = set()
    
    for clause in clauses:
        for literal in clause:
            var = abs(literal)
            if literal > 0:
                positive.add(var)
            else:
                negative.add(var)
    
    # 找出纯文字变量
    pure_positive = positive - negative
    pure_negative = negative - positive
    
    # 删除纯文字相关的子句
    new_clauses = []
    for clause in clauses:
        new_clause = set()
        for literal in clause:
            var = abs(literal)
            # 跳过纯文字（已被固定）
            if var in pure_positive or var in pure_negative:
                continue
            new_clause.add(literal)
        
        if new_clause:
            new_clauses.append(new_clause)
    
    return new_clauses


def choose_literal(clauses: List[Set[int]]) -> int:
    """
    分支启发式：选择要赋值的文字
    
    参数:
        clauses: 子句列表
    
    返回:
        被选中的文字（整数）
    
    启发式策略：选择出现频率最高的文字（Jeroslow-Wang 启发式）
    """
    # Jeroslow-Wang 启发式：优先选择短子句中的文字
    scores = {}
    for clause in clauses:
        weight = 2 ** (-len(clause))  # 短子句权重更高
        for literal in clause:
            var = abs(literal)
            scores[var] = scores.get(var, 0) + weight
    
    if not scores:
        return 0
    
    return max(scores, key=scores.get)


def dpll(clauses: List[Set[int]], assignment: Optional[Dict[int, bool]] = None) -> Optional[Dict[int, bool]]:
    """
    DPLL 主算法
    
    参数:
        clauses: 子句列表（CNF 格式）
        assignment: 当前部分赋值
    
    返回:
        满足赋值，如果不可满足则返回 None
    
    算法流程：
    1. 单元传播
    2. 单子句消除
    3. 如果所有子句满足，返回成功
    4. 如果存在空子句，返回失败
    5. 选择文字，分支尝试
    """
    if assignment is None:
        assignment = {}
    
    # 复制子句避免修改原数据
    current_clauses = [clause.copy() for clause in clauses]
    
    # 步骤1：单元传播
    current_clauses = unit_propagate(current_clauses, assignment)
    
    # 检查是否失败（存在空子句）
    for clause in current_clauses:
        if len(clause) == 0:
            return None
    
    # 检查是否成功（所有子句已满足）
    if not current_clauses:
        return assignment
    
    # 步骤2：单子句消除
    current_clauses = pure_literal_elimination(current_clauses, assignment)
    
    if not current_clauses:
        return assignment
    
    # 步骤3：选择分支文字
    literal = choose_literal(current_clauses)
    var = abs(literal)
    
    # 分支尝试：先尝试 False
    assignment_attempt = assignment.copy()
    assignment_attempt[var] = False
    
    # 构建简化后的子句（假设 var = False）
    simplified = []
    for clause in current_clauses:
        new_clause = set()
        for lit in clause:
            if abs(lit) == var:
                # 如果 lit 是正文字(var>0)，在 var=False 时不满足，跳过
                # 如果 lit 是负文字(var<0)，在 var=False 时满足，消除
                if lit > 0:
                    continue  # 正文字在 False 时不满足
                else:
                    pass  # 负文字在 False 时满足，消除此文字
            new_clause.add(lit)
        
        if not new_clause:
            return None  # 出现空子句
        simplified.append(new_clause)
    
    result = dpll(simplified, assignment_attempt)
    if result is not None:
        return result
    
    # 分支尝试：再尝试 True
    assignment[var] = True
    return dpll(current_clauses, assignment)


def parse_cnf(cnf_str: str) -> List[Set[int]]:
    """
    解析 CNF 格式字符串
    
    参数:
        cnf_str: CNF 格式字符串，如 "1 -2 0\n-1 3 0\n"
    
    返回:
        子句列表
    """
    clauses = []
    for line in cnf_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        clause = set()
        for token in line.split():
            if token == '0':
                break
            literal = int(token)
            clause.add(literal)
        if clause:
            clauses.append(clause)
    return clauses


def solve_sat(clauses: List[Set[int]]) -> Optional[Dict[int, bool]]:
    """
    SAT 求解器入口
    
    参数:
        clauses: CNF 子句列表
    
    返回:
        满足赋值或 None
    """
    return dpll(clauses)


if __name__ == "__main__":
    # 测试用例 1：简单可满足实例
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3)
    test_cnf_1 = [
        {1, 2},
        {-1, 3},
        {-2, 3}
    ]
    
    result = solve_sat(test_cnf_1)
    print("测试1 - 简单可满足实例:")
    print(f"  公式: (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3)")
    print(f"  结果: {result}")
    
    # 验证结果
    if result:
        for clause in test_cnf_1:
            satisfied = any(
                (lit > 0 and result[abs(lit)]) or (lit < 0 and not result[abs(lit)])
                for lit in clause
            )
            print(f"    子句 {clause} 满足: {satisfied}")
    
    print()
    
    # 测试用例 2：不可满足实例（p ∧ ¬p）
    test_cnf_2 = [
        {1},
        {-1}
    ]
    
    result = solve_sat(test_cnf_2)
    print("测试2 - 不可满足实例:")
    print(f"  公式: p ∧ ¬p")
    print(f"  结果: {result}")
    
    print()
    
    # 测试用例 3：使用 CNF 字符串解析
    cnf_str = "1 2 0\n-1 3 0\n-2 -3 0"
    test_cnf_3 = parse_cnf(cnf_str)
    result = solve_sat(test_cnf_3)
    print("测试3 - 解析 CNF 字符串:")
    print(f"  CNF: {cnf_str}")
    print(f"  结果: {result}")
    
    print()
    print("=" * 50)
    print("复杂度分析:")
    print("  时间复杂度: 最坏 O(2^n)，n 为变量数")
    print("  空间复杂度: O(n) 递归栈深度")
    print("  实际性能取决于子句结构和启发式选择")

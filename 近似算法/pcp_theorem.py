# -*- coding: utf-8 -*-
"""
算法实现：近似算法 / pcp_theorem

本文件实现 pcp_theorem 相关的算法功能。
"""

import numpy as np
import random


def generate_random_query_positions(num_variables, num_queries, random_seed=None):
    """
    生成随机查询位置
    
    PCP 验证者随机选择要检查的变量位置
    
    Parameters
    ----------
    num_variables : int
        变量的总数量 n
    num_queries : int
        每次验证查询的位数 q (常数)
    random_seed : int
        随机种子,用于复现
    
    Returns
    -------
    list
        查询位置的列表
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    # 随机生成 num_queries 个不重复的位置索引
    query_positions = random.sample(range(num_variables), num_queries)
    return query_positions


def verify_csp_assignment(proof, constraints, num_queries=3, random_seed=None):
    """
    验证 CSP 赋值是否满足所有约束
    
    标准 PCP 验证流程:
    1. 验证者随机选择一个小约束子集
    2. 仅读取证明的 O(1) 个位置
    3. 检查这些位置的赋值是否满足约束
    
    Parameters
    ----------
    proof : list or dict
        证明字符串/赋值列表,proof[i] 表示变量 i 的赋值
    constraints : list
        约束列表,每个约束是 (变量列表, 谓词函数)
    num_queries : int
        随机查询的位数
    random_seed : int
        随机种子
    
    Returns
    -------
    tuple
        (是否接受, 检查的约束, 检查的赋值)
    """
    n = len(proof)
    
    # 生成随机查询位置
    query_positions = generate_random_query_positions(n, num_queries, random_seed)
    
    # 读取这些位置的赋值
    queried_assignments = [proof[pos] for pos in query_positions]
    
    # 验证这些赋值是否满足某个约束
    # 这里简化处理: 随机选择一个约束检查
    random.seed(random_seed)
    constraint_idx = random.randint(0, len(constraints) - 1)
    selected_constraint = constraints[constraint_idx]
    
    vars_in_constraint = selected_constraint[0]
    predicate = selected_constraint[1]
    
    # 检查约束涉及的变量是否在查询位置中
    # 如果是,验证谓词是否满足
    relevant_assignments = {}
    for var_idx in vars_in_constraint:
        if var_idx in query_positions:
            relevant_assignments[var_idx] = proof[var_idx]
    
    # 如果所有涉及的变量都被查询到了,验证谓词
    if len(relevant_assignments) == len(vars_in_constraint):
        accept = predicate(relevant_assignments)
    else:
        # 部分查询,保守拒绝
        accept = False
    
    return accept, selected_constraint, queried_assignments


def build_3sat_to_csp_reduction(formula):
    """
    3SAT 到 CSP 的归约
    
    每个子句对应一个约束:
    - 子句 (x1 ∨ ¬x2 ∨ x3) 满足当且仅当至少一个文字为真
    
    这是 PCP 归约的基础步骤
    
    Parameters
    ----------
    formula : list
        3SAT 公式,每个元素是子句列表
    
    Returns
    -------
    tuple
        (变量数, 约束列表)
    """
    num_variables = len(formula[0][0]) if formula else 0
    constraints = []
    
    for clause in formula:
        # clause 格式: [(var_idx, is_positive), ...]
        vars_in_clause = [v for v, _ in clause]
        
        # 谓词: 至少一个文字为真
        def predicate(assignments, vars_list=vars_in_clause):
            for var_idx in vars_list:
                literal_val = assignments.get(var_idx, False)
                # 判断是正文字还是负文字
                # 简化: 假设 clause 中存储的是 (var_idx, is_positive)
                is_pos = True  # 这里简化处理
                if is_pos:
                    if literal_val:
                        return True
                else:
                    if not literal_val:
                        return True
            return False
        
        constraints.append((vars_in_clause, predicate))
    
    return num_variables, constraints


def pcp_amplification(num_repetitions, proof, constraints, num_queries=3):
    """
    PCP 放大: 重复验证提高可靠性
    
    核心思想:
    - 单次验证的错误概率为 1/2
    - 重复 t 次后,错误概率降至 (1/2)^t
    - 仍保持 O(log n + t) 随机位数
    
    Parameters
    ----------
    num_repetitions : int
        重复验证次数 t
    proof : list
        证明
    constraints : list
        约束列表
    num_queries : int
        每次验证查询的位数
    
    Returns
    -------
    tuple
        (所有验证是否通过, 每次验证的随机种子)
    """
    random_seeds = []
    all_accept = True
    
    for i in range(num_repetitions):
        seed = random.randint(0, 2**31 - 1)
        random_seeds.append(seed)
        
        accept, _, _ = verify_csp_assignment(
            proof, constraints, num_queries, seed
        )
        
        if not accept:
            all_accept = False
            break
    
    return all_accept, random_seeds


def gap_amplification_for_3sat(formula, assignment, epsilon):
    """
    3SAT 的 Gap 放大
    
    完全满足 (satisfiable) vs 
    最多满足 (1-ε) 比例的子句 (unsatisfiable)
    
    这是 PCP 定理用于硬度证明的核心
    
    Parameters
    ----------
    formula : list
        3SAT 公式
    assignment : list
        赋值
    epsilon : float
        缺口参数
    
    Returns
    -------
    tuple
        (满足的子句数, 总子句数, 是否满足阈值)
    """
    if not formula:
        return 0, 0, True
    
    total_clauses = len(formula)
    satisfied_clauses = 0
    
    for clause in formula:
        # 检查子句是否满足
        clause_satisfied = False
        for var_idx, is_positive in clause:
            var_val = assignment[var_idx] if var_idx < len(assignment) else False
            if is_positive and var_val:
                clause_satisfied = True
                break
            elif not is_positive and not var_val:
                clause_satisfied = True
                break
        
        if clause_satisfied:
            satisfied_clauses += 1
    
    threshold = (1 - epsilon) * total_clauses
    meets_threshold = satisfied_clauses >= threshold
    
    return satisfied_clauses, total_clauses, meets_threshold


def arora_safra_framework(num_variables, constraint_graph):
    """
    Arora-Safra PCP 框架
    
    将 NP 证明转换为可概率检查的格式:
    1. 证明分为多个区块 (oracle access)
    2. 验证者检查区块间的一致性
    3. 通过低度扩展验证局部区域
    
    Parameters
    ----------
    num_variables : int
        变量数量
    constraint_graph : dict
        约束图,邻接表表示
    
    Returns
    -------
    function
        验证函数
    """
    def verify(proof, randomness, queries):
        """
        验证函数
        """
        # 检查查询位置的赋值
        queried = [proof[q] for q in queries]
        
        # 检查一致性约束
        # 简化: 检查所有查询位置的值是否相同 (恒真约束)
        consistency_check = len(set(queried)) == 1
        
        return consistency_check
    
    return verify


def local_testing_distance(assignment, proof, num_samples=100):
    """
    计算局部测试的汉明距离
    
    用于衡量"好"证明与实际证明的接近程度
    
    Parameters
    ----------
    assignment : list
        正确赋值
    proof : list
        待测证明
    num_samples : int
        采样数量
    
    Returns
    -------
    float
        归一化汉明距离 [0, 1]
    """
    n = len(proof)
    disagreements = 0
    
    for _ in range(num_samples):
        idx = random.randint(0, n - 1)
        if idx < len(assignment) and assignment[idx] != proof[idx]:
            disagreements += 1
    
    return disagreements / num_samples


if __name__ == "__main__":
    # 测试: PCP 定理核心概念
    
    print("=" * 60)
    print("PCP 定理核心思想测试")
    print("=" * 60)
    
    # 设置随机种子
    np.random.seed(42)
    random.seed(42)
    
    # 示例: 简单的 CSP
    # 变量 x0, x1, x2, x3
    n_vars = 4
    proof = [True, False, True, False]  # 假设的证明/赋值
    
    # 约束: x0 = x2, x1 ≠ x3, x0 ∨ x1
    constraints = []
    
    # 约束1: x0 = x2
    def eq_constraint(assignments):
        return len(set(assignments.values())) == 1
    
    constraints.append(([0, 2], eq_constraint))
    
    # 约束2: x1 ≠ x3
    def neq_constraint(assignments):
        vals = list(assignments.values())
        return vals[0] != vals[1]
    
    constraints.append(([1, 3], neq_constraint))
    
    # 约束3: x0 ∨ x1 (至少一个为真)
    def or_constraint(assignments):
        return any(assignments.values())
    
    constraints.append(([0, 1], or_constraint))
    
    print(f"\n变量数量: {n_vars}")
    print(f"证明: {proof}")
    print(f"约束数量: {len(constraints)}")
    
    # 测试随机查询验证
    print("\n--- 随机查询验证 ---")
    for trial in range(3):
        seed = random.randint(0, 1000)
        accept, constraint, values = verify_csp_assignment(
            proof, constraints, num_queries=2, random_seed=seed
        )
        print(f"试验 {trial + 1}: {'接受' if accept else '拒绝'}, 约束={constraint[0]}")
    
    # 测试放大
    print("\n--- PCP 放大 (重复验证) ---")
    repetitions = 5
    all_accept, seeds = pcp_amplification(repetitions, proof, constraints, num_queries=2)
    print(f"重复 {repetitions} 次: {'全部接受' if all_accept else '存在拒绝'}")
    print(f"使用的随机种子: {seeds}")
    
    # 测试局部测试距离
    print("\n--- 局部测试距离 ---")
    correct_assignment = [True, False, True, False]
    noisy_proof = [True, True, True, False]  # 添加噪声
    distance = local_testing_distance(correct_assignment, noisy_proof, num_samples=50)
    print(f"正确赋值: {correct_assignment}")
    print(f"噪声证明: {noisy_proof}")
    print(f"汉明距离: {distance:.2f}")
    
    # 测试 Gap 放大
    print("\n--- Gap 放大 ---")
    # 简单公式: (x0 ∨ x1) ∧ (¬x0 ∨ x2) ∧ (x1 ∨ ¬x2)
    test_formula = [
        [(0, True), (1, True)],   # x0 ∨ x1
        [(0, False), (2, True)],  # ¬x0 ∨ x2
        [(1, True), (2, False)],  # x1 ∨ ¬x2
    ]
    test_assignment = [True, True, True]  # 满足所有
    
    for eps in [0.3, 0.5, 0.7]:
        satisfied, total, meets = gap_amplification_for_3sat(
            test_formula, test_assignment, eps
        )
        ratio = satisfied / total if total > 0 else 0
        print(f"ε={eps}: 满足 {satisfied}/{total} ({ratio:.2f}), 阈值={1-eps:.2f}, 通过={meets}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

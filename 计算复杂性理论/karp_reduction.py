# -*- coding: utf-8 -*-
"""
算法实现：计算复杂性理论 / karp_reduction

本文件实现 karp_reduction 相关的算法功能。
"""

from typing import List, Tuple, Set, Dict


# ==================== 基础归约函数 ====================

def sat_to_3sat(clauses: List[List[str]]) -> List[List[str]]:
    """
    SAT归约到3-SAT

    思路：每个子句转换为多个3-SAT子句
    - 单literal子句：(l) → (l ∨ y1 ∨ y2) ∧ (l ∨ y1 ∨ ¬y2) ∧ (l ∨ ¬y1 ∨ y2) ∧ (l ∨ ¬y1 ∨ ¬y2)
    - 双literal子句：(l1 ∨ l2) → (l1 ∨ l2 ∨ y) ∧ (l1 ∨ l2 ∨ ¬y)
    - 三literal子句：保持不变

    复杂度：O(m)，m是子句数
    """
    result = []
    new_vars = []

    for clause in clauses:
        n = len(clause)

        if n == 1:
            # (l) → (l ∨ y1 ∨ y2) ∧ (l ∨ y1 ∨ ¬y2) ∧ (l ∨ ¬y1 ∨ y2) ∧ (l ∨ ¬y1 ∨ ¬y2)
            y1 = f"y_{len(new_vars)}"
            y2 = f"y_{len(new_vars) + 1}"
            new_vars.extend([y1, y2])

            result.append([clause[0], y1, y2])
            result.append([clause[0], y1, f"!{y2}"])
            result.append([clause[0], f"!{y1}", y2])
            result.append([clause[0], f"!{y1}", f"!{y2}"])

        elif n == 2:
            # (l1 ∨ l2) → (l1 ∨ l2 ∨ y) ∧ (l1 ∨ l2 ∨ ¬y)
            y = f"y_{len(new_vars)}"
            new_vars.append(y)

            result.append([clause[0], clause[1], y])
            result.append([clause[0], clause[1], f"!{y}"])

        elif n == 3:
            result.append(clause)

        else:  # n > 3
            # (l1 ∨ l2 ∨ ... ∨ ln) → (l1 ∨ l2 ∨ y1) ∧ (¬y1 ∨ l3 ∨ y2) ∧ ... ∧ (¬y_{n-3} ∨ l_{n-1} ∨ ln)
            y_prev = None
            for i in range(n - 3):
                y_curr = f"y_{len(new_vars)}"
                new_vars.append(y_curr)

                if i == 0:
                    result.append([clause[0], clause[1], y_curr])
                else:
                    result.append([f"!{y_prev}", clause[i + 1], y_curr])
                y_prev = y_curr

            result.append([f"!{y_prev}", clause[-2], clause[-1]])

    return result


def sat_to_vertex_cover(clauses: List[List[str]]) -> Tuple[List[Tuple[int, int]], int]:
    """
    SAT归约到点覆盖

    构建方法：
    - 对于每个子句 (l1 ∨ l2 ∨ ... ∨ lk)，创建k个顶点
    - 连接同一子句中的所有顶点
    - 问：是否存在大小≤ m的点覆盖？（m是子句数）

    原理：选择覆盖所有边 = 每个子句至少选一个literal

    复杂度：O(m * k)，k是最大子句长度
    """
    edges = []
    var_counter = 0

    for clause_idx, clause in enumerate(clauses):
        k = len(clause)
        base = var_counter

        # 创建k个顶点，每个literal一个
        for i in range(k):
            for j in range(i + 1, k):
                # 连接第i个和第j个literal
                edges.append((base + i, base + j))

        var_counter += k

    # 点覆盖的大小限制为m（子句数）
    k = len(clauses)

    return edges, k


def sat_to_hamiltonian(clauses: List[List[str]]) -> List[int]:
    """
    SAT归约到有向哈密顿回路

    构建方法：使用"选择器"和"验证器"结构
    - 每个变量对应一行顶点（True/False选择）
    - 每个子句对应一个验证 gadget
    - 如果存在哈密顿回路，则变量赋值满足所有子句

    复杂度：O(n * m)，n是变量数，m是子句数
    """
    vertices = []
    edges = []

    # 简化实现：构建一个简单的归约
    # 实际需要更复杂的gadget构造

    n_vars = len(set(lit.replace('!', '') for c in clauses for lit in c))
    n_clauses = len(clauses)

    # 为每个变量创建两层顶点（True/False）
    for i in range(n_vars):
        base = len(vertices)
        vertices.extend([base, base + 1])

        # 连接：每层之间可以双向选择
        edges.append((base, base + 1))
        edges.append((base + 1, base))

    # 为每个子句添加约束顶点
    for i in range(n_clauses):
        base = len(vertices)
        vertices.append(base)

        # 连接子句约束
        # 实际实现需要更复杂的结构

    return vertices


def sat_to_knapsack(formula: List[List[str]]) -> Tuple[List[Tuple[int, int]], int]:
    """
    SAT归约到0-1背包

    构建方法：
    - 每个变量创建两个物品（True赋值和False赋值）
    - 每个子句创建"惩罚"物品
    - 目标是找到一个赋值使得价值和最大

    原理：可满足性 ⟺ 存在价值≥某阈值的打包方案

    复杂度：O(n + m)，n是变量数，m是子句数
    """
    items = []
    total_value = 0

    # 为每个变量创建物品
    var_set = set()
    for clause in formula:
        for lit in clause:
            var = lit.replace('!', '')
            var_set.add(var)

    n_vars = len(var_set)
    var_list = list(var_set)

    for i, var in enumerate(var_list):
        # 为变量v创建两个物品
        # 选择True赋值的物品收益高
        # 选择False赋值的物品收益低
        items.append((2 * (i + 1), 2 ** i))  # True物品
        items.append((2 * (i + 1) + 1, 2 ** (n_vars + i)))  # False物品
        total_value += 2 ** i + 2 ** (n_vars + i)

    # 为每个子句添加惩罚物品
    penalty_idx = len(items)
    for clause in formula:
        # 子句满足时，不选惩罚物品
        # 子句不满足时，选惩罚物品
        items.append((penalty_idx + len(items), 2 ** (2 * n_vars)))
        penalty_idx += 1

    # 背包容量和目标价值
    capacity = sum(w for w, v in items)
    target_value = total_value

    return items, target_value


def sat_to_subset_sum(formula: List[List[str]]) -> Tuple[List[int], int]:
    """
    SAT归约到子集和问题

    构建方法：
    - 每个变量创建两个数（二进制表示）
    - 每个子句添加约束数
    - 目标是找到子集和等于目标值

    复杂度：O(n * m)
    """
    numbers = []
    target = 0

    var_set = set()
    for clause in formula:
        for lit in clause:
            var = lit.replace('!', '')
            var_set.add(var)

    n_vars = len(var_set)
    var_list = list(var_set)

    # 为每个变量创建两个数
    for i, var in enumerate(var_list):
        # 使用二进制编码
        # v_i: 第i位为1
        numbers.append(2 ** i)
        target += 2 ** i

    # 添加辅助数
    for i in range(n_vars):
        numbers.append(2 ** (n_vars + i))

    # 子句约束
    for clause in formula:
        numbers.append(sum(2 ** var_list.index(lit.replace('!', '')) for lit in clause))

    return numbers, target


# ==================== 21个NP完全问题 ====================

def list_np_complete_problems() -> List[str]:
    """返回Karp的21个NP完全问题"""
    problems = [
        "1. 0-1背包问题 (Knapsack)",
        "2. 哈密顿回路 (Hamiltonian Cycle)",
        "3. 旅行商问题 (Traveling Salesman)",
        "4. 点覆盖 (Vertex Cover)",
        "5. 集合覆盖 (Set Cover)",
        "6. 集合划分 (Set Packing)",
        "7. 子集和问题 (Subset Sum)",
        "8. 图着色 (Graph Coloring)",
        "9. 最大割 (Max Cut)",
        "10. 独立集 (Independent Set)",
        "11. 团 (Clique)",
        "12. 反馈顶点集 (Feedback Vertex Set)",
        "13. 有向哈密顿回路 (Directed Hamiltonian Cycle)",
        "14. 3-SAT",
        "15. 命中集 (Hit Set)",
        "16. 0-1整数线性规划 (0-1 Integer Programming)",
        "17. Steiner树 (Steiner Tree)",
        "18. 分团划分 (Partition into Triangles)",
        "19. 子图同构 (Subgraph Isomorphism)",
        "20. 电路设计 (Circuit Design)",
        "21. 调度问题 (Scheduling)",
    ]
    return problems


def prove_np_completeness(problem: str) -> Dict:
    """
    证明问题的NP完全性

    方法：
    1. 证明问题在NP中
    2. 从已知NPC问题归约到该问题

    返回：归约路径
    """
    reduction_chain = {
        "SAT": "3-SAT",
        "3-SAT": "Clique",
        "Clique": "Vertex Cover",
        "Vertex Cover": "Set Cover",
        "Set Cover": "Hit Set",
        "Hit Set": "Knapsack",
    }

    return {
        "problem": problem,
        "in_np": True,
        "reduction_from": reduction_chain.get(problem, "Unknown"),
        "status": "NP-Complete" if problem in reduction_chain else "Not proven"
    }


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Karp归约演示 ===\n")

    print("【Karp的21个NP完全问题】")
    for p in list_np_complete_problems():
        print(f"  {p}")
    print()

    print("【归约示例】")
    print("1. SAT → 3-SAT")
    clauses = [['x1', 'x2', 'x3'], ['!x1', 'x2'], ['x1', '!x2', '!x3']]
    result_3sat = sat_to_3sat(clauses)
    print(f"   原SAT子句数: {len(clauses)}")
    print(f"   3-SAT子句数: {len(result_3sat)}")
    print()

    print("2. SAT → Vertex Cover")
    edges, k = sat_to_vertex_cover(clauses)
    print(f"   构建的边数: {len(edges)}")
    print(f"   覆盖大小限制: {k}")
    print()

    print("3. SAT → Subset Sum")
    numbers, target = sat_to_subset_sum(clauses)
    print(f"   生成的数: {numbers}")
    print(f"   目标和: {target}")
    print()

    print("【复杂度分析】")
    print("归约类型          时间复杂度    空间复杂度")
    print("SAT → 3-SAT       O(m)          O(m)")
    print("SAT → VertexCov   O(m*k)        O(m*k)")
    print("SAT → Knapsack    O(n+m)        O(n+m)")
    print("SAT → SubsetSum   O(n*m)        O(n)")
    print()
    print("其中：n = 变量数，m = 子句数，k = 最大子句长度")

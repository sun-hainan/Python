# -*- coding: utf-8 -*-

"""

算法实现：计算复杂性理论 / hamiltonian_cycle



本文件实现 hamiltonian_cycle 相关的算法功能。

"""



from typing import List, Tuple, Set, Optional





# ==================== 哈密顿回路验证 ====================



def verify_hamiltonian_cycle(vertices: List[int], edges: List[Tuple[int, int]],

                             cycle: List[int]) -> bool:

    """

    验证是否是一个有效的哈密顿回路



    条件：

    1. 回路包含所有顶点

    2. 回路中相邻顶点之间有边

    3. 回路首尾相连



    复杂度：O(n + m)

    """

    n = len(vertices)



    # 检查是否包含所有顶点

    if len(set(cycle)) != n:

        return False



    # 检查长度

    if len(cycle) != n:

        return False



    # 检查边是否存在

    edge_set = set(edges)

    for i in range(n):

        u, v = cycle[i], cycle[(i + 1) % n]

        if (u, v) not in edge_set and (v, u) not in edge_set:

            return False



    return True





def find_hamiltonian_cycle_backtracking(vertices: List[int], edges: List[Tuple[int, int]]) -> Optional[List[int]]:

    """

    使用回溯法找哈密顿回路



    复杂度：O(n!) - 指数级

    仅适用于小图

    """

    n = len(vertices)

    edge_set = set(edges)



    adj = {v: set() for v in vertices}

    for u, v in edges:

        adj[u].add(v)

        adj[v].add(u)



    path = [vertices[0]]

    visited = {vertices[0]}



    def backtrack() -> bool:

        if len(path) == n:

            # 检查最后一边

            return path[-1] in adj[path[0]]



        for neighbor in adj[path[-1]]:

            if neighbor not in visited:

                visited.add(neighbor)

                path.append(neighbor)

                if backtrack():

                    return True

                path.pop()

                visited.remove(neighbor)



        return False



    if backtrack():

        return path

    return None





# ==================== NP完全性证明 ====================



def prove_hamcycle_np():

    """

    证明HamCycle ∈ NP



    验证器V(G, C)：

    1. 检查C是V中顶点的排列（包含所有顶点）

    2. 检查相邻顶点之间有边

    3. 检查首尾顶点之间有边



    复杂度：O(|V| + |E|)

    """

    print("【步骤1：证明HamCycle ∈ NP】")

    print()

    print("验证器V(G=(V,E), C=(v1,v2,...,vk)):")

    print("  1. 检查C是V的排列且k=|V|")

    print("  2. 对于i=1到n-1，检查(vi, vi+1)∈E")

    print("  3. 检查(vn, v1)∈E")

    print()

    print("验证时间：O(|V| + |E|) = 多项式时间")

    print("因此HamCycle ∈ NP")

    print()





def build_reduction_gadget(var_name: str, clause_indices: List[int]) -> Tuple[List[int], List[Tuple[int, int]]]:

    """

    为变量构建归约gadget（用于3-SAT → HamCycle）



    每个变量x对应一个"选择器" gadget：

    - 两个平行路径（True和False选择）

    - 长度等于子句数

    - 每个位置可以"跳转到"某个子句验证 gadget



    参数：

        var_name: 变量名

        clause_indices: 该变量出现的子句索引列表



    返回：(顶点列表, 边列表)

    """

    vertices = []

    edges = []



    # 每个子句位置创建两个顶点（True/False）

    base = len(vertices)

    for i in range(len(clause_indices) + 1):

        vertices.append(base + i)  # True路径

        vertices.append(base + len(clause_indices) + 1 + i)  # False路径



    # 连接True路径

    for i in range(len(clause_indices)):

        edges.append((base + i, base + i + 1))

    edges.append((base + len(clause_indices), base))  # 形成环



    # 连接False路径

    offset = len(clause_indices) + 1

    for i in range(len(clause_indices)):

        edges.append((base + offset + i, base + offset + i + 1))

    edges.append((base + offset + len(clause_indices), base + offset))



    return vertices, edges





def hamcycle_reduction_from_3sat(formula: List[List[str]]) -> Tuple[List[int], List[Tuple[int, int]]]:

    """

    从3-SAT归约到哈密顿回路



    归约结构：

    1. 每个变量创建一个选择gadget

    2. 每个子句创建一个验证gadget

    3. 选择gadget和验证gadget之间通过特定边连接



    复杂度：O(n * m)

    """

    vertices = []

    edges = []



    # 收集变量

    var_to_clauses = {}

    for clause_idx, clause in enumerate(formula):

        for lit in clause:

            var = lit.replace('!', '')

            if var not in var_to_clauses:

                var_to_clauses[var] = []

            var_to_clauses[var].append(clause_idx)



    # 为每个变量构建gadget

    for var, clause_list in var_to_clauses.items():

        gadget_v, gadget_e = build_reduction_gadget(var, clause_list)

        edges_offset = len(vertices)

        vertices.extend([v + edges_offset for v in gadget_v])

        edges.extend(gadget_e)



    # 添加子句验证gadget（简化版）

    n_clauses = len(formula)

    clause_base = len(vertices)

    for i in range(n_clauses):

        vertices.append(clause_base + i)



    return vertices, edges





# ==================== 有向哈密顿回路 ====================



def directed_hamiltonian_cycle(vertices: List[int], edges: List[Tuple[int, int]]) -> Optional[List[int]]:

    """

    有向图中的哈密顿回路



    使用回溯法



    复杂度：O(n!)

    """

    n = len(vertices)

    edge_set = set(edges)



    out_edges = {v: [] for v in vertices}

    for u, v in edges:

        out_edges[u].append(v)



    path = [vertices[0]]

    visited = {vertices[0]}



    def backtrack() -> bool:

        if len(path) == n:

            return (path[-1], path[0]) in edge_set



        for neighbor in out_edges[path[-1]]:

            if neighbor not in visited:

                visited.add(neighbor)

                path.append(neighbor)

                if backtrack():

                    return True

                path.pop()

                visited.remove(neighbor)



        return False



    if backtrack():

        return path

    return None





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 哈密顿回路NP完全性证明 ===\n")



    prove_hamcycle_np()



    print("【步骤2：证明HamCycle是NP难的】")

    print()

    print("归约路径：SAT → 3-SAT → Directed Ham Cycle → Ham Cycle")

    print()

    print("归约：3-SAT ≤_p HamCycle")

    print("  - 每个变量对应一个选择gadget（两条平行路径）")

    print("  - 每个子句对应一个验证gadget")

    print("  - 存在哈密顿回路 ⟺ 公式可满足")

    print()



    print("【示例】")

    vertices = [0, 1, 2, 3]

    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 0)]



    print(f"图：G=({vertices}, {edges})")



    cycle = find_hamiltonian_cycle_backtracking(vertices, edges)

    if cycle:

        print(f"哈密顿回路：{cycle}")

        print(f"验证结果：{verify_hamiltonian_cycle(vertices, edges, cycle)}")

    else:

        print("不存在哈密顿回路")

    print()



    print("【复杂度分析】")

    print("验证时间：O(|V| + |E|)")

    print("搜索时间：O(|V|!) - 指数级")

    print("归约构建时间：O(n * m)")

    print()

    print("【应用】")

    print("  - 电路布线优化")

    print("  - 物流配送路线")

    print("  - DNA测序中的片段排序")


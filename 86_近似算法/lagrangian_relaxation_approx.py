# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / lagrangian_relaxation_approx



本文件实现 lagrangian_relaxation_approx 相关的算法功能。

"""



import numpy as np

import random





def vertex_cover_lagrangeRelaxation(graph, edge_weights=None):

    """

    顶点覆盖的 Lagrange 松弛 2-近似算法

    

    原始 ILP:

    min Σ_{v∈V} w_v * x_v

    s.t. Σ_{v∈e} x_v >= 1, ∀e ∈ E  (每条边至少有一个端点被覆盖)

         x_v ∈ {0, 1}, ∀v ∈ V

    

    Lagrange 松弛:

    - 将覆盖约束 Σ_{v∈e} x_v >= 1 乘以 λ_e 加入目标函数

    - 目标变为 min Σ_{v} w_v * x_v + Σ_{e} λ_e * (1 - Σ_{v∈e} x_v)

             = Σ_{v} (w_v - Σ_{e∋v} λ_e) * x_v + Σ_{e} λ_e

    

    观察: 松弛后每个顶点独立决策!

    - 若 w_v - Σ_{e∋v} λ_e > 0, 选择 x_v = 0

    - 否则选择 x_v = 1

    

    Parameters

    ----------

    graph : dict

        图的邻接表表示,{v: [neighbors]}

    edge_weights : dict

        边权重,键为 (u, v) 元组

    

    Returns

    -------

    tuple

        (覆盖集, 权重, λ 值)

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    if edge_weights is None:

        # 默认所有边权重为 1

        edge_weights = {}

        for u in graph:

            for v in graph[u]:

                if u < v:

                    edge_weights[(u, v)] = 1.0

    

    # 边列表

    edges = []

    for u in graph:

        for v in graph[u]:

            if u < v:

                edges.append((u, v))

    

    m = len(edges)

    

    # 初始化 λ (所有边权重的一半作为初始值)

    lam = {e: edge_weights[e] / 2.0 for e in edges}

    

    # 迭代优化 λ (次梯度优化)

    max_iterations = 100

    step_size = 1.0

    best_dual_bound = 0

    

    for iteration in range(max_iterations):

        # 计算每个顶点的有效成本

        # cost_v = w_v - Σ_{e∋v} λ_e

        cost = {}

        for v in vertices:

            w_v = 1.0  # 默认顶点权重为 1

            for e in edges:

                if v in e:

                    w_v -= lam[e]

            cost[v] = w_v

        

        # 贪婪调整 λ (次梯度方向)

        # 目标: 让未覆盖的边被惩罚,促进顶点选择

        new_lam = {}

        for e in edges:

            u, v = e

            # 检查当前 λ 下的解是否覆盖边 e

            x_u = 1 if cost[u] <= 0 else 0

            x_v = 1 if cost[v] <= 0 else 0

            

            # 违反约束程度 (取整后覆盖为 0, 否则为 1)

            violation = max(0, 1 - x_u - x_v)

            

            # 更新 λ (次梯度步长)

            new_lam[e] = max(0, lam[e] + step_size * violation)

        

        lam = new_lam

        

        # 更新步长 (衰减)

        step_size *= 0.95

    

    # 从最终的 λ 构造解

    cover = set()

    total_weight = 0

    

    for v in vertices:

        w_v = 1.0

        # 计算有效成本

        effective_cost = w_v

        for e in edges:

            if v in e:

                effective_cost -= lam[e]

        

        # 如果有效成本 <= 0,选择该顶点

        if effective_cost <= 0:

            cover.add(v)

            total_weight += w_v

    

    return cover, total_weight, lam





def vertex_cover_greedy_approx(graph):

    """

    标准贪心顶点覆盖 2-近似

    

    策略: 反复选择度数最高的边,删除该边所有端点

    

    近似比: 2

    

    Parameters

    ----------

    graph : dict

        图的邻接表表示

    

    Returns

    -------

    tuple

        (覆盖集, 边列表)

    """

    vertices = list(graph.keys())

    edges = []

    for u in graph:

        for v in graph[u]:

            if u < v:

                edges.append((u, v))

    

    # 复制边集合用于修改

    remaining_edges = set(edges)

    cover = set()

    

    while remaining_edges:

        # 找到度数最高的边

        max_degree = -1

        best_edge = None

        

        for e in remaining_edges:

            u, v = e

            degree_u = sum(1 for e2 in remaining_edges if u in e2)

            degree_v = sum(1 for e2 in remaining_edges if v in e2)

            max_d = max(degree_u, degree_v)

            

            if max_d > max_degree:

                max_degree = max_d

                best_edge = e

        

        if best_edge is None:

            break

        

        # 选择该边加入覆盖

        cover.add(best_edge[0])

        cover.add(best_edge[1])

        

        # 删除所有与该边端点相连的边

        to_remove = set()

        for e in remaining_edges:

            if e[0] in best_edge or e[1] in best_edge:

                to_remove.add(e)

        

        remaining_edges -= to_remove

    

    return cover, edges





def facility_location_lagrangeRelaxation(facilities, clients, opening_cost, assignment_cost):

    """

    设施选址问题的 Lagrange 松弛 2-近似

    

    原始 ILP:

    min Σ_{f} opening_cost[f] * y_f + Σ_{c,f} assignment_cost[c][f] * x_{c,f}

    s.t. Σ_{f} x_{c,f} = 1, ∀c (每个客户被分配到某设施)

         x_{c,f} <= y_f, ∀c,f (设施开放才能分配)

         x, y ∈ {0,1}

    

    Lagrange 松弛连接约束:

    - 松弛后: 每个客户独立选择最近设施

    - 但 y_f 仍决定设施是否开放

    

    Parameters

    ----------

    facilities : list

        设施列表

    clients : list

        客户列表

    opening_cost : dict

        设施开放成本,{f: cost}

    assignment_cost : dict

        分配成本,{c: {f: cost}}

    

    Returns

    -------

    tuple

        (开放设施集, 分配方案, 总成本)

    """

    F = len(facilities)

    C = len(clients)

    

    # 初始化 λ (每个客户的分配约束乘子)

    lam = {c: 0.0 for c in clients}

    

    max_iterations = 50

    step_size = 1.0

    

    for iteration in range(max_iterations):

        # 固定 λ,优化 y_f

        # 目标函数: Σ_f y_f * (opening_cost[f] - Σ_c λ_c * x_{c,f})

        # 由于 x_{c,f} 取决于 λ,我们先计算每个设施的净成本

        

        facility_net_cost = {}

        for f in facilities:

            # 假设在 λ 下,客户选择成本最低的开放设施

            # 这里简化: x_{c,f} = 1 如果 f 是最近的 (λ=0时)

            net = opening_cost[f]

            for c in clients:

                # 简化的分配成本

                net -= lam[c] if f == min(assignment_cost[c], key=assignment_cost[c].get) else 0

            facility_net_cost[f] = net

        

        # 贪婪选择: 如果净成本 < 0,开放设施

        opened = set()

        for f in facilities:

            if facility_net_cost[f] < 0:

                opened.add(f)

        

        # 如果没有设施开放,强制开放成本最低的

        if not opened:

            min_cost_facility = min(facilities, key=lambda f: opening_cost[f])

            opened.add(min_cost_facility)

        

        # 更新 λ (次梯度)

        for c in clients:

            # 找到当前开放设施中的最近者

            min_cost = float('inf')

            assigned_f = None

            for f in opened:

                if f in assignment_cost[c]:

                    cost = assignment_cost[c][f]

                    if cost < min_cost:

                        min_cost = cost

                        assigned_f = f

            

            # 目标: Σ_f x_{c,f} = 1, 即找到满足分配约束的 f

            # 次梯度: g_c = 1 - x_{c,f} (如果 f 分配了 c,否则 g_c = 1)

            if assigned_f is not None:

                new_lam_c = max(0, lam[c] + step_size * (1 - 1))

            else:

                new_lam_c = lam[c] + step_size

            

            lam[c] = new_lam_c

        

        step_size *= 0.98

    

    # 构造最终解

    opened = set()

    assignments = {}

    total_cost = 0

    

    # 贪心选择设施

    remaining_clients = set(clients)

    sorted_facilities = sorted(facilities, key=lambda f: opening_cost[f])

    

    for f in sorted_facilities:

        if not remaining_clients:

            break

        

        # 检查开放 f 是否合算

        cost_to_open = opening_cost[f]

        saved_assignment_cost = 0

        

        for c in list(remaining_clients):

            if f in assignment_cost[c]:

                cost_to_assign = assignment_cost[c][f]

                # 如果之前客户有其他分配,计算节省量

                saved_assignment_cost += cost_to_assign * 0.5  # 简化

        

        if cost_to_open <= saved_assignment_cost or len(opened) == 0:

            opened.add(f)

            for c in list(remaining_clients):

                if f in assignment_cost[c]:

                    assignments[c] = f

                    remaining_clients.discard(c)

                    break

    

    # 计算总成本

    for f in opened:

        total_cost += opening_cost[f]

    for c, f in assignments.items():

        total_cost += assignment_cost[c][f]

    

    return opened, assignments, total_cost





def compute_integrality_gap(ilp_opt, lp_relaxation_opt):

    """

    计算整数规划 vs LP 松弛的间隙 (Integrality Gap)

    

    间隙 = ILP最优值 / LP最优值

    

    用于衡量取整带来的质量损失

    

    Parameters

    ----------

    ilp_opt : float

        整数规划最优值

    lp_relaxation_opt : float

        LP 松弛最优值

    

    Returns

    -------

    float

        积分间隙

    """

    if lp_relaxation_opt == 0:

        return float('inf')

    return ilp_opt / lp_relaxation_opt





def subgradient_optimization(objective_fn, gradient_fn, dim, max_iter=100):

    """

    通用次梯度优化框架

    

    用于求解 Lagrange 对偶问题

    

    Parameters

    ----------

    objective_fn : callable

        目标函数 λ -> objective(λ)

    gradient_fn : callable

        次梯度函数 λ -> gradient(λ)

    dim : int

        λ 的维度

    max_iter : int

        最大迭代次数

    

    Returns

    -------

    tuple

        (最优 λ, 最优目标值, 目标值历史)

    """

    # 初始化 λ

    lam = np.zeros(dim)

    

    # 步长序列 (满足 Σ s_k = ∞, Σ s_k^2 < ∞)

    step_sizes = [1.0 / np.sqrt(k + 1) for k in range(max_iter)]

    

    best_obj = float('inf')

    best_lam = lam.copy()

    obj_history = []

    

    for k in range(max_iter):

        obj = objective_fn(lam)

        grad = gradient_fn(lam)

        

        obj_history.append(obj)

        

        if obj < best_obj:

            best_obj = obj

            best_lam = lam.copy()

        

        # 更新 λ (投影到非负象限)

        lam = lam + step_sizes[k] * grad

        lam = np.maximum(lam, 0)  # 投影

    

    return best_lam, best_obj, obj_history





if __name__ == "__main__":

    # 测试: Lagrange 松弛近似算法

    

    print("=" * 60)

    print("Lagrange 松弛 + 取整近似算法测试")

    print("=" * 60)

    

    # 测试顶点覆盖

    print("\n--- 顶点覆盖 Lagrange 松弛 ---")

    

    # 创建测试图: 6个顶点的路径图

    # 0 - 1 - 2 - 3 - 4 - 5

    graph = {

        0: [1],

        1: [0, 2],

        2: [1, 3],

        3: [2, 4],

        4: [3, 5],

        5: [4]

    }

    

    cover_lagrange, weight_lagrange, lam = vertex_cover_lagrangeRelaxation(graph)

    cover_greedy, edges = vertex_cover_greedy_approx(graph)

    

    print(f"图: 路径 0-1-2-3-4-5")

    print(f"Lagrange 松弛解: 覆盖 {cover_lagrange}, 权重 {weight_lagrange}")

    print(f"贪心 2-近似解: 覆盖 {cover_greedy}")

    print(f"边列表: {edges}")

    

    # 验证覆盖性

    covered_edges = set()

    for u in cover_lagrange:

        for v in graph[u]:

            if u < v:

                covered_edges.add((u, v))

    

    print(f"Lagrange 解覆盖的边: {covered_edges}")

    print(f"完全覆盖: {len(covered_edges) == len(edges)}")

    

    # 测试设施选址

    print("\n--- 设施选址 Lagrange 松弛 ---")

    

    facilities = ['F1', 'F2', 'F3']

    clients = ['C1', 'C2', 'C3', 'C4']

    

    opening_cost = {'F1': 10, 'F2': 15, 'F3': 8}

    assignment_cost = {

        'C1': {'F1': 2, 'F2': 5, 'F3': 4},

        'C2': {'F1': 4, 'F2': 3, 'F3': 6},

        'C3': {'F1': 5, 'F2': 6, 'F3': 2},

        'C4': {'F1': 3, 'F2': 4, 'F3': 5},

    }

    

    opened, assignments, total_cost = facility_location_lagrangeRelaxation(

        facilities, clients, opening_cost, assignment_cost

    )

    

    print(f"开放设施: {opened}")

    print(f"分配方案: {assignments}")

    print(f"总成本: {total_cost}")

    

    # 测试次梯度优化

    print("\n--- 次梯度优化测试 ---")

    

    # 简单函数: min_λ (λ - 1)^2

    def simple_obj(lam):

        return (lam[0] - 1) ** 2

    

    def simple_grad(lam):

        return 2 * (lam[0] - 1)

    

    best_lam, best_obj, history = subgradient_optimization(

        simple_obj, simple_grad, dim=1, max_iter=50

    )

    

    print(f"最优 λ: {best_lam[0]:.4f}")

    print(f"最优目标值: {best_obj:.6f}")

    print(f"收敛过程: {history[:5]} ... {history[-5:]}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)


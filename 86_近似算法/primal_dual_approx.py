# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / primal_dual_approx



本文件实现 primal_dual_approx 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict, deque





def vertex_cover_primal_dual(graph, weights=None):

    """

    顶点覆盖的原始对偶 2-近似算法

    

    原始 LP:

    min Σ_{v} w_v * x_v

    s.t. x_u + x_v >= 1, ∀(u,v) ∈ E

         x_v >= 0

    

    对偶 LP:

    max Σ_{e} y_e

    s.t. Σ_{e∋v} y_e <= w_v, ∀v ∈ V

         y_e >= 0

    

    原始对偶算法:

    1. 初始化 y_e = 0, 选择 x_v = 0

    2. 找到违反约束的边 (x_u = x_v = 0)

    3. 同时增加 y_e 和减少 w_v - Σ y_e

    4. 当 w_v - Σ y_e = 0 时,设置 x_v = 1

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重

    

    Returns

    -------

    tuple

        (原始解 x, 对偶解 y, 原始目标值, 对偶目标值)

    """

    vertices = list(graph.keys())

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    # 构建边列表

    edges = []

    for u in graph:

        for v in graph[u]:

            if u < v:

                edges.append((u, v))

    

    # 初始化

    y = {e: 0.0 for e in edges}  # 对偶变量

    x = {v: 0 for v in vertices}  # 原始变量 (0-1)

    

    # 剩余权重

    residual_weight = dict(weights)

    

    while True:

        # 找到未覆盖的边 (x_u = x_v = 0)

        uncovered_edges = []

        for e in edges:

            u, v = e

            if x[u] == 0 and x[v] == 0:

                uncovered_edges.append(e)

        

        if not uncovered_edges:

            break  # 所有边都被覆盖

        

        # 增加所有未覆盖边的 y_e

        delta = min(residual_weight.values())

        

        for e in uncovered_edges:

            y[e] += delta

        

        # 更新残余权重并检查是否需要设置 x_v = 1

        for v in vertices:

            # 计算 Σ_{e∋v} y_e

            sum_y = sum(y[e] for e in edges if v in e)

            

            if abs(residual_weight[v] - sum_y) < 1e-9:

                x[v] = 1

            else:

                residual_weight[v] = weights[v] - sum_y

    

    # 计算目标值

    primal_value = sum(weights[v] * x[v] for v in vertices)

    dual_value = sum(y.values())

    

    cover = {v for v in vertices if x[v] == 1}

    

    return cover, x, y, primal_value, dual_value





def set_cover_primal_dual(universe, subsets, costs):

    """

    集合覆盖的原始对偶 ln n-近似算法

    

    对偶:

    max Σ_{e} y_e

    s.t. Σ_{S∋e} y_S <= cost_S, ∀e ∈ U

         y_e >= 0

    

    Parameters

    ----------

    universe : set

        元素全集

    subsets : dict

        子集字典,{name: set_of_elements}

    costs : dict

        子集成本

    

    Returns

    -------

    tuple

        (选择的子集, 总成本, 对偶解)

    """

    # 初始化

    y = {e: 0.0 for e in universe}  # 元素的对偶变量

    selected = set()  # 选择的子集

    

    uncovered = set(universe)

    

    while uncovered:

        # 增加所有未覆盖元素的 y_e

        # 找到包含未覆盖元素的所有子集

        candidates = {}

        for e in uncovered:

            for s_name, s_elements in subsets.items():

                if e in s_elements:

                    if s_name not in candidates:

                        candidates[s_name] = set()

                    candidates[s_name].add(e)

        

        if not candidates:

            break  # 无法覆盖所有元素

        

        # 选择成本/覆盖元素比最低的子集

        best_s = None

        best_ratio = float('inf')

        

        for s_name, covered_elements in candidates.items():

            ratio = costs[s_name] / len(covered_elements)

            if ratio < best_ratio:

                best_ratio = ratio

                best_s = s_name

        

        # 增加 y_e (受限于子集成本)

        delta = best_ratio

        

        for e in candidates[best_s]:

            y[e] += delta

        

        # 检查是否需要选择子集

        total_y_for_s = sum(y[e] for e in subsets[best_s])

        

        if total_y_for_s >= costs[best_s]:

            selected.add(best_s)

            uncovered -= subsets[best_s]

    

    total_cost = sum(costs[s] for s in selected)

    

    return selected, total_cost, y





def maximum_cut_primal_dual(graph):

    """

    最大割的原始对偶 1/2-近似算法

    

    原始:

    max Σ_{(u,v)} w_{uv} * (x_u + x_v - 2 * x_u * x_v)

    

    简化版本: 基于局部贪心

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    tuple

        (集合 A, 集合 B, 割权重)

    """

    vertices = list(graph.keys())

    

    # 边权重

    edge_weights = {}

    for u in graph:

        for v in graph[u]:

            if u < v:

                edge_weights[(u, v)] = 1.0

    

    # 初始化: 所有顶点在 A

    A = set(vertices)

    B = set()

    

    # 维护每个顶点的割贡献

    cut_contribution = {v: 0.0 for v in vertices}

    

    # 贪心移动顶点到 B 以增加割

    improved = True

    while improved:

        improved = False

        

        for v in list(A):

            # 计算如果将 v 移到 B,割的变化

            delta_gain = 0

            for nb in graph.get(v, []):

                w_uv = edge_weights.get((min(v, nb), max(v, nb)), 1.0)

                # 当前: v 在 A,nb 可能在 A 或 B

                # 移动后: v 在 B,割增加 w_uv 如果 nb 在 A

                if nb in A:

                    delta_gain += w_uv

                elif nb in B:

                    delta_gain -= w_uv

            

            # 如果移动能增加割,则移动

            if delta_gain > 0:

                A.remove(v)

                B.add(v)

                cut_contribution[v] = delta_gain

                improved = True

    

    # 计算割的总权重

    cut_weight = 0

    for u in graph:

        for v in graph[u]:

            if u < v:

                w_uv = edge_weights.get((u, v), 1.0)

                if (u in A and v in B) or (u in B and v in A):

                    cut_weight += w_uv

    

    return A, B, cut_weight





def facility_location_primal_dual(facilities, clients, opening_cost, assignment_cost):

    """

    设施选址的原始对偶近似算法

    

    使用 Lagrangian 松弛 + 原始对偶

    

    Parameters

    ----------

    facilities : list

        设施列表

    clients : list

        客户列表

    opening_cost : dict

        设施开放成本

    assignment_cost : dict

        分配成本 {client: {facility: cost}}

    

    Returns

    -------

    tuple

        (开放设施, 分配方案, 总成本)

    """

    # 初始化对偶变量

    # α_c: 客户 c 的连接约束对偶

    # β_f: 设施开放约束对偶

    

    alpha = {c: 0.0 for c in clients}

    selected = set()

    assignments = {}

    

    # 按连接成本排序的事件

    events = []

    for c in clients:

        for f in facilities:

            if f in assignment_cost[c]:

                events.append((assignment_cost[c][f], c, f))

    

    events.sort()  # 按成本升序

    

    connected = set()

    

    for cost, c, f in events:

        # 增加 α_c

        alpha[c] = cost

        

        # 检查是否需要开放设施

        if f not in selected:

            # 检查所有已连接客户的连接成本是否超过设施开放成本

            total_assignment = sum(alpha[c2] for c2 in connected if f in assignment_cost.get(c2, {}))

            

            # 简化: 当有足够多客户连接时开放设施

            connected.add(c)

            

            if len(connected) >= 2:

                selected.add(f)

    

    # 基于阈值构造最终解

    final_selected = set()

    

    for c in clients:

        best_f = None

        best_cost = float('inf')

        

        for f in facilities:

            if f in assignment_cost[c]:

                total_cost = opening_cost[f] + assignment_cost[c][f]

                if total_cost < best_cost:

                    best_cost = total_cost

                    best_f = f

        

        if best_f:

            final_selected.add(best_f)

            assignments[c] = best_f

    

    # 计算总成本

    total_cost = sum(opening_cost[f] for f in final_selected)

    for c, f in assignments.items():

        total_cost += assignment_cost[c][f]

    

    return final_selected, assignments, total_cost





def minimum_vertex_cover_primal_dual_ip(graph, weights=None):

    """

    顶点覆盖的整数规划原始对偶

    

    IP:

    min Σ w_v * x_v

    s.t. x_u + x_v >= 1, ∀(u,v) ∈ E

         x_v ∈ {0, 1}

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重

    

    Returns

    -------

    tuple

        (覆盖集, 原始值, 对偶值)

    """

    vertices = list(graph.keys())

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    edges = [(u, v) for u in graph for v in graph[u] if u < v]

    

    # 简化的原始对偶实现

    x = {v: 0 for v in vertices}

    y = {e: 0.0 for e in edges}

    

    # 剩余权重

    slack = dict(weights)

    

    iteration = 0

    max_iterations = len(vertices) * 2

    

    while iteration < max_iterations:

        iteration += 1

        

        # 找到 slack > 0 且 y_e < slack 的边

        tight_edges = []

        loose_edges = []

        

        for e in edges:

            u, v = e

            # 检查 x_u + x_v < 1

            if x[u] + x[v] < 1:

                if y[e] < slack[u] and y[e] < slack[v]:

                    loose_edges.append(e)

                elif abs(y[e] - min(slack[u], slack[v])) < 1e-9:

                    tight_edges.append(e)

        

        if not loose_edges:

            break

        

        # 增加 loose 边的 y_e

        delta = min(slack.values())

        

        for e in loose_edges:

            y[e] += delta

        

        # 更新 slack

        for v in vertices:

            sum_y = sum(y[e] for e in edges if v in e)

            slack[v] = weights[v] - sum_y

        

        # 设置 x_v = 1 当 slack[v] = 0

        for v in vertices:

            if slack[v] < 1e-9 and x[v] == 0:

                x[v] = 1

    

    cover = {v for v in vertices if x[v] == 1}

    primal = sum(weights[v] * x[v] for v in vertices)

    dual = sum(y.values())

    

    return cover, primal, dual





def compute_weak_duality_gap(primal, dual):

    """

    计算弱对偶间隙

    

    弱对偶定理: 对偶目标值 <= 原始目标值

    

    Parameters

    ----------

    primal : float

        原始目标值

    dual : float

        对偶目标值

    

    Returns

    -------

    float

        相对间隙

    """

    if primal == 0:

        return 0 if dual == 0 else float('inf')

    return (primal - dual) / primal





if __name__ == "__main__":

    # 测试: 原始对偶近似算法

    

    print("=" * 60)

    print("原始对偶近似算法测试")

    print("=" * 60)

    

    random.seed(42)

    

    # 测试顶点覆盖

    print("\n--- 顶点覆盖原始对偶 ---")

    

    # 测试图

    vc_graph = {

        0: [1, 2],

        1: [0, 2, 3],

        2: [0, 1, 3],

        3: [1, 2, 4],

        4: [3]

    }

    

    cover, x, y, primal, dual = vertex_cover_primal_dual(vc_graph)

    gap = compute_weak_duality_gap(primal, dual)

    

    print(f"图: 5个顶点, 6条边")

    print(f"原始解 (x): {x}")

    print(f"对偶解 (y): {y}")

    print(f"原始目标值: {primal}")

    print(f"对偶目标值: {dual}")

    print(f"弱对偶间隙: {gap:.4f}")

    print(f"近似比验证: primal/dual <= 2? {primal / dual if dual > 0 else 'N/A'}")

    

    # 测试集合覆盖

    print("\n--- 集合覆盖原始对偶 ---")

    

    universe = {1, 2, 3, 4, 5, 6, 7, 8}

    subsets = {

        'S1': {1, 2, 3},

        'S2': {2, 4, 5},

        'S3': {5, 6, 7},

        'S4': {1, 7, 8},

        'S5': {3, 4, 8},

        'S6': {6, 7, 8},

    }

    costs = {'S1': 5, 'S2': 3, 'S3': 4, 'S4': 6, 'S5': 2, 'S6': 5}

    

    selected, total_cost, dual_y = set_cover_primal_dual(universe, subsets, costs)

    

    print(f"全集: {universe}")

    print(f"选择的子集: {selected}")

    print(f"总成本: {total_cost}")

    print(f"对偶目标值 (覆盖下界): {sum(dual_y.values()):.2f}")

    

    # 测试最大割

    print("\n--- 最大割原始对偶 ---")

    

    cut_graph = {

        0: [1, 2, 3],

        1: [0, 2, 3],

        2: [0, 1, 3],

        3: [0, 1, 2]

    }

    

    A, B, cut_weight = maximum_cut_primal_dual(cut_graph)

    

    print(f"完全图 K4")

    print(f"集合 A: {A}")

    print(f"集合 B: {B}")

    print(f"割权重: {cut_weight}")

    print(f"最优割 (二分图): 4")

    print(f"近似比: {4 / cut_weight if cut_weight > 0 else 'N/A'}")

    

    # 测试设施选址

    print("\n--- 设施选址原始对偶 ---")

    

    facilities = ['F1', 'F2', 'F3']

    clients = ['C1', 'C2', 'C3', 'C4']

    

    opening_cost = {'F1': 10, 'F2': 15, 'F3': 8}

    assignment_cost = {

        'C1': {'F1': 2, 'F2': 5, 'F3': 4},

        'C2': {'F1': 4, 'F2': 3, 'F3': 6},

        'C3': {'F1': 5, 'F2': 6, 'F3': 2},

        'C4': {'F1': 3, 'F2': 4, 'F3': 5},

    }

    

    opened, assignments, total_cost_fl = facility_location_primal_dual(

        facilities, clients, opening_cost, assignment_cost

    )

    

    print(f"开放设施: {opened}")

    print(f"分配方案: {assignments}")

    print(f"总成本: {total_cost_fl}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)


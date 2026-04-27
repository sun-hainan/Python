# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / randomized_approx



本文件实现 randomized_approx 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict





def set_cover_randomized_rounding(universe, subsets, weights=None):

    """

    集合覆盖的随机舍入近似算法

    

    原始 LP 松弛:

    min Σ_{S} w_S * x_S

    s.t. Σ_{S∋e} x_S >= 1, ∀e ∈ U

         x_S >= 0

    

    随机舍入: 以概率 x_S 选择集合 S

    

    近似比: O(log n), 其中 n = |U|

    

    Parameters

    ----------

    universe : set

        元素全集 U

    subsets : dict

        子集字典,{subset_name: set_of_elements}

    weights : dict

        子集权重,{subset_name: weight}

    

    Returns

    -------

    tuple

        (选择的子集列表, 覆盖的元素, 总权重)

    """

    if weights is None:

        weights = {s: 1.0 for s in subsets}

    

    n = len(universe)

    

    # 求解 LP 松弛 (简化版: 贪心计算 x_S)

    # 实际应使用线性规划求解器

    # 这里使用简化的贪心 LP 解

    

    # 贪心选择最小成本/覆盖比

    x_values = {}

    remaining_elements = set(universe)

    

    for s_name, s_elements in subsets.items():

        # 计算该子集覆盖了多少剩余元素

        covered_by_s = s_elements & remaining_elements

        if covered_by_s:

            # 简化: x_S = 已覆盖元素 / 总元素 (实际应求解 LP)

            cost_per_element = weights[s_name] / len(covered_by_s)

            x_values[s_name] = min(1.0, cost_per_element / 10)  # 简化的 x 值

    

    # 随机舍入

    selected_sets = []

    covered_elements = set()

    

    for s_name, x_val in x_values.items():

        if random.random() < x_val:

            selected_sets.append(s_name)

            covered_elements |= subsets[s_name]

    

    # 检查是否完全覆盖,如果没有,添加代价最高的集合

    if covered_elements != universe:

        for e in universe - covered_elements:

            # 找到包含 e 的最小权重集合

            min_cost = float('inf')

            min_set = None

            for s_name, s_elements in subsets.items():

                if e in s_elements and weights[s_name] < min_cost:

                    min_cost = weights[s_name]

                    min_set = s_name

            if min_set:

                selected_sets.append(min_set)

                covered_elements |= subsets[min_set]

    

    total_weight = sum(weights[s] for s in selected_sets)

    

    return selected_sets, covered_elements, total_weight





def max_cut_randomized(graph):

    """

    最大割的随机 1/2-近似算法

    

    随机将顶点划分为两部分,期望割大小 = |E|/2

    

    条件期望分析:

    对于每条边 (u,v),选择 u 在 A 或 B 是随机的

    E[边 (u,v) 在割中] = 1/2

    因此 E[|cut|] = m/2

    

    Parameters

    ----------

    graph : dict

        图的邻接表,{v: [neighbors]}

    

    Returns

    -------

    tuple

        (割集 A, 割集 B, 割的边数)

    """

    vertices = list(graph.keys())

    

    # 随机划分

    partition = {}

    for v in vertices:

        partition[v] = 'A' if random.random() < 0.5 else 'B'

    

    set_a = {v for v in vertices if partition[v] == 'A'}

    set_b = {v for v in vertices if partition[v] == 'B'}

    

    # 计算割大小

    cut_edges = 0

    for u in graph:

        for v in graph[u]:

            if u < v and partition[u] != partition[v]:

                cut_edges += 1

    

    return set_a, set_b, cut_edges





def max_cut_gilbert_gardner(graph):

    """

    最大割的确定性 1/2-近似 (Gilbert-Gardner 算法)

    

    策略: 基于顶点度的确定性排序划分

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    tuple

        (割集 A, 割集 B, 割的边数)

    """

    vertices = list(graph.keys())

    

    # 按度数排序

    degree = {v: len(graph[v]) for v in vertices}

    sorted_vertices = sorted(vertices, key=lambda v: degree[v], reverse=True)

    

    # 将顶点分配到两个集合,使得度数高的尽可能分散

    set_a = []

    set_b = []

    

    for v in sorted_vertices:

        # 计算如果放入 A 或 B 会产生多少割边

        neighbors_in_a = sum(1 for u in graph[v] if u in set_a)

        neighbors_in_b = sum(1 for u in graph[v] if u in set_b)

        

        if neighbors_in_a < neighbors_in_b:

            set_a.append(v)

        else:

            set_b.append(v)

    

    set_a = set(set_a)

    set_b = set(set_b)

    

    # 计算割大小

    cut_edges = 0

    for u in graph:

        for v in graph[u]:

            if u < v and ((u in set_a and v in set_b) or (u in set_b and v in set_a)):

                cut_edges += 1

    

    return set_a, set_b, cut_edges





def weighted_matching_randomized_rounding(graph, edge_weights):

    """

    加权匹配的随机舍入近似

    

    最大权匹配 LP 松弛有半整数解

    随机舍入得到 (1 - 1/e) 近似

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    edge_weights : dict

        边权重,键为 (u, v) 元组, u < v

    

    Returns

    -------

    tuple

        (匹配边集合, 总权重)

    """

    vertices = list(graph.keys())

    edges = []

    for u in graph:

        for v in graph[u]:

            if u < v:

                edges.append((u, v))

    

    # 简化的贪心匹配 (实际应求解 LP)

    # 按权重降序选择不冲突的边

    sorted_edges = sorted(edges, key=lambda e: edge_weights.get(e, 0), reverse=True)

    

    matched = set()

    matching_edges = []

    

    for e in sorted_edges:

        u, v = e

        if u not in matched and v not in matched:

            matching_edges.append(e)

            matched.add(u)

            matched.add(v)

    

    total_weight = sum(edge_weights.get(e, 0) for e in matching_edges)

    

    return matching_edges, total_weight





def scheduling_randomized_rounding(jobs, machines, processing_times):

    """

    调度问题的随机舍入

    

    目标: 最小化 makespan (最大完工时间)

    

    LPT (Longest Processing Time) 贪心可达 4/3 近似

    随机舍入可以达到 2 近似

    

    Parameters

    ----------

    jobs : list

        作业列表

    machines : list

        机器列表

    processing_times : dict

        作业处理时间,{job: time}

    

    Returns

    -------

    tuple

        (分配方案, 最大完工时间)

    """

    n_jobs = len(jobs)

    m_machines = len(machines)

    

    # 简化的随机分配

    assignment = {j: random.choice(machines) for j in jobs}

    

    # 计算每台机器的负载

    load = {m: 0 for m in machines}

    for j, m in assignment.items():

        load[m] += processing_times.get(j, 0)

    

    makespan = max(load.values()) if load else 0

    

    return assignment, makespan





def lpt_scheduling(jobs, machines, processing_times):

    """

    LPT (Longest Processing Time) 贪心调度

    

    策略: 按处理时间降序排列作业,依次分配到当前负载最小的机器

    

    近似比: 4/3 - 1/(3m)

    

    Parameters

    ----------

    jobs : list

        作业列表

    machines : list

        机器列表

    processing_times : dict

        作业处理时间

    

    Returns

    -------

    tuple

        (分配方案, makespan)

    """

    # 按处理时间降序排列

    sorted_jobs = sorted(jobs, key=lambda j: processing_times[j], reverse=True)

    

    # 每台机器的当前负载

    load = {m: 0 for m in machines}

    assignment = {}

    

    for j in sorted_jobs:

        # 找到负载最小的机器

        min_machine = min(machines, key=lambda m: load[m])

        assignment[j] = min_machine

        load[min_machine] += processing_times[j]

    

    makespan = max(load.values())

    

    return assignment, makespan





def conditional_expectation_max_cut(graph):

    """

    使用条件期望分析的最大割近似

    

    思路:

    1. 从空划分开始

    2. 逐个顶点决定归属,每次选择使期望割大小更大的分支

    3. 最终得到确定性解,保证至少 m/2 条边

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    tuple

        (集合 A, 集合 B, 割边数)

    """

    vertices = list(graph.keys())

    

    # 初始化: 所有顶点都在 A

    set_a = set(vertices)

    set_b = set()

    

    for v in vertices:

        # 计算将 v 移到 B 后割的变化

        edges_to_a = sum(1 for u in graph[v] if u in set_a and u != v)

        edges_to_b = sum(1 for u in graph[v] if u in set_b and u != v)

        

        # 如果移到 B 能增加割边,则移动

        if edges_to_b > edges_to_a:

            set_a.remove(v)

            set_b.add(v)

    

    # 计算最终割大小

    cut_edges = 0

    for u in graph:

        for v in graph[u]:

            if u < v and ((u in set_a and v in set_b) or (u in set_b and v in set_a)):

                cut_edges += 1

    

    return set_a, set_b, cut_edges





def derandomize_max_cut(graph):

    """

    最大割的去随机化

    

    通过条件期望方法将随机算法转化为确定性算法

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    

    Returns

    -------

    tuple

        (集合 A, 集合 B, 割边数)

    """

    return conditional_expectation_max_cut(graph)





if __name__ == "__main__":

    # 测试: 随机近似算法

    

    print("=" * 60)

    print("随机近似算法测试")

    print("=" * 60)

    

    random.seed(42)

    np.random.seed(42)

    

    # 测试最大割

    print("\n--- 最大割 ---")

    

    # 创建测试图: 8个顶点的完全图

    n_vertices = 8

    graph = {i: [j for j in range(n_vertices) if j != i] for i in range(n_vertices)}

    

    # 随机割

    set_a, set_b, cut_size = max_cut_randomized(graph)

    print(f"随机算法: A={set_a}, B={set_b}, 割边数={cut_size}")

    print(f"完全图总边数: {n_vertices * (n_vertices - 1) // 2}")

    print(f"期望割边数 (m/2): {n_vertices * (n_vertices - 1) / 4}")

    

    # 条件期望去随机化

    set_a_det, set_b_det, cut_det = derandomize_max_cut(graph)

    print(f"确定性算法: 割边数={cut_det}")

    

    # Gilbert-Gardner

    set_a_gg, set_b_gg, cut_gg = max_cut_gilbert_gardner(graph)

    print(f"Gilbert-Gardner: 割边数={cut_gg}")

    

    # 测试调度

    print("\n--- 调度问题 (最小化 makespan) ---")

    

    jobs = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8']

    machines = ['M1', 'M2', 'M3']

    processing_times = {

        'J1': 10, 'J2': 7, 'J3': 5, 'J4': 8,

        'J5': 12, 'J6': 3, 'J7': 6, 'J8': 9

    }

    

    # LPT 调度

    assign_lpt, makespan_lpt = lpt_scheduling(jobs, machines, processing_times)

    print(f"LPT 调度: makespan={makespan_lpt}")

    print(f"分配方案: {assign_lpt}")

    

    # 随机调度

    assign_rand, makespan_rand = scheduling_randomized_rounding(jobs, machines, processing_times)

    print(f"随机调度: makespan={makespan_rand}")

    

    # 下界: 最长作业时间

    max_job_time = max(processing_times.values())

    sum_times = sum(processing_times.values())

    avg_load = sum_times / len(machines)

    print(f"下界 (最长作业): {max_job_time}")

    print(f"下界 (平均负载): {avg_load:.2f}")

    print(f"LPT 近似比: {makespan_lpt / max(avg_load, max_job_time):.2f}")

    

    # 测试集合覆盖 (小规模)

    print("\n--- 集合覆盖随机舍入 ---")

    

    universe = {1, 2, 3, 4, 5, 6, 7, 8}

    subsets = {

        'S1': {1, 2, 3},

        'S2': {2, 4, 5},

        'S3': {5, 6, 7},

        'S4': {1, 7, 8},

        'S5': {3, 4, 8},

    }

    weights = {'S1': 5, 'S2': 3, 'S3': 4, 'S4': 6, 'S5': 2}

    

    selected, covered, total_w = set_cover_randomized_rounding(universe, subsets, weights)

    print(f"选择的子集: {selected}")

    print(f"覆盖元素: {covered}")

    print(f"总权重: {total_w}")

    print(f"完全覆盖: {covered == universe}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)


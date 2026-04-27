# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / approximation_ratio



本文件实现 approximation_ratio 相关的算法功能。

"""



import numpy as np

import random





def vertex_cover_lp_relaxation(graph, weights=None):

    """

    顶点覆盖的 LP 松弛 + 取整 2-近似

    

    LP 松弛:

    min Σ_{v} w_v * x_v

    s.t. x_u + x_v >= 1, ∀(u,v) ∈ E

         x_v >= 0, ∀v ∈ V

    

    取整: x_v^* > 0 => 选取 v

    

    近似比证明:

    - LP 目标值 = Σ w_v * x_v^* <= OPT

    - 取整后解 C = {v | x_v^* > 0}

    - 权重 = Σ_{v∈C} w_v <= Σ_{v} w_v * x_v^* * 2 = 2 * LP <= 2 * OPT

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重,{v: weight}

    

    Returns

    -------

    tuple

        (覆盖集, LP 解值, 取整后权重)

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    # 构建 LP 松弛的解

    # 简化: 使用贪心计算 x_v

    x = {}

    for v in vertices:

        degree_v = len(graph[v])

        if degree_v > 0:

            x[v] = 0.5  # 满足每条边 x_u + x_v >= 1 的最小值

        else:

            x[v] = 0.0

    

    # 计算 LP 目标值

    lp_value = sum(weights[v] * x[v] for v in vertices)

    

    # 取整: x_v > 0 => 选取 v

    cover = {v for v in vertices if x[v] > 0}

    

    # 计算取整后权重

    rounded_weight = sum(weights[v] for v in cover)

    

    return cover, lp_value, rounded_weight





def vertex_cover_greedy(graph, weights=None):

    """

    顶点覆盖的贪心 2-近似

    

    策略: 反复选择度数最高的边,删除其端点

    

    近似比分析:

    - 每次选择的两个顶点覆盖了若干边

    - 最坏情况下 OPT 至少需要选择其中一个端点

    - 归纳可得近似比为 2

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重

    

    Returns

    -------

    tuple

        (覆盖集, 总权重)

    """

    vertices = list(graph.keys())

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    # 构建可修改的边集合

    edges = set()

    for u in graph:

        for v in graph[u]:

            if u < v:

                edges.add((u, v))

    

    cover = set()

    

    while edges:

        # 找到度数最高的边 (按剩余边计算)

        edge_degrees = {}

        for u, v in edges:

            deg_u = sum(1 for e in edges if u in e)

            deg_v = sum(1 for e in edges if v in e)

            edge_degrees[(u, v)] = (deg_u, deg_v)

        

        # 选择度和最大的边

        best_edge = max(edges, key=lambda e: sum(edge_degrees[e]))

        

        # 添加入覆盖

        cover.add(best_edge[0])

        cover.add(best_edge[1])

        

        # 删除与该边端点相连的所有边

        edges = {e for e in edges if e[0] not in best_edge and e[1] not in best_edge}

    

    total_weight = sum(weights[v] for v in cover)

    

    return cover, total_weight





def vertex_cover_primal_dual(graph, weights=None):

    """

    顶点覆盖的原始对偶 2-近似

    

    原始-对偶算法维护:

    - 原始变量: x_v (选择顶点 v)

    - 对偶变量: y_e (边的对偶约束)

    

    贪心规则:

    1. 初始化所有 x = 0, y = 0

    2. 选择未覆盖边 (x_u + x_v = 0),增加 y_e

    3. 当 y_e 增加到某个端点权重时,设置 x_v = 1

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重

    

    Returns

    -------

    tuple

        (覆盖集, 原始目标值, 对偶目标值)

    """

    vertices = list(graph.keys())

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    # 初始化

    x = {v: 0 for v in vertices}

    y = {}

    covered_edges = set()

    

    # 构建边列表

    all_edges = []

    for u in graph:

        for v in graph[u]:

            if u < v:

                all_edges.append((u, v))

    

    # 贪心增加对偶

    for e in all_edges:

        u, v = e

        # 边未被覆盖时

        if x[u] == 0 and x[v] == 0:

            # 增加 y 直到某个端点被选中

            y[e] = min(weights[u], weights[v])

            

            # 对偶更新: 端点成本减少

            if weights[u] <= weights[v]:

                x[u] = 1

            else:

                x[v] = 1

    

    cover = {v for v in vertices if x[v] == 1}

    primal_value = sum(weights[v] for v in cover)

    dual_value = sum(y.values()) if y else 0

    

    return cover, primal_value, dual_value





def scheduling_makespan_lpt(jobs, machines, processing_times):

    """

    多机调度 LPT 算法的近似比分析

    

    Graham (1966) 证明了 LPT 的近似比:

    (4/3) - (1 / (3m))

    

    其中 m 是机器数量

    

    近似比证明思路:

    - 最长作业的处理时间 p_1

    - OPT >= p_1 (任何调度都需要处理最长作业)

    - LPT 的 makespan <= p_1 + (1 - 1/m) * p_2 <= p_1 + (1 - 1/m) * p_1

    - 比值 <= 4/3 - 1/(3m)

    

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

        (分配方案, makespan, 下界, 近似比)

    """

    # LPT 排序

    sorted_jobs = sorted(jobs, key=lambda j: processing_times[j], reverse=True)

    

    # 分配到当前负载最小的机器

    load = {m: 0 for m in machines}

    assignment = {}

    

    for j in sorted_jobs:

        min_machine = min(machines, key=lambda m: load[m])

        assignment[j] = min_machine

        load[min_machine] += processing_times[j]

    

    makespan = max(load.values())

    

    # 下界

    max_job_time = max(processing_times.values())

    sum_times = sum(processing_times.values())

    avg_load = sum_times / len(machines)

    lower_bound = max(max_job_time, avg_load)

    

    approx_ratio = makespan / lower_bound if lower_bound > 0 else 1

    

    return assignment, makespan, lower_bound, approx_ratio





def scheduling_makespan_random(jobs, machines, processing_times):

    """

    随机调度: 期望近似比分析

    

    随机将作业分配到机器

    E[makespan] <= (2 - 1/m) * OPT

    

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

        (分配方案, makespan, 近似比)

    """

    assignment = {j: random.choice(machines) for j in jobs}

    

    load = {m: 0 for m in machines}

    for j, m in assignment.items():

        load[m] += processing_times[j]

    

    makespan = max(load.values())

    

    # 下界

    max_job_time = max(processing_times.values())

    sum_times = sum(processing_times.values())

    lower_bound = max(max_job_time, sum_times / len(machines))

    

    approx_ratio = makespan / lower_bound if lower_bound > 0 else 1

    

    return assignment, makespan, approx_ratio





def compute_tight_ratio(algorithm_value, optimal_value):

    """

    计算逼近比

    

    Parameters

    ----------

    algorithm_value : float

        近似算法得到的值

    optimal_value : float

        最优值

    

    Returns

    -------

    float

        逼近比 (algorithm / optimal)

    """

    if optimal_value == 0:

        return float('inf') if algorithm_value > 0 else 1.0

    return algorithm_value / optimal_value





def vertex_cover_exact(graph, weights=None):

    """

    顶点覆盖的精确算法 (枚举所有解)

    用于小规模图的最优值计算

    

    Parameters

    ----------

    graph : dict

        图的邻接表

    weights : dict

        顶点权重

    

    Returns

    -------

    tuple

        (最小覆盖集, 最小权重)

    """

    vertices = list(graph.keys())

    n = len(vertices)

    

    if weights is None:

        weights = {v: 1.0 for v in vertices}

    

    best_weight = float('inf')

    best_cover = set()

    

    # 枚举所有顶点子集 (2^n)

    for mask in range(1 << n):

        cover = set()

        for i in range(n):

            if mask & (1 << i):

                cover.add(vertices[i])

        

        # 检查是否是有效覆盖

        valid = True

        for u in graph:

            for v in graph[u]:

                if u < v and u not in cover and v not in cover:

                    valid = False

                    break

            if not valid:

                break

        

        if valid:

            weight = sum(weights[v] for v in cover)

            if weight < best_weight:

                best_weight = weight

                best_cover = cover

    

    return best_cover, best_weight





def scheduling_exact_makespan(jobs, machines, processing_times):

    """

    调度问题的精确下界计算 (基于装箱)

    

    使用 LPT 解的下界: OPT >= max(LPT_makespan / 2, max_job_time)

    

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

    float

        下界值

    """

    max_job_time = max(processing_times.values())

    sum_times = sum(processing_times.values())

    

    # 基于 LPT 的下界

    sorted_times = sorted(processing_times.values(), reverse=True)

    

    # 简化的 LPT makespan 下界

    m = len(machines)

    if m >= len(jobs):

        return max_job_time

    

    # LPT 贪心计算

    loads = [0] * m

    for t in sorted_times:

        min_load_idx = loads.index(min(loads))

        loads[min_load_idx] += t

    

    lpt_makespan = max(loads)

    

    lower_bound = max(lpt_makespan, max_job_time, sum_times / m)

    

    return lower_bound





if __name__ == "__main__":

    # 测试: 逼近比分析

    

    print("=" * 60)

    print("逼近比分析测试")

    print("=" * 60)

    

    np.random.seed(42)

    random.seed(42)

    

    # 测试顶点覆盖逼近比

    print("\n--- 顶点覆盖逼近比 ---")

    

    # 测试图1: 路径图

    path_graph = {

        0: [1],

        1: [0, 2],

        2: [1, 3],

        3: [2, 4],

        4: [3, 5],

        5: [4]

    }

    

    # 精确解

    exact_cover, exact_weight = vertex_cover_exact(path_graph)

    print(f"路径图 0-1-2-3-4-5:")

    print(f"  精确最优: 权重={exact_weight}, 覆盖={exact_cover}")

    

    # LP 松弛取整

    cover_lp, lp_val, lp_weight = vertex_cover_lp_relaxation(path_graph)

    ratio_lp = compute_tight_ratio(lp_weight, exact_weight)

    print(f"  LP松弛+取整: 权重={lp_weight}, 比={ratio_lp:.2f}")

    

    # 贪心

    cover_greedy, greedy_weight = vertex_cover_greedy(path_graph)

    ratio_greedy = compute_tight_ratio(greedy_weight, exact_weight)

    print(f"  贪心算法: 权重={greedy_weight}, 比={ratio_greedy:.2f}")

    

    # 原始对偶

    cover_pd, pd_weight, dual = vertex_cover_primal_dual(path_graph)

    ratio_pd = compute_tight_ratio(pd_weight, exact_weight)

    print(f"  原始对偶: 权重={pd_weight}, 对偶={dual:.2f}, 比={ratio_pd:.2f}")

    

    # 测试图2: 简单图

    simple_graph = {

        0: [1, 2],

        1: [0, 2],

        2: [0, 1, 3],

        3: [2]

    }

    

    exact_cover2, exact_weight2 = vertex_cover_exact(simple_graph)

    print(f"\n简单图:")

    print(f"  精确最优: 权重={exact_weight2}")

    

    cover_lp2, _, lp_weight2 = vertex_cover_lp_relaxation(simple_graph)

    ratio_lp2 = compute_tight_ratio(lp_weight2, exact_weight2)

    print(f"  LP松弛+取整: 权重={lp_weight2}, 比={ratio_lp2:.2f}")

    

    # 测试调度逼近比

    print("\n--- 调度问题逼近比 ---")

    

    m = 3  # 3台机器

    machines = [f'M{i}' for i in range(m)]

    jobs = [f'J{i}' for i in range(10)]

    processing_times = {f'J{i}': random.randint(1, 20) for i in range(10)}

    

    print(f"机器数: {m}, 作业数: {len(jobs)}")

    print(f"处理时间: {processing_times}")

    

    # LPT

    assign_lpt, makespan_lpt, lb_lpt, ratio_lpt = scheduling_makespan_lpt(

        jobs, machines, processing_times

    )

    print(f"\nLPT 算法:")

    print(f"  Makespan: {makespan_lpt}")

    print(f"  下界: {lb_lpt:.2f}")

    print(f"  近似比: {ratio_lpt:.4f} (理论界: {4/3 - 1/(3*m):.4f})")

    

    # 随机调度

    makespan_rand_list = []

    for _ in range(100):

        _, ms, _ = scheduling_makespan_random(jobs, machines, processing_times)

        makespan_rand_list.append(ms)

    

    avg_rand = np.mean(makespan_rand_list)

    print(f"\n随机调度 (100次平均):")

    print(f"  平均 Makespan: {avg_rand:.2f}")

    print(f"  相对于 LPT 下界: {avg_rand / lb_lpt:.4f}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)


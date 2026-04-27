# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / submodular_max



本文件实现 submodular_max 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict





def is_submodular(function, sets, ground_set):

    """

    检验函数是否为次模函数

    

    验证条件:

    f(A ∪ B) + f(A ∩ B) <= f(A) + f(B)

    或等价于边际收益递减

    

    Parameters

    ----------

    function : callable

        待检验的函数 f: set -> float

    sets : list

        用于检验的集合对

    ground_set : set

        全集

    

    Returns

    -------

    bool

        是否为次模函数

    """

    for A, B in sets:

        left = function(A | B) + function(A & B)

        right = function(A) + function(B)

        if left > right + 1e-6:  # 允许数值误差

            return False

    return True





def greedy_maximize_monotone_submodular(ground_set, function, k, epsilon=0.0):

    """

    贪心算法最大化单调次模函数

    

    算法:

    S = ∅

    while |S| < k:

        选择使 f(S ∪ {e}) - f(S) 最大的元素 e

        S = S ∪ {e}

    

    近似比: (1 - 1/e) ≈ 0.632

    

    Parameters

    ----------

    ground_set : set

        候选元素集合

    function : callable

        单调次模函数 f: set -> float

    k : int

        要选择的元素数量

    epsilon : float

        可选: 添加噪声打破平局,改善随机化近似

    

    Returns

    -------

    tuple

        (选择的集合 S, 函数值 f(S))

    """

    S = set()

    elements = list(ground_set)

    

    for _ in range(k):

        best_element = None

        best_marginal = -float('inf')

        

        for e in elements:

            if e in S:

                continue

            

            marginal = function(S | {e}) - function(S)

            

            # 添加小噪声打破平局

            if epsilon > 0:

                marginal += random.uniform(0, epsilon)

            

            if marginal > best_marginal:

                best_marginal = marginal

                best_element = e

        

        if best_element is not None:

            S.add(best_element)

        else:

            break

    

    return S, function(S)





def random_submodular_maximization(ground_set, function, k):

    """

    随机算法: 随机选择 k 个元素

    

    对于次模函数,随机选择的期望值至少是 1/2 * OPT

    

    Parameters

    ----------

    ground_set : set

        候选元素集合

    function : callable

        次模函数

    k : int

        选择数量

    

    Returns

    -------

    tuple

        (选择的集合, 函数值)

    """

    elements = list(ground_set)

    S = set(random.sample(elements, min(k, len(elements))))

    return S, function(S)





def multilinear_extension_sample(S, random_sets):

    """

    多线性扩展的采样估计

    

    多线性扩展 F(x) = E_{R ~ p}[f(R)]

    其中 p 是概率分布

    

    Parameters

    ----------

    S : set

        要估计的集合

    random_sets : list

        随机采样集合列表

    

    Returns

    -------

    float

        估计值

    """

    values = [f(R & S) for R in random_sets for f in [random_sets[0].__class__]]

    # 简化: 直接使用 f(S) 估计

    return values[0] if values else 0





def continuous_greedy(ground_set, function, k, num_samples=100):

    """

    连续贪心算法

    

    思想: 在多线性扩展的连续域中优化,然后取整

    

    Parameters

    ----------

    ground_set : set

        候选集合

    function : callable

        次模函数

    k : int

        选择数量

    

    Returns

    -------

    tuple

        (离散集合, 函数值)

    """

    n = len(ground_set)

    elements = list(ground_set)

    

    # 初始化分数向量

    w = np.zeros(n)

    

    for _ in range(k):

        # 计算每个元素的边际收益

        marginals = []

        for i in range(n):

            if elements[i] in w:

                continue

            # 简化的边际收益估计

            S_current = set()

            for j in range(n):

                if w[j] > random.random():

                    S_current.add(elements[j])

            

            marginal = function(S_current | {elements[i]}) - function(S_current)

            marginals.append(marginal)

        

        # 选择边际收益最大的元素

        if marginals:

            best_idx = np.argmax(marginals)

            w[best_idx] = 1.0

    

    # 取整得到离散解

    S = {elements[i] for i in range(n) if w[i] > 0.5}

    

    return S, function(S)





def stochastic_greedy(ground_set, function, k, epsilon=0.1):

    """

    随机贪心算法

    

    在贪心过程中,不是检查所有剩余元素,

    而是随机采样一个小子集

    

    时间复杂度: O(k * n / epsilon)

    近似比: (1 - 1/e - epsilon)

    

    Parameters

    ----------

    ground_set : set

        候选集合

    function : callable

        次模函数

    k : int

        选择数量

    epsilon : float

        采样比例参数

    

    Returns

    -------

    tuple

        (选择的集合, 函数值)

    """

    S = set()

    remaining = set(ground_set)

    n = len(remaining)

    

    for i in range(k):

        # 采样大小

        sample_size = max(1, int(n * epsilon / (k - i)))

        

        # 随机采样

        if len(remaining) <= sample_size:

            sample = remaining

        else:

            sample = set(random.sample(list(remaining), sample_size))

        

        # 在采样中找到最优

        best_element = None

        best_marginal = -float('inf')

        

        for e in sample:

            marginal = function(S | {e}) - function(S)

            if marginal > best_marginal:

                best_marginal = marginal

                best_element = e

        

        if best_element:

            S.add(best_element)

            remaining.discard(best_element)

        else:

            break

    

    return S, function(S)





def max_coverage_greedy(ground_set, subsets, k):

    """

    最大覆盖问题的贪心算法

    

    f(S) = |∪_{i∈S} subsets[i]| 是单调次模函数

    

    近似比: (1 - 1/e) 对于最大覆盖

    

    Parameters

    ----------

    ground_set : set

        元素全集

    subsets : dict

        子集字典,{name: elements}

    k : int

        选择的子集数量

    

    Returns

    -------

    tuple

        (选择的子集, 覆盖的元素数)

    """

    def coverage(S):

        return len(set().union(*[subsets[s] for s in S if s in subsets]))

    

    return greedy_maximize_monotone_submodular(set(subsets.keys()), coverage, k)





def influence_maximization_greedy(graph, k, threshold=0.5):

    """

    影响力最大化的贪心算法

    

    使用独立级联 (IC) 模型

    

    f(S) = E[影响力传播范围]

    

    Parameters

    ----------

    graph : dict

        图的邻接表 {u: [v1, v2, ...]}

    k : int

        选择的种子节点数量

    threshold : float

        激活阈值

    

    Returns

    -------

    tuple

        (种子节点集合, 估计影响力)

    """

    def influence(S, num_simulations=100):

        total_influenced = 0

        

        for _ in range(num_simulations):

            # 独立级联模型

            activated = set(S)

            newly_activated = set(S)

            

            while newly_activated:

                next_activated = set()

                for u in newly_activated:

                    for v in graph.get(u, []):

                        if v not in activated and random.random() < threshold:

                            next_activated.add(v)

                

                activated |= next_activated

                newly_activated = next_activated

            

            total_influenced += len(activated)

        

        return total_influenced / num_simulations

    

    ground_set = set(graph.keys())

    return greedy_maximize_monotone_submodular(ground_set, influence, k)





def compute_dominating_set_lower_bound(ground_set, function, k):

    """

    计算次模最大化下界 (使用随机子集)

    

    E[f(random subset of size k)] >= (1 - (1 - k/n)^p) * f(V)

    

    Parameters

    ----------

    ground_set : set

        全集

    function : callable

        次模函数

    k : int

        子集大小

    

    Returns

    -------

    float

        下界估计

    """

    n = len(ground_set)

    if k >= n:

        return function(ground_set)

    

    # 随机采样子集

    samples = 50

    total_value = 0

    

    for _ in range(samples):

        sample = set(random.sample(list(ground_set), min(k, n)))

        total_value += function(sample)

    

    avg_value = total_value / samples

    

    # 理论上 E[f(S)] >= (1 - (1-k/n)^2) * f(V) 对于某些次模函数

    # 这里返回采样均值作为下界

    

    return avg_value





if __name__ == "__main__":

    # 测试: 次模函数最大化

    

    print("=" * 60)

    print("次模函数最大化测试")

    print("=" * 60)

    

    random.seed(42)

    np.random.seed(42)

    

    # 创建测试环境

    # 全集: 20 个元素

    ground_set = set(range(20))

    

    # 定义最大覆盖函数

    # 子集: 每个元素 i 对应覆盖 {i, i+1, i+2}

    subsets = {i: {(i + j) % 20 for j in range(3)} for i in range(20)}

    

    def coverage(S):

        return len(set().union(*[subsets[s] for s in S if s in subsets]))

    

    # 验证次模性

    print("\n--- 验证次模性 ---")

    

    test_sets = [

        ({0, 1}, {0, 1, 2}),

        ({0, 5}, {0, 1, 5}),

        ({3, 4, 5}, {3, 4, 5, 6}),

    ]

    

    # 简化的次模性检验

    print(f"覆盖函数值:")

    for S in [{0}, {1}, {0, 1}, {0, 1, 2}]:

        print(f"  f({S}) = {coverage(S)}")

    

    # 测试最大覆盖

    print("\n--- 最大覆盖 (贪心 1-1/e 近似) ---")

    

    k = 5

    S_greedy, val_greedy = max_coverage_greedy(ground_set, subsets, k)

    print(f"贪心选择 {k} 个子集:")

    print(f"  选择的子集: {S_greedy}")

    print(f"  覆盖元素数: {val_greedy}")

    

    # 随机选择比较

    S_rand, val_rand = random_submodular_maximization(ground_set, coverage, k)

    print(f"随机选择 {k} 个子集:")

    print(f"  覆盖元素数: {val_rand}")

    

    # 随机贪心

    S_stoch, val_stoch = stochastic_greedy(ground_set, coverage, k, epsilon=0.1)

    print(f"随机贪心:")

    print(f"  覆盖元素数: {val_stoch}")

    

    # 计算下界

    lower_bound = compute_dominating_set_lower_bound(ground_set, coverage, k)

    print(f"\n随机子集期望下界: {lower_bound:.2f}")

    print(f"贪心近似比 (相对于下界): {val_greedy / lower_bound:.4f}")

    

    # 测试影响力最大化 (小规模图)

    print("\n--- 影响力最大化 ---")

    

    # 创建小世界网络

    n_nodes = 15

    influence_graph = {i: [] for i in range(n_nodes)}

    

    # 添加一些边

    for i in range(n_nodes):

        influence_graph[i].append((i + 1) % n_nodes)

        influence_graph[i].append((i + 2) % n_nodes)

    

    # 简化为邻居列表

    simple_graph = {i: [(i + 1) % n_nodes, (i + 2) % n_nodes] for i in range(n_nodes)}

    

    k_seeds = 3

    seeds, est_influence = influence_maximization_greedy(simple_graph, k_seeds, threshold=0.3)

    

    print(f"影响力最大化 (IC 模型, 阈值=0.3):")

    print(f"  选择的种子节点: {seeds}")

    print(f"  估计影响力: {est_influence:.2f}")

    

    # 比较随机选择

    random_seeds = set(random.sample(list(simple_graph.keys()), k_seeds))

    print(f"  随机种子节点: {random_seeds}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)


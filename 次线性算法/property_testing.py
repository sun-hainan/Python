# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / property_testing

本文件实现 property_testing 相关的算法功能。
"""

import numpy as np
import random


def test_linearity(f, domain_size, num_queries=100):
    """
    线性性测试 (BLR Test)
    
    性质: f: {0,1}^n -> {0,1} 是线性的
    即: f(x) + f(y) = f(x+y) (mod 2)
    
    BLR 测试:
    1. 随机选择 x, y
    2. 查询 f(x), f(y), f(x+y)
    3. 如果 f(x) ⊕ f(y) ≠ f(x+y),拒绝
    
    查询复杂度: O(1)
    
    Parameters
    ----------
    f : callable
        黑盒函数 f: bitstring -> bit
    domain_size : int
        定义域大小 (2^n)
    num_queries : int
        测试轮数
    
    Returns
    -------
    tuple
        (是否通过测试, 拒绝次数)
    """
    n = int(np.log2(domain_size))
    rejects = 0
    
    for _ in range(num_queries):
        # 随机选择 x, y
        x = random.randint(0, domain_size - 1)
        y = random.randint(0, domain_size - 1)
        
        # 计算 x ⊕ y
        x_plus_y = x ^ y
        
        # 查询
        fx = f(x)
        fy = f(y)
        fxy = f(x_plus_y)
        
        # 检查线性性
        if fx ^ fy != fxy:
            rejects += 1
    
    # 如果拒绝率过高,认为不满足线性性
    reject_rate = rejects / num_queries
    
    # 对于真正线性函数,拒绝率应该为 0
    # 对于 ε-远离线性,拒绝率至少 ε/2
    passes = reject_rate < 0.1  # 阈值
    
    return passes, reject_rate


def test_dictinctness(stream, sample_size=None):
    """
    测试元素是否全部不同 (Distinctness)
    
    使用 Flajolet-Martin 算法估计不同元素数
    
    参数:
    - 如果估计的不同元素数 ≈ 流长度,则可能全部不同
    
    Parameters
    ----------
    stream : list
        数据流
    sample_size : int
        采样大小
    
    Returns
    -------
    tuple
        (是否可能全部不同, 估计的不同元素数)
    """
    n = len(stream)
    
    if sample_size is None:
        sample_size = min(1000, n)
    
    if n != len(set(stream)):
        return False, len(set(stream))
    
    # 采样估计
    sample = random.sample(stream, min(sample_size, n))
    distinct_in_sample = len(set(sample))
    
    # 估计总体不同元素数
    estimated_distinct = distinct_in_sample * n / sample_size
    
    # 如果估计值接近 n,可能全部不同
    is_distinct = abs(estimated_distinct - n) < 0.1 * n
    
    return is_distinct, estimated_distinct


def test_uniformity(f, domain_size, num_queries=100):
    """
    测试分布的均匀性
    
    性质: f 产生的分布是均匀的
    
    使用 χ^2 检验的思想:
    - 将 domain 分成 k 个桶
    - 观察每个桶的频率
    - 如果偏离均匀分布过多,拒绝
    
    Parameters
    ----------
    f : callable
        黑盒采样函数 f() -> 样本
    domain_size : int
        定义域大小
    num_queries : int
        采样数量
    
    Returns
    -------
    tuple
        (是否通过测试, χ^2 统计量)
    """
    # 分桶
    num_buckets = int(np.sqrt(domain_size))
    bucket_size = domain_size / num_buckets
    
    counts = [0] * num_buckets
    
    # 采样
    for _ in range(num_queries):
        sample = f()
        bucket_idx = min(int(sample / bucket_size), num_buckets - 1)
        counts[bucket_idx] += 1
    
    # 计算 χ^2 统计量
    expected = num_queries / num_buckets
    chi_squared = sum((observed - expected) ** 2 / expected 
                      for observed in counts)
    
    # 自由度 = num_buckets - 1
    df = num_buckets - 1
    
    # 简化判断: 如果 χ^2 太大,拒绝
    threshold = df + 3 * np.sqrt(2 * df)
    passes = chi_squared < threshold
    
    return passes, chi_squared


def test_monotonicity(sequence):
    """
    测试序列是否单调递增
    
    使用二分测试:
    1. 随机查询位置 i < j
    2. 检查 a[i] <= a[j]
    
    单调性测试可以 o(n) 时间完成
    
    Parameters
    ----------
    sequence : list
        输入序列
    
    Returns
    -------
    tuple
        (是否单调, 违反位置对数量)
    """
    n = len(sequence)
    num_queries = min(100, n * (n - 1) // 2)
    
    violations = 0
    
    for _ in range(num_queries):
        i = random.randint(0, n - 2)
        j = random.randint(i + 1, n - 1)
        
        if sequence[i] > sequence[j]:
            violations += 1
    
    # 估计违反比例
    total_pairs = n * (n - 1) // 2
    violation_rate = violations / num_queries
    
    # 如果违反率过高,认为不单调
    is_monotone = violations == 0
    
    return is_monotone, violations


def test_graph_connectivity(graph, sample_size=None):
    """
    测试图是否连通
    
    使用 BFS 从随机起点
    如果能到达所有顶点,则连通
    
    Parameters
    ----------
    graph : dict
        图的邻接表
    sample_size : int
        采样大小 (顶点数量的函数)
    
    Returns
    -------
    tuple
        (是否连通, BFS 访问的顶点数)
    """
    vertices = list(graph.keys())
    n = len(vertices)
    
    if sample_size is None:
        sample_size = min(50, n)
    
    # 多次随机起点测试
    for _ in range(3):
        start = random.choice(vertices)
        
        # BFS
        visited = set()
        queue = [start]
        visited.add(start)
        
        while queue:
            v = queue.pop(0)
            for nb in graph.get(v, []):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        
        # 如果访问的顶点比例过低,认为不连通
        if len(visited) < n * 0.8:
            return False, len(visited)
    
    return True, n


def test_graph_bipartiteness(graph, sample_size=None):
    """
    测试图是否是二分的
    
    使用 BFS 着色:
    1. 从随机起点开始 BFS
    2. 交替着色
    3. 如果发现同色相邻,不是二分
    
    Parameters
    ----------
    graph : dict
        图的邻接表
    
    Returns
    -------
    tuple
        (是否二分, 冲突信息)
    """
    vertices = list(graph.keys())
    n = len(vertices)
    
    if n == 0:
        return True, None
    
    # 初始化颜色 (-1 表示未着色)
    color = {v: -1 for v in vertices}
    
    # 多次连通分量测试
    for start in vertices:
        if color[start] != -1:
            continue
        
        # BFS
        queue = [start]
        color[start] = 0
        
        while queue:
            v = queue.pop(0)
            
            for nb in graph.get(v, []):
                if color[nb] == -1:
                    color[nb] = 1 - color[v]
                    queue.append(nb)
                elif color[nb] == color[v]:
                    return False, f"冲突: {v} 和 {nb} 同色"
    
    return True, None


def test_power_of_two(f, domain_size, num_queries=100):
    """
    测试函数是否是 2 的幂函数
    
    性质: f(x) = 2^x 或类似性质
    
    使用自举测试:
    1. 随机查询 f(x)
    2. 检查 f(x) 是否满足某种代数性质
    
    Parameters
    ----------
    f : callable
        黑盒函数
    domain_size : int
        定义域大小
    num_queries : int
        查询数量
    
    Returns
    -------
    tuple
        (是否通过测试, 统计信息)
    """
    # 简化的测试: 检查函数值是否都是正数
    # 实际应该检查更复杂的性质
    
    values = []
    for _ in range(num_queries):
        x = random.randint(0, domain_size - 1)
        values.append(f(x))
    
    # 检查是否都是正数
    all_positive = all(v > 0 for v in values)
    
    # 检查增长率
    sorted_vals = sorted(values)
    growth_rate = sorted_vals[-1] / sorted_vals[0] if sorted_vals[0] > 0 else float('inf')
    
    return all_positive, {'growth_rate': growth_rate}


def test_juntas(f, n, k, num_queries=None):
    """
    测试函数是否是 k-Junta
    
    定义: f 只依赖于最多 k 个变量
    
    算法:
    1. 随机查询函数值
    2. 找到影响输出较大的变量
    3. 如果只发现 <= k 个重要变量,则是 k-Junta
    
    Parameters
    ----------
    f : callable
        黑盒函数 f: {0,1}^n -> {0,1}
    n : int
        变量数
    k : int
        Junta 参数
    num_queries : int
        查询数量
    
    Returns
    -------
    tuple
        (是否是 k-Junta, 估计的重要变量数)
    """
    if num_queries is None:
        num_queries = 10 * n / k
    
    # 简化的测试: 随机采样检查
    important_vars = set()
    
    for _ in range(int(num_queries)):
        # 随机选择变量子集
        indices = random.sample(range(n), min(k, n))
        
        # 查询函数值
        x = [random.randint(0, 1) for _ in range(n)]
        fx = f(x)
        
        # 简化的影响估计
        for i in indices:
            x_flipped = x.copy()
            x_flipped[i] ^= 1
            fx_flipped = f(x_flipped)
            
            if fx != fx_flipped:
                important_vars.add(i)
    
    is_junta = len(important_vars) <= k
    
    return is_junta, len(important_vars)


def distance_to_property(property_func, actual_func, domain, property_param=None):
    """
    估计函数到性质的"距离"
    
    距离定义为需要改变的最小输入比例
    
    Parameters
    ----------
    property_func : callable
        满足性质的参考函数
    actual_func : callable
        实际函数
    domain : list
        定义域
    property_param : any
        性质的额外参数
    
    Returns
    -------
    float
        估计的距离
    """
    # 采样估计
    sample_size = min(1000, len(domain))
    sample = random.sample(domain, sample_size)
    
    disagreements = sum(1 for x in sample if actual_func(x) != property_func(x, property_param))
    
    distance = disagreements / sample_size
    
    return distance


if __name__ == "__main__":
    # 测试: 性质测试
    
    print("=" * 60)
    print("性质测试算法测试")
    print("=" * 60)
    
    random.seed(42)
    np.random.seed(42)
    
    # 测试线性性
    print("\n--- 线性性测试 (BLR) ---")
    
    def linear_function(x):
        """真正的线性函数: f(x) = x 的最低位"""
        return bin(x).count('1') % 2
    
    def noisy_linear(x):
        """带噪声的线性函数"""
        return linear_function(x) ^ (1 if random.random() < 0.1 else 0)
    
    passes_linear, reject_rate = test_linearity(linear_function, 16, num_queries=50)
    print(f"真正线性函数: 通过={passes_linear}, 拒绝率={reject_rate:.2f}")
    
    passes_noisy, reject_rate_noisy = test_linearity(noisy_linear, 16, num_queries=50)
    print(f"噪声线性函数: 通过={passes_noisy}, 拒绝率={reject_rate_noisy:.2f}")
    
    # 测试连通性
    print("\n--- 图连通性测试 ---")
    
    connected_graph = {
        0: [1, 2],
        1: [0, 2, 3],
        2: [0, 1, 3],
        3: [1, 2, 4],
        4: [3]
    }
    
    disconnected_graph = {
        0: [1],
        1: [0],
        2: [3],
        3: [2]
    }
    
    is_connected, visited = test_graph_connectivity(connected_graph)
    print(f"连通图: 连通={is_connected}, 访问顶点数={visited}")
    
    is_connected2, visited2 = test_graph_connectivity(disconnected_graph)
    print(f"非连通图: 连通={is_connected2}, 访问顶点数={visited2}")
    
    # 测试二分性
    print("\n--- 图二分性测试 ---")
    
    bipartite_graph = {
        0: [1, 2],
        1: [0, 3],
        2: [0, 3],
        3: [1, 2]
    }
    
    non_bipartite = {
        0: [1, 2],
        1: [0, 2],
        2: [0, 1, 3],
        3: [2]
    }  # 三角形
    
    is_bip1, _ = test_graph_bipartiteness(bipartite_graph)
    print(f"二分图: 是二分={is_bip1}")
    
    is_bip2, conflict = test_graph_bipartiteness(non_bipartite)
    print(f"非二分图: 是二分={is_bip2}, 冲突={conflict}")
    
    # 测试单调性
    print("\n--- 单调性测试 ---")
    
    monotone_seq = [1, 3, 5, 7, 9, 11]
    non_monotone_seq = [1, 3, 2, 7, 9, 5]
    
    is_mono1, viol1 = test_monotonicity(monotone_seq)
    print(f"单调序列: 单调={is_mono1}, 违反数={viol1}")
    
    is_mono2, viol2 = test_monotonicity(non_monotone_seq)
    print(f"非单调序列: 单调={is_mono2}, 违反数={viol2}")
    
    # 测试均匀性
    print("\n--- 均匀性测试 ---")
    
    def uniform_sampler():
        return random.randint(0, 9)
    
    def biased_sampler():
        # 90% 概率返回 0
        return 0 if random.random() < 0.9 else random.randint(1, 9)
    
    passes_uniform, chi2_uniform = test_uniformity(uniform_sampler, 10, num_queries=200)
    print(f"均匀分布: 通过={passes_uniform}, χ²={chi2_uniform:.2f}")
    
    passes_biased, chi2_biased = test_uniformity(biased_sampler, 10, num_queries=200)
    print(f"偏斜分布: 通过={passes_biased}, χ²={chi2_biased:.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

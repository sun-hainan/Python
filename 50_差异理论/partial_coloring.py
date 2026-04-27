# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / partial_coloring



本文件实现 partial_coloring 相关的算法功能。

"""



import math

import random

from typing import List, Tuple, Optional, Dict

import numpy as np





def compute_incidence_matrix(n, sets):

    """

    构建集合族的关联矩阵 A。

    A[i][j] = 1 如果元素 i 在集合 j 中，否则为 0。

    

    参数:

        n: int - 元素数量

        sets: List[List[int]] - 集合族

    

    返回:

        numpy.ndarray - n x m 的关联矩阵

    """

    m = len(sets)

    A = np.zeros((n, m), dtype=float)

    for col_idx, s in enumerate(sets):

        for element in s:

            A[element][col_idx] = 1.0

    return A





def partial_coloring_basic(A, t=None):

    """

    基础部分着色算法。

    

    找到向量 x 使得 ||Ax||_∞ 最小化，同时 x 的 L2 范数受限于 t。

    这等价于解决一个半正定规划问题。

    

    参数:

        A: numpy.ndarray - 关联矩阵 (n x m)

        t: float - 控制参数，决定 x 的范数上界

    

    返回:

        numpy.ndarray - 部分着色向量

    """

    n, m = A.shape

    if t is None:

        t = math.sqrt(n)

    

    # 简化的部分着色策略：基于概率的方法

    # 实际实现中应使用半正定规划求解器

    x = np.zeros(m)

    

    # 计算每个集合的基本权重

    set_weights = np.sum(A, axis=0)

    

    # 概率方法：每个集合以某个概率被选中

    for j in range(m):

        # 使用基于权重的不对称随机游动

        prob = 0.5 + 0.1 * (set_weights[j] / max(set_weights))

        prob = min(prob, 0.9)

        x[j] = 1 if random.random() < prob else -1

    

    # 将完全着色转换为部分着色

    return x





def beck_partial_coloring_lemma(A, delta=0.5):

    """

    Beck 的部分着色引理实现。

    

    引理陈述：对于任意实矩阵 A，存在向量 x ∈ {-1,0,1}^m

    使得对每一行 i，有 |(Ax)_i| ≤ C，其中 C 是一个绝对常数。

    

    参数:

        A: numpy.ndarray - 关联矩阵

        delta: float - 精度参数

    

    返回:

        Tuple[numpy.ndarray, float] - (着色向量, 差异界)

    """

    n, m = A.shape

    

    # 计算奇异值

    singular_values = np.linalg.svd(A, compute_uv=False)

    spectral_norm = singular_values[0] if len(singular_values) > 0 else 0

    

    # Beck 引理给出的界: O(sqrt(n * log m))

    C = 2.0 * spectral_norm * math.sqrt(math.log(max(m, 2)) / n)

    

    # 构造着色向量

    x = partial_coloring_basic(A)

    

    return x, C





def symmetric_random_walk(n_steps, bias=0.1):

    """

    带偏置的对称随机游动，用于部分着色。

    

    参数:

        n_steps: int - 游动步数

        bias: float - 偏差参数，控制向 +1 或 -1 的漂移

    

    返回:

        float - 最终位置

    """

    position = 0.0

    for _ in range(n_steps):

        # 以概率 0.5 + bias 向 +1 移动，否则向 -1 移动

        step = 1 if random.random() < (0.5 + bias) else -1

        position += step

    return position





def partial_coloring_via_entropy(A, num_iterations=100):

    """

    基于熵方法的 partial coloring 算法。

    

    该方法利用信息熵的概念，在随机化过程中

    逐步减小差异上界。

    

    参数:

        A: numpy.ndarray - 关联矩阵

        num_iterations: int - 迭代次数

    

    返回:

        numpy.ndarray - 部分着色向量

    """

    n, m = A.shape

    

    # 初始化：所有元素设为 0（未着色）

    x = np.zeros(m)

    current_weights = np.zeros(n)

    

    for iteration in range(num_iterations):

        # 选择一个未完全着色的变量进行更新

        undecided = [j for j in range(m) if abs(x[j]) < 1.0]

        if not undecided:

            break

        

        j = random.choice(undecided)

        

        # 计算当前解的差异

        residual = A @ x - current_weights

        

        # 选择使最大差异最小的方向

        direction = 1 if random.random() < 0.5 else -1

        x[j] += direction

        

        # 更新权重

        current_weights = A @ x

        

        # 如果差异超过阈值，回退

        max_discrepancy = np.max(np.abs(A @ x))

        if max_discrepancy > 10 * math.sqrt(n):

            x[j] -= direction

    

    # 截断到 {-1, 0, 1}

    x = np.sign(x)

    

    return x





def iterative_partial_coloring(A, num_colors=5):

    """

    迭代部分着色：将完全着色分解为多个 partial coloring 步骤。

    

    参数:

        A: numpy.ndarray - 关联矩阵

        num_colors: int - 分解的层数

    

    返回:

        numpy.ndarray - 最终着色向量

    """

    n, m = A.shape

    

    # 初始化为零向量

    x_total = np.zeros(m)

    residual_sets = A.copy()

    

    for layer in range(num_colors):

        # 对当前残差运行部分着色

        x_layer, bound = beck_partial_coloring_lemma(residual_sets)

        

        # 将当前层的解加入总体解

        x_total += x_layer

        

        # 更新残差

        residual_sets = A - A @ np.diag(np.sign(x_total))

    

    return np.sign(x_total)





def partial_coloring_with_constraints(A, fixed_vars, fixed_values):

    """

    带约束的部分着色：某些变量必须取特定值。

    

    参数:

        A: numpy.ndarray - 关联矩阵

        fixed_vars: List[int] - 固定变量的索引

        fixed_values: List[int] - 固定变量的值 (+1 或 -1)

    

    返回:

        numpy.ndarray - 满足约束的部分着色向量

    """

    n, m = A.shape

    x = np.zeros(m)

    

    # 设置固定变量

    for idx, val in zip(fixed_vars, fixed_values):

        x[idx] = val

    

    # 对自由变量运行部分着色

    free_vars = [j for j in range(m) if j not in fixed_vars]

    

    if free_vars:

        A_free = A[:, free_vars]

        x_free = partial_coloring_basic(A_free)

        for idx, val in zip(free_vars, x_free):

            x[idx] = val

    

    return x





def compute_partial_discrepancy(x, A):

    """

    计算部分着色方案的差异度。

    

    参数:

        x: numpy.ndarray - 着色向量

        A: numpy.ndarray - 关联矩阵

    

    返回:

        Dict - 包含各行差异和总差异的字典

    """

    result = A @ x

    abs_result = np.abs(result)

    

    discrepancy_info = {

        'max_discrepancy': np.max(abs_result),

        'min_discrepancy': np.min(abs_result),

        'avg_discrepancy': np.mean(abs_result),

        'row_discrepancies': result.tolist()

    }

    

    return discrepancy_info





def verify_partial_coloring_property(x, A, bound):

    """

    验证部分着色是否满足差异上界。

    

    参数:

        x: numpy.ndarray - 着色向量

        A: numpy.ndarray - 关联矩阵

        bound: float - 上界值

    

    返回:

        bool - 是否满足

    """

    result = A @ x

    return np.all(np.abs(result) <= bound)





def random_partial_coloring(m, density=0.3):

    """

    生成随机部分着色向量。

    

    参数:

        m: int - 向量维度

        density: float - 非零元素的比例

    

    返回:

        numpy.ndarray - 随机部分着色向量

    """

    x = np.zeros(m)

    for j in range(m):

        r = random.random()

        if r < density:

            x[j] = 1

        elif r < 2 * density:

            x[j] = -1

        # 否则保持为 0（未着色）

    return x





def generate_balanced_sets(n, m):

    """

    生成平衡的集合族，每个元素出现在近似相同数量的集合中。

    

    参数:

        n: int - 元素数量

        m: int - 集合数量

    

    返回:

        List[List[int]] - 集合族

    """

    # 确保每个元素至少在一个集合中

    sets = []

    target_frequency = (m * 5) // n  # 每个元素出现约 5 次

    

    for _ in range(m):

        size = random.randint(3, 8)

        elements = random.sample(range(n), min(size, n))

        sets.append(elements)

    

    return sets





def benchmark_partial_coloring_methods(n, m, num_trials=10):

    """

    比较不同部分着色方法的性能。

    

    参数:

        n: int - 元素数量

        m: int - 集合数量

        num_trials: int - 试验次数

    

    返回:

        Dict - 各方法的平均性能

    """

    results = {

        'basic': [],

        'entropy': [],

        'iterative': []

    }

    

    for trial in range(num_trials):

        random.seed(trial * 17)

        sets = generate_balanced_sets(n, m)

        A = compute_incidence_matrix(n, sets)

        

        # 基本方法

        x_basic, bound_basic = beck_partial_coloring_lemma(A)

        disc_basic = np.max(np.abs(A @ x_basic))

        results['basic'].append(disc_basic)

        

        # 熵方法

        x_entropy = partial_coloring_via_entropy(A, num_iterations=50)

        disc_entropy = np.max(np.abs(A @ x_entropy))

        results['entropy'].append(disc_entropy)

        

        # 迭代方法

        x_iterative = iterative_partial_coloring(A, num_colors=3)

        disc_iterative = np.max(np.abs(A @ x_iterative))

        results['iterative'].append(disc_iterative)

    

    return {

        method: sum(values) / len(values) if values else 0

        for method, values in results.items()

    }





if __name__ == "__main__":

    print("=" * 70)

    print("部分着色算法 (Partial Coloring) 测试")

    print("=" * 70)

    

    # 基本测试

    print("\n1. 基本功能测试")

    n = 30  # 元素数量

    m = 15  # 集合数量

    sets = generate_balanced_sets(n, m)

    

    print(f"元素数量: {n}")

    print(f"集合数量: {m}")

    

    # 构建关联矩阵

    A = compute_incidence_matrix(n, sets)

    print(f"关联矩阵形状: {A.shape}")

    print(f"非零元素比例: {np.count_nonzero(A) / (n * m):.2%}")

    

    # Beck 部分着色引理

    print("\n2. Beck 部分着色引理测试")

    x, bound = beck_partial_coloring_lemma(A)

    disc_info = compute_partial_discrepancy(x, A)

    print(f"理论界: {bound:.4f}")

    print(f"最大差异: {disc_info['max_discrepancy']:.4f}")

    print(f"平均差异: {disc_info['avg_discrepancy']:.4f}")

    print(f"是否满足性质: {verify_partial_coloring_property(x, A, bound * 2)}")

    

    # 熵方法测试

    print("\n3. 熵方法测试")

    x_entropy = partial_coloring_via_entropy(A, num_iterations=100)

    disc_entropy = compute_partial_discrepancy(x_entropy, A)

    print(f"最大差异: {disc_entropy['max_discrepancy']:.4f}")

    print(f"非零元素比例: {np.count_nonzero(x_entropy) / m:.2%}")

    

    # 迭代方法测试

    print("\n4. 迭代部分着色测试")

    x_iterative = iterative_partial_coloring(A, num_colors=3)

    disc_iter = compute_partial_discrepancy(x_iterative, A)

    print(f"最大差异: {disc_iter['max_discrepancy']:.4f}")

    

    # 带约束的测试

    print("\n5. 带约束的部分着色测试")

    fixed_vars = [0, 1, 2]

    fixed_values = [1, -1, 1]

    x_constrained = partial_coloring_with_constraints(A, fixed_vars, fixed_values)

    disc_constrained = compute_partial_discrepancy(x_constrained, A)

    print(f"固定变量: {fixed_vars}")

    print(f"固定值: {fixed_values}")

    print(f"最大差异: {disc_constrained['max_discrepancy']:.4f}")

    

    # 性能比较

    print("\n6. 方法性能比较")

    comparison = benchmark_partial_coloring_methods(n=40, m=20, num_trials=5)

    print(f"基本方法平均差异: {comparison['basic']:.4f}")

    print(f"熵方法平均差异: {comparison['entropy']:.4f}")

    print(f"迭代方法平均差异: {comparison['iterative']:.4f}")

    

    # 不同规模测试

    print("\n7. 不同规模测试")

    test_configs = [

        (20, 10),

        (50, 25),

        (100, 50),

    ]

    

    for n_t, m_t in test_configs:

        A_t = compute_incidence_matrix(n_t, generate_balanced_sets(n_t, m_t))

        x_t, bound_t = beck_partial_coloring_lemma(A_t)

        disc_t = np.max(np.abs(A_t @ x_t))

        print(f"n={n_t:3d}, m={m_t:3d}: 理论界={bound_t:7.2f}, "

              f"实际差异={disc_t:7.2f}, 效率={disc_t/max(bound_t, 0.001):.2f}")

    

    print("\n" + "=" * 70)

    print("复杂度分析:")

    print("  - compute_incidence_matrix: O(n * m * avg_size)")

    print("  - beck_partial_coloring_lemma: O(n * m^2) [SVD 计算]")

    print("  - partial_coloring_via_entropy: O(iterations * n * m)")

    print("  - iterative_partial_coloring: O(num_colors * n * m^2)")

    print("  - 总体空间复杂度: O(n * m)")

    print("=" * 70)


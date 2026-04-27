# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / b_spline



本文件实现 b_spline 相关的算法功能。

"""



from typing import List, Tuple

import numpy as np





Point = Tuple[float, float]





def compute_basis_functions(i: int, k: int, t: float, knot_vector: List[float]) -> List[float]:

    """

    计算第 i 个 B 样条基函数（de Boor 递归）

    

    参数:

        i: 基函数索引

        k: 阶数（次数+1）

        t: 参数值

        knot_vector: 节点向量

    

    返回:

        各基函数的取值

    """

    if k == 1:

        # 零阶基函数

        result = [0.0] * (i + 1)

        if i == 0:

            return [1.0 if knot_vector[0] <= t < knot_vector[1] else 0.0]

        

        result = []

        for j in range(i + 1):

            if knot_vector[j] <= t < knot_vector[j + 1]:

                result.append(1.0)

            else:

                result.append(0.0)

        return result

    

    # de Boor 递归

    result = []

    

    for j in range(i + 1):

        denom1 = knot_vector[j + k - 1] - knot_vector[j]

        denom2 = knot_vector[j + k] - knot_vector[j + 1]

        

        val1 = 0.0

        if denom1 != 0:

            val1 = (t - knot_vector[j]) / denom1

        

        val2 = 0.0

        if denom2 != 0:

            val2 = (knot_vector[j + k] - t) / denom2

        

        # 递归计算左右两部分

        left_basis = compute_basis_functions(j, k - 1, t, knot_vector)

        right_basis = compute_basis_functions(j + 1, k - 1, t, knot_vector)

        

        # 这里需要简化的实现

        result.append(val1 + val2 if j < len(left_basis) else 0)

    

    return result





def de_boor_iterative(control_points: List[Point], k: int, 

                     t: float, knot_vector: List[float]) -> Point:

    """

    de Boor 算法：高效评估 B 样条曲线上的点

    

    参数:

        control_points: 控制点列表

        k: 阶数

        t: 参数值

        knot_vector: 节点向量

    

    返回:

        曲线上的点

    """

    # 找到 t 所在的节点区间

    n = len(control_points) - 1  # 控制点数量 - 1

    degree = k - 1

    

    # 找到使 knot_vector[i] <= t < knot_vector[i+1] 的 i

    i = 0

    for j in range(len(knot_vector) - 1):

        if knot_vector[j] <= t < knot_vector[j + 1]:

            i = j

            break

        elif t == knot_vector[j + 1] and t != knot_vector[-1]:

            i = j + 1

            break

    

    # 限制索引范围

    i = max(k - 1, min(i, n))

    

    # 提取相关控制点

    d = [[control_points[j] for j in range(i - degree, i + 1)]]

    

    # de Boor 迭代

    for r in range(1, degree + 1):

        level = []

        for j in range(degree - r + 1):

            idx1 = i - degree + j

            idx2 = i - r + 1 + j

            

            alpha = 0.0

            denom = knot_vector[idx1 + k] - knot_vector[idx1 + r]

            if denom != 0:

                alpha = (t - knot_vector[idx1 + r]) / denom

            

            # 线性插值

            x = (1 - alpha) * d[-1][j][0] + alpha * d[-1][j + 1][0]

            y = (1 - alpha) * d[-1][j][1] + alpha * d[-1][j + 1][1]

            level.append((x, y))

        

        d.append(level)

    

    return d[-1][0]





def evaluate_bspline(control_points: List[Point], k: int,

                    t: float, knot_vector: List[float]) -> Point:

    """

    评估 B 样条曲线上的点

    

    参数:

        control_points: 控制点列表

        k: 阶数

        t: 参数值

        knot_vector: 节点向量

    

    返回:

        曲线上的点

    """

    return de_boor_iterative(control_points, k, t, knot_vector)





def generate_uniform_knot_vector(n: int, k: int) -> List[float]:

    """

    生成均匀节点向量

    

    参数:

        n: 控制点数量 - 1

        k: 阶数

    

    返回:

        节点向量

    """

    total_knots = n + k  # 节点总数

    knots = []

    

    # 重复节点

    for _ in range(k):

        knots.append(0.0)

    

    # 内部节点（均匀分布）

    num_internal = total_knots - 2 * k

    if num_internal > 0:

        for i in range(1, num_internal + 1):

            knots.append(float(i) / (num_internal + 1))

    

    # 重复节点

    for _ in range(k):

        knots.append(1.0)

    

    return knots





def sample_bspline(control_points: List[Point], k: int,

                  num_samples: int = 100) -> List[Point]:

    """

    采样 B 样条曲线

    

    参数:

        control_points: 控制点列表

        k: 阶数

        num_samples: 采样点数

    

    返回:

        曲线上的点列表

    """

    n = len(control_points) - 1

    knot_vector = generate_uniform_knot_vector(n, k)

    

    # 确定有效参数范围

    t_min = knot_vector[k - 1]

    t_max = knot_vector[n]

    

    points = []

    for i in range(num_samples + 1):

        t = t_min + (t_max - t_min) * i / num_samples

        points.append(de_boor_iterative(control_points, k, t, knot_vector))

    

    return points





def b_spline_basis(i: int, k: int, t: float, knot_vector: List[float]) -> float:

    """

    计算单个 B 样条基函数 N_{i,k}(t)

    

    参数:

        i: 索引

        k: 阶数

        t: 参数

        knot_vector: 节点向量

    

    返回:

        基函数值

    """

    if k == 1:

        return 1.0 if knot_vector[i] <= t < knot_vector[i + 1] else 0.0

    

    result = 0.0

    

    # 第一项

    denom1 = knot_vector[i + k - 1] - knot_vector[i]

    if denom1 != 0:

        result += (t - knot_vector[i]) / denom1 * b_spline_basis(i, k - 1, t, knot_vector)

    

    # 第二项

    denom2 = knot_vector[i + k] - knot_vector[i + 1]

    if denom2 != 0:

        result += (knot_vector[i + k] - t) / denom2 * b_spline_basis(i + 1, k - 1, t, knot_vector)

    

    return result





def b_spline_curve_point(control_points: List[Point], k: int,

                         t: float, knot_vector: List[float]) -> Point:

    """

    使用基函数形式计算 B 样条曲线点

    

    C(t) = Σ P_i × N_{i,k}(t)

    

    参数:

        control_points: 控制点

        k: 阶数

        t: 参数

        knot_vector: 节点向量

    

    返回:

        曲线上的点

    """

    n = len(control_points) - 1

    x, y = 0.0, 0.0

    

    for i in range(n + 1):

        basis = b_spline_basis(i, k, t, knot_vector)

        x += control_points[i][0] * basis

        y += control_points[i][1] * basis

    

    return (x, y)





if __name__ == "__main__":

    print("=" * 60)

    print("B样条曲线 (B-Spline) 测试")

    print("=" * 60)

    

    # 测试1：三次均匀 B 样条

    print("\n测试1 - 三次均匀 B 样条:")

    control_points = [

        (0.0, 0.0),

        (3.0, 10.0),

        (7.0, 10.0),

        (10.0, 0.0),

        (13.0, 5.0),

    ]

    

    k = 4  # 四阶 = 三次

    n = len(control_points) - 1

    knot_vector = generate_uniform_knot_vector(n, k)

    

    print(f"  控制点数: {n + 1}")

    print(f"  阶数: {k} (三次)")

    print(f"  节点向量: {[f'{v:.2f}' for v in knot_vector]}")

    

    # 采样

    samples = sample_bspline(control_points, k, 20)

    print(f"\n  采样点 (前10个):")

    for i, p in enumerate(samples[:10]):

        t = i / 20

        print(f"    t={t:.2f}: ({p[0]:.2f}, {p[1]:.2f})")

    

    # 测试2：与其他曲线比较

    print("\n测试2 - 不同阶数比较:")

    for k in [2, 3, 4]:  # 二次、三次、四次

        print(f"\n  {k-1}次 B 样条:")

        knot = generate_uniform_knot_vector(n, k)

        

        # 采样

        samples = sample_bspline(control_points, k, 10)

        print(f"    采样点数: {len(samples)}")

        print(f"    端点: {samples[0]} -> {samples[-1]}")

    

    # 测试3：节点插入

    print("\n测试3 - 节点向量影响:")

    

    # 均匀节点

    uniform_knots = generate_uniform_knot_vector(4, 4)

    print(f"  均匀节点向量: {[f'{v:.2f}' for v in uniform_knots]}")

    

    # 准均匀节点（增加首尾重复）

    def generate_quasi_uniform_knots(n, k):

        knots = [0.0] * k

        internal = 1.0 / (n - k + 2)

        for i in range(1, n - k + 2):

            knots.append(i * internal)

        knots.extend([1.0] * k)

        return knots

    

    quasi_knots = generate_quasi_uniform_knots(5, 4)

    print(f"  准均匀节点向量: {[f'{v:.2f}' for v in quasi_knots]}")

    

    # 测试4：可视化

    print("\n测试4 - 可视化（ASCII）:")

    

    samples = sample_bspline(control_points, 4, 30)

    

    # 创建网格

    width, height = 60, 20

    

    def scale_x(x):

        return int(x * (width - 1) / 15)

    def scale_y(y):

        return int(y * (height - 1) / 12)

    

    grid = [[" " for _ in range(width)] for _ in range(height)]

    

    # 绘制控制多边形

    for i in range(len(control_points) - 1):

        x1, y1 = control_points[i]

        x2, y2 = control_points[i + 1]

        x1, x2 = scale_x(x1), scale_x(x2)

        y1, y2 = scale_y(y1), scale_y(y2)

        

        # 简化：只画端点

        if 0 <= x1 < width and 0 <= y1 < height:

            grid[height - 1 - y1][x1] = "o"

        if 0 <= x2 < width and 0 <= y2 < height:

            grid[height - 1 - y2][x2] = "o"

    

    # 绘制曲线

    for p in samples:

        x, y = scale_x(p[0]), scale_y(p[1])

        if 0 <= x < width and 0 <= y < height:

            grid[height - 1 - y][x] = "*"

    

    # 打印

    for row in grid:

        print("    " + "".join(row))

    

    print("\n  图例: o=控制点, *=B样条曲线")

    

    print("\n" + "=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  评估单个点: O(k × d)  de Boor 算法")

    print("    k = 阶数")

    print("    d = 涉及的控制器数量 ≈ k")

    print("  采样 m 个点: O(m × k²)")

    print("  空间复杂度: O(k) 迭代变量")

    print("  优势: 局部控制，不像 Bezier 全局影响")


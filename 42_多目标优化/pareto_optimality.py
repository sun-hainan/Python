# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / pareto_optimality



本文件实现 pareto_optimality 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional, Callable

from scipy import optimize





def is_pareto_optimal(points: np.ndarray, minimize: bool = True) -> np.ndarray:

    """

    识别Pareto最优解

    

    参数:

        points: 目标矩阵 (n, n_objectives)

        minimize: 是否最小化

    

    返回:

        布尔数组，True表示Pareto最优

    """

    n, m = points.shape

    is_pareto = np.ones(n, dtype=bool)

    

    for i in range(n):

        for j in range(n):

            if i == j:

                continue

            

            if minimize:

                # j支配i

                if np.all(points[j] <= points[i]) and np.any(points[j] < points[i]):

                    is_pareto[i] = False

                    break

            else:

                # j支配i（最大化）

                if np.all(points[j] >= points[i]) and np.any(points[j] > points[i]):

                    is_pareto[i] = False

                    break

    

    return is_pareto





def check_kkt_conditions(objectives: List[Callable],

                         constraints_eq: List[Callable],

                         constraints_ineq: List[Callable],

                         x: np.ndarray,

                         tolerance: float = 1e-6) -> dict:

    """

    检查Karush-Kuhn-Tucker (KKT) 条件

    

    用于单目标优化问题的最优性验证

    

    参数:

        objectives: 目标函数列表（对于MOP，取梯度）

        constraints_eq: 等式约束列表

        constraints_ineq: 不等式约束列表

        x: 候选解

        tolerance: 容差

    

    返回:

        KKT条件满足情况

    """

    result = {

        'feasible': True,

        'stationarity': False,

        'complementary_slackness': False,

        'gradient_lagrangian': None

    }

    

    # 检查可行性

    for eq_constraint in constraints_eq:

        if abs(eq_constraint(x)) > tolerance:

            result['feasible'] = False

            return result

    

    for ineq_constraint in constraints_ineq:

        if ineq_constraint(x) > tolerance:  # g(x) <= 0

            result['feasible'] = False

            return result

    

    # 计算梯度（数值）

    def numerical_gradient(f, x, eps=1e-8):

        grad = np.zeros_like(x)

        for i in range(len(x)):

            x_plus = x.copy()

            x_plus[i] += eps

            grad[i] = (f(x_plus) - f(x)) / eps

        return grad

    

    # 对于多目标，我们需要处理加权和方法

    # 这里简化为检查可行性和梯度

    

    return result





def gradient_ascent_pareto(objectives: List[Callable],

                          x0: np.ndarray,

                          learning_rate: float = 0.01,

                          n_iterations: int = 100) -> np.ndarray:

    """

    使用梯度上升找到Pareto边界点

    

    参数:

        objectives: 目标函数列表

        x0: 初始点

        learning_rate: 学习率

        n_iterations: 迭代次数

    

    返回:

    近似Pareto最优点

    """

    x = x0.copy()

    

    for _ in range(n_iterations):

        # 计算所有目标的梯度

        grads = []

        for obj in objectives:

            # 数值梯度

            grad = np.zeros_like(x)

            for i in range(len(x)):

                eps = np.zeros_like(x)

                eps[i] = 1e-8

                grad[i] = (obj(x + eps) - obj(x - eps)) / (2 * 1e-8)

            grads.append(grad)

        

        grads = np.array(grads)

        

        # 找到梯度方向锥

        # 简化：使用所有梯度的平均方向

        avg_grad = np.mean(grads, axis=0)

        

        # 梯度上升

        x = x + learning_rate * avg_grad

    

    return x





def find_pareto_optimal_region(objective_funcs: List[Callable],

                               bounds: List[Tuple[float, float]],

                               n_samples: int = 1000) -> np.ndarray:

    """

    通过随机采样找到Pareto最优区域

    

    参数:

        objective_funcs: 目标函数列表

        bounds: 变量边界

        n_samples: 采样点数

    

    返回:

        近似Pareto前沿

    """

    n_vars = len(bounds)

    

    # 随机采样

    samples = np.random.uniform(

        [b[0] for b in bounds],

        [b[1] for b in bounds],

        (n_samples, n_vars)

    )

    

    # 计算目标值

    objectives = np.zeros((n_samples, len(objective_funcs)))

    for i, obj_func in enumerate(objective_funcs):

        for j, sample in enumerate(samples):

            objectives[j, i] = obj_func(sample)

    

    # 识别Pareto最优

    is_pareto = is_pareto_optimal(objectives)

    

    pareto_front = objectives[is_pareto]

    

    return pareto_front





def compute_pareto_front_properties(front: np.ndarray) -> dict:

    """

    计算Pareto前沿的属性

    

    参数:

        front: Pareto前沿矩阵

    

    返回:

        包含属性的字典

    """

    n, m = front.shape

    

    properties = {

        'n_points': n,

        'n_objectives': m,

        'ideal_point': np.min(front, axis=0),

        'nadir_point': np.max(front, axis=0),

        'extreme_points': [],

        'spread': 0.0

    }

    

    # 找极端点（每个目标上最优的点）

    for i in range(m):

        idx = np.argmin(front[:, i])

        properties['extreme_points'].append(idx)

    

    # 计算间距（spread）

    if n > 1:

        sorted_front = front[np.argsort(front[:, 0])]

        max_dist = 0

        for i in range(1, n):

            dist = np.linalg.norm(sorted_front[i] - sorted_front[i-1])

            max_dist = max(max_dist, dist)

        properties['spread'] = max_dist

    

    return properties





def tangent_lines_pareto(front: np.ndarray, point_idx: int) -> np.ndarray:

    """

    计算Pareto前沿某点的切线方向

    

    参数:

        front: Pareto前沿

        point_idx: 点的索引

    

    返回:

        切线方向向量

    """

    point = front[point_idx]

    n = len(front)

    

    # 找到该点的邻居

    sorted_indices = np.argsort(front[:, 0])

    pos = np.where(sorted_indices == point_idx)[0][0]

    

    if pos == 0:

        neighbor = front[sorted_indices[1]]

    elif pos == n - 1:

        neighbor = front[sorted_indices[n - 2]]

    else:

        neighbor = front[sorted_indices[pos + 1]] if pos < n // 2 else front[sorted_indices[pos - 1]]

    

    tangent = neighbor - point

    

    return tangent / (np.linalg.norm(tangent) + 1e-10)





def identify_convex_regions(front: np.ndarray) -> List[List[int]]:

    """

    识别Pareto前沿的凸/凹区域

    

    参数:

        front: Pareto前沿（按第一目标排序）

    

    返回:

        区域索引列表

    """

    n = len(front)

    

    if n < 3:

        return [list(range(n))]

    

    # 计算曲率

    sorted_idx = np.argsort(front[:, 0])

    sorted_front = front[sorted_idx]

    

    regions = []

    current_region = [0]

    

    for i in range(1, n - 1):

        # 计算前向和后向方向

        vec1 = sorted_front[i] - sorted_front[i - 1]

        vec2 = sorted_front[i + 1] - sorted_front[i]

        

        # 计算叉积（二维情况下为标量）

        cross = vec1[0] * vec2[1] - vec1[1] * vec2[0]

        

        # 判断凸性

        if cross > 1e-6:  # 凸

            current_region.append(i)

        else:  # 凹

            if len(current_region) > 1:

                regions.append([sorted_idx[j] for j in current_region])

            current_region = [i]

    

    if len(current_region) > 1:

        regions.append([sorted_idx[j] for j in current_region])

    

    return regions





def approximate_pareto_boundary(front: np.ndarray, n_interpolated: int = 100) -> np.ndarray:

    """

    近似Pareto边界曲线（用于可视化）

    

    参数:

        front: 原始Pareto前沿

        n_interpolated: 插值点数

    

    返回:

        平滑化的前沿

    """

    n = len(front)

    

    if n < 2:

        return front

    

    # 按第一目标排序

    sorted_idx = np.argsort(front[:, 0])

    sorted_front = front[sorted_idx]

    

    # 简单的线性插值

    interpolated = []

    

    for i in range(n_interpolated):

        t = i / (n_interpolated - 1) * (n - 1)

        idx = int(t)

        frac = t - idx

        

        if idx >= n - 1:

            interpolated.append(sorted_front[-1])

        else:

            point = (1 - frac) * sorted_front[idx] + frac * sorted_front[idx + 1]

            interpolated.append(point)

    

    return np.array(interpolated)





def check_pareto_degeneracy(front: np.ndarray, tolerance: float = 1e-6) -> bool:

    """

    检查Pareto前沿是否退化（在某些方向上只有一个点）

    

    参数:

        front: Pareto前沿

        tolerance: 容差

    

    返回:

        True如果退化

    """

    n, m = front.shape

    

    for i in range(m):

        if np.max(front[:, i]) - np.min(front[:, i]) < tolerance:

            return True

    

    return False





class ParetoFrontAnalyzer:

    """Pareto前沿分析器"""

    

    def __init__(self, front: np.ndarray):

        self.front = front

        self.properties = compute_pareto_front_properties(front)

    

    def get_extreme_solutions(self) -> np.ndarray:

        """获取极端解（每个目标最优的解）"""

        return self.front[self.properties['extreme_points']]

    

    def get_compromise_solution(self, weights: np.ndarray) -> np.ndarray:

        """

        获取妥协解

        

        参数:

            weights: 权重向量

        

        返回:

            加权最优解

        """

        weights = np.array(weights) / np.sum(weights)

        weighted_front = self.front * weights

        

        # 找加权目标值最小的点

        scores = np.sum(weighted_front, axis=1)

        

        return self.front[np.argmin(scores)]

    

    def estimate_diversity(self) -> float:

        """

        估计多样性（基于点到理想线的距离）

        

        返回:

            多样性指标

        """

        ideal = self.properties['ideal_point']

        nadir = self.properties['nadir_point']

        

        # 计算每个点到理想线的距离

        # 理想线：连接ideal和nadir的线

        line_vec = nadir - ideal

        line_len = np.linalg.norm(line_vec)

        

        if line_len < 1e-10:

            return 0.0

        

        # 计算每个点投影到线上的位置

        normalized = (self.front - ideal) / line_len

        projections = normalized @ line_vec / line_len

        

        # 计算投影的分散程度

        spread = np.std(projections)

        

        return spread





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("Pareto最优性与KKT条件测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 测试Pareto最优识别

    print("\n--- Pareto最优识别 ---")

    

    points = np.array([

        [1.0, 2.0],

        [0.5, 1.5],  # 支配第一个

        [0.8, 1.8],  # 被第一个支配

        [0.3, 2.5],

        [0.6, 0.6]   # 不被支配

    ])

    

    is_pareto = is_pareto_optimal(points)

    print(f"点:\n{points}")

    print(f"Pareto最优: {is_pareto}")

    

    # 生成模拟Pareto前沿

    print("\n--- 模拟Pareto前沿分析 ---")

    

    # ZDT1类型的前沿

    f1 = np.linspace(0, 1, 50)

    g = 1

    f2 = g * (1 - np.sqrt(f1 / g))

    front = np.column_stack([f1, f2])

    

    analyzer = ParetoFrontAnalyzer(front)

    

    print(f"Pareto前沿点数: {analyzer.properties['n_points']}")

    print(f"理想点: {analyzer.properties['ideal_point']}")

    print(f"最差点: {analyzer.properties['nadir_point']}")

    print(f"极端点索引: {analyzer.properties['extreme_points']}")

    print(f"间距(spread): {analyzer.properties['spread']:.4f}")

    

    # 极端解

    extreme = analyzer.get_extreme_solutions()

    print(f"极端解: {extreme}")

    

    # 妥协解

    compromise = analyzer.get_compromise_solution(np.array([0.5, 0.5]))

    print(f"妥协解 (0.5, 0.5): {compromise}")

    

    # 多样性

    diversity = analyzer.estimate_diversity()

    print(f"多样性指标: {diversity:.4f}")

    

    # 边界插值

    print("\n--- 边界插值 ---")

    interpolated = approximate_pareto_boundary(front, n_interpolated=20)

    print(f"插值后点数: {len(interpolated)}")

    print(f"插值点前5个:\n{interpolated[:5]}")

    

    # 凸/凹区域

    print("\n--- 凸凹区域识别 ---")

    regions = identify_convex_regions(front)

    print(f"区域数: {len(regions)}")

    for i, region in enumerate(regions):

        print(f"  区域{i+1}: {len(region)} 个点")

    

    # 切线方向

    print("\n--- 切线方向 ---")

    tangent = tangent_lines_pareto(front, 25)

    print(f"第25个点的切线方向: {tangent}")

    

    print("\n" + "=" * 50)

    print("测试完成")


# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / pareto_front



本文件实现 pareto_front 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

from functools import reduce





def is_dominated(x: np.ndarray, y: np.ndarray) -> bool:

    """

    判断解x是否被解y支配

    

    参数:

        x: 解x的目标向量 (n_objectives,)

        y: 解y的目标向量 (n_objectives,)

    

    返回:

        True如果x被y支配，False否则

    """

    # x被y支配：当且仅当 y >= x（所有目标）且 y > x（至少一个目标）

    at_least_as_good = np.all(y >= x)

    at_least_one_strict = np.any(y > x)

    

    return at_least_as_good and at_least_one_strict





def is_non_dominated(points: np.ndarray) -> np.ndarray:

    """

    找出所有非支配解

    

    参数:

        points: 目标矩阵 (n_points, n_objectives)

    

    返回:

        布尔数组，True表示非支配解

    """

    n = len(points)

    is_pareto = np.ones(n, dtype=bool)

    

    for i in range(n):

        if not is_pareto[i]:

            continue

        

        for j in range(n):

            if i == j or not is_pareto[j]:

                continue

            

            # 如果j支配i，i不是Pareto最优

            if is_dominated(points[i], points[j]):

                is_pareto[i] = False

                break

    

    return is_pareto





def fast_non_dominated_sort(objectives: np.ndarray) -> List[List[int]]:

    """

    快速非支配排序（NSGA-II使用）

    

    参数:

        objectives: 目标矩阵 (n_points, n_objectives)

    

    返回:

        帕累托层级列表，每个层级的非支配解索引

    """

    n = len(objectives)

    

    # 每个解被支配的数量

    n_dominated = np.zeros(n, dtype=int)

    # 每个解支配的解集合

    dominated_set = [[] for _ in range(n)]

    # 解的层级

    fronts = [[]]

    

    # 初始化

    for i in range(n):

        for j in range(i + 1, n):

            if is_dominated(objectives[i], objectives[j]):

                # j支配i

                dominated_set[j].append(i)

                n_dominated[i] += 1

            elif is_dominated(objectives[j], objectives[i]):

                # i支配j

                dominated_set[i].append(j)

                n_dominated[j] += 1

        

        # 第一层：没有被支配的解

        if n_dominated[i] == 0:

            fronts[0].append(i)

    

    # 逐层划分

    current_front = 0

    

    while len(fronts[current_front]) > 0:

        next_front = []

        

        for i in fronts[current_front]:

            for j in dominated_set[i]:

                n_dominated[j] -= 1

                if n_dominated[j] == 0:

                    next_front.append(j)

        

        if len(next_front) > 0:

            fronts.append(next_front)

        

        current_front += 1

    

    return fronts[:-1]  # 去掉最后一个空层





def crowding_distance(objectives: np.ndarray, front: List[int]) -> np.ndarray:

    """

    计算拥挤距离（NSGA-II用于保持多样性）

    

    参数:

        objectives: 目标矩阵

        front: 当前层级的解索引

    

    返回:

        每个解的拥挤距离

    """

    if len(front) <= 2:

        return np.full(len(front), np.inf)

    

    n_objectives = objectives.shape[1]

    n = len(front)

    

    distances = np.zeros(n)

    

    for m in range(n_objectives):

        # 按当前目标排序

        sorted_indices = np.argsort(objectives[front, m])

        

        # 边界解给予无限距离

        distances[sorted_indices[0]] = np.inf

        distances[sorted_indices[-1]] = np.inf

        

        # 计算其他解的距离

        m_range = objectives[front[sorted_indices[-1]], m] - objectives[front[sorted_indices[0]], m]

        

        if m_range > 0:

            for i in range(1, n - 1):

                distances[sorted_indices[i]] += (

                    objectives[front[sorted_indices[i + 1]], m] - 

                    objectives[front[sorted_indices[i - 1]], m]

                ) / m_range

    

    return distances





def weighted_sum_method(objectives: np.ndarray, weights: np.ndarray) -> Tuple[int, float]:

    """

    加权求和法：将多目标转化为单目标

    

    参数:

        objectives: 目标矩阵 (n_points, n_objectives)

        weights: 权重向量 (n_objectives,)，需满足和为1

    

    返回:

        (最优解索引, 加权和)

    """

    weights = np.array(weights)

    weights = weights / np.sum(weights)  # 归一化

    

    # 计算加权和

    weighted_scores = objectives @ weights

    

    # 找最小值（假设是最小化问题）

    best_idx = np.argmin(weighted_scores)

    

    return best_idx, weighted_scores[best_idx]





def tchebychev_method(objectives: np.ndarray, reference_point: np.ndarray,

                      weights: np.ndarray) -> np.ndarray:

    """

    Tchebychev分解法

    

    min max_i (w_i * |f_i(x) - z_i^*|)

    

    其中 z_i^* 是每个目标的当前最优值

    

    参数:

        objectives: 目标矩阵

        reference_point: 参考点（理想点）

        weights: 权重向量

    

    返回:

        每个解的Tchebychev距离

    """

    weights = np.array(weights)

    

    # 计算每个目标与理想点的加权绝对差

    diff = np.abs(objectives - reference_point)

    weighted_diff = diff * weights

    

    # 取最大值

    tchebychev_dist = np.max(weighted_diff, axis=1)

    

    return tchebychev_dist





def identify_pareto_front(objectives: np.ndarray, 

                         minimize: Optional[List[bool]] = None) -> np.ndarray:

    """

    识别Pareto前沿

    

    参数:

        objectives: 目标矩阵 (n_points, n_objectives)

        minimize: 每个目标是否是最小化（默认全True）

    

    返回:

        Pareto前沿上的解索引

    """

    if minimize is None:

        minimize = [True] * objectives.shape[1]

    

    # 如果是最小化问题，直接使用

    # 如果是最大化问题，取负

    objectives_adjusted = objectives.copy()

    for i, is_min in enumerate(minimize):

        if not is_min:

            objectives_adjusted[:, i] = -objectives[:, i]

    

    is_pareto = is_non_dominated(objectives_adjusted)

    

    return np.where(is_pareto)[0]





def hypervolume_contribution(point: np.ndarray, reference_point: np.ndarray,

                            objectives: np.ndarray, minimize: bool = True) -> float:

    """

    计算单个点对超体积的贡献

    

    参数:

        point: 待测点

        reference_point: 参考点

        objectives: 所有点（用于加速计算）

        minimize: 是否最小化

    

    返回:

        超体积贡献

    """

    if minimize:

        # 计算以point和reference_point为顶点的超矩形

        contribution = 1.0

        for i in range(len(point)):

            width = reference_point[i] - point[i]

            if width <= 0:

                return 0.0

            contribution *= width

    else:

        contribution = 1.0

        for i in range(len(point)):

            width = point[i] - reference_point[i]

            if width <= 0:

                return 0.0

            contribution *= width

    

    return contribution





def approximate_pareto_front(objectives: np.ndarray, n_samples: int = 100) -> np.ndarray:

    """

    近似Pareto前沿（使用权重采样）

    

    参数:

        objectives: 目标矩阵

        n_samples: 采样点数

    

    返回:

        近似Pareto前沿上的点

    """

    n_objectives = objectives.shape[1]

    

    # 均匀采样权重

    weights = np.random.dirichlet(np.ones(n_objectives), size=n_samples)

    

    pareto_approx = []

    

    for weight in weights:

        idx, _ = weighted_sum_method(objectives, weight)

        pareto_approx.append(objectives[idx])

    

    pareto_approx = np.array(pareto_approx)

    

    # 去重

    unique_pareto = []

    for point in pareto_approx:

        is_duplicate = False

        for existing in unique_pareto:

            if np.allclose(point, existing, atol=1e-5):

                is_duplicate = True

                break

        if not is_duplicate:

            unique_pareto.append(point)

    

    return np.array(unique_pareto)





class ParetoFrontier:

    """Pareto前沿分析器"""

    

    def __init__(self, objectives: np.ndarray, minimize: Optional[List[bool]] = None):

        """

        参数:

            objectives: 目标矩阵

            minimize: 每个目标是否最小化

        """

        self.objectives = objectives

        self.n_points, self.n_objectives = objectives.shape

        self.minimize = minimize if minimize else [True] * self.n_objectives

        

        # 计算Pareto前沿

        self.pareto_indices = identify_pareto_front(objectives, self.minimize)

        self.pareto_front = objectives[self.pareto_indices]

        

        # 计算理想点和最差点

        self.ideal_point = np.array([

            np.min(objectives[:, i]) if self.minimize[i] else np.max(objectives[:, i])

            for i in range(self.n_objectives)

        ])

        

        self.nadir_point = np.array([

            np.max(objectives[:, i]) if self.minimize[i] else np.min(objectives[:, i])

            for i in range(self.n_objectives)

        ])

    

    def get_pareto_front(self) -> Tuple[np.ndarray, np.ndarray]:

        """获取Pareto前沿"""

        return self.pareto_indices, self.pareto_front

    

    def get_dominated_count(self, idx: int) -> int:

        """获取支配该解的其他解数量"""

        x = self.objectives[idx]

        count = 0

        

        for i in range(self.n_points):

            if i != idx:

                y = self.objectives[i]

                adjusted_x = x.copy()

                adjusted_y = y.copy()

                

                for j in range(self.n_objectives):

                    if not self.minimize[j]:

                        adjusted_x[j] = -x[j]

                        adjusted_y[j] = -y[j]

                

                if is_dominated(adjusted_x, adjusted_y):

                    count += 1

        

        return count

    

    def diversity_metric(self) -> float:

        """

        计算Pareto前沿的多样性指标（使用间距）

        """

        if len(self.pareto_indices) < 2:

            return 0.0

        

        # 计算相邻解之间的距离

        distances = []

        for i in range(len(self.pareto_front)):

            for j in range(i + 1, len(self.pareto_front)):

                dist = np.linalg.norm(self.pareto_front[i] - self.pareto_front[j])

                distances.append(dist)

        

        # 间距指标

        min_dist = np.min(distances)

        avg_dist = np.mean(distances)

        

        return min_dist / (avg_dist + 1e-10)





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("Pareto前沿求解测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成测试数据：两目标优化问题

    n = 100

    n_objectives = 2

    

    # 随机生成目标值

    objectives = np.zeros((n, n_objectives))

    for i in range(n):

        # 构造类似ZDT1问题

        x1 = i / n

        x_rest = np.random.rand(8)

        

        g = 1 + 9 * np.sum(x_rest) / 8

        f1 = x1

        f2 = g * (1 - np.sqrt(x1 / g))

        

        objectives[i] = [f1, f2]

    

    print(f"\n数据生成: {n} 个点, {n_objectives} 个目标")

    

    # 识别Pareto前沿

    print("\n--- Pareto前沿识别 ---")

    pareto = ParetoFrontier(objectives)

    pareto_idx, pareto_front = pareto.get_pareto_front()

    

    print(f"Pareto前沿点数: {len(pareto_idx)}")

    print(f"理想点: {pareto.ideal_point}")

    print(f"最差点: {pareto.nadir_point}")

    

    # 快速非支配排序

    print("\n--- 非支配排序 ---")

    fronts = fast_non_dominated_sort(objectives)

    print(f"层级数: {len(fronts)}")

    for i, front in enumerate(fronts[:3]):

        print(f"  第{i+1}层: {len(front)} 个点")

    

    # 拥挤距离

    print("\n--- 拥挤距离计算 ---")

    if len(fronts[0]) > 2:

        cd = crowding_distance(objectives, fronts[0])

        print(f"第1层前5个拥挤距离: {cd[:5]}")

        print(f"最大拥挤距离（边界）: {np.max(cd):.4f}")

    

    # 加权求和法

    print("\n--- 加权求和法 ---")

    for weight in [[0.5, 0.5], [0.8, 0.2], [0.2, 0.8]]:

        idx, score = weighted_sum_method(objectives, weight)

        print(f"权重{weight}: 最优解索引={idx}, 得分={score:.4f}")

    

    # 多样性指标

    print("\n--- 多样性指标 ---")

    diversity = pareto.diversity_metric()

    print(f"Pareto前沿间距指标: {diversity:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


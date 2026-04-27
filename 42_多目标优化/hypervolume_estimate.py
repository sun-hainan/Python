# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / hypervolume_estimate



本文件实现 hypervolume_estimate 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional

from scipy.spatial import ConvexHull

from scipy.stats import qmc





def monte_carlo_hypervolume(points: np.ndarray, reference_point: np.ndarray,

                            n_samples: int = 10000,

                            bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> float:

    """

    蒙特卡洛估计超体积

    

    参数:

        points: Pareto前沿点 (n, d)

        reference_point: 参考点 (d,)

        n_samples: 采样数量

        bounds: (lower, upper) 边界

    

    返回:

        估计的超体积

    """

    n, d = points.shape

    

    # 确定采样边界

    if bounds is None:

        # 使用参考点和最小目标值

        lower = np.min(points, axis=0)

        upper = reference_point.copy()

    else:

        lower, upper = bounds

    

    # 生成均匀采样点

    samples = np.random.uniform(lower, upper, (n_samples, d))

    

    # 计算被支配的点比例

    dominated_count = 0

    

    for sample in samples:

        for point in points:

            # 检查是否被point支配

            if np.all(point <= sample) and np.any(point < sample):

                dominated_count += 1

                break

    

    # 超体积 = 总体积 * 被支配比例

    total_volume = np.prod(upper - lower)

    hv = total_volume * dominated_count / n_samples

    

    return hv





def quasi_monte_carlo_hypervolume(points: np.ndarray, reference_point: np.ndarray,

                                  n_samples: int = 10000) -> float:

    """

    拟蒙特卡洛估计（使用低差异序列）

    

    更均匀的采样，通常比纯蒙特卡洛方差更小

    """

    n, d = points.shape

    

    # 生成Halton序列

    sampler = qmc.Halton(d=d, scramble=True)

    samples = sampler.random(n=n_samples)

    

    # 缩放到边界

    lower = np.min(points, axis=0)

    upper = reference_point

    

    samples = lower + samples * (upper - lower)

    

    # 计算被支配比例

    dominated_count = 0

    for sample in samples:

        for point in points:

            if np.all(point <= sample) and np.any(point < sample):

                dominated_count += 1

                break

    

    total_volume = np.prod(upper - lower)

    hv = total_volume * dominated_count / n_samples

    

    return hv





def grid_hypervolume(points: np.ndarray, reference_point: np.ndarray,

                    n_bins: int = 50) -> float:

    """

    基于网格的超体积估计

    

    将目标空间划分为网格，计算被覆盖的格子数

    

    参数:

        points: Pareto前沿点

        reference_point: 参考点

        n_bins: 每个维度的格数

    

    返回:

        估计的超体积

    """

    n, d = points.shape

    

    # 计算边界

    lower = np.min(points, axis=0)

    upper = reference_point

    

    # 创建网格

    grid_shape = [n_bins] * d

    hypergrid = np.zeros(grid_shape, dtype=bool)

    

    # 每个维度的大小

    bin_sizes = (upper - lower) / n_bins

    

    # 标记被覆盖的格子

    for point in points:

        indices = ((point - lower) / bin_sizes).astype(int)

        indices = np.clip(indices, 0, n_bins - 1)

        

        hypergrid[tuple(indices)] = True

        

        # 标记所有在point左下方的格子

        for i in range(d):

            for val in range(indices[i] + 1):

                idx = list(indices)

                idx[i] = val

                hypergrid[tuple(idx)] = True

    

    # 计算体积

    cell_volume = np.prod(bin_sizes)

    covered_cells = np.sum(hypergrid)

    

    return cell_volume * covered_cells





def sweepline_hypervolume_2d(points: np.ndarray, reference_point: np.ndarray) -> float:

    """

    二维扫描线算法（精确）

    

    扫描线从左到右，计算每个垂直条带的面积

    """

    # 按x坐标排序

    sorted_points = points[np.argsort(points[:, 0])]

    

    hv = 0.0

    current_height = reference_point[1]

    

    for point in sorted_points:

        x, y = point

        

        if x >= reference_point[0] or y >= reference_point[1]:

            continue

        

        width = reference_point[0] - x

        height = current_height - y

        

        hv += width * height

        

        current_height = min(current_height, y)

    

    return hv





def inclusion_exclusion_hypervolume(points: np.ndarray, reference_point: np.ndarray) -> float:

    """

    容斥原理计算精确超体积（低维）

    

    适用于2-3维

    """

    n, d = points.shape

    

    if d == 2:

        return sweepline_hypervolume_2d(points, reference_point)

    

    if d == 3:

        # 三维：用扫描平面法

        return hypervolume_3d_exact(points, reference_point)

    

    # 高维回退到蒙特卡洛

    return monte_carlo_hypervolume(points, reference_point)





def hypervolume_3d_exact(points: np.ndarray, reference_point: np.ndarray) -> float:

    """

    三维精确超体积计算

    """

    # 过滤

    valid = (points[:, 0] <= reference_point[0]) & \

            (points[:, 1] <= reference_point[1]) & \

            (points[:, 2] <= reference_point[2])

    

    points = points[valid]

    

    if len(points) == 0:

        return 0.0

    

    # 按x排序

    sorted_idx = np.argsort(points[:, 0])

    sorted_points = points[sorted_idx]

    

    hv = 0.0

    prev_x = reference_point[0]

    

    for i, point in enumerate(sorted_points):

        x = point[0]

        

        if i == len(sorted_points) - 1:

            next_x = 0

        else:

            next_x = sorted_points[i + 1, 0]

        

        # 当前层的点（y-z平面）

        layer_points = sorted_points[i:, 1:]

        

        if len(layer_points) < 3:

            # 直接计算

            for p in layer_points:

                hv += (reference_point[1] - p[0]) * (reference_point[2] - p[1])

        else:

            # 使用2D扫描线

            hv_slice = sweepline_hypervolume_2d(layer_points, 

                                               reference_point[1:])

            hv += hv_slice * (prev_x - x)

        

        prev_x = x

    

    return hv





def layered_sampling_hypervolume(points: np.ndarray, reference_point: np.ndarray,

                                n_layers: int = 10,

                                samples_per_layer: int = 1000) -> float:

    """

    分层采样超体积估计

    

    将目标空间分层，在每层独立采样

    提高估计精度

    """

    n, d = points.shape

    

    lower = np.min(points, axis=0)

    upper = reference_point

    

    # 创建层

    layer_boundaries = np.linspace(lower[0], upper[0], n_layers + 1)

    

    total_hv = 0.0

    

    for i in range(n_layers):

        layer_lower = np.array([layer_boundaries[i]] + list(lower[1:]))

        layer_upper = np.array([layer_boundaries[i + 1]] + list(upper[1:]))

        

        # 该层内的Pareto点

        layer_points = points[

            (points[:, 0] >= layer_boundaries[i]) & 

            (points[:, 0] < layer_boundaries[i + 1])

        ]

        

        if len(layer_points) == 0:

            continue

        

        # 在该层内采样

        layer_samples = np.random.uniform(layer_lower, layer_upper, 

                                        (samples_per_layer, d))

        

        # 计算被支配的比例

        dominated = 0

        for sample in layer_samples:

            for point in layer_points:

                if np.all(point <= sample) and np.any(point < sample):

                    dominated += 1

                    break

        

        layer_volume = np.prod(layer_upper - layer_lower)

        layer_hv = layer_volume * dominated / samples_per_layer

        

        total_hv += layer_hv

    

    return total_hv





def adaptive_hypervolume_estimate(points: np.ndarray, reference_point: np.ndarray,

                                tolerance: float = 0.01,

                                max_samples: int = 50000) -> Tuple[float, int]:

    """

    自适应超体积估计

    

    自动增加采样直到收敛

    

    返回:

        (估计值, 实际采样数)

    """

    n, d = points.shape

    

    lower = np.min(points, axis=0)

    upper = reference_point

    total_volume = np.prod(upper - lower)

    

    # 初始采样

    n_samples = 1000

    samples = np.random.uniform(lower, upper, (n_samples, d))

    

    dominated_count = 0

    for sample in samples:

        for point in points:

            if np.all(point <= sample) and np.any(point < sample):

                dominated_count += 1

                break

    

    current_hv = total_volume * dominated_count / n_samples

    prev_hv = 0.0

    

    # 增量采样

    while n_samples < max_samples and abs(current_hv - prev_hv) > tolerance * current_hv:

        prev_hv = current_hv

        

        # 添加更多采样点

        additional_samples = min(1000, max_samples - n_samples)

        new_samples = np.random.uniform(lower, upper, (additional_samples, d))

        

        for sample in new_samples:

            for point in points:

                if np.all(point <= sample) and np.any(point < sample):

                    dominated_count += 1

                    break

        

        n_samples += additional_samples

        current_hv = total_volume * dominated_count / n_samples

    

    return current_hv, n_samples





class HypervolumeEstimator:

    """超体积估计器"""

    

    def __init__(self, reference_point: np.ndarray, method: str = 'quasi_mc'):

        """

        参数:

            reference_point: 参考点

            method: 估计方法 ('mc', 'quasi_mc', 'grid', 'adaptive')

        """

        self.reference_point = reference_point

        self.method = method

    

    def estimate(self, points: np.ndarray) -> float:

        """估计超体积"""

        if self.method == 'mc':

            return monte_carlo_hypervolume(points, self.reference_point)

        elif self.method == 'quasi_mc':

            return quasi_monte_carlo_hypervolume(points, self.reference_point)

        elif self.method == 'grid':

            return grid_hypervolume(points, self.reference_point)

        elif self.method == 'adaptive':

            hv, _ = adaptive_hypervolume_estimate(points, self.reference_point)

            return hv

        else:

            return monte_carlo_hypervolume(points, self.reference_point)

    

    def compute_contributions(self, points: np.ndarray) -> np.ndarray:

        """

        计算每个点的超体积贡献

        

        返回:

            每个点的贡献值数组

        """

        n = len(points)

        contributions = np.zeros(n)

        

        full_hv = self.estimate(points)

        

        for i in range(n):

            reduced_points = np.delete(points, i, axis=0)

            

            if len(reduced_points) == 0:

                contributions[i] = full_hv

            else:

                reduced_hv = self.estimate(reduced_points)

                contributions[i] = full_hv - reduced_hv

        

        return contributions





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("超体积估计方法测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 二维测试

    print("\n--- 二维超体积 ---")

    

    points_2d = np.array([

        [0.2, 0.9],

        [0.4, 0.7],

        [0.6, 0.5],

        [0.8, 0.3]

    ])

    

    ref_2d = np.array([1.0, 1.0])

    

    # 精确值

    exact_hv = sweepline_hypervolume_2d(points_2d, ref_2d)

    print(f"精确超体积: {exact_hv:.6f}")

    

    # 蒙特卡洛

    mc_hv = monte_carlo_hypervolume(points_2d, ref_2d, n_samples=50000)

    print(f"蒙特卡洛 (50k): {mc_hv:.6f}, 误差: {abs(mc_hv - exact_hv):.6f}")

    

    # 拟蒙特卡洛

    quasi_hv = quasi_monte_carlo_hypervolume(points_2d, ref_2d, n_samples=10000)

    print(f"拟蒙特卡洛 (10k): {quasi_hv:.6f}, 误差: {abs(quasi_hv - exact_hv):.6f}")

    

    # 网格法

    grid_hv = grid_hypervolume(points_2d, ref_2d, n_bins=100)

    print(f"网格法 (100 bins): {grid_hv:.6f}, 误差: {abs(grid_hv - exact_hv):.6f}")

    

    # 三维测试

    print("\n--- 三维超体积 ---")

    

    points_3d = np.array([

        [0.2, 0.8, 0.7],

        [0.4, 0.6, 0.5],

        [0.6, 0.4, 0.6],

        [0.8, 0.3, 0.4]

    ])

    

    ref_3d = np.array([1.0, 1.0, 1.0])

    

    # 精确

    exact_hv_3d = hypervolume_3d_exact(points_3d, ref_3d)

    print(f"精确超体积: {exact_hv_3d:.6f}")

    

    # 蒙特卡洛

    mc_hv_3d = monte_carlo_hypervolume(points_3d, ref_3d, n_samples=50000)

    print(f"蒙特卡洛 (50k): {mc_hv_3d:.6f}, 误差: {abs(mc_hv_3d - exact_hv_3d):.6f}")

    

    # 自适应

    adaptive_hv, n_samples = adaptive_hypervolume_estimate(points_3d, ref_3d)

    print(f"自适应 (收敛): {adaptive_hv:.6f}, 采样数: {n_samples}")

    

    # 贡献计算

    print("\n--- 超体积贡献 ---")

    estimator = HypervolumeEstimator(ref_2d, method='quasi_mc')

    contributions = estimator.compute_contributions(points_2d)

    

    print("各点贡献:")

    for i, (point, contrib) in enumerate(zip(points_2d, contributions)):

        print(f"  点{i}: {point}, 贡献: {contrib:.6f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


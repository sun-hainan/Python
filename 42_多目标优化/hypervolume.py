# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / hypervolume



本文件实现 hypervolume 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional

from scipy.spatial import ConvexHull





def hypervolume_2d(points: np.ndarray, reference_point: np.ndarray) -> float:

    """

    二维情况下的Hypervolume计算

    

    高效算法：按第一个目标排序后累加矩形面积

    

    参数:

        points: Pareto前沿点 (n, 2)

        reference_point: 参考点 (2,)

    

    返回:

        Hypervolume值

    """

    # 按第一个目标排序

    sorted_points = points[np.argsort(points[:, 0])]

    

    hv = 0.0

    prev_y = reference_point[1]

    

    for point in sorted_points:

        if point[0] >= reference_point[0] or point[1] >= reference_point[1]:

            continue

        

        # 矩形宽度

        width = reference_point[0] - point[0]

        

        # 矩形高度

        height = reference_point[1] - prev_y

        

        hv += width * height

        prev_y = min(prev_y, point[1])

    

    return hv





def hypervolume_2d_incremental(points: np.ndarray, reference_point: np.ndarray,

                               new_point: np.ndarray) -> Tuple[float, float]:

    """

    增量计算：添加新点后的hypervolume变化

    

    参数:

        points: 原Pareto前沿

        reference_point: 参考点

        new_point: 新增点

    

    返回:

        (新hypervolume, 新增贡献)

    """

    old_hv = hypervolume_2d(points, reference_point)

    

    # 加入新点，重新计算Pareto前沿

    new_points = np.vstack([points, new_point])

    # 过滤被支配的点

    is_pareto = np.ones(len(new_points), dtype=bool)

    for i in range(len(new_points)):

        for j in range(len(new_points)):

            if i != j and is_pareto[i]:

                # 如果j支配i

                if (new_points[j] <= new_points[i]).all() and (new_points[j] < new_points[i]).any():

                    is_pareto[i] = False

                    break

    

    filtered_points = new_points[is_pareto]

    new_hv = hypervolume_2d(filtered_points, reference_point)

    

    return new_hv, new_hv - old_hv





def hypervolume_nd(points: np.ndarray, reference_point: np.ndarray,

                   minimize: bool = True) -> float:

    """

    高维Hypervolume计算（穷举法，适用于小规模问题）

    

    参数:

        points: Pareto前沿 (n, d)

        reference_point: 参考点 (d,)

        minimize: 是否最小化

    

    返回:

        Hypervolume

    """

    n, d = points.shape

    

    # 过滤在参考点之外的点

    if minimize:

        valid = np.all(points <= reference_point, axis=1)

    else:

        valid = np.all(points >= reference_point, axis=1)

    

    points = points[valid]

    

    if len(points) == 0:

        return 0.0

    

    # 穷举计算（对于低维可行）

    # 分解为三角形（二维）或四面体（三维）

    

    if d == 2:

        return hypervolume_2d(points, reference_point)

    

    elif d == 3:

        # 三维：使用扫描线法

        return hypervolume_3d(points, reference_point)

    

    else:

        # 高维：使用蒙特卡洛近似

        return hypervolume_monte_carlo(points, reference_point, n_samples=10000)





def hypervolume_3d(points: np.ndarray, reference_point: np.ndarray) -> float:

    """

    三维Hypervolume计算

    

    使用扫描平面法：将体积分解为多个2D切片

    """

    # 过滤

    valid = (points[:, 0] <= reference_point[0]) & \

            (points[:, 1] <= reference_point[1]) & \

            (points[:, 2] <= reference_point[2])

    

    points = points[valid]

    

    if len(points) == 0:

        return 0.0

    

    # 按x坐标排序

    sorted_indices = np.argsort(points[:, 0])

    sorted_points = points[sorted_indices]

    

    hv = 0.0

    prev_x = reference_point[0]

    

    for i, point in enumerate(sorted_points):

        x = point[0]

        

        # 在x处计算2D hypervolume（y-z平面）

        if i == len(sorted_points) - 1:

            next_x = 0  # 或参考点x

        else:

            next_x = sorted_points[i + 1, 0]

        

        # 当前层的点（投影到y-z平面）

        layer_points = sorted_points[i:, 1:]

        

        # 计算当前层的贡献

        if len(layer_points) >= 3:

            # 使用凸包计算2D HV

            ref_yz = np.array([reference_point[1], reference_point[2]])

            hv_slice = hypervolume_2d(layer_points, ref_yz)

        else:

            # 直接计算

            hv_slice = 0

            for p in layer_points:

                hv_slice += (reference_point[1] - p[0]) * (reference_point[2] - p[1])

        

        # 乘以x方向的厚度

        dx = prev_x - x

        hv += hv_slice * dx

        prev_x = x

    

    return hv





def hypervolume_monte_carlo(points: np.ndarray, reference_point: np.ndarray,

                           n_samples: int = 10000, 

                           bounds: Optional[np.ndarray] = None) -> float:

    """

    蒙特卡洛近似计算高维Hypervolume

    

    参数:

        points: Pareto前沿

        reference_point: 参考点

        n_samples: 采样点数

        bounds: 搜索边界（如果不提供，使用参考点和原点）

    

    返回:

        近似HV

    """

    n, d = points.shape

    

    # 确定边界

    if bounds is None:

        lower_bounds = np.zeros(d)

        upper_bounds = reference_point.copy()

    else:

        lower_bounds, upper_bounds = bounds

    

    # 生成随机点

    samples = np.random.uniform(lower_bounds, upper_bounds, (n_samples, d))

    

    # 检查每个点是否被Pareto前沿支配

    dominated_count = 0

    

    for sample in samples:

        # 检查是否至少有一个Pareto点支配该样本

        for point in points:

            if np.all(point <= sample) and np.any(point < sample):

                dominated_count += 1

                break

    

    # HV = 总体积 * 被支配比例

    total_volume = np.prod(upper_bounds - lower_bounds)

    hv = total_volume * dominated_count / n_samples

    

    return hv





def hypervolume_contribution(point: np.ndarray, 

                             pareto_front: np.ndarray,

                             reference_point: np.ndarray) -> float:

    """

    计算单个点对整体hypervolume的贡献

    

    使用几何法：HV(整体) - HV(去除该点后的前沿)

    

    参数:

        point: 待测点

        pareto_front: 完整Pareto前沿

        reference_point: 参考点

    

    返回:

        贡献值

    """

    # 计算完整HV

    full_front = np.vstack([pareto_front, point])

    # 过滤非法点

    valid = np.all(full_front <= reference_point, axis=1)

    full_front = full_front[valid]

    

    full_hv = hypervolume_2d(full_front, reference_point) if full_front.shape[1] == 2 else \

              hypervolume_monte_carlo(full_front, reference_point)

    

    # 计算去除该点后的HV

    reduced_front = pareto_front.copy()

    # 移除该点

    reduced_front = reduced_front[np.any(reduced_front != point, axis=1)]

    valid = np.all(reduced_front <= reference_point, axis=1)

    reduced_front = reduced_front[valid]

    

    reduced_hv = hypervolume_2d(reduced_front, reference_point) if len(reduced_front) > 0 and reduced_front.shape[1] == 2 else \

                 (hypervolume_monte_carlo(reduced_front, reference_point) if len(reduced_front) > 0 else 0)

    

    return full_hv - reduced_hv





class HypervolumeIndicator:

    """Hypervolume指标计算器"""

    

    def __init__(self, reference_point: np.ndarray, minimize: bool = True):

        """

        参数:

            reference_point: 参考点

            minimize: 是否最小化问题

        """

        self.reference_point = reference_point

        self.minimize = minimize

        self.dimension = len(reference_point)

    

    def compute(self, points: np.ndarray) -> float:

        """计算Hypervolume"""

        return hypervolume_nd(points, self.reference_point, self.minimize)

    

    def compute_incremental(self, existing_front: np.ndarray, 

                            new_point: np.ndarray) -> Tuple[float, float]:

        """增量计算"""

        new_front = np.vstack([existing_front, new_point])

        

        # 重新识别Pareto前沿

        if self.minimize:

            valid = np.all(new_front <= self.reference_point, axis=1)

        else:

            valid = np.all(new_front >= self.reference_point, axis=1)

        

        new_front = new_front[valid]

        

        # 识别非支配解

        is_pareto = np.ones(len(new_front), dtype=bool)

        for i in range(len(new_front)):

            for j in range(len(new_front)):

                if i != j and is_pareto[i]:

                    if (new_front[j] <= new_front[i]).all() and (new_front[j] < new_front[i]).any():

                        is_pareto[i] = False

                        break

        

        pareto_front = new_front[is_pareto]

        

        old_hv = self.compute(existing_front)

        new_hv = self.compute(pareto_front)

        

        return new_hv, new_hv - old_hv

    

    def diversity(self, pareto_front: np.ndarray) -> float:

        """

        基于HV的多样性指标

        

        计算移除每个点后的HV减少量

        """

        contributions = []

        for i in range(len(pareto_front)):

            reduced = np.delete(pareto_front, i, axis=0)

            hv_reduced = self.compute(reduced)

            hv_full = self.compute(pareto_front)

            contributions.append(hv_full - hv_reduced)

        

        return np.std(contributions)





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("Hypervolume指标计算测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 测试二维问题

    print("\n--- 二维Hypervolume ---")

    

    # 生成一些Pareto最优解

    pareto_front = np.array([

        [0.2, 0.9],

        [0.4, 0.7],

        [0.6, 0.5],

        [0.8, 0.3],

        [0.95, 0.15]

    ])

    

    reference = np.array([1.0, 1.0])

    

    hv = hypervolume_2d(pareto_front, reference)

    print(f"Pareto前沿:\n{pareto_front}")

    print(f"参考点: {reference}")

    print(f"Hypervolume: {hv:.4f}")

    

    # 手动验证：覆盖的矩形面积

    manual_hv = 0

    prev_x = reference[0]

    for point in pareto_front[np.argsort(pareto_front[:, 0])]:

        manual_hv += (prev_x - point[0]) * (reference[1] - point[1])

        prev_x = point[0]

    print(f"手动计算HV: {manual_hv:.4f}")

    

    # 增量计算

    print("\n--- 增量计算 ---")

    new_point = np.array([0.5, 0.6])

    new_hv, contribution = hypervolume_2d_incremental(pareto_front, reference, new_point)

    print(f"新点: {new_point}")

    print(f"新增贡献: {contribution:.4f}")

    

    # 计算每个点的贡献

    print("\n--- 各点贡献 ---")

    for i, point in enumerate(pareto_front):

        contrib = hypervolume_contribution(point, pareto_front, reference)

        print(f"点{i}: {point}, 贡献: {contrib:.4f}")

    

    # 三维测试

    print("\n--- 三维Hypervolume ---")

    pareto_3d = np.array([

        [0.2, 0.8, 0.7],

        [0.4, 0.6, 0.5],

        [0.6, 0.4, 0.6],

        [0.8, 0.3, 0.4]

    ])

    ref_3d = np.array([1.0, 1.0, 1.0])

    

    hv_3d = hypervolume_3d(pareto_3d, ref_3d)

    print(f"三维HV: {hv_3d:.4f}")

    

    # 蒙特卡洛近似

    print("\n--- 蒙特卡洛近似 ---")

    hv_mc = hypervolume_monte_carlo(pareto_3d, ref_3d, n_samples=50000)

    print(f"蒙特卡洛HV (50k样本): {hv_mc:.4f}")

    

    # 指标计算器

    print("\n--- 指标计算器 ---")

    indicator = HypervolumeIndicator(reference, minimize=True)

    

    hv1 = indicator.compute(pareto_front)

    print(f"计算器HV: {hv1:.4f}")

    

    diversity = indicator.diversity(pareto_front)

    print(f"多样性指标: {diversity:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


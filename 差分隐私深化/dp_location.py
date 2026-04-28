# -*- coding: utf-8 -*-
"""
位置隐私保护模块 (dp_location.py)
====================================

算法原理
--------
本模块实现了基于差分隐私的位置隐私保护技术，主要包括：
1. 地理不可区分性 (Geo-Ind)：在地理空间中为真实位置添加满足差分隐私的噪声，
   使得攻击者无法区分相邻两个位置的发布结果。
2. 空间划分 (Spatial Partitioning)：将地理空间递归划分为网格或四叉树结构，
   在每个划分单元上独立应用差分隐私噪声。
3. 轨迹发布 (Trajectory Release)：对时序位置序列进行差分隐私扰动，
   在相邻时间点的位置变化上添加拉普拉斯噪声。
4. QuadTree 空间划分：基于四叉树递归细分地理空间，
   在不同层级节点上分别应用隐私预算，实现自适应精度的位置保护。

时间复杂度：O(n log n) ~ O(n^2)，取决于划分深度和数据规模
空间复杂度：O(n) ~ O(n log n)，用于存储划分结构和噪声

应用场景
--------
- 位置推荐系统中的用户隐私保护
- 交通数据分析与 GPS 轨迹发布
- 基于位置的服务 (LBS) 数据采集
- 智慧城市中的移动模式挖掘
"""

import math
import random
import sys
from typing import List, Tuple, Optional


# =============================================================================
# 工具函数：差分隐私噪声生成
# =============================================================================

def laplace_noise(scale: float) -> float:
    """
    生成服从拉普拉斯分布的噪声。

    参数:
        scale (float): 拉普拉斯分布的尺度参数 b，满足 mean=0, variance=2b^2。
                      在差分隐私中，scale = 1/epsilon（敏感度已归一化）。

    返回:
        float: 拉普拉斯噪声样本。
    """
    # 逆分布函数法（Inverse CDF method）生成拉普拉斯随机数
    uniform_u = random.random() - 0.5  # [-0.5, 0.5)
    noise = -scale * math.copysign(1.0, uniform_u) * math.log(1 - 2 * abs(uniform_u))
    return noise


def geometric_mechanism(count: int, epsilon: float) -> int:
    """
    几何机制（Geometric Mechanism）：用于发布非负整数的差分隐私扰动。

    参数:
        count (int): 需要扰动的非负计数，敏感度为 1。
        epsilon (float): 隐私预算 epsilon。

    返回:
        int: 扰动后的非负计数（若为负则截断为 0）。
    """
    # 概率 p = (e^epsilon - 1) / (e^epsilon + 1) 决定符号
    p = (math.exp(epsilon) - 1.0) / (math.exp(epsilon) + 1.0)
    sign = 1 if random.random() < 0.5 + p / 2 else -1
    # 几何分布采样：P(X = k) = (1 - q) * q^k, q = e^{-epsilon}
    q = math.exp(-epsilon)
    k = 0
    while random.random() < q:
        k += 1
    return max(0, count + sign * k)


# =============================================================================
# 1. 地理不可区分性 (Geo-Ind)
# =============================================================================

def geo_indistinguishable(location: Tuple[float, float],
                          epsilon: float,
                          radius: float = 0.01) -> Tuple[float, float]:
    """
    实现地理不可区分性 (Geographic Indistinguishability, Geo-Ind)。

    原理：在以真实位置为圆心、半径为 r 的圆内，任意两个点 l 和 l'
    的发布结果分布 D_l 和 D_{l'} 满足：对于任意输出 o，
    D_l(o) <= e^epsilon * D_{l'}(o)。

    这里采用径向极坐标噪声：在极坐标下对 (r, theta) 添加拉普拉斯噪声。

    参数:
        location (Tuple[float, float]): 真实位置 (latitude, longitude)。
        epsilon (float): 隐私预算 epsilon，控制隐私保护强度。
        radius (float): 噪声注入的最大半径（地理单位，与坐标系统相关）。

    返回:
        Tuple[float, float]: 扰动后的位置 (latitude, longitude)。
    """
    lat, lon = location
    # 将半径归一化：敏感度为 radius，拉普拉斯尺度 = radius / epsilon
    scale = radius / epsilon
    # 径向距离扰动：添加拉普拉斯噪声后取绝对值（距离非负）
    r_noise = abs(laplace_noise(scale))
    # 方向角扰动：添加均匀噪声
    theta_noise = random.uniform(-math.pi, math.pi)
    # 转换为笛卡尔偏移量（简化近似，适用于小范围）
    delta_lat = r_noise * math.cos(theta_noise)
    delta_lon = r_noise * math.sin(theta_noise) / math.cos(math.radians(lat))
    # 叠加噪声得到扰动位置
    noisy_lat = lat + delta_lat
    noisy_lon = lon + delta_lon
    return (noisy_lat, noisy_lon)


# =============================================================================
# 2. 空间网格划分 (Grid Spatial Partitioning)
# =============================================================================

class GridPartitioner:
    """
    空间网格划分器：将二维地理区域递归划分为等大小网格，
    在每个网格计数上独立应用差分隐私噪声。
    """

    def __init__(self,
                 lat_min: float, lat_max: float,
                 lon_min: float, lon_max: float,
                 grid_size: float,
                 epsilon: float):
        """
        初始化空间网格划分器。

        参数:
            lat_min, lat_max: 纬度范围 [min, max]。
            lon_min, lon_max: 经度范围 [min, max]。
            grid_size (float): 网格的地理跨度（度数）。
            epsilon (float): 总隐私预算，将均匀分配到每个网格。
        """
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.grid_size = grid_size
        self.epsilon = epsilon
        # 计算网格总数
        n_lat = math.ceil((lat_max - lat_min) / grid_size)
        n_lon = math.ceil((lon_max - lon_min) / grid_size)
        self.n_grids = n_lat * n_lon
        # 每个网格的隐私预算
        self.eps_per_grid = epsilon / self.n_grids

    def location_to_grid(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        将地理坐标映射到网格索引。

        参数:
            lat, lon: 地理坐标。

        返回:
            Tuple[int, int]: 网格行索引和列索引。
        """
        row = int((lat - self.lat_min) / self.grid_size)
        col = int((lon - self.lon_min) / self.grid_size)
        return (row, col)

    def grid_to_location(self, row: int, col: int) -> Tuple[float, float]:
        """
        将网格索引映射回网格中心坐标。

        参数:
            row, col: 网格索引。

        返回:
            Tuple[float, float]: 网格中心点的地理坐标。
        """
        center_lat = self.lat_min + (row + 0.5) * self.grid_size
        center_lon = self.lon_min + (col + 0.5) * self.grid_size
        return (center_lat, center_lon)

    def add_noise_to_count(self, count: int) -> int:
        """
        对计数添加几何机制噪声。

        参数:
            count (int): 原始计数。

        返回:
            int: 扰动后计数（保证非负）。
        """
        noisy = geometric_mechanism(count, self.eps_per_grid)
        return noisy

    def release_grid_counts(self, points: List[Tuple[float, float]]) -> dict:
        """
        发布带差分隐私噪声的网格热力图。

        参数:
            points (List[Tuple[float, float]]): 所有用户位置点列表。

        返回:
            dict: { (row, col): noisy_count } 扰动后的网格计数。
        """
        # 统计每个网格的真实计数
        grid_counts = {}
        for lat, lon in points:
            row, col = self.location_to_grid(lat, lon)
            grid_counts[(row, col)] = grid_counts.get((row, col), 0) + 1
        # 对每个网格计数添加噪声
        noisy_grids = {}
        for key, true_count in grid_counts.items():
            noisy_grids[key] = self.add_noise_to_count(true_count)
        return noisy_grids


# =============================================================================
# 3. 轨迹发布 (Trajectory Release)
# =============================================================================

def release_differential_trajectory(locations: List[Tuple[float, float]],
                                     epsilon: float,
                                     sens: float = 1.0) -> List[Tuple[float, float]]:
    """
    差分隐私轨迹发布：在相邻位置点的差异（位移向量）上添加拉普拉斯噪声。

    原理：轨迹由一系列位置点组成。将第一个位置直接发布，
    后续每个位置通过发布与前一个位置的偏移量来间接表示。
    对偏移量添加拉普拉斯噪声后重建轨迹。

    参数:
        locations (List[Tuple[float, float]]): 原始轨迹位置列表。
        epsilon (float): 隐私预算（分配给每个偏移量）。
        sens (float): 敏感度上界，即相邻轨迹中位置变化的最大距离。

    返回:
        List[Tuple[float, float]]: 扰动后的轨迹位置列表。
    """
    if not locations:
        return []
    noisy = [locations[0]]  # 第一个点直接保留（可添加独立噪声）
    for i in range(1, len(locations)):
        lat1, lon1 = noisy[-1]  # 上一个（扰动后的）位置
        lat2, lon2 = locations[i]  # 当前位置
        # 计算偏移量
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        # 对偏移量添加拉普拉斯噪声，敏感度为 sens
        noisy_delta_lat = delta_lat + laplace_noise(sens / epsilon)
        noisy_delta_lon = delta_lon + laplace_noise(sens / epsilon)
        # 重建当前位置
        noisy_lat = lat1 + noisy_delta_lat
        noisy_lon = lon1 + noisy_delta_lon
        noisy.append((noisy_lat, noisy_lon))
    return noisy


# =============================================================================
# 4. QuadTree 空间划分 (QuadTree Partitioning)
# =============================================================================

class QuadTreeNode:
    """
    四叉树节点：表示空间划分的一个矩形区域。
    """

    def __init__(self,
                 lat_min: float, lat_max: float,
                 lon_min: float, lon_max: float,
                 epsilon: float,
                 max_depth: int = 6,
                 min_count: int = 2):
        """
        初始化四叉树节点。

        参数:
            lat_min, lat_max: 节点区域的纬度边界。
            lon_min, lon_max: 节点区域的经度边界。
            epsilon (float): 该节点可用的隐私预算。
            max_depth (int): 最大递归深度，防止无限划分。
            min_count (int): 最小计数阈值，少于此计数则不再划分。
        """
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.epsilon = epsilon
        self.max_depth = max_depth
        self.min_count = min_count
        self.count = 0  # 落入该节点的位置点数量
        self.children = None  # 四个子节点 (NW, NE, SW, SE)
        self.is_leaf = True  # 是否为叶子节点

    @property
    def center_lat(self) -> float:
        """节点区域中心纬度。"""
        return (self.lat_min + self.lat_max) / 2.0

    @property
    def center_lon(self) -> float:
        """节点区域中心经度。"""
        return (self.lon_min + self.lon_max) / 2.0

    def insert(self, lat: float, lon: float, depth: int = 0) -> None:
        """
        将一个位置点插入四叉树（递归）。

        参数:
            lat, lon: 位置坐标。
            depth (int): 当前递归深度。
        """
        # 检查是否在节点区域内
        if not (self.lat_min <= lat <= self.lat_max and
                self.lon_min <= lon <= self.lon_max):
            return
        self.count += 1
        # 判断是否应该继续划分
        should_split = (
            self.is_leaf
            and depth < self.max_depth
            and self.count >= self.min_count * 4
        )
        if should_split:
            self._split(depth)

    def _split(self, depth: int) -> None:
        """
        将当前节点分裂为四个子节点（NW/NE/SW/SE）。
        """
        mid_lat = self.center_lat
        mid_lon = self.center_lon
        # 将当前计数重置为 0，后续子节点会重新计数
        self.count = 0
        self.is_leaf = False
        # 子节点预算为父节点预算的一半（可递归分配）
        child_eps = self.epsilon * 0.5
        self.children = [
            QuadTreeNode(self.lat_min, mid_lat, self.lon_min, mid_lon, child_eps,
                         self.max_depth, self.min_count),  # NW
            QuadTreeNode(self.lat_min, mid_lat, mid_lon, self.lon_max, child_eps,
                         self.max_depth, self.min_count),  # NE
            QuadTreeNode(mid_lat, self.lat_max, self.lon_min, mid_lon, child_eps,
                         self.max_depth, self.min_count),  # SW
            QuadTreeNode(mid_lat, self.lat_max, mid_lon, self.lon_max, child_eps,
                         self.max_depth, self.min_count),  # SE
        ]

    def add_noise_to_count(self) -> int:
        """
        对该节点的计数添加拉普拉斯噪声，并返回扰动后计数。

        返回:
            int: 扰动后计数（若为负则截断为 0）。
        """
        noisy_count = self.count + laplace_noise(1.0 / self.epsilon)
        return max(0, int(round(noisy_count)))

    def get_all_leaf_noisy_counts(self) -> List[Tuple[Tuple[float, float, float, float], int]]:
        """
        获取所有叶子节点的扰动后计数（差分隐私）。

        返回:
            List[ (bounds, noisy_count) ]：每个叶子节点的范围和扰动计数。
        """
        if self.is_leaf:
            noisy = self.add_noise_to_count()
            return [((self.lat_min, self.lat_max,
                      self.lon_min, self.lon_max), noisy)]
        results = []
        if self.children:
            for child in self.children:
                results.extend(child.get_all_leaf_noisy_counts())
        return results


class QuadTreePartitioner:
    """
    四叉树空间划分器：对地理空间建立四叉树索引，
    在每个叶子节点上应用差分隐私计数扰动。
    """

    def __init__(self,
                 lat_min: float, lat_max: float,
                 lon_min: float, lon_max: float,
                 epsilon: float,
                 max_depth: int = 6,
                 min_count: int = 2):
        """
        初始化四叉树划分器。

        参数:
            lat_min, lat_max: 纬度范围。
            lon_min, lon_max: 经度范围。
            epsilon (float): 总隐私预算。
            max_depth (int): 最大深度。
            min_count (int): 最小计数阈值。
        """
        self.root = QuadTreeNode(
            lat_min, lat_max, lon_min, lon_max,
            epsilon, max_depth, min_count
        )

    def build(self, points: List[Tuple[float, float]]) -> None:
        """
        从位置点列表构建四叉树。

        参数:
            points (List[Tuple[float, float]]): 位置点列表。
        """
        for lat, lon in points:
            self.root.insert(lat, lon, depth=0)

    def release(self) -> List[Tuple[Tuple[float, float, float, float], int]]:
        """
        发布带差分隐私扰动的四叉树叶子节点热力图。

        返回:
            List[ (bounds, noisy_count) ]：每个叶子节点的范围和扰动计数。
        """
        return self.root.get_all_leaf_noisy_counts()


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("位置隐私保护模块 测试")
    print("=" * 60)

    # 测试 1：地理不可区分性
    print("\n[测试1] 地理不可区分性 (Geo-Ind)")
    print("-" * 40)
    true_location = (31.2304, 121.4737)  # 上海
    print(f"真实位置: 纬度={true_location[0]}, 经度={true_location[1]}")
    for eps in [0.5, 1.0, 2.0]:
        noisy_location = geo_indistinguishable(true_location, epsilon=eps, radius=0.01)
        offset = math.sqrt(
            (noisy_location[0] - true_location[0])**2
            + (noisy_location[1] - true_location[1])**2
        )
        print(f"  epsilon={eps}: 扰动位置=({noisy_location[0]:.6f}, {noisy_location[1]:.6f}), "
              f"偏移量={offset:.6f}")

    # 测试 2：空间网格划分
    print("\n[测试2] 空间网格划分")
    print("-" * 40)
    # 生成模拟位置数据（上海市中心附近，范围 0.1度 x 0.1度）
    random.seed(42)
    sim_points = [
        (31.23 + random.uniform(-0.05, 0.05), 121.47 + random.uniform(-0.05, 0.05))
        for _ in range(200)
    ]
    grid_partitioner = GridPartitioner(
        lat_min=31.18, lat_max=31.28,
        lon_min=121.42, lon_max=121.52,
        grid_size=0.02,
        epsilon=1.0
    )
    noisy_grids = grid_partitioner.release_grid_counts(sim_points)
    print(f"模拟位置点数: {len(sim_points)}")
    print(f"网格总数: {grid_partitioner.n_grids}")
    print(f"有位置点的网格数: {len(noisy_grids)}")
    print("部分扰动结果（网格左上角坐标 -> 扰动计数）:")
    for (row, col), noisy_cnt in list(noisy_grids.items())[:5]:
        center = grid_partitioner.grid_to_location(row, col)
        print(f"  中心({center[0]:.4f}, {center[1]:.4f}): 扰动计数={noisy_cnt}")

    # 测试 3：轨迹发布
    print("\n[测试3] 轨迹发布")
    print("-" * 40)
    trajectory = [
        (31.2300, 121.4700),
        (31.2310, 121.4720),
        (31.2325, 121.4740),
        (31.2318, 121.4755),
        (31.2305, 121.4730),
        (31.2290, 121.4710),
    ]
    print(f"原始轨迹点数: {len(trajectory)}")
    noisy_traj = release_differential_trajectory(trajectory, epsilon=1.0, sens=0.01)
    print("原始轨迹 -> 扰动轨迹:")
    for orig, noisy in zip(trajectory, noisy_traj):
        delta = math.sqrt((noisy[0] - orig[0])**2 + (noisy[1] - orig[1])**2)
        print(f"  ({orig[0]:.4f}, {orig[1]:.4f}) -> ({noisy[0]:.4f}, {noisy[1]:.4f}), "
              f"偏移={delta:.6f}")

    # 测试 4：四叉树空间划分
    print("\n[测试4] QuadTree 空间划分")
    print("-" * 40)
    qt = QuadTreePartitioner(
        lat_min=31.18, lat_max=31.28,
        lon_min=121.42, lon_max=121.52,
        epsilon=1.0,
        max_depth=4,
        min_count=2
    )
    qt.build(sim_points)
    noisy_results = qt.release()
    print(f"叶子节点总数: {len(noisy_results)}")
    print("部分叶子节点结果（边界 -> 扰动计数）:")
    for bounds, noisy_cnt in noisy_results[:5]:
        print(f"  lat=[{bounds[0]:.4f}, {bounds[1]:.4f}], "
              f"lon=[{bounds[2]:.4f}, {bounds[3]:.4f}]: 扰动计数={noisy_cnt}")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

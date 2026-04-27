# -*- coding: utf-8 -*-

"""

算法实现：11_计算几何 / voronoi_diagram



本文件实现 voronoi_diagram 相关的算法功能。

"""



import math

from typing import List, Tuple, Dict



Point = Tuple[float, float]

Polygon = List[Point]





def euclidean_distance(p1: Point, p2: Point) -> float:

    """

    计算两点间的欧几里得距离

    

    Args:

        p1: 第一个点坐标 (x, y)

        p2: 第二个点坐标 (x, y)

    

    Returns:

        两点间的欧几里得距离

    """

    dx = p1[0] - p2[0]

    dy = p1[1] - p2[1]

    return math.sqrt(dx * dx + dy * dy)





def find_nearest_site(point: Point, sites: List[Point]) -> Point:

    """

    找到距离给定点的最近站点

    

    Args:

        point: 查询点 (x, y)

        sites: 所有站点列表

    

    Returns:

        距离最近的站点

    """

    min_dist = float('inf')

    nearest = sites[0]

    for site in sites:

        dist = euclidean_distance(point, site)

        if dist < min_dist:

            min_dist = dist

            nearest = site

    return nearest





def build_voronoi_regions(sites: List[Point], resolution: int = 100) -> Dict[Point, List[Point]]:

    """

    构建每个站点对应的Voronoi区域（离散采样）

    

    算法思路：

        将 bounding box 划分为 resolution x resolution 的网格，

        对每个网格点找到最近站点，该点归入该站点的区域。

    

    Args:

        sites: 站点列表

        resolution: 网格分辨率（每一维的采样点数）

    

    Returns:

        字典，键为站点，值为该站点区域内的采样点列表

    

    复杂度：O(resolution^2 * n)

    """

    if not sites:

        return {}

    

    # 计算站点的边界框

    min_x = min(s[0] for s in sites)

    max_x = max(s[0] for s in sites)

    min_y = min(s[1] for s in sites)

    max_y = max(s[1] for s in sites)

    

    # 边界扩展，防止边界点丢失

    margin = max(max_x - min_x, max_y - min_y) * 0.1

    min_x -= margin

    max_x += margin

    min_y -= margin

    max_y += margin

    

    # 计算网格步长

    step_x = (max_x - min_x) / (resolution - 1)

    step_y = (max_y - min_y) / (resolution - 1)

    

    # 初始化每个站点的区域点集

    regions: Dict[Point, List[Point]] = {site: [] for site in sites}

    

    # 遍历网格，为每个点分配最近站点

    for i in range(resolution):

        for j in range(resolution):

            x = min_x + i * step_x

            y = min_y + j * step_y

            grid_point: Point = (x, y)

            nearest = find_nearest_site(grid_point, sites)

            regions[nearest].append(grid_point)

    

    return regions





def compute_voronoi_cell_boundary(site: Point, other_sites: List[Point], 

                                  resolution: int = 100) -> List[Point]:

    """

    计算单个站点的Voronoi区域边界（近似）

    

    通过射线法判断点是否在区域内，采样边界上的点。

    

    Args:

        site: 目标站点

        other_sites: 其他站点列表

        resolution: 采样分辨率

    

    Returns:

        区域边界点列表（顺时针）

    """

    all_sites = [site] + other_sites

    

    min_x = min(s[0] for s in all_sites) - 1

    max_x = max(s[0] for s in all_sites) + 1

    min_y = min(s[1] for s in all_sites) - 1

    max_y = max(s[1] for s in all_sites) + 1

    

    boundary_points = []

    

    # 采样上边界和下边界

    for i in range(resolution):

        x = min_x + i * (max_x - min_x) / (resolution - 1)

        

        # 上边界

        y_top = max_y

        top_point: Point = (x, y_top)

        if find_nearest_site(top_point, all_sites) == site:

            boundary_points.append(top_point)

        

        # 下边界

        y_bottom = min_y

        bottom_point: Point = (x, y_bottom)

        if find_nearest_site(bottom_point, all_sites) == site:

            boundary_points.append(bottom_point)

    

    # 采样左边界和右边界

    for j in range(resolution):

        y = min_y + j * (max_y - min_y) / (resolution - 1)

        

        # 左边界

        x_left = min_x

        left_point: Point = (x_left, y)

        if find_nearest_site(left_point, all_sites) == site:

            boundary_points.append(left_point)

        

        # 右边界

        x_right = max_x

        right_point: Point = (x_right, y)

        if find_nearest_site(right_point, all_sites) == site:

            boundary_points.append(right_point)

    

    return boundary_points





def compute_voronoi_diagram(sites: List[Point]) -> List[Tuple[Point, List[Point]]]:

    """

    计算完整的Voronoi图（离散近似）

    

    返回每个站点及其对应的Voronoi区域点集

    

    Args:

        sites: 站点列表

    

    Returns:

        列表，每个元素为 (站点, 区域点列表)

    

    复杂度：O(n * resolution^2)

    """

    regions = build_voronoi_regions(sites, resolution=50)

    return [(site, points) for site, points in regions.items()]





if __name__ == "__main__":

    import matplotlib.pyplot as plt

    

    # 测试站点

    test_sites: List[Point] = [

        (0, 0), (1, 0), (0, 1), (1, 1),

        (0.5, 0.5), (2, 0), (2, 1)

    ]

    

    print("=== Voronoi图测试 ===")

    print(f"站点数量: {len(test_sites)}")

    

    # 构建Voronoi区域

    regions = build_voronoi_regions(test_sites, resolution=80)

    

    # 统计每个区域的点数

    for site, points in regions.items():

        print(f"站点 {site}: {len(points)} 个采样点")

    

    # 绘制Voronoi图

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    

    colors = plt.cm.tab10.colors

    for idx, (site, points) in enumerate(regions.items()):

        if points:

            xs = [p[0] for p in points]

            ys = [p[1] for p in points]

            ax.scatter(xs, ys, c=[colors[idx % len(colors)]], s=1, alpha=0.5)

    

    # 绘制站点

    site_xs = [s[0] for s in test_sites]

    site_ys = [s[1] for s in test_sites]

    ax.scatter(site_xs, site_ys, c='red', s=50, zorder=5, marker='x')

    

    ax.set_title("Voronoi图 - 离散近似")

    ax.set_aspect('equal')

    plt.tight_layout()

    plt.savefig("voronoi_diagram.png", dpi=150)

    print("图像已保存至 voronoi_diagram.png")

    plt.close()


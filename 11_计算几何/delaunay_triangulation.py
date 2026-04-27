# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / delaunay_triangulation

本文件实现 delaunay_triangulation 相关的算法功能。
"""

import math
from typing import List, Tuple, Set, Dict, Optional
from collections import defaultdict

Point = Tuple[float, float]


class Triangle:
    """
    三角形类，包含三个顶点索引和外接圆信息
    
    Attributes:
        p1, p2, p3: 三角形三个顶点的索引
        center: 外接圆圆心
        radius_sq: 外接圆半径的平方
    """
    def __init__(self, p1: int, p2: int, p3: int):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.center: Optional[Point] = None
        self.radius_sq: Optional[float] = None
        self._compute_circumcircle()
    
    def _compute_circumcircle(self) -> None:
        """
        计算三角形的外接圆圆心和半径
        
        使用坐标几何公式计算外接圆
        """
        # 获取三点坐标
        x1, y1 = points[self.p1]
        x2, y2 = points[self.p2]
        x3, y3 = points[self.p3]
        
        # 计算外接圆圆心
        # 使用行列式公式
        d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(d) < 1e-10:
            # 三点共线，退化为线段中点
            self.center = ((x1 + x2) / 2, (y1 + y2) / 2)
            dx = x2 - x1
            dy = y2 - y1
            self.radius_sq = (dx * dx + dy * dy) / 4
            return
        
        ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + 
              (x2 * x2 + y2 * y2) * (y3 - y1) + 
              (x3 * x3 + y3 * y3) * (y1 - y2)) / d
        uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + 
              (x2 * x2 + y2 * y2) * (x1 - x3) + 
              (x3 * x3 + y3 * y3) * (x2 - x1)) / d
        
        self.center = (ux, uy)
        dx = ux - x1
        dy = uy - y1
        self.radius_sq = dx * dx + dy * dy
    
    def contains_point_in_circumcircle(self, point_idx: int) -> bool:
        """
        检查外接圆内是否包含指定点（空圆性质验证）
        
        Args:
            point_idx: 待检测点的索引
        
        Returns:
            True if the point is inside the circumcircle
        """
        if self.center is None or self.radius_sq is None:
            return False
        x, y = points[point_idx]
        cx, cy = self.center
        dx = x - cx
        dy = y - cy
        return dx * dx + dy * dy <= self.radius_sq
    
    def __repr__(self) -> str:
        return f"Triangle({self.p1}, {self.p2}, {self.p3})"


# 全局站点列表（便于索引访问）
points: List[Point] = []


def cross_product(o: Point, a: Point, b: Point) -> float:
    """
    计算向量OA和OB的叉积（Z分量）
    
    用于判断点的相对位置：
    > 0 表示 OA 在 OB 的左侧（逆时针）
    < 0 表示 OA 在 OB 的右侧（顺时针）
    = 0 表示三点共线
    
    Args:
        o: 公共原点
        a: 向量终点A
        b: 向量终点B
    
    Returns:
        叉积的Z分量
    """
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def delaunay_triangulation(sites: List[Point]) -> List[Triangle]:
    """
    使用Bowyer-Watson算法进行Delaunay三角剖分
    
    Args:
        sites: 站点列表
    
    Returns:
        三角形列表
    
    复杂度：O(n^2) 最坏情况
    """
    global points
    points = sites
    
    if len(sites) < 3:
        return []
    
    # Step 1: 创建覆盖所有站点的大三角形
    # 使用足够大的三角形确保包含所有点
    min_x = min(p[0] for p in sites)
    max_x = max(p[0] for p in sites)
    min_y = min(p[1] for p in sites)
    max_y = max(p[1] for p in sites)
    
    dx = max_x - min_x
    dy = max_y - min_y
    delta_max = max(dx, dy) * 2
    
    # 大三角形的三个顶点（在所有站点外部）
    super_p1: Point = (min_x - delta_max, min_y - delta_max)
    super_p2: Point = (min_x + dx / 2, max_y + delta_max)
    super_p3: Point = (max_x + delta_max, min_y - delta_max)
    
    # 添加大三角形的顶点
    super_idx1 = len(points)
    super_idx2 = len(points) + 1
    super_idx3 = len(points) + 2
    points.extend([super_p1, super_p2, super_p3])
    
    # 初始化三角形列表，包含大三角形
    triangles: List[Triangle] = [Triangle(super_idx1, super_idx2, super_idx3)]
    
    # Step 2: 逐个插入站点
    for site_idx in range(len(sites)):
        # Step 3: 找到所有"坏三角形"（外接圆包含新站点的三角形）
        bad_triangles: List[Triangle] = []
        for tri in triangles:
            if tri.contains_point_in_circumcircle(site_idx):
                bad_triangles.append(tri)
        
        # Step 4: 构建空腔边界（坏三角形的边，去重）
        edges: Set[Tuple[int, int]] = set()
        for tri in bad_triangles:
            # 提取三角形的边（无向边）
            edge1: Tuple[int, int] = (tri.p1, tri.p2) if tri.p1 < tri.p2 else (tri.p2, tri.p1)
            edge2: Tuple[int, int] = (tri.p2, tri.p3) if tri.p2 < tri.p3 else (tri.p3, tri.p2)
            edge3: Tuple[int, int] = (tri.p3, tri.p1) if tri.p3 < tri.p1 else (tri.p1, tri.p3)
            
            # 判断该边是否被多个坏三角形共享
            # 如果只被一个坏三角形使用，则是边界边
            count = 0
            for other_tri in bad_triangles:
                if other_tri is tri:
                    continue
                e1 = (other_tri.p1, other_tri.p2) if other_tri.p1 < other_tri.p2 else (other_tri.p2, other_tri.p1)
                e2 = (other_tri.p2, other_tri.p3) if other_tri.p2 < other_tri.p3 else (other_tri.p3, other_tri.p2)
                e3 = (other_tri.p3, other_tri.p1) if other_tri.p3 < other_tri.p1 else (other_tri.p1, other_tri.p3)
                if edge1 == e1 or edge1 == e2 or edge1 == e3:
                    count += 1
                if edge2 == e1 or edge2 == e2 or edge2 == e3:
                    count += 1
                if edge3 == e1 or edge3 == e2 or edge3 == e3:
                    count += 1
            
            # 只添加边界边（只被一个坏三角形使用的边）
            for edge in [edge1, edge2, edge3]:
                edge_count = 0
                for other_tri in bad_triangles:
                    if other_tri is tri:
                        continue
                    e1 = (other_tri.p1, other_tri.p2) if other_tri.p1 < other_tri.p2 else (other_tri.p2, other_tri.p1)
                    e2 = (other_tri.p2, other_tri.p3) if other_tri.p2 < other_tri.p3 else (other_tri.p3, other_tri.p2)
                    e3 = (other_tri.p3, other_tri.p1) if other_tri.p3 < other_tri.p1 else (other_tri.p1, other_tri.p3)
                    if edge == e1 or edge == e2 or edge == e3:
                        edge_count += 1
                
                if edge_count == 0:
                    edges.add(edge)
        
        # Step 5: 从三角形列表中移除坏三角形
        for tri in bad_triangles:
            triangles.remove(tri)
        
        # Step 6: 用新三角形替换（连接站点与空腔边界）
        for edge in edges:
            p1_idx, p2_idx = edge
            new_tri = Triangle(p1_idx, p2_idx, site_idx)
            triangles.append(new_tri)
    
    # Step 7: 移除涉及大三角形顶点的三角形
    final_triangles: List[Triangle] = []
    for tri in triangles:
        if tri.p1 >= len(sites) or tri.p2 >= len(sites) or tri.p3 >= len(sites):
            continue  # 包含超三角形的顶点，跳过
        final_triangles.append(tri)
    
    return final_triangles


def get_triangles_edges(triangles: List[Triangle]) -> Set[Tuple[Point, Point]]:
    """
    从三角形列表提取所有边（用于可视化）
    
    Args:
        triangles: 三角形列表
    
    Returns:
        边的集合（用端点坐标表示）
    """
    edges: Set[Tuple[Point, Point]] = set()
    for tri in triangles:
        edge1: Tuple[Point, Point] = (points[tri.p1], points[tri.p2])
        edge2: Tuple[Point, Point] = (points[tri.p2], points[tri.p3])
        edge3: Tuple[Point, Point] = (points[tri.p3], points[tri.p1])
        edges.add(edge1)
        edges.add(edge2)
        edges.add(edge3)
    return edges


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # 测试站点
    test_sites: List[Point] = [
        (0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1),
        (0.5, 2), (1.5, 2), (1, 3), (0.3, 1.5), (1.7, 1.5)
    ]
    
    print("=== Delaunay三角剖分测试 ===")
    print(f"站点数量: {len(test_sites)}")
    
    # 执行三角剖分
    triangles = delaunay_triangulation(test_sites)
    print(f"三角形数量: {len(triangles)}")
    
    # 验证空圆性质
    print("\n=== 空圆性质验证 ===")
    valid_count = 0
    for tri in triangles:
        for i, site in enumerate(test_sites):
            # 检查除自身三个顶点外的其他点
            other_points = [j for j in range(len(test_sites)) 
                          if j != tri.p1 and j != tri.p2 and j != tri.p3]
            if tri.contains_point_in_circumcircle(i):
                # 确认不是自身顶点
                if i not in [tri.p1, tri.p2, tri.p3]:
                    print(f"警告: 三角形 {tri} 的外接圆包含点 {site}")
                else:
                    valid_count += 1
    
    print(f"空圆性质验证: {len(triangles) * 3 - valid_count} 个非顶点检查通过")
    
    # 绘制三角剖分结果
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # 绘制边
    for tri in triangles:
        # 绘制三条边
        for i, j in [(tri.p1, tri.p2), (tri.p2, tri.p3), (tri.p3, tri.p1)]:
            x_coords = [test_sites[i][0], test_sites[j][0]]
            y_coords = [test_sites[i][1], test_sites[j][1]]
            ax.plot(x_coords, y_coords, 'b-', linewidth=0.8)
    
    # 绘制站点
    site_xs = [s[0] for s in test_sites]
    site_ys = [s[1] for s in test_sites]
    ax.scatter(site_xs, site_ys, c='red', s=50, zorder=5, marker='o')
    
    # 标注站点索引
    for idx, site in enumerate(test_sites):
        ax.annotate(str(idx), site, textcoords="offset points", 
                   xytext=(5, 5), fontsize=8, color='darkred')
    
    ax.set_title("Delaunay三角剖分 - Bowyer-Watson算法")
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("delaunay_triangulation.png", dpi=150)
    print("\n图像已保存至 delaunay_triangulation.png")
    plt.close()

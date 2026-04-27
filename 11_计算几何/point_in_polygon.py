# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / point_in_polygon

本文件实现 point_in_polygon 相关的算法功能。
"""

import math
from typing import List, Tuple

Point = Tuple[float, float]
Polygon = List[Point]


def on_segment(p: Point, q: Point, r: Point) -> bool:
    """
    判断点q是否在线段pr上（用于边界检测）
    
    使用有界区域判断：
    q在pr上 当且仅当 q在以pr为对角线的矩形内
    
    Args:
        p: 线段起点
        q: 待检测点
        r: 线段终点
    
    Returns:
        True if q is on segment pr
    """
    return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
            min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))


def orientation(p: Point, q: Point, r: Point) -> int:
    """
    计算三个点的方向
    
    使用叉积判断：
    > 0 表示逆时针（CCW）
    < 0 表示顺时针（CW）
    = 0 表示共线
    
    Args:
        p: 第一个点
        q: 第二个点（顶点）
        r: 第三个点
    
    Returns:
        0 共线, 1 顺时针, 2 逆时针
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(val) < 1e-10:
        return 0
    return 1 if val < 0 else 2


def point_on_boundary(point: Point, polygon: Polygon) -> bool:
    """
    判断点是否在多边形边界上
    
    Args:
        point: 待检测点
        polygon: 多边形顶点列表
    
    Returns:
        True if point is on polygon boundary
    """
    n = len(polygon)
    if n < 3:
        return False
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        if on_segment(p1, point, p2):
            return True
    
    return False


def ray_casting(point: Point, polygon: Polygon) -> bool:
    """
    射线法判断点是否在多边形内
    
    算法：
        从待检测点向右水平发射一条射线
        统计射线与多边形边的交点个数
        - 奇数个交点 → 点在多边形内
        - 偶数个交点 → 点在多边形外
    
    特殊情况处理：
        - 射线经过顶点：只计数一次（使用特定规则避免重复）
        - 射线与边重合：跳过这种情况
    
    Args:
        point: 待检测点 (x, y)
        polygon: 多边形顶点列表（顺时针或逆时针均可）
    
    Returns:
        True if point is inside polygon
    
    复杂度：O(n)
    """
    n = len(polygon)
    if n < 3:
        return False
    
    # 如果点在边界上，直接返回True
    if point_on_boundary(point, polygon):
        return True
    
    # 射线起点
    ray_start = point
    # 射线方向点（向右延伸）
    ray_end: Point = (float('inf'), point[1])
    
    intersect_count = 0
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        
        # 检查边是否与射线相交
        # 边的y坐标范围必须包含射线高度
        if (min(p1[1], p2[1]) < point[1] <= max(p1[1], p2[1])):
            # 计算交点的x坐标
            if abs(p1[1] - p2[1]) > 1e-10:
                x_intersect = p1[0] + (point[1] - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                
                # 只考虑向右的交点
                if x_intersect > point[0]:
                    intersect_count += 1
    
    # 奇数个交点表示在内部
    return intersect_count % 2 == 1


def angle_sum(point: Point, polygon: Polygon) -> float:
    """
    角度和法判断点是否在多边形内
    
    算法：
        从待检测点向多边形每个顶点发射向量
        计算相邻向量之间的角度累加和
        - 角度和 ≈ 2π → 内部
        - 角度和 ≈ 0 → 外部
        - 角度和 ≈ π → 边界情况
    
    使用向量叉积的atan2形式计算角度
    
    Args:
        point: 待检测点
        polygon: 多边形顶点列表
    
    Returns:
        角度和（弧度）
    
    复杂度：O(n)
    """
    angle_sum_val = 0.0
    n = len(polygon)
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        
        # 向量从点到两个相邻顶点
        v1 = (p1[0] - point[0], p1[1] - point[1])
        v2 = (p2[0] - point[0], p2[1] - point[1])
        
        # 计算两个向量的夹角
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        
        # atan2返回[-π, π]的角度
        angle = math.atan2(cross, dot)
        angle_sum_val += angle
    
    return abs(angle_sum_val)


def winding_number(point: Point, polygon: Polygon) -> int:
    """
    绕数法判断点是否在多边形内
    
    算法：
        计算从点看多边形各边的绕数（winding number）
        绕数非零表示点在内部
    
    绕数定义为：围绕点一周后，边的循环次数
    对于简单多边形，绕数为1表示内部，0表示外部
    
    Args:
        point: 待检测点
        polygon: 多边形顶点列表
    
    Returns:
        绕数
    
    复杂度：O(n)
    """
    wn = 0
    n = len(polygon)
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        
        # 检查下顶点到上顶点的边（上行边）
        if p1[1] <= point[1]:
            if p2[1] > point[1]:
                # 这是一个上行边
                if is_left(p1, p2, point) > 0:
                    wn += 1
        else:
            # 这是一个下行边
            if p2[1] <= point[1]:
                if is_left(p1, p2, point) < 0:
                    wn -= 1
    
    return wn


def is_left(p1: Point, p2: Point, point: Point) -> float:
    """
    判断点相对于线段的位置
    
    Args:
        p1: 线段起点
        p2: 线段终点
        point: 待检测点
    
    Returns:
        > 0 点在左侧
        < 0 点在右侧
        = 0 共线
    """
    return (p2[0] - p1[0]) * (point[1] - p1[1]) - (point[0] - p1[0]) * (p2[1] - p1[1])


def point_in_polygon(point: Point, polygon: Polygon, method: str = "ray") -> bool:
    """
    判断点是否在多边形内的主函数
    
    Args:
        point: 待检测点 (x, y)
        polygon: 多边形顶点列表
        method: "ray" 射线法, "angle" 角度和法, "winding" 绕数法
    
    Returns:
        True if point is inside polygon
    
    复杂度：O(n)
    """
    if method == "ray":
        return ray_casting(point, polygon)
    elif method == "angle":
        angle_sum_val = angle_sum(point, polygon)
        # 角度和在2π附近表示内部
        return abs(angle_sum_val - 2 * math.pi) < 1e-6 or abs(angle_sum_val) > 1e-6 and angle_sum_val > math.pi
    elif method == "winding":
        return winding_number(point, polygon) != 0
    else:
        raise ValueError(f"Unknown method: {method}")


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # 定义测试多边形（凹多边形）
    test_polygon: Polygon = [
        (0, 0), (4, 0), (4, 3), (2, 1), (0, 3)
    ]
    
    # 测试点集
    test_points: List[Tuple[Point, bool]] = [
        ((2, 0.5), True),   # 内部
        ((2, 2), True),     # 内部
        ((1, 1), True),     # 内部
        ((5, 1), False),   # 外部
        ((2, -1), False),   # 外部
        ((0, 0), True),     # 边界
        ((4, 1.5), True),   # 内部
    ]
    
    print("=== 点是否在多边形内测试 ===")
    print(f"多边形顶点: {test_polygon}")
    
    for point, expected in test_points:
        result_ray = ray_casting(point, test_polygon)
        result_angle = abs(angle_sum(point, test_polygon) - 2 * math.pi) < 0.1 or abs(angle_sum(point, test_polygon)) > 0.1 and abs(angle_sum(point, test_polygon) - math.pi) < 0.1
        result_winding = winding_number(point, test_polygon) != 0
        
        print(f"\n点 {point}:")
        print(f"  射线法: {'内部' if result_ray else '外部'} (期望: {'内部' if expected else '外部'})")
        print(f"  角度和: {angle_sum(point, test_polygon):.4f}")
        print(f"  绕数法: {'内部' if result_winding else '外部'}")
    
    # 绘制测试结果
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    
    # 绘制多边形
    polygon_closed = test_polygon + [test_polygon[0]]
    poly_xs = [p[0] for p in polygon_closed]
    poly_ys = [p[1] for p in polygon_closed]
    ax.fill(poly_xs, poly_ys, alpha=0.3, color='blue')
    ax.plot(poly_xs, poly_ys, 'b-', linewidth=2)
    
    # 绘制测试点
    for point, is_inside in test_points:
        color = 'green' if is_inside else 'red'
        marker = 'o' if is_inside else 'x'
        ax.scatter(point[0], point[1], c=color, s=100, marker=marker, zorder=5)
    
    ax.set_title("点是否在多边形内测试\n(绿色=内部, 红色=外部)")
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("point_in_polygon.png", dpi=150)
    print("\n图像已保存至 point_in_polygon.png")
    plt.close()

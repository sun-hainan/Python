# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / sutherland_hodgman

本文件实现 sutherland_hodgman 相关的算法功能。
"""

from typing import List, Tuple, Optional


Point = Tuple[float, float]


def clip_polygon_by_edge(polygon: List[Point], 
                        edge_start: Point, edge_end: Point,
                        inside_func) -> List[Point]:
    """
    用一条边裁剪多边形
    
    参数:
        polygon: 输入多边形顶点列表 [(x,y), ...]
        edge_start: 边起点
        edge_end: 边终点
        inside_func: 判断点是否在边内侧的函数 (p1, p2, p) -> bool
    
    返回:
        裁剪后的多边形
    """
    if len(polygon) == 0:
        return []
    
    output = []
    
    # 遍历多边形的每条边 (S, E)
    S = polygon[-1]
    
    for E in polygon:
        # S 是边起点，E 是边终点
        S_inside = inside_func(edge_start, edge_end, S)
        E_inside = inside_func(edge_start, edge_end, E)
        
        if S_inside:
            # S 在内侧
            if E_inside:
                # E 也在内侧 -> 保留 E
                output.append(E)
            else:
                # E 在外侧 -> 添加交点 I
                I = compute_intersection(S, E, edge_start, edge_end)
                if I is not None:
                    output.append(I)
        else:
            # S 在外侧
            if E_inside:
                # E 在内侧 -> 添加交点 I 和 E
                I = compute_intersection(S, E, edge_start, edge_end)
                if I is not None:
                    output.append(I)
                output.append(E)
            # else: 两者都在外侧，不添加任何点
        
        S = E
    
    return output


def compute_intersection(P1: Point, P2: Point, 
                         edge_start: Point, edge_end: Point) -> Optional[Point]:
    """
    计算线段 (P1, P2) 与边 (edge_start, edge_end) 的交点
    
    使用参数方程:
    P = P1 + t(P2 - P1), t ∈ [0, 1]
    Q = edge_start + u(edge_end - edge_start), u ∈ [0, 1]
    
    交点满足: P1 + t(P2 - P1) = edge_start + u(edge_end - edge_start)
    """
    x1, y1 = P1
    x2, y2 = P2
    x3, y3 = edge_start
    x4, y4 = edge_end
    
    # 计算行列式
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-10:
        return None  # 平行或重合
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    
    # 计算交点
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    
    return (x, y)


def inside_left(p1: Point, p2: Point, p: Point) -> bool:
    """判断 p 是否在边的左侧（内侧）"""
    x1, y1 = p1
    x2, y2 = p2
    x, y = p
    return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) >= 0


def inside_right(p1: Point, p2: Point, p: Point) -> bool:
    """判断 p 是否在边的右侧"""
    x1, y1 = p1
    x2, y2 = p2
    x, y = p
    return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) <= 0


def inside_bottom(p1: Point, p2: Point, p: Point) -> bool:
    """判断 p 是否在边的下方（内侧）"""
    x1, y1 = p1
    x2, y2 = p2
    x, y = p
    return (y2 - y1) * (x - x1) - (x2 - x1) * (y - y1) >= 0


def inside_top(p1: Point, p2: Point, p: Point) -> bool:
    """判断 p 是否在边的上方"""
    x1, y1 = p1
    x2, y2 = p2
    x, y = p
    return (y2 - y1) * (x - x1) - (x2 - x1) * (y - y1) <= 0


def sutherland_hodgman_clip(polygon: List[Point],
                            x_min: float, y_min: float,
                            x_max: float, y_max: float) -> List[Point]:
    """
    Sutherland-Hodgman 多边形裁剪主算法
    
    参数:
        polygon: 输入多边形顶点列表
        x_min, y_min: 裁剪窗口左下角
        x_max, y_max: 裁剪窗口右上角
    
    返回:
        裁剪后的多边形顶点列表
    """
    if len(polygon) == 0:
        return []
    
    # 四条边: 左、右、下、上
    edges = [
        ((x_min, y_min), (x_min, y_max), inside_left),    # 左边界
        ((x_max, y_min), (x_max, y_max), inside_right),   # 右边界
        ((x_min, y_min), (x_max, y_min), inside_bottom),  # 下边界
        ((x_min, y_max), (x_max, y_max), inside_top),     # 上边界
    ]
    
    output = polygon
    
    for edge_start, edge_end, inside in edges:
        if len(output) == 0:
            return []
        output = clip_polygon_by_edge(output, edge_start, edge_end, inside)
    
    return output


def convex_polygon_clip(polygon: List[Point],
                        clip_window: List[Point]) -> List[Point]:
    """
    用凸多边形裁剪另一个多边形（通用版本）
    
    参数:
        polygon: 被裁剪的多边形
        clip_window: 裁剪窗口（凸多边形顶点列表）
    
    返回:
        裁剪后的多边形
    """
    if len(polygon) == 0 or len(clip_window) < 3:
        return []
    
    output = polygon
    
    # 遍历裁剪窗口的每条边
    for i in range(len(clip_window)):
        if len(output) == 0:
            return []
        
        edge_start = clip_window[i]
        edge_end = clip_window[(i + 1) % len(clip_window)]
        
        # 判断点是否在边内侧
        def inside(p1, p2, p):
            x1, y1 = p1
            x2, y2 = p2
            x, y = p
            return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) >= 0
        
        output = clip_polygon_by_edge(output, edge_start, edge_end, inside)
    
    return output


if __name__ == "__main__":
    print("=" * 60)
    print("Sutherland-Hodgman 多边形裁剪算法测试")
    print("=" * 60)
    
    # 定义裁剪窗口
    x_min, y_min = 2, 2
    x_max, y_max = 8, 8
    
    print(f"\n裁剪窗口: ({x_min},{y_min}) - ({x_max},{y_max})")
    
    # 测试多边形
    test_polygons = [
        # 完全在窗口内
        ([(3, 3), (5, 3), (5, 5), (3, 5)], "小正方形在内"),
        # 跨越多个边界
        ([(0, 0), (10, 0), (10, 10), (0, 10)], "大正方形穿过"),
        ([(0, 5), (10, 5), (10, 6), (0, 6)], "水平条穿过"),
        # 凹多边形
        ([(0, 0), (4, 0), (4, 4), (6, 4), (6, 8), (0, 8)], "L形多边形"),
        # 三角形
        ([(1, 1), (5, 1), (3, 9)], "三角形穿过"),
        # 复杂形状
        ([(0, 0), (3, 5), (5, 3), (7, 7), (9, 5), (10, 10), (0, 10)], "星形"),
    ]
    
    print("\n测试结果:")
    for polygon, desc in test_polygons:
        result = sutherland_hodgman_clip(polygon, x_min, y_min, x_max, y_max)
        print(f"  {desc}:")
        print(f"    输入顶点数: {len(polygon)}")
        print(f"    输出顶点数: {len(result)}")
        if result:
            print(f"    顶点: {result[:5]}{'...' if len(result) > 5 else ''}")
    
    # 可视化测试
    print("\n可视化测试:")
    print("  多边形: 三角形 (0,0), (10,5), (5,10)")
    
    triangle = [(0.0, 0.0), (10.0, 5.0), (5.0, 10.0)]
    result = sutherland_hodgman_clip(triangle, x_min, y_min, x_max, y_max)
    
    print(f"  裁剪窗口: ({x_min},{y_min}) - ({x_max},{y_max})")
    print(f"  裁剪后顶点数: {len(result)}")
    
    # 简单文本可视化
    print("\n  裁剪前示意图:")
    print("    y=9 ...")
    print("    y=8 ......")
    print("    y=7 .......  (5,10)")
    print("    y=6 ......")
    print("    y=5 ....  (10,5)")
    print("    y=4 ......")
    print("    y=3 ......")
    print("    y=2 ......")
    print("    y=1 ....")
    print("    y=0 ..  (0,0)")
    print("       0123456789 x")
    
    # 输出裁剪后顶点的可视化
    if result:
        print("\n  裁剪后顶点:")
        for p in result:
            print(f"    ({p[0]:.2f}, {p[1]:.2f})")
    
    # 凸多边形裁剪测试
    print("\n" + "=" * 60)
    print("凸多边形裁剪测试:")
    print("=" * 60)
    
    # 裁剪窗口是凸多边形（三角形）
    triangle_clip = [(3, 3), (7, 3), (5, 7)]
    polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
    
    result = convex_polygon_clip(polygon, triangle_clip)
    print(f"  被裁剪: 正方形 (0,0)-(10,10)")
    print(f"  裁剪窗口: 三角形 (3,3)-(7,3)-(5,7)")
    print(f"  结果顶点数: {len(result)}")
    
    print("\n" + "=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  时间复杂度: O(n + m)")
    print("    n = 输入多边形顶点数")
    print("    m = 交点总数")
    print("  空间复杂度: O(n)")
    print("  注意事项:")
    print("    - 输出顶点数可能大于输入（产生新交点）")
    print("    - 每次迭代可能增加顶点数")

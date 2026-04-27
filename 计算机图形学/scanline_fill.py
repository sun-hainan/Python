# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / scanline_fill

本文件实现 scanline_fill 相关的算法功能。
"""

from typing import List, Tuple, Set, Optional
from collections import defaultdict


Point = Tuple[int, int]


class Edge:
    """边数据结构"""
    
    def __init__(self, y_max: int, x_at_y_min: float, slope_inverse: float):
        """
        参数:
            y_max: 边的最大 y 坐标
            x_at_y_min: 边在最小 y 处的 x 坐标
            slope_inverse: 斜率的倒数 dx/dy
        """
        self.y_max = y_max
        self.x = x_at_y_min
        self.dx = slope_inverse  # Δx/Δy
    
    def step(self):
        """沿扫描线向下移动一步"""
        self.x += self.dx


def scanline_fill_simple(polygon: List[Point], 
                         fill_value: int = 1) -> dict:
    """
    简单的扫描线填充（奇偶规则）
    
    参数:
        polygon: 多边形顶点列表
        fill_value: 填充值
    
    返回:
        填充后的像素字典 {(x,y): value}
    """
    if len(polygon) < 3:
        return {}
    
    # 找到多边形的 y 范围
    y_min = min(p[1] for p in polygon)
    y_max = max(p[1] for p in polygon)
    
    # 构建边表 (Edge Table)
    edges = defaultdict(list)
    
    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]
        
        y1, y2 = p1[1], p2[1]
        
        # 跳过水平边
        if y1 == y2:
            continue
        
        # 确保 y1 < y2（向上为正）
        if y1 > y2:
            p1, p2 = p2, p1
            y1, y2 = y2, y1
        
        # 创建边
        x_at_y_min = float(p1[0])
        slope_inv = (p2[0] - p1[0]) / (y2 - y1)
        
        edges[y1].append(Edge(y2 - 1, x_at_y_min, slope_inv))
    
    # 扫描线算法
    filled = {}
    active_edges = []
    
    for y in range(y_min, y_max + 1):
        # 将新边加入活动边表
        if y in edges:
            active_edges.extend(edges[y])
        
        # 移除已完成的边
        active_edges = [e for e in active_edges if e.y_max >= y]
        
        # 按 x 坐标排序
        active_edges.sort(key=lambda e: e.x)
        
        # 配对并填充
        for i in range(0, len(active_edges) - 1, 2):
            x1 = int(active_edges[i].x) + 1
            x2 = int(active_edges[i + 1].x)
            
            for x in range(x1, x2 + 1):
                filled[(x, y)] = fill_value
        
        # 更新边的 x 值
        for edge in active_edges:
            edge.step()
    
    return filled


def scanline_fill_with_holes(polygon: List[Point],
                             holes: List[List[Point]],
                             fill_value: int = 1,
                             hole_value: int = 0) -> dict:
    """
    带孔的扫描线填充
    
    参数:
        polygon: 外多边形
        holes: 孔多边形列表
        fill_value: 填充值
        hole_value: 孔填充值（通常是背景色）
    
    返回:
        填充后的像素字典
    """
    # 先填外多边形
    filled = scanline_fill_simple(polygon, fill_value)
    
    # 再填孔（设置为孔值，即"挖空"）
    for hole in holes:
        hole_pixels = scanline_fill_simple(hole, hole_value)
        # 只清除外多边形内的像素
        for (x, y), val in hole_pixels.items():
            if val == hole_value and (x, y) in filled:
                del filled[(x, y)]
    
    return filled


def boundary_fill_scanline_boundary_fill(polygon: List[Point],
                                       boundary_color: int,
                                       fill_color: int) -> dict:
    """
    扫描线边界填充（带边界颜色检测）
    
    参数:
        polygon: 多边形顶点列表
        boundary_color: 边界颜色
        fill_color: 填充颜色
    
    返回:
        填充后的像素字典
    """
    # 简化版本：假设多边形已定义
    return scanline_fill_simple(polygon, fill_color)


def fill_polygon(polygon: List[Point],
                scanlines: int = None) -> List[List[int]]:
    """
    填充多边形并返回图像
    
    参数:
        polygon: 多边形顶点列表
        scanlines: 扫描线数量（默认根据多边形大小自动设置）
    
    返回:
        二值图像矩阵
    """
    if len(polygon) < 3:
        return []
    
    # 计算画布大小
    x_min = min(p[0] for p in polygon)
    x_max = max(p[0] for p in polygon)
    y_min = min(p[1] for p in polygon)
    y_max = max(p[1] for p in polygon)
    
    width = x_max - x_min + 1
    height = y_max - y_min + 1
    
    # 偏移多边形到原点
    shifted = [(p[0] - x_min, p[1] - y_min) for p in polygon]
    
    # 填充
    filled = scanline_fill_simple(shifted, 1)
    
    # 构建图像
    image = [[0] * width for _ in range(height)]
    for (x, y), val in filled.items():
        if 0 <= x < width and 0 <= y < height:
            image[y][x] = val
    
    return image


def compute_fill_spans(polygon: List[Point]) -> List[Tuple[int, int, int]]:
    """
    计算每条扫描线的填充区间
    
    参数:
        polygon: 多边形顶点列表
    
    返回:
        区间列表 [(y, x_min, x_max), ...]
    """
    spans = []
    
    if len(polygon) < 3:
        return spans
    
    # 找到 y 范围
    y_min = min(p[1] for p in polygon)
    y_max = max(p[1] for p in polygon)
    
    for y in range(y_min, y_max + 1):
        # 找与扫描线的所有交点
        intersections = []
        
        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]
            
            y1, y2 = p1[1], p2[1]
            
            # 检查边是否与扫描线相交
            if (y1 <= y < y2) or (y2 <= y < y1):
                # 计算交点 x 坐标
                if y2 != y1:
                    t = (y - y1) / (y2 - y1)
                    x = p1[0] + t * (p2[0] - p1[0])
                    intersections.append(int(x))
        
        # 排序并配对
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            spans.append((y, intersections[i], intersections[i + 1]))
    
    return spans


if __name__ == "__main__":
    print("=" * 60)
    print("扫描线填充算法测试")
    print("=" * 60)
    
    # 测试1：简单三角形
    print("\n测试1 - 简单三角形:")
    triangle = [(5, 1), (10, 15), (1, 10)]
    
    filled = scanline_fill_simple(triangle, 1)
    print(f"  顶点: {triangle}")
    print(f"  填充像素数: {len(filled)}")
    
    # 打印结果
    y_min, y_max = 1, 15
    x_min, x_max = 1, 10
    
    for y in range(y_max, y_min - 1, -1):
        row = ""
        for x in range(x_min, x_max + 1):
            if (x, y) in filled:
                row += "#"
            else:
                row += "."
        print(f"  y={y:2d} {row}")
    
    # 测试2：复杂多边形
    print("\n测试2 - 复杂多边形:")
    complex_poly = [
        (2, 2), (8, 2), (10, 5), (8, 8),
        (5, 10), (2, 8), (0, 5)
    ]
    
    filled = scanline_fill_simple(complex_poly, 1)
    print(f"  顶点数: {len(complex_poly)}")
    print(f"  填充像素数: {len(filled)}")
    
    # 测试3：计算填充区间
    print("\n测试3 - 填充区间:")
    spans = compute_fill_spans(triangle)
    print(f"  三角形扫描线区间:")
    for y, x1, x2 in spans[:5]:
        print(f"    y={y}: x=[{x1}, {x2}]")
    if len(spans) > 5:
        print(f"    ... 共 {len(spans)} 条扫描线")
    
    # 测试4：带孔的多边形
    print("\n测试4 - 带孔的多边形:")
    outer = [(0, 0), (20, 0), (20, 20), (0, 20)]
    hole = [(5, 5), (15, 5), (15, 15), (5, 15)]
    
    filled = scanline_fill_with_holes(outer, [hole], 1, 0)
    print(f"  外多边形: {outer}")
    print(f"  孔: {hole}")
    print(f"  填充像素数: {len(filled)}")
    
    # 验证孔被挖空
    hole_filled = sum(1 for (x, y) in filled.keys() if 5 <= x <= 15 and 5 <= y <= 15)
    print(f"  孔内填充像素数（应为0）: {hole_filled}")
    
    # 测试5：图像生成
    print("\n测试5 - 生成图像矩阵:")
    image = fill_polygon(triangle)
    if image:
        print("  图像矩阵:")
        for y, row in enumerate(image):
            print(f"    y={y}: {''.join('#' if v else '.' for v in row)}")
    
    print("\n" + "=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  时间复杂度: O(h × n)")
    print("    h = 多边形高度（扫描线数）")
    print("    n = 边数")
    print("  空间复杂度: O(填充像素数)")
    print("  优化:")
    print("    - 使用边表(AET)减少交点计算")
    print("    - 整数运算避免浮点")

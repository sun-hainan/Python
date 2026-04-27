# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / bresenham_line

本文件实现 bresenham_line 相关的算法功能。
"""

from typing import List, Tuple


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    Bresenham 画线算法
    
    参数:
        x0, y0: 起点坐标
        x1, y1: 终点坐标
    
    返回:
        像素坐标列表 [(x, y), ...]
    
    算法步骤：
    1. 计算 dx, dy
    2. 确定步进方向
    3. 初始化误差项
    4. 迭代绘制像素
    """
    points = []
    
    # 计算增量
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    
    # 确定主移动方向
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    
    # 初始化误差项
    # 对于浅斜率线，err = dx/2
    # 对于深斜率线，err = dy/2
    err = dx - dy
    
    # 当前点
    x, y = x0, y0
    
    while True:
        points.append((x, y))
        
        # 检查是否到达终点
        if x == x1 and y == y1:
            break
        
        # 计算误差
        e2 = 2 * err
        
        # 沿 x 方向移动
        if e2 > -dy:
            err -= dy
            x += sx
        
        # 沿 y 方向移动
        if e2 < dx:
            err += dx
            y += sy
    
    return points


def bresenham_line_thick(x0: int, y0: int, x1: int, y1: int, 
                         thickness: int = 1) -> List[Tuple[int, int]]:
    """
    带粗细的 Bresenham 画线
    
    参数:
        x0, y0: 起点坐标
        x1, y1: 终点坐标
        thickness: 线宽（奇数）
    
    返回:
        像素坐标列表
    """
    points = []
    
    if thickness == 1:
        return bresenham_line(x0, y0, x1, y1)
    
    # 对于粗线，绘制多根平行线
    half_width = thickness // 2
    
    # 计算垂直于线段的方向
    dx = x1 - x0
    dy = y1 - y0
    
    # 线段长度为0时
    if dx == 0 and dy == 0:
        return [(x0, y0)]
    
    # 计算法线方向
    length = (dx * dx + dy * dy) ** 0.5
    nx = -dy / length
    ny = dx / length
    
    # 沿法线方向偏移
    for offset in range(-half_width, half_width + 1):
        ox = int(nx * offset)
        oy = int(ny * offset)
        points.extend(bresenham_line(x0 + ox, y0 + oy, x1 + ox, y1 + oy))
    
    return points


def bresenham_circle(center_x: int, center_y: int, radius: int) -> List[Tuple[int, int]]:
    """
    Bresenham 画圆算法（基于中点圆算法）
    
    参数:
        center_x, center_y: 圆心坐标
        radius: 半径
    
    返回:
        像素坐标列表（只含第一象限，需自行对称扩展）
    
    算法原理：
    使用决策参数 pk 判断像素与圆的近似程度
    pk = F(xk+1, yk-1/2) = (xk+1)^2 + (yk-1/2)^2 - r^2
    """
    points = []
    
    x = 0
    y = radius
    d = 1 - radius  # 决策参数
    
    # 只绘制第一象限，其他象限通过对称得到
    while x <= y:
        # 八分圆对称：绘制8个点
        # 第一象限(y轴正半轴和x轴正半轴之间)
        # 第二象限
        # ...
        symmetry_points = [
            (center_x + x, center_y + y),  # 第1象限
            (center_x - x, center_y + y),  # 第2象限
            (center_x + x, center_y - y),  # 第3象限
            (center_x - x, center_y - y),  # 第4象限
            (center_x + y, center_y + x),  # 第5象限
            (center_x - y, center_y + x),  # 第6象限
            (center_x + y, center_y - x),  # 第7象限
            (center_x - y, center_y - x),  # 第8象限
        ]
        points.extend(symmetry_points)
        
        # 更新决策参数
        if d < 0:
            # 决策参数小于0，选择E点
            d += 2 * x + 3
        else:
            # 决策参数大于等于0，选择SE点
            d += 2 * (x - y) + 5
            y -= 1
        
        x += 1
    
    return points


def bresenham_ellipse(center_x: int, center_y: int, 
                      radius_x: int, radius_y: int) -> List[Tuple[int, int]]:
    """
    Bresenham 画椭圆算法
    
    参数:
        center_x, center_y: 椭圆中心
        radius_x: x半径
        radius_y: y半径
    
    返回:
        像素坐标列表
    """
    points = []
    
    x = 0
    y = radius_y
    
    # 第一部分：弧度在45度以下时
    d1 = (radius_x * radius_x) + (radius_y * radius_y) - \
          (2 * radius_x * radius_x * radius_y)
    
    while (radius_x * radius_x * y) > (radius_y * radius_y * x):
        points.append((center_x + x, center_y + y))
        points.append((center_x - x, center_y + y))
        points.append((center_x + x, center_y - y))
        points.append((center_x - x, center_y - y))
        
        if d1 < 0:
            d1 += (2 * radius_x * radius_x * y) - (radius_x * radius_x) + \
                  (2 * radius_x * radius_x)
        else:
            d1 += (2 * radius_x * radius_x * y) - (radius_x * radius_x) + \
                  (2 * radius_x * radius_x)
            y -= 1
        
        x += 1
    
    # 第二部分：弧度大于45度
    d2 = (radius_x * radius_x * (y - 1) * (y - 1)) + \
          (radius_y * radius_y * (x + 1) * (x + 1)) - \
          (radius_x * radius_x * radius_y * radius_y)
    
    while y >= 0:
        points.append((center_x + x, center_y + y))
        points.append((center_x - x, center_y + y))
        points.append((center_x + x, center_y - y))
        points.append((center_x - x, center_y - y))
        
        if d2 > 0:
            d2 -= (2 * radius_y * radius_y * x) + (radius_y * radius_y) + \
                  (2 * radius_y * radius_y)
        else:
            d2 -= (2 * radius_y * radius_y * x) + (radius_y * radius_y) + \
                  (2 * radius_y * radius_y)
            y -= 1
        
        x += 1
    
    return points


def draw_line_naive(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    朴素画线算法（DDA 的简化版本）
    
    参数:
        x0, y0: 起点
        x1, y1: 终点
    
    返回:
        像素坐标列表
    
    特点：
    - 使用浮点运算
    - 每次 step 一个像素
    - 速度较慢但直观
    """
    points = []
    
    dx = x1 - x0
    dy = y1 - y0
    
    # 计算步数
    steps = max(abs(dx), abs(dy))
    
    if steps == 0:
        return [(x0, y0)]
    
    # 计算增量
    x_inc = dx / steps
    y_inc = dy / steps
    
    # 迭代绘制
    x, y = float(x0), float(y0)
    
    for _ in range(steps + 1):
        points.append((round(x), round(y)))
        x += x_inc
        y += y_inc
    
    return points


if __name__ == "__main__":
    print("=" * 60)
    print("Bresenham 画线算法测试")
    print("=" * 60)
    
    # 测试1：基本线段
    test_cases = [
        (0, 0, 10, 5, "浅斜率线"),
        (0, 0, 5, 10, "陡斜率线"),
        (0, 0, 10, 0, "水平线"),
        (0, 0, 0, 10, "垂直线"),
        (0, 0, 10, 10, "对角线45度"),
        (0, 0, 10, 3, "负斜率线"),
        (5, 5, 0, 0, "反向线段"),
    ]
    
    print("\n测试1 - 基本线段:")
    for x0, y0, x1, y1, desc in test_cases:
        points = bresenham_line(x0, y0, x1, y1)
        print(f"  {desc}: ({x0},{y0}) -> ({x1},{y1})")
        print(f"    像素数: {len(points)}")
        print(f"    前5个点: {points[:5]}")
        print(f"    后5个点: {points[-5:]}")
    
    # 测试2：与朴素算法对比
    print("\n测试2 - 与朴素算法对比:")
    x0, y0, x1, y1 = 0, 0, 17, 8
    bresenham_points = bresenham_line(x0, y0, x1, y1)
    naive_points = draw_line_naive(x0, y0, x1, y1)
    
    print(f"  线段: ({x0},{y0}) -> ({x1},{y1})")
    print(f"  Bresenham: {len(bresenham_points)} 个像素")
    print(f"  朴素算法: {len(naive_points)} 个像素")
    
    # 测试3：画圆
    print("\n测试3 - 画圆:")
    radius = 10
    circle_points = bresenham_circle(0, 0, radius)
    print(f"  圆心(0,0) 半径{radius}")
    print(f"  像素数: {len(circle_points)}")
    
    # 测试4：画椭圆
    print("\n测试4 - 画椭圆:")
    ellipse_points = bresenham_ellipse(0, 0, 15, 8)
    print(f"  椭圆中心(0,0) rx=15 ry=8")
    print(f"  像素数: {len(ellipse_points)}")
    
    # 可视化测试
    print("\n测试5 - 可视化线段:")
    print("  线段 (0,0) -> (20,8):")
    points = bresenham_line(0, 0, 20, 8)
    
    # 创建画布
    max_x = max(p[0] for p in points) + 2
    max_y = max(p[1] for p in points) + 2
    canvas = [[" " for _ in range(max_x)] for _ in range(max_y)]
    
    # 绘制点
    for x, y in points:
        if 0 <= y < max_y and 0 <= x < max_x:
            canvas[y][x] = "#"
    
    # 打印（从上到下，y递增）
    for row in canvas:
        print("    " + "".join(row))
    
    print("\n" + "=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  时间复杂度: O(|dx| + |dy|)")
    print("  空间复杂度: O(|dx| + |dy|) 存储像素点")
    print("  优势:")
    print("    - 只用整数运算（无浮点、无乘除）")
    print("    - 只需加法和移位")
    print("    - 适合硬件实现")

# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / bezier_curve

本文件实现 bezier_curve 相关的算法功能。
"""

from typing import List, Tuple


Point = Tuple[float, float]


def lerp(p1: Point, p2: Point, t: float) -> Point:
    """
    线性插值
    
    参数:
        p1, p2: 两个端点
        t: 参数 [0, 1]
    
    返回:
        插值点
    """
    x1, y1 = p1
    x2, y2 = p2
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def de_casteljau_recursive(control_points: List[Point], t: float) -> Point:
    """
    de Casteljau 算法（递归版本）
    
    参数:
        control_points: 控制点列表
        t: 参数 [0, 1]
    
    返回:
        曲线上的点
    
    算法：
    1. 在每条边上取 t 处的新点
    2. 连接相邻点形成新的多边形
    3. 重复直到只有一个点
    """
    if len(control_points) == 1:
        return control_points[0]
    
    # 计算中间点
    new_points = []
    for i in range(len(control_points) - 1):
        new_points.append(lerp(control_points[i], control_points[i + 1], t))
    
    # 递归
    return de_casteljau_recursive(new_points, t)


def de_casteljau_iterative(control_points: List[Point], t: float) -> Point:
    """
    de Casteljau 算法（迭代版本，优化）
    
    参数:
        control_points: 控制点列表
        t: 参数 [0, 1]
    
    返回:
        曲线上的点
    """
    points = list(control_points)
    
    # 逐层迭代
    while len(points) > 1:
        new_points = []
        for i in range(len(points) - 1):
            new_points.append(lerp(points[i], points[i + 1], t))
        points = new_points
    
    return points[0]


def evaluate_bezier(control_points: List[Point], t: float) -> Point:
    """
    评估 Bezier 曲线上的点
    
    参数:
        control_points: 控制点列表
        t: 参数 [0, 1]
    
    返回:
        曲线上的点
    """
    return de_casteljau_iterative(control_points, t)


def split_bezier(control_points: List[Point], t: float) -> Tuple[List[Point], List[Point]]:
    """
    将 Bezier 曲线在参数 t 处分割为两段
    
    参数:
        control_points: 控制点列表
        t: 分割参数 [0, 1]
    
    返回:
        (左半段控制点, 右半段控制点)
    """
    points = list(control_points)
    left = [points[0]]
    right = [points[-1]]
    
    # de Casteljau 过程
    while len(points) > 1:
        new_points = []
        for i in range(len(points) - 1):
            new_points.append(lerp(points[i], points[i + 1], t))
        
        left.append(new_points[0])
        right.insert(0, new_points[-1])
        
        points = new_points
    
    return left, right


def bezier_derivative(control_points: List[Point], t: float) -> Point:
    """
    计算 Bezier 曲线在参数 t 处的导数（切向量）
    
    参数:
        control_points: 控制点列表
        t: 参数 [0, 1]
    
    返回:
        切向量
    """
    n = len(control_points) - 1  # 次数
    
    if n == 0:
        return (0.0, 0.0)
    
    # 导数曲线的控制点
    derivative_points = []
    for i in range(n):
        x = n * (control_points[i + 1][0] - control_points[i][0])
        y = n * (control_points[i + 1][1] - control_points[i][1])
        derivative_points.append((x, y))
    
    # 评估导数曲线
    return evaluate_bezier(derivative_points, t)


def sample_bezier(control_points: List[Point], num_samples: int = 100) -> List[Point]:
    """
    采样 Bezier 曲线
    
    参数:
        control_points: 控制点列表
        num_samples: 采样点数
    
    返回:
        曲线上的点列表
    """
    points = []
    for i in range(num_samples + 1):
        t = i / num_samples
        points.append(evaluate_bezier(control_points, t))
    return points


def degree_elevation(control_points: List[Point], degree: int = 1) -> List[Point]:
    """
    提高 Bezier 曲线次数
    
    参数:
        control_points: 控制点列表
        degree: 提高次数
    
    返回:
        提高次数后的控制点
    """
    points = list(control_points)
    n = len(points) - 1
    
    for _ in range(degree):
        new_points = [points[0]]
        for i in range(1, len(points)):
            # 插值公式: new[i] = (i/(n+1)) * old[i-1] + (1 - i/(n+1)) * old[i]
            x = (i / (n + 1)) * points[i - 1][0] + (1 - i / (n + 1)) * points[i][0]
            y = (i / (n + 1)) * points[i - 1][1] + (1 - i / (n + 1)) * points[i][1]
            new_points.append((x, y))
        new_points.append(points[-1])
        points = new_points
    
    return points


if __name__ == "__main__":
    print("=" * 60)
    print("Bezier 曲线 (de Casteljau 算法) 测试")
    print("=" * 60)
    
    # 测试1：二次 Bezier 曲线
    print("\n测试1 - 二次 Bezier 曲线:")
    p0 = (0.0, 0.0)
    p1 = (5.0, 10.0)
    p2 = (10.0, 0.0)
    
    control_points = [p0, p1, p2]
    
    print(f"  控制点: {control_points}")
    
    # 采样曲线
    samples = sample_bezier(control_points, 10)
    print("  采样点 (t=0.0 到 1.0):")
    for i, p in enumerate(samples):
        t = i / 10
        print(f"    t={t:.1f}: ({p[0]:.2f}, {p[1]:.2f})")
    
    # 测试2：三次 Bezier 曲线
    print("\n测试2 - 三次 Bezier 曲线:")
    p0 = (0.0, 0.0)
    p1 = (3.0, 10.0)
    p2 = (7.0, 10.0)
    p3 = (10.0, 0.0)
    
    control_points = [p0, p1, p2, p3]
    
    print(f"  控制点: {control_points}")
    
    samples = sample_bezier(control_points, 10)
    print("  采样点:")
    for i, p in enumerate(samples):
        t = i / 10
        print(f"    t={t:.1f}: ({p[0]:.2f}, {p[1]:.2f})")
    
    # 测试3：曲线分割
    print("\n测试3 - 曲线分割 (t=0.5):")
    left, right = split_bezier(control_points, 0.5)
    print(f"  左半段控制点: {left}")
    print(f"  右半段控制点: {right}")
    
    # 验证：两段连接处是否是同一点
    mid_point = evaluate_bezier(control_points, 0.5)
    print(f"  中点: {mid_point}")
    
    # 测试4：导数（切向量）
    print("\n测试4 - 导数/切向量:")
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        point = evaluate_bezier(control_points, t)
        tangent = bezier_derivative(control_points, t)
        print(f"  t={t:.2f}: 点={point}, 切向量={tangent}")
    
    # 测试5：可视化（二维ASCII）
    print("\n测试5 - 可视化（10x10网格）:")
    
    # 生成更多采样点用于绘图
    samples = sample_bezier(control_points, 20)
    
    # 创建网格
    width, height = 50, 20
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    def scale_x(x):
        return int(x * (width - 1) / 10)
    def scale_y(y):
        return int(y * (height - 1) / 10)
    
    # 绘制控制多边形
    for i in range(len(control_points) - 1):
        x1, y1 = control_points[i]
        x2, y2 = control_points[i + 1]
        x1, x2 = scale_x(x1), scale_x(x2)
        y1, y2 = scale_y(y1), scale_y(y2)
        
        # 简化绘制
        pass
    
    # 绘制曲线
    for p in samples:
        x, y = scale_x(p[0]), scale_y(p[1])
        if 0 <= x < width and 0 <= y < height:
            grid[height - 1 - y][x] = "*"
    
    # 绘制控制点
    for p in control_points:
        x, y = scale_x(p[0]), scale_y(p[1])
        if 0 <= x < width and 0 <= y < height:
            grid[height - 1 - y][x] = "o"
    
    # 打印
    for row in grid:
        print("    " + "".join(row))
    
    print("\n  图例: o=控制点, *=贝塞尔曲线")
    
    # 测试6：提高次数
    print("\n测试6 - 提高曲线次数:")
    quadratic = [(0.0, 0.0), (5.0, 10.0), (10.0, 0.0)]
    cubic = degree_elevation(quadratic)
    print(f"  二次: {quadratic}")
    print(f"  提高到三次: {cubic}")
    
    print("\n" + "=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  评估单个点: O(n²), n=控制点数")
    print("  采样 m 个点: O(m × n²)")
    print("  曲线分割: O(n²)")
    print("  优化：可用预处理达到 O(n) per point")
    print("  空间复杂度: O(n)")

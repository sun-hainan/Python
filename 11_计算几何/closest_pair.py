# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / closest_pair

本文件实现 closest_pair 相关的算法功能。
"""

import math
from typing import List, Tuple, Optional

Point = Tuple[float, float]


def euclidean_distance(p1: Point, p2: Point) -> float:
    """
    计算两点间的欧几里得距离
    
    Args:
        p1: 第一个点
        p2: 第二个点
    
    Returns:
        欧几里得距离
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx * dx + dy * dy)


def closest_pair_brute_force(points: List[Point]) -> Tuple[Point, Point, float]:
    """
    暴力法求最近点对（O(n^2)）
    
    作为基准函数，验证分治法结果
    
    Args:
        points: 点列表（至少2个点）
    
    Returns:
        (最近点1, 最近点2, 最小距离)
    """
    min_dist = float('inf')
    closest_pair: Tuple[Point, Point] = (points[0], points[1])
    
    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            dist = euclidean_distance(points[i], points[j])
            if dist < min_dist:
                min_dist = dist
                closest_pair = (points[i], points[j])
    
    return closest_pair[0], closest_pair[1], min_dist


def closest_pair_divide_and_conquer(points_x: List[Point], 
                                    points_y: List[Point]) -> Tuple[Point, Point, float]:
    """
    分治法求平面最近点对
    
    Args:
        points_x: 点列表（按x坐标排序）
        points_y: 点列表（按y坐标排序）
    
    Returns:
        (最近点1, 最近点2, 最小距离)
    
    复杂度：O(n log n)
    """
    n = len(points_x)
    
    # 基础情况：暴力法（点数量较少时）
    if n <= 3:
        return closest_pair_brute_force(points_x)
    
    # Step 1: 分割点集
    mid = n // 2
    mid_x = points_x[mid][0]  # 分割线的x坐标
    
    # 左半部分（按x排序）
    left_x = points_x[:mid]
    # 右半部分（按x排序）
    right_x = points_x[mid:]
    
    # 构建按y排序的左右半部分
    # 利用归并思想，避免每次O(n log n)排序
    left_y: List[Point] = []
    right_y: List[Point] = []
    for p in points_y:
        if p[0] < mid_x or (p[0] == mid_x and p in left_x):
            left_y.append(p)
        else:
            right_y.append(p)
    
    # Step 2: 递归求解左右两半
    (p1_left, p2_left, d_left) = closest_pair_divide_and_conquer(left_x, left_y)
    (p1_right, p2_right, d_right) = closest_pair_divide_and_conquer(right_x, right_y)
    
    # 取较小距离
    if d_left < d_right:
        d = d_left
        closest_pair = (p1_left, p2_left)
    else:
        d = d_right
        closest_pair = (p1_right, p2_right)
    
    # Step 3: 合并 - 在分割线附近查找更优解
    # 构建strip区域：距离分割线小于d的所有点（按y排序）
    strip: List[Point] = []
    for p in points_y:
        if abs(p[0] - mid_x) < d:
            strip.append(p)
    
    # 在strip中查找更近的点对
    strip_len = len(strip)
    for i in range(strip_len):
        # 每个点只需检查后续最多7个点（几何性质保证）
        j = i + 1
        count = 0
        while j < strip_len and count < 7:
            dist = euclidean_distance(strip[i], strip[j])
            if dist < d:
                d = dist
                closest_pair = (strip[i], strip[j])
            j += 1
            count += 1
    
    return closest_pair[0], closest_pair[1], d


def closest_pair(points: List[Point]) -> Tuple[Point, Point, float]:
    """
    平面最近点对求解入口函数
    
    预处理：按x坐标和y坐标分别排序
    然后调用分治法
    
    Args:
        points: 任意顺序的点列表
    
    Returns:
        (最近点1, 最近点2, 最小距离)
    
    复杂度：O(n log n)
    """
    if len(points) < 2:
        raise ValueError("需要至少2个点")
    
    # 分别按x和y坐标排序
    points_x = sorted(points, key=lambda p: (p[0], p[1]))
    points_y = sorted(points, key=lambda p: (p[1], p[0]))
    
    return closest_pair_divide_and_conquer(points_x, points_y)


def closest_pair_strip_optimized(points_x: List[Point], 
                                  points_y: List[Point], 
                                  d: float, 
                                  mid_x: float) -> Tuple[Point, Point, float]:
    """
    在strip区域内查找更近的点对（优化版）
    
    利用几何性质：对于strip中的任意点，只需检查其后7个y坐标更大的点
    
    Args:
        points_x: 按x排序的点列表
        points_y: 按y排序的点列表
        d: 当前最小距离
        mid_x: 分割线x坐标
    
    Returns:
        (最近点1, 最近点2, 最小距离)
    """
    # 构建strip区域
    strip: List[Point] = [p for p in points_y if abs(p[0] - mid_x) < d]
    
    min_dist = d
    closest_pair = (points_x[0], points_x[1])
    
    strip_len = len(strip)
    for i in range(strip_len):
        # 内层循环只需检查有限个点
        # 根据几何性质，距离小于d的点对中，y坐标差小于d
        # 且在任意deltaY宽度的带状区域内只有O(1)个点
        k = i + 1
        while k < strip_len and (strip[k][1] - strip[i][1])**2 < d**2:
            # 距离计算（避免开方，加速比较）
            dx = strip[k][0] - strip[i][0]
            dy = strip[k][1] - strip[i][1]
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < min_dist:
                min_dist = dist_sq
                closest_pair = (strip[i], strip[k])
            k += 1
    
    if min_dist == float('inf'):
        return closest_pair[0], closest_pair[1], d
    
    return closest_pair[0], closest_pair[1], math.sqrt(min_dist)


if __name__ == "__main__":
    import random
    
    # 测试用例1：简单点集
    test_points_1: List[Point] = [
        (2, 3), (12, 30), (40, 70), (5, 1), (12, 10), (3, 4)
    ]
    
    print("=== 测试1: 简单点集 ===")
    p1, p2, d = closest_pair(test_points_1)
    print(f"最近点对: {p1} - {p2}")
    print(f"最小距离: {d:.6f}")
    
    # 暴力验证
    p1_b, p2_b, d_b = closest_pair_brute_force(test_points_1)
    print(f"暴力验证: {p1_b} - {p2_b} = {d_b:.6f}")
    print(f"结果一致: {abs(d - d_b) < 1e-10}")
    
    # 测试用例2：大规模随机点集
    print("\n=== 测试2: 大规模随机点集 ===")
    random.seed(42)
    test_points_2: List[Point] = [(random.uniform(0, 1000), random.uniform(0, 1000)) 
                                   for _ in range(1000)]
    
    import time
    start = time.time()
    p1, p2, d = closest_pair(test_points_2)
    elapsed = time.time() - start
    print(f"点数: {len(test_points_2)}")
    print(f"最近点对: {p1} - {p2}")
    print(f"最小距离: {d:.6f}")
    print(f"耗时: {elapsed:.4f}秒")
    
    # 暴力验证（小规模）
    test_small = test_points_2[:50]
    p1_b, p2_b, d_b = closest_pair_brute_force(test_small)
    print(f"\n小规模暴力验证: {p1_b} - {p2_b} = {d_b:.6f}")
    
    # 测试用例3：对跖点（最坏情况）
    print("\n=== 测试3: 对跖点（圆形分布） ===")
    n = 100
    angle = [2 * math.pi * i / n for i in range(n)]
    test_points_3: List[Point] = [(math.cos(a) * 100, math.sin(a) * 100) for a in angle]
    
    p1, p2, d = closest_pair(test_points_3)
    print(f"最近点对: {p1} - {p2}")
    print(f"最小距离: {d:.6f}")
    
    # 可视化
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 图1：简单点集
    ax1 = axes[0]
    xs = [p[0] for p in test_points_1]
    ys = [p[1] for p in test_points_1]
    ax1.scatter(xs, ys, c='blue', s=50, zorder=5)
    ax1.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=2, label='最近点对')
    ax1.scatter([p1[0], p2[0]], [p1[1], p2[1]], c='red', s=150, marker='*', zorder=6)
    ax1.set_title("最近点对 - 简单点集")
    ax1.set_aspect('equal')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2：大规模点集（显示最近点对）
    ax2 = axes[1]
    xs = [p[0] for p in test_points_2]
    ys = [p[1] for p in test_points_2]
    ax2.scatter(xs, ys, c='blue', s=5, alpha=0.5)
    ax2.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=2, label='最近点对')
    ax2.scatter([p1[0], p2[0]], [p1[1], p2[1]], c='red', s=150, marker='*', zorder=6)
    ax2.set_title(f"最近点对 - 1000随机点")
    ax2.set_aspect('equal')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig("closest_pair.png", dpi=150)
    print("\n图像已保存至 closest_pair.png")
    plt.close()

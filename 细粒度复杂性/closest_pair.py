# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / closest_pair

本文件实现 closest_pair 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Optional


def brute_force_closest_pair(points: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
    """
    暴力算法:O(n²)
    
    Args:
        points: 点列表 [(x,y), ...]
    
    Returns:
        (点1, 点2, 最小距离)
    """
    n = len(points)
    if n < 2:
        return None, None, float('inf')
    
    min_dist = float('inf')
    best_pair = (None, None)
    
    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1])
            if d < min_dist:
                min_dist = d
                best_pair = (points[i], points[j])
    
    return best_pair[0], best_pair[1], min_dist


def closest_pair_divide_conquer(points: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
    """
    分治算法:O(n log n)
    1. 按x坐标排序
    2. 递归求左右两半的最近点对
    3. 合并:在中间带状区域找更近的点对
    
    Args:
        points: 点列表
    
    Returns:
        (点1, 点2, 最小距离)
    """
    n = len(points)
    if n <= 3:
        return brute_force_closest_pair(points)
    
    # 按x坐标排序
    points_sorted = sorted(points, key=lambda p: p[0])
    
    # 分成两半
    mid = n // 2
    mid_x = points_sorted[mid][0]
    
    # 递归求左右两半的最近点对
    p1, p2, d1 = closest_pair_divide_conquer(points_sorted[:mid])
    q1, q2, d2 = closest_pair_divide_conquer(points_sorted[mid:])
    
    # 取较小者
    if d1 < d2:
        min_dist = d1
        best_pair = (p1, p2)
    else:
        min_dist = d2
        best_pair = (q1, q2)
    
    # 在中间带状区域查找
    strip = [p for p in points_sorted if abs(p[0] - mid_x) < min_dist]
    
    # 按y坐标排序strip
    strip.sort(key=lambda p: p[1])
    
    # 检查strip中的点
    m = len(strip)
    for i in range(m):
        # 只需检查后面7个点(数学证明)
        for j in range(i + 1, min(i + 8, m)):
            d = math.hypot(strip[i][0] - strip[j][0], strip[i][1] - strip[j][1])
            if d < min_dist:
                min_dist = d
                best_pair = (strip[i], strip[j])
    
    return best_pair[0], best_pair[1], min_dist


def closest_pair_strip(points: List[Tuple[float, float]], d: float) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
    """
    在带状区域中找更近的点对
    
    Args:
        points: 已按y排序的点列表
        d: 当前最小距离
    
    Returns:
        (点1, 点2, 最小距离)
    """
    n = len(points)
    best = (None, None), (None, None), d
    
    for i in range(n):
        for j in range(i + 1, min(i + 8, n)):
            dy = points[j][1] - points[i][1]
            if dy >= d:
                break
            
            dx = points[j][0] - points[i][0]
            if dx < d:
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < d:
                    best = points[i], points[j], dist
    
    return best


def verify_closest_pair(points: List[Tuple[float, float]]) -> bool:
    """
    验证最近点对算法的正确性
    
    Args:
        points: 点列表
    
    Returns:
        是否正确
    """
    p1, p2, d = closest_pair_divide_conquer(points)
    
    # 用暴力算法验证
    bp1, bp2, bd = brute_force_closest_pair(points)
    
    return abs(d - bd) < 1e-9


# 测试代码
if __name__ == "__main__":
    import time
    
    # 测试1: 简单实例
    print("测试1 - 简单实例:")
    points1 = [(2, 3), (12, 30), (40, 50), (5, 1), (12, 10), (3, 4)]
    
    p1, p2, d = closest_pair_divide_conquer(points1)
    print(f"  点: {points1}")
    print(f"  最近点对: {p1} 和 {p2}")
    print(f"  距离: {d:.4f}")
    
    # 验证
    bp1, bp2, bd = brute_force_closest_pair(points1)
    print(f"  验证(暴力): {bp1} 和 {bp2}, 距离={bd:.4f}")
    print(f"  匹配: {abs(d - bd) < 1e-9}")
    
    # 测试2: 随机点
    print("\n测试2 - 随机点(100个):")
    random.seed(42)
    points2 = [(random.uniform(0, 1000), random.uniform(0, 1000)) for _ in range(100)]
    
    p1, p2, d = closest_pair_divide_conquer(points2)
    print(f"  最近点对: {p1} 和 {p2}")
    print(f"  距离: {d:.4f}")
    
    # 测试3: 性能对比
    print("\n测试3 - 性能对比:")
    for n in [100, 1000, 5000, 10000]:
        points = [(random.uniform(0, 10000), random.uniform(0, 10000)) for _ in range(n)]
        
        # 分治算法
        start = time.time()
        p1, p2, d = closest_pair_divide_conquer(points)
        time_divconq = time.time() - start
        
        print(f"  n={n}: 分治算法={time_divconq:.4f}s")
    
    # 测试4: 验证正确性
    print("\n测试4 - 正确性验证:")
    for n in [10, 50, 100]:
        points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n)]
        correct = verify_closest_pair(points)
        print(f"  n={n}: 正确={correct}")
    
    # 测试5: 特殊情况
    print("\n测试5 - 特殊情况:")
    # 共线点
    points_line = [(i, 0) for i in range(10)]
    p1, p2, d = closest_pair_divide_conquer(points_line)
    print(f"  共线点: 距离={d:.4f} (应为1)")
    
    # 网格点
    points_grid = [(i % 10, i // 10) for i in range(100)]
    p1, p2, d = closest_pair_divide_conquer(points_grid)
    print(f"  网格点(10x10): 距离={d:.4f} (应为1)")
    
    print("\n所有测试完成!")

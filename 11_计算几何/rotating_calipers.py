# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / rotating_calipers

本文件实现 rotating_calipers 相关的算法功能。
"""

import math
from typing import List, Tuple

Point = Tuple[float, float]


def cross_product(o: Point, a: Point, b: Point) -> float:
    """
    计算向量OA和OB的叉积
    
    Args:
        o: 公共原点
        a: 向量终点A
        b: 向量终点B
    
    Returns:
        叉积的Z分量（正值表示a在b的逆时针方向）
    """
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def monotone_chain_convex_hull(points: List[Point]) -> List[Point]:
    """
    单调链算法计算凸包（上凸包+下凸包）
    
    Args:
        points: 输入点集
    
    Returns:
        凸包上的点列表（逆时针顺序，不包含最后一个重复点）
    
    复杂度：O(n log n)
    """
    if len(points) <= 1:
        return list(points)
    
    # 按x坐标排序，x相同则按y坐标排序
    sorted_points = sorted(points, key=lambda p: (p[0], p[1]))
    
    # 构建下凸包
    lower: List[Point] = []
    for p in sorted_points:
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    # 构建上凸包
    upper: List[Point] = []
    for p in reversed(sorted_points):
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    # 移除重复端点
    lower.pop()
    upper.pop()
    
    return lower + upper


def rotating_calipers_diameter(convex_hull: List[Point]) -> Tuple[Point, Point, float]:
    """
    使用旋转卡壳算法求凸包的最远点对（直径）
    
    算法思路：
        1. 找到凸包上y值最低和最高的两个点（对跖点对的初始候选）
        2. 以这两点为初始卡壳位置
        3. 旋转卡壳，保持两条平行切线
        4. 在旋转过程中跟踪最大距离的两个点
    
    Args:
        convex_hull: 凸包上的点列表（逆时针顺序）
    
    Returns:
        (最远点1, 最远点2, 最大距离)
    
    复杂度：O(n)
    """
    n = len(convex_hull)
    if n == 2:
        d = math.sqrt((convex_hull[0][0] - convex_hull[1][0])**2 + 
                     (convex_hull[0][1] - convex_hull[1][1])**2)
        return convex_hull[0], convex_hull[1], d
    
    # 找到y值最低和最高的点（作为初始卡壳）
    y_min_idx = 0
    y_max_idx = 0
    for i in range(n):
        if convex_hull[i][1] < convex_hull[y_min_idx][1]:
            y_min_idx = i
        if convex_hull[i][1] > convex_hull[y_max_idx][1]:
            y_max_idx = i
    
    # 初始化最大距离
    max_dist = 0.0
    max_pair: Tuple[Point, Point] = (convex_hull[0], convex_hull[1])
    
    # 初始化卡壳角度
    i = y_min_idx
    j = y_max_idx
    
    # 旋转卡壳主循环
    while True:
        # 计算当前边向量
        edge_i = (convex_hull[(i + 1) % n][0] - convex_hull[i][0],
                  convex_hull[(i + 1) % n][1] - convex_hull[i][1])
        edge_j = (convex_hull[(j + 1) % n][0] - convex_hull[j][0],
                  convex_hull[(j + 1) % n][1] - convex_hull[j][1])
        
        # 计算两个边的法向量（在2D中为垂直向量）
        # 选择能够向外旋转的方向
        normal_i = (-edge_i[1], edge_i[0])
        normal_j = (-edge_j[1], edge_j[0])
        
        # 计算点到直线的距离，确定旋转角度
        # 使用叉积计算有向面积
        area_i = abs(cross_product(convex_hull[i], convex_hull[(i + 1) % n], convex_hull[j]))
        area_j = abs(cross_product(convex_hull[j], convex_hull[(j + 1) % n], convex_hull[i]))
        
        # 选择旋转角度较小的边
        len_i = math.sqrt(edge_i[0]**2 + edge_i[1]**2)
        len_j = math.sqrt(edge_j[0]**2 + edge_j[1]**2)
        
        # 计算需要旋转的角度（用sin近似）
        sin_i = area_i / (len_i * math.sqrt((convex_hull[j][0] - convex_hull[i][0])**2 + 
                                           (convex_hull[j][1] - convex_hull[i][1])**2))
        sin_j = area_j / (len_j * math.sqrt((convex_hull[i][0] - convex_hull[j][0])**2 + 
                                           (convex_hull[i][1] - convex_hull[j][1])**2))
        
        # 更新最大距离（检查当前点对）
        for p_idx in [i, j]:
            for q_idx in range(n):
                d = math.sqrt((convex_hull[p_idx][0] - convex_hull[q_idx][0])**2 +
                             (convex_hull[p_idx][1] - convex_hull[q_idx][1])**2)
                if d > max_dist:
                    max_dist = d
                    max_pair = (convex_hull[p_idx], convex_hull[q_idx])
        
        # 判断是否完成旋转（一周回到起始位置）
        if i == y_min_idx and j == y_max_idx:
            break
        
        # 移动到下一个顶点
        if sin_i < sin_j:
            i = (i + 1) % n
        else:
            j = (j + 1) % n
    
    return max_pair[0], max_pair[1], max_dist


def rotating_calipers_min_width(convex_hull: List[Point]) -> float:
    """
    使用旋转卡壳算法求凸包的最小宽度
    
    最小宽度定义为凸包在任意方向上的投影的最小长度。
    等价于凸包的最小外接矩形的短边长度。
    
    算法思路：
        1. 对每条凸包边，计算与其平行的两条支撑线
        2. 找到与该边垂直方向上距离最远的两点
        3. 取所有方向中的最小宽度
    
    Args:
        convex_hull: 凸包上的点列表（逆时针顺序）
    
    Returns:
        最小宽度值
    
    复杂度：O(n)
    """
    n = len(convex_hull)
    if n < 3:
        return 0.0
    
    min_width = float('inf')
    
    # j是对边上的点，初始在对跖方向
    j = 1
    
    for i in range(n):
        # 当前边
        edge = convex_hull[(i + 1) % n]
        
        # 找到与当前边垂直方向上距离最远的点
        while True:
            next_j = (j + 1) % n
            # 计算当前边与点到直线距离的比值
            x1, y1 = convex_hull[i]
            x2, y2 = convex_hull[(i + 1) % n]
            x3, y3 = convex_hull[j]
            x4, y4 = convex_hull[next_j]
            
            # 计算点到直线的距离
            dist_j = abs((y2 - y1) * x3 - (x2 - x1) * y3 + x2 * y1 - y2 * x1)
            dist_next = abs((y2 - y1) * x4 - (x2 - x1) * y4 + x2 * y1 - y2 * x1)
            
            if dist_next > dist_j:
                j = next_j
            else:
                break
        
        # 计算当前边对应的宽度
        # 使用向量叉积计算距离
        x1, y1 = convex_hull[i]
        x2, y2 = convex_hull[(i + 1) % n]
        x3, y3 = convex_hull[j]
        
        # 点到直线的距离
        edge_len = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if edge_len > 0:
            dist = abs((x2 - x1) * (y1 - y3) - (x1 - x3) * (y2 - y1)) / edge_len
            min_width = min(min_width, dist)
    
    return min_width


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    
    # 测试点集（凸包形状）
    test_points: List[Point] = [
        (0, 0), (4, 0), (5, 3), (4, 5), (2, 5), (0, 3), (1, 1.5), (3, 1.5)
    ]
    
    print("=== 旋转卡壳算法测试 ===")
    print(f"输入点数: {len(test_points)}")
    
    # 计算凸包
    hull = monotone_chain_convex_hull(test_points)
    print(f"凸包点数: {len(hull)}")
    print(f"凸包顶点: {hull}")
    
    # 求最远点对（直径）
    p1, p2, diameter = rotating_calipers_diameter(hull)
    print(f"\n最远点对: {p1} - {p2}")
    print(f"直径: {diameter:.4f}")
    
    # 求最小宽度
    min_width = rotating_calipers_min_width(hull)
    print(f"\n最小宽度: {min_width:.4f}")
    
    # 绘制凸包和最远点对
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    
    # 绘制凸包边
    hull_closed = hull + [hull[0]]
    hull_xs = [p[0] for p in hull_closed]
    hull_ys = [p[1] for p in hull_closed]
    ax.plot(hull_xs, hull_ys, 'b-', linewidth=1.5, label='凸包')
    
    # 绘制最远点对连线
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r--', linewidth=2, label=f'直径={diameter:.2f}')
    
    # 绘制站点
    ax.scatter([p[0] for p in test_points], [p[1] for p in test_points], 
               c='blue', s=50, zorder=5)
    
    # 标注最远点对
    ax.scatter([p1[0], p2[0]], [p1[1], p2[1]], c='red', s=150, zorder=6, marker='*')
    ax.annotate(f'p1({p1[0]:.1f},{p1[1]:.1f})', p1, textcoords="offset points", xytext=(10, 10))
    ax.annotate(f'p2({p2[0]:.1f},{p2[1]:.1f})', p2, textcoords="offset points", xytext=(10, 10))
    
    ax.set_title("旋转卡壳算法 - 最远点对")
    ax.set_aspect('equal')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("rotating_calipers.png", dpi=150)
    print("\n图像已保存至 rotating_calipers.png")
    plt.close()

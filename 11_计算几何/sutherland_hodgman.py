# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / sutherland_hodgman

本文件实现 sutherland_hodgman 相关的算法功能。
"""

from typing import List, Tuple

Point = Tuple[float, float]
Polygon = List[Point]
Rect = Tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)


def clip_polygon_by_edge(polygon: Polygon, edge_start: Point, 
                          edge_end: Point, keep_inside: bool = True) -> Polygon:
    """
    按单条有向边裁剪多边形
    
    Sutherland-Hodgman算法的核心步骤：
    使用有向边将平面划分为"内侧"和"外侧"，
    然后根据端点位置决定是否保留顶点。
    
    边界判断规则：
        S(始点)在内且E(末点)在内：输出E
        S在内且E在外：输出边界交点I
        S在外且E在内：输出I和E
        S,E都在外：不输出
    
    Args:
        polygon: 待裁剪多边形顶点列表
        edge_start: 有向边起点
        edge_end: 有向边终点
        keep_inside: True则保留有向边左侧（内侧），False则保留右侧
    
    Returns:
        裁剪后的多边形顶点列表
    
    复杂度：O(n)
    """
    if len(polygon) == 0:
        return []
    
    output_polygon: Polygon = []
    n = len(polygon)
    
    for i in range(n):
        # 当前边：S -> E
        s = polygon[i]
        e = polygon[(i + 1) % n]
        
        # 计算S和E相对于有向边的位置
        # 使用叉积判断：cross > 0 表示点在外侧（右侧），< 0 表示内侧（左侧）
        def side(p: Point) -> float:
            """计算点相对于有向边的叉积（> 0 外侧, < 0 内侧）"""
            return (edge_end[0] - edge_start[0]) * (p[1] - edge_start[1]) - \
                   (edge_end[1] - edge_start[1]) * (p[0] - edge_start[0])
        
        s_side = side(s)
        e_side = side(e)
        
        # 如果keep_inside=True，内侧对应 side < 0
        s_inside = s_side < 0 if keep_inside else s_side > 0
        e_inside = e_side < 0 if keep_inside else e_side > 0
        
        if s_inside and e_inside:
            # 情况1：S在内,E在内 → 输出E
            output_polygon.append(e)
        
        elif s_inside and not e_inside:
            # 情况2：S在内,E在外 → 输出交点I
            if abs(s_side - e_side) > 1e-10:
                t = s_side / (s_side - e_side)
                intersection: Point = (
                    s[0] + t * (e[0] - s[0]),
                    s[1] + t * (e[1] - s[1])
                )
                output_polygon.append(intersection)
        
        elif not s_inside and e_inside:
            # 情况3：S在外,E在内 → 输出交点I和E
            if abs(s_side - e_side) > 1e-10:
                t = s_side / (s_side - e_side)
                intersection = (
                    s[0] + t * (e[0] - s[0]),
                    s[1] + t * (e[1] - s[1])
                )
                output_polygon.append(intersection)
            output_polygon.append(e)
        
        # 情况4：S,E都在外 → 不输出
    
    return output_polygon


def sutherland_hodgman_clip(polygon: Polygon, rect: Rect) -> Polygon:
    """
    Sutherland-Hodgman多边形裁剪主函数
    
    依次按左、右、下、上四条边界进行裁剪
    
    Args:
        polygon: 输入多边形顶点列表（顺时针或逆时针均可）
        rect: 裁剪窗口 (xmin, ymin, xmax, ymax)
    
    Returns:
        裁剪后的多边形顶点列表
    
    复杂度：O(n)，n为多边形顶点数
    """
    xmin, ymin, xmax, ymax = rect
    
    # 依次按四条边界裁剪
    # 注意边的方向：内侧是左侧
    # 左边界：从(0,0)到(0,1)，内侧在上方
    left_edge_start: Point = (xmin, ymin)
    left_edge_end: Point = (xmin, ymax)
    
    # 右边界：从(xmax,0)到(xmax,ymin)，内侧在下方
    right_edge_start: Point = (xmax, ymin)
    right_edge_end: Point = (xmax, ymax)
    
    # 下边界：从(0,0)到(xmax,0)，内侧在上方
    bottom_edge_start: Point = (xmin, ymin)
    bottom_edge_end: Point = (xmax, ymin)
    
    # 上边界：从(xmax,ymax)到(0,ymax)，内侧在下方
    top_edge_start: Point = (xmax, ymax)
    top_edge_end: Point = (xmin, ymax)
    
    # 逐边裁剪
    result = clip_polygon_by_edge(polygon, left_edge_start, left_edge_end, keep_inside=True)
    result = clip_polygon_by_edge(result, right_edge_start, right_edge_end, keep_inside=True)
    result = clip_polygon_by_edge(result, bottom_edge_start, bottom_edge_end, keep_inside=True)
    result = clip_polygon_by_edge(result, top_edge_start, top_edge_end, keep_inside=True)
    
    return result


def convex_polygon_clip(polygon: Polygon, clip_window: Polygon) -> Polygon:
    """
    通用凸多边形裁剪（支持任意凸裁剪窗口）
    
    将Sutherland-Hodgman推广到任意凸多边形窗口
    
    Args:
        polygon: 输入多边形
        clip_window: 凸裁剪窗口多边形（顺时针或逆时针）
    
    Returns:
        裁剪后的多边形
    
    复杂度：O(n * m)，n为输入顶点数，m为裁剪窗口边数
    """
    if len(polygon) == 0 or len(clip_window) < 3:
        return []
    
    result = polygon
    
    # 依次按裁剪窗口的每条边裁剪
    m = len(clip_window)
    for i in range(m):
        if len(result) == 0:
            return []
        edge_start = clip_window[i]
        edge_end = clip_window[(i + 1) % m]
        result = clip_polygon_by_edge(result, edge_start, edge_end, keep_inside=True)
    
    return result


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    
    # 定义裁剪窗口
    clip_rect: Rect = (2, 2, 6, 5)
    
    # 定义输入多边形（凹多边形，穿越多个边界）
    test_polygon: Polygon = [
        (0, 0), (4, 0), (4, 2), (8, 2), (8, 6), (4, 6), (4, 4), (0, 4)
    ]
    
    print("=== Sutherland-Hodgman多边形裁剪测试 ===")
    print(f"裁剪窗口: {clip_rect}")
    print(f"输入多边形: {test_polygon}")
    
    # 执行裁剪
    clipped = sutherland_hodgman_clip(test_polygon, clip_rect)
    print(f"裁剪后顶点数: {len(clipped)}")
    print(f"裁剪后多边形: {clipped}")
    
    # 绘制结果
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    
    # 图1：原始多边形和裁剪窗口
    ax1 = axes[0]
    
    # 绘制裁剪窗口
    xmin, ymin, xmax, ymax = clip_rect
    window = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                               linewidth=2, edgecolor='black', 
                               facecolor='lightgray', alpha=0.3)
    ax1.add_patch(window)
    
    # 绘制输入多边形
    poly_closed = test_polygon + [test_polygon[0]]
    poly_xs = [p[0] for p in poly_closed]
    poly_ys = [p[1] for p in poly_closed]
    ax1.plot(poly_xs, poly_ys, 'b-', linewidth=2, label='输入多边形')
    ax1.fill(poly_xs[:-1], poly_ys[:-1], alpha=0.2, color='blue')
    
    # 标注顶点
    for idx, p in enumerate(test_polygon):
        ax1.annotate(str(idx), p, textcoords="offset points", xytext=(5, 5), fontsize=9)
    
    ax1.scatter([p[0] for p in test_polygon], [p[1] for p in test_polygon], 
               c='blue', s=50, zorder=5)
    
    ax1.set_xlim(-1, 9)
    ax1.set_ylim(-1, 7)
    ax1.set_aspect('equal')
    ax1.set_title("裁剪前")
    ax1.grid(True, alpha=0.3)
    
    # 图2：裁剪后的多边形
    ax2 = axes[1]
    
    # 绘制裁剪窗口
    window2 = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                  linewidth=2, edgecolor='black', 
                                  facecolor='lightgray', alpha=0.3)
    ax2.add_patch(window2)
    
    # 绘制裁剪后的多边形
    if len(clipped) > 0:
        clipped_closed = clipped + [clipped[0]]
        clipped_xs = [p[0] for p in clipped_closed]
        clipped_ys = [p[1] for p in clipped_closed]
        ax2.plot(clipped_xs, clipped_ys, 'r-', linewidth=2, label='裁剪后多边形')
        ax2.fill(clipped_xs[:-1], clipped_ys[:-1], alpha=0.3, color='red')
        ax2.scatter([p[0] for p in clipped], [p[1] for p in clipped], 
                   c='red', s=50, zorder=5)
        
        # 标注新顶点
        for idx, p in enumerate(clipped):
            ax2.annotate(str(idx), p, textcoords="offset points", xytext=(5, 5), fontsize=9)
    
    ax2.set_xlim(-1, 9)
    ax2.set_ylim(-1, 7)
    ax2.set_aspect('equal')
    ax2.set_title("裁剪后")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("sutherland_hodgman.png", dpi=150)
    print("\n图像已保存至 sutherland_hodgman.png")
    plt.close()

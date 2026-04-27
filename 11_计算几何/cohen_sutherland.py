# -*- coding: utf-8 -*-

"""

算法实现：11_计算几何 / cohen_sutherland



本文件实现 cohen_sutherland 相关的算法功能。

"""



import math

from typing import List, Tuple, Optional



Point = Tuple[float, float]

Rect = Tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)





# 区域码位标志定义

LEFT_BIT = 1      # 0b0001 - 左侧

RIGHT_BIT = 2     # 0b0010 - 右侧

BOTTOM_BIT = 4    # 0b0100 - 下方

TOP_BIT = 8       # 0b1000 - 上方





def compute_region_code(point: Point, rect: Rect) -> int:

    """

    计算点的区域码（Cohen-Sutherland编码）

    

    区域码用4位二进制表示，每位对应一个方向：

    | TOP | BOTTOM | RIGHT | LEFT |

    

    Args:

        point: 待编码点 (x, y)

        rect: 裁剪窗口 (xmin, ymin, xmax, ymax)

    

    Returns:

        4位区域码

    

    示例：

        0b0000 = 0  → 点在窗口内

        0b0001 = 1  → 点在左侧

        0b1010 = 10 → 点在上方和右侧

    """

    xmin, ymin, xmax, ymax = rect

    x, y = point

    

    code = 0

    

    # 检查左侧 (x < xmin)

    if x < xmin:

        code |= LEFT_BIT

    

    # 检查右侧 (x > xmax)

    if x > xmax:

        code |= RIGHT_BIT

    

    # 检查下方 (y < ymin)

    if y < ymin:

        code |= BOTTOM_BIT

    

    # 检查上方 (y > ymax)

    if y > ymax:

        code |= TOP_BIT

    

    return code





def cohen_sutherland_clip(p1: Point, p2: Point, rect: Rect) -> Optional[Tuple[Point, Point]]:

    """

    Cohen-Sutherland直线裁剪主函数

    

    算法流程：

        1. 计算两端点的区域码

        2. 两端点全0 → 完全在窗口内，直接返回

        3. 两端点区域码按位与非0 → 完全在窗口外，返回None

        4. 否则，按边界裁剪线段，重复直到完成或舍弃

    

    Args:

        p1: 线段起点 (x1, y1)

        p2: 线段终点 (x2, y2)

        rect: 裁剪窗口 (xmin, ymin, xmax, ymax)

    

    Returns:

        裁剪后的线段端点，或None（如果线段完全不可见）

    

    复杂度：O(1)

    """

    xmin, ymin, xmax, ymax = rect

    

    # Step 1: 计算两端点的区域码

    code1 = compute_region_code(p1, rect)

    code2 = compute_region_code(p2, rect)

    

    # 无限循环，正常情况下最多4次迭代后退出

    while True:

        # Step 2: 两端点都在窗口内（区域码全0）

        if code1 == 0 and code2 == 0:

            return p1, p2

        

        # Step 3: 两端点都在窗口外（区域码按位与非0）

        if code1 & code2 != 0:

            return None

        

        # Step 4: 选择一个在窗口外的端点进行裁剪

        if code1 != 0:

            code_out = code1

        else:

            code_out = code2

        

        # 计算交点

        x, y = p1[0], p1[1]

        x1, y1 = p1

        x2, y2 = p2

        

        # 根据code_out确定与哪条边界相交

        # 计算斜率（避免除零）

        if x2 != x1:

            slope = (y2 - y1) / (x2 - x1)

        else:

            slope = float('inf')

        

        # 与左边界相交 (x = xmin)

        if code_out & LEFT_BIT:

            y = y1 + slope * (xmin - x1)

            x = xmin

        # 与右边界相交 (x = xmax)

        elif code_out & RIGHT_BIT:

            y = y1 + slope * (xmax - x1)

            x = xmax

        # 与下边界相交 (y = ymin)

        elif code_out & BOTTOM_BIT:

            if slope != 0:

                x = x1 + (ymin - y1) / slope

            else:

                x = x1

            y = ymin

        # 与上边界相交 (y = ymax)

        elif code_out & TOP_BIT:

            if slope != 0:

                x = x1 + (ymax - y1) / slope

            else:

                x = x1

            y = ymax

        

        # 用交点替换窗口外的端点

        if code_out == code1:

            p1 = (x, y)

            code1 = compute_region_code(p1, rect)

        else:

            p2 = (x, y)

            code2 = compute_region_code(p2, rect)





def liang_barsky_clip(p1: Point, p2: Point, rect: Rect) -> Optional[Tuple[Point, Point]]:

    """

    Liang-Barsky直线裁剪算法（参数化Cohen-Sutherland的改进版）

    

    算法使用参数化表示线段：

        P(t) = P1 + t * (P2 - P1), t ∈ [0, 1]

    

    通过求解不等式约束得到裁剪结果

    

    Args:

        p1: 线段起点

        p2: 线段终点

        rect: 裁剪窗口

    

    Returns:

        裁剪后的线段端点，或None

    

    复杂度：O(1)

    """

    xmin, ymin, xmax, ymax = rect

    

    # 线段参数方程的增量

    dx = p2[0] - p1[0]

    dy = p2[1] - p1[1]

    

    # 参数t的初始范围

    t0 = 0.0

    t1 = 1.0

    

    # 对四条边界进行裁剪

    # 左侧

    if dx != 0:

        p = -dx

        q = x1 = p1[0] - xmin

    else:

        p = 0

        q = x1

    

    if p < 0:

        r = q / p if p != 0 else float('inf')

        if r > t1:

            return None

        if r > t0:

            t0 = r

    elif p > 0:

        r = q / p if p != 0 else float('inf')

        if r < t0:

            return None

        if r < t1:

            t1 = r

    else:

        if q < 0:

            return None

    

    # 右侧

    if dx != 0:

        p = dx

        q = xmax - p1[0]

    else:

        p = 0

        q = xmax - p1[0]

    

    if p < 0:

        r = q / p if p != 0 else float('inf')

        if r > t1:

            return None

        if r > t0:

            t0 = r

    elif p > 0:

        r = q / p if p != 0 else float('inf')

        if r < t0:

            return None

        if r < t1:

            t1 = r

    else:

        if q < 0:

            return None

    

    # 下方

    if dy != 0:

        p = -dy

        q = y1 = p1[1] - ymin

    else:

        p = 0

        q = y1

    

    if p < 0:

        r = q / p if p != 0 else float('inf')

        if r > t1:

            return None

        if r > t0:

            t0 = r

    elif p > 0:

        r = q / p if p != 0 else float('inf')

        if r < t0:

            return None

        if r < t1:

            t1 = r

    else:

        if q < 0:

            return None

    

    # 上方

    if dy != 0:

        p = dy

        q = ymax - p1[1]

    else:

        p = 0

        q = ymax - p1[1]

    

    if p < 0:

        r = q / p if p != 0 else float('inf')

        if r > t1:

            return None

        if r > t0:

            t0 = r

    elif p > 0:

        r = q / p if p != 0 else float('inf')

        if r < t0:

            return None

        if r < t1:

            t1 = r

    else:

        if q < 0:

            return None

    

    # 计算裁剪后的端点

    if t0 < 1.0 and t0 > 0.0:

        clipped_p1 = (p1[0] + t0 * dx, p1[1] + t0 * dy)

    else:

        clipped_p1 = p1

    

    if t1 < 1.0 and t1 > 0.0:

        clipped_p2 = (p1[0] + t1 * dx, p1[1] + t1 * dy)

    else:

        clipped_p2 = p2

    

    return clipped_p1, clipped_p2





if __name__ == "__main__":

    import matplotlib.pyplot as plt

    import matplotlib.patches as patches

    

    # 定义裁剪窗口

    clip_rect: Rect = (1, 1, 5, 4)

    

    # 测试线段

    test_segments: List[Tuple[Point, Point, str]] = [

        ((0, 2), (6, 2), "水平穿越"),

        ((2, 0), (2, 5), "垂直穿越"),

        ((0, 0), (6, 5), "对角线穿越"),

        ((0, 2.5), (6, 2.5), "水平在内部y"),

        ((-1, -1), (-0.5, -0.5), "完全在外侧-1"),

        ((3, 2), (3, 2), "点在线上"),

        ((0.5, 0.5), (5.5, 4.5), "部分在内部"),

        ((-1, 2), (0.5, 2), "端点在边界"),

    ]

    

    print("=== Cohen-Sutherland直线裁剪测试 ===")

    print(f"裁剪窗口: {clip_rect}")

    

    # 绘制设置

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    

    # 绘制裁剪窗口

    xmin, ymin, xmax, ymax = clip_rect

    window = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,

                                linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.3)

    ax.add_patch(window)

    

    colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'cyan']

    

    for idx, (p1, p2, desc) in enumerate(test_segments):

        result = cohen_sutherland_clip(p1, p2, clip_rect)

        

        print(f"\n线段 {idx + 1}: {p1} → {p2} ({desc})")

        if result is not None:

            c_p1, c_p2 = result

            print(f"  裁剪结果: {c_p1} → {c_p2}")

            

            # 绘制原线段（虚线）

            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], linestyle='--', 

                    color=colors[idx % len(colors)], linewidth=1, alpha=0.5)

            

            # 绘制裁剪后的线段（实线）

            ax.plot([c_p1[0], c_p2[0]], [c_p1[1], c_p2[1]], 

                    color=colors[idx % len(colors)], linewidth=2.5,

                    label=f'{idx + 1}: {desc}')

        else:

            print(f"  裁剪结果: 无交集（完全裁剪掉）")

            

            # 仅绘制虚线（表示被完全裁剪）

            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], linestyle=':', 

                    color=colors[idx % len(colors)], linewidth=1, alpha=0.3)

    

    # 标注区域码

    for x in [xmin - 0.3, xmax + 0.3]:

        for y in [ymin - 0.3, ymax + 0.3]:

            ax.annotate('1' if x < xmin else ('0' if x < xmax else '1'), 

                       (x, ymin + (ymax - ymin) / 2), fontsize=12, ha='center')

    

    ax.set_xlim(-2, 7)

    ax.set_ylim(-2, 6)

    ax.set_aspect('equal')

    ax.set_title("Cohen-Sutherland直线裁剪\n虚线=原线段, 实线=裁剪后")

    ax.legend(loc='upper right')

    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig("cohen_sutherland.png", dpi=150)

    print("\n图像已保存至 cohen_sutherland.png")

    plt.close()


# -*- coding: utf-8 -*-

"""

算法实现：11_计算几何 / line_intersection



本文件实现 line_intersection 相关的算法功能。

"""



import math

from typing import Tuple, Optional



Point = Tuple[float, float]

Segment = Tuple[Point, Point]





def cross_product(o: Point, a: Point, b: Point) -> float:

    """

    计算向量OA和OB的叉积（Z分量）

    

    物理意义：叉积的符号表示a相对于b的方向

    - > 0：a在b的逆时针方向（左转）

    - < 0：a在b的顺时针方向（右转）

    - = 0：a与b共线

    

    Args:

        o: 公共原点

        a: 向量终点A

        b: 向量终点B

    

    Returns:

        叉积的Z分量

    """

    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])





def on_segment(p: Point, q: Point, r: Point) -> bool:

    """

    判断点q是否在线段pr上

    

    用于处理共线且端点重合的边界情况

    

    Args:

        p: 线段起点

        q: 待检测点

        r: 线段终点

    

    Returns:

        True if q is on segment pr

    """

    return (min(p[0], r[0]) - 1e-10 <= q[0] <= max(p[0], r[0]) + 1e-10 and

            min(p[1], r[1]) - 1e-10 <= q[1] <= max(p[1], r[1]) + 1e-10)





def segments_intersect(seg1: Segment, seg2: Segment) -> bool:

    """

    判断两条线段是否相交（快速算法）

    

    算法流程：

        1. 快速排斥实验：检查AABB是否相交

        2. 跨立实验：检查两条线段是否相互跨立

    

    Args:

        seg1: 第一条线段 ((x1, y1), (x2, y2))

        seg2: 第二条线段 ((x3, y3), (x4, y4))

    

    Returns:

        True if segments intersect

    

    复杂度：O(1)

    """

    p1, p2 = seg1

    p3, p4 = seg2

    

    # 线段1的端点坐标

    x1, y1 = p1

    x2, y2 = p2

    # 线段2的端点坐标

    x3, y3 = p3

    x4, y4 = p4

    

    # Step 1: 快速排斥实验

    # 检查两条线段的AABB是否相交

    if max(min(x1, x2), min(x3, x4)) > min(max(x1, x2), max(x3, x4)):

        return False  # x轴方向不相交

    if max(min(y1, y2), min(y3, y4)) > min(max(y1, y2), max(y3, y4)):

        return False  # y轴方向不相交

    

    # Step 2: 跨立实验

    # 检查线段1是否跨立线段2

    cross1 = cross_product(p3, p4, p1)

    cross2 = cross_product(p3, p4, p2)

    cross3 = cross_product(p1, p2, p3)

    cross4 = cross_product(p1, p2, p4)

    

    # 跨立条件：叉积符号相反（允许共线情况）

    if cross1 * cross2 < 0 and cross3 * cross4 < 0:

        return True

    

    # 处理共线情况（端点在线段上）

    if abs(cross1) < 1e-10 and on_segment(p3, p1, p4):

        return True

    if abs(cross2) < 1e-10 and on_segment(p3, p2, p4):

        return True

    if abs(cross3) < 1e-10 and on_segment(p1, p3, p2):

        return True

    if abs(cross4) < 1e-10 and on_segment(p1, p4, p2):

        return True

    

    return False





def compute_intersection(seg1: Segment, seg2: Segment) -> Optional[Point]:

    """

    计算两条线段的交点（假设它们相交）

    

    使用参数化方程求解：

        线段1: P = p1 + t * (p2 - p1)

        线段2: P = p3 + u * (p4 - p3)

    

    解方程组得到t和u，然后计算交点

    

    Args:

        seg1: 第一条线段

        seg2: 第二条线段

    

    Returns:

        交点坐标，如果线段平行则返回None

    

    复杂度：O(1)

    """

    p1, p2 = seg1

    p3, p4 = seg2

    

    x1, y1 = p1

    x2, y2 = p2

    x3, y3 = p3

    x4, y4 = p4

    

    # 计算系数

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    

    # 检查是否平行（共线）

    if abs(denom) < 1e-10:

        return None

    

    # 计算交点（使用克莱姆法则的变形）

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / -denom

    

    # 验证交点在线段范围内（浮点误差容许）

    if 0 <= t <= 1 and 0 <= u <= 1:

        intersection: Point = (

            x1 + t * (x2 - x1),

            y1 + t * (y2 - y1)

        )

        return intersection

    

    return None





def line_intersection_point(seg1: Segment, seg2: Segment) -> Optional[Point]:

    """

    求两条直线（非线段）的交点

    

    与compute_intersection不同，这里不要求交点在线段范围内

    

    Args:

        seg1: 第一条线段

        seg2: 第二条线段

    

    Returns:

        交点坐标，平行则返回None

    """

    p1, p2 = seg1

    p3, p4 = seg2

    

    x1, y1 = p1

    x2, y2 = p2

    x3, y3 = p3

    x4, y4 = p4

    

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    

    if abs(denom) < 1e-10:

        return None  # 平行或重合

    

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

    

    return (

        x1 + t * (x2 - x1),

        y1 + t * (y2 - y1)

    )





def segment_intersections(segments: List[Segment]) -> List[Tuple[Segment, Segment, Point]]:

    """

    找出所有相交的线段对及其交点

    

    O(n^2)暴力枚举，用于小规模场景

    

    Args:

        segments: 线段列表

    

    Returns:

        列表，每个元素为 (线段1, 线段2, 交点)

    

    复杂度：O(n^2)

    """

    results: List[Tuple[Segment, Segment, Point]] = []

    n = len(segments)

    

    for i in range(n):

        for j in range(i + 1, n):

            seg1 = segments[i]

            seg2 = segments[j]

            

            if segments_intersect(seg1, seg2):

                intersection = compute_intersection(seg1, seg2)

                if intersection is not None:

                    results.append((seg1, seg2, intersection))

    

    return results





if __name__ == "__main__":

    import matplotlib.pyplot as plt

    

    # 测试线段

    test_cases: List[Tuple[Segment, Segment, str, bool]] = [

        (((0, 0), (4, 4)), ((0, 4), (4, 0)), "对角线交叉", True),

        (((0, 0), (2, 2)), ((3, 3), (5, 5)), "共线但不重叠", False),

        (((0, 0), (4, 0)), ((2, 0), (6, 0)), "共线且重叠", True),

        (((0, 0), (1, 1)), ((1, 0), (2, 1)), "端点相交", True),

        (((0, 0), (3, 3)), ((3, 3), (6, 0)), "T形相交", True),

        (((0, 0), (1, 1)), ((2, 2), (3, 3)), "分离线段", False),

        (((0, 0), (5, 0)), ((2, 2), (2, -2)), "垂直相交", True),

        (((0, 0), (4, 0)), ((1, 2), (3, 2)), "水平平行不相交", False),

    ]

    

    print("=== 线段相交检测测试 ===")

    

    all_pass = True

    for seg1, seg2, desc, expected in test_cases:

        result = segments_intersect(seg1, seg2)

        intersection = compute_intersection(seg1, seg2) if result else None

        

        status = "✓" if result == expected else "✗"

        if result != expected:

            all_pass = False

        

        print(f"{status} {desc}")

        print(f"   线段1: {seg1[0]} → {seg1[1]}")

        print(f"   线段2: {seg2[0]} → {seg2[1]}")

        print(f"   相交: {result} (期望: {expected})")

        if intersection:

            print(f"   交点: ({intersection[0]:.4f}, {intersection[1]:.4f})")

        print()

    

    print(f"测试结果: {'全部通过' if all_pass else '存在失败'}")

    

    # 绘制测试线段

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    

    colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'cyan']

    

    for idx, (seg1, seg2, desc, expected) in enumerate(test_cases):

        color = colors[idx % len(colors)]

        p1, p2 = seg1

        p3, p4 = seg2

        

        # 绘制线段

        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=2, alpha=0.7)

        ax.plot([p3[0], p4[0]], [p3[1], p4[1]], color=color, linewidth=2, alpha=0.7)

        

        # 如果相交，计算并绘制交点

        if segments_intersect(seg1, seg2):

            intersection = compute_intersection(seg1, seg2)

            if intersection:

                ax.scatter(intersection[0], intersection[1], c='red', s=100, 

                          marker='x', zorder=5)

    

    ax.set_aspect('equal')

    ax.grid(True, alpha=0.3)

    ax.set_xlim(-1, 7)

    ax.set_ylim(-3, 5)

    ax.set_title("线段相交检测\n红色X为交点")

    plt.tight_layout()

    plt.savefig("line_intersection.png", dpi=150)

    print("图像已保存至 line_intersection.png")

    plt.close()


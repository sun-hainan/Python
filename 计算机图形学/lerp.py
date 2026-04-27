# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / lerp



本文件实现 lerp 相关的算法功能。

"""



from typing import Tuple, List





Point = Tuple[float, float]

Point3D = Tuple[float, float, float]

Color = Tuple[int, int, int]





def lerp(a: float, b: float, t: float) -> float:

    """

    线性插值 (LERP)

    

    参数:

        a: 起点值

        b: 终点值

        t: 参数 [0, 1]

    

    返回:

        插值结果

    

    公式: result = a + t * (b - a)

        = (1 - t) * a + t * b

    """

    return a + t * (b - a)





def lerp_point(p1: Point, p2: Point, t: float) -> Point:

    """

    点之间的线性插值

    

    参数:

        p1, p2: 两个点

        t: 参数

    

    返回:

        插值点

    """

    x1, y1 = p1

    x2, y2 = p2

    return (lerp(x1, x2, t), lerp(y1, y2, t))





def lerp_color(c1: Color, c2: Color, t: float) -> Color:

    """

    颜色线性插值

    

    参数:

        c1, c2: 两个颜色 (r, g, b)

        t: 参数

    

    返回:

        插值颜色

    """

    r1, g1, b1 = c1

    r2, g2, b2 = c2

    return (

        int(lerp(r1, r2, t)),

        int(lerp(g1, g2, t)),

        int(lerp(b1, b2, t))

    )





def inverse_lerp(a: float, b: float, v: float) -> float:

    """

    逆线性插值：已知值 v，求参数 t

    

    参数:

        a, b: 范围

        v: 当前值

    

    返回:

        参数 t

    

    公式: t = (v - a) / (b - a)

    """

    if abs(b - a) < 1e-10:

        return 0.0

    return (v - a) / (b - a)





def bilinear_interpolate(values: List[List[float]], 

                        x: float, y: float) -> float:

    """

    双线性插值

    

    在 2D 网格的四个角点值之间进行插值

    

    参数:

        values: 2x2 网格的值 [[v00, v01], [v10, v11]]

                v00 = (0,0), v01 = (1,0)

                v10 = (0,1), v11 = (1,1)

        x, y: 插值坐标 [0, 1]

    

    返回:

        插值结果

    """

    v00, v01 = values[0]

    v10, v11 = values[1]

    

    # 先沿 x 方向插值

    v0 = lerp(v00, v01, x)

    v1 = lerp(v10, v11, x)

    

    # 再沿 y 方向插值

    return lerp(v0, v1, y)





def bilinear_interpolate_full(grid: List[List[float]],

                              x: float, y: float,

                              x0: int, y0: int) -> float:

    """

    双线性插值（完整版本，任意网格）

    

    参数:

        grid: 2D 网格

        x, y: 插值坐标（浮点数）

        x0, y0: 插值点左下角网格坐标

    """

    # 获取四个角点

    y1 = y0 + 1

    x1 = x0 + 1

    

    # 获取角点值（带边界检查）

    def get_val(xi, yi):

        if 0 <= xi < len(grid[0]) and 0 <= yi < len(grid):

            return grid[yi][xi]

        return 0.0

    

    v00 = get_val(x0, y0)

    v01 = get_val(x1, y0)

    v10 = get_val(x0, y1)

    v11 = get_val(x1, y1)

    

    # 计算在小格子内的相对位置

    tx = x - x0

    ty = y - y0

    

    # 双线性插值

    v0 = lerp(v00, v01, tx)

    v1 = lerp(v10, v11, tx)

    return lerp(v0, v1, ty)





def trilinear_interpolate(corners: List[float],

                         x: float, y: float, z: float) -> float:

    """

    三线性插值

    

    参数:

        corners: 8个角点值，按 (x,y,z) 组合排列

        x, y, z: 插值坐标 [0, 1]

    

    返回:

        插值结果

    """

    # 简化版本：假设角点按索引排列

    # c000, c001, c010, c011, c100, c101, c110, c111

    

    c000 = corners[0]

    c001 = corners[1]

    c010 = corners[2]

    c011 = corners[3]

    c100 = corners[4]

    c101 = corners[5]

    c110 = corners[6]

    c111 = corners[7]

    

    # x 方向插值

    c00 = lerp(c000, c001, x)

    c01 = lerp(c010, c011, x)

    c10 = lerp(c100, c101, x)

    c11 = lerp(c110, c111, x)

    

    # y 方向插值

    c0 = lerp(c00, c01, y)

    c1 = lerp(c10, c11, y)

    

    # z 方向插值

    return lerp(c0, c1, z)





def barycentric_coords(p: Point, v0: Point, v1: Point, v2: Point) -> Tuple[float, float, float]:

    """

    计算点的重心坐标

    

    参数:

        p: 要计算的点

        v0, v1, v2: 三角形的三个顶点

    

    返回:

        重心坐标 (u, v, w)，满足 u + v + w = 1

    

    几何意义：

        u = 三角形 Pv1v2 的面积 / 三角形 v0v1v2 的面积

        v = 三角形 Pv0v2 的面积 / 三角形 v0v1v2 的面积

        w = 三角形 Pv0v1 的面积 / 三角形 v0v1v2 的面积

    """

    x, y = p

    x0, y0 = v0

    x1, y1 = v1

    x2, y2 = v2

    

    # 计算三角形面积（叉积的绝对值）

    def area_sign(ax, ay, bx, by, cx, cy):

        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

    

    total_area = abs(area_sign(x0, y0, x1, y1, x2, y2))

    

    if total_area < 1e-10:

        return (1.0/3.0, 1.0/3.0, 1.0/3.0)

    

    # 计算 u, v, w

    area_p12 = abs(area_sign(x, y, x1, y1, x2, y2))

    area_0p2 = abs(area_sign(x0, y0, x, y, x2, y2))

    area_01p = abs(area_sign(x0, y0, x1, y1, x, y))

    

    u = area_p12 / total_area

    v = area_0p2 / total_area

    w = area_01p / total_area

    

    return (u, v, w)





def barycentric_interpolate(values: List[float],

                           bary: Tuple[float, float, float]) -> float:

    """

    使用重心坐标插值值

    

    参数:

        values: [v0, v1, v2] 三个顶点上的值

        bary: 重心坐标 (u, v, w)

    

    返回:

        插值结果

    """

    u, v, w = bary

    v0, v1, v2 = values

    return u * v0 + v * v1 + w * v2





def perspective_correct_interpolate(values: List[float],

                                 depths: List[float],

                                 bary: Tuple[float, float, float],

                                 w_reciprocal: float) -> float:

    """

    透视校正插值

    

    问题：在透视投影后，直接线性插值会导致非线性畸变

    解决：在屏幕空间中对 1/z 进行插值，然后取倒数得到正确的 z

    

    参数:

        values: 顶点属性值（如纹理坐标）

        depths: 顶点深度值 (z)

        bary: 重心坐标

        w_reciprocal: 透视校正因子

    

    返回:

        校正后的插值

    """

    u, v, w = bary

    v0, v1, v2 = values

    z0, z1, z2 = depths

    

    # 对 1/z 进行插值

    one_over_z = u / z0 + v / z1 + w / z2

    

    # 对属性值/ z 进行插值

    attr_over_z = u * v0 / z0 + v * v1 / z1 + w * v2 / z2

    

    # 透视校正

    return attr_over_z / one_over_z





# ============ 缓动函数 (Easing Functions) ============



def ease_in(t: float, power: float = 2.0) -> float:

    """加速缓动"""

    return t ** power





def ease_out(t: float, power: float = 2.0) -> float:

    """减速缓动"""

    return 1 - (1 - t) ** power





def ease_in_out(t: float, power: float = 2.0) -> float:

    """先加速后减速"""

    if t < 0.5:

        return ease_in(2 * t, power) / 2

    else:

        return (1 + ease_out(2 * t - 1, power)) / 2





if __name__ == "__main__":

    print("=" * 60)

    print("线性插值 / 光栅化基础测试")

    print("=" * 60)

    

    # 测试1：基本线性插值

    print("\n测试1 - 基本线性插值:")

    print(f"  lerp(0, 10, 0.0) = {lerp(0, 10, 0.0)}")

    print(f"  lerp(0, 10, 0.5) = {lerp(0, 10, 0.5)}")

    print(f"  lerp(0, 10, 1.0) = {lerp(0, 10, 1.0)}")

    print(f"  lerp(100, 200, 0.3) = {lerp(100, 200, 0.3)}")

    

    # 测试2：逆线性插值

    print("\n测试2 - 逆线性插值:")

    print(f"  inverse_lerp(0, 10, 5) = {inverse_lerp(0, 10, 5)}")

    print(f"  inverse_lerp(0, 10, 2.5) = {inverse_lerp(0, 10, 2.5)}")

    print(f"  inverse_lerp(0, 10, 0) = {inverse_lerp(0, 10, 0)}")

    

    # 测试3：颜色插值

    print("\n测试3 - 颜色插值:")

    red = (255, 0, 0)

    blue = (0, 0, 255)

    

    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:

        color = lerp_color(red, blue, t)

        print(f"  t={t:.2f}: {color}")

    

    # 测试4：双线性插值

    print("\n测试4 - 双线性插值:")

    grid = [

        [0, 100],

        [50, 200]

    ]

    

    test_points = [

        (0.0, 0.0),

        (1.0, 1.0),

        (0.5, 0.5),

        (0.25, 0.75),

        (0.75, 0.25),

    ]

    

    for x, y in test_points:

        val = bilinear_interpolate(grid, x, y)

        print(f"  ({x:.2f}, {y:.2f}): {val:.2f}")

    

    # 测试5：重心坐标

    print("\n测试5 - 重心坐标:")

    v0 = (0.0, 0.0)

    v1 = (1.0, 0.0)

    v2 = (0.0, 1.0)

    

    test_pts = [

        (0.5, 0.5),

        (0.25, 0.25),

        (0.0, 0.0),

        (0.75, 0.25),

    ]

    

    for p in test_pts:

        u, v, w = barycentric_coords(p, v0, v1, v2)

        print(f"  {p}: u={u:.3f}, v={v:.3f}, w={w:.3f}, sum={u+v+w:.3f}")

    

    # 测试6：重心坐标插值

    print("\n测试6 - 重心坐标插值属性:")

    values = [10.0, 20.0, 30.0]

    

    for p in test_pts:

        u, v, w = barycentric_coords(p, v0, v1, v2)

        val = barycentric_interpolate(values, (u, v, w))

        print(f"  {p}: u={u:.3f}, v={v:.3f}, w={w:.3f} -> 值={val:.2f}")

    

    # 测试7：缓动函数可视化

    print("\n测试7 - 缓动函数可视化:")

    print("  ease_in (二次):")

    row = ""

    for i in range(11):

        t = i / 10

        val = ease_in(t)

        row += "#" if val > 0.5 else "."

    print(f"    {row}")

    

    print("  ease_out:")

    row = ""

    for i in range(11):

        t = i / 10

        val = ease_out(t)

        row += "#" if val > 0.5 else "."

    print(f"    {row}")

    

    # 测试8：三角形光栅化

    print("\n测试8 - 三角形光栅化（使用重心坐标）:")

    

    def rasterize_triangle(v0, v1, v2, color00, color01, color10):

        """简化光栅化：只打印像素"""

        pixels = []

        

        # 计算包围盒

        min_x = max(0, int(min(v0[0], v1[0], v2[0])))

        max_x = min(10, int(max(v0[0], v1[0], v2[0])))

        min_y = max(0, int(min(v0[1], v1[1], v2[1])))

        max_y = min(10, int(max(v0[1], v1[1], v2[1])))

        

        for y in range(min_y, max_y + 1):

            for x in range(min_x, max_x + 1):

                p = (x + 0.5, y + 0.5)

                u, v, w = barycentric_coords(p, v0, v1, v2)

                

                if u >= 0 and v >= 0 and w >= 0:

                    # 插值颜色

                    r = int(u * color00[0] + v * color01[0] + w * color10[0])

                    g = int(u * color00[1] + v * color01[1] + w * color10[1])

                    b = int(u * color00[2] + v * color01[2] + w * color10[2])

                    pixels.append((x, y, (r, g, b)))

        

        return pixels

    

    # 简单三角形测试

    v0 = (2.0, 2.0)

    v1 = (8.0, 2.0)

    v2 = (5.0, 8.0)

    c0 = (255, 0, 0)

    c1 = (0, 255, 0)

    c2 = (0, 0, 255)

    

    pixels = rasterize_triangle(v0, v1, v2, c0, c1, c2)

    print(f"  三角形顶点: {v0}, {v1}, {v2}")

    print(f"  覆盖像素数: {len(pixels)}")

    

    # 打印部分像素

    for x, y, c in pixels[:5]:

        print(f"    ({x},{y}): {c}")

    if len(pixels) > 5:

        print(f"    ... 共 {len(pixels)} 像素")

    

    print("\n" + "=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  线性插值: O(1)")

    print("  双线性插值: O(1)")

    print("  三线性插值: O(1)")

    print("  重心坐标: O(1)")

    print("  透视校正插值: O(1)")

    print("  三角形光栅化: O(w × h) 包围盒面积")


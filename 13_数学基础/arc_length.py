# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / arc_length



本文件实现 arc_length 相关的算法功能。

"""



import math

from typing import Callable





def arc_length_circle(radius: float, angle_degrees: float) -> float:

    """

    圆弧长度



    参数：

        radius: 圆的半径

        angle_degrees: 圆心角度数



    返回：弧长



    公式：L = 2 * π * r * (角度 / 360)

        = r * θ (θ以弧度计)

    """

    angle_radians = math.radians(angle_degrees)

    return radius * angle_radians





def arc_length_sector(radius: float, angle_degrees: float) -> float:

    """

    扇形弧长（含两条半径）



    参数：

        radius: 圆的半径

        angle_degrees: 圆心角度数



    返回：扇形周长（弧长 + 2*半径）

    """

    arc = arc_length_circle(radius, angle_degrees)

    return arc + 2 * radius





def arc_length_ellipse(a: float, b: float, angle_degrees: float) -> float:

    """

    椭圆弧长（近似）



    参数：

        a: 半长轴

        b: 半短轴

        angle_degrees: 弧度范围



    返回：近似弧长



    注意：椭圆弧长没有初等闭式解

    使用 Ramanujan 第二近似公式

    """

    angle_radians = math.radians(angle_degrees)



    # Ramanujan 第二近似

    h = ((a - b) ** 2) / ((a + b) ** 2)

    h_modified = h * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))



    # 完整椭圆周长

    perimeter_full = math.pi * (a + b) * (1 + 3 * h_modified / (10 + math.sqrt(4 - 3 * h_modified)))



    # 按角度比例

    return perimeter_full * (angle_radians / (2 * math.pi))





def arc_length_parametric(func_x: Callable, func_y: Callable,

                         t_start: float, t_end: float, n: int = 1000) -> float:

    """

    参数曲线的弧长（数值方法）



    参数曲线 (x(t), y(t)) 从 t=t_start 到 t=t_end



    参数：

        func_x: x(t) 函数

        func_y: y(t) 函数

        t_start: 参数起点

        t_end: 参数终点

        n: 分割数



    返回：弧长近似值



    公式：L = ∫ sqrt((dx/dt)^2 + (dy/dt)^2) dt

    """

    dt = (t_end - t_start) / n

    length = 0.0



    t = t_start

    for i in range(n):

        # 简化的梯形法则

        dx = (func_x(t + dt) - func_x(t)) / dt

        dy = (func_y(t + dt) - func_y(t)) / dt



        segment_length = math.sqrt(dx**2 + dy**2) * dt

        length += segment_length



        t += dt



    return length





def arc_length_curve(func: Callable, a: float, b: float, n: int = 1000) -> float:

    """

    y = f(x) 形式曲线的弧长



    参数：

        func: f(x) 函数

        a: x起点

        b: x终点

        n: 分割数



    返回：弧长近似值



    公式：L = ∫ sqrt(1 + (f'(x))^2) dx

    """

    dx = (b - a) / n

    length = 0.0



    x = a

    for i in range(n):

        # 中点梯形法

        x_mid = x + dx / 2

        derivative = (func(x + dx) - func(x)) / dx



        integrand = math.sqrt(1 + derivative**2)

        length += integrand * dx



        x += dx



    return length





def helix_length(radius: float, pitch: float, turns: float) -> float:

    """

    圆柱螺旋线的长度



    参数：

        radius: 螺旋半径

        pitch: 螺距（一圈的轴向距离）

        turns: 圈数



    返回：螺旋线总长度



    公式：L = n * sqrt((2πr)^2 + p^2)

    """

    circumference = 2 * math.pi * radius

    helix_per_turn = math.sqrt(circumference**2 + pitch**2)

    return turns * helix_per_turn





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 弧长计算测试 ===\n")



    # 圆形弧长

    radius = 5.0

    angle = 90  # 四分之一圆



    arc = arc_length_circle(radius, angle)

    print(f"圆弧：半径={radius}, 角度={angle}°")

    print(f"  弧长 = {arc:.4f}")

    print(f"  验证：2πr * (90/360) = {2*math.pi*radius*(90/360):.4f}")



    print()



    # 扇形周长

    sector = arc_length_sector(radius, angle)

    print(f"  扇形周长 = {sector:.4f}")



    print()



    # 椭圆弧长

    a, b = 5.0, 3.0  # 半长轴和半短轴

    ellipse_arc = arc_length_ellipse(a, b, 90)

    print(f"椭圆弧：a={a}, b={b}, 角度=90°")

    print(f"  弧长 ≈ {ellipse_arc:.4f}")



    print()



    # 参数曲线：摆线

    def cycloid_x(t):

        return 5 * (t - math.sin(t))



    def cycloid_y(t):

        return 5 * (1 - math.cos(t))



    t_start = 0

    t_end = 2 * math.pi  # 一圈



    cycloid_len = arc_length_parametric(cycloid_x, cycloid_y, t_start, t_end, n=10000)

    print(f"摆线（半径5，一圈）：")

    print(f"  计算弧长 ≈ {cycloid_len:.4f}")

    print(f"  理论弧长 = 16 * r = {16 * 5:.4f}")



    print()



    # 螺旋线

    helix_len = helix_length(radius=3, pitch=2, turns=5)

    print(f"螺旋线：半径=3, 螺距=2, 5圈")

    print(f"  长度 ≈ {helix_len:.4f}")



    print()

    print("复杂度分析：")

    print("  解析解：O(1)")

    print("  数值积分：O(n)，n为分割数")

    print()

    print("说明：")

    print("  - 大多数曲线弧长没有初等公式")

    print("  - 数值方法是实际工程中的主要工具")

    print("  - 椭圆积分用于精确椭圆弧长计算")


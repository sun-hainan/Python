# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / ray_sphere_intersection

本文件实现 ray_sphere_intersection 相关的算法功能。
"""

import numpy as np
import math


class Sphere:
    """
    球体类

    球体由球心 C 和半径 r 定义：
    ||P - C||² = r²
    """

    def __init__(self, center, radius, material=None):
        """
        初始化球体

        参数:
            center: 球心坐标 (3,)
            radius: 半径
            material: 材质属性
        """
        self.center = np.array(center, dtype=float)
        self.radius = radius
        self.material = material

    def area(self):
        """计算球体表面积"""
        return 4 * math.pi * self.radius ** 2

    def volume(self):
        """计算球体体积"""
        return (4 / 3) * math.pi * self.radius ** 3


class Ray:
    """
    光线类

    光线：P(t) = O + tD, t >= 0
    """

    def __init__(self, origin, direction):
        """
        初始化光线

        参数:
            origin: 起点 (3,)
            direction: 方向 (3,)（会自动归一化）
        """
        self.origin = np.array(origin, dtype=float)
        self.direction = np.array(direction, dtype=float)
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction = self.direction / norm

    def at(self, t):
        """计算 P(t)"""
        return self.origin + t * self.direction


def ray_sphere_intersection(ray, sphere, epsilon=1e-7):
    """
    光线-球体求交（解析法）

    解二次方程 ||O + tD - C||² = r²

    参数:
        ray: 光线
        sphere: 球体
        epsilon: 浮点误差阈值
    返回:
        hit: 是否相交
        t1: 较近交点的参数
        t2: 较远交点的参数
    """
    O = ray.origin
    D = ray.direction
    C = sphere.center
    r = sphere.radius

    # 向量 OC
    L = C - O

    # t_ca = L · D（光线方向上到球心的投影）
    t_ca = np.dot(L, D)

    # 如果球心在光线"背后"，且距离大于半径，则不相交
    if t_ca < 0 and np.linalg.norm(L) > r:
        return False, float('inf'), float('inf')

    # d² = L² - t_ca²（勾股定理求垂直距离）
    d_sq = np.dot(L, L) - t_ca * t_ca

    # 如果垂直距离大于半径，光线错过球体
    if d_sq > r * r:
        return False, float('inf'), float('inf')

    # 半弦长
    t_hc = math.sqrt(r * r - d_sq)

    # 两个交点的参数
    t1 = t_ca - t_hc
    t2 = t_ca + t_hc

    # 检查有效解（t >= 0）
    if t1 < epsilon and t2 < epsilon:
        return False, float('inf'), float('inf')

    return True, t1, t2


def ray_sphere_intersection_quadratic(ray, sphere, epsilon=1e-7):
    """
    光线-球体求交（二次方程标准解法）

    参数:
        ray: 光线
        sphere: 球体
        epsilon: 误差阈值
    返回:
        hit: 是否相交
        t_near: 最近交点的参数
        t_far: 最远交点的参数
    """
    O = ray.origin
    D = ray.direction
    C = sphere.center
    r = sphere.radius

    # 计算二次方程系数
    # ||O + tD - C||² = r²
    # (D·D)t² + 2D·(O-C)t + ||O-C||² - r² = 0

    a = np.dot(D, D)
    b = 2.0 * np.dot(D, O - C)
    c = np.dot(O - C, O - C) - r * r

    # 计算判别式
    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        # 无实数解
        return False, float('inf'), float('inf')

    if abs(discriminant) < epsilon:
        # 判别式为零，相切
        t = -b / (2 * a)
        return True, t, t

    # 两个实数解
    sqrt_d = math.sqrt(discriminant)
    t1 = (-b - sqrt_d) / (2 * a)
    t2 = (-b + sqrt_d) / (2 * a)

    # 确保 t1 <= t2
    if t1 > t2:
        t1, t2 = t2, t1

    return True, t1, t2


def get_intersection_normal(sphere, hit_point):
    """
    计算球面上的交点法线

    球面上任意点的法线就是从球心指向该点的方向。

    参数:
        sphere: 球体
        hit_point: 交点位置
    返回:
        normal: 法线向量（归一化）
    """
    normal = hit_point - sphere.center
    norm = np.linalg.norm(normal)
    if norm > 0:
        normal = normal / norm
    return normal


def get_uv_coords(sphere, hit_point):
    """
    计算球面上的 UV 坐标

    使用球面坐标系：
    θ = atan2(z, x)
    φ = acos(y / r)

    参数:
        sphere: 球体
        hit_point: 交点位置
    返回:
        u, v: UV 坐标 [0, 1]
    """
    p = hit_point - sphere.center
    r = sphere.radius

    # 归一化到球面
    x, y, z = p / r

    # 计算球面坐标
    theta = math.atan2(z, x)  # [0, 2π]
    phi = math.acos(np.clip(y, -1, 1))  # [0, π]

    # 转换到 [0, 1]
    u = (theta + math.pi) / (2 * math.pi)
    v = phi / math.pi

    return u, v


def intersect(ray, sphere, epsilon=1e-7):
    """
    光线-球体求交（简化接口）

    参数:
        ray: 光线
        sphere: 球体
        epsilon: 误差阈值
    返回:
        hit: 是否相交
        t: 交点参数
        hit_point: 交点坐标
        normal: 交点法线
    """
    hit, t1, t2 = ray_sphere_intersection(ray, sphere, epsilon)

    if not hit:
        return False, float('inf'), None, None

    # 选择较小的正 t
    if t1 < epsilon:
        t = t2
    else:
        t = t1

    if t < epsilon:
        return False, float('inf'), None, None

    hit_point = ray.at(t)
    normal = get_intersection_normal(sphere, hit_point)

    return True, t, hit_point, normal


def batch_intersect(ray, spheres):
    """
    批量光线-球体求交

    参数:
        ray: 光线
        spheres: 球体列表
    返回:
        result: 最近交点信息
    """
    best_t = float('inf')
    best_hit = False
    best_point = None
    best_normal = None
    best_sphere = None

    for sphere in spheres:
        hit, t, point, normal = intersect(ray, sphere)
        if hit and t < best_t:
            best_t = t
            best_hit = hit
            best_point = point
            best_normal = normal
            best_sphere = sphere

    return {
        'hit': best_hit,
        't': best_t,
        'point': best_point,
        'normal': best_normal,
        'sphere': best_sphere
    }


if __name__ == "__main__":
    # 创建测试球体
    center = np.array([2.0, 0.0, 5.0])
    radius = 1.5
    sphere = Sphere(center, radius)

    print("=== 光线-球体求交测试 ===")
    print(f"球心: {center}")
    print(f"半径: {radius}")

    # 测试1：正射球心
    ray1 = Ray(origin=[0.0, 0.0, 0.0], direction=[0.0, 0.0, 1.0])
    print(f"\n测试1（正射球心）:")
    print(f"  光线起点: {ray1.origin}, 方向: {ray1.direction}")

    hit1, t1_1, t1_2 = ray_sphere_intersection(ray1, sphere)
    print(f"  命中: {hit1}, t1={t1_1:.4f}, t2={t1_2:.4f}")

    if hit1:
        p1 = ray1.at(t1_1)
        n1 = get_intersection_normal(sphere, p1)
        u1, v1 = get_uv_coords(sphere, p1)
        print(f"  交点: {p1}")
        print(f"  法线: {n1}")
        print(f"  UV: ({u1:.4f}, {v1:.4f})")

    # 测试2：擦边而过
    ray2 = Ray(origin=[0.0, 0.0, 0.0], direction=[1.0, 0.0, 1.0])
    ray2.direction = ray2.direction / np.linalg.norm(ray2.direction)
    print(f"\n测试2（擦边）:")
    print(f"  光线起点: {ray2.origin}, 方向: {ray2.direction}")

    hit2, t2_1, t2_2 = ray_sphere_intersection(ray2, sphere)
    print(f"  命中: {hit2}, t1={t2_1:.4f}, t2={t2_2:.4f}")

    # 测试3：完全错过
    ray3 = Ray(origin=[0.0, 0.0, 0.0], direction=[0.0, 1.0, 0.0])
    print(f"\n测试3（错过）:")
    print(f"  光线起点: {ray3.origin}, 方向: {ray3.direction}")

    hit3, t3_1, t3_2 = ray_sphere_intersection(ray3, sphere)
    print(f"  命中: {hit3}")

    # 测试4：从球体内部
    ray4 = Ray(origin=[2.0, 0.0, 4.5], direction=[0.0, 0.0, 1.0])
    print(f"\n测试4（内部出发）:")
    print(f"  光线起点: {ray4.origin}, 方向: {ray4.direction}")

    hit4, t4_1, t4_2 = ray_sphere_intersection(ray4, sphere)
    print(f"  命中: {hit4}, t1={t4_1:.4f}, t2={t4_2:.4f}")
    if hit4 and t4_1 < 0:
        print(f"  正确：t1<0 表示从内部出发")

    # 批量求交测试
    print("\n=== 批量求交测试 ===")
    spheres = [
        Sphere([1.0, 0.0, 5.0], 0.5),
        Sphere([3.0, 1.0, 5.0], 0.8),
        Sphere([2.0, -0.5, 6.0], 0.3),
    ]

    ray5 = Ray(origin=[0.0, 0.0, 0.0], direction=[0.0, 0.0, 1.0])
    result = batch_intersect(ray5, spheres)
    print(f"3个球体批量求交:")
    print(f"  命中: {result['hit']}")
    if result['hit']:
        print(f"  t = {result['t']:.4f}")
        print(f"  交点: {result['point']}")

    # 验证二次方程解法和几何解法一致性
    print("\n=== 两种算法对比 ===")
    for sphere in spheres:
        hit_geo, t1_geo, t2_geo = ray_sphere_intersection(ray5, sphere)
        hit_quad, t1_quad, t2_quad = ray_sphere_intersection_quadratic(ray5, sphere)
        print(f"  几何法: t1={t1_geo:.6f}, t2={t2_geo:.6f}")
        print(f"  二次方程: t1={t1_quad:.6f}, t2={t2_quad:.6f}")
        diff = abs(t1_geo - t1_quad) + abs(t2_geo - t2_quad)
        print(f"  差异: {diff:.10f}")

    print("\n光线-球体求交测试完成!")

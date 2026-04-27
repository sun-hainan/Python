# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / ray_triangle_intersection

本文件实现 ray_triangle_intersection 相关的算法功能。
"""

import numpy as np
import math


class Ray:
    """
    光线类

    光线由起点 O 和方向 D 参数化：
    P(t) = O + tD, t >= 0
    """

    def __init__(self, origin, direction):
        """
        初始化光线

        参数:
            origin: 光线起点 (3,)
            direction: 光线方向 (3,)（归一化）
        """
        self.origin = np.array(origin, dtype=float)  # O
        self.direction = np.array(direction, dtype=float)  # D
        # 确保方向是单位向量
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction = self.direction / norm

    def at(self, t):
        """
        计算光线在参数 t 处的位置

        参数:
            t: 参数
        返回:
            point: P(t) = O + tD
        """
        return self.origin + t * self.direction


class Triangle:
    """
    三角形类

    三角形由三个顶点 V0, V1, V2 定义。
    使用逆时针顺序（右手定则确定法线方向）。
    """

    def __init__(self, v0, v1, v2, material=None):
        """
        初始化三角形

        参数:
            v0, v1, v2: 三角形的三个顶点 (3,)
            material: 材质属性
        """
        self.v0 = np.array(v0, dtype=float)
        self.v1 = np.array(v1, dtype=float)
        self.v2 = np.array(v2, dtype=float)
        self.material = material

        # 计算法线（右手定则）
        edge1 = self.v1 - self.v0
        edge2 = self.v2 - self.v0
        self.normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(self.normal)
        if norm > 0:
            self.normal = self.normal / norm

        # 预计算边向量
        self.edge1 = edge1
        self.edge2 = edge2

    def area(self):
        """计算三角形面积"""
        return 0.5 * np.linalg.norm(np.cross(self.edge1, self.edge2))


def moller_trumbore(ray, triangle, epsilon=1e-7):
    """
    Möller–Trumbore 光线-三角形求交算法

    这是最快的光线-三角形求交算法，直接计算参数 t, u, v。

    参数:
        ray: 光线
        triangle: 三角形
        epsilon: 浮点误差阈值
    返回:
        hit: 是否相交
        t: 交点参数（P = O + tD）
        u, v: 重心坐标
    """
    # 光线方向
    D = ray.direction
    O = ray.origin

    # 三角形顶点
    V0, V1, V2 = triangle.v0, triangle.v1, triangle.v2

    # 边向量
    E1 = V1 - V0
    E2 = V2 - V0

    # P = D × E2
    P = np.cross(D, E2)

    # 行列式
    det = np.dot(E1, P)

    # 如果行列式接近0，光线平行于三角形平面
    if abs(det) < epsilon:
        return False, float('inf'), 0.0, 0.0

    inv_det = 1.0 / det

    # T = O - V0
    T = O - V0

    # u = T · P / det
    u = np.dot(T, P) * inv_det

    # 检查 u 是否在 [0, 1] 范围内
    if u < 0.0 or u > 1.0:
        return False, float('inf'), 0.0, 0.0

    # Q = T × E1
    Q = np.cross(T, E1)

    # v = D · Q / det
    v = np.dot(D, Q) * inv_det

    # 检查 v 是否在有效范围内（u + v <= 1）
    if v < 0.0 or u + v > 1.0:
        return False, float('inf'), 0.0, 0.0

    # t = E2 · Q / det
    t = np.dot(E2, Q) * inv_det

    # 检查 t 是否为正（光线方向）
    if t < epsilon:
        return False, float('inf'), 0.0, 0.0

    # 命中！
    return True, t, u, v


def barycentric_coords(point, v0, v1, v2):
    """
    计算点的重心坐标

    参数:
        point: 待计算点
        v0, v1, v2: 三角形顶点
    返回:
        u, v: 重心坐标（w = 1 - u - v）
    """
    # 向量
    e0 = v1 - v0
    e1 = v2 - v0
    e2 = point - v0

    # 点积
    dot00 = np.dot(e0, e0)
    dot01 = np.dot(e0, e1)
    dot02 = np.dot(e0, e2)
    dot11 = np.dot(e1, e1)
    dot12 = np.dot(e1, e2)

    # 计算重心坐标
    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-10:
        return 0.0, 0.0

    inv_denom = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom

    return u, v


def intersect(ray, triangle, epsilon=1e-7):
    """
    光线-三角形求交（简化版本）

    参数:
        ray: 光线
        triangle: 三角形
        epsilon: 误差阈值
    返回:
        hit: 是否相交
        t: 交点距离
        hit_point: 交点坐标
        normal: 交点处法线
    """
    hit, t, u, v = moller_trumbore(ray, triangle, epsilon)

    if hit:
        hit_point = ray.at(t)
        return True, t, hit_point, triangle.normal

    return False, float('inf'), None, None


def batch_intersect(ray, triangles):
    """
    批量光线-三角形求交

    参数:
        ray: 光线
        triangles: 三角形列表
    返回:
        best_hit: 最近交点信息
    """
    best_t = float('inf')
    best_hit = None
    best_point = None
    best_normal = None
    best_tri = None

    for tri in triangles:
        hit, t, point, normal = intersect(ray, tri)
        if hit and t < best_t:
            best_t = t
            best_hit = hit
            best_point = point
            best_normal = normal
            best_tri = tri

    return {
        'hit': best_hit,
        't': best_t,
        'point': best_point,
        'normal': best_normal,
        'triangle': best_tri
    }


if __name__ == "__main__":
    # 创建测试三角形（一个朝向 Z 轴的平面三角形）
    v0 = np.array([-1.0, -1.0, 5.0])
    v1 = np.array([1.0, -1.0, 5.0])
    v2 = np.array([0.0, 1.0, 5.0])
    triangle = Triangle(v0, v1, v2)

    print("=== Möller–Trumbore 光线-三角形求交测试 ===")
    print(f"三角形顶点: V0={v0}, V1={v1}, V2={v2}")
    print(f"三角形法线: {triangle.normal}")
    print(f"三角形面积: {triangle.area():.4f}")

    # 创建光线（从原点看向三角形）
    ray = Ray(origin=[0.0, 0.0, 0.0], direction=[0.0, 0.0, 1.0])

    print(f"\n光线起点: {ray.origin}")
    print(f"光线方向: {ray.direction}")

    # 求交
    hit, t, u, v = moller_trumbore(ray, triangle)
    print(f"\n交点测试（正射）:")
    print(f"  命中: {hit}")
    if hit:
        point = ray.at(t)
        print(f"  t = {t:.4f}")
        print(f"  u = {u:.4f}, v = {v:.4f}")
        print(f"  交点: {point}")
        # 验证重心坐标
        w = 1 - u - v
        reconstructed = u * v1 + v * v2 + w * v0
        print(f"  重心重建: {reconstructed}")

    # 测试偏离的光线（应该不命中）
    ray2 = Ray(origin=[0.0, 0.0, 0.0], direction=[1.0, 0.0, 0.0])
    hit2, t2, _, _ = moller_trumbore(ray2, triangle)
    print(f"\n交点测试（平行光线）:")
    print(f"  命中: {hit2}")

    # 测试背面入射
    ray3 = Ray(origin=[0.0, 0.0, 10.0], direction=[0.0, 0.0, -1.0])
    hit3, t3, _, _ = moller_trumbore(ray3, triangle)
    print(f"\n交点测试（背面入射）:")
    print(f"  命中: {hit3}")

    # 批量测试
    print("\n=== 批量求交测试 ===")
    triangles = []
    for i in range(5):
        for j in range(5):
            z = 5.0
            v0 = np.array([-1.0 + i * 0.5, -1.0 + j * 0.5, z])
            v1 = np.array([-0.5 + i * 0.5, -1.0 + j * 0.5, z])
            v2 = np.array([-0.75 + i * 0.5, -0.5 + j * 0.5, z])
            triangles.append(Triangle(v0, v1, v2))

    ray4 = Ray(origin=[0.0, 0.0, 0.0], direction=[0.0, 0.0, 1.0])
    result = batch_intersect(ray4, triangles)
    print(f"25个三角形批量求交:")
    print(f"  命中: {result['hit']}")
    if result['hit']:
        print(f"  t = {result['t']:.4f}")

    print("\n光线-三角形求交测试完成!")

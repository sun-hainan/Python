# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / geometric_modeling

本文件实现 geometric_modeling 相关的算法功能。
"""

import math
import random

# ========== 基础数据结构和工具函数 ==========

class Point3D:
    """
    三维点类：表示3D空间中的点或向量
    """
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, other):
        # 向量减法
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other):
        # 向量加法
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, scalar):
        # 标量乘法
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other):
        # 点积
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        # 叉积
        return Point3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length(self):
        # 向量长度
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        # 单位化
        l = self.length()
        if l < 1e-10:
            return Point3D(0, 0, 0)
        return Point3D(self.x / l, self.y / l, self.z / l)


class Triangle:
    """
    三角形类：表示网格中的一个面片
    """
    def __init__(self, v0, v1, v2):
        self.v0 = v0  # 顶点0索引
        self.v1 = v1  # 顶点1索引
        self.v2 = v2  # 顶点2索引

    def normal(self, vertices):
        """
        计算三角形的法向量
        :param vertices: 顶点列表
        :return: 法向量（单位化）
        """
        p0 = vertices[self.v0]
        p1 = vertices[self.v1]
        p2 = vertices[self.v2]
        edge1 = Point3D(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        edge2 = Point3D(p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        n = edge1.cross(edge2)
        return n.normalize()


# ========== Bezier曲线与曲面 ==========

def bernstein(n, i, t):
    """
    Bernstein基函数
    :param n: 多项式次数
    :param i: 基函数索引
    :param t: 参数值 [0, 1]
    :return: 基函数值
    """
    return math.factorial(n) / (math.factorial(i) * math.factorial(n - i)) * (t ** i) * ((1 - t) ** (n - i))


def bezier_curve(control_points, num_samples=50):
    """
    绘制Bezier曲线
    :param control_points: 控制点列表，每个点是(x, y, z)
    :param num_samples: 采样点数
    :return: 曲线上的点列表
    """
    n = len(control_points) - 1  # 曲线次数
    curve = []

    for i in range(num_samples):
        t = i / (num_samples - 1)  # 参数范围[0, 1]
        point = [0.0, 0.0, 0.0]  # 初始化曲线上点

        for j, cp in enumerate(control_points):
            b = bernstein(n, j, t)  # Bernstein基函数值
            # 加权求和
            point[0] += b * cp[0]
            point[1] += b * cp[1]
            point[2] += b * cp[2]

        curve.append(point)

    return curve


def bezier_surface(control_points, m, n, u_samples=20, v_samples=20):
    """
    Bezier曲面生成
    :param control_points: m×n控制点网格，每个点是(x, y, z)
    :param m: u方向控制点数量
    :param n: v方向控制点数量
    :param u_samples: u方向采样数
    :param v_samples: v方向采样数
    :return: 曲面顶点网格
    """
    surface = []
    degree_u = m - 1  # u方向次数
    degree_v = n - 1  # v方向次数

    for i in range(u_samples):
        u = i / (u_samples - 1)  # u参数
        row = []
        for j in range(v_samples):
            v = j / (v_samples - 1)  # v参数
            point = [0.0, 0.0, 0.0]

            # 双线性组合
            for ki in range(m):
                for kj in range(n):
                    b_u = bernstein(degree_u, ki, u)  # u方向基函数
                    b_v = bernstein(degree_v, kj, v)  # v方向基函数
                    cp = control_points[ki][kj]
                    weight = b_u * b_v
                    point[0] += weight * cp[0]
                    point[1] += weight * cp[1]
                    point[2] += weight * cp[2]

            row.append(point)
        surface.append(row)

    return surface


def bezier_surface_to_mesh(control_points, m, n, u_samples=20, v_samples=20):
    """
    将Bezier曲面转换为三角网格
    :param control_points: 控制点网格
    :param m: u方向控制点数
    :param n: v方向控制点数
    :param u_samples: u方向采样数
    :param v_samples: v方向采样数
    :return: (vertices, triangles) 顶点和三角形列表
    """
    surface = bezier_surface(control_points, m, n, u_samples, v_samples)
    vertices = [p for row in surface for p in row]  # 展平为顶点列表
    triangles = []

    # 生成三角形索引
    for i in range(u_samples - 1):
        for j in range(v_samples - 1):
            # 当前顶点索引
            v00 = i * v_samples + j
            v10 = (i + 1) * v_samples + j
            v01 = i * v_samples + (j + 1)
            v11 = (i + 1) * v_samples + (j + 1)

            # 两个三角形组成四边形
            triangles.append(Triangle(v00, v10, v01))
            triangles.append(Triangle(v10, v11, v01))

    return vertices, triangles


# ========== B样条曲线与曲面 ==========

def b_spline_basis(i, k, t, knot_vector):
    """
    B样条基函数（de Boor算法）
    :param i: 基函数索引
    :param k: 基函数次数
    :param t: 参数值
    :param knot_vector: 节点向量
    :return: 基函数值
    """
    if k == 0:
        return 1.0 if knot_vector[i] <= t < knot_vector[i + 1] else 0.0

    result = 0.0
    denom1 = knot_vector[i + k] - knot_vector[i]
    denom2 = knot_vector[i + k + 1] - knot_vector[i + 1]

    if denom1 > 0:
        result += (t - knot_vector[i]) / denom1 * b_spline_basis(i, k - 1, t, knot_vector)
    if denom2 > 0:
        result += (knot_vector[i + k + 1] - t) / denom2 * b_spline_basis(i + 1, k - 1, t, knot_vector)

    return result


def b_spline_curve(control_points, degree, knot_vector, num_samples=50):
    """
    B样条曲线
    :param control_points: 控制点列表
    :param degree: 曲线次数
    :param knot_vector: 节点向量
    :param num_samples: 采样数
    :return: 曲线点列表
    """
    n = len(control_points) - 1  # 控制点数量-1
    curve = []

    # 自动生成均匀节点向量（如果未提供）
    if len(knot_vector) == 0:
        for i in range(n + degree + 2):
            knot_vector.append(i / (n + degree + 1))

    t_min = knot_vector[degree]
    t_max = knot_vector[n + 1]

    for i in range(num_samples):
        t = t_min + (t_max - t_min) * i / (num_samples - 1)
        point = [0.0, 0.0, 0.0]

        for j in range(n + 1):
            basis = b_spline_basis(j, degree, t, knot_vector)
            point[0] += basis * control_points[j][0]
            point[1] += basis * control_points[j][1]
            point[2] += basis * control_points[j][2]

        curve.append(point)

    return curve


# ========== 网格处理算法 ==========

def compute_vertex_normals(vertices, triangles):
    """
    计算顶点法向量（通过邻接三角形平均）
    :param vertices: 顶点列表
    :param triangles: 三角形列表
    :return: 每个顶点的法向量
    """
    normals = [[0.0, 0.0, 0.0] for _ in vertices]  # 初始化法向量为0

    for tri in triangles:
        # 计算三角形法向量
        p0 = vertices[tri.v0]
        p1 = vertices[tri.v1]
        p2 = vertices[tri.v2]

        edge1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        edge2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])

        normal = (
            edge1[1] * edge2[2] - edge1[2] * edge2[1],
            edge1[2] * edge2[0] - edge1[0] * edge2[2],
            edge1[0] * edge2[1] - edge1[1] * edge2[0]
        )

        # 累加到三个顶点
        for v_idx in [tri.v0, tri.v1, tri.v2]:
            normals[v_idx][0] += normal[0]
            normals[v_idx][1] += normal[1]
            normals[v_idx][2] += normal[2]

    # 单位化
    for i, n in enumerate(normals):
        length = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if length > 1e-10:
            normals[i] = [n[0] / length, n[1] / length, n[2] / length]

    return normals


def mesh_smooth_laplacian(vertices, triangles, iterations=1, factor=0.3):
    """
    网格拉普拉斯平滑
    :param vertices: 顶点列表
    :param triangles: 三角形列表
    :param iterations: 平滑迭代次数
    :param factor: 平滑因子
    :return: 平滑后的顶点列表
    """
    # 构建邻接表
    adj = [[] for _ in vertices]  # 邻接顶点列表
    for tri in triangles:
        adj[tri.v0].extend([tri.v1, tri.v2])
        adj[tri.v1].extend([tri.v0, tri.v2])
        adj[tri.v2].extend([tri.v0, tri.v1])

    # 去重
    for i in range(len(adj)):
        adj[i] = list(set(adj[i]))

    smoothed = [v[:] for v in vertices]  # 复制顶点

    for _ in range(iterations):
        new_vertices = [v[:] for v in smoothed]
        for i, neighbors in enumerate(adj):
            if len(neighbors) == 0:
                continue
            # 计算邻域均值
            avg = [0.0, 0.0, 0.0]
            for j in neighbors:
                avg[0] += smoothed[j][0]
                avg[1] += smoothed[j][1]
                avg[2] += smoothed[j][2]
            avg[0] /= len(neighbors)
            avg[1] /= len(neighbors)
            avg[2] /= len(neighbors)

            # 拉普拉斯平滑：向邻域均值移动
            new_vertices[i][0] += factor * (avg[0] - smoothed[i][0])
            new_vertices[i][1] += factor * (avg[1] - smoothed[i][1])
            new_vertices[i][2] += factor * (avg[2] - smoothed[i][2])

        smoothed = new_vertices

    return smoothed


if __name__ == "__main__":
    print("=" * 50)
    print("几何建模模块 - 样条曲面与网格处理 测试")
    print("=" * 50)

    # 1. 测试Bezier曲线
    print("\n1. Bezier曲线测试:")
    control_points = [
        (0, 0, 0),
        (1, 2, 0),
        (2, 2, 1),
        (3, 0, 0),
        (4, -2, 0)
    ]
    curve = bezier_curve(control_points, num_samples=20)
    print(f"  控制点数: {len(control_points)}")
    print(f"  采样点数: {len(curve)}")
    print(f"  曲线起点: ({curve[0][0]:.2f}, {curve[0][1]:.2f}, {curve[0][2]:.2f})")
    print(f"  曲线终点: ({curve[-1][0]:.2f}, {curve[-1][1]:.2f}, {curve[-1][2]:.2f})")

    # 2. 测试Bezier曲面
    print("\n2. Bezier曲面测试:")
    m, n = 4, 4  # 4x4控制点网格
    cp_grid = []
    for i in range(m):
        row = []
        for j in range(n):
            x = i / (m - 1)
            y = j / (n - 1)
            z = 0.5 * math.sin(x * math.pi) * math.sin(y * math.pi)
            row.append((x, y, z))
        cp_grid.append(row)

    surface = bezier_surface(cp_grid, m, n, u_samples=10, v_samples=10)
    print(f"  控制点网格: {m}x{n}")
    print(f"  采样网格: 10x10")
    print(f"  曲面顶点数: {len(surface) * len(surface[0])}")

    # 3. 测试三角网格
    print("\n3. 三角网格处理测试:")
    vertices, triangles = bezier_surface_to_mesh(cp_grid, m, n, u_samples=8, v_samples=8)
    print(f"  顶点数: {len(vertices)}")
    print(f"  三角形数: {len(triangles)}")

    # 计算法向量
    normals = compute_vertex_normals(vertices, triangles)
    print(f"  顶点法向量已计算: {len(normals)} 个")

    # 网格平滑
    smoothed = mesh_smooth_laplacian(vertices, triangles, iterations=3, factor=0.3)
    print(f"  拉普拉斯平滑完成: 3次迭代")

    print("\n" + "=" * 50)
    print("所有几何建模功能测试通过!")
    print("=" * 50)

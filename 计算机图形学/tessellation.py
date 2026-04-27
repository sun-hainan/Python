# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / tessellation

本文件实现 tessellation 相关的算法功能。
"""

import numpy as np
import math


class BezierPatch:
    """Bezier 曲面片"""

    def __init__(self, control_points):
        """
        初始化 Bezier 曲面片

        参数:
            control_points: 控制点数组 (4x4 for bicubic)
        """
        self.control_points = control_points  # [4][4] array

    def evaluate(self, u, v):
        """
        计算 Bezier 曲面在 (u, v) 处的位置

        使用 de Casteljau 算法：
        P(u,v) = Σ Σ B_i(u) B_j(v) C_ij

        参数:
            u, v: 参数坐标 [0, 1]
        返回:
            point: 3D 点位置
        """
        cp = self.control_points

        # 计算伯恩斯坦多项式
        def bernstein(i, n, t):
            return self._factorial(n) / (self._factorial(i) * self._factorial(n - i)) * \
                   (t ** i) * ((1 - t) ** (n - i))

        # 双变量 Bezier
        point = np.zeros(3)
        for i in range(4):
            for j in range(4):
                b_i = bernstein(i, 3, u)
                b_j = bernstein(j, 3, v)
                point += cp[i][j] * b_i * b_j

        return point

    def normal(self, u, v, epsilon=0.001):
        """
        计算 Bezier 曲面的法线（数值方法）

        参数:
            u, v: 参数坐标
            epsilon: 微分步长
        返回:
            normal: 法线向量
        """
        p = self.evaluate(u, v)
        p_u = self.evaluate(u + epsilon, v)
        p_v = self.evaluate(u, v + epsilon)

        # 切向量
        t_u = (p_u - p) / epsilon
        t_v = (p_v - p) / epsilon

        # 法线 = 切向量叉积
        n = np.cross(t_u, t_v)
        norm = np.linalg.norm(n)
        if norm > 0:
            n = n / norm

        return n

    def _factorial(self, n):
        """阶乘"""
        if n <= 1:
            return 1
        return n * self._factorial(n - 1)


class PN_Triangle:
    """
    PN-Triangles（Point Normal Triangles）

    一种基于顶点和法线的曲面细分方法，
    不需要额外的曲面接种点数据。
    """

    def __init__(self, v0, v1, v2, n0, n1, n2):
        """
        初始化 PN-Triangle

        参数:
            v0, v1, v2: 三角形顶点
            n0, n1, n2: 各顶点的法线
        """
        self.v0 = np.array(v0, dtype=float)
        self.v1 = np.array(v1, dtype=float)
        self.v2 = np.array(v2, dtype=float)
        self.n0 = np.array(n0, dtype=float) / np.linalg.norm(n0)
        self.n1 = np.array(n1, dtype=float) / np.linalg.norm(n1)
        self.n2 = np.array(n2, dtype=float) / np.linalg.norm(n2)

    def compute_control_points(self):
        """
        计算 PN-Triangle 的 10 个控制点

        基于原始三角形顶点和法线计算 Bezier 控制点。
        """
        v0, v1, v2 = self.v0, self.v1, self.v2
        n0, n1, n2 = self.n0, self.n1, self.n2

        # 边中点
        w0 = (v0 + v1) / 2
        w1 = (v1 + v2) / 2
        w2 = (v2 + v0) / 2

        # 边向量
        e0 = v1 - v0
        e1 = v2 - v1
        e2 = v0 - v2

        # 计算弯曲点
        b012 = (v0 + v1 + v2) / 3

        # 控制点
        b0 = v0
        b1 = v1
        b2 = v2
        b3 = w0 + (n0 + n1) / 4 * np.dot(e0, e0) / (np.dot(n0 + n1, e0) + 1e-8)
        b4 = w1 + (n1 + n2) / 4 * np.dot(e1, e1) / (np.dot(n1 + n2, e1) + 1e-8)
        b5 = w2 + (n2 + n0) / 4 * np.dot(e2, e2) / (np.dot(n2 + n0, e2) + 1e-8)

        # 三个角点的切平面交点
        b6 = (v0 + v1 + v2) / 3

        self.control_points = [b0, b1, b2, b3, b4, b5, b6, b012, w0, w1, w2]
        return self.control_points

    def evaluate(self, u, v, w):
        """
        计算 PN-Triangle 在重心坐标 (u, v, w) 处的位置

        参数:
            u, v, w: 重心坐标 (u + v + w = 1)
        返回:
            point: 3D 位置
        """
        if not hasattr(self, 'control_points'):
            self.compute_control_points()

        cp = self.control_points

        # 简化的位置计算
        # 实际需要完整的二次 Bezier 曲面公式
        P = u * cp[0] + v * cp[1] + w * cp[2]

        # 添加弯曲修正
        b3 = cp[3] if len(cp) > 3 else cp[0]
        b4 = cp[4] if len(cp) > 4 else cp[1]
        b5 = cp[5] if len(cp) > 5 else cp[2]

        P += 4 * (u * v * (b3 - 0.5 * (cp[0] + cp[1])) +
                  v * w * (b4 - 0.5 * (cp[1] + cp[2])) +
                  w * u * (b5 - 0.5 * (cp[2] + cp[0])))

        return P


class TessellationFactor:
    """
    细分级别因子计算

    决定在屏幕上的每个三角形应该细分多少。
    """

    @staticmethod
    def compute_edge_factor(screen_pos0, screen_pos1, screen_size_factor=0.02):
        """
        根据屏幕空间距离计算边缘细分级别

        参数:
            screen_pos0, screen_pos1: 三角形两个顶点的屏幕位置
            screen_size_factor: 屏幕大小因子
        返回:
            factor: 细分因子
        """
        dist = np.linalg.norm(screen_pos1 - screen_pos0)
        factor = dist * screen_size_factor
        return max(1.0, min(factor, 64.0))  # 限制在 1-64

    @staticmethod
    def compute_distance_factor(world_pos, camera_pos, min_dist=1.0, max_dist=100.0):
        """
        根据到相机距离计算细分级别

        参数:
            world_pos: 世界空间位置
            camera_pos: 相机位置
            min_dist: 最近距离（最高细分）
            max_dist: 最远距离（最低细分）
        返回:
            factor: 细分因子
        """
        dist = np.linalg.norm(world_pos - camera_pos)
        t = (dist - min_dist) / (max_dist - min_dist)
        t = max(0, min(1, t))
        # 距离越远，细分越少
        return 64.0 * (1 - t)

    @staticmethod
    def compute_curvature_factor(screen_pos0, screen_pos1, screen_pos2,
                                 proj_matrix):
        """
        根据曲率计算自适应细分

        参数:
            screen_pos0, screen_pos1, screen_pos2: 屏幕位置
            proj_matrix: 投影矩阵
        返回:
            factor: 细分因子
        """
        # 计算屏幕空间曲率
        edge0 = screen_pos1 - screen_pos0
        edge1 = screen_pos2 - screen_pos1
        edge2 = screen_pos0 - screen_pos2

        # 检测边缘弯曲
        curvature = np.abs(np.cross(edge0, edge1) / (np.linalg.norm(edge0) * np.linalg.norm(edge1) + 1e-8))
        factor = 1.0 + curvature * 10
        return max(1.0, min(factor, 64.0))


class TessellationStage:
    """
    细分阶段管理

    管理 Hull Shader、Fixed Tessellator、Domain Shader 的协同工作。
    """

    def __init__(self, max_tess_level=64):
        """
        初始化细分阶段

        参数:
            max_tess_level: 最大细分级别
        """
        self.max_tess_level = max_tess_level
        self.tess_levels = [1.0, 1.0, 1.0, 1.0]  # [inside, inside, edge0, edge1, edge2]

    def set_tessellation_levels(self, edge0, edge1, edge2, inside=None):
        """
        设置细分级别

        参数:
            edge0, edge1, edge2: 边缘细分级别
            inside: 内部细分级别（默认同 edge0）
        """
        self.tess_levels = [
            edge0, edge1, edge2,
            inside if inside is not None else (edge0 + edge1 + edge2) / 3
        ]

    def generate_subdivision_points(self, u0, v0, w0, u1, v1, w1, u2, v2, w2):
        """
        生成三角形细分点

        使用重心坐标生成均匀细分的点。

        参数:
            u0, v0, w0: 顶点0 的重心坐标
            u1, v1, w1: 顶点1 的重心坐标
            u2, v2, w2: 顶点2 的重心坐标
        返回:
            points: 新的重心坐标列表
        """
        inside_level = self.tess_levels[3]

        # 生成沿各边的点
        edge_points = []

        for i in range(int(inside_level) + 1):
            t = i / inside_level
            # 沿边 0-1
            edge_points.append((
                u0 + t * (u1 - u0),
                v0 + t * (v1 - v0),
                w0 + t * (w1 - w0)
            ))
            # 沿边 1-2
            edge_points.append((
                u1 + t * (u2 - u1),
                v1 + t * (v2 - v1),
                w1 + t * (w2 - w1)
            ))
            # 沿边 2-0
            edge_points.append((
                u2 + t * (u0 - u2),
                v2 + t * (v0 - v2),
                w2 + t * (w0 - w2)
            ))

        return edge_points

    def domain_shader_barycentric(self, tri, u, v, w):
        """
        域着色器 - 计算重心坐标位置

        参数:
            tri: 原始三角形
            u, v, w: 重心坐标
        返回:
            position: 新顶点的世界位置
            normal: 新顶点的法线
        """
        # 线性插值位置
        v0, v1, v2 = tri.vertices
        n0, n1, n2 = tri.normals if hasattr(tri, 'normals') else [None]*3

        position = u * v0 + v * v1 + w * v2

        # 法线插值
        if n0 is not None:
            normal = u * n0 + v * n1 + w * n2
            normal = normal / np.linalg.norm(normal)
        else:
            normal = np.array([0, 0, 1])

        return position, normal


def generate_tessellated_mesh(base_mesh, tess_level=2):
    """
    对基础网格进行细分

    参数:
        base_mesh: 基础网格
        tess_level: 细分级别
    返回:
        new_mesh: 细分后的网格
    """
    new_vertices = []
    new_faces = []

    for face in base_mesh.get('faces', []):
        vertices = face.get('vertices', [])
        if len(vertices) == 3:
            # 三角形细分
            sub_verts, sub_faces = _tessellate_triangle(vertices, tess_level)
            new_vertices.extend(sub_verts)
            new_faces.extend([[v + len(new_vertices) - len(sub_verts) for v in f]
                             for f in sub_faces])

    return {'vertices': new_vertices, 'faces': new_faces}


def _tessellate_triangle(vertices, level):
    """
    细分单个三角形

    参数:
        vertices: [v0, v1, v2]
        level: 细分级别
    返回:
        sub_vertices: 细分后的顶点
        sub_faces: 细分后的面
    """
    v0, v1, v2 = vertices

    # 生成网格点
    points = []
    for i in range(level + 1):
        for j in range(level + 1 - i):
            u = i / level
            v = j / level
            w = 1 - u - v
            point = u * v0 + v * v1 + w * v2
            points.append(point)

    # 生成三角形面
    faces = []
    for i in range(level):
        for j in range(level - i):
            idx00 = sum(range(level + 1 - i)) + j
            idx10 = idx00 + 1
            idx01 = sum(range(level + 2 - i)) + j
            idx11 = idx01 + 1

            if j < level - i - 1:
                faces.append([idx00, idx10, idx11])
                faces.append([idx00, idx11, idx01])
            else:
                faces.append([idx00, idx10, idx01])

    return points, faces


if __name__ == "__main__":
    print("=== 曲面细分测试 ===")

    # PN-Triangle 测试
    print("\n1. PN-Triangle 测试")
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.5, 1.0, 0.0])
    n0 = np.array([0.0, 0.0, 1.0])
    n1 = np.array([0.0, 0.0, 1.0])
    n2 = np.array([0.0, 0.0, 1.0])

    pn = PN_Triangle(v0, v1, v2, n0, n1, n2)
    cp = pn.compute_control_points()
    print(f"控制点数: {len(cp)}")
    print(f"控制点 0-2 (顶点): {cp[0].round(2)}, {cp[1].round(2)}, {cp[2].round(2)}")
    print(f"控制点 3 (边中点修正): {cp[3].round(3)}")

    # 评估几个点
    print("\n细分点采样:")
    for u, v, w in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (0.33, 0.33, 0.34)]:
        p = pn.evaluate(u, v, w)
        print(f"  (u={u}, v={v}, w={w}): {p.round(3)}")

    # Bezier 曲面测试
    print("\n2. Bezier 曲面测试")
    cp_grid = np.array([
        [[0, 0, 0], [0, 1, 0.2], [0, 2, 0.3], [0, 3, 0]],
        [[1, 0, 0.2], [1, 1, 0.5], [1, 2, 0.7], [1, 3, 0.2]],
        [[2, 0, 0.3], [2, 1, 0.7], [2, 2, 0.9], [2, 3, 0.3]],
        [[3, 0, 0], [3, 1, 0.2], [3, 2, 0.3], [3, 3, 0]]
    ], dtype=float)

    bezier = BezierPatch(cp_grid)
    print("Bezier 曲面角点:")
    print(f"  (0,0): {bezier.evaluate(0, 0).round(3)}")
    print(f"  (1,0): {bezier.evaluate(1, 0).round(3)}")
    print(f"  (0,1): {bezier.evaluate(0, 1).round(3)}")
    print(f"  (1,1): {bezier.evaluate(1, 1).round(3)}")

    # 曲面中心
    print(f"  (0.5,0.5): {bezier.evaluate(0.5, 0.5).round(3)}")

    # 法线测试
    n = bezier.normal(0.5, 0.5)
    print(f"  法线 (0.5,0.5): {n.round(3)}")

    # 细分级别计算
    print("\n3. 细分级别因子")
    screen_pos0 = np.array([100, 100, 0])
    screen_pos1 = np.array([200, 100, 0])
    screen_pos2 = np.array([150, 200, 0])

    factor = TessellationFactor.compute_edge_factor(screen_pos0, screen_pos1)
    print(f"  边缘细分因子 (100px): {factor:.1f}")

    factor = TessellationFactor.compute_distance_factor(
        np.array([0, 0, 10]), np.array([0, 0, -2])
    )
    print(f"  距离因子 (dist=12): {factor:.1f}")

    # 细分阶段
    print("\n4. 细分阶段测试")
    tess = TessellationStage(max_tess_level=64)
    tess.set_tessellation_levels(edge0=4, edge1=4, edge2=4, inside=4)

    sub_points = tess.generate_subdivision_points(1, 0, 0, 0, 1, 0, 0, 0, 1)
    print(f"  生成细分点数量: {len(sub_points)}")
    print(f"  细分级别: {tess.tess_levels}")

    # 网格细分测试
    print("\n5. 网格细分测试")
    base_mesh = {
        'faces': [
            {'vertices': [np.array([0,0,0]), np.array([1,0,0]), np.array([0.5,1,0])]}
        ]
    }

    for level in [1, 2, 3, 4]:
        result = generate_tessellated_mesh(base_mesh, tess_level=level)
        print(f"  level={level}: {len(result['vertices'])} 顶点, {len(result['faces'])} 面")

    print("\n曲面细分测试完成!")

# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / catmull_clark

本文件实现 catmull_clark 相关的算法功能。
"""

import numpy as np


class QuadVertex:
    """四边形网格顶点"""

    def __init__(self, position, index=None):
        self.position = np.array(position, dtype=float)
        self.index = index
        self.new_position = None


class QuadEdge:
    """边"""

    def __init__(self, v1, v2, index=None):
        self.v1 = v1
        self.v2 = v2
        self.index = index
        self.edge_point = None
        self.faces = []  # 邻接面


class QuadFace:
    """四边形面"""

    def __init__(self, v0, v1, v2, v3):
        self.vertices = [v0, v1, v2, v3]
        self.center = None  # 面心点
        self.edges = [None, None, None, None]


class CatmullClarkSubdivider:
    """
    Catmull-Clark 细分

    实现 Catmull-Clark 细分曲面算法。
    支持四边形网格（也兼容三角形，自动处理）。
    """

    def __init__(self):
        self.vertices = []
        self.edges = []
        self.faces = []

    def add_vertex(self, position):
        """添加顶点"""
        v = QuadVertex(position, len(self.vertices))
        self.vertices.append(v)
        return v

    def add_face(self, v0_idx, v1_idx, v2_idx, v3_idx):
        """添加四边形面"""
        v0 = self.vertices[v0_idx]
        v1 = self.vertices[v1_idx]
        v2 = self.vertices[v2_idx]
        v3 = self.vertices[v3_idx]

        f = QuadFace(v0, v1, v2, v3)
        self.faces.append(f)

        # 创建或获取边
        edges = [
            self._get_or_create_edge(v0, v1, f),
            self._get_or_create_edge(v1, v2, f),
            self._get_or_create_edge(v2, v3, f),
            self._get_or_create_edge(v3, v0, f)
        ]
        f.edges = edges

        return f

    def _get_or_create_edge(self, v1, v2, face):
        """获取或创建边"""
        # 检查现有边
        for e in v1.edge_corners if hasattr(v1, 'edge_corners') else []:
            if e is v2:
                e.faces.append(face)
                return e

        # 创建新边
        edge = QuadEdge(v1, v2, len(self.edges))
        edge.faces.append(face)
        self.edges.append(edge)

        # 关联到顶点
        if not hasattr(v1, 'edges'):
            v1.edges = []
        if not hasattr(v2, 'edges'):
            v2.edges = []
        v1.edges.append(edge)
        v2.edges.append(edge)

        return edge

    def subdivide(self):
        """
        执行一次 Catmull-Clark 细分

        返回:
            new_mesh: 细分后的新网格
        """
        # 1. 计算面心点
        for face in self.faces:
            face.center = np.mean([v.position for v in face.vertices], axis=0)

        # 2. 计算边心点
        for edge in self.edges:
            edge.edge_point = self._compute_edge_point(edge)

        # 3. 计算顶点新位置
        for vertex in self.vertices:
            vertex.new_position = self._compute_vertex_new_position(vertex)

        # 4. 构建新网格
        new_mesh = CatmullClarkSubdivider()

        # 复制顶点到新网格（带新位置）
        vertex_map = {}  # 旧顶点 -> 新网格中的顶点
        for v in self.vertices:
            new_v = new_mesh.add_vertex(v.new_position)
            vertex_map[v] = new_v

        # 添加面心点作为新顶点
        face_point_map = {}  # 旧面 -> 新面心点顶点
        for f in self.faces:
            new_fv = new_mesh.add_vertex(f.center)
            face_point_map[f] = new_fv

        # 添加边心点作为新顶点
        edge_point_map = {}  # 旧边 -> 新边心点顶点
        for e in self.edges:
            new_ev = new_mesh.add_vertex(e.edge_point)
            edge_point_map[e] = new_ev

        # 5. 重新连接面
        for face in self.faces:
            self._subdivide_face_quad(face, new_mesh, vertex_map,
                                      face_point_map, edge_point_map)

        return new_mesh

    def _compute_edge_point(self, edge):
        """
        计算边心点

        E = (V1 + V2 + F1 + F2) / 4
        如果是边界边：E = (V1 + V2) / 2
        """
        v1, v2 = edge.v1, edge.v2
        if len(edge.faces) == 2:
            # 内部边
            f1_center, f2_center = edge.faces[0].center, edge.faces[1].center
            edge_point = (v1.position + v2.position + f1_center + f2_center) / 4.0
        else:
            # 边界边
            edge_point = (v1.position + v2.position) / 2.0

        return edge_point

    def _compute_vertex_new_position(self, vertex):
        """
        计算顶点新位置

        P' = (Q + 2R + (n-3)P) / n
        """
        if not hasattr(vertex, 'edges') or not vertex.edges:
            return vertex.position.copy()

        n = len(vertex.edges)  # 价（邻接边数）

        # 计算 Q：邻接面心点的平均
        q_points = []
        for edge in vertex.edges:
            for face in edge.faces:
                q_points.append(face.center)

        if q_points:
            Q = np.mean(q_points, axis=0)
        else:
            Q = vertex.position

        # 计算 R：邻接边中点的平均
        r_points = []
        for edge in vertex.edges:
            r_points.append((edge.v1.position + edge.v2.position) / 2.0)

        if r_points:
            R = np.mean(r_points, axis=0)
        else:
            R = vertex.position

        # 新位置
        if n >= 3:
            P_new = (Q + 2 * R + (n - 3) * vertex.position) / n
        else:
            # 特殊情况
            P_new = vertex.position

        return P_new

    def _subdivide_face_quad(self, face, new_mesh, vertex_map,
                            face_point_map, edge_point_map):
        """
        细分四边形面

        每个四边形面变成 4 个小四边形
        """
        # 面顶点（原始网格顶点）
        v0, v1, v2, v3 = [vertex_map[v] for v in face.vertices]

        # 边心点
        e0 = edge_point_map[face.edges[0]]  # v0-v1
        e1 = edge_point_map[face.edges[1]]  # v1-v2
        e2 = edge_point_map[face.edges[2]]  # v2-v3
        e3 = edge_point_map[face.edges[3]]  # v3-v0

        # 面心点
        f = face_point_map[face]

        # 创建 4 个新四边形
        # 左上
        new_mesh.add_face_quad(
            v0.index, e0.index, f.index, e3.index
        )
        # 右上
        new_mesh.add_face_quad(
            e0.index, v1.index, e1.index, f.index
        )
        # 右下
        new_mesh.add_face_quad(
            f.index, e1.index, v2.index, e2.index
        )
        # 左下
        new_mesh.add_face_quad(
            e3.index, f.index, e2.index, v3.index
        )

    def add_face_quad(self, v0_idx, v1_idx, v2_idx, v3_idx):
        """添加四边形面（兼容方法）"""
        return self.add_face(v0_idx, v1_idx, v2_idx, v3_idx)


def create_cube_quad():
    """创建立方体网格（四边形面）"""
    mesh = CatmullClarkSubdivider()

    # 创建立方体的 8 个顶点
    for x, y, z in [(0,0,0), (1,0,0), (1,1,0), (0,1,0),
                    (0,0,1), (1,0,1), (1,1,1), (0,1,1)]:
        mesh.add_vertex([x, y, z])

    # 创建立方体的 6 个四边形面
    # 前面
    mesh.add_face(0, 1, 2, 3)
    # 后面
    mesh.add_face(5, 4, 7, 6)
    # 下面
    mesh.add_face(0, 4, 5, 1)
    # 上面
    mesh.add_face(3, 2, 6, 7)
    # 左面
    mesh.add_face(4, 0, 3, 7)
    # 右面
    mesh.add_face(1, 5, 6, 2)

    return mesh


def create_grid_plane(nx=4, ny=4):
    """创建网格平面"""
    mesh = CatmullClarkSubdivider()

    # 创建顶点
    for y in range(ny + 1):
        for x in range(nx + 1):
            mesh.add_vertex([x / nx, y / ny, 0])

    # 创建四边形面
    for y in range(ny):
        for x in range(nx):
            v0 = y * (nx + 1) + x
            v1 = v0 + 1
            v2 = v0 + (nx + 1) + 1
            v3 = v0 + (nx + 1)
            mesh.add_face(v0, v1, v2, v3)

    return mesh


def mesh_stats(mesh):
    """获取网格统计"""
    return {
        'n_vertices': len(mesh.vertices),
        'n_edges': len(mesh.edges),
        'n_faces': len(mesh.faces)
    }


if __name__ == "__main__":
    print("=== Catmull-Clark 细分算法测试 ===")

    # 创建并细分立方体
    print("\n1. 立方体细分测试")
    cube = create_cube_quad()
    print(f"原始立方体: {mesh_stats(cube)}")

    cube1 = cube.subdivide()
    print(f"一次细分: {mesh_stats(cube1)}")

    cube2 = cube1.subdivide()
    print(f"二次细分: {mesh_stats(cube2)}")

    # 验证欧拉公式
    print("\n2. 欧拉公式验证 (V - E + F = 2)")
    for name, m in [("原始", cube), ("一次细分", cube1), ("二次细分", cube2)]:
        s = mesh_stats(m)
        euler = s['n_vertices'] - s['n_edges'] + s['n_faces']
        print(f"  {name}: V={s['n_vertices']}, E={s['n_edges']}, F={s['n_faces']}, V-E+F={euler}")

    # 创建并细分网格平面
    print("\n3. 网格平面细分测试")
    plane = create_grid_plane(2, 2)
    print(f"原始平面 (2x2): {mesh_stats(plane)}")

    plane1 = plane.subdivide()
    print(f"一次细分: {mesh_stats(plane1)}")

    plane2 = plane1.subdivide()
    print(f"二次细分: {mesh_stats(plane2)}")

    # 顶点位置验证
    print("\n4. 立方体顶点位置验证")
    print("原始顶点:")
    for i, v in enumerate(cube.vertices):
        print(f"  V{i}: ({v.position[0]:.1f}, {v.position[1]:.1f}, {v.position[2]:.1f})")
        print(f"      新位置: ({v.new_position[0]:.3f}, {v.new_position[1]:.3f}, {v.new_position[2]:.3f})")

    # 面心点验证
    print("\n5. 面心点示例")
    for i, f in enumerate(cube.faces):
        print(f"  Face {i}: center=({f.center[0]:.3f}, {f.center[1]:.3f}, {f.center[2]:.3f})")

    # 边心点验证
    print("\n6. 边心点示例")
    for i, e in enumerate(cube.edges[:3]):
        print(f"  Edge {i}: ({e.v1.position[0]:.1f},...) -> edge_point=({e.edge_point[0]:.3f},...)")

    print("\nCatmull-Clark 细分算法测试完成!")

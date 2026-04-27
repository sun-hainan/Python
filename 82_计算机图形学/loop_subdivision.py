# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / loop_subdivision



本文件实现 loop_subdivision 相关的算法功能。

"""



import numpy as np

import math





class Vertex:

    """顶点"""



    def __init__(self, position, index=None):

        self.position = np.array(position, dtype=float)

        self.index = index  # 顶点索引

        self.new_position = None  # 细分后的新位置

        self.edge_corners = []  # 关联的边角



    def add_edge_corner(self, edge_corner):

        """添加关联的边角"""

        self.edge_corners.append(edge_corner)





class Edge:

    """边"""



    def __init__(self, v1, v2, index=None):

        self.v1 = v1

        self.v2 = v2

        self.index = index

        self.new_vertex = None  # 边中点创建的新顶点





class Face:

    """面（三角形）"""



    def __init__(self, v0, v1, v2):

        self.vertices = [v0, v1, v2]

        self.edges = [None, None, None]  # 三个边

        self.edge_corners = []  # 边角





class EdgeCorner:

    """

    边角（Edge Corner）



    面-边-顶点三元组的表示。

    存储顶点和其在该边上的对边信息。

    """



    def __init__(self, face, edge, vertex):

        self.face = face

        self.edge = edge

        self.vertex = vertex





class LoopSubdivider:

    """

    Loop 细分



    实现 Loop 细分算法，用于平滑三角形网格。

    """



    def __init__(self):

        self.vertices = []

        self.edges = []

        self.faces = []



    def add_vertex(self, position):

        """添加顶点"""

        v = Vertex(position, len(self.vertices))

        self.vertices.append(v)

        return v



    def add_face(self, v0_idx, v1_idx, v2_idx):

        """添加三角形面"""

        v0 = self.vertices[v0_idx]

        v1 = self.vertices[v1_idx]

        v2 = self.vertices[v2_idx]



        f = Face(v0, v1, v2)

        self.faces.append(f)



        # 创建边

        edges = [

            self._get_or_create_edge(v0, v1),

            self._get_or_create_edge(v1, v2),

            self._get_or_create_edge(v2, v0)

        ]

        f.edges = edges



        # 创建边角并关联

        for i, (edge, vi) in enumerate(zip(edges, [v0, v1, v2])):

            corner = EdgeCorner(f, edge, vi)

            f.edge_corners.append(corner)

            vi.add_edge_corner(corner)



        return f



    def _get_or_create_edge(self, v1, v2):

        """获取或创建边"""

        # 查找现有边

        for edge in v1.edge_corners[0].vertex.edge_corners if v1.edge_corners else []:

            other_v = edge.edge.v1 if edge.edge.v2 is edge.vertex else edge.edge.v2

            if other_v is v2:

                return edge.edge



        # 创建新边

        edge = Edge(v1, v2, len(self.edges))

        self.edges.append(edge)

        return edge



    def subdivide(self):

        """

        执行一次 Loop 细分



        返回:

            subdivider: 新的细分网格的 LoopSubdivider

        """

        # 1. 创建边中点新顶点

        for edge in self.edges:

            midpoint = (edge.v1.position + edge.v2.position) / 2.0

            new_v = Vertex(midpoint, len(self.vertices))

            edge.new_vertex = new_v



        # 2. 计算原有顶点的新位置

        for vertex in self.vertices:

            vertex.new_position = self._compute_new_vertex_position(vertex)



        # 3. 创建新网格

        new_mesh = LoopSubdivider()



        # 添加原有顶点（带新位置）

        for vertex in self.vertices:

            new_mesh.add_vertex(vertex.new_position)



        # 4. 对每个面进行细分

        for face in self.faces:

            self._subdivide_face(face, new_mesh)



        return new_mesh



    def _compute_new_vertex_position(self, vertex):

        """

        计算顶点的新位置



        参数:

            vertex: 原始顶点

        返回:

            new_pos: 新位置

        """

        corners = vertex.edge_corners

        if not corners:

            return vertex.position.copy()



        # 获取邻接顶点

        neighbor_1 = corners[0].edge.v1 if corners[0].edge.v2 is vertex else corners[0].edge.v2

        neighbor_2 = corners[1].edge.v1 if corners[1].edge.v2 is vertex else corners[1].edge.v2

        neighbor_3 = corners[2].edge.v1 if len(corners) > 2 and corners[2].edge.v2 is vertex else corners[2].edge.v2



        m = len(corners)  # 价（邻接边数）



        if m == 2:

            # 边界顶点：使用边界规则

            p = vertex.position

            n1 = neighbor_1.position

            n2 = neighbor_2.position

            new_pos = (3.0 / 4.0) * p + (1.0 / 8.0) * (n1 + n2)

        else:

            # 内部顶点

            beta = 3.0 / (16.0 * m) if m < 3 else 3.0 / (8.0 * m)



            new_pos = (1.0 - m * beta) * vertex.position



            # 累加邻接顶点

            sum_neighbors = np.zeros(3)

            for corner in corners:

                neighbor = corner.edge.v1 if corner.edge.v2 is vertex else corner.edge.v2

                sum_neighbors += neighbor.position



            new_pos += beta * sum_neighbors



        return new_pos



    def _subdivide_face(self, face, new_mesh):

        """

        细分一个面



        原面被分成 4 个小面：

            1

           / \

        E1 *--* E3

         /  *  \

        0 *--*--* 2

         \  *  /

          E2 *--* E1

             \ /

              1



        """

        v0, v1, v2 = face.vertices

        e01 = face.edges[0]

        e12 = face.edges[1]

        e20 = face.edges[2]



        # 边中点顶点

        m01 = e01.new_vertex

        m12 = e12.new_vertex

        m20 = e20.new_vertex



        # 创建 4 个新三角形

        # 中心三角形: m01, m12, m20

        # 周围 3 个三角形

        new_mesh.add_face(v0.index, m01.index, m20.index)

        new_mesh.add_face(m01.index, v1.index, m12.index)

        new_mesh.add_face(m20.index, m12.index, v2.index)

        new_mesh.add_face(m01.index, m12.index, m20.index)





def create_cube():

    """创建立方体网格"""

    mesh = LoopSubdivider()



    # 创建立方体的 8 个顶点

    for x, y, z in [(0,0,0), (1,0,0), (1,1,0), (0,1,0),

                    (0,0,1), (1,0,1), (1,1,1), (0,1,1)]:

        mesh.add_vertex([x, y, z])



    # 创建立方体的 12 个三角形（每个面 2 个）

    # 前面

    mesh.add_face(0, 1, 2)

    mesh.add_face(0, 2, 3)

    # 后面

    mesh.add_face(4, 6, 5)

    mesh.add_face(4, 7, 6)

    # 左面

    mesh.add_face(0, 3, 7)

    mesh.add_face(0, 7, 4)

    # 右面

    mesh.add_face(1, 5, 6)

    mesh.add_face(1, 6, 2)

    # 上面

    mesh.add_face(3, 2, 6)

    mesh.add_face(3, 6, 7)

    # 下面

    mesh.add_face(0, 4, 5)

    mesh.add_face(0, 5, 1)



    return mesh





def create_icosphere(subdivisions=1):

    """创建二十面体球体"""

    t = (1 + np.sqrt(5)) / 2  # 黄金比例



    mesh = LoopSubdivider()



    # 二十面体的 12 个顶点

    verts = [

        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],

        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],

        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]

    ]



    for v in verts:

        mesh.add_vertex(v)



    # 二十面体的 20 个三角形

    faces = [

        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),

        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),

        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),

        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)

    ]



    for f in faces:

        mesh.add_face(f[0], f[1], f[2])



    return mesh





def mesh_stats(mesh):

    """获取网格统计信息"""

    return {

        'n_vertices': len(mesh.vertices),

        'n_edges': len(mesh.edges),

        'n_faces': len(mesh.faces)

    }





if __name__ == "__main__":

    print("=== Loop 细分算法测试 ===")



    # 创建并细分立方体

    print("\n1. 立方体细分测试")

    cube = create_cube()

    print(f"原始立方体: {mesh_stats(cube)}")



    # 细分一次

    cube1 = cube.subdivide()

    print(f"一次细分: {mesh_stats(cube1)}")



    # 细分两次

    cube2 = cube1.subdivide()

    print(f"二次细分: {mesh_stats(cube2)}")



    # 细分三次

    cube3 = cube2.subdivide()

    print(f"三次细分: {mesh_stats(cube3)}")



    # 验证欧拉公式

    print("\n2. 欧拉公式验证 (V - E + F = 2)")

    for name, m in [("原始", cube), ("一次细分", cube1),

                    ("二次细分", cube2), ("三次细分", cube3)]:

        s = mesh_stats(m)

        euler = s['n_vertices'] - s['n_edges'] + s['n_faces']

        print(f"  {name}: V={s['n_vertices']}, E={s['n_edges']}, F={s['n_faces']}, "

              f"V-E+F={euler}")



    # 创建并细分二十面体球体

    print("\n3. 二十面体球体细分测试")

    ico = create_icosphere()

    print(f"原始二十面体: {mesh_stats(ico)}")



    ico1 = ico.subdivide()

    print(f"一次细分: {mesh_stats(ico1)}")



    ico2 = ico1.subdivide()

    print(f"二次细分: {mesh_stats(ico2)}")



    # 顶点位置验证

    print("\n4. 顶点位置验证")

    print("立方体原始顶点位置:")

    for i, v in enumerate(cube.vertices):

        print(f"  V{i}: {v.position}")

        print(f"      新位置: {v.new_position}")



    # 测试细分后的顶点

    print("\n立方体一次细分后的顶点示例:")

    for i in range(min(6, len(cube1.vertices))):

        v = cube1.vertices[i]

        print(f"  V{i}: pos=({v.position[0]:.3f}, {v.position[1]:.3f}, {v.position[2]:.3f})")



    print("\nLoop 细分算法测试完成!")


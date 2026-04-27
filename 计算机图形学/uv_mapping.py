# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / uv_mapping



本文件实现 uv_mapping 相关的算法功能。

"""



import numpy as np

import math





class UVCoord:

    """UV 坐标"""



    def __init__(self, u=0.0, v=0.0):

        self.u = u

        self.v = v



    def __repr__(self):

        return f"UV({self.u:.3f}, {self.v:.3f})"





class Vertex:

    """带 UV 的顶点"""



    def __init__(self, position, normal=None, uv=None):

        self.position = np.array(position, dtype=float)

        self.normal = np.array(normal, dtype=float) if normal else np.array([0, 0, 1])

        self.uv = uv if uv else UVCoord()





class Triangle:

    """三角形面"""



    def __init__(self, v0, v1, v2):

        self.v0 = v0

        self.v1 = v1

        self.v2 = v2





def planar_projection(vertex, axis='z'):

    """

    平面投影 UV



    将顶点沿指定轴方向投影到 2D 平面。



    参数:

        vertex: Vertex 对象

        axis: 投影轴 ('x', 'y', 'z')

    返回:

        uv: UVCoord

    """

    p = vertex.position

    if axis == 'x':

        uv = UVCoord(p[1], p[2])

    elif axis == 'y':

        uv = UVCoord(p[0], p[2])

    else:  # 'z'

        uv = UVCoord(p[0], p[1])

    return uv





def spherical_mapping(vertex, center=np.array([0, 0, 0])):

    """

    球面映射 UV



    适用于球体或近似球形物体。



    参数:

        vertex: Vertex 对象

        center: 球心

    返回:

        uv: UVCoord

    """

    p = vertex.position - center

    r = np.linalg.norm(p)

    if r < 1e-10:

        return UVCoord(0.5, 0.5)



    # 归一化

    x, y, z = p / r



    # 球面坐标

    # θ = atan2(z, x) -> u [0, 1]

    # φ = acos(y) -> v [0, 1]

    u = (math.atan2(z, x) + math.pi) / (2 * math.pi)

    v = math.acos(np.clip(y, -1, 1)) / math.pi



    return UVCoord(u, v)





def cylindrical_mapping(vertex, axis=np.array([0, 1, 0])):

    """

    圆柱投影 UV



    适用于圆柱体或带圆柱部分的对象。



    参数:

        vertex: Vertex 对象

        axis: 圆柱轴方向

    返回:

        uv: UVCoord

    """

    p = vertex.position

    axis = axis / np.linalg.norm(axis)



    # 投影到垂直于轴的平面

    d = p - np.dot(p, axis) * axis



    # 计算角度

    x, y = d[0], d[1]

    u = (math.atan2(y, x) + math.pi) / (2 * math.pi)



    # 高度

    v = np.dot(p, axis)



    return UVCoord(u, v)





def cube_mapping(vertex, size=1.0):

    """

    立方体映射 UV



    将顶点映射到立方体表面，然后展开为 UV。



    参数:

        vertex: Vertex 对象

        size: 立方体大小

    返回:

        uv: UVCoord

    """

    p = vertex.position

    abs_p = np.abs(p)

    normal = vertex.normal



    # 确定投影面

    if abs_p[0] > abs_p[1] and abs_p[0] > abs_p[2]:

        # X 面

        if normal[0] > 0:

            u, v = p[2], p[1]

        else:

            u, v = -p[2], p[1]

    elif abs_p[1] > abs_p[2]:

        # Y 面

        if normal[1] > 0:

            u, v = p[0], p[2]

        else:

            u, v = p[0], -p[2]

    else:

        # Z 面

        if normal[2] > 0:

            u, v = p[0], p[1]

        else:

            u, v = -p[0], p[1]



    # 归一化到 [0, 1]

    u = (u / size + 1) / 2

    v = (v / size + 1) / 2



    return UVCoord(np.clip(u, 0, 1), np.clip(v, 0, 1))





def generate_uv_for_mesh(vertices, method='spherical'):

    """

    为网格生成 UV 坐标



    参数:

        vertices: Vertex 列表

        method: 映射方法 ('planar', 'spherical', 'cylindrical', 'cube')

    返回:

        填充了 UV 的顶点列表

    """

    for v in vertices:

        if method == 'planar':

            v.uv = planar_projection(v)

        elif method == 'spherical':

            v.uv = spherical_mapping(v)

        elif method == 'cylindrical':

            v.uv = cylindrical_mapping(v)

        elif method == 'cube':

            v.uv = cube_mapping(v)

        else:

            v.uv = UVCoord(0.5, 0.5)



    return vertices





def bilinear_sample(image, u, v):

    """

    双线性纹理采样



    参数:

        image: 2D RGB/N 图像数组 (H, W, C)

        u, v: UV 坐标 [0, 1]

    返回:

        color: 采样颜色

    """

    h, w = image.shape[:2]



    # 转换到像素坐标

    px = u * (w - 1)

    py = v * (h - 1)



    # 取整

    x0 = int(px)

    y0 = int(py)

    x1 = min(x0 + 1, w - 1)

    y1 = min(y0 + 1, h - 1)



    # 插值权重

    fx = px - x0

    fy = py - y0



    # 双线性插值

    c00 = image[y0, x0]

    c10 = image[y0, x1]

    c01 = image[y1, x0]

    c11 = image[y1, x1]



    c0 = c00 * (1 - fx) + c10 * fx

    c1 = c01 * (1 - fx) + c11 * fx

    color = c0 * (1 - fy) + c1 * fy



    return color





def trilinear_sample(volume, u, v, w):

    """

    三线性纹理采样（3D 纹理）



    参数:

        volume: 3D 数组 (D, H, W, C)

        u, v, w: UVW 坐标 [0, 1]

    返回:

        color: 采样颜色

    """

    d, h, w = volume.shape[:3]



    px = u * (w - 1)

    py = v * (h - 1)

    pz = w * (d - 1)



    x0, y0, z0 = int(px), int(py), int(pz)

    x1 = min(x0 + 1, w - 1)

    y1 = min(y0 + 1, h - 1)

    z1 = min(z0 + 1, d - 1)



    fx = px - x0

    fy = py - y0

    fz = pz - z0



    # 8 个角点插值

    c000 = volume[z0, y0, x0]

    c100 = volume[z0, y0, x1]

    c010 = volume[z0, y1, x0]

    c110 = volume[z0, y1, x1]

    c001 = volume[z1, y0, x0]

    c101 = volume[z1, y0, x1]

    c011 = volume[z1, y1, x0]

    c111 = volume[z1, y1, x1]



    # X 方向插值

    c00 = c000 * (1 - fx) + c100 * fx

    c01 = c001 * (1 - fx) + c101 * fx

    c10 = c010 * (1 - fx) + c110 * fx

    c11 = c011 * (1 - fx) + c111 * fx



    # Y 方向插值

    c0 = c00 * (1 - fy) + c10 * fy

    c1 = c01 * (1 - fy) + c11 * fy



    # Z 方向插值

    color = c0 * (1 - fz) + c1 * fz



    return color





class UVAtlas:

    """

    UV 图集管理



    多个纹理合并到一个图集（Atlas）中。

    """



    def __init__(self, atlas_width=512, atlas_height=512):

        """

        初始化 UV 图集



        参数:

            atlas_width: 图集宽度

            atlas_height: 图集高度

        """

        self.atlas_width = atlas_width

        self.atlas_height = atlas_height

        self.textures = {}  # name -> (uv_rect, image)

        self.current_x = 0

        self.current_y = 0

        self.row_height = 0



    def add_texture(self, name, image):

        """

        添加纹理到图集



        参数:

            name: 纹理名称

            image: 纹理图像 (H, W, C)

        返回:

            uv_min, uv_max: UV 坐标范围

        """

        h, w = image.shape[:2]



        # 简单打包策略（行扫描）

        if self.current_x + w > self.atlas_width:

            self.current_x = 0

            self.current_y += self.row_height

            self.row_height = 0



        # UV 范围

        uv_min = UVCoord(self.current_x / self.atlas_width,

                         self.current_y / self.atlas_height)

        uv_max = UVCoord((self.current_x + w) / self.atlas_width,

                         (self.current_y + h) / self.atlas_height)



        # 存储

        self.textures[name] = {

            'rect': (self.current_x, self.current_y, w, h),

            'image': image,

            'uv_min': uv_min,

            'uv_max': uv_max

        }



        # 更新位置

        self.current_x += w

        self.row_height = max(self.row_height, h)



        return uv_min, uv_max



    def sample_texture(self, name, local_u, local_v):

        """

        从图集中采样指定纹理



        参数:

            name: 纹理名称

            local_u, local_v: 纹理内的局部 UV

        返回:

            color: 颜色

        """

        if name not in self.textures:

            return np.array([1.0, 0.0, 1.0])  # 错误颜色（品红）



        info = self.textures[name]

        return bilinear_sample(info['image'], local_u, local_v)





class SimpleUVUnwrap:

    """

    简单 UV 展开



    将 3D 网格表面展开为 2D UV 坐标。

    使用简单的参数化方法（可能不是最优的）。

    """



    def __init__(self, vertices, triangles):

        """

        初始化 UV 展开



        参数:

            vertices: Vertex 列表

            triangles: Triangle 列表

        """

        self.vertices = vertices

        self.triangles = triangles



    def unwrap(self):

        """

        执行 UV 展开



        简化为保角映射。



        返回:

            vertices: 填充了 UV 的顶点

        """

        # 识别主要平面

        normals = [v.normal for v in self.vertices]

        avg_normal = np.mean(normals, axis=0)

        avg_normal = avg_normal / np.linalg.norm(avg_normal)



        # 根据平均法线选择投影平面

        abs_n = np.abs(avg_normal)

        if abs_n[2] >= abs_n[0] and abs_n[2] >= abs_n[1]:

            # Z 主导 -> XY 平面

            for v in self.vertices:

                v.uv = UVCoord(v.position[0], v.position[1])

        elif abs_n[0] >= abs_n[1]:

            # X 主导 -> YZ 平面

            for v in self.vertices:

                v.uv = UVCoord(v.position[1], v.position[2])

        else:

            # Y 主导 -> XZ 平面

            for v in self.vertices:

                v.uv = UVCoord(v.position[0], v.position[2])



        # 平移 UV 到 [0, 1] 范围

        us = [v.uv.u for v in self.vertices]

        vs = [v.uv.v for v in self.vertices]

        u_min, u_max = min(us), max(us)

        v_min, v_max = min(vs), max(vs)



        if u_max > u_min:

            u_range = u_max - u_min

        else:

            u_range = 1.0

        if v_max > v_min:

            v_range = v_max - v_min

        else:

            v_range = 1.0



        for v in self.vertices:

            v.uv.u = (v.uv.u - u_min) / u_range

            v.uv.v = (v.uv.v - v_min) / v_range



        return self.vertices





if __name__ == "__main__":

    print("=== UV 映射测试 ===")



    # 创建球体顶点

    print("\n1. 球面映射测试")

    vertices = []

    radius = 1.0

    n_samples = 5



    for i in range(n_samples):

        phi = math.pi * i / (n_samples - 1)

        for j in range(n_samples * 2):

            theta = 2 * math.pi * j / (n_samples * 2 - 1)

            x = radius * math.sin(phi) * math.cos(theta)

            y = radius * math.cos(phi)

            z = radius * math.sin(phi) * math.sin(theta)

            v = Vertex(position=[x, y, z],

                      normal=[x, y, z],  # 球面法线 = 位置归一化

                      uv=None)

            v.normal = v.normal / np.linalg.norm(v.normal)

            vertices.append(v)



    # 生成 UV

    vertices = generate_uv_for_mesh(vertices, method='spherical')



    print(f"生成了 {len(vertices)} 个顶点")

    print("前 5 个顶点的 UV:")

    for i, v in enumerate(vertices[:5]):

        print(f"  V{i}: pos=({v.position[0]:.2f}, {v.position[1]:.2f}, {v.position[2]:.2f}) "

              f"-> UV={v.uv}")



    # 测试平面投影

    print("\n2. 平面投影测试")

    plane_v = Vertex(position=[2, 3, 5], normal=[0, 0, 1])

    for axis in ['x', 'y', 'z']:

        uv = planar_projection(plane_v, axis)

        print(f"  沿 {axis} 轴投影: UV={uv}")



    # 测试纹理采样

    print("\n3. 双线性采样测试")

    # 创建简单棋盘纹理

    checker_size = 8

    texture = np.zeros((checker_size * 4, checker_size * 4, 3))

    for y in range(texture.shape[0]):

        for x in range(texture.shape[1]):

            if ((x // checker_size) + (y // checker_size)) % 2 == 0:

                texture[y, x] = [1, 1, 1]

            else:

                texture[y, x] = [0, 0, 0]



    print(f"纹理尺寸: {texture.shape}")



    # 采样

    sample_points = [(0.1, 0.1), (0.5, 0.5), (0.9, 0.9), (0.25, 0.75)]

    for u, v in sample_points:

        color = bilinear_sample(texture, u, v)

        print(f"  UV=({u:.1f}, {v:.1f}) -> color={color}")



    # 测试 UV 展开

    print("\n4. UV 展开测试")

    box_vertices = [

        Vertex(position=[0, 0, 0], normal=[0, 0, -1]),

        Vertex(position=[1, 0, 0], normal=[0, 0, -1]),

        Vertex(position=[1, 1, 0], normal=[0, 0, -1]),

        Vertex(position=[0, 1, 0], normal=[0, 0, -1]),

    ]

    box_triangles = [

        Triangle(box_vertices[0], box_vertices[1], box_vertices[2]),

        Triangle(box_vertices[0], box_vertices[2], box_vertices[3]),

    ]



    unwrapper = SimpleUVUnwrap(box_vertices, box_triangles)

    unwrapper.unwrap()



    print("展开后的 UV:")

    for i, v in enumerate(box_vertices):

        print(f"  V{i}: UV={v.uv}")



    # 测试 UV Atlas

    print("\n5. UV Atlas 测试")

    atlas = UVAtlas(256, 256)



    # 添加纹理

    tex1 = np.random.rand(32, 32, 3)

    tex2 = np.random.rand(64, 64, 3)



    uv1_min, uv1_max = atlas.add_texture("tex1", tex1)

    uv2_min, uv2_max = atlas.add_texture("tex2", tex2)



    print(f"Texture 1 UV: {uv1_min} - {uv1_max}")

    print(f"Texture 2 UV: {uv2_min} - {uv2_max}")



    print("\nUV 映射测试完成!")


# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / rendering_pipeline



本文件实现 rendering_pipeline 相关的算法功能。

"""



import numpy as np

import math





class Matrix4:

    """4x4 矩阵（用于变换）"""



    @staticmethod

    def identity():

        """单位矩阵"""

        return np.eye(4, dtype=float)



    @staticmethod

    def translation(x, y, z):

        """平移矩阵"""

        m = np.eye(4, dtype=float)

        m[0, 3] = x

        m[1, 3] = y

        m[2, 3] = z

        return m



    @staticmethod

    def scaling(x, y, z):

        """缩放矩阵"""

        m = np.eye(4, dtype=float)

        m[0, 0] = x

        m[1, 1] = y

        m[2, 2] = z

        return m



    @staticmethod

    def rotation_x(angle):

        """绕 X 轴旋转（弧度）"""

        c, s = math.cos(angle), math.sin(angle)

        m = np.eye(4, dtype=float)

        m[1, 1] = c

        m[1, 2] = -s

        m[2, 1] = s

        m[2, 2] = c

        return m



    @staticmethod

    def rotation_y(angle):

        """绕 Y 轴旋转"""

        c, s = math.cos(angle), math.sin(angle)

        m = np.eye(4, dtype=float)

        m[0, 0] = c

        m[0, 2] = s

        m[2, 0] = -s

        m[2, 2] = c

        return m



    @staticmethod

    def rotation_z(angle):

        """绕 Z 轴旋转"""

        c, s = math.cos(angle), math.sin(angle)

        m = np.eye(4, dtype=float)

        m[0, 0] = c

        m[0, 1] = -s

        m[1, 0] = s

        m[1, 1] = c

        return m



    @staticmethod

    def perspective(fov_y, aspect, near, far):

        """

        透视投影矩阵



        参数:

            fov_y: 垂直视野（弧度）

            aspect: 宽高比

            near: 近裁剪面

            far: 远裁剪面

        """

        f = 1.0 / math.tan(fov_y / 2)

        m = np.zeros((4, 4), dtype=float)

        m[0, 0] = f / aspect

        m[1, 1] = f

        m[2, 2] = (far + near) / (near - far)

        m[2, 3] = 2 * far * near / (near - far)

        m[3, 2] = -1

        return m



    @staticmethod

    def look_at(eye, center, up):

        """

        视图矩阵（Look At）



        参数:

            eye: 相机位置

            center: 观察目标

            up: 上方向向量

        """

        f = center - eye

        f = f / np.linalg.norm(f)



        s = np.cross(f, up)

        s = s / np.linalg.norm(s)



        u = np.cross(s, f)



        m = np.eye(4, dtype=float)

        m[0, :3] = s

        m[1, :3] = u

        m[2, :3] = -f

        m[0, 3] = -np.dot(s, eye)

        m[1, 3] = -np.dot(u, eye)

        m[2, 3] = np.dot(f, eye)

        return m





class Vertex:

    """顶点"""



    def __init__(self, position, normal=None, uv=None, color=None):

        self.position = np.array(position, dtype=float)  # 3D 位置

        self.normal = np.array(normal, dtype=float) if normal else None

        self.uv = np.array(uv, dtype=float) if uv else None

        self.color = np.array(color, dtype=float) if color else None

        self.clip_position = None  # 裁剪空间位置





class Mesh:

    """网格"""



    def __init__(self, name=""):

        self.name = name

        self.vertices = []

        self.triangles = []  # 顶点索引

        self.model_matrix = Matrix4.identity()



    def add_vertex(self, position, normal=None, uv=None, color=None):

        """添加顶点"""

        v = Vertex(position, normal, uv, color)

        self.vertices.append(v)

        return len(self.vertices) - 1



    def add_triangle(self, i0, i1, i2):

        """添加三角形面"""

        self.triangles.append((i0, i1, i2))





class Camera:

    """相机"""



    def __init__(self, eye, target, up, fov=60, aspect=1.0, near=0.1, far=100):

        self.eye = np.array(eye, dtype=float)

        self.target = np.array(target, dtype=float)

        self.up = np.array(up, dtype=float) / np.linalg.norm(np.array(up, dtype=float))

        self.fov = math.radians(fov)

        self.aspect = aspect

        self.near = near

        self.far = far



        # 计算矩阵

        self.view_matrix = Matrix4.look_at(self.eye, self.target, self.up)

        self.projection_matrix = Matrix4.perspective(self.fov, self.aspect, self.near, self.far)

        self.view_projection = self.projection_matrix @ self.view_matrix





class RenderingPipeline:

    """

    渲染管线



    完整的 CPU 端渲染流程。

    """



    def __init__(self, width, height):

        """

        初始化渲染管线



        参数:

            width: 视口宽度

            height: 视口高度

        """

        self.width = width

        self.height = height

        self.framebuffer = np.zeros((height, width, 3), dtype=float)

        self.depthbuffer = np.ones((height, width), dtype=float) * 1e10



        # 光源

        self.lights = []



        # 相机

        self.camera = None



        # 渲染状态

        self.clear_color = np.array([0.1, 0.1, 0.1])

        self.wireframe = False



    def clear(self):

        """清空帧缓冲和深度缓冲"""

        self.framebuffer[:] = self.clear_color

        self.depthbuffer[:] = 1e10



    def set_camera(self, camera):

        """设置相机"""

        self.camera = camera



    def add_light(self, position, color, intensity=1.0):

        """添加点光源"""

        self.lights.append({

            'position': np.array(position, dtype=float),

            'color': np.array(color, dtype=float),

            'intensity': intensity

        })



    def vertex_shader(self, vertex, model_matrix):

        """

        顶点着色器



        参数:

            vertex: 输入顶点

            model_matrix: 模型变换矩阵

        返回:

            clip_position: 裁剪空间位置

        """

        # 世界空间位置

        world_pos = model_matrix @ np.append(vertex.position, 1)



        # 视图投影

        clip_pos = self.camera.view_projection @ world_pos

        vertex.clip_position = clip_pos



        return vertex



    def rasterize_triangle(self, v0, v1, v2):

        """

        光栅化三角形



        参数:

            v0, v1, v2: 裁剪空间的顶点

        """

        # 齐次除法得到 NDC

        def to_ndc(clip_pos):

            w = clip_pos[3]

            return (clip_pos[:3] / w, w)



        ndc0, w0 = to_ndc(v0.clip_position)

        ndc1, w1 = to_ndc(v1.clip_position)

        ndc2, w2 = to_ndc(v2.clip_position)



        # 视口变换

        def to_screen(ndc):

            x = (ndc[0] + 1) * 0.5 * self.width

            y = (1 - ndc[1]) * 0.5 * self.height  # Y 轴翻转

            z = ndc[2]

            return np.array([x, y, z])



        s0 = to_screen(ndc0)

        s1 = to_screen(ndc1)

        s2 = to_screen(ndc2)



        # 包围盒

        min_x = max(0, int(min(s0[0], s1[0], s2[0])))

        max_x = min(self.width - 1, int(max(s0[0], s1[0], s2[0])) + 1)

        min_y = max(0, int(min(s0[1], s1[1], s2[1])))

        max_y = min(self.height - 1, int(max(s0[1], s1[1], s2[1])) + 1)



        # 遍历包围盒像素

        for y in range(min_y, max_y + 1):

            for x in range(min_x, max_x + 1):

                p = np.array([x + 0.5, y + 0.5])

                bary = self._barycentric_coords(p, s0[:2], s1[:2], s2[:2])



                if bary is None:

                    continue



                u, v, w = bary



                # 深度测试（透视正确深度）

                z = u * ndc0[2] / w0 + v * ndc1[2] / w1 + w * ndc2[2] / w2

                z = 1.0 / (u / w0 + v / w1 + w / w2)



                if z < 0 or z > 1:

                    continue



                # 深度缓冲测试

                if z < self.depthbuffer[y, x]:

                    self.depthbuffer[y, x] = z



                    # 简单的漫反射着色

                    color = np.array([0.8, 0.8, 0.8]) * (0.5 + 0.5 * abs(u - v))



                    # 光源影响

                    world_pos = u * v0.position + v * v1.position + w * v2.position

                    normal = u * v0.normal + v * v1.normal + w * v2.normal if v0.normal is not None else np.array([0, 0, 1])



                    if np.linalg.norm(normal) > 0:

                        normal = normal / np.linalg.norm(normal)



                    for light in self.lights:

                        L = light['position'] - world_pos

                        dist = np.linalg.norm(L)

                        L = L / dist

                        NdotL = max(0, np.dot(normal, L))

                        attenuation = 1.0 / (1.0 + 0.1 * dist)

                        color += light['color'] * light['intensity'] * NdotL * attenuation



                    self.framebuffer[y, x] = np.clip(color, 0, 1)



    def _barycentric_coords(self, p, a, b, c):

        """

        计算点的重心坐标



        参数:

            p: 像素点

            a, b, c: 三角形顶点（2D）

        """

        v0 = b - a

        v1 = c - a

        v2 = p - a



        dot00 = np.dot(v0, v0)

        dot01 = np.dot(v0, v1)

        dot02 = np.dot(v0, v2)

        dot11 = np.dot(v1, v1)

        dot12 = np.dot(v1, v2)



        denom = dot00 * dot11 - dot01 * dot01

        if abs(denom) < 1e-10:

            return None



        inv_denom = 1.0 / denom

        u = (dot11 * dot02 - dot01 * dot12) * inv_denom

        v = (dot00 * dot12 - dot01 * dot02) * inv_denom



        if u < 0 or v < 0 or u + v > 1:

            return None



        return (u, v, 1 - u - v)



    def render_mesh(self, mesh):

        """

        渲染网格



        参数:

            mesh: 要渲染的网格

        """

        # 顶点着色

        transformed_vertices = []

        for v in mesh.vertices:

            transformed = self.vertex_shader(v, mesh.model_matrix)

            transformed_vertices.append(transformed)



        # 几何处理和光栅化

        for i0, i1, i2 in mesh.triangles:

            v0 = transformed_vertices[i0]

            v1 = transformed_vertices[i1]

            v2 = transformed_vertices[i2]

            self.rasterize_triangle(v0, v1, v2)



    def render(self, scene):

        """

        渲染整个场景



        参数:

            scene: Scene 对象

        """

        self.clear()



        for mesh in scene.meshes:

            self.render_mesh(mesh)





class Scene:

    """场景"""



    def __init__(self):

        self.meshes = []





def create_cube_mesh():

    """创建立方体网格"""

    mesh = Mesh("Cube")



    # 8 个顶点

    for x, y, z in [(-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),

                    (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)]:

        mesh.add_vertex([x, y, z], normal=[0, 0, 0])  # 法线待计算



    # 6 个面（每个面 2 个三角形）

    # 前面

    mesh.add_triangle(0, 1, 2)

    mesh.add_triangle(0, 2, 3)

    # 后面

    mesh.add_triangle(5, 4, 7)

    mesh.add_triangle(5, 7, 6)

    # 下面

    mesh.add_triangle(0, 4, 5)

    mesh.add_triangle(0, 5, 1)

    # 上面

    mesh.add_triangle(3, 2, 6)

    mesh.add_triangle(3, 6, 7)

    # 左面

    mesh.add_triangle(4, 0, 3)

    mesh.add_triangle(4, 3, 7)

    # 右面

    mesh.add_triangle(1, 5, 6)

    mesh.add_triangle(1, 6, 2)



    return mesh





def create_triangle_mesh():

    """创建简单三角形"""

    mesh = Mesh("Triangle")

    mesh.add_vertex([0, 1, 0], normal=[0, 0, 1], color=[1, 0, 0])

    mesh.add_vertex([-1, -1, 0], normal=[0, 0, 1], color=[0, 1, 0])

    mesh.add_vertex([1, -1, 0], normal=[0, 0, 1], color=[0, 0, 1])

    mesh.add_triangle(0, 1, 2)

    return mesh





if __name__ == "__main__":

    print("=== 渲染管线测试 ===")



    # 创建渲染管线

    width, height = 32, 32

    pipeline = RenderingPipeline(width, height)



    # 创建相机

    camera = Camera(

        eye=[0, 0, -5],

        target=[0, 0, 0],

        up=[0, 1, 0],

        fov=60,

        aspect=1.0,

        near=0.1,

        far=100

    )

    pipeline.set_camera(camera)



    # 添加光源

    pipeline.add_light([5, 5, -5], [1.0, 1.0, 1.0], intensity=1.0)



    # 创建场景

    scene = Scene()



    # 添加三角形

    tri = create_triangle_mesh()

    scene.meshes.append(tri)



    # 渲染

    print("\n1. 渲染三角形")

    pipeline.render(scene)

    print(f"   帧缓冲范围: [{np.min(pipeline.framebuffer):.3f}, {np.max(pipeline.framebuffer):.3f}]")



    # 添加立方体

    print("\n2. 渲染立方体")

    cube = create_cube_mesh()

    cube.model_matrix = Matrix4.translation(0, 0, 3)

    scene.meshes.append(cube)

    pipeline.render(scene)



    # 统计

    valid_pixels = np.sum(pipeline.framebuffer[:, :, 0] > 0.1)

    print(f"   有效像素数: {valid_pixels}")



    # 矩阵变换测试

    print("\n3. 矩阵变换测试")

    m = Matrix4.identity()

    print(f"   单位矩阵:\n{m}")



    m = Matrix4.translation(1, 2, 3)

    print(f"   平移矩阵 (1,2,3):\n{m}")



    m = Matrix4.rotation_y(math.pi / 4)

    print(f"   Y 轴旋转 (45度):\n{m.round(3)}")



    m = Matrix4.perspective(math.radians(60), 1.0, 0.1, 100)

    print(f"   透视投影:\n{m.round(3)}")



    # 视锥裁剪测试

    print("\n4. 视锥裁剪概念验证")

    print("   场景中有点在视锥外应该被裁剪")

    print(f"   近裁剪面 z > -0.1: 任何顶点 z > -near")

    print(f"   远裁剪面 z < -100: 任何顶点 z < -far")



    # 光栅化测试

    print("\n5. 光栅化统计")

    depth_range = [np.min(pipeline.depthbuffer), np.max(pipeline.depthbuffer)]

    print(f"   深度缓冲范围: {depth_range}")

    valid_depth = np.sum(pipeline.depthbuffer < 1e9)

    print(f"   写入深度的像素: {valid_depth}")



    # 顶点变换测试

    print("\n6. 顶点变换验证")

    v = Vertex(position=[0, 0, 5], normal=[0, 0, 1])

    mvp = camera.view_projection

    clip_pos = mvp @ np.append(v.position, 1)

    print(f"   顶点 (0, 0, 5) -> 裁剪空间 {clip_pos.round(2)}")

    ndc = clip_pos[:3] / clip_pos[3]

    print(f"   NDC: {ndc.round(3)}")



    print("\n渲染管线测试完成!")


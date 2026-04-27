# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / deferred_shading



本文件实现 deferred_shading 相关的算法功能。

"""



import numpy as np

import math





class GBuffer:

    """

    G-Buffer（几何缓冲区）



    存储屏幕空间的中间结果。

    """



    def __init__(self, width, height):

        """

        初始化 G-Buffer



        参数:

            width: 屏幕宽度

            height: 屏幕高度

        """

        self.width = width

        self.height = height



        # 分配 G-Buffer 纹理

        self.albedo = np.zeros((height, width, 3), dtype=np.float32)  # RGB

        self.normal = np.zeros((height, width, 3), dtype=np.float32)   # RGB (归一化)

        self.position = np.zeros((height, width, 3), dtype=np.float32)  # XYZ

        self.depth = np.zeros((height, width), dtype=np.float32)        # 深度



        # PBR 参数

        self.metallic = np.zeros((height, width), dtype=np.float32)

        self.roughness = np.zeros((height, width), dtype=np.float32)

        self.ao = np.ones((height, width), dtype=np.float32)  # 环境光遮蔽



        # 标记哪些像素有有效数据

        self.valid_mask = np.zeros((height, width), dtype=bool)



    def clear(self):

        """清空 G-Buffer"""

        self.albedo.fill(0)

        self.normal.fill(0)

        self.position.fill(0)

        self.depth.fill(0)

        self.metallic.fill(0)

        self.roughness.fill(0)

        self.ao.fill(1.0)

        self.valid_mask.fill(False)





class Light:

    """光照"""



    def __init__(self, light_type='directional'):

        self.light_type = light_type

        self.color = np.array([1.0, 1.0, 1.0])

        self.intensity = 1.0



        if light_type == 'directional':

            self.direction = np.array([0, -1, 0])  # 光照方向

            self.position = None

        elif light_type == 'point':

            self.position = np.array([0, 0, 0])

            self.direction = None

            self.constant = 1.0

            self.linear = 0.09

            self.quadratic = 0.032

        elif light_type == 'spot':

            self.position = np.array([0, 0, 0])

            self.direction = np.array([0, -1, 0])

            self.cutoff = math.cos(math.radians(12.5))

            self.outer_cutoff = math.cos(math.radians(17.5))





class Camera:

    """虚拟相机（用于屏幕空间计算）"""



    def __init__(self, position, fov=60, aspect=1.0):

        self.position = np.array(position, dtype=float)

        self.fov = fov

        self.aspect = aspect

        self.near = 0.1

        self.far = 100.0



    def world_to_view(self, world_pos):

        """世界坐标转视图坐标（简化版）"""

        # 简化为从相机位置的偏移

        return world_pos - self.position



    def view_to_screen(self, view_pos):

        """视图坐标转屏幕坐标（简化版）"""

        x, y, z = view_pos

        # 简化的透视投影

        scale = 1.0 / z if z > 0 else 1.0

        sx = x * scale / math.tan(math.radians(self.fov / 2)) + self.width / 2

        sy = y * scale / math.tan(math.radians(self.fov / 2)) * self.aspect + self.height / 2

        return int(sx), int(sy)





class DeferredRenderer:

    """

    延迟渲染器



    实现延迟着色的两个主要 Pass：

    1. Geometry Pass：填充 G-Buffer

    2. Lighting Pass：屏幕空间光照计算

    """



    def __init__(self, width, height):

        """

        初始化延迟渲染器



        参数:

            width: 屏幕宽度

            height: 屏幕高度

        """

        self.width = width

        self.height = height



        # 创建 G-Buffer

        self.gbuffer = GBuffer(width, height)



        # 光源列表

        self.lights = []



        # 环境光

        self.ambient = np.array([0.03, 0.03, 0.03])



    def add_light(self, light):

        """添加光源"""

        self.lights.append(light)



    def geometry_pass(self, scene_objects):

        """

        几何 Pass：填充 G-Buffer



        参数:

            scene_objects: 场景物体列表

        """

        self.gbuffer.clear()



        for obj in scene_objects:

            self._render_object_to_gbuffer(obj)



    def _render_object_to_gbuffer(self, obj):

        """

        将物体渲染到 G-Buffer



        参数:

            obj: 包含顶点、材质等信息的物体

        """

        # 简化实现：假设每个物体是屏幕空间覆盖的简单几何体

        # 实际应用中需要光栅化



        h, w = self.height, self.width



        # 简化：创建测试数据

        y_min = int(h * 0.2)

        y_max = int(h * 0.8)

        x_min = int(w * 0.2)

        x_max = int(w * 0.8)



        # 填充 G-Buffer

        for y in range(y_min, y_max):

            for x in range(x_min, x_max):

                if not self.gbuffer.valid_mask[y, x]:

                    # 设置基础数据

                    self.gbuffer.albedo[y, x] = obj.get('albedo', [0.8, 0.8, 0.8])

                    self.gbuffer.normal[y, x] = obj.get('normal', [0, 0, 1])

                    self.gbuffer.position[y, x] = obj.get('position', [x, y, 5])

                    self.gbuffer.depth[y, x] = 5.0

                    self.gbuffer.metallic[y, x] = obj.get('metallic', 0.0)

                    self.gbuffer.roughness[y, x] = obj.get('roughness', 0.5)

                    self.gbuffer.valid_mask[y, x] = True



    def lighting_pass(self, camera):

        """

        光照 Pass：计算光照



        参数:

            camera: 相机

        返回:

            output: 最终图像

        """

        output = np.zeros((self.height, self.width, 3), dtype=np.float32)



        for y in range(self.height):

            for x in range(self.width):

                if not self.gbuffer.valid_mask[y, x]:

                    output[y, x] = self.ambient

                    continue



                # 获取 G-Buffer 数据

                albedo = self.gbuffer.albedo[y, x]

                normal = self.gbuffer.normal[y, x]

                world_pos = self.gbuffer.position[y, x]

                metallic = self.gbuffer.metallic[y, x]

                roughness = self.gbuffer.roughness[y, x]

                ao = self.gbuffer.ao[y, x]



                # 计算光照

                color = np.zeros(3)



                for light in self.lights:

                    color += self._calculate_lighting(

                        light, world_pos, normal, albedo,

                        metallic, roughness, camera.position

                    )



                # 应用环境光遮蔽

                color += self.ambient * albedo * ao



                # Tone mapping（简单）

                color = color / (color + 1.0)



                output[y, x] = color



        return output



    def _calculate_lighting(self, light, position, normal, albedo,

                            metallic, roughness, view_pos):

        """

        计算单个光源的贡献（PBR）



        参数:

            light: 光源

            position: 片段位置

            normal: 法线

            albedo: 漫反射颜色

            metallic: 金属度

            roughness: 粗糙度

            view_pos: 观察位置

        返回:

            color: 光照贡献

        """

        # 光照方向

        if light.light_type == 'directional':

            L = -light.direction

        else:

            L = light.position - position

            dist = np.linalg.norm(L)

            L = L / dist



        # 视角方向

        V = view_pos - position

        V = V / np.linalg.norm(V)



        # 法线

        N = normal / np.linalg.norm(normal)



        # 半程向量

        H = V + L

        H = H / np.linalg.norm(H)



        # 基础参数

        NdotV = max(np.dot(N, V), 0.001)

        NdotL = max(np.dot(N, L), 0.0)

        NdotH = max(np.dot(N, H), 0.0)

        HdotV = max(np.dot(H, V), 0.0)



        # F0（基础反射率）

        F0 = 0.04 * np.ones(3)  # 非金属

        F0 = np.lerp(F0, albedo, metallic)



        # Fresnel-Schlick

        F = F0 + (1 - F0) * pow(1 - HdotV, 5)



        # GGX 分布

        alpha = roughness * roughness

        alpha_sq = alpha * alpha

        denom = NdotH * NdotH * (alpha_sq - 1) + 1

        D = alpha_sq / (math.pi * denom * denom)



        # 几何遮蔽

        k = (roughness + 1) ** 2 / 8

        G_V = NdotV / (NdotV * (1 - k) + k)

        G_L = NdotL / (NdotL * (1 - k) + k)

        G = G_V * G_L



        # Cook-Torrance BRDF

        specular = D * F * G / (4 * NdotV * NdotL + 0.001)



        # Lambertian 漫反射

        kD = (1 - F) * (1 - metallic)

        diffuse = kD * albedo / math.pi



        # 光源衰减

        radiance = light.color * light.intensity



        if light.light_type == 'point':

            dist = np.linalg.norm(light.position - position)

            attenuation = 1.0 / (light.constant + light.linear * dist + light.quadratic * dist ** 2)

            radiance *= attenuation

        elif light.light_type == 'spot':

            theta = np.dot(-L, light.direction)

            if theta < light.outer_cutoff:

                return np.zeros(3)

            epsilon = light.cutoff - light.outer_cutoff

            intensity = np.clip((theta - light.outer_cutoff) / epsilon, 0, 1)

            radiance *= intensity



        # 最终光照

        Lo = (diffuse + specular) * radiance * NdotL



        return Lo





def np_lerp(a, b, t):

    """NumPy 线性插值"""

    return a * (1 - t) + b * t





class ForwardRenderer:

    """

    前向渲染器（对比用）



    前向渲染在每个物体上计算所有光源的贡献。

    """



    def __init__(self, width, height):

        self.width = width

        self.height = height

        self.lights = []

        self.ambient = np.array([0.03, 0.03, 0.03])



    def add_light(self, light):

        self.lights.append(light)



    def render(self, scene_objects, camera):

        """

        渲染场景



        参数:

            scene_objects: 物体列表

            camera: 相机

        返回:

            output: 图像

        """

        output = np.zeros((self.height, self.width, 3), dtype=np.float32)



        for obj in scene_objects:

            color = self._shade_object(obj, camera)

            # 简单混合（实际需要深度测试）

            output += color * 0.1



        return np.clip(output, 0, 1)





if __name__ == "__main__":

    print("=== 延迟着色测试 ===")



    # 创建延迟渲染器

    width, height = 64, 64

    deferred = DeferredRenderer(width, height)

    forward = ForwardRenderer(width, height)



    # 添加光源

    dir_light = Light('directional')

    dir_light.direction = np.array([-0.5, -1.0, -0.5])

    dir_light.color = np.array([1.0, 0.95, 0.9])

    dir_light.intensity = 3.0

    deferred.add_light(dir_light)

    forward.add_light(dir_light)



    point_light = Light('point')

    point_light.position = np.array([32, 32, 10])

    point_light.color = np.array([0.5, 0.8, 1.0])

    point_light.intensity = 20.0

    deferred.add_light(point_light)

    forward.add_light(point_light)



    # 创建场景物体

    scene_objects = [

        {

            'albedo': [0.8, 0.2, 0.2],

            'normal': [0, 0, 1],

            'position': [32, 32, 5],

            'metallic': 0.0,

            'roughness': 0.5

        },

        {

            'albedo': [0.2, 0.8, 0.2],

            'normal': [0, 0, 1],

            'position': [32, 32, 5],

            'metallic': 0.8,

            'roughness': 0.2

        },

        {

            'albedo': [0.8, 0.8, 0.8],

            'normal': [0, 0, 1],

            'position': [32, 32, 5],

            'metallic': 0.0,

            'roughness': 0.8

        }

    ]



    # 创建相机

    camera = Camera(position=[32, 32, -10], fov=60, aspect=1.0)



    # 几何 Pass

    print("\n1. 几何 Pass（填充 G-Buffer）")

    deferred.geometry_pass(scene_objects)

    print(f"   G-Buffer 有效像素: {np.sum(deferred.gbuffer.valid_mask)}")

    print(f"   Albedo 范围: [{np.min(deferred.gbuffer.albedo)}, {np.max(deferred.gbuffer.albedo)}]")



    # 光照 Pass

    print("\n2. 光照 Pass")

    result = deferred.lighting_pass(camera)

    print(f"   输出范围: [{np.min(result)}, {np.max(result)}]")



    # 前向渲染对比

    print("\n3. 前向渲染对比")

    forward_result = forward.render(scene_objects, camera)

    print(f"   前向渲染输出范围: [{np.min(forward_result)}, {np.max(forward_result)}]")



    # G-Buffer 内容检查

    print("\n4. G-Buffer 内容检查")

    gb = deferred.gbuffer

    valid_y, valid_x = np.where(gb.valid_mask)

    if len(valid_x) > 0:

        idx = valid_x[0], valid_y[0]

        print(f"   第一个有效像素 ({idx[0]}, {idx[1]}):")

        print(f"     Albedo: {gb.albedo[idx[1], idx[0]]}")

        print(f"     Normal: {gb.normal[idx[1], idx[0]]}")

        print(f"     Position: {gb.position[idx[1], idx[0]]}")

        print(f"     Metallic: {gb.metallic[idx[1], idx[0]]:.2f}")

        print(f"     Roughness: {gb.roughness[idx[1], idx[0]]:.2f}")



    # 性能对比

    print("\n5. 光源数量对性能的影响")

    import time



    for n_lights in [1, 5, 10]:

        lights = []

        for i in range(n_lights):

            l = Light('point')

            l.position = np.array([np.random.uniform(0, width),

                                   np.random.uniform(0, height),

                                   np.random.uniform(5, 20)])

            l.intensity = 5.0

            lights.append(l)



        deferred_test = DeferredRenderer(width, height)

        for l in lights:

            deferred_test.add_light(l)



        deferred_test.geometry_pass(scene_objects)



        start = time.time()

        for _ in range(10):

            deferred_test.lighting_pass(camera)

        deferred_time = time.time() - start



        start = time.time()

        for _ in range(10):

            forward_test = ForwardRenderer(width, height)

            for l in lights:

                forward_test.add_light(l)

            forward_test.render(scene_objects, camera)

        forward_time = time.time() - start



        print(f"   {n_lights} 光源:")

        print(f"     延迟渲染: {deferred_time*100:.2f}ms")

        print(f"     前向渲染: {forward_time*100:.2f}ms")

        print(f"     加速比: {forward_time/deferred_time:.1f}x")



    print("\n延迟着色测试完成!")


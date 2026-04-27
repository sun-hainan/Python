# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / pbr_rendering



本文件实现 pbr_rendering 相关的算法功能。

"""



import numpy as np

import math





class PBRMaterial:

    """PBR 材质"""



    def __init__(self, albedo=(0.8, 0.8, 0.8), metallic=0.0,

                 roughness=0.5, ao=1.0, emissive=(0, 0, 0)):

        """

        初始化 PBR 材质



        参数:

            albedo: 基础颜色 (RGB)

            metallic: 金属度 [0, 1]

            roughness: 粗糙度 [0, 1]

            ao: 环境光遮蔽 [0, 1]

            emissive: 自发光颜色

        """

        self.albedo = np.array(albedo, dtype=float)

        self.metallic = metallic

        self.roughness = roughness

        self.ao = ao

        self.emissive = np.array(emissive, dtype=float)





class PBRLight:

    """PBR 光源"""



    def __init__(self, light_type='directional'):

        self.light_type = light_type



        if light_type == 'directional':

            self.direction = np.array([0, -1, 0])

        elif light_type == 'point':

            self.position = np.array([0, 0, 0])

            self.constant = 1.0

            self.linear = 0.09

            self.quadratic = 0.032

        elif light_type == 'spot':

            self.position = np.array([0, 0, 0])

            self.direction = np.array([0, -1, 0])

            self.cutoff = math.cos(math.radians(12.5))

            self.outer_cutoff = math.cos(math.radians(17.5))



        self.color = np.array([1.0, 1.0, 1.0])

        self.intensity = 1.0



    def get_radiance(self, world_pos=None):

        """

        获取光源辐射强度



        参数:

            world_pos: 世界位置（用于点光源衰减计算）

        返回:

            radiance: 辐射强度 (RGB)

        """

        radiance = self.color * self.intensity



        if self.light_type == 'point' and world_pos is not None:

            dist = np.linalg.norm(self.position - world_pos)

            attenuation = 1.0 / (self.constant + self.linear * dist +

                                 self.quadratic * dist * dist)

            radiance = radiance * attenuation



        elif self.light_type == 'spot' and world_pos is not None:

            L = world_pos - self.position

            L = L / np.linalg.norm(L)

            theta = np.dot(L, self.direction)

            if theta < self.outer_cutoff:

                return np.zeros(3)

            epsilon = self.cutoff - self.outer_cutoff

            intensity = np.clip((theta - self.outer_cutoff) / epsilon, 0, 1)

            radiance = radiance * intensity



        return radiance





class PBRRenderer:

    """PBR 渲染器"""



    def __init__(self):

        self.lights = []

        self.ambient = np.array([0.03, 0.03, 0.03])



    def add_light(self, light):

        """添加光源"""

        self.lights.append(light)



    def fresnel_schlick(self, cos_theta, F0):

        """

        Fresnel-Schlick 近似



        F(v, h) = F0 + (1 - F0) * (1 - (v·h))^5



        参数:

            cos_theta: V · H

            F0: 基础反射率

        返回:

            F: Fresnel 系数

        """

        return F0 + (1 - F0) * pow(1 - cos_theta, 5)



    def distribution_ggx(self, N, H, roughness):

        """

        GGX 法线分布函数（NDF）



        D(h) = α² / (π((n·h)²(α² - 1) + 1)²)



        参数:

            N: 法线

            H: 半程向量

            roughness: 粗糙度

        返回:

            D: 分布值

        """

        alpha = roughness * roughness

        alpha_sq = alpha * alpha

        NdotH_sq = np.dot(N, H) ** 2



        denom = NdotH_sq * (alpha_sq - 1) + 1

        denom = math.pi * denom * denom



        return alpha_sq / denom



    def geometry_schlick_ggx(self, NdotV, roughness):

        """

        Schlick-GGX 几何遮蔽函数



        G(v) = (n·v) / ((n·v)(1 - k) + k)

        k = α/2 for direct lighting



        参数:

            NdotV: N · V

            roughness: 粗糙度

        返回:

            G: 几何遮蔽值

        """

        k = (roughness + 1) ** 2 / 8

        return NdotV / (NdotV * (1 - k) + k)



    def geometry_smith(self, N, V, L, roughness):

        """

        Smith 几何遮蔽函数



        G(n, v, l) = G1(v) * G1(l)



        参数:

            N: 法线

            V: 视角方向

            L: 光照方向

            roughness: 粗糙度

        返回:

            G: Smith 几何遮蔽

        """

        NdotV = max(np.dot(N, V), 0.001)

        NdotL = max(np.dot(N, L), 0.0)



        ggx_v = self.geometry_schlick_ggx(NdotV, roughness)

        ggx_l = self.geometry_schlick_ggx(NdotL, roughness)



        return ggx_v * ggx_l



    def cook_torrance(self, N, V, L, material):

        """

        Cook-Torrance BRDF



        参数:

            N: 法线

            V: 视角方向

            L: 光照方向

            material: PBR 材质

        返回:

            spec: 高光反射

        """

        H = V + L

        H = H / np.linalg.norm(H)



        NdotV = max(np.dot(N, V), 0.001)

        NdotL = max(np.dot(N, L), 0.001)

        NdotH = max(np.dot(N, H), 0.0)

        HdotV = max(np.dot(H, V), 0.0)



        # F0

        F0 = np.lerp(np.array([0.04, 0.04, 0.04]), material.albedo, material.metallic)



        # Fresnel

        F = self.fresnel_schlick(HdotV, F0)



        # NDF

        D = self.distribution_ggx(N, H, material.roughness)



        # Geometry

        G = self.geometry_smith(N, V, L, material.roughness)



        # Cook-Torrance

        denominator = 4 * NdotV * NdotL + 0.001

        specular = (D * F * G) / denominator



        return specular, F



    def render(self, position, normal, material, view_pos):

        """

        PBR 渲染



        参数:

            position: 片段世界位置

            normal: 片段法线

            material: PBR 材质

            view_pos: 相机位置

        返回:

            color: 最终颜色

        """

        N = normal / np.linalg.norm(normal)

        V = view_pos - position

        V = V / np.linalg.norm(V)



        # 自发光

        Lo = material.emissive



        # 环境光

        kD = (1 - material.metallic) * (1 - material.roughness)

        Lo += self.ambient * kD * material.albedo * material.ao



        # 每个光源的贡献

        for light in self.lights:

            # 光照方向

            if light.light_type == 'directional':

                L = -light.direction

            else:

                L = light.position - position

            L = L / np.linalg.norm(L)



            # 辐射强度

            radiance = light.get_radiance(position)



            # Cook-Torrance

            specular, F = self.cook_torrance(N, V, L, material)



            # 漫反射

            kD = (1 - F) * (1 - material.metallic)

            diffuse = kD * material.albedo / math.pi



            # Lambertian

            NdotL = max(np.dot(N, L), 0.0)



            # 最终贡献

            Lo += (diffuse + specular) * radiance * NdotL



        # HDR Tone mapping

        Lo = Lo / (Lo + 1.0)



        # Gamma correction

        gamma = 1.0 / 2.2

        color = np.power(np.clip(Lo, 0, 1), np.array([gamma, gamma, gamma]))



        return color





class EnvironmentMap:

    """环境贴图"""



    def __init__(self, width=256, height=128):

        self.width = width

        self.height = height

        # 简化：预计算天空颜色

        self.data = self._generate_skybox()



    def _generate_skybox(self):

        """生成简单天空盒"""

        sky = np.zeros((self.height, self.width, 3))



        for y in range(self.height):

            # 垂直方向：0=地平线，1=天顶

            t = y / self.height

            # 天蓝色到白色渐变

            sky[y, :] = [

                0.3 + 0.5 * (1 - t),

                0.5 + 0.4 * (1 - t),

                0.7 + 0.3 * (1 - t)

            ]

            # 地平线处加亮

            if 0.3 < t < 0.4:

                sky[y, :] = [1.0, 0.9, 0.7]



        return sky



    def sample(self, direction):

        """

        采样环境贴图



        参数:

            direction: 方向向量

        返回:

            color: 环境颜色

        """

        d = direction / np.linalg.norm(direction)



        # 转换到球面坐标

        theta = math.atan2(d[2], d[0])  # [-π, π]

        phi = math.acos(np.clip(d[1], -1, 1))  # [0, π]



        # 转换到像素坐标

        u = (theta + math.pi) / (2 * math.pi)

        v = phi / math.pi



        x = int(u * (self.width - 1))

        y = int(v * (self.height - 1))

        x = max(0, min(x, self.width - 1))

        y = max(0, min(y, self.height - 1))



        return self.data[y, x]



    def sample_ibl(self, N, roughness, albedo):

        """

        基于图像的光照（IBL）采样



        参数:

            N: 法线

            roughness: 粗糙度

            albedo: 漫反射颜色

        返回:

            irradiance: 环境光辐射

        """

        # 简化：使用天空采样

        sky_color = self.sample(N)



        # 简单环境遮蔽

        ao = 1.0 - roughness * 0.5



        # 漫反射环境光

        irradiance = albedo * sky_color * ao * (1 - roughness)



        return irradiance





def cook_torrance_visualize():

    """可视化 Cook-Torrance BRDF 的各个分量"""

    print("=== Cook-Torrance BRDF 可视化 ===")



    # 参数

    N = np.array([0, 0, 1])

    V = np.array([0, 0, 1])

    L = np.array([0.5, 0.5, 0.707])

    L = L / np.linalg.norm(L)

    roughness = 0.4

    metallic = 0.0

    albedo = np.array([0.8, 0.2, 0.2])



    # F0

    F0 = np.lerp(np.array([0.04, 0.04, 0.04]), albedo, metallic)



    renderer = PBRRenderer()



    H = V + L

    H = H / np.linalg.norm(H)



    # 计算各分量

    D = renderer.distribution_ggx(N, H, roughness)

    F = renderer.fresnel_schlick(np.dot(V, H), F0)

    G = renderer.geometry_smith(N, V, L, roughness)



    print(f"\n输入: N={N}, V={V}, L={L}")

    print(f"材质: roughness={roughness}, metallic={metallic}, albedo={albedo}")

    print(f"\nBRDF 分量:")

    print(f"  D (GGX NDF): {D:.4f}")

    print(f"  F (Fresnel): {F}")

    print(f"  G (Smith): {G:.4f}")





if __name__ == "__main__":

    print("=== PBR 渲染测试 ===")



    # 创建 PBR 渲染器

    renderer = PBRRenderer()



    # 添加光源

    sun = PBRLight('directional')

    sun.direction = np.array([-0.5, -1.0, -0.5])

    sun.color = np.array([1.0, 0.98, 0.95])  # 阳光色温

    sun.intensity = 3.0

    renderer.add_light(sun)



    point = PBRLight('point')

    point.position = np.array([2, 2, 2])

    point.color = np.array([0.5, 0.7, 1.0])  # 冷光

    point.intensity = 10.0

    renderer.add_light(point)



    # 创建材质

    print("\n1. 不同材质测试")

    materials = [

        ("塑料红", PBRMaterial(albedo=(0.8, 0.1, 0.1), metallic=0.0, roughness=0.3)),

        ("金金属", PBRMaterial(albedo=(1.0, 0.8, 0.3), metallic=1.0, roughness=0.2)),

        ("铜金属", PBRMaterial(albedo=(0.8, 0.4, 0.2), metallic=1.0, roughness=0.3)),

        ("粗糙白", PBRMaterial(albedo=(0.9, 0.9, 0.9), metallic=0.0, roughness=0.8)),

        ("镜面", PBRMaterial(albedo=(0.9, 0.9, 0.9), metallic=0.0, roughness=0.05)),

    ]



    position = np.array([0, 0, 0])

    normal = np.array([0, 0, 1])

    view_pos = np.array([0, 0, -2])



    for name, mat in materials:

        color = renderer.render(position, normal, mat, view_pos)

        print(f"  {name}: RGB=({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})")



    # Cook-Torrance 可视化

    print("\n2. Cook-Torrance BRDF 分析")

    cook_torrance_visualize()



    # 粗糙度对高光的影响

    print("\n3. 粗糙度对高光的影响")

    for roughness in [0.1, 0.3, 0.5, 0.7, 0.9]:

        mat = PBRMaterial(albedo=(0.8, 0.8, 0.8), metallic=0.9, roughness=roughness)

        color = renderer.render(position, normal, mat, view_pos)

        print(f"  roughness={roughness:.1f}: RGB=({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})")



    # 金属度对反射的影响

    print("\n4. 金属度对颜色的影响")

    for metallic in [0.0, 0.2, 0.5, 0.8, 1.0]:

        mat = PBRMaterial(albedo=(0.8, 0.2, 0.2), metallic=metallic, roughness=0.3)

        color = renderer.render(position, normal, mat, view_pos)

        print(f"  metallic={metallic:.1f}: RGB=({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})")



    # 环境贴图测试

    print("\n5. 环境贴图采样")

    env = EnvironmentMap()



    directions = [

        ("上", [0, 1, 0]),

        ("下", [0, -1, 0]),

        ("前", [0, 0, 1]),

        ("右", [1, 0, 0]),

    ]



    for name, d in directions:

        color = env.sample(np.array(d))

        print(f"  {name}: RGB=({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})")



    # IBL 测试

    print("\n6. IBL 环境光照")

    mat = PBRMaterial(albedo=(0.8, 0.8, 0.8), metallic=0.0, roughness=0.5)

    irradiance = env.sample_ibl(np.array([0, 0, 1]), 0.5, mat.albedo)

    print(f"  平面法线方向 irradiance: {irradiance}")



    print("\nPBR 渲染测试完成!")


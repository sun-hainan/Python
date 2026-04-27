# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / radiosity



本文件实现 radiosity 相关的算法功能。

"""



import numpy as np

import math





class Patch:

    """

    辐射度 Patch（面片）



    场景被离散化为若干 Patch，每个 Patch 有均匀的属性。

    """



    def __init__(self, vertices, color=None, emission=None, reflectivity=0.5):

        """

        初始化 Patch



        参数:

            vertices: 四个角点 [(x,y,z), ...]

            color: RGB 颜色

            emission: 自发光强度

            reflectivity: 漫反射率

        """

        self.vertices = [np.array(v, dtype=float) for v in vertices]

        self.area = self._compute_area()

        self.center = self._compute_center()

        self.normal = self._compute_normal()



        self.color = np.array(color, dtype=float) if color else np.array([0.8, 0.8, 0.8])

        self.emission = np.array(emission, dtype=float) if emission else np.zeros(3)

        self.reflectivity = reflectivity



        self.radiosity = self.emission.copy()  # 初始辐射度 = 自发光

        self.form_factors = {}  # 到其他 patch 的形状因子



    def _compute_area(self):

        """计算面积（分解为两个三角形）"""

        v0, v1, v2, v3 = self.vertices

        # 三角形1: v0, v1, v2

        e1 = v1 - v0

        e2 = v2 - v0

        area1 = 0.5 * np.linalg.norm(np.cross(e1, e2))

        # 三角形2: v0, v2, v3

        e2 = v2 - v0

        e3 = v3 - v0

        area2 = 0.5 * np.linalg.norm(np.cross(e2, e3))

        return area1 + area2



    def _compute_center(self):

        """计算中心点"""

        return np.mean(self.vertices, axis=0)



    def _compute_normal(self):

        """计算法线"""

        v0, v1, v2, _ = self.vertices

        e1 = v1 - v0

        e2 = v2 - v0

        n = np.cross(e1, e2)

        norm = np.linalg.norm(n)

        return n / norm if norm > 0 else n





class RadiosityRenderer:

    """

    辐射度渲染器



    实现逐步迭代求解辐射度：

    1. 计算所有 Patch 对之间的形状因子

    2. 迭代更新辐射度直到收敛

    """



    def __init__(self, patches, tolerance=0.01, max_iterations=100):

        """

        初始化辐射度渲染器



        参数:

            patches: Patch 列表

            tolerance: 收敛阈值

            max_iterations: 最大迭代次数

        """

        self.patches = patches

        self.n_patches = len(patches)

        self.tolerance = tolerance

        self.max_iterations = max_iterations



    def compute_form_factor(self, patch_i, patch_j):

        """

        计算两个 Patch 之间的形状因子



        使用数值积分（N 采样点）近似：

        F_ij = (1/A_i) * ∫∫ cosθ_i * cosθ_j / (π * d²) dA_j



        简化版本（使用中心点）：

        F_ij = (cosθ_i * cosθ_j * A_j) / (π * d²)

        """

        # 中心到中心向量

        d_vec = patch_j.center - patch_i.center

        d = np.linalg.norm(d_vec)



        if d < 1e-8:

            return 0.0



        d_hat = d_vec / d



        # 方向角

        cos_i = max(0, np.dot(patch_i.normal, d_hat))

        cos_j = max(0, np.dot(patch_j.normal, -d_hat))



        # 形状因子（简化公式）

        form_factor = (cos_i * cos_j * patch_j.area) / (math.pi * d * d)



        # 可见性检查（简化：忽略遮挡）

        # 实际应用中需要光线追踪检查



        return max(0, min(1, form_factor))



    def compute_all_form_factors(self):

        """计算所有 Patch 对之间的形状因子"""

        print(f"计算 {self.n_patches} 个 Patch 的形状因子...")



        for i, patch_i in enumerate(self.patches):

            for j, patch_j in enumerate(self.patches):

                if i != j:

                    ff = self.compute_form_factor(patch_i, patch_j)

                    patch_i.form_factors[j] = ff



            if (i + 1) % 10 == 0:

                print(f"  已处理 {i+1}/{self.n_patches}")



    def radiosity_iteration(self):

        """

        单次辐射度迭代



        B_i^{new} = E_i + ρ_i * Σ F_ij * B_j



        返回:

            delta: 最大变化量

        """

        delta = 0.0

        new_radiosity = []



        for i, patch_i in enumerate(self.patches):

            # 计算入射辐射度

            incident = np.zeros(3)



            for j, patch_j in enumerate(self.patches):

                if i != j and j in patch_i.form_factors:

                    ff = patch_i.form_factors[j]

                    incident += patch_j.radiosity * ff * patch_j.color



            # 加上自发光

            incident_radiosity = self.emission + patch_i.reflectivity * incident



            new_radiosity.append(incident_radiosity)



            # 记录最大变化

            delta = max(delta, np.max(np.abs(incident_radiosity - patch_i.radiosity)))



        # 更新辐射度

        for i, patch in enumerate(self.patches):

            patch.radiosity = new_radiosity[i]



        return delta



    def solve(self):

        """

        求解辐射度（迭代）



        返回:

            final_radiosity: 最终辐射度值列表

        """

        print("开始辐射度求解...")



        # 首先计算形状因子

        self.compute_all_form_factors()



        # 迭代求解

        for iteration in range(self.max_iterations):

            delta = self.radiosity_iteration()

            print(f"迭代 {iteration+1}: 最大变化 = {delta:.6f}")



            if delta < self.tolerance:

                print(f"收敛！经过 {iteration+1} 次迭代")

                break



        return [p.radiosity for p in self.patches]



    def get_color(self, patch):

        """

        获取 Patch 的最终颜色



        参数:

            patch: Patch 对象

        返回:

            color: RGB 颜色（归一化）

        """

        return np.clip(patch.radiosity, 0, 1)





class HemCubeFormFactor:

    """

    HemCube 方法计算形状因子



    HemCube 是一个以 Patch 中心为原点的单位立方体，

    通过对立方体六个面的像素进行采样来数值计算形状因子。



    这里提供简化版本。

    """



    def __init__(self, n_samples=8):

        """

        初始化 HemCube



        参数:

            n_samples: 每边采样点数

        """

        self.n_samples = n_samples

        self.delta = 2.0 / n_samples



        # 预计算采样方向

        self.hemisphere_dirs = self._generate_directions()



    def _generate_directions(self):

        """生成半球采样方向"""

        dirs = []

        for i in range(self.n_samples):

            for j in range(self.n_samples):

                u = -1.0 + self.delta * (i + 0.5)

                v = -1.0 + self.delta * (j + 0.5)

                d = np.array([u, v, math.sqrt(1 - u*u - v*v)])

                dirs.append(d / np.linalg.norm(d))

        return dirs



    def compute_form_factor(self, patch_i, patch_j):

        """

        使用 HemCube 近似计算形状因子



        参数:

            patch_i: 目标 Patch

            patch_j: 源 Patch

        返回:

            form_factor: 形状因子

        """

        # 计算从 i 看到 j 的贡献

        to_j = patch_j.center - patch_i.center

        d = np.linalg.norm(to_j)

        if d < 1e-8:

            return 0.0



        to_j_normalized = to_j / d



        # 检查 j 是否在 i 的法线方向半球内

        if np.dot(patch_i.normal, to_j_normalized) < 0:

            return 0.0



        # HemCube 方法

        solid_angle = 0.0

        for direction in self.hemisphere_dirs:

            # 检查该方向是否击中 patch j

            if self._ray_hits_patch(patch_i.center, direction, patch_j):

                solid_angle += 1.0 / (len(self.hemisphere_dirs))



        # 形状因子

        form_factor = solid_angle * np.dot(patch_i.normal, to_j_normalized) / math.pi



        return max(0, form_factor)



    def _ray_hits_patch(self, origin, direction, patch):

        """检查光线是否击中 Patch（简化）"""

        # 简化的击中测试

        d = patch.center - origin

        t = np.dot(d, patch.normal) / np.dot(direction, patch.normal)

        if t < 0:

            return False

        hit_point = origin + t * direction

        # 检查是否在 Patch 范围内（简化）

        to_center = patch.center - hit_point

        return np.linalg.norm(to_center) < patch.area ** 0.5





if __name__ == "__main__":

    print("=== 辐射度算法测试 ===")



    # 创建简单场景：地板 + 墙壁 + 天花板

    patches = []



    # 地板（y = 0）

    floor = Patch(

        [[-5, 0, -5], [5, 0, -5], [5, 0, 5], [-5, 0, 5]],

        color=[0.8, 0.8, 0.8],

        reflectivity=0.5

    )

    patches.append(floor)



    # 天花板（y = 3）

    ceiling = Patch(

        [[-5, 3, -5], [5, 3, -5], [5, 3, 5], [-5, 3, 5]],

        color=[0.9, 0.9, 0.9],

        reflectivity=0.5

    )

    patches.append(ceiling)



    # 左墙（x = -5）

    left_wall = Patch(

        [[-5, 0, -5], [-5, 3, -5], [-5, 3, 5], [-5, 0, 5]],

        color=[0.7, 0.3, 0.3],  # 红色

        reflectivity=0.5

    )

    patches.append(left_wall)



    # 右墙（x = 5）

    right_wall = Patch(

        [[5, 0, -5], [5, 3, -5], [5, 3, 5], [5, 0, 5]],

        color=[0.3, 0.3, 0.7],  # 蓝色

        reflectivity=0.5

    )

    patches.append(right_wall)



    # 后墙（z = -5）

    back_wall = Patch(

        [[-5, 0, -5], [5, 0, -5], [5, 3, -5], [-5, 3, -5]],

        color=[0.7, 0.7, 0.7],

        reflectivity=0.5

    )

    patches.append(back_wall)



    # 发光矩形（在左墙上）

    light = Patch(

        [[-4.9, 1, -2], [-4.9, 1, 2], [-4.9, 2, 2], [-4.9, 2, -2]],

        color=[1.0, 1.0, 1.0],

        emission=[1.0, 0.9, 0.8],  # 暖白色发光

        reflectivity=0.3

    )

    patches.append(light)



    print(f"创建了 {len(patches)} 个 Patch")



    # 创建渲染器

    renderer = RadiosityRenderer(patches, tolerance=0.01, max_iterations=20)



    # 求解

    radiosity = renderer.solve()



    # 输出结果

    print("\n=== 辐射度结果 ===")

    patch_names = ['地板', '天花板', '左墙', '右墙', '后墙', '光源']

    for i, (name, rad) in enumerate(zip(patch_names, radiosity)):

        print(f"{name}: B = {rad.round(4)}")

        print(f"  颜色: {patches[i].color}")

        print(f"  辐射度: {rad}")



    # 测试 HemCube

    print("\n=== HemCube 形状因子测试 ===")

    hemcube = HemCubeFormFactor(n_samples=4)

    ff = hemcube.compute_form_factor(floor, light)

    print(f"地板到光源的形状因子: {ff:.6f}")



    ff2 = hemcube.compute_form_factor(ceiling, light)

    print(f"天花板到光源的形状因子: {ff2:.6f}")



    print("\n辐射度算法测试完成!")


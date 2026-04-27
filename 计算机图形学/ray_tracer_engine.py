# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / ray_tracer_engine



本文件实现 ray_tracer_engine 相关的算法功能。

"""



import numpy as np

import math

import time





class Vec3:

    """三维向量（用于简化表示）"""



    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = x

        self.y = y

        self.z = z



    def __add__(self, other):

        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)



    def __sub__(self, other):

        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)



    def __mul__(self, scalar):

        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)



    def dot(self, other):

        return self.x * other.x + self.y * other.y + self.z * other.z



    def cross(self, other):

        return Vec3(

            self.y * other.z - self.z * other.y,

            self.z * other.x - self.x * other.z,

            self.x * other.y - self.y * other.x

        )



    def norm(self):

        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)



    def normalize(self):

        n = self.norm()

        if n > 0:

            return Vec3(self.x / n, self.y / n, self.z / n)

        return Vec3()



    def to_array(self):

        return np.array([self.x, self.y, self.z])





class Ray:

    """光线"""



    def __init__(self, origin, direction):

        self.origin = np.array(origin, dtype=float)

        d = np.array(direction, dtype=float)

        norm = np.linalg.norm(d)

        self.direction = d / norm if norm > 0 else d





class Material:

    """材质"""



    def __init__(self, kd=(0.8, 0.8, 0.8), ks=(0.0, 0.0, 0.0), ka=(0.2, 0.2, 0.2),

                 shininess=32.0, reflectivity=0.0, transparency=0.0, ior=1.0):

        """

        初始化材质



        参数:

            kd: 漫反射系数 (RGB)

            ks: 高光系数 (RGB)

            ka: 环境光系数 (RGB)

            shininess: 光泽度

            reflectivity: 反射率

            transparency: 透明度

            ior: 折射率

        """

        self.kd = np.array(kd, dtype=float)

        self.ks = np.array(ks, dtype=float)

        self.ka = np.array(ka, dtype=float)

        self.shininess = shininess

        self.reflectivity = reflectivity

        self.transparency = transparency

        self.ior = ior





class Sphere:

    """球体"""



    def __init__(self, center, radius, material=None):

        self.center = np.array(center, dtype=float)

        self.radius = radius

        self.material = material or Material()



    def intersect(self, ray, t_min=0.001, t_max=np.inf):

        """光线-球体求交"""

        L = self.center - ray.origin

        t_ca = np.dot(L, ray.direction)

        if t_ca < 0:

            return False, float('inf')

        d_sq = np.dot(L, L) - t_ca * t_ca

        if d_sq > self.radius ** 2:

            return False, float('inf')

        t_hc = math.sqrt(self.radius ** 2 - d_sq)

        t1 = t_ca - t_hc

        t2 = t_ca + t_hc

        if t1 > t_min:

            t = t1

        elif t2 > t_min:

            t = t2

        else:

            return False, float('inf')

        if t > t_max:

            return False, float('inf')

        return True, t



    def get_normal(self, point):

        """计算法线"""

        return (np.array(point) - self.center) / self.radius





class Plane:

    """平面"""



    def __init__(self, point, normal, material=None):

        self.point = np.array(point, dtype=float)

        n = np.array(normal, dtype=float)

        self.normal = n / np.linalg.norm(n)

        self.material = material or Material()



    def intersect(self, ray, t_min=0.001, t_max=np.inf):

        """光线-平面求交"""

        denom = np.dot(self.normal, ray.direction)

        if abs(denom) < 1e-8:

            return False, float('inf')

        t = np.dot(self.point - ray.origin, self.normal) / denom

        if t < t_min or t > t_max:

            return False, float('inf')

        return True, t



    def get_normal(self, point):

        """返回法线"""

        return self.normal





class Scene:

    """场景"""



    def __init__(self):

        self.objects = []

        self.lights = []

        self.ambient = np.array([0.1, 0.1, 0.1])



    def add_object(self, obj):

        self.objects.append(obj)



    def add_light(self, position, intensity):

        self.lights.append({

            'position': np.array(position, dtype=float),

            'intensity': np.array(intensity, dtype=float)

        })



    def set_ambient(self, ambient):

        self.ambient = np.array(ambient, dtype=float)





class Camera:

    """摄影机"""



    def __init__(self, position, look_at, up, fov=60, aspect=1.0):

        """

        初始化摄影机



        参数:

            position: 位置

            look_at: 观察点

            up: 上方向

            fov: 垂直视野角度

            aspect: 宽高比

        """

        self.position = np.array(position, dtype=float)

        self.look_at = np.array(look_at, dtype=float)

        self.up = np.array(up, dtype=float)

        self.fov = fov

        self.aspect = aspect



        # 计算相机坐标系

        self.forward = self.look_at - self.position

        self.forward = self.forward / np.linalg.norm(self.forward)



        self.right = np.cross(self.forward, self.up)

        self.right = self.right / np.linalg.norm(self.right)



        self.cam_up = np.cross(self.right, self.forward)



    def get_ray(self, u, v):

        """

        获取穿过像素 (u, v) 的光线



        参数:

            u, v: 归一化的像素坐标 [0, 1]

        返回:

            ray: 光线

        """

        # u, v 是归一化坐标，转换到屏幕坐标

        # 屏幕坐标范围 [-1, 1]

        sx = (2 * u - 1) * self.aspect * math.tan(math.radians(self.fov / 2))

        sy = (1 - 2 * v) * math.tan(math.radians(self.fov / 2))



        # 光线方向

        direction = self.forward + sx * self.right + sy * self.cam_up

        direction = direction / np.linalg.norm(direction)



        return Ray(self.position, direction)





class RayTracer:

    """光线追踪器"""



    def __init__(self, scene, camera, max_depth=3):

        """

        初始化光线追踪器



        参数:

            scene: 场景

            camera: 摄影机

            max_depth: 最大递归深度

        """

        self.scene = scene

        self.camera = camera

        self.max_depth = max_depth



    def trace_ray(self, ray, depth=0):

        """

        追踪光线



        参数:

            ray: 光线

            depth: 当前深度

        返回:

            color: 颜色 (RGB)

        """

        if depth > self.max_depth:

            return np.array([0.0, 0.0, 0.0])



        # 找最近交点

        hit_obj = None

        hit_t = float('inf')

        hit_point = None



        for obj in self.scene.objects:

            hit, t = obj.intersect(ray, t_min=0.001, t_max=hit_t)

            if hit:

                hit_t = t

                hit_obj = obj

                hit_point = ray.origin + t * ray.direction



        if hit_obj is None:

            # 背景色（简单渐变）

            t = 0.5 * (ray.direction[1] + 1.0)

            return (1 - t) * np.array([1.0, 1.0, 1.0]) + t * np.array([0.5, 0.7, 1.0])



        # 计算着色

        color = self._shade(ray, hit_obj, hit_point, depth)



        return color



    def _shade(self, ray, obj, hit_point, depth):

        """

        着色计算



        参数:

            ray: 光线

            obj: 命中物体

            hit_point: 交点

            depth: 递归深度

        返回:

            color: 颜色

        """

        material = obj.material

        normal = obj.get_normal(hit_point)



        # 确保法线朝向光源

        if np.dot(normal, ray.direction) > 0:

            normal = -normal



        color = np.zeros(3)



        # 环境光

        color += material.ka * self.scene.ambient



        # 光源贡献

        for light in self.scene.lights:

            light_dir = light['position'] - hit_point

            light_dist = np.linalg.norm(light_dir)

            light_dir = light_dir / light_dist



            # 漫反射

            diff = max(0, np.dot(normal, light_dir))

            color += material.kd * diff * light['intensity']



            # 高光

            view_dir = -ray.direction

            reflect_dir = 2 * np.dot(normal, light_dir) * normal - light_dir

            reflect_dir = reflect_dir / np.linalg.norm(reflect_dir)

            spec = pow(max(0, np.dot(view_dir, reflect_dir)), material.shininess)

            color += material.ks * spec * light['intensity']



        # 反射

        if material.reflectivity > 0 and depth < self.max_depth:

            reflect_dir = ray.direction - 2 * np.dot(ray.direction, normal) * normal

            reflect_ray = Ray(hit_point + normal * 0.001, reflect_dir)

            reflect_color = self.trace_ray(reflect_ray, depth + 1)

            color = (1 - material.reflectivity) * color + material.reflectivity * reflect_color



        # 限制在 [0, 1]

        color = np.clip(color, 0, 1)



        return color



    def render(self, width, height):

        """

        渲染图像



        参数:

            width: 图像宽度

            height: 图像高度

        返回:

            image: 图像数据 (height, width, 3)

        """

        image = np.zeros((height, width, 3))



        for y in range(height):

            for x in range(width):

                u = (x + 0.5) / width

                v = (y + 0.5) / height



                ray = self.camera.get_ray(u, v)

                color = self.trace_ray(ray)

                image[y, x] = color



            if y % 10 == 0:

                print(f"渲染进度: {y}/{height}")



        return image





def simple_render_test():

    """简单渲染测试"""

    print("=== 光线追踪渲染测试 ===")



    # 创建场景

    scene = Scene()



    # 添加物体

    mat_red = Material(kd=[0.8, 0.2, 0.2], ks=[0.5, 0.5, 0.5], shininess=32)

    mat_green = Material(kd=[0.2, 0.8, 0.2], ks=[0.3, 0.3, 0.3], shininess=16)

    mat_white = Material(kd=[0.9, 0.9, 0.9], ks=[0.1, 0.1, 0.1], shininess=4)

    mat_mirror = Material(kd=[0.9, 0.9, 0.9], ks=[0.9, 0.9, 0.9],

                          shininess=128, reflectivity=0.9)



    scene.add_object(Sphere([0, 0, 5], 1.0, mat_red))

    scene.add_object(Sphere([2, 0, 5], 0.8, mat_mirror))

    scene.add_object(Plane([0, -1, 0], [0, 1, 0], mat_white))



    # 添加光源

    scene.add_light([5, 5, 5], [1.0, 1.0, 1.0])

    scene.add_light([-3, 3, 3], [0.5, 0.5, 0.5])



    scene.set_ambient([0.1, 0.1, 0.1])



    # 创建摄影机

    camera = Camera(

        position=[0, 1, 0],

        look_at=[0, 0, 5],

        up=[0, 1, 0],

        fov=60,

        aspect=1.0

    )



    # 创建光线追踪器

    tracer = RayTracer(scene, camera, max_depth=3)



    # 渲染低分辨率测试

    print("\n渲染 64x64 测试图像...")

    start = time.time()

    image = tracer.render(64, 64)

    print(f"渲染时间: {time.time() - start:.2f}s")



    # 统计信息

    avg_color = np.mean(image)

    print(f"平均像素值: {avg_color:.4f}")

    print(f"图像尺寸: {image.shape}")



    # 验证渲染结果

    print(f"像素值范围: [{np.min(image):.4f}, {np.max(image):.4f}]")



    return image





if __name__ == "__main__":

    image = simple_render_test()



    # 保存为文本检查

    print("\n=== 部分像素值 ===")

    print(f"左上角 (0,0): {image[0, 0].round(3)}")

    print(f"中心 ({32}, {32}): {image[32, 32].round(3)}")

    print(f"右下角 (63, 63): {image[63, 63].round(3)}")



    print("\n光线追踪渲染测试完成!")


# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / ray_tracing_basic



本文件实现 ray_tracing_basic 相关的算法功能。

"""



from typing import List, Tuple, Optional

import math





# ============ 向量和基本类 ============



class Vec3:

    """三维向量"""

    

    def __init__(self, x: float, y: float, z: float):

        self.x = x

        self.y = y

        self.z = z

    

    def __add__(self, other: 'Vec3') -> 'Vec3':

        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    

    def __sub__(self, other: 'Vec3') -> 'Vec3':

        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    

    def __mul__(self, scalar: float) -> 'Vec3':

        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    

    def __rmul__(self, scalar: float) -> 'Vec3':

        return self.__mul__(scalar)

    

    def dot(self, other: 'Vec3') -> float:

        return self.x * other.x + self.y * other.y + self.z * other.z

    

    def cross(self, other: 'Vec3') -> 'Vec3':

        return Vec3(

            self.y * other.z - self.z * other.y,

            self.z * other.x - self.x * other.z,

            self.x * other.y - self.y * other.x

        )

    

    def length(self) -> float:

        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    

    def normalize(self) -> 'Vec3':

        l = self.length()

        if l < 1e-10:

            return Vec3(0, 0, 0)

        return Vec3(self.x / l, self.y / l, self.z / l)

    

    def reflect(self, normal: 'Vec3') -> 'Vec3':

        """计算反射向量"""

        return self - normal * (2 * self.dot(normal))

    

    def __repr__(self) -> str:

        return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"





class Ray:

    """光线"""

    

    def __init__(self, origin: Vec3, direction: Vec3):

        self.origin = origin

        self.direction = direction.normalize()

    

    def point_at(self, t: float) -> Vec3:

        """计算光线在参数 t 处的点"""

        return self.origin + self.direction * t





# ============ 几何物体 ============



class Sphere:

    """球体"""

    

    def __init__(self, center: Vec3, radius: float, color: Tuple[int, int, int]):

        self.center = center

        self.radius = radius

        self.color = color

    

    def intersect(self, ray: Ray) -> Optional[float]:

        """

        计算光线与球体的交点

        

        参数:

            ray: 光线

        

        返回:

            交点距离 t，如果无交点则返回 None

        """

        oc = ray.origin - self.center

        a = ray.direction.dot(ray.direction)

        b = 2.0 * oc.dot(ray.direction)

        c = oc.dot(oc) - self.radius * self.radius

        discriminant = b * b - 4 * a * c

        

        if discriminant < 0:

            return None

        

        t1 = (-b - math.sqrt(discriminant)) / (2 * a)

        t2 = (-b + math.sqrt(discriminant)) / (2 * a)

        

        # 返回最近的交点（且为正）

        if t1 > 0.001:

            return t1

        if t2 > 0.001:

            return t2

        return None

    

    def normal(self, point: Vec3) -> Vec3:

        """计算球面上某点的法向量"""

        return (point - self.center).normalize()





class Plane:

    """平面"""

    

    def __init__(self, point: Vec3, normal: Vec3, color: Tuple[int, int, int]):

        self.point = point

        self.normal = normal.normalize()

        self.color = color

    

    def intersect(self, ray: Ray) -> Optional[float]:

        """计算光线与平面的交点"""

        denom = self.normal.dot(ray.direction)

        

        if abs(denom) < 1e-10:

            return None  # 光线与平面平行

        

        t = (self.point - ray.origin).dot(self.normal) / denom

        

        if t > 0.001:

            return t

        return None





class Triangle:

    """三角形"""

    

    def __init__(self, v0: Vec3, v1: Vec3, v2: Vec3, color: Tuple[int, int, int]):

        self.v0 = v0

        self.v1 = v1

        self.v2 = v2

        self.color = color

        self.normal = (v1 - v0).cross(v2 - v0).normalize()

    

    def intersect(self, ray: Ray) -> Optional[float]:

        """Möller-Trumbore 算法计算光线与三角形的交点"""

        epsilon = 1e-10

        

        edge1 = self.v1 - self.v0

        edge2 = self.v2 - self.v0

        h = ray.direction.cross(edge2)

        a = edge1.dot(h)

        

        if abs(a) < epsilon:

            return None  # 光线与三角形平行

        

        f = 1.0 / a

        s = ray.origin - self.v0

        u = f * s.dot(h)

        

        if u < 0 or u > 1:

            return None

        

        q = s.cross(edge1)

        v = f * ray.direction.dot(q)

        

        if v < 0 or u + v > 1:

            return None

        

        t = f * edge2.dot(q)

        

        if t > epsilon:

            return t

        

        return None





# ============ 光线和着色 ============



class PointLight:

    """点光源"""

    

    def __init__(self, position: Vec3, color: Tuple[int, int, int]):

        self.position = position

        self.color = color





def shade(ray: Ray, hit_point: Vec3, normal: Vec3, 

          material_color: Tuple[int, int, int],

          lights: List[PointLight],

          objects: List) -> Tuple[int, int, int]:

    """

    简单的 Phong 着色的

    

    参数:

        ray: 射入光线

        hit_point: 交点

        normal: 法向量

        material_color: 材质颜色

        lights: 光源列表

    

    返回:

        着色后的颜色

    """

    # 环境光

    ambient = 0.1

    r, g, b = material_color

    r = int(r * ambient)

    g = int(g * ambient)

    b = int(b * ambient)

    

    # 漫反射和镜面反射

    for light in lights:

        # 光照方向

        light_dir = (light.position - hit_point).normalize()

        

        # 检查阴影（简化：不计算阴影）

        

        # 漫反射

        diffuse_factor = max(0, normal.dot(light_dir))

        r += int(material_color[0] * diffuse_factor * light.color[0] / 255)

        g += int(material_color[1] * diffuse_factor * light.color[1] / 255)

        b += int(material_color[2] * diffuse_factor * light.color[2] / 255)

        

        # 镜面反射

        view_dir = (ray.origin - hit_point).normalize()

        reflect_dir = light_dir.reflect(normal)

        spec_factor = max(0, view_dir.dot(reflect_dir)) ** 50  # 光泽度

        

        r += int(255 * spec_factor * light.color[0] / 255)

        g += int(255 * spec_factor * light.color[1] / 255)

        b += int(255 * spec_factor * light.color[2] / 255)

    

    # 限制颜色范围

    r = min(255, max(0, r))

    g = min(255, max(0, g))

    b = min(255, max(0, b))

    

    return (r, g, b)





def trace_ray(ray: Ray, objects: List, lights: List[PointLight]) -> Optional[Tuple[int, int, int]]:

    """

    追踪单条光线

    

    参数:

        ray: 光线

        objects: 物体列表

        lights: 光源列表

    

    返回:

        颜色或 None（无交点）

    """

    closest_t = float('inf')

    closest_obj = None

    

    # 找到最近的交点

    for obj in objects:

        t = obj.intersect(ray)

        if t is not None and t < closest_t:

            closest_t = t

            closest_obj = obj

    

    if closest_obj is None:

        return None  # 无交点，返回背景色

    

    # 计算交点信息

    hit_point = ray.point_at(closest_t)

    normal = closest_obj.normal(hit_point)

    

    # 着色的

    return shade(ray, hit_point, normal, closest_obj.color, lights, objects)





def render(width: int, height: int, 

           camera_pos: Vec3,

           objects: List, lights: List[PointLight]) -> List[List[Tuple[int, int, int]]]:

    """

    渲染整个场景

    

    参数:

        width: 图像宽度

        height: 图像高度

        camera_pos: 相机位置

        objects: 物体列表

        lights: 光源列表

    

    返回:

        图像矩阵

    """

    image = []

    

    # 相机参数

    fov = 60  # 视场角（度）

    aspect_ratio = width / height

    screen_distance = 1.0 / math.tan(math.radians(fov / 2))

    

    for y in range(height):

        row = []

        for x in range(width):

            # 计算像素对应的光线方向

            # 归一化像素坐标 (-1 到 1)

            px = (2 * ((x + 0.5) / width) - 1) * aspect_ratio

            py = 1 - 2 * ((y + 0.5) / height)

            

            # 光线方向（朝向屏幕）

            direction = Vec3(px, py, -screen_distance).normalize()

            

            # 创建光线

            ray = Ray(camera_pos, direction)

            

            # 追踪光线

            color = trace_ray(ray, objects, lights)

            

            # 背景色（深蓝）

            if color is None:

                color = (20, 20, 50)

            

            row.append(color)

        

        image.append(row)

    

    return image





if __name__ == "__main__":

    print("=" * 60)

    print("基础光线追踪测试")

    print("=" * 60)

    

    # 创建场景

    objects = [

        # 地面

        Plane(Vec3(0, -2, 0), Vec3(0, 1, 0), (100, 100, 100)),

        # 球体1

        Sphere(Vec3(0, 0, -10), 2.0, (255, 0, 0)),

        # 球体2

        Sphere(Vec3(3, -1, -12), 1.5, (0, 255, 0)),

        # 球体3

        Sphere(Vec3(-3, 1, -8), 1.0, (0, 0, 255)),

    ]

    

    # 光源

    lights = [

        PointLight(Vec3(5, 10, -5), (255, 255, 255)),

    ]

    

    # 相机位置

    camera = Vec3(0, 2, 10)

    

    # 渲染小图像用于测试

    print("\n渲染 10x10 图像:")

    image = render(10, 10, camera, objects, lights)

    

    print("\n  图像输出 (ASCII 颜色块):")

    color_chars = {

        (255, 0, 0): "R",

        (0, 255, 0): "G",

        (0, 0, 255): "B",

        (100, 100, 100): ".",

        (20, 20, 50): " ",

    }

    

    for y, row in enumerate(image):

        chars = ""

        for x, color in enumerate(row):

            char = color_chars.get(color, "X")

            chars += char

        print(f"    y={y}: {chars}")

    

    # 测试求交计算

    print("\n测试球体求交:")

    ray = Ray(Vec3(0, 2, 10), Vec3(0, 0, -1))

    sphere = Sphere(Vec3(0, 0, -10), 2.0, (255, 0, 0))

    

    t = sphere.intersect(ray)

    print(f"  光线: 从(0,2,10)朝(0,0,-1)")

    print(f"  球体: 中心(0,0,-10), 半径2")

    print(f"  交点距离 t = {t}")

    

    if t:

        hit_point = ray.point_at(t)

        normal = sphere.normal(hit_point)

        print(f"  交点: {hit_point}")

        print(f"  法向量: {normal}")

    

    # 测试平面求交

    print("\n测试平面求交:")

    plane = Plane(Vec3(0, -2, 0), Vec3(0, 1, 0), (100, 100, 100))

    t = plane.intersect(ray)

    print(f"  光线: 从(0,2,10)朝(0,0,-1)")

    print(f"  平面: 点(0,-2,0), 法向量(0,1,0)")

    print(f"  交点距离 t = {t}")

    

    if t:

        hit_point = ray.point_at(t)

        print(f"  交点: {hit_point}")

    

    print("\n" + "=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  时间复杂度: O(w × h × n)")

    print("    w × h = 像素数")

    print("    n = 物体数")

    print("  空间复杂度: O(n) 物体数据 + O(w×h) 图像")

    print("  优化:")

    print("    - BVH 加速结构")

    print("    - 光线追踪加速")

    print("    - 并行渲染")


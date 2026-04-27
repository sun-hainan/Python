# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / z_buffer



本文件实现 z_buffer 相关的算法功能。

"""



from typing import List, Tuple, Optional

import math





# ============ 顶点变换 ============



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

    

    def to_homogeneous(self, w: float = 1.0) -> 'Vec4':

        """转换为齐次坐标"""

        return Vec4(self.x, self.y, self.z, w)





class Vec4:

    """四维向量（齐次坐标）"""

    

    def __init__(self, x: float, y: float, z: float, w: float):

        self.x = x

        self.y = y

        self.z = z

        self.w = w

    

    def __mul__(self, scalar: float) -> 'Vec4':

        return Vec4(self.x * scalar, self.y * scalar, self.z * scalar, self.w * scalar)

    

    def to_perspective(self) -> Vec3:

        """透视除法"""

        if abs(self.w) < 1e-10:

            return Vec3(0, 0, 0)

        return Vec3(self.x / self.w, self.y / self.w, self.z / self.w)





class Mat4:

    """4x4 变换矩阵"""

    

    def __init__(self, data: List[List[float]]):

        self.data = data

    

    @staticmethod

    def identity() -> 'Mat4':

        return Mat4([

            [1, 0, 0, 0],

            [0, 1, 0, 0],

            [0, 0, 1, 0],

            [0, 0, 0, 1]

        ])

    

    @staticmethod

    def translation(x: float, y: float, z: float) -> 'Mat4':

        return Mat4([

            [1, 0, 0, x],

            [0, 1, 0, y],

            [0, 0, 1, z],

            [0, 0, 0, 1]

        ])

    

    @staticmethod

    def scaling(x: float, y: float, z: float) -> 'Mat4':

        return Mat4([

            [x, 0, 0, 0],

            [0, y, 0, 0],

            [0, 0, z, 0],

            [0, 0, 0, 1]

        ])

    

    @staticmethod

    def rotation_y(angle: float) -> 'Mat4':

        c = math.cos(angle)

        s = math.sin(angle)

        return Mat4([

            [c, 0, s, 0],

            [0, 1, 0, 0],

            [-s, 0, c, 0],

            [0, 0, 0, 1]

        ])

    

    @staticmethod

    def perspective(fov: float, aspect: float, near: float, far: float) -> 'Mat4':

        """透视投影矩阵"""

        f = 1.0 / math.tan(fov / 2)

        return Mat4([

            [f / aspect, 0, 0, 0],

            [0, f, 0, 0],

            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],

            [0, 0, -1, 0]

        ])

    

    def transform(self, v: Vec3) -> Vec3:

        """变换顶点"""

        v4 = v.to_homogeneous()

        result = self * v4

        return result.to_perspective()

    

    def __mul__(self, other: 'Mat4') -> 'Mat4':

        """矩阵乘法"""

        result = [[0.0] * 4 for _ in range(4)]

        for i in range(4):

            for j in range(4):

                for k in range(4):

                    result[i][j] += self.data[i][k] * other.data[k][j]

        return Mat4(result)

    

    def __mul__(self, v: Vec4) -> Vec4:

        """矩阵与向量乘法"""

        result = [0.0] * 4

        for i in range(4):

            for j in range(4):

                result[i] += self.data[i][j] * (v.x if j == 0 else v.y if j == 1 else v.z if j == 2 else v.w)

        return Vec4(result[0], result[1], result[2], result[3])





# ============ Z-Buffer 算法 ============



class ZBuffer:

    """

    Z-Buffer 深度缓冲

    

    属性:

        width: 宽度

        height: 高度

        depth_buffer: 深度缓冲

        color_buffer: 颜色缓冲

    """

    

    def __init__(self, width: int, height: int):

        self.width = width

        self.height = height

        

        # 初始化深度缓冲（最大深度表示最远）

        self.depth_buffer = [[float('inf') for _ in range(width)] for _ in range(height)]

        

        # 初始化颜色缓冲

        self.color_buffer = [[(128, 128, 128) for _ in range(width)] for _ in range(height)]

    

    def set_pixel(self, x: int, y: int, z: float, color: Tuple[int, int, int]):

        """

        设置像素（带深度测试）

        

        参数:

            x, y: 像素坐标

            z: 深度值

            color: 颜色

        """

        if 0 <= x < self.width and 0 <= y < self.height:

            # 深度测试：z 值越小表示越近

            if z < self.depth_buffer[y][x]:

                self.depth_buffer[y][x] = z

                self.color_buffer[y][x] = color

    

    def clear(self):

        """清除缓冲"""

        self.depth_buffer = [[float('inf') for _ in range(self.width)] for _ in range(self.height)]

        self.color_buffer = [[(128, 128, 128) for _ in range(self.width)] for _ in range(self.height)]





class Triangle:

    """三角形"""

    

    def __init__(self, v0: Vec3, v1: Vec3, v2: Vec3, color: Tuple[int, int, int]):

        self.v0 = v0

        self.v1 = v1

        self.v2 = v2

        self.color = color

    

    def bounding_box(self) -> Tuple[int, int, int, int]:

        """计算包围盒"""

        min_x = int(min(self.v0.x, self.v1.x, self.v2.x))

        max_x = int(max(self.v0.x, self.v1.x, self.v2.x))

        min_y = int(min(self.v0.y, self.v1.y, self.v2.y))

        max_y = int(max(self.v0.y, self.v1.y, self.v2.y))

        return min_x, max_x, min_y, max_y

    

    def render(self, zbuffer: ZBuffer, transform: Mat4):

        """

        光栅化三角形到 Z-Buffer

        

        参数:

            zbuffer: Z-Buffer

            transform: 变换矩阵

        """

        # 变换顶点

        p0 = transform.transform(self.v0)

        p1 = transform.transform(self.v1)

        p2 = transform.transform(self.v2)

        

        # 视口变换

        def viewport(x, y, z, width, height):

            # 简化的视口变换

            px = int((x + 1) * width / 2)

            py = int((1 - y) * height / 2)  # y 翻转

            pz = z  # 保持原始 z

            return px, py, pz

        

        w, h = zbuffer.width, zbuffer.height

        

        # 计算变换后的顶点

        pts = [

            viewport(p0.x, p0.y, p0.z, w, h),

            viewport(p1.x, p1.y, p1.z, w, h),

            viewport(p2.x, p2.y, p2.z, w, h)

        ]

        

        # 包围盒

        min_x = max(0, min(pts[0][0], pts[1][0], pts[2][0]))

        max_x = min(w - 1, max(pts[0][0], pts[1][0], pts[2][0]))

        min_y = max(0, min(pts[0][1], pts[1][1], pts[2][1]))

        max_y = min(h - 1, max(pts[0][1], pts[1][1], pts[2][1]))

        

        # 边缘函数（光栅化）

        for y in range(min_y, max_y + 1):

            for x in range(min_x, max_x + 1):

                # 计算像素中心

                px = x + 0.5

                py = y + 0.5

                

                # 重心坐标插值计算 z

                def area(v0, v1, v2):

                    return (v1[0] - v0[0]) * (v2[1] - v0[1]) - (v2[0] - v0[0]) * (v1[1] - v0[1])

                

                A0 = pts[0][0] - px

                A1 = pts[1][0] - px

                A2 = pts[2][0] - px

                B0 = pts[0][1] - py

                B1 = pts[1][1] - py

                B2 = pts[2][1] - py

                

                # 简化的包围测试

                if (pts[0][0] - px) * (pts[1][1] - pts[0][1]) - (pts[1][0] - pts[0][0]) * (pts[0][1] - py) < 0:

                    continue

                if (pts[1][0] - px) * (pts[2][1] - pts[1][1]) - (pts[2][0] - pts[1][0]) * (pts[1][1] - py) < 0:

                    continue

                if (pts[2][0] - px) * (pts[0][1] - pts[2][1]) - (pts[0][0] - pts[2][0]) * (pts[2][1] - py) < 0:

                    continue

                

                # 计算 z 值（简化：使用平均 z）

                z = (pts[0][2] + pts[1][2] + pts[2][2]) / 3.0

                

                zbuffer.set_pixel(x, y, z, self.color)





def render_scene_zbuffer(width: int, height: int,

                         triangles: List[Triangle],

                         model_matrix: Mat4,

                         view_matrix: Mat4,

                         projection_matrix: Mat4) -> ZBuffer:

    """

    使用 Z-Buffer 渲染场景

    

    参数:

        width, height: 输出尺寸

        triangles: 三角形列表

        model_matrix: 模型变换

        view_matrix: 视图变换

        projection_matrix: 投影变换

    

    返回:

        Z-Buffer

    """

    zbuffer = ZBuffer(width, height)

    

    # 组合变换矩阵

    mvp = projection_matrix * view_matrix * model_matrix

    

    # 光栅化每个三角形

    for tri in triangles:

        tri.render(zbuffer, mvp)

    

    return zbuffer





if __name__ == "__main__":

    print("=" * 60)

    print("Z-Buffer 深度测试算法测试")

    print("=" * 60)

    

    # 创建测试场景

    triangles = [

        # 红色三角形（远处）

        Triangle(Vec3(-1, -1, -5), Vec3(1, -1, -5), Vec3(0, 1, -5), (255, 0, 0)),

        # 绿色三角形（更近）

        Triangle(Vec3(-0.5, -0.5, -3), Vec3(0.5, -0.5, -3), Vec3(0, 0.5, -3), (0, 255, 0)),

    ]

    

    # 创建 Z-Buffer

    width, height = 20, 20

    zbuffer = ZBuffer(width, height)

    

    # 变换矩阵

    model = Mat4.identity()

    view = Mat4.identity()

    projection = Mat4.perspective(math.radians(60), 1.0, 0.1, 100.0)

    

    # 渲染

    for tri in triangles:

        tri.render(zbuffer, projection * view * model)

    

    # 打印颜色缓冲（ASCII）

    print("\n渲染结果 (20x10 放大显示):")

    print("  绿色三角形应该在红色前面")

    

    char_map = {

        (255, 0, 0): "R",

        (0, 255, 0): "G",

        (128, 128, 128): ".",

    }

    

    for y in range(height - 1, -1, -2):  # 每两行取一行

        row = ""

        for x in range(0, width, 2):  # 每两列取一列

            color = zbuffer.color_buffer[y][x]

            char = char_map.get(color, "?")

            row += char

        print(f"    y={y:2d} {row}")

    

    # 测试深度测试

    print("\n测试深度测试逻辑:")

    zbuf = ZBuffer(10, 10)

    

    print("  1. 写入 (5,5) z=10 颜色红")

    zbuf.set_pixel(5, 5, 10.0, (255, 0, 0))

    print(f"     当前 z={zbuf.depth_buffer[5][5]:.1f}")

    

    print("  2. 写入 (5,5) z=5 颜色绿 (更近)")

    zbuf.set_pixel(5, 5, 5.0, (0, 255, 0))

    print(f"     当前 z={zbuf.depth_buffer[5][5]:.1f}, 颜色={zbuf.color_buffer[5][5]}")

    

    print("  3. 写入 (5,5) z=8 颜色蓝 (中间距离)")

    zbuf.set_pixel(5, 5, 8.0, (0, 0, 255))

    print(f"     当前 z={zbuf.depth_buffer[5][5]:.1f}, 颜色={zbuf.color_buffer[5][5]}")

    

    print("  4. 写入 (5,5) z=15 颜色黄 (更远)")

    zbuf.set_pixel(5, 5, 15.0, (255, 255, 0))

    print(f"     当前 z={zbuf.depth_buffer[5][5]:.1f}, 颜色={zbuf.color_buffer[5][5]}")

    

    print("\n  期望结果: z=5.0, 颜色=(0,255,0) 绿色")

    print(f"  实际结果: z={zbuf.depth_buffer[5][5]:.1f}, 颜色={zbuf.color_buffer[5][5]}")

    

    print("\n" + "=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  时间复杂度: O(w × h × n)")

    print("    w × h = 像素数")

    print("    n = 三角形数")

    print("  空间复杂度: O(w × h) 深度缓冲 + 颜色缓冲")

    print("  优点:")

    print("    - 简单实现")

    print("    - 硬件友好")

    print("    - 支持任意三角形顺序")

    print("  缺点:")

    print("    - 需要大量内存")

    print("    - z 精度问题")

    print("    - 不支持透明物体")


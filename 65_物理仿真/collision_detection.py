# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / collision_detection



本文件实现 collision_detection 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt

import matplotlib.patches as patches

from matplotlib.collections import PatchCollection





class AABB:

    """

    轴对齐包围盒 (Axis-Aligned Bounding Box)

    

    由两个点定义：min_corner (xmin, ymin) 和 max_corner (xmax, ymax)

    盒子边与坐标轴平行

    """

    

    def __init__(self, min_corner, max_corner):

        """

        初始化AABB

        

        参数:

            min_corner: 左下角坐标 [xmin, ymin]

            max_corner: 右上角坐标 [xmax, ymax]

        """

        self.min_corner = np.array(min_corner)

        self.max_corner = np.array(max_corner)

    

    @property

    def center(self):

        """返回包围盒中心"""

        return (self.min_corner + self.max_corner) / 2.0

    

    @property

    def size(self):

        """返回包围盒尺寸 [width, height]"""

        return self.max_corner - self.min_corner

    

    @property

    def width(self):

        """返回宽度"""

        return self.max_corner[0] - self.min_corner[0]

    

    @property

    def height(self):

        """返回高度"""

        return self.max_corner[1] - self.min_corner[1]

    

    def intersects(self, other):

        """

        检测与另一个AABB是否相交

        

        参数:

            other: 另一个AABB对象

        

        返回:

            bool: 是否相交

        """

        # 两个AABB相交当且仅当在每个维度上都有重叠

        # 即：a.min < b.max 且 a.max > b.min

        if self.max_corner[0] < other.min_corner[0]:

            return False  # a在b左侧

        if self.min_corner[0] > other.max_corner[0]:

            return False  # a在b右侧

        if self.max_corner[1] < other.min_corner[1]:

            return False  # a在b下方

        if self.min_corner[1] > other.max_corner[1]:

            return False  # a在b上方

        return True

    

    def contains_point(self, point):

        """

        检测点是否在AABB内部

        

        参数:

            point: 点坐标 [x, y]

        

        返回:

            bool: 是否在内部

        """

        p = np.array(point)

        return (self.min_corner <= p).all() and (p <= self.max_corner).all()

    

    def expand(self, margin):

        """

        扩展包围盒

        

        参数:

            margin: 扩展距离

        """

        self.min_corner -= margin

        self.max_corner += margin

    

    def draw(self, ax, color='blue', alpha=0.3):

        """

        绘制AABB

        

        参数:

            ax: matplotlib Axes对象

            color: 颜色

            alpha: 透明度

        """

        rect = patches.Rectangle(

            self.min_corner,

            self.width,

            self.height,

            linewidth=2,

            edgecolor=color,

            facecolor=color,

            alpha=alpha

        )

        ax.add_patch(rect)





class Sphere:

    """

    球体碰撞体

    

    由圆心坐标和半径定义

    """

    

    def __init__(self, center, radius):

        """

        初始化球体

        

        参数:

            center: 圆心坐标 [x, y]

            radius: 半径

        """

        self.center = np.array(center, dtype=float)

        self.radius = radius

    

    def intersects(self, other):

        """

        检测与另一个球体是否相交

        

        原理：两球相交当 distance(c1, c2) < r1 + r2

        

        参数:

            other: 另一个Sphere对象

        

        返回:

            bool: 是否相交

        """

        # 计算两圆心距离

        distance = np.linalg.norm(self.center - other.center)

        

        # 相交条件：距离小于半径之和

        return distance < (self.radius + other.radius)

    

    def intersects_aabb(self, aabb):

        """

        检测与AABB是否相交

        

        原理：找到AABB中距离球心最近的点

        如果该点距离 < radius，则相交

        

        参数:

            aabb: AABB对象

        

        返回:

            bool: 是否相交

        """

        # 找到AABB中距离球心最近的点

        # clamp将值限制在[min, max]范围内

        closest_x = np.clip(self.center[0], aabb.min_corner[0], aabb.max_corner[0])

        closest_y = np.clip(self.center[1], aabb.min_corner[1], aabb.max_corner[1])

        closest_point = np.array([closest_x, closest_y])

        

        # 计算距离

        distance = np.linalg.norm(self.center - closest_point)

        

        return distance < self.radius

    

    def get_aabb(self):

        """

        获取球体的AABB包围盒

        

        返回:

            AABB对象

        """

        min_corner = self.center - self.radius

        max_corner = self.center + self.radius

        return AABB(min_corner, max_corner)

    

    def draw(self, ax, color='green', alpha=0.3):

        """

        绘制球体

        

        参数:

            ax: matplotlib Axes对象

            color: 颜色

            alpha: 透明度

        """

        circle = patches.Circle(

            self.center,

            self.radius,

            linewidth=2,

            edgecolor=color,

            facecolor=color,

            alpha=alpha

        )

        ax.add_patch(circle)





class OBB:

    """

    定向包围盒 (Oriented Bounding Box)

    

    盒子可以任意方向，不与坐标轴平行

    使用分离轴定理(SAT)进行碰撞检测

    """

    

    def __init__(self, center, half_extents, rotation_angle):

        """

        初始化OBB

        

        参数:

            center: 盒子中心 [x, y]

            half_extents: 半尺寸 [half_width, half_height]

            rotation_angle: 旋转角度（弧度）

        """

        self.center = np.array(center, dtype=float)

        self.half_extents = np.array(half_extents, dtype=float)

        self.rotation_angle = rotation_angle

        

        # 计算旋转矩阵

        c = np.cos(rotation_angle)

        s = np.sin(rotation_angle)

        self.rotation_matrix = np.array([[c, -s], [s, c]])

        

        # 计算四个顶点（相对于中心）

        self.local_corners = np.array([

            [-1, -1], [1, -1], [1, 1], [-1, 1]

        ]) * self.half_extents  # 本地坐标

    

    @property

    def world_corners(self):

        """返回世界坐标系的四个顶点"""

        rotated = self.local_corners @ self.rotation_matrix.T

        return self.center + rotated

    

    def get_axes(self):

        """

        获取OBB的两个局部轴（用于SAT检测）

        

        返回:

            两个轴向量（单位向量）

        """

        axis1 = self.rotation_matrix @ np.array([1, 0])

        axis2 = self.rotation_matrix @ np.array([0, 1])

        return axis1, axis2

    

    def project_onto_axis(self, axis):

        """

        将OBB投影到指定轴上

        

        参数:

            axis: 轴向量（单位向量）

        

        返回:

            (min, max): 投影的最小和最大值

        """

        corners = self.world_corners

        # 点积得到投影标量

        projections = corners @ axis

        return np.min(projections), np.max(projections)

    

    def intersects(self, other):

        """

        检测与另一个OBB是否相交（使用SAT）

        

        分离轴定理：两个凸多面体不相交当且仅当存在一个分离轴

        对于2D OBB，只需检测4个轴（各2个）

        

        参数:

            other: 另一个OBB对象

        

        返回:

            bool: 是否相交

        """

        # 获取两个OBB的局部轴

        axes = list(self.get_axes()) + list(other.get_axes())

        

        for axis in axes:

            # 归一化轴

            axis = axis / np.linalg.norm(axis)

            

            # 投影两个OBB

            min1, max1 = self.project_onto_axis(axis)

            min2, max2 = other.project_onto_axis(axis)

            

            # 检查是否分离（无重叠）

            if max1 < min2 or max2 < min1:

                return False  # 分离轴存在，不相交

        

        return True  # 所有轴都有重叠，相交

    

    def get_aabb(self):

        """

        获取OBB的AABB包围盒

        

        返回:

            AABB对象

        """

        corners = self.world_corners

        min_corner = np.min(corners, axis=0)

        max_corner = np.max(corners, axis=0)

        return AABB(min_corner, max_corner)

    

    def draw(self, ax, color='red', alpha=0.3):

        """

        绘制OBB

        

        参数:

            ax: matplotlib Axes对象

            color: 颜色

            alpha: 透明度

        """

        corners = self.world_corners

        # 闭合多边形

        polygon = patches.Polygon(

            np.vstack([corners, corners[0]]),

            linewidth=2,

            edgecolor=color,

            facecolor=color,

            alpha=alpha

        )

        ax.add_patch(polygon)





def demo_collision_detection():

    """

    演示碰撞检测

    """

    print("=" * 55)

    print("碰撞检测算法演示")

    print("=" * 55)

    

    # 创建几个AABB

    aabb1 = AABB([0, 0], [2, 2])

    aabb2 = AABB([1.5, 1], [3.5, 3])

    aabb3 = AABB([4, 4], [6, 6])

    

    print("\n1. AABB碰撞检测:")

    print(f"   AABB1: {[0,0]} to [2,2]")

    print(f"   AABB2: {[1.5,1]} to [3.5,3]")

    print(f"   AABB3: {[4,4]} to [6,6]}")

    print(f"   AABB1 vs AABB2: {aabb1.intersects(aabb2)}")  # 应该True

    print(f"   AABB1 vs AABB3: {aabb1.intersects(aabb3)}")  # 应该False

    

    # 创建球体

    sphere1 = Sphere([5, 5], 1.0)

    sphere2 = Sphere([5.8, 5.3], 0.8)

    sphere3 = Sphere([10, 10], 1.0)

    

    print("\n2. 球体碰撞检测:")

    print(f"   Sphere1: center=[5,5], r=1.0")

    print(f"   Sphere2: center=[5.8,5.3], r=0.8")

    print(f"   Sphere3: center=[10,10], r=1.0")

    print(f"   Sphere1 vs Sphere2: {sphere1.intersects(sphere2)}")  # 应该True

    print(f"   Sphere1 vs Sphere3: {sphere1.intersects(sphere3)}")  # 应该False

    

    # 创建OBB

    obb1 = OBB([3, 3], [1, 0.5], np.pi/6)  # 中心[3,3], 半尺寸[1,0.5], 旋转30°

    obb2 = OBB([3.5, 3.2], [1, 0.5], np.pi/6)  # 略微重叠

    obb3 = OBB([6, 6], [1, 0.5], 0)

    

    print("\n3. OBB碰撞检测:")

    print(f"   OBB1: center=[3,3], half=[1,0.5], angle=30°")

    print(f"   OBB2: center=[3.5,3.2], half=[1,0.5], angle=30°")

    print(f"   OBB3: center=[6,6], half=[1,0.5], angle=0°")

    print(f"   OBB1 vs OBB2: {obb1.intersects(obb2)}")  # 应该True

    print(f"   OBB1 vs OBB3: {obb1.intersects(obb3)}")  # 应该False

    

    # 点包含测试

    print("\n4. 点包含检测:")

    print(f"   点[1,1] 在 AABB1 内: {aabb1.contains_point([1, 1])}")  # True

    print(f"   点[3,3] 在 AABB1 内: {aabb1.contains_point([3, 3])}")  # False

    

    # 球体与AABB

    print("\n5. 球体 vs AABB检测:")

    print(f"   Sphere1 vs AABB1: {sphere1.intersects_aabb(aabb1)}")  # False

    print(f"   Sphere1 vs AABB3: {sphere1.intersects_aabb(aabb3)}")  # True





def plot_collision_scenes():

    """

    可视化碰撞检测场景

    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    

    # 场景1：AABB

    ax = axes[0]

    aabb1 = AABB([0, 0], [2, 2])

    aabb2 = AABB([1.5, 1], [3.5, 3])

    aabb3 = AABB([4, 4], [6, 6])

    

    aabb1.draw(ax, 'blue', 0.3)

    aabb2.draw(ax, 'orange', 0.3)

    aabb3.draw(ax, 'green', 0.3)

    

    ax.set_xlim(-1, 7)

    ax.set_ylim(-1, 7)

    ax.set_aspect('equal')

    ax.set_title('AABB碰撞检测\n(蓝色与橙色重叠，绿色分离)')

    ax.grid(True, alpha=0.3)

    ax.axhline(y=0, color='k', linewidth=0.5)

    ax.axvline(x=0, color='k', linewidth=0.5)

    

    # 场景2：球体

    ax = axes[1]

    sphere1 = Sphere([5, 5], 1.5)

    sphere2 = Sphere([6.8, 5.5], 1.2)

    sphere3 = Sphere([10, 10], 1.5)

    

    sphere1.draw(ax, 'green', 0.3)

    sphere2.draw(ax, 'orange', 0.3)

    sphere3.draw(ax, 'red', 0.3)

    

    ax.set_xlim(0, 12)

    ax.set_ylim(0, 12)

    ax.set_aspect('equal')

    ax.set_title('球体碰撞检测\n(绿色与橙色重叠，红色分离)')

    ax.grid(True, alpha=0.3)

    ax.axhline(y=0, color='k', linewidth=0.5)

    ax.axvline(x=0, color='k', linewidth=0.5)

    

    # 场景3：OBB

    ax = axes[2]

    obb1 = OBB([3, 3], [1.5, 0.8], np.pi/6)

    obb2 = OBB([4.2, 3.3], [1.5, 0.8], np.pi/6)

    obb3 = OBB([8, 5], [1.5, 0.8], 0)

    

    obb1.draw(ax, 'blue', 0.3)

    obb2.draw(ax, 'orange', 0.3)

    obb3.draw(ax, 'green', 0.3)

    

    ax.set_xlim(0, 11)

    ax.set_ylim(0, 8)

    ax.set_aspect('equal')

    ax.set_title('OBB碰撞检测\n(蓝色与橙色重叠，绿色分离)')

    ax.grid(True, alpha=0.3)

    ax.axhline(y=0, color='k', linewidth=0.5)

    ax.axvline(x=0, color='k', linewidth=0.5)

    

    plt.tight_layout()

    plt.savefig('collision_detection_result.png', dpi=150)

    plt.show()

    print("图像已保存至 collision_detection_result.png")





if __name__ == "__main__":

    demo_collision_detection()

    plot_collision_scenes()

    print("\n测试完成！碰撞检测是物理仿真的基础算法。")


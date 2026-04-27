# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / collision_detection_2d

本文件实现 collision_detection_2d 相关的算法功能。
"""

import numpy as np
import math


class AABB:
    """
    轴对齐包围盒（Axis-Aligned Bounding Box）

    由最小点和最大点定义：
    min = (min_x, min_y)
    max = (max_x, max_y)
    """

    def __init__(self, min_x, min_y, max_x, max_y):
        """
        初始化 AABB

        参数:
            min_x, min_y: 最小点
            max_x, max_y: 最大点
        """
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    @property
    def min(self):
        return np.array([self.min_x, self.min_y])

    @property
    def max(self):
        return np.array([self.max_x, self.max_y])

    @property
    def center(self):
        return (self.min + self.max) / 2

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    def intersects(self, other):
        """
        检测与另一个 AABB 的碰撞

        公式：两轴上的投影都重叠则碰撞
        """
        if self.max_x < other.min_x or other.max_x < self.min_x:
            return False
        if self.max_y < other.min_y or other.max_y < self.min_y:
            return False
        return True

    def contains_point(self, px, py):
        """检查点是否在 AABB 内"""
        return (self.min_x <= px <= self.max_x and
                self.min_y <= py <= self.max_y)

    def expand(self, margin):
        """扩展 AABB"""
        return AABB(self.min_x - margin, self.min_y - margin,
                   self.max_x + margin, self.max_y + margin)

    def __repr__(self):
        return f"AABB(min=({self.min_x:.2f},{self.min_y:.2f}), " \
               f"max=({self.max_x:.2f},{self.max_y:.2f}))"


class Circle:
    """圆形"""

    def __init__(self, cx, cy, radius):
        """
        初始化圆形

        参数:
            cx, cy: 圆心
            radius: 半径
        """
        self.cx = cx
        self.cy = cy
        self.radius = radius

    @property
    def center(self):
        return np.array([self.cx, self.cy])

    @property
    def diameter(self):
        return self.radius * 2

    def intersects(self, other):
        """
        检测与另一个圆的碰撞

        公式：distance(c1, c2) < r1 + r2
        """
        if isinstance(other, Circle):
            return self._circle_circle(other)
        elif isinstance(other, AABB):
            return self._circle_aabb(other)
        return False

    def _circle_circle(self, other):
        """圆与圆碰撞"""
        dx = self.cx - other.cx
        dy = self.cy - other.cy
        dist_sq = dx * dx + dy * dy
        radius_sum = self.radius + other.radius
        return dist_sq < radius_sum * radius_sum

    def _circle_aabb(self, aabb):
        """圆与 AABB 碰撞"""
        # 找 AABB 上最近的点
        closest_x = max(aabb.min_x, min(self.cx, aabb.max_x))
        closest_y = max(aabb.min_y, min(self.cy, aabb.max_y))

        dx = self.cx - closest_x
        dy = self.cy - closest_y
        dist_sq = dx * dx + dy * dy

        return dist_sq < self.radius * self.radius

    def contains_point(self, px, py):
        """检查点是否在圆内"""
        dx = px - self.cx
        dy = py - self.cy
        return dx * dx + dy * dy <= self.radius * self.radius

    def bounding_box(self):
        """返回外接 AABB"""
        return AABB(self.cx - self.radius, self.cy - self.radius,
                   self.cx + self.radius, self.cy + self.radius)

    def __repr__(self):
        return f"Circle(center=({self.cx:.2f},{self.cy:.2f}), r={self.radius:.2f})"


class Polygon:
    """凸多边形"""

    def __init__(self, vertices):
        """
        初始化多边形

        参数:
            vertices: 顶点列表 [(x,y), ...]（逆时针或顺时针）
        """
        self.vertices = [np.array(v, dtype=float) for v in vertices]

    @property
    def center(self):
        return np.mean(self.vertices, axis=0)

    def get_edges(self):
        """获取所有边向量"""
        n = len(self.vertices)
        edges = []
        for i in range(n):
            edges.append(self.vertices[(i + 1) % n] - self.vertices[i])
        return edges

    def get_normals(self):
        """获取所有边的法线（指向多边形外部）"""
        normals = []
        for i in range(len(self.vertices)):
            p1 = self.vertices[i]
            p2 = self.vertices[(i + 1) % len(self.vertices)]
            edge = p2 - p1
            normal = np.array([edge[1], -edge[0]])  # 左手边法线
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
            normals.append(normal)
        return normals

    def project(self, axis):
        """在轴上投影，返回 (min, max)"""
        projections = [np.dot(v, axis) for v in self.vertices]
        return min(projections), max(projections)

    def contains_point(self, px, py):
        """检查点是否在多边形内（射线投射法）"""
        p = np.array([px, py])
        n = len(self.vertices)
        inside = False

        j = n - 1
        for i in range(n):
            vi = self.vertices[i]
            vj = self.vertices[j]
            if ((vi[1] > p[1]) != (vj[1] > p[1]) and
                p[0] < (vj[0] - vi[0]) * (p[1] - vi[1]) / (vj[1] - vi[1]) + vi[0]):
                inside = not inside
            j = i

        return inside


def sat_collision(poly1, poly2):
    """
    分离轴定理（SAT）检测两个凸多边形碰撞

    原理：如果存在一个轴使两个多边形在该轴上的投影不重叠，
    则它们不相撞。

    参数:
        poly1: 第一个多边形
        poly2: 第二个多边形
    返回:
        colliding: 是否碰撞
        minimum_translation: 最小分离向量
    """
    polygons = [poly1, poly2]

    # 获取所有可能的分离轴（两个多边形所有边的法线）
    axes = []
    for poly in polygons:
        axes.extend(poly.get_normals())

    min_overlap = float('inf')
    min_axis = None

    for axis in axes:
        # 确保轴方向一致（指向多边形中心）
        axis = axis / np.linalg.norm(axis)

        proj1_min, proj1_max = poly1.project(axis)
        proj2_min, proj2_max = poly2.project(axis)

        # 检查投影是否重叠
        overlap = min(proj1_max, proj2_max) - max(proj1_min, proj2_min)

        if overlap <= 0:
            # 发现分离轴，无碰撞
            return False, None

        # 记录最小重叠
        if overlap < min_overlap:
            min_overlap = overlap
            min_axis = axis

    return True, min_axis * min_overlap


class SpatialHashGrid:
    """
    空间哈希网格

    用于加速大量物体的碰撞检测。
    将空间划分为网格，每个物体只与同格或邻格物体检测碰撞。
    """

    def __init__(self, cell_size):
        """
        初始化空间哈希网格

        参数:
            cell_size: 网格大小
        """
        self.cell_size = cell_size
        self.grid = {}

    def _hash_pos(self, x, y):
        """将世界坐标映射到网格坐标"""
        return (int(x / self.cell_size), int(y / self.cell_size))

    def insert(self, obj_id, x, y, width, height):
        """插入物体到网格"""
        min_cell = self._hash_pos(x, y)
        max_cell = self._hash_pos(x + width, y + height)

        for cx in range(min_cell[0], max_cell[0] + 1):
            for cy in range(min_cell[1], max_cell[1] + 1):
                key = (cx, cy)
                if key not in self.grid:
                    self.grid[key] = []
                self.grid[key].append(obj_id)

    def get_potential_collisions(self):
        """
        获取所有可能碰撞的物体对

        返回:
            pairs: 物体对列表 [(id1, id2), ...]
        """
        pairs = []
        seen = set()

        for cell_key, obj_list in self.grid.items():
            for i, obj_id in enumerate(obj_list):
                for other_id in obj_list[i + 1:]:
                    pair = tuple(sorted([obj_id, other_id]))
                    if pair not in seen:
                        seen.add(pair)
                        pairs.append(pair)

        return pairs

    def clear(self):
        """清空网格"""
        self.grid.clear()


class CollisionDetector:
    """
    碰撞检测器

    支持多种形状和检测算法。
    """

    def __init__(self, use_spatial_hash=False, cell_size=50):
        """
        初始化碰撞检测器

        参数:
            use_spatial_hash: 是否使用空间哈希加速
            cell_size: 空间哈希网格大小
        """
        self.use_spatial_hash = use_spatial_hash
        self.spatial_hash = SpatialHashGrid(cell_size) if use_spatial_hash else None
        self.objects = {}  # id -> (shape, x, y)
        self.next_id = 0

    def add_object(self, shape, x, y, width=None, height=None, radius=None):
        """
        添加物体

        参数:
            shape: 形状类型 ('aabb', 'circle', 'polygon')
            x, y: 位置
            width, height: AABB 尺寸
            radius: 圆形半径
            vertices: 多边形顶点（相对于 x, y）
        """
        obj_id = self.next_id
        self.next_id += 1

        if shape == 'aabb':
            bbox = AABB(x, y, x + width, y + height)
            self.objects[obj_id] = ('aabb', bbox)
        elif shape == 'circle':
            circle = Circle(x, y, radius)
            self.objects[obj_id] = ('circle', circle)
        elif shape == 'polygon':
            # vertices 应该是相对于原点的顶点列表
            verts = [(x + v[0], y + v[1]) for v in width]  # width 复用为 vertices
            polygon = Polygon(verts)
            self.objects[obj_id] = ('polygon', polygon)

        return obj_id

    def detect_collisions(self):
        """
        检测所有碰撞

        返回:
            collisions: 碰撞列表 [(id1, id2), ...]
        """
        collisions = []

        if self.use_spatial_hash:
            # 使用空间哈希
            self.spatial_hash.clear()
            for obj_id, (shape_type, shape) in self.objects.items():
                if shape_type == 'aabb':
                    self.spatial_hash.insert(obj_id, shape.min_x, shape.min_y,
                                            shape.width, shape.height)
                elif shape_type == 'circle':
                    self.spatial_hash.insert(obj_id, shape.cx - shape.radius,
                                            shape.cy - shape.radius,
                                            shape.diameter, shape.diameter)

            potential_pairs = self.spatial_hash.get_potential_collisions()

            for id1, id2 in potential_pairs:
                if self._check_collision(id1, id2):
                    collisions.append((id1, id2))
        else:
            # 暴力检测
            obj_ids = list(self.objects.keys())
            for i, id1 in enumerate(obj_ids):
                for id2 in obj_ids[i + 1:]:
                    if self._check_collision(id1, id2):
                        collisions.append((id1, id2))

        return collisions

    def _check_collision(self, id1, id2):
        """检查两个物体的碰撞"""
        shape1_type, shape1 = self.objects[id1]
        shape2_type, shape2 = self.objects[id2]

        # AABB vs AABB
        if shape1_type == 'aabb' and shape2_type == 'aabb':
            return shape1.intersects(shape2)

        # Circle vs Circle
        if shape1_type == 'circle' and shape2_type == 'circle':
            return shape1.intersects(shape2)

        # Circle vs AABB
        if (shape1_type == 'circle' and shape2_type == 'aabb') or \
           (shape1_type == 'aabb' and shape2_type == 'circle'):
            c = shape1 if shape1_type == 'circle' else shape2
            a = shape2 if shape2_type == 'aabb' else shape1
            return c.intersects(a)

        # Polygon vs Polygon (SAT)
        if shape1_type == 'polygon' and shape2_type == 'polygon':
            colliding, _ = sat_collision(shape1, shape2)
            return colliding

        return False


if __name__ == "__main__":
    print("=== 二维碰撞检测测试 ===")

    # 测试 AABB 碰撞
    print("\n1. AABB 碰撞测试")
    aabb1 = AABB(0, 0, 2, 2)
    aabb2 = AABB(1, 1, 3, 3)
    aabb3 = AABB(5, 5, 7, 7)

    print(f"  AABB1: {aabb1}")
    print(f"  AABB2: {aabb2}")
    print(f"  AABB3: {aabb3}")
    print(f"  AABB1 vs AABB2: {aabb1.intersects(aabb2)}")
    print(f"  AABB1 vs AABB3: {aabb1.intersects(aabb3)}")

    # 测试圆形碰撞
    print("\n2. 圆形碰撞测试")
    c1 = Circle(0, 0, 1)
    c2 = Circle(1.5, 0, 1)
    c3 = Circle(5, 0, 1)

    print(f"  Circle1: {c1}")
    print(f"  Circle2: {c2}")
    print(f"  Circle3: {c3}")
    print(f"  C1 vs C2: {c1.intersects(c2)}")
    print(f"  C1 vs C3: {c1.intersects(c3)}")

    # 测试圆与 AABB 碰撞
    print("\n3. 圆与 AABB 碰撞测试")
    print(f"  Circle1 vs AABB1: {c1.intersects(aabb1)}")
    print(f"  Circle1 vs AABB3: {c1.intersects(aabb3)}")

    # 测试多边形
    print("\n4. 多边形碰撞测试 (SAT)")
    poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    poly2 = Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])
    poly3 = Polygon([(5, 5), (7, 5), (7, 7), (5, 7)])

    colliding1, mtv1 = sat_collision(poly1, poly2)
    colliding2, mtv2 = sat_collision(poly1, poly3)
    print(f"  Poly1 vs Poly2: colliding={colliding1}, MTV={mtv1}")
    print(f"  Poly1 vs Poly3: colliding={colliding2}")

    # 点在多边形内
    print("\n5. 点包含测试")
    print(f"  Point (1, 1) in Poly1: {poly1.contains_point(1, 1)}")
    print(f"  Point (3, 3) in Poly1: {poly1.contains_point(3, 3)}")
    print(f"  Point (0.5, 0.5) in Circle1: {c1.contains_point(0.5, 0.5)}")

    # 空间哈希网格测试
    print("\n6. 空间哈希网格测试")
    detector = CollisionDetector(use_spatial_hash=True, cell_size=10)
    detector.add_object('aabb', 0, 0, 2, 2)
    detector.add_object('aabb', 1, 1, 2, 2)
    detector.add_object('aabb', 5, 5, 2, 2)
    detector.add_object('aabb', 6, 6, 2, 2)

    collisions = detector.detect_collisions()
    print(f"  潜在碰撞对数: {len(detector.spatial_hash.get_potential_collisions())}")
    print(f"  实际碰撞: {collisions}")

    # 性能测试
    print("\n7. 性能测试")
    import time

    n_objects = 100
    detector = CollisionDetector(use_spatial_hash=True, cell_size=10)
    import random
    for _ in range(n_objects):
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        detector.add_object('aabb', x, y, 1, 1)

    start = time.time()
    for _ in range(100):
        collisions = detector.detect_collisions()
    elapsed = time.time() - start
    print(f"  100物体 x 100帧: {elapsed*1000:.2f}ms")
    print(f"  检测到的碰撞: {len(collisions)}")

    print("\n二维碰撞检测测试完成!")

# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / bvh_acceleration



本文件实现 bvh_acceleration 相关的算法功能。

"""



import numpy as np

import random





class AABB:

    """

    轴对齐包围盒（Axis-Aligned Bounding Box）



    AABB 由最小点和最大点定义：

    min = (min_x, min_y, min_z)

    max = (max_x, max_y, max_z)



    特点：

    - 简单，易于求交

    - 可能不是最紧凑的包围盒

    """



    def __init__(self, min_point=None, max_point=None):

        """

        初始化 AABB



        参数:

            min_point: 最小点 (3,)

            max_point: 最大点 (3,)

        """

        if min_point is None:

            self.min = np.array([np.inf, np.inf, np.inf])

            self.max = np.array([-np.inf, -np.inf, -np.inf])

        else:

            self.min = np.array(min_point, dtype=float)

            self.max = np.array(max_point, dtype=float)



    def merge(self, other):

        """合并两个 AABB"""

        new_min = np.minimum(self.min, other.min)

        new_max = np.maximum(self.max, other.max)

        return AABB(new_min, new_max)



    def centroid(self):

        """返回包围盒中心"""

        return (self.min + self.max) / 2.0



    def surface_area(self):

        """计算表面积（用于 SAH）"""

        d = self.max - self.min

        return 2.0 * (d[0] * d[1] + d[1] * d[2] + d[2] * d[0])



    def volume(self):

        """计算体积"""

        d = self.max - self.min

        return d[0] * d[1] * d[2]



    def ray_intersect(self, ray, t_min=0.001, t_max=np.inf):

        """

        光线与 AABB 求交



        参数:

            ray: 光线

            t_min: 最小 t 值

            t_max: 最大 t 值

        返回:

            hit: 是否相交

            t_near: 入口 t

            t_far: 出口 t

        """

        # 分解光线方程 O + tD

        for i in range(3):

            # 避免除以零

            if abs(ray.direction[i]) < 1e-8:

                # 光线平行于该轴

                if ray.origin[i] < self.min[i] or ray.origin[i] > self.max[i]:

                    return False, t_min, t_max

            else:

                # 计算交点

                t1 = (self.min[i] - ray.origin[i]) / ray.direction[i]

                t2 = (self.max[i] - ray.origin[i]) / ray.direction[i]



                if t1 > t2:

                    t1, t2 = t2, t1



                t_min = max(t_min, t1)

                t_max = min(t_max, t2)



                if t_min > t_max:

                    return False, t_min, t_max



        return True, t_min, t_max



    def contains_point(self, point):

        """检查点是否在包围盒内"""

        p = np.array(point)

        return (np.all(p >= self.min) and np.all(p <= self.max))



    def expand(self, margin):

        """扩展包围盒"""

        return AABB(self.min - margin, self.max + margin)



    def __repr__(self):

        return f"AABB(min={self.min}, max={self.max})"





class BVHNode:

    """

    BVH 树节点



    BVH 树结构：

    - 内部节点：存储包围盒和子节点引用

    - 叶节点：存储物体列表和包围盒

    """



    def __init__(self, bounds, left=None, right=None, objects=None):

        """

        初始化 BVH 节点



        参数:

            bounds: 包围盒

            left: 左子节点

            right: 右子节点

            objects: 叶节点包含的物体列表

        """

        self.bounds = bounds

        self.left = left

        self.right = right

        self.objects = objects  # 仅叶节点使用



    def is_leaf(self):

        """是否为叶节点"""

        return self.objects is not None





class BVH:

    """

    BVH 加速结构



    使用 SAH（Surface Area Heuristic）构建：

    - 分割成本 = N_left * SA_left + N_right * SA_right

    - 选择成本最低的分割方式

    """



    def __init__(self, objects, max_objects_per_leaf=4, max_depth=16):

        """

        初始化 BVH



        参数:

            objects: 物体列表，每个物体需要有 bounds 属性

            max_objects_per_leaf: 叶节点最大物体数

            max_depth: 最大深度

        """

        self.objects = objects

        self.max_objects_per_leaf = max_objects_per_leaf

        self.max_depth = max_depth

        self.nodecount = 0



        if objects:

            self.root = self._build(objects, depth=0)

        else:

            self.root = None



    def _compute_bounds(self, objects):

        """计算物体集合的包围盒"""

        if not objects:

            return AABB()

        bounds = AABB(objects[0].bounds.min, objects[0].bounds.max)

        for obj in objects[1:]:

            bounds = bounds.merge(obj.bounds)

        return bounds



    def _build(self, objects, depth):

        """

        递归构建 BVH



        参数:

            objects: 物体列表

            depth: 当前深度

        返回:

            root: BVH 树根节点

        """

        self.nodecount += 1



        # 创建包围盒

        bounds = self._compute_bounds(objects)



        # 终止条件

        if len(objects) <= self.max_objects_per_leaf or depth >= self.max_depth:

            return BVHNode(bounds, objects=objects)



        # SAH 分割

        best_axis, best_pos, best_cost = self._sah_split(objects, bounds)



        if best_cost >= len(objects):

            # 不值得分割

            return BVHNode(bounds, objects=objects)



        # 按分割平面分组

        left_objects = []

        right_objects = []

        centroid = bounds.centroid()



        for obj in objects:

            if obj.bounds.centroid()[best_axis] < best_pos:

                left_objects.append(obj)

            else:

                right_objects.append(obj)



        # 避免空的一边

        if not left_objects or not right_objects:

            return BVHNode(bounds, objects=objects)



        # 递归构建子树

        left_node = self._build(left_objects, depth + 1)

        right_node = self._build(right_objects, depth + 1)



        return BVHNode(bounds, left=left_node, right=right_node)



    def _sah_split(self, objects, bounds):

        """

        SAH 分割算法



        参数:

            objects: 物体列表

            bounds: 当前包围盒

        返回:

            best_axis: 分割轴

            best_pos: 分割位置

            best_cost: 最小成本

        """

        best_cost = float('inf')

        best_axis = 0

        best_pos = 0.0



        n_objects = len(objects)

        surface_area = bounds.surface_area()



        # 尝试每个轴

        for axis in range(3):

            # 按重心排序

            sorted_objects = sorted(objects, key=lambda o: o.bounds.centroid()[axis])



            # 尝试每个可能的分割点

            for i in range(1, n_objects):

                left_count = i

                right_count = n_objects - i



                # 粗略估计左右包围盒

                left_bounds = self._compute_bounds(sorted_objects[:i])

                right_bounds = self._compute_bounds(sorted_objects[i:])



                # SAH 成本

                cost = (left_count * left_bounds.surface_area() +

                       right_count * right_bounds.surface_area()) / surface_area



                if cost < best_cost:

                    best_cost = cost

                    best_axis = axis

                    best_pos = (sorted_objects[i-1].bounds.centroid()[axis] +

                              sorted_objects[i].bounds.centroid()[axis]) / 2.0



        return best_axis, best_pos, best_cost



    def intersect(self, ray):

        """

        光线与 BVH 求交



        参数:

            ray: 光线

        返回:

            hit_object: 最近的命中物体

            hit_info: 命中信息

        """

        if self.root is None:

            return None, None



        return self._intersect_node(self.root, ray)



    def _intersect_node(self, node, ray, t_min=0.001, t_max=np.inf):

        """

        递归与节点求交



        参数:

            node: 当前节点

            ray: 光线

            t_min: 最小 t

            t_max: 最大 t

        返回:

            hit_object: 命中物体

            hit_info: 命中信息

        """

        # 光线与包围盒求交

        hit, t_enter, t_exit = node.bounds.ray_intersect(ray, t_min, t_max)



        if not hit:

            return None, None



        if node.is_leaf():

            # 叶节点：测试所有物体

            return self._intersect_objects(node.objects, ray)



        # 内部节点：递归测试子节点

        # 先测试较近的节点

        left_result = None, None

        right_result = None, None



        if node.left:

            left_result = self._intersect_node(node.left, ray, t_min, t_max)

        if node.right:

            right_result = self._intersect_node(node.right, ray, t_min, t_max)



        # 返回最近的命中

        if left_result[0] is not None and right_result[0] is not None:

            if left_result[1] and right_result[1]:

                return left_result if left_result[1] < right_result[1] else right_result

            return left_result if left_result[1] else right_result



        return left_result if left_result[0] else right_result



    def _intersect_objects(self, objects, ray):

        """

        测试物体列表



        参数:

            objects: 物体列表

            ray: 光线

        返回:

            最近的命中物体

        """

        best_obj = None

        best_t = np.inf

        best_info = None



        for obj in objects:

            if hasattr(obj, 'intersect'):

                hit, t, info = obj.intersect(ray)

                if hit and t < best_t:

                    best_t = t

                    best_obj = obj

                    best_info = info



        return best_obj, best_info



    def print_stats(self):

        """打印 BVH 统计信息"""

        print(f"BVH 统计:")

        print(f"  总节点数: {self.nodecount}")

        print(f"  物体数: {len(self.objects)}")





class DummyObject:

    """用于测试的虚拟物体"""



    def __init__(self, bounds):

        self.bounds = bounds



    def intersect(self, ray):

        """虚拟求交"""

        hit, t, _, _ = self.bounds.ray_intersect(ray)

        return hit, t, {'t': t}





if __name__ == "__main__":

    print("=== BVH 加速结构测试 ===")



    # 创建随机物体

    np.random.seed(42)

    objects = []



    for i in range(100):

        # 随机位置和大小

        center = np.random.uniform(-5, 5, 3)

        size = np.random.uniform(0.1, 0.5, 3)

        min_p = center - size / 2

        max_p = center + size / 2

        bounds = AABB(min_p, max_p)

        obj = DummyObject(bounds)

        objects.append(obj)



    print(f"创建了 {len(objects)} 个物体")



    # 构建 BVH

    bvh = BVH(objects, max_objects_per_leaf=4, max_depth=10)

    bvh.print_stats()



    # 创建测试光线

    class TestRay:

        def __init__(self, origin, direction):

            self.origin = np.array(origin, dtype=float)

            self.direction = np.array(direction, dtype=float)

            norm = np.linalg.norm(self.direction)

            if norm > 0:

                self.direction = self.direction / norm



    # 测试求交

    print("\n=== 光线求交测试 ===")

    ray = TestRay([0, 0, 0], [1, 0.5, 0.2])



    # BVH 求交

    import time

    start = time.time()

    for _ in range(1000):

        obj, info = bvh.intersect(ray)

    bvh_time = time.time() - start



    # 暴力遍历

    start = time.time()

    for _ in range(1000):

        best_t = np.inf

        best_obj = None

        for o in objects:

            hit, t, _ = o.intersect(ray)

            if hit and t < best_t:

                best_t = t

                best_obj = o

    brute_time = time.time() - start



    print(f"BVH 求交 (1000次): {bvh_time*1000:.2f} ms")

    print(f"暴力遍历 (1000次): {brute_time*1000:.2f} ms")

    print(f"加速比: {brute_time/bvh_time:.1f}x")



    if obj:

        print(f"命中物体: 包围盒 {obj.bounds}")



    # 测试不同深度的 BVH

    print("\n=== 不同参数 BVH 性能 ===")

    for max_leaf in [2, 4, 8, 16]:

        bvh_test = BVH(objects, max_objects_per_leaf=max_leaf, max_depth=16)

        start = time.time()

        for _ in range(1000):

            bvh_test.intersect(ray)

        t = time.time() - start

        print(f"max_objects_per_leaf={max_leaf}: {t*1000:.2f} ms, 节点数={bvh_test.nodecount}")



    print("\nBVH 加速结构测试完成!")


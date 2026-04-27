# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / kd_tree

本文件实现 kd_tree 相关的算法功能。
"""

import math
from typing import List, Tuple, Optional, Set


Point = Tuple[float, ...]  # k 维点


class KDNode:
    """
    KD 树节点。

    Attributes:
        point: 节点存储的点
        dim: 分割维度
        left: 左子树（<= 分界点）
        right: 右子树（> 分界点）
        bounding_box: 该子树对应的边界框 (min_point, max_point)
    """

    def __init__(self, point: Point, dim: int,
                 left: Optional['KDNode'] = None,
                 right: Optional['KDNode'] = None):
        self.point = point
        self.dim = dim
        self.left = left
        self.right = right
        self.bbox_min: Optional[Point] = None
        self.bbox_max: Optional[Point] = None

    def __repr__(self):
        return f"KDNode({self.point}, dim={self.dim})"


def _nth_element(points: List[Point], dim: int, k: int) -> Point:
    """
    使用 nth_element（快速选择）找到第 k 小的点（按维度 dim）。

    Python 标准库没有 nth_element，但可以通过排序实现（实际使用时可改用 numpy）。

    Args:
        points: 点列表
        dim: 分割维度
        k: 选择第 k 小（0-indexed）

    Returns:
        第 k 小的点
    """
    sorted_pts = sorted(points, key=lambda p: p[dim])
    return sorted_pts[k]


class KDTree:
    """
    KD 树实现（静态构建版）。

    Attributes:
        k: 空间维度
        root: 根节点
        n: 点数
    """

    def __init__(self, points: List[Point], k: int = 2):
        """
        初始化并构建 KD 树。

        Args:
            points: 点列表
            k: 维度（默认 2）
        """
        self.k = k
        self.n = len(points)
        if self.n == 0:
            self.root = None
        else:
            self.root = self._build(points, depth=0)

    def _build(self, points: List[Point], depth: int) -> Optional[KDNode]:
        """
        递归构建 KD 树。

        Args:
            points: 当前划分范围内的点列表
            depth: 当前深度

        Returns:
            子树根节点
        """
        if not points:
            return None
        dim = depth % self.k
        n = len(points)
        # 取中位数分割（使树尽量平衡）
        median_idx = n // 2
        # 找到中位点（用排序实现）
        sorted_pts = sorted(points, key=lambda p: p[dim])
        median_point = sorted_pts[median_idx]

        left_pts = sorted_pts[:median_idx]
        right_pts = sorted_pts[median_idx + 1:]

        left_child = self._build(left_pts, depth + 1)
        right_child = self._build(right_pts, depth + 1)

        node = KDNode(median_point, dim, left_child, right_child)
        # 计算边界框
        node.bbox_min = self._compute_bbox_min(node)
        node.bbox_max = self._compute_bbox_max(node)
        return node

    def _compute_bbox_min(self, node: KDNode) -> Point:
        """计算子树节点集的最小边界点"""
        all_pts = self._collect_points(node)
        if not all_pts:
            return node.point
        return tuple(min(coord[i] for coord in all_pts) for i in range(self.k))

    def _compute_bbox_max(self, node: KDNode) -> Point:
        """计算子树节点集的最大边界点"""
        all_pts = self._collect_points(node)
        if not all_pts:
            return node.point
        return tuple(max(coord[i] for coord in all_pts) for i in range(self.k))

    def _collect_points(self, node: Optional[KDNode]) -> List[Point]:
        """收集子树所有点"""
        if node is None:
            return []
        return [node.point] + self._collect_points(node.left) + self._collect_points(node.right)

    # ---- 范围查询 ----

    def range_query(self, query_min: Point, query_max: Point) -> List[Point]:
        """
        范围查询：找出所有在 [query_min, query_max] 矩形内的点。

        Args:
            query_min: 查询矩形最小点
            query_max: 查询矩形最大点

        Returns:
            矩形内所有点的列表
        """
        results: List[Point] = []

        def _in_rect(point: Point) -> bool:
            """检查点是否在查询矩形内"""
            return all(query_min[i] <= point[i] <= query_max[i] for i in range(self.k))

        def _intersects(node: Optional[KDNode]) -> bool:
            """检查节点子树边界框是否与查询矩形相交"""
            if node is None:
                return False
            if node.bbox_min is None or node.bbox_max is None:
                return True
            return all(node.bbox_min[i] <= query_max[i] and node.bbox_max[i] >= query_min[i]
                       for i in range(self.k))

        def _search(node: Optional[KDNode]):
            if node is None:
                return
            # 不相交则剪枝
            if not _intersects(node):
                return
            # 检查当前点
            if _in_rect(node.point):
                results.append(node.point)
            # 递归左右子树
            _search(node.left)
            _search(node.right)

        _search(self.root)
        return results

    # ---- 最近邻查询 ----

    def nearest_neighbor(self, query: Point) -> Optional[Tuple[Point, float]]:
        """
        查找最近邻点。

        Args:
            query: 查询点

        Returns:
            (最近点, 距离) 或 None
        """
        best_point: Optional[Point] = None
        best_dist = float('inf')

        def _dist(p1: Point, p2: Point) -> float:
            return math.sqrt(sum((p1[i] - p2[i]) ** 2 for i in range(self.k)))

        def _search(node: Optional[KDNode]):
            nonlocal best_point, best_dist
            if node is None:
                return

            # 计算到当前点的距离
            d = _dist(query, node.point)
            if d < best_dist:
                best_dist = d
                best_point = node.point

            # 确定先搜索哪边（先搜索更可能包含更近点的子树）
            dim = node.dim
            diff = query[dim] - node.point[dim]
            first, second = (node.left, node.right) if diff < 0 else (node.right, node.left)

            _search(first)

            # 如果查询点到分割超平面的距离 < 当前最优，还需搜索另一侧
            if abs(diff) < best_dist:
                _search(second)

        _search(self.root)
        if best_point is None:
            return None
        return (best_point, best_dist)

    def k_nearest_neighbors(self, query: Point, k: int) -> List[Tuple[Point, float]]:
        """
        查找 k 个最近邻点。

        Args:
            query: 查询点
            k: 近邻数量

        Returns:
            [(点, 距离), ...]，按距离升序
        """
        candidates: List[Tuple[float, Point]] = []
        heap = []  # 最大堆（-dist, point）

        def _dist(p1: Point, p2: Point) -> float:
            return math.sqrt(sum((p1[i] - p2[i]) ** 2 for i in range(self.k)))

        def _search(node: Optional[KDNode]):
            if node is None:
                return

            d = _dist(query, node.point)
            if len(heap) < k:
                import heapq
                heapq.heappush(heap, (-d, node.point))
            else:
                if d < -heap[0][0]:
                    import heapq
                    heapq.heapreplace(heap, (-d, node.point))

            dim = node.dim
            diff = query[dim] - node.point[dim]
            first, second = (node.left, node.right) if diff < 0 else (node.right, node.left)

            _search(first)
            # 剪枝：另一子树可能含更近点时才搜索
            if abs(diff) < (-heap[0][0] if heap else float('inf')):
                _search(second)

        _search(self.root)
        import heapq
        sorted_results = sorted([(-d, p) for d, p in heap])
        return [(p, -neg_d) for neg_d, p in sorted_results]


def _bbox_intersects_2d(bbox_min: Point, bbox_max: Point,
                        qmin: Point, qmax: Point) -> bool:
    """检查两个轴对齐矩形是否相交"""
    return all(bbox_min[i] <= qmax[i] and bbox_max[i] >= qmin[i] for i in range(len(bbox_min)))


if __name__ == "__main__":
    import math

    # ----------------- 测试 1: 基础范围查询 -----------------
    points_2d = [
        (0, 0), (1, 2), (3, 1), (4, 4),
        (5, 2), (6, 6), (7, 3), (8, 5),
        (2, 5), (5, 7),
    ]
    kd2 = KDTree(points_2d, k=2)
    qmin = (3, 2)
    qmax = (7, 6)
    result = kd2.range_query(qmin, qmax)
    print(f"[测试1] 2D 范围查询 {qmin}~{qmax}")
    print(f"  找到: {sorted(result)}")
    print(f"  期望: 包含 (3,1),(4,4),(5,2),(6,6),(7,3) 等")

    # ----------------- 测试 2: 最近邻 -----------------
    query = (5, 3)
    nn, d = kd2.nearest_neighbor(query)
    print(f"\n[测试2] 最近邻查询 {query}")
    print(f"  最近邻: {nn}, 距离: {d:.4f}")
    assert nn is not None

    # ----------------- 测试 3: KNN -----------------
    knn = kd2.k_nearest_neighbors((5, 3), k=3)
    print(f"\n[测试3] 3-最近邻查询 (5,3)")
    for pt, dist in knn:
        print(f"  {pt} -> {dist:.4f}")

    # ----------------- 测试 4: 3D KD 树 -----------------
    points_3d = [
        (1, 2, 3), (5, 4, 9), (2, 7, 1), (8, 3, 7),
        (4, 6, 2), (9, 1, 5), (3, 8, 4), (7, 6, 8),
    ]
    kd3 = KDTree(points_3d, k=3)
    nn3, d3 = kd3.nearest_neighbor((4, 5, 4))
    print(f"\n[测试4] 3D 最近邻 (4,5,4) -> {nn3}, dist={d3:.4f}")

    # ----------------- 测试 5: 空树 -----------------
    empty_tree = KDTree([], k=2)
    result5 = empty_tree.range_query((0, 0), (10, 10))
    print(f"\n[测试5] 空 KD 树范围查询 = {result5}")
    assert result5 == []

    # ----------------- 测试 6: 精确边界 -----------------
    # 只包含矩形边上的点
    points_boundary = [(0, 0), (0, 5), (5, 0), (5, 5), (2, 2)]
    kd_b = KDTree(points_boundary, k=2)
    result_b = kd_b.range_query((0, 0), (5, 5))
    print(f"\n[测试6] 精确边界查询: {sorted(result_b)}")
    assert len(result_b) == 5

    # ----------------- 测试 7: 单点树 -----------------
    single = KDTree([(3, 4)], k=2)
    nn_single, d_single = single.nearest_neighbor((3, 4))
    print(f"\n[测试7] 单点最近邻 = {nn_single}, dist={d_single}")
    assert d_single == 0.0

    print("\n所有 KD 树测试通过！")

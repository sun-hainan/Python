# -*- coding: utf-8 -*-
"""
算法实现：11_计算几何 / plane_sweep

本文件实现 plane_sweep 相关的算法功能。
"""

from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
import math


Point = Tuple[float, float]
Segment = Tuple[Point, Point]


def _y_at_x(seg: Segment, x: float) -> float:
    """
    计算线段 seg 在给定 x 坐标处的 y 值。
    假设 seg 不是垂直的（x 在两端点 x 范围内）。

    Args:
        seg: 线段 (p1, p2)
        x: x 坐标

    Returns:
        对应的 y 坐标
    """
    (x1, y1), (x2, y2) = seg
    if abs(x2 - x1) < 1e-12:
        return (y1 + y2) / 2.0
    t = (x - x1) / (x2 - x1)
    return y1 + t * (y2 - y1)


def _segment_intersects(seg1: Segment, seg2: Segment) -> bool:
    """
    判断两条线段是否相交（含端点相交）。

    使用有向面积（叉积）法：
    - p1, p2, q1: 叉积 sign(p2-p1, q1-p1)
    - p1, p2, q2: 叉积 sign(p2-p1, q2-p1)
    - q1, q2, p1: 叉积 sign(q2-q1, p1-q1)
    - q1, q2, p2: 叉积 sign(q2-q1, p2-q1)
    两线段相交当且仅当两个叉积符号相反（不含 0），
    或任一点恰好在另一线段上（叉积为 0）。
    """
    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    p1, p2 = seg1
    q1, q2 = seg2
    d1 = cross(p1, p2, q1)
    d2 = cross(p1, p2, q2)
    d3 = cross(q1, q2, p1)
    d4 = cross(q1, q2, p2)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    # 共线退化情况
    eps = 1e-9
    if abs(d1) < eps and _on_segment(p1, p2, q1):
        return True
    if abs(d2) < eps and _on_segment(p1, p2, q2):
        return True
    if abs(d3) < eps and _on_segment(q1, q2, p1):
        return True
    if abs(d4) < eps and _on_segment(q1, q2, p2):
        return True
    return False


def _on_segment(p1: Point, p2: Point, q: Point) -> bool:
    """检查点 q 是否在线段 p1-p2 上（含端点）。"""
    return (min(p1[0], p2[0]) - 1e-9 <= q[0] <= max(p1[0], p2[0]) + 1e-9 and
            min(p1[1], p2[1]) - 1e-9 <= q[1] <= max(p1[1], p2[1]) + 1e-9)


@dataclass
class Event:
    """
    事件点。

    Attributes:
        x: 事件点的 x 坐标
        y: 事件点的 y 坐标（用于同 x 的排序）
        segs: 该 x 处共线的线段列表
        type: 事件类型 ('left', 'right', 'intersection')
    """
    x: float
    y: float
    segs: List[Segment] = field(default_factory=list)
    type: str = 'left'  # 'left', 'right', 'intersection'


class StatusLineNode:
    """
    状态线中的节点（对应一条线段）。
    按线段在当前扫描线 x 处的 y 坐标排序。

    Attributes:
        seg: 线段
        current_x: 当前扫描线 x 坐标（用于计算 y）
        y_value: 在 current_x 处的 y 坐标
    """
    __slots__ = ('seg', 'current_x', 'y_value', 'seg_id')

    def __init__(self, seg: Segment, current_x: float, seg_id: int):
        self.seg = seg
        self.current_x = current_x
        self.y_value = _y_at_x(seg, current_x)
        self.seg_id = seg_id

    def __lt__(self, other: 'StatusLineNode') -> bool:
        """比较两个节点：按 y 值升序排列（扫描线从上往下看）"""
        if abs(self.y_value - other.y_value) < 1e-9:
            # y 相同时，按线段斜率 tie-break
            (_, y1), (_, y2) = self.seg
            (_, oy1), (_, oy2) = other.seg
            # 斜率：dy/dx，dx 相同时比较 dy
            return y1 < oy1
        return self.y_value < other.y_value


class StatusLine:
    """
    扫描线状态（自组织有序集合）。
    使用列表 + bisect 模拟有序结构（O(n) 插入删除，均摊可接受）。
    实际应用中应使用平衡 BST。

    Attributes:
        items: 有序的 StatusLineNode 列表
        current_x: 当前扫描线 x 坐标
    """
    __slots__ = ('items', 'current_x')

    def __init__(self):
        self.items: List[StatusLineNode] = []
        self.current_x = 0.0

    def _recompute_y(self, node: StatusLineNode):
        """重新计算节点在线 current_x 处的 y 值"""
        node.y_value = _y_at_x(node.seg, self.current_x)

    def _reorder(self):
        """重新排序（当线段顺序变化时调用）"""
        for item in self.items:
            self._recompute_y(item)
        self.items.sort(key=lambda n: n.y_value)

    def insert(self, seg: Segment, seg_id: int) -> StatusLineNode:
        """插入一条线段"""
        node = StatusLineNode(seg, self.current_x, seg_id)
        # bisect 插入
        import bisect
        bisect.insort(self.items, node)
        return node

    def remove(self, seg_id: int):
        """删除一条线段（通过 seg_id）"""
        self.items = [n for n in self.items if n.seg_id != seg_id]

    def find_above(self, seg_id: int) -> Optional[StatusLineNode]:
        """找 seg_id 线段上方相邻的线段"""
        idx = next((i for i, n in enumerate(self.items) if n.seg_id == seg_id), -1)
        if idx > 0:
            return self.items[idx - 1]
        return None

    def find_below(self, seg_id: int) -> Optional[StatusLineNode]:
        """找 seg_id 线段下方相邻的线段"""
        idx = next((i for i, n in enumerate(self.items) if n.seg_id == seg_id), -1)
        if 0 <= idx < len(self.items) - 1:
            return self.items[idx + 1]
        return None

    def set_x(self, x: float):
        """移动扫描线到新 x，更新所有 y 值并重排序"""
        self.current_x = x
        self._reorder()

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


def _compute_intersection_point(seg1: Segment, seg2: Segment) -> Optional[Point]:
    """
    计算两条线段的交点（假设它们相交）。

    使用参数方程求解：
    seg1: p + t*r (t∈[0,1])，r = p2-p1
    seg2: q + u*s (u∈[0,1])，s = q2-q1
    交点: p + t*r = q + u*s
    => t*r - u*s = q - p
    用克莱姆法则求解 2x2 方程。
    """
    p1x, p1y = seg1[0]
    p2x, p2y = seg1[1]
    q1x, q1y = seg2[0]
    q2x, q2y = seg2[1]

    r_x = p2x - p1x
    r_y = p2y - p1y
    s_x = q2x - q1x
    s_y = q2y - q1y

    denom = r_x * s_y - r_y * s_x
    if abs(denom) < 1e-12:
        return None  # 平行或重合

    qp_x = q1x - p1x
    qp_y = q1y - p1y

    t = (qp_x * s_y - qp_y * s_x) / denom
    # u = (qp_x * r_y - qp_y * r_x) / denom  # 可用于验证

    ix = p1x + t * r_x
    iy = p1y + t * r_y
    return (ix, iy)


def plane_sweep_intersections(segments: List[Segment]) -> List[Tuple[Segment, Segment, Point]]:
    """
    平面扫描算法：找出所有线段交点。

    Args:
        segments: 线段列表

    Returns:
        交点列表 [(seg1, seg2, intersection_point), ...]
    """
    n = len(segments)
    if n < 2:
        return []

    # 构建事件点列表
    # 每个线段有两个端点事件
    events: List[Event] = []
    for i, seg in enumerate(segments):
        (x1, y1), (x2, y2) = seg
        if x1 < x2 or (abs(x1 - x2) < 1e-9 and y1 < y2):
            left, right = seg, seg
        else:
            left, right = seg, seg

        # 左端点（x 较小）
        ev_left = Event(min(x1, x2), max(y1, y2) if min(x1, x2) == x1 else min(y1, y2),
                        segs=[seg], type='left')
        ev_right = Event(max(x1, x2), min(y1, y2) if max(x1, x2) == x2 else max(y1, y2),
                         segs=[seg], type='right')

        # 精确处理：按实际 y 排序
        ev_left.x = min(x1, x2)
        ev_left.y = y1 if x1 <= x2 else y2
        ev_right.x = max(x1, x2)
        ev_right.y = y2 if x1 <= x2 else y1

        events.append(ev_left)
        events.append(ev_right)

    # 按 x 优先、y 次优先排序
    events.sort(key=lambda e: (e.x, e.y))

    # 去除重复事件（同一 x 的端点）
    merged_events: List[Event] = []
    i = 0
    while i < len(events):
        cur_x = events[i].x
        cur_events = [events[i]]
        j = i + 1
        while j < len(events) and abs(events[j].x - cur_x) < 1e-9:
            cur_events.append(events[j])
            j += 1
        # 合并
        merged = Event(cur_x, cur_events[0].y, segs=cur_events[0].segs, type=cur_events[0].type)
        if len(cur_events) > 1:
            merged.segs = [e.segs[0] for e in cur_events]
            merged.type = 'left'  # 多条线同 x 时，视为左端点
        merged_events.append(merged)
        i = j

    status = StatusLine()
    intersections: Set[Tuple[int, int, float, float]] = set()
    seg_to_id = {seg: i for i, seg in enumerate(segments)}

    current_x = float('-inf')

    for ev in merged_events:
        # 扫描线移动到新 x
        if abs(ev.x - current_x) > 1e-9:
            current_x = ev.x
            status.set_x(current_x)

        for seg in ev.segs:
            seg_id = seg_to_id.get(seg, -1)
            if seg_id == -1:
                continue

            # 插入新线段（对于 'left' 事件）
            status.insert(seg, seg_id)

            # 检查与上下相邻线段是否相交
            above = status.find_above(seg_id)
            below = status.find_below(seg_id)

            if above is not None and _segment_intersects(seg, above.seg):
                pt = _compute_intersection_point(seg, above.seg)
                if pt:
                    key = (min(seg_id, above.seg_id), max(seg_id, above.seg_id),
                           round(pt[0], 9), round(pt[1], 9))
                    intersections.add(key)

            if below is not None and _segment_intersects(seg, below.seg):
                pt = _compute_intersection_point(seg, below.seg)
                if pt:
                    key = (min(seg_id, below.seg_id), max(seg_id, below.seg_id),
                           round(pt[0], 9), round(pt[1], 9))
                    intersections.add(key)

        # 'right' 事件：从状态线删除
        for seg in ev.segs:
            seg_id = seg_to_id.get(seg, -1)
            if seg_id != -1:
                # 左右相邻线段在删除后可能需要检查
                above = status.find_above(seg_id)
                below = status.find_below(seg_id)
                if above and below and _segment_intersects(above.seg, below.seg):
                    pt = _compute_intersection_point(above.seg, below.seg)
                    if pt:
                        key = (min(above.seg_id, below.seg_id), max(above.seg_id, below.seg_id),
                               round(pt[0], 9), round(pt[1], 9))
                        intersections.add(key)
                status.remove(seg_id)

    # 转换回 (seg1, seg2, point) 格式
    results: List[Tuple[Segment, Segment, Point]] = []
    for i1, i2, ix, iy in intersections:
        results.append((segments[i1], segments[i2], (ix, iy)))
    return results


if __name__ == "__main__":
    import random

    # ----------------- 测试 1: 简单网格 -----------------
    # 3 水平 x 3 垂直 = 9 个交点
    segs_grid = []
    for i in range(3):
        segs_grid.append(((0, i), (3, i)))  # 水平
        segs_grid.append(((i, 0), (i, 3)))  # 垂直
    intersections1 = plane_sweep_intersections(segs_grid)
    print(f"[测试1] 3x3 网格: {len(intersections1)} 个交点 (期望: 9)")
    assert len(intersections1) == 9, f"期望 9，实际 {len(intersections1)}"

    # ----------------- 测试 2: 随机线段（少量）-----------------
    random.seed(42)
    segs_random = []
    for _ in range(20):
        x1, y1 = random.uniform(0, 10), random.uniform(0, 10)
        x2, y2 = random.uniform(0, 10), random.uniform(0, 10)
        if abs(x1 - x2) < 0.5:  # 保证不接近垂直
            x2 = x1 + 0.6
        segs_random.append(((x1, y1), (x2, y2)))
    intersections2 = plane_sweep_intersections(segs_random)
    print(f"\n[测试2] 20 条随机线段: {len(intersections2)} 个交点")

    # ----------------- 测试 3: 无交点 -----------------
    segs_parallel = [
        ((0, 0), (1, 0)),
        ((0, 1), (1, 1)),
        ((0, 2), (1, 2)),
        ((0, 3), (1, 3)),
    ]
    intersections3 = plane_sweep_intersections(segs_parallel)
    print(f"\n[测试3] 平行线段: {len(intersections3)} 个交点 (期望: 0)")
    assert len(intersections3) == 0

    # ----------------- 测试 4: 全部相交（星形）-----------------
    n_rays = 10
    segs_star = []
    cx, cy = 5.0, 5.0
    for i in range(n_rays):
        angle = 2 * math.pi * i / n_rays
        x, y = cx + math.cos(angle), cy + math.sin(angle)
        segs_star.append(((cx, cy), (x, y)))
    intersections4 = plane_sweep_intersections(segs_star)
    print(f"\n[测试4] {n_rays}-射线星形: {len(intersections4)} 个交点 (期望: C({n_rays},2))")
    print(f"  C({n_rays},2) = {n_rays*(n_rays-1)//2}")

    # ----------------- 测试 5: 三角形（3 条边两两相交）-----------------
    segs_tri = [
        ((0, 0), (5, 0)),
        ((5, 0), (2.5, 5)),
        ((2.5, 5), (0, 0)),
    ]
    intersections5 = plane_sweep_intersections(segs_tri)
    print(f"\n[测试5] 三角形（无边相交）: {len(intersections5)} 个交点 (期望: 0)")
    assert len(intersections5) == 0

    # ----------------- 测试 6: 交叉线段 -----------------
    segs_cross = [
        ((0, 0), (10, 10)),
        ((0, 10), (10, 0)),
        ((5, 2), (5, 8)),
        ((2, 5), (8, 5)),
    ]
    intersections6 = plane_sweep_intersections(segs_cross)
    print(f"\n[测试6] 交叉线段: {len(intersections6)} 个交点 (期望: 4)")
    print(f"  交点: {[pt for _, _, pt in intersections6]}")

    # ----------------- 测试 7: 空输入 -----------------
    print(f"\n[测试7] 空输入: {plane_sweep_intersections([])}")

    # ----------------- 测试 8: 单条线段 -----------------
    print(f"[测试8] 单条线段: {plane_sweep_intersections([((0,0),(1,1))])}")

    print("\n所有平面扫描测试通过！")

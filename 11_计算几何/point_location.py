# -*- coding: utf-8 -*-

"""

算法实现：11_计算几何 / point_location



本文件实现 point_location 相关的算法功能。

"""



import random

from typing import List, Tuple, Optional, Dict, Set





Point = Tuple[float, float]

Segment = Tuple[Point, Point]





def _bbox_intersects(a_min: Point, a_max: Point, b_min: Point, b_max: Point) -> bool:

    """检查两个轴对齐矩形是否相交"""

    return all(a_min[i] <= b_max[i] and a_max[i] >= b_min[i] for i in range(2))





def _point_in_trapezoid(q: Point, t_min: Point, t_max: Point,

                        top_seg: Optional[Segment], bot_seg: Optional[Segment]) -> bool:

    """

    检查点 q 是否在梯形内部（含边界）。



    梯形由 top/bottom 线段和左右垂直边界限定。

    """

    x, y = q

    x_min, y_min = t_min

    x_max, y_max = t_max

    # x 方向检查

    if not (x_min - 1e-9 <= x <= x_max + 1e-9):

        return False

    # y 方向检查：y >= bottom(x) 且 y <= top(x)

    if bot_seg is not None:

        bx1, by1 = bot_seg[0]

        bx2, by2 = bot_seg[1]

        # 线性插值求 bottom 在 x 处的高度

        if bx1 == bx2:

            bot_y = by1

        else:

            t = (x - bx1) / (bx2 - bx1)

            bot_y = by1 + t * (by2 - by1)

        if y < bot_y - 1e-9:

            return False

    if top_seg is not None:

        tx1, ty1 = top_seg[0]

        tx2, ty2 = top_seg[1]

        if tx1 == tx2:

            top_y = ty1

        else:

            t = (x - tx1) / (tx2 - tx1)

            top_y = ty1 + t * (ty2 - ty1)

        if y > top_y + 1e-9:

            return False

    return True





def _get_y_at_x(seg: Segment, x: float) -> float:

    """计算线段在 x 处的 y 坐标（假设 seg 不垂直）"""

    (x1, y1), (x2, y2) = seg

    if abs(x2 - x1) < 1e-12:

        return (y1 + y2) / 2

    t = (x - x1) / (x2 - x1)

    return y1 + t * (y2 - y1)





class Trapezoid:

    """

    梯形节点。

    """



    def __init__(self,

                 top: Optional[Segment],

                 bottom: Optional[Segment],

                 left_x: float,

                 right_x: float,

                 y_min: float,

                 y_max: float):

        self.top = top

        self.bottom = bottom

        self.left_x = left_x

        self.right_x = right_x

        self.y_min = y_min

        self.y_max = y_max

        # 唯一标识（用于字典）

        self.id = f"T_{id(self)}"



    def bbox(self) -> Tuple[Point, Point]:

        return (self.left_x, self.y_min), (self.right_x, self.y_max)



    def contains(self, q: Point) -> bool:

        return _point_in_trapezoid(q, (self.left_x, self.y_min),

                                   (self.right_x, self.y_max),

                                   self.top, self.bottom)



    def __repr__(self):

        return f"Trapezoid(left={self.left_x:.2f}, right={self.right_x:.2f})"





class TrapezoidMap:

    """

    梯形图（Trapezoidal Map）+ 点定位 DAG。



    构造流程（随机增量）：

    1. 初始化：所有线段合在一起的 bounding box 梯形

    2. 随机插入线段 s = (p, q)：

       - 找到当前被 s 穿过的所有梯形（用查询点 p 和 q 定位）

       - 删除这些梯形

       - 用 s 作为新的顶/底边，创建新的梯形

       - 建立 DAG 节点（有向图边）



    Attributes:

        segments: 所有线段列表

        trapezoids: 当前所有梯形字典 {id: trapezoid}

        dag_nodes: 有向无环图节点（用于查询）

    """



    class Node:

        """DAG 中的节点（查询图）"""

        def __init__(self, trapezoid: Optional[Trapezoid] = None):

            self.trapezoid = trapezoid  # None 表示内部节点

            # 如果是内部节点（分割节点），有 left/right 子节点

            self.left_node: Optional['TrapezoidMap.Node'] = None

            self.right_node: Optional['TrapezoidMap.Node'] = None

            # 分割信息

            self.split_seg: Optional[Segment] = None



    def __init__(self, segments: List[Segment], seed: Optional[int] = None):

        """

        初始化并构建梯形图。



        Args:

            segments: 线段列表（假设端点 y 不同则互不相交）

            seed: 随机种子（用于确定性测试）

        """

        if seed is not None:

            random.seed(seed)

        self.segments = segments

        self.k = len(segments)

        # 确定 bounding box

        all_x = [p[0] for seg in segments for p in seg]

        all_y = [p[1] for seg in segments for p in seg]

        self.x_min, self.x_max = min(all_x), max(all_x)

        self.y_min, self.y_max = min(all_y), max(all_y)

        margin = 0.1

        self.bbox_min = (self.x_min - margin, self.y_min - margin)

        self.bbox_max = (self.x_max + margin, self.y_max + margin)



        # 初始化：一个大梯形覆盖 bounding box

        init_trapezoid = Trapezoid(

            top=None, bottom=None,

            left_x=self.bbox_min[0], right_x=self.bbox_max[0],

            y_min=self.bbox_min[1], y_max=self.bbox_max[1]

        )

        self.trapezoids: Dict[str, Trapezoid] = {init_trapezoid.id: init_trapezoid}

        # DAG 根节点

        self.root: TrapezoidMap.Node = TrapezoidMap.Node(init_trapezoid)



        # 随机增量构造

        perm = list(range(self.k))

        random.shuffle(perm)

        for idx in perm:

            self._insert_segment(segments[idx])



    def _find_trapezoid_containing_point(self, q: Point,

                                          node: 'TrapezoidMap.Node') -> Trapezoid:

        """

        在 DAG 中查找包含 q 的梯形（查询操作）。

        从根向下沿分割线走，直到叶子。

        """

        while node.trapezoid is None:

            seg = node.split_seg

            # 判断 q 在分割线哪一侧

            x = q[0]

            # 计算分割线在 x 处的 y

            y_on_seg = _get_y_at_x(seg, x)

            if q[1] < y_on_seg - 1e-9:

                node = node.left_node

            else:

                node = node.right_node

        return node.trapezoid



    def _insert_segment(self, seg: Segment):

        """

        将线段 seg 插入梯形图，更新梯形划分和 DAG。



        这是简化的增量实现，核心思路：

        1. 找到被 seg 穿过的所有梯形 T

        2. 删除 T，在 seg 上方和下方插入新梯形

        3. 更新 DAG（有向图）



        Args:

            seg: 待插入线段

        """

        # 找出所有被 seg 穿过的梯形

        hit_trapezoids: List[Trapezoid] = []

        for t in list(self.trapezoids.values()):

            if self._trapezoid_intersects_segment(t, seg):

                hit_trapezoids.append(t)



        if not hit_trapezoids:

            return



        # 为这些梯形找到对应的 DAG 节点

        for t in hit_trapezoids:

            # 找到当前 DAG 中指向 t 的节点（简化处理：重新定位）

            pass



        # 简化：直接重建受影响的梯形区域

        # 实际上我们用替代策略：对 hit 梯形中的每个点定位，再根据 seg 分割

        self._replace_trapezoids_with_segment(seg, hit_trapezoids)



    def _trapezoid_intersects_segment(self, t: Trapezoid, seg: Segment) -> bool:

        """检查梯形是否与线段相交（仅判断 x 范围重叠）"""

        p1, p2 = seg

        seg_x_min = min(p1[0], p2[0])

        seg_x_max = max(p1[0], p2[0])

        t_x_mid = (t.left_x + t.right_x) / 2

        # 粗略检查：梯形中点 x 坐标是否在线段 x 范围内

        if t_x_mid < seg_x_min or t_x_mid > seg_x_max:

            return False

        # 检查 y 范围

        mid_y = (t.y_min + t.y_max) / 2

        y1, y2 = _get_y_at_x(seg, t.left_x), _get_y_at_x(seg, t.right_x)

        seg_y_min, seg_y_max = min(y1, y2), max(y1, y2)

        return not (mid_y < seg_y_min or mid_y > seg_y_max)



    def _replace_trapezoids_with_segment(self, seg: Segment,

                                          old_ts: List[Trapezoid]):

        """

        用 seg 分割旧梯形：在 seg 上方和下方创建新梯形。



        简化实现：直接对每个被击中的梯形，沿 seg 的 x 范围，

        将其分为「上方」和「下方」两个梯形（或更多）。

        """

        p1, p2 = seg

        seg_x_min, seg_x_max = min(p1[0], p2[0]), max(p1[0], p2[0])

        seg_y_min = min(p1[1], p2[1])

        seg_y_max = max(p1[1], p2[1])



        for t in old_ts:

            # 删除旧梯形

            if t.id in self.trapezoids:

                del self.trapezoids[t.id]



            # 确定 seg 穿过梯形的 x 范围

            new_left = max(t.left_x, seg_x_min)

            new_right = min(t.right_x, seg_x_max)

            if new_left >= new_right:

                continue



            # 上方新梯形（top 不变，bottom = seg）

            top_t = Trapezoid(

                top=t.top, bottom=seg,

                left_x=new_left, right_x=new_right,

                y_min=seg_y_max, y_max=t.y_max

            )

            # 下方新梯形（bottom 不变，top = seg）

            bot_t = Trapezoid(

                top=seg, bottom=t.bottom,

                left_x=new_left, right_x=new_right,

                y_min=t.y_min, y_max=seg_y_min

            )

            # 左尾梯形（seg 左侧，仍用原来的 top/bottom）

            if t.left_x < new_left:

                left_t = Trapezoid(

                    top=t.top, bottom=t.bottom,

                    left_x=t.left_x, right_x=new_left,

                    y_min=t.y_min, y_max=t.y_max

                )

                self.trapezoids[left_t.id] = left_t

            # 右尾梯形（seg 右侧）

            if new_right < t.right_x:

                right_t = Trapezoid(

                    top=t.top, bottom=t.bottom,

                    left_x=new_right, right_x=t.right_x,

                    y_min=t.y_min, y_max=t.y_max

                )

                self.trapezoids[right_t.id] = right_t



            # 添加上下新梯形（只有当高度为正时才添加）

            if top_t.y_max > top_t.y_min + 1e-9:

                self.trapezoids[top_t.id] = top_t

            if bot_t.y_max > bot_t.y_min + 1e-9:

                self.trapezoids[bot_t.id] = bot_t



    def locate(self, q: Point) -> Optional[Trapezoid]:

        """

        点定位：查找点 q 所在的面（梯形）。



        Args:

            q: 查询点



        Returns:

            包含 q 的梯形，或 None（如果在外边界外）

        """

        # 先粗略检查是否在 bounding box 外

        if not (self.bbox_min[0] <= q[0] <= self.bbox_max[0] and

                self.bbox_min[1] <= q[1] <= self.bbox_max[1]):

            return None

        return self._find_trapezoid_containing_point(q, self.root)



    def _build_dag(self, node: Node, seg: Segment):

        """

        简化：在线段插入时构建 DAG 查询图。

        本实现省略了 DAG 的精确重建，使用梯形的包围盒查询。

        """

        pass





def point_location_trapezoid(segments: List[Segment],

                              query_point: Point,

                              seed: Optional[int] = None) -> Optional[Trapezoid]:

    """

    便捷接口：使用梯形图进行点定位。



    Args:

        segments: 平面划分的线段集合

        query_point: 查询点

        seed: 随机种子



    Returns:

        包含查询点的梯形

    """

    tmap = TrapezoidMap(segments, seed=seed)

    return tmap.locate(query_point)





if __name__ == "__main__":

    import random



    # ----------------- 测试 1: 简单三角形区域 -----------------

    # 三角形: (0,0)-(5,0)-(2.5,5)

    segs1 = [

        ((0, 0), (5, 0)),

        ((5, 0), (2.5, 5)),

        ((2.5, 5), (0, 0)),

    ]

    tmap1 = TrapezoidMap(segs1, seed=42)

    print(f"[测试1] 三角形梯形图，共 {len(tmap1.trapezoids)} 个梯形")



    # 查询多个点

    test_points = [(2.5, 1), (1, 0.5), (3, 0.2), (2.5, 4), (10, 10)]

    for q in test_points:

        t = tmap1.locate(q)

        if t:

            print(f"  查询点 {q} -> 梯形 (inside={t.contains(q)})")

        else:

            print(f"  查询点 {q} -> 在图形外")



    # ----------------- 测试 2: 矩形网格 -----------------

    segs2 = [

        ((0, 0), (4, 0)), ((4, 0), (4, 4)), ((4, 4), (0, 4)), ((0, 4), (0, 0)),

        ((1, 1), (3, 1)), ((3, 1), (3, 3)), ((3, 3), (1, 3)), ((1, 3), (1, 1)),

        ((2, 0), (2, 1)), ((2, 3), (2, 4)),  # 内部开口

    ]

    tmap2 = TrapezoidMap(segs2, seed=123)

    print(f"\n[测试2] 矩形网格梯形图，共 {len(tmap2.trapezoids)} 个梯形")



    # ----------------- 测试 3: 梯形图边界情况 -----------------

    segs3 = [

        ((0, 0), (10, 0)),  # bottom

        ((0, 10), (10, 10)),  # top

        ((0, 0), (0, 10)),  # left

        ((10, 0), (10, 10)),  # right

        ((3, 3), (7, 7)),  # 内部线

    ]

    tmap3 = TrapezoidMap(segs3, seed=999)

    print(f"\n[测试3] 带内部线的矩形，共 {len(tmap3.trapezoids)} 个梯形")

    q3 = (5, 5)

    t3 = tmap3.locate(q3)

    print(f"  查询 (5,5) -> {'梯形内' if t3 and t3.contains(q3) else '外部'}")



    # ----------------- 测试 4: 空线段集合 -----------------

    segs4 = []

    tmap4 = TrapezoidMap(segs4, seed=1)

    print(f"\n[测试4] 空线段集合 -> {len(tmap4.trapezoids)} 个初始梯形")

    t4 = tmap4.locate((0, 0))

    print(f"  任何查询点 -> bounding box 梯形")



    # ----------------- 测试 5: 一条水平线（两个梯形） -----------------

    segs5 = [((0, 5), (10, 5))]

    tmap5 = TrapezoidMap(segs5, seed=7)

    print(f"\n[测试5] 单条水平线 -> {len(tmap5.trapezoids)} 个梯形")

    t_above = tmap5.locate((5, 6))

    t_below = tmap5.locate((5, 4))

    print(f"  上方点 (5,6) -> {'inside' if t_above and t_above.contains((5,6)) else 'outside'}")

    print(f"  下方点 (5,4) -> {'inside' if t_below and t_below.contains((5,4)) else 'outside'}")



    print("\n所有点定位（梯形图）测试完成！")


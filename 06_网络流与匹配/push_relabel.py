# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / push_relabel



本文件实现 push_relabel 相关的算法功能。

"""



from collections import deque

from typing import List, Dict, Tuple, Optional





class PushRelabel:

    """

    Push-Relabel 最高标号算法实现。



    Attributes:

        n: 顶点数量（不含超源超汇）

        capacity: 邻接矩阵形式的容量，边 (i, j) 的容量

        flow: 当前流值

        height: 每个顶点的高度标号

        excess: 每个顶点的超额流（流入 - 流出）

        count: 顶点激活计数（用于 gap heuristic）

    """



    def __init__(self, n: int, source: int, sink: int):

        """

        初始化 Push-Relabel 算法实例。



        Args:

            n: 图中顶点数（不含超源超汇）

            source: 源点编号

            sink: 汇点编号

        """

        self.n = n

        self.source = source

        self.sink = sink

        # 扩展到包含一个工作顶点的索引范围

        self.N = n + 2

        self.capacity: List[List[float]] = [[0.0] * self.N for _ in range(self.N)]

        self.flow: List[List[float]] = [[0.0] * self.N for _ in range(self.N)]

        self.height: List[int] = [0] * self.N

        self.excess: List[float] = [0.0] * self.N

        # 用于 gap heuristic: 高度为 h 的顶点个数

        self.height_count: List[int] = [0] * self.N



    def add_edge(self, u: int, v: int, cap: float):

        """

        添加一条有向边及其容量。



        Args:

            u: 起点

            v: 终点

            cap: 容量（必须非负）

        """

        # 正向边容量

        self.capacity[u][v] += cap



    def _initialize_preflow(self):

        """

        初始化预流（Preflow）：

        - 将源点高度设为 N（高于所有其他顶点）

        - 从源点向所有邻接顶点推送尽可能多的 flow

        这将产生超额流的顶点（active vertices）。

        """

        # 源点高度 = 顶点数（最高）

        self.height[self.source] = self.N

        # 遍历所有从源点出发的边，推送全部容量

        for v in range(self.N):

            if self.capacity[self.source][v] > 0:

                # flow = 推送的量

                pushed = self.capacity[self.source][v]

                self.flow[self.source][v] = pushed

                self.flow[v][self.source] = -pushed

                self.excess[v] += pushed

                self.excess[self.source] -= pushed

        # 初始化高度计数

        self.height_count[0] = self.N - 1

        self.height_count[self.N] = 1



    def _push(self, u: int, v: int) -> bool:

        """

        从 u 向 v 推送 flow（需要满足推送条件）。



        推送条件:

            1. capacity(u, v) - flow(u, v) > 0（还有剩余容量）

            2. height[u] > height[v]（高度差驱动）



        Args:

            u: 源顶点（必须有 excess > 0）

            v: 目标顶点



        Returns:

            True 如果成功推送，False 否则

        """

        # 计算剩余容量

        residual = self.capacity[u][v] - self.flow[u][v]

        if residual <= 0 or self.height[u] <= self.height[v]:

            return False

        # 实际可推送的量 = min(excess[u], residual)

        amount = min(self.excess[u], residual)

        self.flow[u][v] += amount

        self.flow[v][u] -= amount

        self.excess[u] -= amount

        self.excess[v] += amount

        return True



    def _relabel(self, u: int):

        """

        对顶点 u 进行重标记（relabel）。



        当 u 有 excess > 0 但无法推送到任何邻接顶点时调用。

        将 u 的高度设为所有可推送邻接顶点中的最小高度 + 1。



        Args:

            u: 待重标记的顶点

        """

        old_height = self.height[u]

        # 找到所有允许推送的邻接顶点（还有剩余容量且高度小于当前最小）

        min_height = float('inf')

        for v in range(self.N):

            residual = self.capacity[u][v] - self.flow[u][v]

            if residual > 0 and self.height[v] < min_height:

                min_height = self.height[v]

        # 更新高度

        self.height_count[old_height] -= 1

        self.height[u] = min_height + 1

        self.height_count[self.height[u]] += 1

        # Gap heuristic: 如果某个高度 h 的计数变为 0，且没有更高顶点，则可切断所有高度 > h 的顶点

        if self.height_count[old_height] == 0 and old_height < self.N:

            self._discharge_gap(old_height)



    def _discharge_gap(self, h: int):

        """

        Gap heuristic：当某个高度层没有顶点时，所有高度 > h 的顶点

        的高度可以设为 N（或更高），使其不再参与后续操作。



        Args:

            h: 出现空缺的高度层

        """

        for v in range(self.N):

            if h < self.height[v] < self.N:

                self.height_count[self.height[v]] -= 1

                self.height[v] = self.N

                self.height_count[self.N] += 1



    def _discharge(self, u: int):

        """

        排出（discharge）顶点 u 的所有 excess flow。

        反复尝试推送，然后重标记，直到 u 的 excess 为 0。



        Args:

            u: 待排出的顶点

        """

        while self.excess[u] > 1e-9:

            # 尝试从每个邻接顶点推送（使用 current_edge 优化）

            pushed = False

            for v in range(self.N):

                if self._push(u, v):

                    pushed = True

                    if self.excess[u] < 1e-9:

                        break

            if not pushed:

                # 无法推送，进行重标记

                self._relabel(u)



    def _select_active_vertex(self) -> Optional[int]:

        """

        最高标号选择：从所有活跃顶点中选择高度最高的。

        活跃顶点：excess > 0 且不是 source 或 sink。



        Returns:

            高度最高的活跃顶点编号，如果没有则返回 None

        """

        max_height = -1

        result = -1

        for v in range(self.N):

            if v == self.source or v == self.sink:

                continue

            if self.excess[v] > 1e-9 and self.height[v] > max_height:

                max_height = self.height[v]

                result = v

        return result if max_height > 0 else None



    def max_flow(self) -> float:

        """

        执行 Push-Relabel 最高标号算法，计算最大流。



        Returns:

            从 source 到 sink 的最大流值

        """

        self._initialize_preflow()



        # 使用优先队列（最大堆）选择最高标号活跃顶点

        # 也可以用普通队列得到 FIFO 版本

        active_queue = []

        # 初始活跃顶点集合

        for v in range(self.N):

            if v != self.source and v != self.sink and self.excess[v] > 1e-9:

                active_queue.append(v)



        while active_queue:

            # 选择最高标号顶点

            active_queue.sort(key=lambda x: self.height[x], reverse=True)

            u = active_queue.pop(0)

            if self.excess[u] < 1e-9:

                continue

            old_height = self.height[u]

            self._discharge(u)

            # 如果 relabel 后高度增加了，重排队列

            if self.height[u] > old_height and self.excess[u] > 1e-9:

                active_queue.append(u)



        return self.excess[self.sink]



    def get_flow_value(self) -> float:

        """返回当前流的 flow 值（即超汇的 excess）。"""

        return self.excess[self.sink]





def build_network(n: int, edges: List[Tuple[int, int, float]], source: int, sink: int) -> PushRelabel:

    """

    从边列表构建网络流实例。



    Args:

        n: 顶点数

        edges: 边列表，每项为 (u, v, capacity)

        source: 源点

        sink: 汇点



    Returns:

        配置好的 PushRelabel 实例

    """

    pr = PushRelabel(n, source, sink)

    for u, v, cap in edges:

        pr.add_edge(u, v, cap)

    return pr





if __name__ == "__main__":

    import sys



    # ----------------- 测试 1: 经典示例 -----------------

    #    s --(10)--> a --(10)--> t

    #    s --(1)-->  b --(10)--> t

    #    a --(2)-->  b

    n1 = 4

    edges1 = [

        (0, 1, 10), (0, 2, 1),

        (1, 3, 10), (2, 3, 1),

        (1, 2, 2),

    ]

    pr1 = build_network(n1, edges1, source=0, sink=3)

    flow1 = pr1.max_flow()

    print(f"[测试1] 经典网络最大流 = {flow1} (期望: 11)")

    assert flow1 == 11.0, f"期望 11，实际 {flow1}"



    # ----------------- 测试 2: 二分图匹配 -----------------

    #    s --(1)--> 左顶点 --(1)--> 右顶点 --(1)--> t

    n2 = 5

    edges2 = [

        (0, 1, 1), (0, 2, 1), (0, 3, 1),

        (1, 4, 1), (2, 4, 1),

        (3, 4, 1),

    ]

    pr2 = build_network(n2, edges2, source=0, sink=4)

    flow2 = pr2.max_flow()

    print(f"[测试2] 二分图匹配最大流 = {flow2} (期望: 3)")

    assert flow2 == 3.0, f"期望 3，实际 {flow2}"



    # ----------------- 测试 3: 单边 -----------------

    n3 = 2

    edges3 = [(0, 1, 5)]

    pr3 = build_network(n3, edges3, source=0, sink=1)

    flow3 = pr3.max_flow()

    print(f"[测试3] 单边网络 = {flow3} (期望: 5)")

    assert flow3 == 5.0, f"期望 5，实际 {flow3}"



    # ----------------- 测试 4: 无连通 -----------------

    n4 = 3

    edges4 = [(0, 1, 10)]

    pr4 = build_network(n4, edges4, source=0, sink=2)

    flow4 = pr4.max_flow()

    print(f"[测试4] 无连通路径 = {flow4} (期望: 0)")

    assert flow4 == 0.0, f"期望 0，实际 {flow4}"



    # ----------------- 测试 5: 较大网络 -----------------

    #      0

    #    / | \

    #   1  2  3

    #   |  |  |

    #   4--5--6

    #    \ | /

    #      7

    n5 = 8

    edges5 = [

        (0, 1, 5), (0, 2, 7), (0, 3, 3),

        (1, 4, 3), (2, 5, 4), (3, 6, 2),

        (4, 7, 6), (5, 7, 5), (6, 7, 4),

        (4, 5, 2), (5, 6, 1),

    ]

    pr5 = build_network(n5, edges5, source=0, sink=7)

    flow5 = pr5.max_flow()

    print(f"[测试5] 较大网络最大流 = {flow5} (期望: 14)")

    assert flow5 == 14.0, f"期望 14，实际 {flow5}"



    print("\n所有 Push-Relabel 测试通过！")


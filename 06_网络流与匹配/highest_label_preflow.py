# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / highest_label_preflow



本文件实现 highest_label_preflow 相关的算法功能。

"""



from collections import deque





class HighestLabelPreflowPush:

    """最高标号预流推进算法"""

    

    def __init__(self, n):

        self.n = n

        self.graph = defaultdict(list)

        self.capacity = {}

        self.flow = {}

        self.height = [0] * n  # 高度（距离函数）

        self.excess = [0] * n  # 超额流量

    

    def add_edge(self, u, v, cap):

        """添加有向边"""

        self.graph[u].append(v)

        self.graph[v].append(u)

        self.capacity[(u, v)] = cap

        self.capacity[(v, u)] = 0

        self.flow[(u, v)] = 0

        self.flow[(v, u)] = 0

    

    def initialize_preflow(self, source):

        """初始化预流：将所有从源出发的边填满"""

        self.height[source] = self.n  # 源高度设为 n

        

        for v in self.graph[source]:

            cap = self.capacity.get((source, v), 0)

            if cap > 0:

                self.flow[(source, v)] = cap

                self.flow[(v, source)] = -cap

                self.excess[v] = cap

                self.excess[source] -= cap

    

    def relabel(self, u):

        """

        再标号操作

        

        将 u 的高度增加到比所有可推送邻接点高 1

        """

        min_height = float('inf')

        

        for v in self.graph[u]:

            residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

            if residual > 0 and self.height[v] < min_height:

                min_height = self.height[v]

        

        self.height[u] = min_height + 1

    

    def push(self, u, v):

        """

        推送操作

        

        将尽可能多的流量从 u 推到 v

        """

        residual_uv = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

        push_amount = min(self.excess[u], residual_uv)

        

        if push_amount > 0:

            self.flow[(u, v)] += push_amount

            self.flow[(v, u)] -= push_amount

            self.excess[u] -= push_amount

            self.excess[v] += push_amount

            return True

        return False

    

    def get_active_vertices(self):

        """获取所有活跃顶点（ excess > 0 且不是源和汇）"""

        active = []

        for v in range(self.n):

            if self.excess[v] > 0:

                active.append((self.height[v], v))

        return active

    

    def max_flow(self, source, sink):

        """

        最高标号预流推进主算法

        

        步骤：

        1. 初始化预流

        2. 选择高度最高的活跃顶点

        3. 尝试推送流量

        4. 如果不能推送，则再标号

        5. 重复直到没有活跃顶点

        """

        from collections import defaultdict

        

        # 重新初始化

        self.height = [0] * self.n

        self.excess = [0] * self.n

        

        # Step 1: 初始化

        self.initialize_preflow(source)

        

        iteration = 0

        max_label = 0

        

        while True:

            # 找到最高标号的活跃顶点

            active = self.get_active_vertices()

            

            if not active:

                break  # 没有活跃顶点

            

            # 按高度降序排序（最高标号优先）

            active.sort(reverse=True)

            h, u = active[0]

            

            if h > max_label:

                max_label = h

            

            # 检查是否可以推送

            can_push = False

            

            for v in self.graph[u]:

                residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

                if residual > 0 and self.height[u] > self.height[v]:

                    # 可以推送

                    self.push(u, v)

                    can_push = True

                    iteration += 1

                    if iteration % 5 == 0:

                        print(f"  迭代 {iteration}: 从 {u} 推送到 {v}，活跃顶点数 {len(active)}")

                    break

            

            if not can_push:

                # 需要再标号

                old_h = self.height[u]

                self.relabel(u)

                iteration += 1

                if iteration % 10 == 0:

                    print(f"  迭代 {iteration}: 再标号 {u}: {old_h} -> {self.height[u]}")

        

        # 计算总流量

        total_flow = sum(self.flow.get((source, v), 0) for v in self.graph[source])

        return total_flow





def build_preflow_network():

    """构建测试网络"""

    from collections import defaultdict

    

    n = 6

    hlf = HighestLabelPreflowPush(n)

    

    edges = [

        (0, 1, 10),

        (0, 2, 10),

        (1, 2, 2),

        (1, 3, 4),

        (1, 4, 8),

        (2, 4, 9),

        (3, 4, 6),

        (3, 5, 10),

        (4, 5, 10),

    ]

    

    for u, v, cap in edges:

        hlf.add_edge(u, v, cap)

    

    return hlf





if __name__ == "__main__":

    print("=" * 55)

    print("最高标号预流推进算法（Highest Label Preflow-Push）")

    print("=" * 55)

    

    hlf = build_preflow_network()

    

    print("\n网络：源=0, 汇=5, 6节点")

    print("边及容量：")

    print("  0->1(10), 0->2(10), 1->2(2), 1->3(4), 1->4(8)")

    print("  2->4(9), 3->4(6), 3->5(10), 4->5(10)")

    

    print("\n算法执行：")

    max_flow = hlf.max_flow(source=0, sink=5)

    

    print(f"\n{'='*55}")

    print(f"最大流 = {max_flow}")

    print(f"最高活跃标号 = {max(hlf.height)}")


# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / cyclic_network_flow



本文件实现 cyclic_network_flow 相关的算法功能。

"""



from collections import defaultdict, deque





class CyclicNetworkFlow:

    """有环网络流分析"""

    

    def __init__(self, n):

        self.n = n

        self.graph = defaultdict(list)

        self.capacity = {}

        self.flow = {}

        self.cost = {}  # (u, v) -> unit cost

    

    def add_edge(self, u, v, cap, cost=0):

        """添加有向边"""

        self.graph[u].append(v)

        self.graph[v].append(u)

        self.capacity[(u, v)] = cap

        self.capacity[(v, u)] = 0

        self.flow[(u, v)] = 0

        self.flow[(v, u)] = 0

        self.cost[(u, v)] = cost

        self.cost[(v, u)] = -cost

    

    def detect_cycles(self):

        """

        使用 DFS 检测有向环

        

        返回：环列表，每个环是一个节点列表

        """

        WHITE, GRAY, BLACK = 0, 1, 2

        color = [WHITE] * self.n

        parent = [-1] * self.n

        cycles = []

        

        def dfs(u, path):

            color[u] = GRAY

            path.append(u)

            

            for v in self.graph[u]:

                residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

                if residual > 0:  # 只考虑有残留容量的边

                    if color[v] == GRAY:

                        # 发现环！

                        cycle_start = path.index(v)

                        cycle = path[cycle_start:] + [v]

                        cycles.append(cycle)

                    elif color[v] == WHITE:

                        parent[v] = u

                        dfs(v, path)

            

            path.pop()

            color[u] = BLACK

        

        for i in range(self.n):

            if color[i] == WHITE:

                dfs(i, [])

        

        return cycles

    

    def cancel_cycles(self):

        """

        消除环流

        

        概念：对于检测到的每个环，可以沿环调整流量

        使总流量不变但消除循环

        """

        cycles = self.detect_cycles()

        

        if not cycles:

            return 0, 0

        

        total_cancelled = 0

        total_cost_saved = 0

        

        print(f"\n检测到 {len(cycles)} 个环")

        

        for idx, cycle in enumerate(cycles):

            # 计算环上每个边的最小残留容量

            min_residual = float('inf')

            for i in range(len(cycle) - 1):

                u, v = cycle[i], cycle[i+1]

                residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

                min_residual = min(min_residual, residual)

            

            # 计算环流可以抵消的流量

            if min_residual > 0:

                # 沿环减少流量（抵消）

                for i in range(len(cycle) - 1):

                    u, v = cycle[i], cycle[i+1]

                    self.flow[(u, v)] -= min_residual

                    self.flow[(v, u)] += min_residual

                

                # 计算节省的成本

                cycle_cost = sum(self.cost.get((cycle[i], cycle[i+1]), 0) 

                               for i in range(len(cycle) - 1))

                total_cost_saved += min_residual * cycle_cost

                total_cancelled += min_residual

                

                print(f"  环 {idx+1}: {cycle[:-1]}, 抵消流量 {min_residual}")

        

        return total_cancelled, total_cancelled, total_cost_saved

    

    def ford_fulkerson_basic(self, source, sink):

        """

        基础的 Ford-Fulkerson 最大流

        """

        flow = 0

        

        while True:

            # BFS 找增广路

            parent = {}

            queue = deque([source])

            parent[source] = None

            

            while queue:

                u = queue.popleft()

                if u == sink:

                    break

                for v in self.graph[u]:

                    if v not in parent:

                        residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

                        if residual > 0:

                            parent[v] = u

                            queue.append(v)

            

            if sink not in parent:

                break

            

            # 找瓶颈

            bottleneck = float('inf')

            v = sink

            while v != source:

                u = parent[v]

                residual = self.capacity.get((u, v), 0) - self.flow.get((u, v), 0)

                bottleneck = min(bottleneck, residual)

                v = u

            

            # 增广

            v = sink

            while v != source:

                u = parent[v]

                self.flow[(u, v)] += bottleneck

                self.flow[(v, u)] -= bottleneck

                v = u

            

            flow += bottleneck

        

        return flow





def build_cyclic_network():

    """构建包含环的网络"""

    cnf = CyclicNetworkFlow(5)

    

    # 添加边（带费用）

    cnf.add_edge(0, 1, 10, 1)  # 源->1

    cnf.add_edge(0, 2, 10, 2)  # 源->2

    cnf.add_edge(1, 2, 3, 1)   # 环边 1->2

    cnf.add_edge(1, 3, 5, 2)   # 1->汇

    cnf.add_edge(2, 3, 5, 1)  # 2->汇

    cnf.add_edge(3, 2, 2, 1)   # 环边 3->2

    cnf.add_edge(3, 4, 8, 2)   # 汇->4（形成另一个环）

    cnf.add_edge(4, 2, 3, 1)   # 4->2

    

    return cnf





if __name__ == "__main__":

    print("=" * 55)

    print("有环网络流（Cyclic Network Flow）分析")

    print("=" * 55)

    

    cnf = build_cyclic_network()

    

    print("\n网络：5节点，有向环结构")

    print("边（带费用）：")

    shown = set()

    for (u, v), cap in cnf.capacity.items():

        if u < v and (u, v) not in shown:

            cost = cnf.cost.get((u, v), 0)

            print(f"  {u} -> {v}: 容量{cap}, 费用{cost}")

            shown.add((u, v))

    

    print("\n运行最大流算法...")

    flow = cnf.ford_fulkerson_basic(source=0, sink=3)

    

    print(f"\n最大流 = {flow}")

    

    print("\n检测并消除环流...")

    cancelled, _, saved = cnf.cancel_cycles()

    

    print(f"\n抵消的环流量 = {cancelled}")

    print(f"节省的费用 = {saved}")

    

    print("\n各边最终流量：")

    shown = set()

    for (u, v), f in cnf.flow.items():

        if u < v and f > 0 and (u, v) not in shown:

            print(f"  {u} -> {v}: {f}")

            shown.add((u, v))


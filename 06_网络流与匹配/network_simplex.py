# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / network_simplex



本文件实现 network_simplex 相关的算法功能。

"""



from collections import deque





class NetworkSimplex:

    """网络单纯形法求解最小费用流"""

    

    def __init__(self, n, source, sink, demand):

        self.n = n

        self.source = source

        self.sink = sink

        self.demand = demand

        

        # 边信息

        self.arcs = []  # (head, tail, capacity, cost, flow, is_tree_edge)

        self.arc_id = {}  # (head, tail) -> arc index

        

        # 树结构

        self.parent = [-1] * n  # BFS树父节点

        self.depth = [0] * n

        self.edge_to_parent = [-1] * n  # 节点到父节点的弧索引

        

        # 节点势

        self.potential = [0.0] * n

        

        # 反向弧映射

        self.rev_arc = {}  # arc_id -> reverse_arc_id

    

    def add_arc(self, head, tail, cap, cost):

        """添加一条弧（从tail到head）"""

        idx = len(self.arcs)

        self.arcs.append([head, tail, cap, cost, 0.0, False])

        

        # 反向弧（容量0，费用为负）

        rev_idx = len(self.arcs)

        self.arcs.append([tail, head, 0.0, -cost, 0.0, False])

        

        self.arc_id[(head, tail)] = idx

        self.rev_arc[idx] = rev_idx

        self.rev_arc[rev_idx] = idx

    

    def initialize_tree(self):

        """初始化生成树（使用从源到所有节点的BFS树）"""

        parent = [-1] * self.n

        edge_to_parent = [-1] * self.n

        

        queue = deque([self.source])

        parent[self.source] = -1

        

        while queue:

            u = queue.popleft()

            for idx, arc in enumerate(self.arcs):

                h, t = arc[0], arc[1]

                if h == u and parent[t] == -1 and t != self.source:

                    parent[t] = u

                    edge_to_parent[t] = idx

                    queue.append(t)

        

        self.parent = parent

        self.edge_to_parent = edge_to_parent

        

        # 标记树边

        for t in range(self.n):

            if self.edge_to_parent[t] != -1:

                self.arcs[self.edge_to_parent[t]][5] = True

    

    def compute_potentials(self):

        """根据当前树计算节点势"""

        # 势通过后序遍历计算

        self.potential[self.source] = 0

        

        # 简化：使用DFS计算势

        visited = [False] * self.n

        stack = [(self.source, -1)]

        

        while stack:

            u, parent_arc = stack.pop()

            if visited[u]:

                continue

            visited[u] = True

            

            for idx, arc in enumerate(self.arcs):

                h, t = arc[0], arc[1]

                if t == u and not visited[h]:

                    if self.edge_to_parent[h] == idx:

                        self.potential[h] = self.potential[u] + arc[3]

                        stack.append((h, idx))

    

    def find_entering_arc(self):

        """找入基弧（violated arc），返回弧索引或-1"""

        for idx, arc in enumerate(self.arcs):

            if arc[5]:  # 跳过树边

                continue

            

            h, t = arc[0], arc[1]

            # reduced cost = cost + pi(t) - pi(h)

            rc = arc[3] + self.potential[t] - self.potential[h]

            

            if arc[2] > 0 and rc < -1e-9:  # 可以增加流量

                return idx, 'increase'

            if arc[4] > 0 and -rc < -1e-9:  # 可以减少流量

                return idx, 'decrease'

        

        return None, None

    

    def find_cycle(self, entering_idx):

        """找由入基弧和树形成的圈，返回路径"""

        entering = self.arcs[entering_idx]

        h, t = entering[0], entering[1]

        

        # 从 h 和 t 向上到 LCA

        path_h = []

        path_t = []

        

        node = h

        while node != -1:

            path_h.append(node)

            if self.parent[node] == -1:

                break

            node = self.parent[node]

        

        node = t

        while node != -1:

            path_t.append(node)

            if self.parent[node] == -1:

                break

            node = self.parent[node]

        

        # 找最近公共祖先

        set_h = set(path_h)

        lca = None

        for v in path_t:

            if v in set_h:

                lca = v

                break

        

        return lca, path_h, path_t

    

    def leave_and_augment(self, entering_idx, direction):

        """确定离基弧并调整流量"""

        entering = self.arcs[entering_idx]

        h, t = entering[0], entering[1]

        

        # 确定增广方向

        if direction == 'increase':

            delta = entering[2]  # 尽可能增加

        else:

            delta = entering[4]  # 尽可能减少

        

        return delta





def build_network():

    """构建测试网络"""

    n = 6

    ns = NetworkSimplex(n, source=0, sink=5, demand=10)

    

    # (head, tail, capacity, cost)

    arcs_data = [

        (1, 0, 4, 2),

        (2, 0, 6, 1),

        (3, 1, 3, 3),

        (2, 1, 2, 2),

        (3, 2, 4, 1),

        (4, 2, 2, 4),

        (5, 3, 5, 2),

        (5, 4, 3, 1),

    ]

    

    for h, t, cap, cost in arcs_data:

        ns.add_arc(h, t, cap, cost)

    

    return ns





if __name__ == "__main__":

    print("=" * 55)

    print("网络单纯形法（Network Simplex）")

    print("=" * 55)

    

    ns = build_network()

    

    print(f"\n网络：{ns.n} 节点，{len(ns.arcs)//2} 弧")

    print(f"源={ns.source}, 汇={ns.sink}, 需求={ns.demand}")

    

    print("\n弧列表（head->tail: cap, cost）：")

    shown = set()

    for i, arc in enumerate(ns.arcs):

        if i % 2 == 0:

            h, t, cap, cost = arc[0], arc[1], arc[2], arc[3]

            if (h, t) not in shown:

                print(f"  {h} -> {t}: cap={cap}, cost={cost}")

                shown.add((h, t))

    

    print("\n初始化生成树...")

    ns.initialize_tree()

    

    print("\n节点势初始化：", ns.potential)

    

    print("\n注意：完整网络单纯形法需要复杂的圈基础操作，")

    print("这里展示核心数据结构和初始化过程。")


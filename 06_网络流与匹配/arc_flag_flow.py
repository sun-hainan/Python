# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / arc_flag_flow



本文件实现 arc_flag_flow 相关的算法功能。

"""



from collections import defaultdict, deque





class ArcFlagFlow:

    """弧标号流算法"""

    

    def __init__(self, n):

        self.n = n

        self.graph = defaultdict(list)

        self.arc_flags = {}  # (u, v, level) -> flag

    

    def add_edge(self, u, v, cap):

        """添加有向边"""

        # 正向边

        self.graph[u].append({

            'to': v, 

            'cap': cap, 

            'flow': 0, 

            'rev': len(self.graph[v])

        })

        # 反向边

        self.graph[v].append({

            'to': u, 

            'cap': 0, 

            'flow': 0, 

            'rev': len(self.graph[u]) - 1

        })

    

    def build_level_graph(self, source, sink):

        """

        构建分层图（BFS）

        

        返回：

            level[v] = 节点 v 的层次（距离源的跳数）

            如果 v 不可达，返回 -1

        """

        level = [-1] * self.n

        level[source] = 0

        

        queue = deque([source])

        

        while queue:

            u = queue.popleft()

            for edge in self.graph[u]:

                v = edge['to']

                residual = edge['cap'] - edge['flow']

                

                if residual > 0 and level[v] < 0:

                    level[v] = level[u] + 1

                    queue.append(v)

        

        return level

    

    def update_arc_flags(self, level):

        """

        更新弧标号

        

        弧 (u, v) 在当前分层图中是有效的

        当且仅当 level[u] >= 0 且 level[v] = level[u] + 1

        """

        for u in range(self.n):

            for edge in self.graph[u]:

                v = edge['to']

                residual = edge['cap'] - edge['flow']

                

                if level[u] >= 0 and level[v] == level[u] + 1 and residual > 0:

                    # 弧是前向弧，在当前分层图中有效

                    self.arc_flags[(u, v, level[u])] = True

                else:

                    # 标记为无效（或删除）

                    self.arc_flags.pop((u, v, level.get(u, -1)), None)

    

    def blocking_flow(self, source, sink, level):

        """

        寻找阻塞流（使用 DFS + 弧标号优化）

        

        弧标号优化：如果弧 (u, v) 不在当前分层图的正确层次，

        直接跳过

        """

        n = self.n

        ptr = [0] * n  # 当前弧指针（用于避免重复遍历）

        

        def dfs(u, pushed):

            if u == sink or pushed == 0:

                return pushed

            

            for ptr[u] in range(ptr[u], len(self.graph[u])):

                edge = self.graph[u][ptr[u]]

                v = edge['to']

                residual = edge['cap'] - edge['flow']

                

                # 弧标号检查：只考虑当前分层图中的前向弧

                if (u, v, level[u]) not in self.arc_flags:

                    continue

                

                if residual > 0 and level[v] == level[u] + 1:

                    tr = dfs(v, min(pushed, residual))

                    if tr == 0:

                        continue

                    

                    # 增广

                    edge['flow'] += tr

                    self.graph[v][edge['rev']]['flow'] -= tr

                    return tr

            

            return 0

        

        flow = 0

        while True:

            pushed = dfs(source, float('inf'))

            if pushed == 0:

                break

            flow += pushed

        

        return flow

    

    def max_flow(self, source, sink):

        """

        Dinic + 弧标号优化的最大流

        

        主循环：

        1. BFS 构建分层图

        2. 更新弧标号

        3. 在当前分层图上找阻塞流

        4. 重复直到无法到达汇

        """

        flow = 0

        iteration = 0

        

        while True:

            iteration += 1

            

            # BFS 构建分层图

            level = self.build_level_graph(source, sink)

            

            if level[sink] < 0:

                break  # 汇不可达

            

            # 更新弧标号

            self.update_arc_flags(level)

            

            # 找阻塞流

            current_flow = self.blocking_flow(source, sink, level)

            

            if current_flow == 0:

                break

            

            flow += current_flow

            print(f"  迭代 {iteration}: 增广 {current_flow}，累计 {flow}")

        

        return flow





def build_arc_flag_network():

    """构建测试网络"""

    n = 6

    aff = ArcFlagFlow(n)

    

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

        aff.add_edge(u, v, cap)

    

    return aff





if __name__ == "__main__":

    print("=" * 55)

    print("弧标号流（Arc-Flag Flow）算法")

    print("=" * 55)

    

    aff = build_arc_flag_network()

    

    print("\n网络：源=0, 汇=5, 6节点")

    print("边及容量：")

    print("  0->1(10), 0->2(10), 1->2(2), 1->3(4), 1->4(8)")

    print("  2->4(9), 3->4(6), 3->5(10), 4->5(10)")

    

    print("\n算法执行：")

    max_flow = aff.max_flow(source=0, sink=5)

    

    print(f"\n{'='*55}")

    print(f"最大流 = {max_flow}")

    

    # 弧标号统计

    valid_flags = sum(1 for k in aff.arc_flags if aff.arc_flags[k])

    print(f"活跃弧标号数 = {valid_flags}")


# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / tarjan_scc



本文件实现 tarjan_scc 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple

from collections import defaultdict





class TarjanSCC:

    """

    Tarjan强连通分量算法

    """

    

    def __init__(self):

        self.graph: Dict[str, Set[str]] = defaultdict(set)

        self.nodes: Set[str] = set()

        

        # Tarjan算法状态

        self.index = 0

        self.stack: List[str] = []

        self.on_stack: Set[str] = set()

        self.indices: Dict[str, int] = {}

        self.lowlinks: Dict[str, int] = {}

        self.sccs: List[List[str]] = []

    

    def add_node(self, node: str):

        """添加节点"""

        self.nodes.add(node)

    

    def add_edge(self, from_node: str, to_node: str):

        """添加有向边"""

        self.nodes.add(from_node)

        self.nodes.add(to_node)

        self.graph[from_node].add(to_node)

    

    def strong_connect(self, v: str):

        """

        DFS强连通分量探索

        

        参数:

            v: 当前节点

        """

        # 设置深度索引

        self.indices[v] = self.index

        self.lowlinks[v] = self.index

        self.index += 1

        self.stack.append(v)

        self.on_stack.add(v)

        

        # 递归探索所有后继

        for w in self.graph[v]:

            if w not in self.indices:

                # w未被访问

                self.strong_connect(w)

                self.lowlinks[v] = min(self.lowlinks[v], self.lowlinks[w])

            elif w in self.on_stack:

                # w在栈中，是当前SCC的一部分

                self.lowlinks[v] = min(self.lowlinks[v], self.indices[w])

        

        # 如果v是根节点，弹出栈生成SCC

        if self.lowlinks[v] == self.indices[v]:

            scc = []

            while True:

                w = self.stack.pop()

                self.on_stack.remove(w)

                scc.append(w)

                if w == v:

                    break

            self.sccs.append(scc)

    

    def find_sccs(self) -> List[List[str]]:

        """

        找出所有强连通分量

        

        返回:

            SCC列表

        """

        self.index = 0

        self.stack = []

        self.on_stack = set()

        self.indices = {}

        self.lowlinks = {}

        self.sccs = []

        

        for node in self.nodes:

            if node not in self.indices:

                self.strong_connect(node)

        

        return self.sccs





def find_circular_dependencies(graph: Dict[str, Set[str]]) -> List[List[str]]:

    """

    查找循环依赖

    

    参数:

        graph: 有向图

    

    返回:

        循环依赖列表

    """

    finder = TarjanSCC()

    for node, neighbors in graph.items():

        for neighbor in neighbors:

            finder.add_edge(node, neighbor)

    

    sccs = finder.find_sccs()

    

    # 只返回大小大于1的SCC（真正的循环）

    return [scc for scc in sccs if len(scc) > 1]





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 50)

    print("Tarjan强连通分量测试")

    print("=" * 50)

    

    # 示例图

    # A -> B -> C -> A (循环)

    # C -> D

    

    finder = TarjanSCC()

    edges = [

        ('A', 'B'),

        ('B', 'C'),

        ('C', 'A'),  # 形成SCC: A,B,C

        ('C', 'D'),

    ]

    

    for from_n, to_n in edges:

        finder.add_edge(from_n, to_n)

    

    sccs = finder.find_sccs()

    

    print("强连通分量:")

    for scc in sccs:

        print(f"  {scc}")

    

    print("\n循环依赖检测:")

    circular = find_circular_dependencies(finder.graph)

    print(f"  循环依赖: {circular}")


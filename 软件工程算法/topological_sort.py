# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / topological_sort



本文件实现 topological_sort 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from collections import defaultdict, deque





class DirectedGraph:

    """

    有向图类

    """

    

    def __init__(self):

        self.graph: Dict[str, Set[str]] = defaultdict(set)  # 邻接表

        self.in_degree: Dict[str, int] = defaultdict(int)   # 入度

        self.nodes: Set[str] = set()

    

    def add_node(self, node: str):

        """

        添加节点

        

        参数:

            node: 节点名称

        """

        self.nodes.add(node)

    

    def add_edge(self, from_node: str, to_node: str):

        """

        添加有向边

        

        参数:

            from_node: 起始节点

            to_node: 目标节点

        """

        self.nodes.add(from_node)

        self.nodes.add(to_node)

        

        if to_node not in self.graph[from_node]:

            self.graph[from_node].add(to_node)

            self.in_degree[to_node] += 1

    

    def has_cycle(self) -> bool:

        """

        检查是否存在环

        

        返回:

            是否存在环

        """

        visited = set()

        rec_stack = set()

        

        def dfs(node: str) -> bool:

            visited.add(node)

            rec_stack.add(node)

            

            for neighbor in self.graph[node]:

                if neighbor not in visited:

                    if dfs(neighbor):

                        return True

                elif neighbor in rec_stack:

                    return True

            

            rec_stack.remove(node)

            return False

        

        for node in self.nodes:

            if node not in visited:

                if dfs(node):

                    return True

        

        return False





def topological_sort_kahn(graph: DirectedGraph) -> Tuple[bool, List[str]]:

    """

    Kahn算法（基于入度）

    

    步骤：

    1. 计算所有节点的入度

    2. 将入度为0的节点加入队列

    3. 反复取出队首节点，将其加入结果

    4. 更新相邻节点的入度

    5. 重复直到队列为空

    

    参数:

        graph: 有向图

    

    返回:

        (是否成功排序, 拓扑排序结果)

    """

    if graph.has_cycle():

        return False, []

    

    in_degree = dict(graph.in_degree)

    for node in graph.nodes:

        if node not in in_degree:

            in_degree[node] = 0

    

    # 入度为0的节点队列

    queue = deque([node for node in graph.nodes if in_degree[node] == 0])

    result = []

    

    while queue:

        node = queue.popleft()

        result.append(node)

        

        for neighbor in graph.graph[node]:

            in_degree[neighbor] -= 1

            if in_degree[neighbor] == 0:

                queue.append(neighbor)

    

    if len(result) != len(graph.nodes):

        return False, []

    

    return True, result





def topological_sort_dfs(graph: DirectedGraph) -> Tuple[bool, List[str]]:

    """

    基于DFS的拓扑排序

    

    步骤：

    1. 对所有未访问节点进行DFS

    2. 在DFS返回前，将节点加入结果

    3. 结果逆序即为拓扑排序

    

    参数:

        graph: 有向图

    

    返回:

        (是否成功排序, 拓扑排序结果)

    """

    if graph.has_cycle():

        return False, []

    

    visited = set()

    result = []

    rec_stack = set()

    

    def dfs(node: str):

        """深度优先搜索"""

        if node in rec_stack:

            return False

        if node in visited:

            return True

        

        visited.add(node)

        rec_stack.add(node)

        

        for neighbor in graph.graph[node]:

            if neighbor not in visited:

                if not dfs(neighbor):

                    return False

        

        rec_stack.remove(node)

        result.append(node)

        return True

    

    for node in graph.nodes:

        if node not in visited:

            if not dfs(node):

                return False, []

    

    result.reverse()

    return True, result





def dependency_resolution(dependencies: Dict[str, List[str]]) -> List[str]:

    """

    依赖解析（典型的拓扑排序应用）

    

    参数:

        dependencies: {包名: [依赖列表]}

    

    返回:

        安装顺序

    """

    graph = DirectedGraph()

    

    # 添加所有节点

    for pkg in dependencies:

        graph.add_node(pkg)

    

    # 添加边（依赖 -> 被依赖）

    for pkg, deps in dependencies.items():

        for dep in deps:

            graph.add_edge(dep, pkg)

    

    success, order = topological_sort_kahn(graph)

    

    if not success:

        return []  # 存在循环依赖

    

    return order





def course_schedule(prerequisites: List[Tuple[int, int]]) -> bool:

    """

    课程安排问题

    

    判断是否可能完成所有课程（检测环）

    

    参数:

        prerequisites: [(先修课, 课程), ...]

    

    返回:

        是否可能完成

    """

    graph = DirectedGraph()

    

    for course, prereq in prerequisites:

        graph.add_edge(prereq, course)

    

    return not graph.has_cycle()





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本拓扑排序

    print("=" * 50)

    print("测试1: 基本拓扑排序")

    print("=" * 50)

    

    # 构建依赖图: A -> B -> C

    graph = DirectedGraph()

    graph.add_edge('A', 'B')

    graph.add_edge('B', 'C')

    graph.add_edge('A', 'C')

    

    print("图结构: A -> B -> C, A -> C")

    

    success, order = topological_sort_kahn(graph)

    print(f"Kahn算法: {'成功' if success else '失败'}, 顺序: {order}")

    

    success, order = topological_sort_dfs(graph)

    print(f"DFS算法: {'成功' if success else '失败'}, 顺序: {order}")

    

    # 测试用例2：复杂依赖

    print("\n" + "=" * 50)

    print("测试2: 复杂依赖图")

    print("=" * 50)

    

    graph = DirectedGraph()

    edges = [

        ('A', 'C'),

        ('B', 'C'),

        ('C', 'D'),

        ('D', 'E'),

        ('C', 'E'),

    ]

    

    for from_n, to_n in edges:

        graph.add_edge(from_n, to_n)

    

    print("依赖关系:")

    for from_n, to_n in edges:

        print(f"  {from_n} -> {to_n}")

    

    success, order = topological_sort_kahn(graph)

    print(f"\n拓扑排序: {order}")

    

    # 测试用例3：依赖解析

    print("\n" + "=" * 50)

    print("测试3: 包依赖解析")

    print("=" * 50)

    

    dependencies = {

        'app': ['framework', 'database'],

        'framework': ['logging'],

        'database': ['logging'],

        'logging': [],

        'ui': ['framework'],

    }

    

    print("依赖关系:")

    for pkg, deps in dependencies.items():

        print(f"  {pkg}: {deps if deps else '(无依赖)'}")

    

    order = dependency_resolution(dependencies)

    print(f"\n安装顺序: {order}")

    

    # 测试用例4：循环依赖检测

    print("\n" + "=" * 50)

    print("测试4: 循环依赖检测")

    print("=" * 50)

    

    graph = DirectedGraph()

    graph.add_edge('A', 'B')

    graph.add_edge('B', 'C')

    graph.add_edge('C', 'A')  # 形成环

    

    has_cycle = graph.has_cycle()

    print(f"图 A->B->C->A 是否有环: {has_cycle}")

    

    success, order = topological_sort_kahn(graph)

    print(f"拓扑排序: {'成功' if success else '失败'}")

    

    # 测试用例5：课程安排

    print("\n" + "=" * 50)

    print("测试5: 课程安排")

    print("=" * 50)

    

    # 课程0 -> 课程1 -> 课程2

    prerequisites = [(0, 1), (1, 2)]

    can_finish = course_schedule(prerequisites)

    print(f"课程 0->1->2 是否可行: {can_finish}")

    

    # 形成环: 0->1->2->0

    prerequisites = [(0, 1), (1, 2), (2, 0)]

    can_finish = course_schedule(prerequisites)

    print(f"课程 0->1->2->0 是否可行: {can_finish}")

    

    # 测试用例6：入度分析

    print("\n" + "=" * 50)

    print("测试6: 入度分析")

    print("=" * 50)

    

    graph = DirectedGraph()

    edges = [

        ('A', 'C'),

        ('B', 'C'),

        ('B', 'D'),

        ('C', 'E'),

        ('D', 'E'),

    ]

    

    for from_n, to_n in edges:

        graph.add_edge(from_n, to_n)

    

    print("图结构和入度:")

    for node in sorted(graph.nodes):

        in_d = graph.in_degree[node]

        out_neighbors = sorted(graph.graph[node])

        print(f"  {node}: 入度={in_d}, 出边={out_neighbors}")


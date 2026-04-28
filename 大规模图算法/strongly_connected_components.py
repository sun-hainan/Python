"""
强连通分量算法 (Strongly Connected Components)
=============================================
实现Kosaraju算法和Tarjan算法，用于分解有向图为强连通分量。

强连通分量：有向图中任意两个顶点互相可达的最大子图。

Kosaraju算法：两次DFS，第一次记录后继顺序，第二次按逆序遍历。
Tarjan算法：单次DFS，使用栈和lowlink实现。

参考：
    - Kosaraju, S.R. (1978). On computing the strongly connected components.
    - Tarjan, R.E. (1972). Depth-first search and linear graph algorithms.
"""

from typing import List, Dict, Set, Optional
from collections import deque


class DirectedGraph:
    """有向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.succ = [[] for _ in range(n)]  # 后继
        self.pred = [[] for _ in range(n)]  # 前驱
    
    def add_edge(self, u: int, v: int):
        """添加有向边 u -> v"""
        self.succ[u].append(v)
        self.pred[v].append(u)
    
    def successors(self, u: int) -> List[int]:
        return self.succ[u]
    
    def predecessors(self, u: int) -> List[int]:
        return self.pred[u]
    
    def reverse(self) -> 'DirectedGraph':
        """返回反向图"""
        g_rev = DirectedGraph(self.n)
        for u in range(self.n):
            for v in self.succ[u]:
                g_rev.add_edge(v, u)  # 反向
        return g_rev


def kosaraju_scc(graph: DirectedGraph) -> List[List[int]]:
    """
    Kosaraju算法求强连通分量
    
    步骤:
        1. 在原图上DFS，记录完成顺序（按完成时间降序）
        2. 在反向图上，按完成顺序的逆序DFS，得到的连通块即为SCC
    
    参数:
        graph: 有向图
    
    返回:
        强连通分量列表，每个分量是一个节点列表
    """
    n = graph.n
    visited = [False] * n
    finish_order = []  # 完成顺序
    
    # 第一次DFS：在原图上
    def dfs1(u: int):
        visited[u] = True
        for v in graph.successors(u):
            if not visited[v]:
                dfs1(v)
        finish_order.append(u)
    
    for v in range(n):
        if not visited[v]:
            dfs1(v)
    
    # 第二次DFS：在反向图上
    graph_rev = graph.reverse()
    visited2 = [False] * n
    sccs = []
    
    def dfs2(u: int, component: List[int]):
        visited2[u] = True
        component.append(u)
        for v in graph_rev.successors(u):
            if not visited2[v]:
                dfs2(v, component)
    
    # 按完成时间的逆序遍历
    for v in reversed(finish_order):
        if not visited2[v]:
            component = []
            dfs2(v, component)
            sccs.append(component)
    
    return sccs


def tarjan_scc(graph: DirectedGraph) -> List[List[int]]:
    """
    Tarjan算法求强连通分量（单次DFS）
    
    使用:
        - index: DFS访问序号
         - lowlink: 能回溯到的最小index
         - on_stack: 节点是否在栈上
    
    参数:
        graph: 有向图
    
    返回:
        强连通分量列表
    """
    n = graph.n
    
    # 状态变量
    index = 0
    node_index = [-1] * n  # 每个节点的访问序号
    lowlink = [0] * n
    on_stack = [False] * n
    stack = []  # DFS栈
    
    sccs = []
    
    def strongconnect(v: int):
        nonlocal index
        
        # 设置节点的index和lowlink
        node_index[v] = index
        lowlink[v] = index
        index += 1
        
        stack.append(v)
        on_stack[v] = True
        
        # 遍历后继
        for w in graph.successors(v):
            if node_index[w] == -1:
                # w未被访问，递归
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack[w]:
                # w在当前栈中，更新lowlink
                lowlink[v] = min(lowlink[v], node_index[w])
        
        # 检查是否为SCC的根
        if lowlink[v] == node_index[v]:
            # 弹出栈直到v
            component = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == v:
                    break
            sccs.append(component)
    
    for v in range(n):
        if node_index[v] == -1:
            strongconnect(v)
    
    return sccs


def gabow_scc(graph: DirectedGraph) -> List[List[int]]:
    """
    Gabow算法（Kosaraju的变体，不需反向图）
    
    使用两个栈：
        - 第一个栈：DFS树栈
        - 第二个栈：候选SCC根栈
    
    参数:
        graph: 有向图
    
    返回:
        强连通分量列表
    """
    n = graph.n
    
    index = 0
    node_index = [-1] * n
    preorder = []  # 第一个栈：DFS顺序
    path = []  # 第二个栈：路径
    
    sccs = []
    
    def process_edge(u: int, v: int):
        nonlocal index
        
        if node_index[v] == -1:
            # v未被访问，入path栈
            node_index[v] = index
            index += 1
            path.append(v)
            return True  # 继续DFS
        elif v in path:
            # v在当前路径中，压缩路径
            while node_index[path[-1]] > node_index[v]:
                path.pop()
            return False  # 不继续DFS
        return False  # v不在当前路径中，不继续DFS
    
    def dfs(u: int):
        node_index[u] = index
        index += 1
        path.append(u)
        
        for v in graph.successors(u):
            if node_index[v] == -1:
                dfs(v)
            elif v in path:
                # 压缩
                while node_index[path[-1]] > node_index[v]:
                    path.pop()
        
        # 回溯时检查是否为SCC根
        if u == path[-1]:
            path.pop()
            # 弹出所有可达节点
            while preorder and node_index[preorder[-1]] > node_index[u]:
                w = preorder.pop()
                if w != u:
                    sccs.append([w])  # 简化处理
    
    # 更清晰的实现
    stack1 = []  # DFS栈
    stack2 = []  # 候选栈
    indices = [-1] * n
    lowlink = [0] * n
    
    def strongconnect(v: int):
        nonlocal index
        
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack1.append(v)
        stack2.append(v)
        
        for w in graph.successors(v):
            if indices[w] == -1:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in stack2:
                lowlink[v] = min(lowlink[v], indices[w])
        
        # 判断是否为SCC根
        if lowlink[v] == indices[v]:
            component = []
            while True:
                w = stack1.pop()
                stack2.remove(w)
                component.append(w)
                if w == v:
                    break
            sccs.append(component)
    
    for v in range(n):
        if indices[v] == -1:
            strongconnect(v)
    
    return sccs


def weakly_connected_components(graph: DirectedGraph) -> List[List[int]]:
    """
    弱连通分量：将有向图当作无向图看的连通分量
    
    参数:
        graph: 有向图
    
    返回:
        弱连通分量列表
    """
    n = graph.n
    visited = [False] * n
    components = []
    
    def dfs(u: int, component: List[int]):
        visited[u] = True
        component.append(u)
        for v in graph.successors(u):
            if not visited[v]:
                dfs(v, component)
        for v in graph.predecessors(u):
            if not visited[v]:
                dfs(v, component)
    
    for v in range(n):
        if not visited[v]:
            component = []
            dfs(v, component)
            components.append(component)
    
    return components


def condensation_graph(graph: DirectedGraph, sccs: List[List[int]]) -> DirectedGraph:
    """
    构建SCC压缩图（凝聚图）
    
    参数:
        graph: 原图
        sccs: 强连通分量列表
    
    返回:
        以SCC为节点的DAG
    """
    # 创建SCC到索引的映射
    scc_id = {}
    for i, scc in enumerate(sccs):
        for v in scc:
            scc_id[v] = i
    
    # 创建压缩图
    cond = DirectedGraph(len(sccs))
    
    # 添加边
    for u in range(graph.n):
        for v in graph.successors(u):
            scc_u = scc_id[u]
            scc_v = scc_id[v]
            if scc_u != scc_v:
                cond.add_edge(scc_u, scc_v)
    
    return cond


def kosaraju_iterative(graph: DirectedGraph) -> List[List[int]]:
    """
    Kosaraju算法的迭代版本（避免递归栈溢出）
    
    参数:
        graph: 有向图
    
    返回:
        强连通分量列表
    """
    n = graph.n
    visited = [False] * n
    finish_order = []
    
    # 第一次DFS（迭代）
    for start in range(n):
        if visited[start]:
            continue
        
        stack = [(start, 0)]  # (节点, 状态) 状态0=进入, 1=离开
        while stack:
            u, state = stack.pop()
            if state == 0:
                if visited[u]:
                    continue
                visited[u] = True
                stack.append((u, 1))  # 离开时处理
                for v in graph.successors(u):
                    if not visited[v]:
                        stack.append((v, 0))
            else:
                finish_order.append(u)
    
    # 反向图
    graph_rev = graph.reverse()
    visited2 = [False] * n
    sccs = []
    
    # 第二次DFS（迭代）
    for start in reversed(finish_order):
        if visited2[start]:
            continue
        
        component = []
        stack = [start]
        while stack:
            u = stack.pop()
            if visited2[u]:
                continue
            visited2[u] = True
            component.append(u)
            for v in graph_rev.successors(u):
                if not visited2[v]:
                    stack.append(v)
        sccs.append(component)
    
    return sccs


if __name__ == "__main__":
    print("=== 强连通分量算法测试 ===")
    
    # 创建测试图
    g = DirectedGraph(8)
    edges = [
        (0, 1), (1, 2), (2, 0),  # SCC: {0,1,2}
        (2, 3),  # 边到SCC 3
        (3, 4), (4, 5), (5, 3),  # SCC: {3,4,5}
        (5, 6),  # 边到SCC 6,7
        (6, 7), (7, 5)  # SCC: {5,6,7}...实际上5,6,7应该合并
    ]
    
    # 重新设计：0->1->2->0, 2->3, 3->4->5->3, 5->6->7->5
    g2 = DirectedGraph(8)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    g2.add_edge(2, 0)  # SCC1
    g2.add_edge(2, 3)
    g2.add_edge(3, 4)
    g2.add_edge(4, 5)
    g2.add_edge(5, 3)  # SCC2: {3,4,5}
    g2.add_edge(5, 6)
    g2.add_edge(6, 7)
    g2.add_edge(7, 5)  # SCC3: {5,6,7}...实际上5在SCC2里
    
    # 修正测试图
    g3 = DirectedGraph(7)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    g3.add_edge(2, 0)  # SCC1: {0,1,2}
    g3.add_edge(2, 3)
    g3.add_edge(3, 4)
    g3.add_edge(4, 5)
    g3.add_edge(5, 3)  # SCC2: {3,4,5}
    g3.add_edge(5, 6)  # SCC3: {6} (单独)
    
    print("\n测试图结构:")
    print("  SCC1: 0->1->2->0")
    print("  SCC2: 2->3->4->5->3")
    print("  SCC3: 5->6")
    
    # Kosaraju
    sccs_kosaraju = kosaraju_scc(g3)
    print(f"\nKosaraju算法: 找到 {len(sccs_kosaraju)} 个SCC")
    for i, scc in enumerate(sccs_kosaraju):
        print(f"  SCC{i+1}: {sorted(scc)}")
    
    # Tarjan
    sccs_tarjan = tarjan_scc(g3)
    print(f"\nTarjan算法: 找到 {len(sccs_tarjan)} 个SCC")
    for i, scc in enumerate(sccs_tarjan):
        print(f"  SCC{i+1}: {sorted(scc)}")
    
    # Kosaraju迭代版
    sccs_iter = kosaraju_iterative(g3)
    print(f"\nKosaraju迭代版: 找到 {len(sccs_iter)} 个SCC")
    for i, scc in enumerate(sccs_iter):
        print(f"  SCC{i+1}: {sorted(scc)}")
    
    # 凝聚图
    print("\n构建凝聚图:")
    cond = condensation_graph(g3, sccs_tarjan)
    print(f"  压缩为 {cond.n} 个节点")
    print("  边:", [(u, v) for u in range(cond.n) for v in cond.successors(u)])
    
    # 弱连通分量
    wcc = weakly_connected_components(g3)
    print(f"\n弱连通分量: {len(wcc)} 个")
    for i, comp in enumerate(wcc):
        print(f"  分量{i+1}: {sorted(comp)}")
    
    # 链式图测试
    print("\n\n链式图测试:")
    g_chain = DirectedGraph(4)
    g_chain.add_edge(0, 1)
    g_chain.add_edge(1, 2)
    g_chain.add_edge(2, 3)
    
    sccs_chain = tarjan_scc(g_chain)
    print(f"链式图 SCC数: {len(sccs_chain)}")
    for scc in sccs_chain:
        print(f"  {scc}")
    
    print("\n=== 测试完成 ===")

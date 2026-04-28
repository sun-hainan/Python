"""
图编辑距离 (Graph Edit Distance, GED)
=====================================
使用动态规划计算两图之间的最小编辑距离。

图编辑距离定义：将一个图G通过一系列编辑操作转换为另一个图G'所需的
最小代价。编辑操作包括：节点插入、节点删除、节点替换、边插入、边删除、边替换。

使用A*搜索结合动态规划下界估计来加速搜索。

参考：
    - Sanfeliu, A. & Fu, K.S. (1983). A distance measure between graphs.
    - Riesen, K. & Bunke, H. (2009). Approximate graph edit distance computation.
"""

from typing import List, Dict, Set, Tuple, Optional
import heapq
from collections import deque


class Graph:
    """图数据结构"""
    
    def __init__(self, n: int = 0, labels: Optional[List[int]] = None):
        self.n = n  # 节点数量
        self.labels = labels if labels else [0] * n  # 节点标签，默认全0
        self.adj = [set() for _ in range(n)]  # 邻接集合
    
    def add_edge(self, u: int, v: int):
        """添加无向边"""
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def has_edge(self, u: int, v: int) -> bool:
        """检查边是否存在"""
        return v in self.adj[u]


class GEDState:
    """A*搜索中的状态"""
    
    def __init__(self, g1: Graph, g2: Graph, partial_map: Dict[int, int], g: float):
        self.g1 = g1  # 源图
        self.g2 = g2  # 目标图
        self.partial_map = partial_map  # 部分映射 {g1_node: g2_node}
        self.g_cost = g  # 从起点到当前状态的实际代价
        self.unmapped_g1 = []  # g1中未映射的节点
        self.unmapped_g2 = []  # g2中未映射的节点
        self._compute_unmapped()
    
    def _compute_unmapped(self):
        """计算未映射节点列表"""
        self.unmapped_g1 = [i for i in range(self.g1.n) if i not in self.partial_map]
        self.unmapped_g2 = [j for j in range(self.g2.n) if j not in self.partial_map.values()]
    
    def compute_h(self) -> float:
        """计算启发式下界（乐观估计剩余代价）"""
        h = 0.0
        
        # 节点替换代价：标签不同的节点对
        # 对于完全未映射的节点，假设最好的情况是标签相同
        min_nodes = min(len(self.unmapped_g1), len(self.unmapped_g2))
        
        # 每个未匹配节点至少产生1的插入或删除代价
        h += abs(len(self.unmapped_g1) - len(self.unmapped_g2))
        
        # 节点替换代价的上界（乐观估计都是0）
        # 边的编辑代价下界
        # 每个未映射节点对，最多可能产生的边代价
        max_edges_per_node = max(len(self.unmapped_g1), len(self.unmapped_g2))
        h += min_nodes * max_edges_per_node * 0.5  # 乐观估计
        
        return h
    
    def f(self) -> float:
        """A*的f值 = g + h"""
        return self.g_cost + self.compute_h()
    
    def __lt__(self, other):
        """用于优先队列比较"""
        return self.f() < other.f()


def edit_cost_node_substitute(label1: int, label2: int) -> float:
    """节点替换代价：标签不同时产生代价"""
    return 0.0 if label1 == label2 else 1.0


def edit_cost_edge_substitute(has_edge: bool) -> float:
    """边替换代价（这里简化为二元情况）"""
    return 0.0


def edit_cost_node_insert() -> float:
    """节点插入代价"""
    return 1.0


def edit_cost_node_delete() -> float:
    """节点删除代价"""
    return 1.0


def edit_cost_edge_insert() -> float:
    """边插入代价"""
    return 1.0


def edit_cost_edge_delete() -> float:
    """边插入代价"""
    return 1.0


def compute_edge_edit_cost(g1: Graph, g2: Graph, partial_map: Dict[int, int],
                          u: int, v: Optional[int]) -> float:
    """
    计算由于节点u的映射而需要编辑的边的代价
    
    参数:
        g1: 源图
        g2: 目标图
        partial_map: 当前部分映射
        u: g1中的节点
        v: g2中映射到的节点（None表示删除u）
    """
    cost = 0.0
    
    # 计算u在g1中的邻居
    neighbors_u = g1.adj[u]
    
    if v is not None:
        # u映射到v，计算需要编辑的边
        neighbors_v = g2.adj[v]
        
        # 遍历g1中u的邻居
        for w in neighbors_u:
            if w in partial_map:
                w_prime = partial_map[w]
                # w已经映射，检查边是否需要编辑
                if w_prime in neighbors_v:
                    # 边都存在，不需要编辑
                    pass
                else:
                    # g1有边(u,w)但g2没有(v,w')，需要删除或替换
                    cost += edit_cost_edge_delete()
            # 如果w未映射，边编辑代价在后续计算
    else:
        # u被删除，其所有边都需要删除
        cost += len(neighbors_u) * edit_cost_edge_delete()
    
    return cost


def a_star_ged(g1: Graph, g2: Graph, max_iterations: int = 5000) -> Tuple[float, Optional[Dict[int, int]]]:
    """
    使用A*搜索计算GED
    
    参数:
        g1: 源图
        g2: 目标图
        max_iterations: 最大迭代次数
    
    返回:
        (最小编辑距离, 最优映射) 或 (-1, None) 如果超时
    """
    # 初始化：从空映射开始
    initial_state = GEDState(g1, g2, {}, 0.0)
    
    # 优先队列：(f值, 迭代次数, 状态)
    pq = [(initial_state.f(), 0, initial_state)]
    visited = set()
    iteration = 0
    
    while pq and iteration < max_iterations:
        iteration += 1
        _, _, state = heapq.heappop(pq)
        
        # 生成状态的唯一键
        map_key = tuple(sorted(state.partial_map.items()))
        if map_key in visited:
            continue
        visited.add(map_key)
        
        # 检查是否到达目标状态
        if len(state.partial_map) == min(g1.n, g2.n):
            # 所有可能的映射都已尝试
            # 计算最终的编辑代价
            final_cost = compute_final_edit_cost(g1, g2, state.partial_map)
            return final_cost, state.partial_map
        
        # 选择下一步操作
        if state.unmapped_g1 and state.unmapped_g2:
            # 既有未映射的g1节点，又有未映射的g2节点
            # 尝试替换/匹配操作
            u = state.unmapped_g1[0]
            
            # 尝试将u映射到g2的某个未映射节点
            for v in state.unmapped_g2:
                new_map = state.partial_map.copy()
                new_map[u] = v
                
                # 计算代价增量
                cost_inc = edit_cost_node_substitute(g1.labels[u], g2.labels[v])
                cost_inc += compute_edge_edit_cost(g1, g2, new_map, u, v)
                
                new_state = GEDState(g1, g2, new_map, state.g_cost + cost_inc)
                heapq.heappush(pq, (new_state.f(), iteration, new_state))
            
            # 尝试删除u（不映射到任何节点）
            new_map = state.partial_map.copy()
            cost_inc = edit_cost_node_delete()
            cost_inc += compute_edge_edit_cost(g1, g2, new_map, u, None)
            new_state = GEDState(g1, g2, new_map, state.g_cost + cost_inc)
            heapq.heappush(pq, (new_state.f(), iteration, new_state))
        
        elif state.unmapped_g1:
            # 只有未映射的g1节点：必须删除
            u = state.unmapped_g1[0]
            new_map = state.partial_map.copy()
            cost_inc = edit_cost_node_delete()
            cost_inc += compute_edge_edit_cost(g1, g2, new_map, u, None)
            new_state = GEDState(g1, g2, new_map, state.g_cost + cost_inc)
            heapq.heappush(pq, (new_state.f(), iteration, new_state))
        
        elif state.unmapped_g2:
            # 只有未映射的g2节点：必须插入
            v = state.unmapped_g2[0]
            new_map = state.partial_map.copy()
            # 找一个g1节点来"替换"（实际上是插入）
            cost_inc = edit_cost_node_insert()
            new_state = GEDState(g1, g2, new_map, state.g_cost + cost_inc)
            heapq.heappush(pq, (new_state.f(), iteration, new_state))
    
    return -1.0, None  # 超时


def compute_final_edit_cost(g1: Graph, g2: Graph, mapping: Dict[int, int]) -> float:
    """计算最终映射的编辑代价"""
    cost = 0.0
    
    # 1. 节点替换代价
    for u, v in mapping.items():
        cost += edit_cost_node_substitute(g1.labels[u], g2.labels[v])
    
    # 2. 边的编辑代价
    # 对于映射的节点对(u, v)，计算其邻居边的编辑代价
    mapped_g2 = set(mapping.values())
    
    for u, v in mapping.items():
        # g1中u的邻居
        neighbors_u = g1.adj[u]
        # g2中v的邻居（只考虑已映射的）
        neighbors_v = set(g2.adj[v]) & mapped_g2
        
        for w in neighbors_u:
            if w in mapping:
                w_prime = mapping[w]
                # (u,w)在g1中有边
                if w_prime not in neighbors_v:
                    # g2中没有对应的边
                    cost += edit_cost_edge_delete()
        
        for w_prime in neighbors_v:
            # 反向检查：g2有边但g1没有
            u_prime = [k for k, val in mapping.items() if val == w_prime][0]
            if u_prime not in neighbors_u:
                cost += edit_cost_edge_insert()
    
    return cost


def ged_exact(g1: Graph, g2: Graph) -> float:
    """
    精确GED计算（暴力搜索，适用于小图）
    
    参数:
        g1: 源图
        g2: 目标图
    
    返回:
        最小图编辑距离
    """
    n1, n2 = g1.n, g2.n
    
    # 使用动态规划思想：枚举所有可能的节点映射
    # 扩展映射允许多对一（通过插入dummy节点）
    # 这里使用BFS枚举
    
    max_nodes = max(n1, n2)
    
    # 状态：(映射列表, 当前代价)
    # 映射列表前n1个是g1到g2的映射（值-1表示删除，值>=n2表示插入的dummy）
    # 但为了简化，我们使用部分映射的BFS
    
    result = float('inf')
    
    def dfs(partial_map: Dict[int, int], remaining_budget: float):
        nonlocal result
        
        if len(partial_map) == n1:
            # 所有g1节点都已处理
            # 计算当前代价
            cost = compute_current_cost(g1, g2, partial_map)
            result = min(result, cost)
            return
        
        # 选择下一个要映射的g1节点
        for u in range(n1):
            if u not in partial_map:
                break
        
        # 尝试映射到g2的任意节点（包括删除）
        for v in range(-1, n2):  # -1表示删除节点u
            partial_map[u] = v
            cost_estimate = compute_current_cost(g1, g2, partial_map)
            if cost_estimate < result and cost_estimate <= remaining_budget:
                dfs(partial_map, remaining_budget)
            partial_map.pop(u)
    
    def compute_current_cost(g1: Graph, g2: Graph, partial_map: Dict[int, int]) -> float:
        """计算部分映射的当前代价上界"""
        cost = 0.0
        mapped_g2 = set(partial_map.values()) - {-1}
        
        # 节点代价
        for u, v in partial_map.items():
            if v == -1:
                cost += edit_cost_node_delete()
            else:
                cost += edit_cost_node_substitute(g1.labels[u], g2.labels[v])
        
        # 边的部分代价
        for u, v in partial_map.items():
            if v == -1:
                cost += len(g1.adj[u]) * edit_cost_edge_delete()
            else:
                for w in g1.adj[u]:
                    if w in partial_map:
                        w_prime = partial_map[w]
                        if w_prime != -1 and w_prime not in g2.adj[v]:
                            cost += edit_cost_edge_delete()
        
        return cost
    
    # 从初始上界开始搜索
    initial_bound = max(n1, n2) * 2  # 粗略上界
    dfs({}, initial_bound)
    
    return result if result != float('inf') else -1.0


def ged_approx(g1: Graph, g2: Graph, method: str = "greedy") -> float:
    """
    近似GED算法
    
    参数:
        g1: 源图
        g2: 目标图
        method: "greedy" 或 "hausdorff"
    
    返回:
        近似编辑距离
    """
    if method == "greedy":
        return _ged_greedy(g1, g2)
    elif method == "hausdorff":
        return _ged_hausdorff(g1, g2)
    else:
        raise ValueError(f"Unknown method: {method}")


def _ged_greedy(g1: Graph, g2: Graph) -> float:
    """贪婪近似算法"""
    n1, n2 = g1.n, g2.n
    
    # 初始化：所有节点未映射
    mapping = {}  # g1节点 -> g2节点
    unmapped_g1 = set(range(n1))
    unmapped_g2 = set(range(n2))
    cost = 0.0
    
    # 贪婪匹配：每次选择代价最小的映射
    while unmapped_g1 and unmapped_g2:
        best_cost = float('inf')
        best_u, best_v = None, None
        
        for u in unmapped_g1:
            for v in unmapped_g2:
                node_cost = edit_cost_node_substitute(g1.labels[u], g2.labels[v])
                if node_cost < best_cost:
                    best_cost = node_cost
                    best_u, best_v = u, v
        
        if best_u is not None:
            mapping[best_u] = best_v
            unmapped_g1.remove(best_u)
            unmapped_g2.remove(best_v)
            cost += best_cost
        else:
            break
    
    # 处理剩余未匹配节点
    cost += len(unmapped_g1) * edit_cost_node_delete()
    cost += len(unmapped_g2) * edit_cost_node_insert()
    
    # 计算边编辑代价
    cost += _compute_edge_cost(g1, g2, mapping)
    
    return cost


def _ged_hausdorff(g1: Graph, g2: Graph) -> float:
    """基于Hausdorff距离的近似"""
    # 计算节点替换代价矩阵
    n1, n2 = g1.n, g2.n
    cost_matrix = [[0.0] * n2 for _ in range(n1)]
    
    for i in range(n1):
        for j in range(n2):
            cost_matrix[i][j] = edit_cost_node_substitute(g1.labels[i], g2.labels[j])
    
    # 对于每个g1节点，找最近的g2节点
    hausdorff_1_2 = 0.0
    for i in range(n1):
        min_cost = min(cost_matrix[i])
        hausdorff_1_2 += min_cost
    
    # 对于每个g2节点，找最近的g1节点
    hausdorff_2_1 = 0.0
    for j in range(n2):
        min_cost = min(cost_matrix[i][j] for i in range(n1))
        hausdorff_2_1 += min_cost
    
    node_cost = max(hausdorff_1_2, hausdorff_2_1)
    
    # 边代价（简化估计）
    edge_cost = abs(len(g1.adj) - len(g2.adj))
    
    return node_cost + edge_cost


def _compute_edge_cost(g1: Graph, g2: Graph, mapping: Dict[int, int]) -> float:
    """计算边编辑代价"""
    cost = 0.0
    mapped_g2 = set(mapping.values())
    
    for u, v in mapping.items():
        # g1中u的邻居
        for w in g1.adj[u]:
            if w in mapping:
                w_prime = mapping[w]
                if w_prime not in g2.adj[v]:
                    cost += edit_cost_edge_delete()
        
        # g2中v的邻居
        for w_prime in g2.adj[v]:
            if w_prime in mapped_g2:
                u_prime = [k for k, val in mapping.items() if val == w_prime][0]
                if u_prime not in g1.adj[u]:
                    cost += edit_cost_edge_insert()
    
    return cost


if __name__ == "__main__":
    print("=== 图编辑距离测试 ===")
    
    # 测试1: 相同图
    g1 = Graph(3)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    
    g2 = Graph(3)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    
    print(f"相同图 GED = {ged_exact(g1, g2)}")
    
    # 测试2: 路径vs三角形
    g3 = Graph(3)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    
    g4 = Graph(3)
    g4.add_edge(0, 1)
    g4.add_edge(1, 2)
    g4.add_edge(2, 0)
    
    ged_val = ged_exact(g3, g4)
    print(f"路径 vs 三角形 (精确) GED = {ged_val}")
    
    ged_approx_val = ged_approx(g3, g4)
    print(f"路径 vs 三角形 (近似) GED = {ged_approx_val}")
    
    # 测试3: 简单图
    g5 = Graph(2)
    g5.add_edge(0, 1)
    
    g6 = Graph(2)
    # g6是隔离的两节点，无边
    
    ged_val2 = ged_exact(g5, g6)
    print(f"有边 vs 无边 (精确) GED = {ged_val2}")
    
    ged_approx_val2 = ged_approx(g5, g6)
    print(f"有边 vs 无边 (近似) GED = {ged_approx_val2}")
    
    # 测试4: 不同大小的图
    g7 = Graph(3)
    g7.add_edge(0, 1)
    g7.add_edge(1, 2)
    
    g8 = Graph(4)
    g8.add_edge(0, 1)
    g8.add_edge(1, 2)
    g8.add_edge(2, 3)
    
    result, mapping = a_star_ged(g7, g8)
    print(f"A* GED = {result}, 映射 = {mapping}")
    
    print("\n=== 测试完成 ===")

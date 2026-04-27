# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / graph_property_test

本文件实现 graph_property_test 相关的算法功能。
"""

import random
from typing import List, Dict, Set, Optional, Tuple, Callable
from collections import defaultdict


class GraphPropertyTester:
    """
    图性质测试器框架，支持多种图性质的次线性测试。
    
    属性:
        n: 图的顶点数量
        epsilon: 距离参数（ε-远离的阈值）
        neighbor_fn: 邻域查询函数，输入顶点返回其邻居列表
        degree_fn: 度查询函数，输入顶点返回其度数
        edge_fn: 边查询函数，输入两个顶点返回是否有边
    
    使用方式：
        tester = GraphPropertyTester(n=1000, epsilon=0.1, ...)
        is_close = tester.test_property(property_name, neighbor_fn, degree_fn)
    """
    
    def __init__(self, n: int, epsilon: float,
                 neighbor_fn: Optional[Callable[[int], List[int]]] = None,
                 degree_fn: Optional[Callable[[int], int]] = None,
                 edge_fn: Optional[Callable[[int, int], bool]] = None):
        # n: 图的顶点数
        self.n = n
        # epsilon: 相对误差参数，控制测试的精度
        self.epsilon = epsilon
        # neighbor_fn: 邻域查询函数
        self.neighbor_fn = neighbor_fn
        # degree_fn: 度查询函数
        self.degree_fn = degree_fn
        # edge_fn: 边查询函数
        self.edge_fn = edge_fn
        
        # 如果没有提供查询函数，则使用邻接表表示
        self._adj_list: Optional[Dict[int, Set[int]]] = None
        if neighbor_fn is None:
            self._adj_list = {}
    
    def set_graph_from_adjlist(self, adj_list: Dict[int, Set[int]]):
        """
        从邻接表设置图（用于测试）。
        
        参数:
            adj_list: 邻接表，键为顶点，值为邻居集合
        """
        self._adj_list = adj_list
        # 构建度查询和边查询的闭包
        self.degree_fn = lambda v: len(adj_list.get(v, set()))
        self.neighbor_fn = lambda v: list(adj_list.get(v, set()))
        self.edge_fn = lambda u, v: v in adj_list.get(u, set())
    
    def test_connectivity(self) -> bool:
        """
        测试图的连通性。
        
        查询复杂度：O(1/ε²) 次邻域查询
        是否 ε-远离连通性：如果图不连通，则需要 Ω(n) 条边才能变为连通
        
        返回:
            如果图 ε-接近连通返回 True，否则返回 False
        """
        # Goldreich-Goldwasser 的简化版本：采样 O(1/ε²) 个起始顶点
        # 从每个顶点做 BFS 深度 O(log n) 来检测大连通分量
        
        sample_size = int(12.0 / (self.epsilon ** 2))  # 采样数量
        visited_total: Set[int] = set()  # 累计访问过的顶点集合
        
        for _ in range(sample_size):
            start = random.randint(0, self.n - 1)  # 随机起始顶点
            
            # BFS 探索连通分量
            queue = [start]
            visited = {start}
            while queue:
                v = queue.pop(0)
                neighbors = self.neighbor_fn(v)
                for u in neighbors:
                    if u not in visited:
                        visited.add(u)
                        queue.append(u)
                        # 为防止查询过多，限制 BFS 深度
                        if len(visited) > 10 * len(self._adj_list) // sample_size:
                            break
                if len(visited) > 10 * len(self._adj_list) // sample_size:
                    break
            
            visited_total.update(visited)
        
        # 如果采样的顶点的连通分量覆盖了大部分顶点，则图接近连通
        coverage = len(visited_total) / self.n
        return coverage >= 1.0 - self.epsilon / 2
    
    def test_triangle_freeness(self) -> bool:
        """
        测试图是否不含三角形。
        
        查询复杂度：O(1/ε²) 次邻域查询
        算法：随机采样顶点，检查其两跳邻居是否形成边
        
        返回:
            如果图 ε-接近无三角形返回 True，否则返回 False
        """
        sample_size = int(6.0 / (self.epsilon ** 2))  # 采样顶点数量
        
        for _ in range(sample_size):
            v = random.randint(0, self.n - 1)  # 随机采样顶点
            neighbors_v = set(self.neighbor_fn(v))  # v 的一跳邻居集合
            
            if len(neighbors_v) < 2:
                continue  # 度小于 2 的顶点不可能参与三角形
            
            # 对 v 的每个邻居 u，检查 u 和 w 之间是否有边
            # 其中 w 也是 v 的邻居（两跳路径）
            neighbors_list = list(neighbors_v)
            # 采样最多 20 个邻居进行检查（节省查询）
            check_sample = min(20, len(neighbors_list))
            checked = random.sample(neighbors_list, check_sample)
            
            for u in checked:
                neighbors_u = set(self.neighbor_fn(u))  # u 的邻居集合
                # 找 v 和 u 的公共邻居（长度 2 的环）
                common = neighbors_v & neighbors_u
                for w in common:
                    if w != v and w != u:
                        # v-u-w 构成三角形（v 是中心顶点）
                        return False
        
        return True
    
    def test_bipartiteness(self, max_query: int = 100000) -> bool:
        """
        测试图是否为二分图（使用 Goldreich-Goldwasser 算法）。
        
        查询复杂度：O(Δ / ε²) 其中 Δ 是最大度
        
        参数:
            max_query: 最大查询次数限制，防止超时
        
        返回:
            如果图 ε-接近二分返回 True，否则返回 False
        """
        # 简化的随机分裂测试：
        # 反复随机将顶点染成红/蓝，检查是否存在单色边
        
        num_iterations = int(12.0 / (self.epsilon ** 2))  # 迭代次数
        query_count = 0  # 当前已使用的查询数
        
        for _ in range(num_iterations):
            # 随机为所有顶点分配颜色（简化：只分配采样顶点）
            color: Dict[int, int] = {}  # vertex -> {0=red, 1=blue}
            
            # 采样 O(n) 个顶点进行着色
            sample_size = int(6.0 / self.epsilon)
            sampled_vertices = random.sample(range(self.n), min(sample_size, self.n))
            
            for v in sampled_vertices:
                color[v] = random.randint(0, 1)  # 随机分配红或蓝
                query_count += 1
                
                if query_count > max_query:
                    return True  # 超时则保守返回
            
            # 检查采样的顶点之间是否有违规的单色边
            edges_checked = 0
            for v in sampled_vertices:
                neighbors_v = self.neighbor_fn(v)
                query_count += 1
                edges_checked += len(neighbors_v)
                
                if edges_checked > max_query:
                    break
                
                for u in neighbors_v:
                    if u in color and color[u] == color[v]:
                        # 发现单色边，说明不是二分图
                        return False
        
        return True
    
    def test_4cycle_freeness(self) -> bool:
        """
        测试图是否不含四边形（C4）。
        
        查询复杂度：O(n^{1/2} / ε²)（Alon-Krivelevich-Sudakov）
        
        算法思路：
        - 如果图中有很多四边形，则随机采样两条边 (u,v) 和 (w,x)，
          有较高概率能在中间顶点处相交
        - 通过采样和两跳邻居查询检测四边形的存在
        
        返回:
            如果图 ε-接近无四边形返回 True，否则返回 False
        """
        # 采样边的数量
        m_est = self.n * 10  # 估计的边数上界
        sample_edges = int(6.0 / (self.epsilon ** 2))  # 边采样数量
        
        edge_list: List[Tuple[int, int]] = []  # 采样的边列表
        
        for _ in range(sample_edges):
            # 随机选择一条边（通过随机顶点+随机邻居）
            v = random.randint(0, self.n - 1)  # 随机起始顶点
            neighbors = self.neighbor_fn(v)  # 查询 v 的邻居
            
            if len(neighbors) == 0:
                continue  # 孤立顶点跳过
            
            u = random.choice(neighbors)  # 随机选择一条边 (v,u)
            edge_list.append((min(v, u), max(v, u)))
        
        # 检测边列表中是否存在形成四边形的两条边
        # 四边形由两条平行的边组成：边 (a,b) 和 (c,d)，
        # 其中 a-c 和 b-d 都有边，且 a,b,c,d 两两不同
        
        for i, (a, b) in enumerate(edge_list):
            # 找与 (a,b) 有公共顶点但不等于 (a,b) 的边
            for c, d in edge_list[i+1:]:
                # 检查是否形成四边形
                # 情况1: a-c 和 b-d 都有边，且 a,b,c,d 不同
                # 情况2: a-d 和 b-c 都有边
                
                if {a, b} & {c, d}:
                    # 共享顶点，只能形成三角形
                    continue
                
                # 检查 a-c 边
                if self.edge_fn(a, c):
                    # 检查 b-d 边
                    if self.edge_fn(b, d):
                        return False  # 发现 C4
                
                # 检查 a-d 边
                if self.edge_fn(a, d):
                    # 检查 b-c 边
                    if self.edge_fn(b, c):
                        return False  # 发现 C4
        
        return True
    
    def test_degree_regularity(self) -> bool:
        """
        测试图是否为度正则的（所有顶点度相同）。
        
        查询复杂度：O(n^{1/2})（需要采样约 n^{1/2} 个顶点）
        
        返回:
            如果图 ε-接近度正则返回 True，否则返回 False
        """
        # 采样足够多的顶点来估计度分布
        sample_size = int(6.0 / (self.epsilon ** 2))
        degrees: List[int] = []  # 采样顶点的度列表
        
        for _ in range(sample_size):
            v = random.randint(0, self.n - 1)
            d = self.degree_fn(v)
            degrees.append(d)
        
        # 检查度的方差
        avg_degree = sum(degrees) / len(degrees)
        variance = sum((d - avg_degree) ** 2 for d in degrees) / len(degrees)
        
        # 如果方差过大，说明不是正则的
        # 正则图的方差应该为 0
        return variance <= (avg_degree ** 2) * self.epsilon


def goldreich_goldwasser_tester(adj_list: Dict[int, Set[int]], 
                                property_type: str,
                                epsilon: float = 0.1) -> bool:
    """
    Goldreich-Goldwasser 测试器的便捷包装函数。
    
    参数:
        adj_list: 图的邻接表表示
        property_type: 性质类型（'connectivity', 'triangle', 'bipartite', '4cycle'）
        epsilon: 距离参数
    
    返回:
        如果图 ε-接近指定性质返回 True，否则返回 False
    """
    n = max(adj_list.keys()) + 1 if adj_list else 0
    tester = GraphPropertyTester(n, epsilon)
    tester.set_graph_from_adjlist(adj_list)
    
    if property_type == 'connectivity':
        return tester.test_connectivity()
    elif property_type == 'triangle':
        return tester.test_triangle_freeness()
    elif property_type == 'bipartite':
        return tester.test_bipartiteness()
    elif property_type == '4cycle':
        return tester.test_4cycle_freeness()
    elif property_type == 'regular':
        return tester.test_degree_regularity()
    else:
        raise ValueError(f"Unknown property type: {property_type}")


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("图性质次线性测试 — 测试套件")
    print("=" * 60)
    
    # 测试 1：连通性测试
    print("\n[测试 1] 连通性测试")
    
    # 完全图（连通）
    complete_graph: Dict[int, Set[int]] = {i: set(range(i)) | set(range(i+1, 10)) for i in range(10)}
    result = goldreich_goldwasser_tester(complete_graph, 'connectivity', epsilon=0.1)
    print(f"  完全图 K_10: ε-连通 = {result}")
    
    # 断开连接的图
    disconnected_graph: Dict[int, Set[int]] = {i: set() for i in range(10)}
    for i in range(5):
        disconnected_graph[i].add(i + 5)
        disconnected_graph[i + 5].add(i)
    
    result = goldreich_goldwasser_tester(disconnected_graph, 'connectivity', epsilon=0.1)
    print(f"  两分图（断开）: ε-连通 = {result}")
    
    # 测试 2：三角形测试
    print("\n[测试 2] 三角形检测")
    
    # 完全图 K_5（包含大量三角形）
    k5: Dict[int, Set[int]] = {i: set(range(5)) - {i} for i in range(5)}
    result = goldreich_goldwasser_tester(k5, 'triangle', epsilon=0.1)
    print(f"  K_5（含三角形）: 无三角形 = {result}")
    
    # 空图（无三角形）
    empty: Dict[int, Set[int]] = {i: set() for i in range(20)}
    result = goldreich_goldwasser_tester(empty, 'triangle', epsilon=0.1)
    print(f"  空图（无三角形）: 无三角形 = {result}")
    
    # 测试 3：二分性测试
    print("\n[测试 3] 二分性测试")
    
    # 偶环（是二分图）
    n = 8
    cycle_graph: Dict[int, Set[int]] = {i: {(i-1) % n, (i+1) % n} for i in range(n)}
    result = goldreich_goldwasser_tester(cycle_graph, 'bipartite', epsilon=0.1)
    print(f"  8-环（二分）: ε-二分 = {result}")
    
    # 三角形（不是二分图）
    triangle: Dict[int, Set[int]] = {0: {1, 2}, 1: {0, 2}, 2: {0, 1}}
    result = goldreich_goldwasser_tester(triangle, 'bipartite', epsilon=0.1)
    print(f"  三角形（非二分）: ε-二分 = {result}")
    
    # 测试 4：四边形测试
    print("\n[测试 4] 四边形（C4）测试")
    
    # 完整二分图 K_{3,3}（包含多个四边形）
    k33: Dict[int, Set[int]] = {}
    for i in range(3):
        k33[i] = {j + 3 for j in range(3)}
    for j in range(3, 6):
        k33[j] = {i for i in range(3)}
    result = goldreich_goldwasser_tester(k33, '4cycle', epsilon=0.1)
    print(f"  K_{{3,3}}（含四边形）: 无四边形 = {result}")
    
    # 星图（无四边形）
    star: Dict[int, Set[int]] = {0: {1, 2, 3, 4}}
    for i in range(1, 5):
        star[i] = {0}
    result = goldreich_goldwasser_tester(star, '4cycle', epsilon=0.1)
    print(f"  星图（无四边形）: 无四边形 = {result}")
    
    # 测试 5：度正则性测试
    print("\n[测试 5] 度正则性测试")
    
    # 3-正则图（完全三分图 K_{5,5,5} 是 10-正则的，用简单的例子）
    n_reg = 6
    regular_graph: Dict[int, Set[int]] = {i: set((j for j in range(n_reg) if j != i)) for i in range(n_reg)}
    result = goldreich_goldwasser_tester(regular_graph, 'regular', epsilon=0.1)
    print(f"  完全图 K_6（5-正则）: ε-正则 = {result}")
    
    # 非正则图
    irregular: Dict[int, Set[int]] = {
        0: {1, 2},
        1: {0, 2, 3},
        2: {0, 1},
        3: {1}
    }
    result = goldreich_goldwasser_tester(irregular, 'regular', epsilon=0.1)
    print(f"  非正则图: ε-正则 = {result}")
    
    print("\n" + "=" * 60)
    print("图性质测试完成")
    print("=" * 60)

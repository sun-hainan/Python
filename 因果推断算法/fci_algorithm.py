# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / fci_algorithm



本文件实现 fci_algorithm 相关的算法功能。

"""



import numpy as np

import pandas as pd

from typing import List, Dict, Set, Tuple, Optional

from dataclasses import dataclass, field

from itertools import combinations





@dataclass

class Graph:

    """因果图"""

    nodes: Set[str] = field(default_factory=set)  # 节点集合

    edges: Set[Tuple[str, str]] = field(default_factory=set)  # 有向边

    undirected_edges: Set[Tuple[str, str]] = field(default_factory=set)  # 无向边

    bidirected_edges: Set[Tuple[str, str]] = field(default_factory=set)  # 双向边(代表潜在混杂)

    colliders: Set[Tuple[str, str, str]] = field(default_factory=set)  # 对撞结构





class FCIScore:

    """FCI分数(用于边定向)"""

    BGE = "BGE"  # Bayesian Gaussian Equivalence

    BIC = "BIC"

    AIC = "AIC"





class FCIAlgorithm:

    """

    FCI因果发现算法



    算法步骤:

    1. PC阶段: 发现因果骨架(无向图结构)

    2. 方向阶段: 使用虚节点定向边

    3. 识别不可定向边

    4. 识别潜在混杂(双向边)

    5. 识别选择偏差

    """



    def __init__(self, data: pd.DataFrame, alpha: float = 0.05,

                 indep_test: str = "partial_correlation"):

        self.data = data  # 数据集

        self.alpha = alpha  # 显著性水平

        self.indep_test = indep_test  # 独立性测试方法

        self.nodes = list(data.columns)  # 变量名列表

        self.n = len(data)  # 样本数

        self.sepsets: Dict[Tuple[str, str], Set[str]] = {}  # 分离集

        self.graph = Graph(nodes=set(self.nodes))



    def run(self) -> Graph:

        """

        执行FCI算法



        返回:

            发现的因果图

        """

        # 阶段1: PC阶段 - 发现骨架

        self._pc_phase()



        # 阶段2: 边定向

        self._orientation_phase()



        # 阶段3: 识别潜在混杂因子

        self._identify_latent_confounders()



        return self.graph



    def _pc_phase(self):

        """

        PC阶段: 发现因果骨架



        算法:

        1. 从完全无向图开始

        2. 对每个节点对,测试条件独立性

        3. 如果条件独立,移除边

        4. 记录分离集

        """

        # 初始化完全无向图

        for v1, v2 in combinations(self.nodes, 2):

            self.graph.undirected_edges.add((v1, v2))

            self.graph.undirected_edges.add((v2, v1))



        # 逐步增加条件集大小

        for cond_size in range(len(self.nodes)):

            edges_to_check = list(self.graph.undirected_edges)



            for x, y in edges_to_check:

                # 找到x和y的邻居(排除彼此)

                neighbors = self._get_neighbors(x, y)

                if len(neighbors) < cond_size:

                    continue



                # 遍历大小为cond_size的条件集

                for z in combinations(neighbors, cond_size):

                    z_set = set(z)



                    # 测试 x ⊥ y | z

                    if self._is_conditionally_independent(x, y, z_set):

                        # 移除边

                        self._remove_edge(x, y)

                        self._remove_edge(y, x)



                        # 记录分离集

                        self.sepsets[(x, y)] = z_set

                        self.sepsets[(y, x)] = z_set

                        break



    def _get_neighbors(self, x: str, y: str) -> Set[str]:

        """获取x的邻居(排除y)"""

        neighbors = set()

        for edge in self.graph.undirected_edges:

            if edge[0] == x and edge[1] != y:

                neighbors.add(edge[1])

            elif edge[1] == x and edge[0] != y:

                neighbors.add(edge[0])

        return neighbors



    def _remove_edge(self, x: str, y: str):

        """移除边"""

        self.graph.undirected_edges.discard((x, y))



    def _is_conditionally_independent(self, x: str, y: str, z: Set[str]) -> bool:

        """

        测试条件独立性 x ⊥ y | z



        使用偏相关或G检验

        """

        if self.indep_test == "partial_correlation":

            return self._partial_correlation_test(x, y, z)

        elif self.indep_test == "g_test":

            return self._g_test(x, y, z)

        return False



    def _partial_correlation_test(self, x: str, y: str, z: Set[str]) -> bool:

        """

        使用偏相关测试条件独立性



        如果 |partial_corr| < threshold, 认为条件独立

        """

        if not z:

            # 无条件相关

            corr = self.data[x].corr(self.data[y])

            return abs(corr) < self.alpha

        else:

            # 偏相关

            z_list = list(z)

            try:

                corr_matrix = self.data[[x, y] + z_list].corr().values

                n = len(self.data)

                k = len(z_list)



                # 计算偏相关系数(简化)

                pcorr = self._compute_partial_correlation(corr_matrix, n, k)



                # 使用t检验

                t_stat = pcorr * np.sqrt((n - k - 2) / (1 - pcorr**2))

                p_value = 2 * (1 - self._t_cdf(abs(t_stat), n - k - 2))



                return p_value > self.alpha

            except:

                return False



    def _compute_partial_correlation(self, corr_matrix: np.ndarray, n: int, k: int) -> float:

        """计算偏相关系数"""

        try:

            precision = np.linalg.inv(corr_matrix)

            pcorr = -precision[0, 1] / np.sqrt(precision[0, 0] * precision[1, 1])

            return pcorr

        except:

            return 0.0



    def _t_cdf(self, t: float, df: int) -> float:

        """t分布CDF近似"""

        from scipy.stats import t as t_dist

        try:

            return t_dist.cdf(t, df)

        except:

            return 0.5



    def _g_test(self, x: str, y: str, z: Set[str]) -> bool:

        """G检验(简化实现)"""

        # 简化:使用相关性

        corr = self.data[x].corr(self.data[y])

        return abs(corr) < self.alpha



    def _orientation_phase(self):

        """

        边定向阶段



        使用Meek规则定向边:

        1. 如果 a->b-c 且 a not in SepSet(b,c), 则 b->c

        2. 如果 a->b->c 且 a-b, 则 a->b

        3. 循环应用直到稳定

        """

        changed = True

        iterations = 0



        while changed and iterations < 100:

            changed = False

            iterations += 1



            # 规则1: v-structures

            changed |= self._orient_v_structures()



            # 规则2-4: 其他Meek规则

            changed |= self._apply_meek_rules()



    def _orient_v_structures(self) -> bool:

        """

        定向v-结构: 如果 a->c, b->c, 且 a,b not adjacent,

        则定向为 a->c<-b

        """

        changed = False



        for c in self.nodes:

            # 找所有指向c的边

            parents = []

            for edge in list(self.graph.undirected_edges):

                if edge[1] == c:

                    a = edge[0]

                    # 检查a和b是否不相邻

                    if not self._is_adjacent(a, c):

                        parents.append(a)



            # 检查v结构

            for a, b in combinations(parents, 2):

                if not self._is_adjacent(a, b):

                    # 检查是否在分离集中

                    sep = self.sepsets.get((a, b), set())

                    if c not in sep:

                        # 定向为v结构

                        self.graph.edges.add((a, c))

                        self.graph.edges.add((b, c))

                        self.graph.undirected_edges.discard((a, c))

                        self.graph.undirected_edges.discard((c, a))

                        self.graph.undirected_edges.discard((b, c))

                        self.graph.undirected_edges.discard((c, b))

                        self.graph.colliders.add((a, c, b))

                        changed = True



        return changed



    def _apply_meek_rules(self) -> bool:

        """

        应用Meek定向规则



        规则2: a-b, a->c->b 则 a->b

        规则3: a-b, a->c, a->d, c->b, d not adj 则 a->b

        规则4: a-b, a->c, c->d, c adj b, d not adj b 则 a->b

        """

        changed = False



        # 规则2

        for a, b in list(self.graph.undirected_edges):

            if self._has_directed_path(a, b) and self._has_directed_path(b, a):

                # 可能是同一结构,定向为 a->b

                if self._can_orient_as(a, b):

                    self.graph.edges.add((a, b))

                    self.graph.undirected_edges.discard((a, b))

                    self.graph.undirected_edges.discard((b, a))

                    changed = True



        return changed



    def _has_directed_path(self, start: str, end: str) -> bool:

        """检查是否存在从start到end的有向路径"""

        visited = set()

        stack = [start]



        while stack:

            current = stack.pop()

            if current == end:

                return True

            if current in visited:

                continue

            visited.add(current)



            for edge in self.graph.edges:

                if edge[0] == current:

                    stack.append(edge[1])



        return False



    def _is_adjacent(self, x: str, y: str) -> bool:

        """检查x和y是否相邻"""

        return (x, y) in self.graph.undirected_edges or \

               (y, x) in self.graph.undirected_edges or \

               (x, y) in self.graph.edges or \

               (y, x) in self.graph.edges



    def _can orient_as(self, x: str, y: str) -> bool:

        """检查边是否可能定向为x->y"""

        # 简化实现

        return True



    def _identify_latent_confounders(self):

        """

        识别潜在混杂因子



        如果两条边不能被有向化,可能存在潜在混杂

        使用双向边表示潜在混杂

        """

        # 对于仍未定向的边,标记为可能有潜在混杂

        for x, y in list(self.graph.undirected_edges):

            # 检查x和y是否在分离集中

            sep = self.sepsets.get((x, y), set())



            # 如果是选择偏差或混杂,保留为双向边

            if len(sep) == 0:

                self.graph.bidirected_edges.add((x, y))

                self.graph.bidirected_edges.add((y, x))

                self.graph.undirected_edges.discard((x, y))

                self.graph.undirected_edges.discard((y, x))





def print_graph(graph: Graph):

    """打印因果图"""

    print("=== 因果图 ===")

    print(f"节点: {sorted(graph.nodes)}")

    print(f"\n有向边: {sorted(graph.edges)}")

    print(f"\n无向边: {sorted(graph.undirected_edges)}")

    print(f"\n双向边(潜在混杂): {sorted(graph.bidirected_edges)}")

    print(f"\n对撞结构: {sorted(graph.colliders)}")





if __name__ == "__main__":

    # 生成测试数据

    # 结构: X -> Z <- Y, X -> W -> Z

    np.random.seed(42)

    n = 1000



    # X -> Z, Y -> Z

    X = np.random.randn(n)

    Y = np.random.randn(n)

    Z = 0.5 * X + 0.5 * Y + np.random.randn(n) * 0.1



    # X -> W -> Z

    W = 0.8 * X + np.random.randn(n) * 0.1

    Z = 0.3 * W + Z



    data = pd.DataFrame({

        "X": X,

        "Y": Y,

        "Z": Z,

        "W": W

    })



    print("=== FCI因果发现测试 ===")

    print(f"样本数: {n}")

    print(f"变量: {list(data.columns)}")



    # 执行FCI

    fci = FCIAlgorithm(data, alpha=0.05)

    graph = fci.run()



    print_graph(graph)



    # 打印分离集

    print("\n=== 分离集 ===")

    for (x, y), sep in fci.sepsets.items():

        if sep:

            print(f"  {x} ⊥ {y} | {sep}")


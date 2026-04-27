# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / causal_discovery_local

本文件实现 causal_discovery_local 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Set, Tuple, Optional, Callable
from dataclasses import dataclass, field
from itertools import combinations, permutations
from scipy.stats import chi2, pearsonr
import networkx as nx


@dataclass
class CausalGraph:
    """因果图"""
    nodes: List[str]  # 节点列表
    edges: Set[Tuple[str, str]] = field(default_factory=set)  # 有向边
    undirected: Set[Tuple[str, str]] = field(default_factory=set)  # 无向边
    bidirected: Set[Tuple[str, str]] = field(default_factory=set)  # 双向边(潜在混杂)
    separation_sets: Dict[Tuple[str, str], Set[str]] = field(default_factory=dict)  # 分离集


class PCAlgorithm:
    """
    PC算法 - 经典因果发现算法

    算法步骤:
    1. 从完全无向图开始
    2. 逐步删除可条件独立的边
    3. 使用条件独立性定向边
    4. 使用v-结构识别定向边

    假设: 因果充分性(无隐藏混杂)
    """

    def __init__(self, alpha: float = 0.05, indep_test: str = "partial_correlation"):
        self.alpha = alpha
        self.indep_test = indep_test
        self.graph = None
        self.sep_sets: Dict[Tuple[str, str], Set[str]] = {}

    def discover(self, data: pd.DataFrame) -> CausalGraph:
        """
        从数据发现因果结构

        参数:
            data: 数据框,列名为变量名

        返回:
            CausalGraph
        """
        nodes = list(data.columns)
        n = len(data)

        # 阶段1: 构建骨架
        skeleton = self._build_skeleton(nodes, data)

        # 阶段2: 定向边
        cpdag = self._orient_edges(nodes, skeleton, data)

        # 构建结果图
        result = CausalGraph(
            nodes=nodes,
            edges=cpdag["directed"],
            undirected=cpdag["undirected"],
            separation_sets=self.sep_sets
        )

        self.graph = result
        return result

    def _build_skeleton(self, nodes: List[str], data: pd.DataFrame) -> Dict[Tuple[str, str], bool]:
        """
        构建因果骨架(无向图)

        返回:
            边表 {(x,y): 是否相邻}
        """
        # 初始化完全图
        adj = {}
        for x, y in combinations(nodes, 2):
            adj[(x, y)] = True
            adj[(y, x)] = True

        # 逐步增加条件集大小
        for cond_size in range(len(nodes)):
            for x, y in combinations(nodes, 2):
                if not adj.get((x, y), False):
                    continue

                # 获取x的邻居(排除y)
                neighbors = [z for z in nodes if adj.get((x, z), False) and z != y]

                if len(neighbors) < cond_size:
                    continue

                # 遍历条件集
                for z_set in combinations(neighbors, cond_size):
                    z_set = set(z_set)

                    # 测试 x ⊥ y | z_set
                    if self._is_independent(x, y, z_set, data):
                        adj[(x, y)] = False
                        adj[(y, x)] = False

                        # 记录分离集
                        self.sep_sets[(x, y)] = z_set
                        self.sep_sets[(y, x)] = z_set
                        break

        return adj

    def _is_independent(self, x: str, y: str, z_set: Set[str], data: pd.DataFrame) -> bool:
        """测试条件独立性"""
        if self.indep_test == "partial_correlation":
            return self._partial_corr_test(x, y, z_set, data)
        elif self.indep_test == "chi2":
            return self._chi2_test(x, y, z_set, data)
        return False

    def _partial_corr_test(self, x: str, y: str, z_set: Set[str], data: pd.DataFrame) -> bool:
        """偏相关独立性检验"""
        if not z_set:
            # 无条件相关
            corr, p_value = pearsonr(data[x], data[y])
            return p_value > self.alpha
        else:
            # 偏相关
            try:
                z_list = list(z_set)
                all_cols = [x, y] + z_list
                corr_matrix = data[all_cols].corr().values

                # 计算偏相关
                precision = np.linalg.inv(corr_matrix)
                pcorr = -precision[0, 1] / np.sqrt(precision[0, 0] * precision[1, 1])

                n = len(data)
                k = len(z_set)
                df = n - k - 2
                t_stat = pcorr * np.sqrt(df / (1 - pcorr**2))
                p_value = 2 * (1 - chi2.cdf(abs(t_stat), df))

                return p_value > self.alpha
            except:
                return False

    def _chi2_test(self, x: str, y: str, z_set: Set[str], data: pd.DataFrame) -> bool:
        """卡方独立性检验(离散数据)"""
        from scipy.stats import chi2_contingency

        try:
            if not z_set:
                # 列联表
                table = pd.crosstab(data[x], data[y])
                chi2_stat, p_value, dof, expected = chi2_contingency(table)
                return p_value > self.alpha
            else:
                # 条件独立性,简化处理
                return self._partial_corr_test(x, y, z_set, data)
        except:
            return False

    def _orient_edges(self, nodes: List[str], adj: Dict, data: pd.DataFrame) -> Dict:
        """
        定向边

        规则:
        1. v-结构: a->c<-b, 且a,b不相邻,c不在sep(a,b)
        2. 避免新v-结构
        3. 其他用Meek规则
        """
        directed = set()
        undirected = set()

        # 添加所有保留的边到undirected
        for (x, y), connected in adj.items():
            if connected and (x, y) not in directed and (y, x) not in directed:
                undirected.add((x, y))

        # 定向v-结构
        for x, y in combinations(nodes, 2):
            if not adj.get((x, y), False):
                continue

            # 找共同邻居
            for z in nodes:
                if z == x or z == y:
                    continue
                if not (adj.get((x, z), False) and adj.get((y, z), False)):
                    continue

                # 检查z不在sep(x,y)
                sep = self.sep_sets.get((x, y), set())
                if z not in sep:
                    # v-结构: x -> z <- y
                    directed.add((x, z))
                    directed.add((y, z))
                    undirected.discard((x, z))
                    undirected.discard((z, x))
                    undirected.discard((y, z))
                    undirected.discard((z, y))

        # Meek规则定向
        changed = True
        while changed:
            changed = False

            for x, y in list(undirected):
                # 规则: 如果 a->b, b-c, a not adj c, 则 b->c
                for a in nodes:
                    if a == x or a == y:
                        continue
                    if (a, x) in directed and (y, x) in undirected:
                        if not adj.get((a, y), False):
                            directed.add((x, y))
                            undirected.discard((x, y))
                            undirected.discard((y, x))
                            changed = True

        return {"directed": directed, "undirected": undirected}


def plot_causal_graph(graph: CausalGraph):
    """可视化因果图(文本版)"""
    print("=== 因果图 ===")
    print(f"节点: {graph.nodes}")

    print("\n有向边:")
    for e in sorted(graph.edges):
        print(f"  {e[0]} -> {e[1]}")

    print("\n无向边:")
    for e in sorted(graph.undirected):
        print(f"  {e[0]} -- {e[1]}")


def compare_causal_structures(true_edges: Set, estimated_edges: Set) -> Dict:
    """比较因果结构"""
    true_directed = {(a, b) for a, b in true_edges if "->" in str(a)}
    # 简化比较

    tp = len(true_directed & estimated_edges)
    fp = len(estimated_edges - true_directed)
    fn = len(true_directed - estimated_edges)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "shd": len(true_directed ^ estimated_edges)  # 结构汉明距离
    }


if __name__ == "__main__":
    # 生成测试数据: X -> Y <- Z, X -> W -> Y
    np.random.seed(42)
    n = 500

    X = np.random.randn(n)
    Z = np.random.randn(n)
    W = 0.5 * X + np.random.randn(n) * 0.2
    Y = 0.5 * X + 0.5 * Z + 0.3 * W + np.random.randn(n) * 0.1

    data = pd.DataFrame({
        "X": X,
        "Y": Y,
        "Z": Z,
        "W": W
    })

    print("=== PC算法因果发现 ===")
    print(f"样本数: {n}")
    print(f"变量: {list(data.columns)}")

    # 执行PC算法
    pc = PCAlgorithm(alpha=0.05)
    graph = pc.discover(data)

    plot_causal_graph(graph)

    # 分离集
    print("\n分离集:")
    for (x, y), sep in pc.sep_sets.items():
        if sep:
            print(f"  {x} ⊥ {y} | {sep}")

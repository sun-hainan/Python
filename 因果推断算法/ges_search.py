# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / ges_search

本文件实现 ges_search 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from itertools import combinations
import copy


@dataclass
class CPDAG:
    """完全部分有向无环图(CPDAG)"""
    nodes: Set[str]  # 节点集合
    directed_edges: Set[Tuple[str, str]]  # 有向边
    undirected_edges: Set[Tuple[str, str]]  # 无向边

    def add_directed(self, x: str, y: str):
        """添加有向边 x -> y"""
        self.directed_edges.add((x, y))
        # 如果存在无向边,移除
        self.undirected_edges.discard((x, y))
        self.undirected_edges.discard((y, x))

    def add_undirected(self, x: str, y: str):
        """添加无向边 x - y"""
        self.undirected_edges.add((x, y))
        self.undirected_edges.add((y, x))

    def is_directed(self, x: str, y: str) -> bool:
        """检查是否有边 x -> y"""
        return (x, y) in self.directed_edges

    def is_adjacent(self, x: str, y: str) -> bool:
        """检查x和y是否相邻"""
        return (x, y) in self.directed_edges or \
               (y, x) in self.directed_edges or \
               (x, y) in self.undirected_edges or \
               (y, x) in self.undirected_edges


class ScoreFunction:
    """评分函数基类"""

    def score(self, data: pd.DataFrame, graph: CPDAG) -> float:
        """计算图的分数"""
        raise NotImplementedError


class BICScore(ScoreFunction):
    """BIC评分函数"""

    def __init__(self, lambda_pen: float = 1.0):
        self.lambda_pen = lambda_pen

    def score(self, data: pd.DataFrame, graph: CPDAG) -> float:
        """
        计算BIC分数

        BIC = log_likelihood - (d/2) * log(n)
        """
        n = len(data)
        log_lik = self._log_likelihood(data, graph)
        d = self._count_parameters(graph, data)
        bic = log_lik - (d / 2) * np.log(n)
        return bic

    def _log_likelihood(self, data: pd.DataFrame, graph: CPDAG) -> float:
        """计算对数似然"""
        ll = 0.0
        for var in graph.nodes:
            parents = self._get_parents(var, graph)
            ll += self._local_score(data, var, parents)
        return ll

    def _get_parents(self, node: str, graph: CPDAG) -> Set[str]:
        """获取节点的父节点"""
        parents = set()
        for edge in graph.directed_edges:
            if edge[1] == node:
                parents.add(edge[0])
        return parents

    def _local_score(self, data: pd.DataFrame, node: str, parents: Set[str]) -> float:
        """
        计算局部BIC分数

        假设线性高斯模型
        """
        if not parents:
            # 无父节点: 仅基于方差
            var = data[node].var()
            return -len(data) / 2 * np.log(var + 1e-10)
        else:
            # 有父节点: 线性回归
            parent_list = list(parents)
            X = data[parent_list].values
            y = data[node].values

            # 线性回归拟合
            try:
                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                y_pred = X @ coef
                residual_var = np.var(y - y_pred) + 1e-10

                n = len(y)
                d = len(parents) + 1
                sigma2 = residual_var

                score = -n / 2 * np.log(sigma2) - d * self.lambda_pen / 2 * np.log(n)
                return score
            except:
                return -1e10

    def _count_parameters(self, graph: CPDAG, data: pd.DataFrame) -> int:
        """计算参数数量"""
        count = 0
        for node in graph.nodes:
            parents = self._get_parents(node, graph)
            count += len(parents) + 1  # 父节点系数 + 截距 + 方差
        return count


class GESSearch:
    """
    GES贪婪等价搜索算法

    算法:
    1. 从空图开始
    2. 贪婪添加边,直到分数不再增加
    3. 贪婪删除边,直到分数不再增加
    4. 返回CPDAG
    """

    def __init__(self, data: pd.DataFrame, score: ScoreFunction = None):
        self.data = data
        self.nodes = set(data.columns)
        self.score_func = score or BICScore()
        self.current_score = 0.0
        self.history: List[float] = []

    def search(self, max_iterations: int = 100) -> CPDAG:
        """
        执行GES搜索

        返回:
            CPDAG(完全部分有向无环图)
        """
        # 阶段1: 贪婪添加
        cpdag = self._greedy_insert()

        # 阶段2: 贪婪删除
        cpdag = self._greedy_delete(cpdag)

        return cpdag

    def _greedy_insert(self) -> CPDAG:
        """贪婪添加边"""
        # 初始化为空图
        cpdag = CPDAG(nodes=self.nodes, directed_edges=set(), undirected_edges=set())
        self.current_score = self.score_func.score(self.data, cpdag)

        improved = True
        iterations = 0

        while improved and iterations < 100:
            improved = False
            iterations += 1

            best_delta = 0.0
            best_edge = None
            best_orientation = None

            # 遍历所有可能的边添加
            for x, y in combinations(self.nodes, 2):
                if cpdag.is_adjacent(x, y):
                    continue

                # 尝试 x -> y
                delta_forward = self._insert_delta(x, y, cpdag)
                if delta_forward > best_delta:
                    best_delta = delta_forward
                    best_edge = (x, y)
                    best_orientation = "forward"

                # 尝试 y -> x
                delta_backward = self._insert_delta(y, x, cpdag)
                if delta_backward > best_delta:
                    best_delta = delta_backward
                    best_edge = (x, y)
                    best_orientation = "backward"

            # 如果有改进,添加边
            if best_delta > 0 and best_edge:
                x, y = best_edge
                if best_orientation == "forward":
                    cpdag.add_directed(x, y)
                else:
                    cpdag.add_directed(y, x)
                self.current_score += best_delta
                improved = True
                self.history.append(self.current_score)

        return cpdag

    def _insert_delta(self, x: str, y: str, cpdag: CPDAG) -> float:
        """
        计算添加边 x -> y 的分数增益

        使用局部评分和v-structures检查
        """
        # 获取x的父节点,y的父节点
        x_parents = self._get_parents(x, cpdag)
        y_parents = self._get_parents(y, cpdag)

        # 检查是否会创建新的v-structure
        # 如果添加 x -> y,且存在 z -> x 和 z -> y,可能会改变结构

        # 计算新分数
        old_parents_y = y_parents.copy()
        new_parents_y = y_parents | {x}

        old_score = self._local_score(y, old_parents_y)
        new_score = self._local_score(y, new_parents_y)

        delta = new_score - old_score

        # 检查v-structure冲突
        # 如果 x 没有父节点,且存在 z 同时指向 x 和 y,可能需要调整
        if not x_parents:
            for z in self.nodes:
                if z != x and z != y:
                    if self._points_to(x, z, cpdag) and self._points_to(y, z, cpdag):
                        # 可能存在v-structure冲突
                        # 需要更复杂的检查
                        pass

        return delta

    def _get_parents(self, node: str, cpdag: CPDAG) -> Set[str]:
        """获取节点的父节点"""
        parents = set()
        for edge in cpdag.directed_edges:
            if edge[1] == node:
                parents.add(edge[0])
        return parents

    def _points_to(self, target: str, source: str, cpdag: CPDAG) -> bool:
        """检查是否存在从source到target的有向路径"""
        visited = set()
        stack = [source]

        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)

            for edge in cpdag.directed_edges:
                if edge[0] == current:
                    stack.append(edge[1])

        return False

    def _local_score(self, node: str, parents: Set[str]) -> float:
        """计算局部分数"""
        if not parents:
            var = self.data[node].var()
            return -len(self.data) / 2 * np.log(var + 1e-10)
        else:
            parent_list = list(parents)
            X = self.data[parent_list].values
            y = self.data[node].values

            try:
                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                y_pred = X @ coef
                residual_var = np.var(y - y_pred) + 1e-10
                n = len(y)
                d = len(parents) + 1
                return -n / 2 * np.log(residual_var) - d / 2 * np.log(n)
            except:
                return -1e10

    def _greedy_delete(self, cpdag: CPDAG) -> CPDAG:
        """贪婪删除边"""
        improved = True
        iterations = 0

        while improved and iterations < 100:
            improved = False
            iterations += 1

            best_delta = 0.0
            best_edge = None

            # 遍历所有有向边
            for x, y in list(cpdag.directed_edges):
                delta = self._delete_delta(x, y, cpdag)
                if delta > best_delta:
                    best_delta = delta
                    best_edge = (x, y)

            # 如果有改进,删除边
            if best_delta > 0 and best_edge:
                x, y = best_edge
                cpdag.directed_edges.discard((x, y))
                cpdag.add_undirected(x, y)
                self.current_score += best_delta
                improved = True
                self.history.append(self.current_score)

        return cpdag

    def _delete_delta(self, x: str, y: str, cpdag: CPDAG) -> float:
        """计算删除边 x -> y 的分数增益"""
        y_parents = self._get_parents(y, cpdag)
        old_parents = y_parents.copy()
        new_parents = y_parents - {x}

        old_score = self._local_score(y, old_parents)
        new_score = self._local_score(y, new_parents)

        return new_score - old_score


def print_cpdag(cpdag: CPDAG):
    """打印CPDAG"""
    print("=== CPDAG ===")
    print(f"节点: {sorted(cpdag.nodes)}")
    print(f"\n有向边: {sorted(cpdag.directed_edges)}")
    print(f"\n无向边: {sorted(cpdag.undirected_edges)}")


if __name__ == "__main__":
    # 生成测试数据: X -> Y -> Z
    np.random.seed(42)
    n = 1000

    X = np.random.randn(n)
    Y = 0.5 * X + np.random.randn(n) * 0.2
    Z = 0.5 * Y + np.random.randn(n) * 0.2

    data = pd.DataFrame({"X": X, "Y": Y, "Z": Z})

    print("=== GES因果发现测试 ===")
    print(f"样本数: {n}")
    print(f"变量: {list(data.columns)}")

    # 执行GES
    ges = GESSearch(data, BICScore())
    cpdag = ges.search()

    print_cpdag(cpdag)

    # 打印分数历史
    print(f"\n分数历史: {ges.history}")

    # 测试另一个结构: X <- Z -> Y (X和Y无直接边)
    print("\n" + "="*50)
    print("测试结构: X <- Z -> Y")

    Z2 = np.random.randn(n)
    X2 = 0.5 * Z2 + np.random.randn(n) * 0.2
    Y2 = 0.5 * Z2 + np.random.randn(n) * 0.2

    data2 = pd.DataFrame({"X": X2, "Y": Y2, "Z": Z2})

    ges2 = GESSearch(data2, BICScore())
    cpdag2 = ges2.search()

    print_cpdag(cpdag2)

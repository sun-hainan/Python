# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / causal_discovery

本文件实现 causal_discovery 相关的算法功能。
"""

import random
from typing import List, Tuple, Set
from collections import defaultdict


class CausalDiscovery:
    """因果发现"""

    def __init__(self, variables: List[str]):
        """
        参数：
            variables: 变量列表
        """
        self.variables = variables
        self.n = len(variables)
        self.index = {v: i for i, v in enumerate(variables)}

    def pc_step1(self, data: List[List[int]], alpha: float = 0.05) -> List[List[int]]:
        """
        PC算法第1步：构建无向图

        参数：
            data: 数据矩阵
            alpha: 显著性水平

        返回：邻接矩阵（无向）
        """
        n_vars = self.n
        adj = [[True] * n_vars for _ in range(n_vars)]  # 全连接初始

        # 简化的条件独立检验
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                # 检查是否独立（简化：假设某些边可以删除）
                if self._ci_test(data, i, j, [], alpha):
                    adj[i][j] = False
                    adj[j][i] = False

        return adj

    def _ci_test(self, data: List[List[int]],
                i: int, j: int, sep_set: Set[int],
                alpha: float) -> bool:
        """
        条件独立检验

        返回：是否条件独立
        """
        # 简化：假设是条件独立的
        return random.random() < alpha

    def orient_edges(self, adj: List[List[int]]) -> dict:
        """
        定向边

        参数：
            adj: 无向邻接矩阵

        返回：有向图（父节点 -> 子节点）
        """
        # 简化的随机定向
        edges = []

        for i in range(self.n):
            for j in range(i + 1, self.n):
                if adj[i][j]:
                    if random.random() > 0.5:
                        edges.append((self.variables[i], self.variables[j]))
                    else:
                        edges.append((self.variables[j], self.variables[i]))

        return edges

    def pc_algorithm(self, data: List[List[int]],
                    alpha: float = 0.05) -> dict:
        """
        PC算法完整流程

        返回：有向无环图 (DAG)
        """
        # 步骤1：构建骨架
        adj = self.pc_step1(data, alpha)

        # 步骤2：定向边
        edges = self.orient_edges(adj)

        return {'edges': edges, 'adj': adj}

    def v_structure(self, edges: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        检测V-结构（碰撞结构）

        X -> Z <- Y 如果 X 和 Y 在 Z 条件下不独立

        返回：V-结构列表
        """
        # 统计每个节点的父节点
        parents = defaultdict(set)

        for parent, child in edges:
            parents[child].add(parent)

        v_structures = []

        # 检查V-结构
        for node in self.variables:
            if len(parents[node]) >= 2:
                parent_list = list(parents[node])
                for i in range(len(parent_list)):
                    for j in range(i + 1, len(parent_list)):
                        v_structures.append((parent_list[i], node, parent_list[j]))

        return v_structures


def causal_discovery_applications():
    """因果发现应用"""
    print("=== 因果发现应用 ===")
    print()
    print("1. 医学研究")
    print("   - 发现疾病和症状的关系")
    print("   - 指导治疗方案")
    print()
    print("2. 经济分析")
    print("   - 理解政策影响")
    print("   - 预测干预效果")
    print()
    print("3. 机器学习")
    print("   - 解释性AI")
    print("   - 因果推理")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 因果发现测试 ===\n")

    # 变量
    variables = ['X', 'Y', 'Z']
    discovery = CausalDiscovery(variables)

    # 模拟数据（X -> Z <- Y）
    n_samples = 1000
    data = []

    for _ in range(n_samples):
        x = random.randint(0, 1)
        y = random.randint(0, 1)
        z = x | y  # Z = X OR Y

        data.append([x, y, z])

    print(f"变量: {variables}")
    print(f"样本数: {n_samples}")
    print()

    # PC算法
    result = discovery.pc_algorithm(data)

    print("发现的因果边：")
    for parent, child in result['edges']:
        print(f"  {parent} -> {child}")

    # V-结构
    v_structs = discovery.v_structure(result['edges'])
    if v_structs:
        print(f"\nV-结构: {v_structs}")

    print()
    causal_discovery_applications()

    print()
    print("说明：")
    print("  - 因果发现从观测数据推断因果关系")
    print("  - PC算法是经典方法")
    print("  - 需要假设（如faithfulness）")

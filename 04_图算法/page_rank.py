# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / page_rank

本文件实现 page_rank 相关的算法功能。
"""

from collections import Counter
from random import random


class Node:
    """图的节点"""
    def __init__(self, name):
        self.name = name
        self.inbound = []   # 指向该节点的节点
        self.outbound = []   # 该节点指向的节点

    def add_inbound(self, node):
        self.inbound.append(node)

    def add_outbound(self, node):
        self.outbound.append(node)

    def __repr__(self):
        return f"<节点={self.name}, 入链={self.inbound}, 出链={self.outbound}>"


def page_rank(nodes, limit=3, d=0.85):
    """
    PageRank 算法

    参数:
        nodes: 节点列表
        limit: 迭代次数
        d: 阻尼系数（0.85 表示用户有 85% 概率继续点击链接）

    返回:
        每个节点的 PageRank 值

    示例:
        >>> names = ['A', 'B', 'C']
        >>> nodes = [Node(n) for n in names]
        >>> graph = [[0, 1, 1], [0, 0, 1], [1, 0, 0]]
        >>> for ri, row in enumerate(graph):
        ...     for ci, col in enumerate(row):
        ...         if col == 1:
        ...             nodes[ci].add_inbound(names[ri])
        ...             nodes[ri].add_outbound(names[ci])
        >>> ranks = page_rank(nodes, limit=10)
    """
    ranks = {}
    n = len(nodes)

    # 初始化：每个节点的 PR 值
    for node in nodes:
        ranks[node.name] = 1

    # 统计每个节点的出链数
    outbounds = {}
    for node in nodes:
        outbounds[node.name] = len(node.outbound)

    # 迭代计算
    for i in range(limit):
        print(f"======= 第 {i + 1} 次迭代 =======")
        for _, node in enumerate(nodes):
            # PageRank 公式：(1-d) + d * Σ(PR(Ti)/C(Ti))
            ranks[node.name] = (1 - d) + d * sum(
                ranks[ib] / outbounds[ib]
                for ib in node.inbound
                if outbounds[ib] > 0  # 避免除零
            )
        print(ranks)

    return ranks


def main():
    # 示例输入
    # 图结构：
    # A -> B, A -> C
    # B -> C
    # C -> A
    graph = [[0, 1, 1], [0, 0, 1], [1, 0, 0]]

    names = ['A', 'B', 'C']
    nodes = [Node(name) for name in names]

    # 构建图
    for ri, row in enumerate(graph):
        for ci, col in enumerate(row):
            if col == 1:
                nodes[ci].add_inbound(names[ri])
                nodes[ri].add_outbound(names[ci])

    print("======= 节点信息 =======")
    for node in nodes:
        print(node)

    print()
    page_rank(nodes, limit=5)


if __name__ == "__main__":
    main()

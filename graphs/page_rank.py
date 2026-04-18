"""
PageRank 算法 - 中文注释版
==========================================

算法背景：
    PageRank 是 Google 创始人 Larry Page 和 Sergey Brin 提出的算法，
    用于评估网页的重要性，是 Google 搜索引擎排名的核心算法之一。

核心思想：
    一个网页的重要性取决于：
    1. 指向它的网页数量
    2. 这些指向它的网页本身的重要性

公式：
    PR(A) = (1-d)/N + d * Σ(PR(Ti)/C(Ti))

    其中：
    - PR(A): 页面 A 的 PageRank 值
    - d: 阻尼系数（通常为 0.85）
    - N: 总页面数
    - Ti: 指向 A 的页面
    - C(Ti): 页面 Ti 的出链数量

迭代过程：
    1. 初始化所有页面的 PR 值为 1/N
    2. 迭代计算直到收敛
    3. 每次迭代考虑所有页面的贡献

应用场景：
    - 网页排名
    - 社交网络影响力分析
    - 推荐系统
    - 学术引用分析
"""

from __future__ import annotations
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

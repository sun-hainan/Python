"""
马尔可夫链 (Markov Chain) - 中文注释版
==========================================

算法原理：
    马尔可夫链是一个随机过程模型，
    核心假设：下一步的状态只与当前状态有关，与之前的历史无关。
    这称为"马尔可夫性质"。

应用场景：
    - 搜索引擎的 PageRank
    - 天气预测
    - 股票价格模型
    - 自然语言处理（词性标注）
    - 推荐系统

核心概念：
    - 状态（State）：系统可能处于的情况
    - 转移概率（Transition Probability）：从一个状态转移到另一个状态的概率
    - 转移矩阵（Transition Matrix）：所有转移概率的矩阵

平稳分布：
    当迭代次数足够多时，马尔可夫链会收敛到一个稳定状态，
    此时各状态的概率分布不再改变。
"""

from __future__ import annotations
from collections import Counter
from random import random


class MarkovChainGraphUndirectedUnweighted:
    """
    马尔可夫链图（无向无权版本）
    """

    def __init__(self):
        self.connections = {}  # {节点: {邻居: 概率}}

    def add_node(self, node: str) -> None:
        self.connections[node] = {}

    def add_transition_probability(
        self, node1: str, node2: str, probability: float
    ) -> None:
        if node1 not in self.connections:
            self.add_node(node1)
        if node2 not in self.connections:
            self.add_node(node2)
        self.connections[node1][node2] = probability

    def get_nodes(self) -> list[str]:
        return list(self.connections)

    def transition(self, node: str) -> str:
        """
        根据转移概率，从当前节点随机转移到下一个节点
        """
        current_probability = 0
        random_value = random()

        for dest in self.connections[node]:
            current_probability += self.connections[node][dest]
            if current_probability > random_value:
                return dest
        return ""


def get_transitions(
    start: str, transitions: list[tuple[str, str, float]], steps: int
) -> dict[str, int]:
    """
    运行马尔可夫链并统计各节点访问次数

    参数:
        start: 起始节点
        transitions: 转移列表 [(起点, 终点, 概率), ...]
        steps: 模拟步数

    返回:
        各节点被访问的次数

    示例:
        >>> transitions = [
        ...     ('a', 'a', 0.9),
        ...     ('a', 'b', 0.075),
        ...     ('a', 'c', 0.025),
        ...     ('b', 'a', 0.15),
        ...     ('b', 'b', 0.8),
        ...     ('b', 'c', 0.05),
        ...     ('c', 'a', 0.25),
        ...     ('c', 'b', 0.25),
        ...     ('c', 'c', 0.5)
        ... ]
        >>> result = get_transitions('a', transitions, 5000)
        >>> result['a'] > result['b'] > result['c']
        True
    """
    graph = MarkovChainGraphUndirectedUnweighted()

    # 构建转移图
    for node1, node2, probability in transitions:
        graph.add_transition_probability(node1, node2, probability)

    visited = Counter(graph.get_nodes())
    node = start

    # 模拟马尔可夫链
    for _ in range(steps):
        node = graph.transition(node)
        if node:  # 确保节点有效
            visited[node] += 1

    return visited


if __name__ == "__main__":
    import doctest
    doctest.testmod()

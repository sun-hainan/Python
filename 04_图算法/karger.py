# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / karger

本文件实现 karger 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""



import random

# Adjacency list representation of this graph:
# https://en.wikipedia.org/wiki/File:Single_run_of_Karger%E2%80%99s_Mincut_algorithm.svg
TEST_GRAPH = {
    "1": ["2", "3", "4", "5"],
    "2": ["1", "3", "4", "5"],
    "3": ["1", "2", "4", "5", "10"],
    "4": ["1", "2", "3", "5", "6"],
    "5": ["1", "2", "3", "4", "7"],
    "6": ["7", "8", "9", "10", "4"],
    "7": ["6", "8", "9", "10", "5"],
    "8": ["6", "7", "9", "10"],
    "9": ["6", "7", "8", "10"],
    "10": ["6", "7", "8", "9", "3"],
}


def partition_graph(graph: dict[str, list[str]]) -> set[tuple[str, str]]:
    # partition_graph function

    # partition_graph function
    # partition_graph 函数实现
    """
    Partitions a graph using Karger's Algorithm. Implemented from
    pseudocode found here:
    https://en.wikipedia.org/wiki/Karger%27s_algorithm.
    This function involves random choices, meaning it will not give
    consistent outputs.

    Args:
        graph: A dictionary containing adacency lists for the graph.
            Nodes must be strings.

    Returns:
        The cutset of the cut found by Karger's Algorithm.

    >>> graph = {'0':['1'], '1':['0']}
    >>> partition_graph(graph)
    {('0', '1')}
    """
    # Dict that maps contracted nodes to a list of all the nodes it "contains."
    contracted_nodes = {node: {node} for node in graph}

    graph_copy = {node: graph[node][:] for node in graph}

    while len(graph_copy) > 2:
        # Choose a random edge.
        u = random.choice(list(graph_copy.keys()))
        v = random.choice(graph_copy[u])

        # Contract edge (u, v) to new node uv
        uv = u + v
        uv_neighbors = list(set(graph_copy[u] + graph_copy[v]))
        uv_neighbors.remove(u)
        uv_neighbors.remove(v)
        graph_copy[uv] = uv_neighbors
        for neighbor in uv_neighbors:
            graph_copy[neighbor].append(uv)

        contracted_nodes[uv] = set(contracted_nodes[u].union(contracted_nodes[v]))

        # Remove nodes u and v.
        del graph_copy[u]
        del graph_copy[v]
        for neighbor in uv_neighbors:
            if u in graph_copy[neighbor]:
                graph_copy[neighbor].remove(u)
            if v in graph_copy[neighbor]:
                graph_copy[neighbor].remove(v)

    # Find cutset.
    groups = [contracted_nodes[node] for node in graph_copy]
    return {
        (node, neighbor)
        for node in groups[0]
        for neighbor in graph[node]
        if neighbor in groups[1]
    }


if __name__ == "__main__":
    print(partition_graph(TEST_GRAPH))

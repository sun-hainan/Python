# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / graph_list

本文件实现 graph_list 相关的算法功能。
"""

#!/usr/bin/env python3
"""
==============================================================
图算法 - 邻接表实现（图数据结构）
==============================================================
使用邻接表（Adjacency List）存储图的节点和边，支持有向图和无向图。

功能：
- 有向图/无向图的增删边操作
- 图的字符串表示
- 支持泛型（任意哈希类型作为顶点）

参考：OMKAR PATHAK, Nwachukwu Chidiebere
"""

from __future__ import annotations

from pprint import pformat
from typing import TypeVar

T = TypeVar("T")


class GraphAdjacencyList[T]:
    """
    邻接表类型图数据结构。
    
    支持有向图和无向图，通过 directed 参数区分。
    
    示例（有向图）:
    >>> d_graph = GraphAdjacencyList()
    >>> d_graph.add_edge(0, 1)
    {0: [1], 1: []}
    >>> d_graph.add_edge(1, 2).add_edge(1, 4).add_edge(1, 5)
    {0: [1], 1: [2, 4, 5], 2: [], 4: [], 5: []}
    
    示例（无向图）:
    >>> u_graph = GraphAdjacencyList(directed=False)
    >>> u_graph.add_edge(0, 1)
    {0: [1], 1: [0]}
    >>> u_graph.add_edge(1, 2)
    {0: [1], 1: [0, 2], 2: [1]}
    """

    def __init__(self, directed: bool = True) -> None:
        """
        初始化图结构。
        
        Args:
            directed: 是否为有向图，默认 True（有向图）。
                     False 表示无向图。
        """
        # adj_list: 字典，键为顶点，值为其邻接顶点列表
        self.adj_list: dict[T, list[T]] = {}
        self.directed = directed

    def add_edge(
        self, source_vertex: T, destination_vertex: T
    ) -> GraphAdjacencyList[T]:
        """
        连接两个顶点，创建边。
        
        如果顶点不存在，会自动创建。
        
        Args:
            source_vertex: 起始顶点
            destination_vertex: 目标顶点
        
        Returns:
            返回 self，支持链式调用
        """
        if not self.directed:
            # 无向图：双向添加
            if source_vertex in self.adj_list and destination_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
                self.adj_list[destination_vertex].append(source_vertex)
            elif source_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
                self.adj_list[destination_vertex] = [source_vertex]
            elif destination_vertex in self.adj_list:
                self.adj_list[destination_vertex].append(source_vertex)
                self.adj_list[source_vertex] = [destination_vertex]
            else:
                self.adj_list[source_vertex] = [destination_vertex]
                self.adj_list[destination_vertex] = [source_vertex]
        else:
            # 有向图：只从 source -> destination
            if source_vertex in self.adj_list and destination_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
            elif source_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
                self.adj_list[destination_vertex] = []
            elif destination_vertex in self.adj_list:
                self.adj_list[source_vertex] = [destination_vertex]
            else:
                self.adj_list[source_vertex] = [destination_vertex]
                self.adj_list[destination_vertex] = []

        return self

    def __repr__(self) -> str:
        """返回图的字符串表示。"""
        return pformat(self.adj_list)


if __name__ == "__main__":
    # 测试用例
    # 创建有向图
    d_graph = GraphAdjacencyList()
    d_graph.add_edge(0, 1).add_edge(1, 2).add_edge(2, 3)
    print("有向图:", d_graph)
    
    # 创建无向图
    u_graph = GraphAdjacencyList(directed=False)
    u_graph.add_edge('A', 'B').add_edge('B', 'C').add_edge('A', 'C')
    print("无向图:", u_graph)

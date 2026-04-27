# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / deep_clone_graph

本文件实现 deep_clone_graph 相关的算法功能。
"""

from dataclasses import dataclass


@dataclass
class Node:
    # Node class

    # Node class
    # Node 类实现
    value: int = 0
    neighbors: list["Node"] | None = None

    def __post_init__(self) -> None:
    # __post_init__ function

    # __post_init__ function
        """
        >>> Node(3).neighbors
        []
        """
        self.neighbors = self.neighbors or []

    def __hash__(self) -> int:
    # __hash__ function

    # __hash__ function
        """
        >>> hash(Node(3)) != 0
        True
        """
        return id(self)


def clone_graph(node: Node | None) -> Node | None:
    # clone_graph function

    # clone_graph function
    # clone_graph 函数实现
    """
    This function returns a clone of a connected undirected graph.
    >>> clone_graph(Node(1))
    Node(value=1, neighbors=[])
    >>> clone_graph(Node(1, [Node(2)]))
    Node(value=1, neighbors=[Node(value=2, neighbors=[])])
    >>> clone_graph(None) is None
    True
    """
    if not node:
        return None

    originals_to_clones = {}  # map nodes to clones

    stack = [node]

    while stack:
        original = stack.pop()

        if original in originals_to_clones:
            continue

        originals_to_clones[original] = Node(original.value)

        stack.extend(original.neighbors or [])

    for original, clone in originals_to_clones.items():
        for neighbor in original.neighbors or []:
            cloned_neighbor = originals_to_clones[neighbor]

            if not clone.neighbors:
                clone.neighbors = []

            clone.neighbors.append(cloned_neighbor)

    return originals_to_clones[node]


if __name__ == "__main__":
    import doctest

    doctest.testmod()

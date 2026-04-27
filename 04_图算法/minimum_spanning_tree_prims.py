# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / minimum_spanning_tree_prims

本文件实现 minimum_spanning_tree_prims 相关的算法功能。
"""

import sys
from collections import defaultdict


class Heap:
    """最小堆，用于高效选择最小边"""

    def __init__(self):
        self.node_position = []

    def get_position(self, vertex):
        return self.node_position[vertex]

    def set_position(self, vertex, pos):
        self.node_position[vertex] = pos

    def top_to_bottom(self, heap, start, size, positions):
        """向下调整堆（用于删除最小元素后）"""
        if start > size // 2 - 1:
            return
        smallest_child = 2 * start + 2 >= size and 2 * start + 1 or (
            2 * start + 1 if heap[2 * start + 1] < heap[2 * start + 2] else 2 * start + 2
        )
        if heap[smallest_child] < heap[start]:
            heap[smallest_child], positions[smallest_child] = positions[start], heap[start]
            positions[start], heap[start] = positions[smallest_child], heap[smallest_child]
            self.top_to_bottom(heap, smallest_child, size, positions)

    def bottom_to_top(self, val, index, heap, position):
        """向上调整堆（用于更新某个节点的值）"""
        while index != 0:
            parent = int((index - 2) / 2) if index % 2 == 0 else int((index - 1) / 2)
            if val < heap[parent]:
                heap[index] = heap[parent]
                position[index] = position[parent]
                self.set_position(position[parent], index)
            else:
                heap[index] = val
                position[index] = position[index]
                self.set_position(position[index], index)
                break
            index = parent
        else:
            heap[0] = val
            position[0] = position[0]
            self.set_position(position[0], 0)

    def heapify(self, heap, positions):
        """构建堆"""
        start = len(heap) // 2 - 1
        for i in range(start, -1, -1):
            self.top_to_bottom(heap, i, len(heap), positions)

    def delete_minimum(self, heap, positions):
        """删除并返回最小元素"""
        temp = positions[0]
        heap[0] = sys.maxsize
        self.top_to_bottom(heap, 0, len(heap), positions)
        return temp


def prisms_algorithm(adjacency_list):
    """
    Prim 最小生成树算法

    参数:
        adjacency_list: 邻接表，格式 {顶点: [[邻居, 权重], ...]}

    返回:
        最小生成树的边列表 [(起点, 终点), ...]

    示例:
        >>> adjacency_list = {0: [[1, 1], [3, 3]],
        ...                   1: [[0, 1], [2, 6], [3, 5], [4, 1]],
        ...                   2: [[1, 6], [4, 5], [5, 2]],
        ...                   3: [[0, 3], [1, 5], [4, 1]],
        ...                   4: [[1, 1], [2, 5], [3, 1], [5, 4]],
        ...                   5: [[2, 2], [4, 4]]}
        >>> prisms_algorithm(adjacency_list)
        [(0, 1), (1, 4), (4, 3), (4, 5), (5, 2)]
    """
    heap = Heap()
    visited = [0] * len(adjacency_list)
    nbr_tv = [-1] * len(adjacency_list)  # 连接已选树的邻居顶点
    distance_tv = []
    positions = []

    for vertex in range(len(adjacency_list)):
        distance_tv.append(sys.maxsize)
        positions.append(vertex)
        heap.node_position.append(vertex)

    tree_edges = []
    visited[0] = 1  # 从顶点 0 开始
    distance_tv[0] = sys.maxsize
    for neighbor, distance in adjacency_list[0]:
        nbr_tv[neighbor] = 0
        distance_tv[neighbor] = distance
    heap.heapify(distance_tv, positions)

    for _ in range(1, len(adjacency_list)):
        vertex = heap.delete_minimum(distance_tv, positions)
        if visited[vertex] == 0:
            tree_edges.append((nbr_tv[vertex], vertex))
            visited[vertex] = 1
            for neighbor, distance in adjacency_list[vertex]:
                if visited[neighbor] == 0 and distance < distance_tv[heap.get_position(neighbor)]:
                    distance_tv[heap.get_position(neighbor)] = distance
                    heap.bottom_to_top(distance, heap.get_position(neighbor), distance_tv, positions)
                    nbr_tv[neighbor] = vertex

    return tree_edges


if __name__ == "__main__":
    edges_number = int(input("输入边数: ").strip())
    adjacency_list = defaultdict(list)
    for _ in range(edges_number):
        edge = [int(x) for x in input().strip().split()]
        adjacency_list[edge[0]].append([edge[1], edge[2]])
        adjacency_list[edge[1]].append([edge[0], edge[2]])
    print(f"最小生成树边: {prisms_algorithm(adjacency_list)}")

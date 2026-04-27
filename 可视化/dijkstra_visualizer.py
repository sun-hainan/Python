# -*- coding: utf-8 -*-
"""
算法实现：可视化 / dijkstra_visualizer

本文件实现 dijkstra_visualizer 相关的算法功能。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import heapq


class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = {}  # (u, v) -> weight

    def add_edge(self, u, v, w):
        self.nodes.add(u)
        self.nodes.add(v)
        self.edges[(u, v)] = w
        self.edges[(v, u)] = w

    def neighbors(self, u):
        for v in self.nodes:
            if (u, v) in self.edges:
                yield v, self.edges[(u, v)]


def dijkstra(graph, source):
    """
    Dijkstra 算法实现

    返回：(distances, predecessor, steps)
    steps 记录每一步的松弛操作，用于可视化
    """
    dist = {node: float('inf') for node in graph.nodes}
    prev = {node: None for node in graph.nodes}
    dist[source] = 0
    steps = []

    # 优先队列：(距离, 节点)
    pq = [(0, source)]
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)
        steps.append(('visit', u, d, None, None))

        for v, w in graph.neighbors(u):
            if v in visited:
                continue

            if dist[u] + w < dist[v]:
                old_dist = dist[v]
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
                steps.append(('relax', v, dist[v], u, old_dist))

    return dist, prev, steps


def visualize_dijkstra(graph, source, dist, steps, save_path='dijkstra.png'):
    """可视化 Dijkstra 算法过程"""
    nodes = sorted(graph.nodes)
    n = len(nodes)
    node_idx = {n: i for i, n in enumerate(nodes)}

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(-1, 4)
    ax.set_ylim(-1, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'Dijkstra 算法从节点 {source} 开始的最短路径', fontsize=14)

    # 预设节点位置
    pos = {
        'A': (0, 3), 'B': (1.5, 3), 'C': (3, 3),
        'D': (0, 1.5), 'E': (1.5, 1.5), 'F': (3, 1.5),
        'G': (1.5, 0)
    }

    # 绘制边
    drawn_edges = set()
    for (u, v), w in graph.edges.items():
        if (u, v) not in drawn_edges and (v, u) not in drawn_edges:
            drawn_edges.add((u, v))
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            ax.plot([x1, x2], [y1, y2], 'gray', linewidth=1.5, alpha=0.5)
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, str(w), fontsize=9, color='gray')

    # 绘制节点
    for node in nodes:
        x, y = pos[node]
        d = dist[node] if dist[node] < float('inf') else '∞'
        color = 'lightgreen' if node == source else 'lightblue'
        circle = plt.Circle((x, y), 0.25, color=color, ec='navy', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, node, ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(x, y - 0.45, f'd={d}', ha='center', va='center', fontsize=9, color='red')

    # 显示步骤
    step_text = f"算法步骤（最多显示10步）:\n"
    for i, step in enumerate(steps[:10]):
        if step[0] == 'visit':
            step_text += f"  {i+1}. 访问节点 {step[1]}，距离={step[2]}\n"
        else:
            step_text += f"  {i+1}. 松弛 {step[1]}: {step[4]}→{step[2]}（经节点 {step[3]}）\n"
    ax.text(-0.5, -0.8, step_text, fontsize=9, family='monospace', va='top')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"图片已保存: {save_path}")
    plt.show()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Dijkstra 最短路径可视化 ===\n")

    # 创建示例图
    g = Graph()
    edges = [
        ('A', 'B', 4), ('A', 'C', 2), ('B', 'C', 1), ('B', 'D', 5),
        ('C', 'D', 8), ('C', 'E', 10), ('D', 'E', 2), ('D', 'F', 6),
        ('E', 'F', 3), ('E', 'G', 8), ('F', 'G', 1)
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)

    print("图的边:")
    for u, v, w in edges:
        print(f"  {u} -- {v}: {w}")

    source = 'A'
    dist, prev, steps = dijkstra(g, source)

    print(f"\n从节点 {source} 出发的最短距离:")
    for node in sorted(dist.keys()):
        print(f"  到 {node}: {dist[node]}")
    print()

    visualize_dijkstra(g, source, dist, steps)

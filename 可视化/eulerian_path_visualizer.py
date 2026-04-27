# -*- coding: utf-8 -*-
"""
算法实现：可视化 / eulerian_path_visualizer

本文件实现 eulerian_path_visualizer 相关的算法功能。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict


class Graph:
    def __init__(self):
        self.adj = defaultdict(list)  # {node: [(neighbor, edge_id), ...]}
        self.edges = []  # [(u, v)] 边列表

    def add_edge(self, u, v):
        edge_id = len(self.edges)
        self.edges.append((u, v))
        self.adj[u].append((v, edge_id))
        self.adj[v].append((u, edge_id))

    def degree(self, node):
        return len(self.adj[node])


def has_euler_path_or_cycle(graph):
    """判断是否存在欧拉路径或回路"""
    odd_degree_nodes = [node for node in graph.adj if graph.degree(node) % 2 == 1]

    if len(odd_degree_nodes) == 0:
        return 'cycle', list(graph.adj.keys())[0]  # 从任意点开始
    elif len(odd_degree_nodes) == 2:
        return 'path', odd_degree_nodes[0]  # 从奇度数点开始
    else:
        return None, None


def hierholzer(graph, start):
    """
    Hierholzer 算法求欧拉路径/回路

    返回：边的遍历顺序
    """
    edge_used = [False] * len(graph.edges)
    path = []

    def dfs(u):
        while graph.adj[u]:
            v, eid = graph.adj[u].pop()
            if edge_used[eid]:
                continue
            edge_used[eid] = True
            dfs(v)
        path.append(u)

    dfs(start)
    path.reverse()
    return path


def get_edge_path(graph, vertex_path):
    """从顶点路径获取边序列"""
    edge_path = []
    for i in range(len(vertex_path) - 1):
        u, v = vertex_path[i], vertex_path[i + 1]
        for neighbor, eid in graph.adj[u]:
            if neighbor == v:
                edge_path.append((u, v, eid))
                break
    return edge_path


def draw_graph(graph, vertex_path, edge_index, ax, title=""):
    """绘制图和当前遍历状态"""
    ax.clear()
    ax.set_xlim(-1, 6)
    ax.set_ylim(-1, 6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=12)

    if not graph.edges:
        ax.text(2.5, 3, "图为空", fontsize=14)
        return

    # 预设节点位置（根据节点数调整）
    nodes = list(graph.adj.keys())
    n = len(nodes)
    pos = {}
    if n == 5:
        pos = {nodes[0]: (2.5, 5), nodes[1]: (0, 2.5), nodes[2]: (5, 2.5),
               nodes[3]: (1, 0), nodes[4]: (4, 0)}
    elif n == 4:
        pos = {nodes[0]: (0, 3), nodes[1]: (5, 3), nodes[2]: (5, 0), nodes[3]: (0, 0)}
    elif n == 3:
        pos = {nodes[0]: (2.5, 4), nodes[1]: (0, 0), nodes[2]: (5, 0)}
    else:
        for i, node in enumerate(nodes):
            angle = 2 * np.pi * i / n - np.pi / 2
            pos[node] = (2.5 + 2.5 * np.cos(angle), 2.5 + 2.5 * np.sin(angle))

    # 已访问的边
    visited_edges = set()
    for i in range(edge_index):
        if i < len(vertex_path) - 1:
            u, v = vertex_path[i], vertex_path[i + 1]
            for neighbor, eid in graph.adj[u]:
                if neighbor == v:
                    visited_edges.add(eid)
                    break

    # 绘制边
    for eid, (u, v) in enumerate(graph.edges):
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        color = 'green' if eid in visited_edges else 'gray'
        lw = 3 if eid in visited_edges else 1.5
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, alpha=0.8)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, str(eid), fontsize=8,
               color='green' if eid in visited_edges else 'gray')

    # 绘制节点
    for node in nodes:
        x, y = pos[node]
        in_path = node in vertex_path[:edge_index + 1]
        color = 'orange' if in_path else 'lightblue'
        circle = plt.Circle((x, y), 0.3, color=color, ec='navy', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, str(node), ha='center', va='center', fontsize=11, fontweight='bold')

        # 度数标注
        ax.text(x + 0.35, y - 0.35, f'd={graph.degree(node)}', fontsize=8, color='gray')


def visualize_eulerian_path(graph, save_path='eulerian_path.png'):
    """可视化欧拉路径/回路"""
    exists, start = has_euler_path_or_cycle(graph)

    if not exists:
        print(f"不存在欧拉路径/回路（奇度数顶点过多）")
        return

    print(f"存在{'欧拉回路' if exists == 'cycle' else '欧拉路径'}，起点: {start}")

    # 求欧拉路径
    vertex_path = hierholzer(graph, start)
    edge_path = get_edge_path(graph, vertex_path)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"欧拉{'回路' if exists == 'cycle' else '路径'}可视化", fontsize=14)

    # 初始状态
    draw_graph(graph, vertex_path, 0, axes[0], '初始状态（尚未遍历）')

    # 中间状态
    mid = len(vertex_path) // 2
    draw_graph(graph, vertex_path, mid, axes[1], f'遍历中（已完成 {mid}/{len(vertex_path)-1} 条边）')

    # 最终状态
    draw_graph(graph, vertex_path, len(vertex_path), axes[2], f'完成！共 {len(edge_path)} 条边')

    # 结果输出
    result_text = f"欧拉{'回路' if exists == 'cycle' else '路径'}:\n"
    result_text += f"顶点顺序: {vertex_path}\n"
    result_text += f"边遍历: {edge_path}"
    axes[2].text(0, -0.8, result_text, fontsize=9, family='monospace',
                transform=axes[2].transAxes, verticalalignment='top')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"图片已保存: {save_path}")
    plt.show()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 欧拉路径可视化测试 ===\n")

    # 测试1：欧拉回路（所有顶点度数为偶数）
    print("--- 测试1：欧拉回路 ---")
    g1 = Graph()
    edges1 = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    for u, v in edges1:
        g1.add_edge(u, v)
    print(f"边: {edges1}")
    print(f"各顶点度数: {[g1.degree(i) for i in range(4)]}")

    visualize_eulerian_path(g1, 'eulerian_cycle.png')

    print()

    # 测试2：欧拉路径（恰好两个奇度数顶点）
    print("--- 测试2：欧拉路径 ---")
    g2 = Graph()
    edges2 = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]
    for u, v in edges2:
        g2.add_edge(u, v)
    print(f"边: {edges2}")
    print(f"各顶点度数: {[g2.degree(i) for i in range(5)]}")

    visualize_eulerian_path(g2, 'eulerian_path.png')

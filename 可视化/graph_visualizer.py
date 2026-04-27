#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图搜索算法可视化
使用 matplotlib 动画展示：BFS/DFS 遍历、Dijkstra 最短路径、A* 寻路

使用方法：python visualization/graph_visualizer.py
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import numpy as np

# ============== 常量配置 ==============
NODE_RADIUS = 0.3
GRID_SIZE = 0.8
COLORS = {
    'empty': '#ecf0f1',
    'start': '#27ae60',
    'end': '#c0392b',
    'wall': '#2c3e50',
    'visited': '#3498db',
    'current': '#e74c3c',
    'path': '#f39c12',
    'frontier': '#9b59b6',
    'node_default': '#3498db',
    'edge_default': '#7f8c8d',
    'edge_highlight': '#e74c3c',
}


# ============== 网格图类 ==============

class GridGraph:
    """网格图（用于寻路�?""

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[0] * cols for _ in range(rows)]  # 0=�? 1=�?        self.history = []  # 记录探索过程

    def set_wall(self, row, col):
        self.grid[row][col] = 1

    def is_valid(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == 0

    def get_neighbors(self, row, col):
        """返回四个方向的邻�?""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if self.is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors


# ============== 图类（通用�?==============

class Graph:
    """通用图结�?""

    def __init__(self):
        self.nodes = {}  # node_id -> (x, y)
        self.edges = []  # [(u, v, weight)]
        self.adj = {}   # 邻接�?        self.history = []

    def add_node(self, node_id, x, y):
        self.nodes[node_id] = (x, y)
        if node_id not in self.adj:
            self.adj[node_id] = []

    def add_edge(self, u, v, weight=1):
        self.edges.append((u, v, weight))
        if u not in self.adj:
            self.adj[u] = []
        if v not in self.adj:
            self.adj[v] = []
        self.adj[u].append((v, weight))
        self.adj[v].append((u, weight))


# ============== BFS 可视�?==============

def visualize_bfs(grid, start, end):
    """BFS 遍历可视�?""
    queue = [start]
    visited = {start}
    parent = {start: None}
    step = 0

    history = [{
        'visited': set(),
        'current': start,
        'frontier': set(queue),
        'path': [],
        'step': 0,
        'message': f'起点入队: {start}'
    }]

    while queue:
        current = queue.pop(0)
        step += 1

        history.append({
            'visited': set(visited),
            'current': current,
            'frontier': set(queue),
            'path': [],
            'step': step,
            'message': f'出队: {current}'
        })

        if current == end:
            # 回溯路径
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path = path[::-1]

            history.append({
                'visited': set(visited),
                'current': end,
                'frontier': set(),
                'path': path,
                'step': step,
                'message': f'找到终点! 路径长度: {len(path)-1}'
            })
            return history

        for neighbor in grid.get_neighbors(*current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
                history.append({
                    'visited': set(visited),
                    'current': neighbor,
                    'frontier': set(queue),
                    'path': [],
                    'step': step,
                    'message': f'入队: {neighbor}, 父节�? {current}'
                })

    return history


# ============== DFS 可视�?==============

def visualize_dfs(grid, start, end):
    """DFS 遍历可视�?""
    stack = [start]
    visited = set()
    parent = {start: None}
    step = 0

    history = [{
        'visited': set(),
        'current': start,
        'stack': list(stack),
        'path': [],
        'step': 0,
        'message': f'起点入栈: {start}'
    }]

    while stack:
        current = stack.pop()
        step += 1

        if current in visited:
            history.append({
                'visited': set(visited),
                'current': current,
                'stack': list(stack),
                'path': [],
                'step': step,
                'message': f'跳过(已访�?: {current}'
            })
            continue

        visited.add(current)
        history.append({
            'visited': set(visited),
            'current': current,
            'stack': list(stack),
            'path': [],
            'step': step,
            'message': f'弹出: {current}, 标记已访�?
        })

        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path = path[::-1]

            history.append({
                'visited': set(visited),
                'current': end,
                'stack': [],
                'path': path,
                'step': step,
                'message': f'找到终点! 路径长度: {len(path)-1}'
            })
            return history

        neighbors = grid.get_neighbors(*current)
        for neighbor in reversed(neighbors):
            if neighbor not in visited:
                parent[neighbor] = current
                stack.append(neighbor)
                history.append({
                    'visited': set(visited),
                    'current': neighbor,
                    'stack': list(stack),
                    'path': [],
                    'step': step,
                    'message': f'入栈: {neighbor}'
                })

    return history


# ============== Dijkstra 可视�?==============

def visualize_dijkstra(graph, start, end):
    """Dijkstra 最短路径可视化"""
    import heapq

    dist = {node: float('inf') for node in graph.nodes}
    parent = {start: None}
    dist[start] = 0
    visited = set()

    # priority queue: (dist, node)
    pq = [(0, start)]
    step = 0

    history = [{
        'dist': dict(dist),
        'visited': set(),
        'current': start,
        'frontier': set([start]),
        'path': [],
        'step': 0,
        'message': f'起点: {start}, 距离=0'
    }]

    while pq:
        d, current = heapq.heappop(pq)
        step += 1

        if current in visited:
            history.append({
                'dist': dict(dist),
                'visited': set(visited),
                'current': current,
                'frontier': set(),
                'path': [],
                'step': step,
                'message': f'跳过(已处�?: {current}'
            })
            continue

        visited.add(current)
        history.append({
            'dist': dict(dist),
            'visited': set(visited),
            'current': current,
            'frontier': set(),
            'path': [],
            'step': step,
            'message': f'处理节点: {current}, 当前距离: {d}'
        })

        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path = path[::-1]

            history.append({
                'dist': dict(dist),
                'visited': set(visited),
                'current': end,
                'frontier': set(),
                'path': path,
                'step': step,
                'message': f'找到最短路�? 总距�? {dist[end]}'
            })
            return history

        for neighbor, weight in graph.adj.get(current, []):
            if neighbor in visited:
                continue

            new_dist = dist[current] + weight
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                parent[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))
                history.append({
                    'dist': dict(dist),
                    'visited': set(visited),
                    'current': neighbor,
                    'frontier': set(v for _, v in pq),
                    'path': [],
                    'step': step,
                    'message': f'更新 {neighbor}: 距离={new_dist} (经过 {current})'
                })

    return history


# ============== A* 可视�?==============

def heuristic(a, b):
    """曼哈顿距离启发函�?""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def visualize_astar(grid, start, end):
    """A* 寻路可视�?""
    import heapq

    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    parent = {start: None}
    open_set = [(f_score[start], start)]
    visited = set()
    step = 0

    history = [{
        'g': dict(g_score),
        'f': dict(f_score),
        'open': set([start]),
        'closed': set(),
        'current': start,
        'path': [],
        'step': 0,
        'message': f'起点: {start}, f={f_score[start]}'
    }]

    while open_set:
        f, current = heapq.heappop(open_set)
        step += 1

        if current in visited:
            history.append({
                'g': dict(g_score),
                'f': dict(f_score),
                'open': set(v for _, v in open_set),
                'closed': set(visited),
                'current': current,
                'path': [],
                'step': step,
                'message': f'跳过(已关�?: {current}'
            })
            continue

        visited.add(current)
        history.append({
            'g': dict(g_score),
            'f': dict(f_score),
            'open': set(v for _, v in open_set),
            'closed': set(visited),
            'current': current,
            'path': [],
            'step': step,
            'message': f'关闭: {current}, g={g_score.get(current,"?")}, f={f}'
        })

        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path = path[::-1]

            history.append({
                'g': dict(g_score),
                'f': dict(f_score),
                'open': set(),
                'closed': set(visited),
                'current': end,
                'path': path,
                'step': step,
                'message': f'找到路径! 总代�?g={g_score[end]}, 启发估计 h={heuristic(end, end)}'
            })
            return history

        for neighbor in grid.get_neighbors(*current):
            if neighbor in visited:
                continue

            tentative_g = g_score[current] + 1  # 网格图每步代价为1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, end)
                f_score[neighbor] = f
                heapq.heappush(open_set, (f, neighbor))
                history.append({
                    'g': dict(g_score),
                    'f': dict(f_score),
                    'open': set(v for _, v in open_set),
                    'closed': set(visited),
                    'current': neighbor,
                    'path': [],
                    'step': step,
                    'message': f'探索 {neighbor}: g={tentative_g}, h={heuristic(neighbor, end)}, f={f}'
                })

    return history


# ============== 绘图函数 ==============

def draw_grid(ax, grid, state, title=''):
    """绘制网格�?""
    ax.clear()
    ax.set_xlim(-0.5, grid.cols - 0.5)
    ax.set_ylim(-0.5, grid.rows - 0.5)
    ax.set_aspect('equal')
    ax.set_xticks(range(grid.cols))
    ax.set_yticks(range(grid.rows))
    ax.set_title(title, fontsize=14, fontweight='bold')

    # 绘制每个格子
    for r in range(grid.rows):
        for c in range(grid.cols):
            color = COLORS['empty']
            if grid.grid[r][c] == 1:
                color = COLORS['wall']
            ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                        facecolor=color, edgecolor='#bdc3c7', linewidth=0.5))

    visited = state.get('visited', set())
    current = state.get('current', None)
    frontier = state.get('frontier', set())
    path = state.get('path', [])

    # 绘制已访问节�?    for (r, c) in visited:
        if (r, c) != current and (r, c) not in frontier:
            ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                        facecolor=COLORS['visited'], edgecolor='#bdc3c7', linewidth=0.5,
                                        alpha=0.7))

    # 绘制前沿节点
    for (r, c) in frontier:
        ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                    facecolor=COLORS['frontier'], edgecolor='#bdc3c7', linewidth=0.5,
                                    alpha=0.7))

    # 绘制当前节点
    if current:
        ax.add_patch(plt.Rectangle((current[1] - 0.5, current[0] - 0.5), 1, 1,
                                    facecolor=COLORS['current'], edgecolor='white', linewidth=2))

    # 绘制路径
    for (r, c) in path:
        ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                    facecolor=COLORS['path'], edgecolor='white', linewidth=1.5,
                                    alpha=0.8))

    ax.invert_yaxis()


def draw_graph(ax, graph, state, title=''):
    """绘制通用�?""
    ax.clear()
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axis('off')

    # 绘制�?    path = state.get('path', [])
    path_edges = set()
    for i in range(len(path) - 1):
        path_edges.add((min(path[i], path[i+1]), max(path[i], path[i+1])))

    for (u, v, w) in graph.edges:
        x1, y1 = graph.nodes[u]
        x2, y2 = graph.nodes[v]
        is_path = (min(u, v), max(u, v)) in path_edges
        color = COLORS['path'] if is_path else COLORS['edge_default']
        width = 3 if is_path else 1
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, zorder=1)
        # 权重标签
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, str(w), fontsize=8, ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.8))

    # 绘制节点
    visited = state.get('visited', set())
    current = state.get('current', None)
    frontier = state.get('frontier', set())
    dist = state.get('dist', {})

    for node_id, (x, y) in graph.nodes.items():
        color = COLORS['node_default']
        if node_id == current:
            color = COLORS['current']
        elif node_id in visited:
            color = COLORS['visited']
        elif node_id in frontier:
            color = COLORS['frontier']

        ax.add_patch(Circle((x, y), 0.3, facecolor=color, edgecolor='white', linewidth=2, zorder=2))
        ax.text(x, y, str(node_id), ha='center', va='center', fontsize=10,
               fontweight='bold', color='white', zorder=3)

        # 显示距离（用�?Dijkstra�?        if node_id in dist and dist[node_id] != float('inf'):
            ax.text(x, y - 0.5, f'd={dist[node_id]}', ha='center', va='top', fontsize=8, color='#333')


def draw_astar_grid(ax, grid, state, title=''):
    """绘制 A* 网格（带 f/g 值标注）"""
    ax.clear()
    ax.set_xlim(-0.5, grid.cols - 0.5)
    ax.set_ylim(-0.5, grid.rows - 0.5)
    ax.set_aspect('equal')
    ax.set_xticks(range(grid.cols))
    ax.set_yticks(range(grid.rows))
    ax.set_title(title, fontsize=14, fontweight='bold')

    g = state.get('g', {})
    f = state.get('f', {})
    open_set = state.get('open', set())
    closed = state.get('closed', set())
    path = state.get('path', [])
    current = state.get('current', None)

    for r in range(grid.rows):
        for c in range(0, grid.cols):
            color = COLORS['empty']
            if grid.grid[r][c] == 1:
                color = COLORS['wall']
            elif (r, c) in closed:
                color = COLORS['visited']
            elif (r, c) in open_set:
                color = COLORS['frontier']

            ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                        facecolor=color, edgecolor='#bdc3c7', linewidth=0.5))

            # 显示 f �?            if (r, c) in f:
                ax.text(c, r, f'f={f[(r,c)]}\ng={g.get((r,c), "?")}',
                       ha='center', va='center', fontsize=7,
                       color='white' if color != COLORS['empty'] else '#333')

    if current:
        ax.add_patch(plt.Rectangle((current[1] - 0.5, current[0] - 0.5), 1, 1,
                                    facecolor=COLORS['current'], edgecolor='white', linewidth=2))

    for (r, c) in path:
        ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                    facecolor=COLORS['path'], edgecolor='white', linewidth=1.5,
                                    alpha=0.8))

    ax.invert_yaxis()


# ============== 动画创建函数 ==============

def create_grid_animation(grid, history, title, filename, draw_func):
    """创建网格动画"""
    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame):
        draw_func(ax, grid, history[frame], f'{title} (步骤 {frame+1}/{len(history)})')
        # 显示消息
        ax.set_xlabel(history[frame].get('message', ''), fontsize=10)

    ani = animation.FuncAnimation(fig, update, frames=len(history),
                                  interval=500, repeat=False)
    ani.save(filename, writer='pillow', fps=2)
    plt.close()
    print(f'  已保�? {filename}')


def create_graph_animation(graph, history, title, filename):
    """创建图动�?""
    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame):
        draw_graph(ax, graph, history[frame], f'{title} (步骤 {frame+1}/{len(history)})')
        ax.set_xlabel(history[frame].get('message', ''), fontsize=10)

    ani = animation.FuncAnimation(fig, update, frames=len(history),
                                  interval=800, repeat=False)
    ani.save(filename, writer='pillow', fps=1.25)
    plt.close()
    print(f'  已保�? {filename}')


# ============== 主函�?==============

def main():
    print('=' * 50)
    print('图搜索算法可视化演示')
    print('=' * 50)
    print()

    output_dir = 'D:/openclaw-home/.openclaw/workspace/计算机算�?可视�?'

    # ---- BFS ----
    print('[1/4] BFS 遍历动画生成�?..')
    bfs_grid = GridGraph(10, 15)
    # 创建迷宫
    walls = [(2, 3), (2, 4), (2, 5), (3, 5), (4, 5), (5, 5),
             (5, 6), (5, 7), (5, 8), (6, 8), (7, 8), (7, 7), (7, 6),
             (4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (8, 10), (8, 11)]
    for r, c in walls:
        bfs_grid.set_wall(r, c)

    bfs_history = visualize_bfs(bfs_grid, (1, 1), (8, 13))
    create_grid_animation(bfs_grid, bfs_history, 'BFS 广度优先搜索',
                         output_dir + 'bfs_demo.gif', draw_grid)

    # ---- DFS ----
    print('[2/4] DFS 遍历动画生成�?..')
    dfs_grid = GridGraph(10, 15)
    for r, c in walls:
        dfs_grid.set_wall(r, c)

    dfs_history = visualize_dfs(dfs_grid, (1, 1), (8, 13))
    create_grid_animation(dfs_grid, dfs_history, 'DFS 深度优先搜索',
                         output_dir + 'dfs_demo.gif', draw_grid)

    # ---- Dijkstra ----
    print('[3/4] Dijkstra 最短路径动画生成中...')
    dij_graph = Graph()
    # 创建带权重的�?    node_positions = {
        'A': (0, 0), 'B': (0, 1), 'C': (0, 2),
        'D': (1, 0), 'E': (1, 1), 'F': (1, 2),
        'G': (2, 0), 'H': (2, 1), 'I': (2, 2)
    }
    for node, pos in node_positions.items():
        dij_graph.add_node(node, *pos)

    # 添加边（带权重）
    edges = [
        ('A', 'B', 4), ('A', 'D', 2),
        ('B', 'C', 1), ('B', 'E', 3),
        ('C', 'F', 5),
        ('D', 'E', 1), ('D', 'G', 4),
        ('E', 'F', 2), ('E', 'H', 3),
        ('F', 'I', 2),
        ('G', 'H', 1),
        ('H', 'I', 4),
    ]
    for u, v, w in edges:
        dij_graph.add_edge(u, v, w)

    dij_history = visualize_dijkstra(dij_graph, 'A', 'I')
    create_graph_animation(dij_graph, dij_history, 'Dijkstra 最短路�?,
                          output_dir + 'dijkstra_demo.gif')

    # ---- A* ----
    print('[4/4] A* 寻路动画生成�?..')
    astar_grid = GridGraph(12, 16)
    # 创建随机迷宫
    import random
    random.seed(42)
    walls2 = set()
    for _ in range(40):
        r, c = random.randint(0, 11), random.randint(0, 15)
        if (r, c) not in [(1, 1), (10, 14)]:
            walls2.add((r, c))
    for r, c in walls2:
        astar_grid.set_wall(r, c)

    astar_history = visualize_astar(astar_grid, (1, 1), (10, 14))
    create_grid_animation(astar_grid, astar_history, 'A* 寻路算法',
                         output_dir + 'astar_demo.gif', draw_astar_grid)

    print()
    print('=' * 50)
    print('所有图搜索动画已生成完毕！')
    print('GIF文件位于: 可视�? 目录�?)
    print('=' * 50)


if __name__ == '__main__':
    main()


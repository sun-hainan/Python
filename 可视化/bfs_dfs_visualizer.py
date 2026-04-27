# -*- coding: utf-8 -*-

"""

算法实现：可视化 / bfs_dfs_visualizer



本文件实现 bfs_dfs_visualizer 相关的算法功能。

"""



import matplotlib.pyplot as plt

import matplotlib.patches as mpatches

import numpy as np

from collections import deque





def bfs(grid, start):

    """BFS 遍历，返回每步状态"""

    rows, cols = len(grid), len(grid[0])

    visited = [[False] * cols for _ in range(rows)]

    steps = []

    queue = deque([start])

    visited[start[0]][start[1]] = True



    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]



    while queue:

        x, y = queue.popleft()

        steps.append(((x, y), 'visit'))



        for dx, dy in directions:

            nx, ny = x + dx, y + dy

            if 0 <= nx < rows and 0 <= ny < cols and not visited[nx][ny] and grid[nx][ny] != '#':

                visited[nx][ny] = True

                queue.append((nx, ny))

                steps.append(((nx, ny), 'enqueue'))



    return steps





def dfs(grid, start):

    """DFS 遍历，返回每步状态"""

    rows, cols = len(grid), len(grid[0])

    visited = [[False] * cols for _ in range(rows)]

    steps = []

    stack = [start]

    visited[start[0]][start[1]] = True



    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]



    while stack:

        x, y = stack.pop()

        steps.append(((x, y), 'visit'))



        for dx, dy in directions:

            nx, ny = x + dx, y + dy

            if 0 <= nx < rows and 0 <= ny < cols and not visited[nx][ny] and grid[nx][ny] != '#':

                visited[nx][ny] = True

                stack.append((nx, ny))

                steps.append(((nx, ny), 'push'))



    return steps





def visualize_grid(grid, bfs_steps, dfs_steps, save_path='bfs_dfs_grid.png'):

    """可视化 BFS 和 DFS 在网格上的遍历过程"""

    rows, cols = len(grid), len(grid[0])



    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    fig.suptitle('BFS vs DFS 网格遍历可视化', fontsize=16)



    # BFS 图

    ax1 = axes[0]

    ax1.set_title('BFS（广度优先）- 队列实现，一圈一圈扩散', fontsize=12)

    ax1.set_xlim(-0.5, cols - 0.5)

    ax1.set_ylim(-0.5, rows - 0.5)

    ax1.set_aspect('equal')



    # 绘制网格

    for i in range(rows):

        for j in range(cols):

            color = 'black' if grid[i][j] == '#' else 'white'

            rect = mpatches.FancyBboxPatch((j - 0.45, rows - 1 - i - 0.45), 0.9, 0.9,

                                             boxstyle="round,pad=0.02",

                                             facecolor=color, edgecolor='gray')

            ax1.add_patch(rect)

            if grid[i][j] == '.':

                ax1.text(j, rows - 1 - i, '·', ha='center', va='center', fontsize=8, color='gray')



    # BFS 动画（只用最后几步展示）

    bfs_visited = set()

    for (x, y), action in bfs_steps[:min(10, len(bfs_steps))]:

        bfs_visited.add((x, y))



    for i, j in bfs_visited:

        rect = mpatches.FancyBboxPatch((j - 0.4, rows - 1 - i - 0.4), 0.8, 0.8,

                                         boxstyle="round,pad=0.02",

                                         facecolor='lightblue', edgecolor='blue', linewidth=2)

        ax1.add_patch(rect)

        ax1.text(j, rows - 1 - i, str(bfs_steps.index(next(s for s in bfs_steps if s[0] == (i, j)))),

                ha='center', va='center', fontsize=8, color='blue')



    ax1.text(0, -1, f'访问节点数: {len(set(s[0] for s in bfs_steps))}', fontsize=10)

    ax1.axis('off')



    # DFS 图

    ax2 = axes[1]

    ax2.set_title('DFS（深度优先）- 栈实现，一条路走到黑', fontsize=12)

    ax2.set_xlim(-0.5, cols - 0.5)

    ax2.set_ylim(-0.5, rows - 0.5)

    ax2.set_aspect('equal')



    # 绘制网格

    for i in range(rows):

        for j in range(cols):

            color = 'black' if grid[i][j] == '#' else 'white'

            rect = mpatches.FancyBboxPatch((j - 0.45, rows - 1 - i - 0.45), 0.9, 0.9,

                                             boxstyle="round,pad=0.02",

                                             facecolor=color, edgecolor='gray')

            ax2.add_patch(rect)

            if grid[i][j] == '.':

                ax2.text(j, rows - 1 - i, '·', ha='center', va='center', fontsize=8, color='gray')



    # DFS 动画

    dfs_visited = set()

    for (x, y), action in dfs_steps[:min(10, len(dfs_steps))]:

        dfs_visited.add((x, y))



    for i, j in dfs_visited:

        rect = mpatches.FancyBboxPatch((j - 0.4, rows - 1 - i - 0.4), 0.8, 0.8,

                                         boxstyle="round,pad=0.02",

                                         facecolor='lightgreen', edgecolor='green', linewidth=2)

        ax2.add_patch(rect)



    ax2.text(0, -1, f'访问节点数: {len(set(s[0] for s in dfs_steps))}', fontsize=10)

    ax2.axis('off')



    plt.tight_layout()

    plt.savefig(save_path, dpi=150, bbox_inches='tight')

    print(f"图片已保存: {save_path}")

    plt.show()





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== BFS/DFS 网格遍历可视化 ===\n")



    # 测试网格 (0=起点, .=空, #=障碍)

    grid = [

        ['.', '.', '.', '#', '.'],

        ['#', '.', '.', '.', '.'],

        ['.', '#', '.', '#', '.'],

        ['.', '.', '.', '.', '.'],

    ]

    start = (0, 0)



    print(f"网格:")

    for row in grid:

        print(' '.join(row))

    print(f"起点: {start}")

    print()



    bfs_steps = bfs(grid, start)

    dfs_steps = dfs(grid, start)



    print(f"BFS 访问顺序: {[s[0] for s in bfs_steps if s[1] == 'visit']}")

    print(f"DFS 访问顺序: {[s[0] for s in dfs_steps if s[1] == 'visit']}")

    print()



    visualize_grid(grid, bfs_steps, dfs_steps)


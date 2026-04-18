"""
A* 寻路算法 - 中文注释版
==========================================

算法原理：
    A* 是最经典的启发式搜索算法，用于在网格/图中找到从起点到终点的最短路径。
    它结合了 Dijkstra（依赖实际距离）和贪心（依赖启发式估计）的优点。

核心公式：
    f(n) = g(n) + h(n)
    - g(n)：从起点到当前节点的实际代价
    - h(n)：从当前节点到终点的估计代价（启发函数）
    - f(n)：综合评估值，越小越先被探索

启发函数的选择：
    - Manhattan 距离（4方向移动）
    - Euclidean 距离（8方向或自由移动）
    - 对角线距离（允许对角移动）

A* vs Dijkstra：
    - Dijkstra：h(n) = 0，相当于 A* 的特例
    - A*：通过启发函数引导搜索方向，比 Dijkstra 快

时间复杂度：O(E log V)
空间复杂度：O(V)
"""

from __future__ import annotations

# 四个方向：左、下、右、上
DIRECTIONS = [
    [-1, 0],  # left
    [0, -1],  # down
    [1, 0],   # right
    [0, 1],   # up
]


def search(
    grid: list[list[int]],
    init: list[int],
    goal: list[int],
    cost: int,
    heuristic: list[list[int]],
) -> tuple[list[list[int]], list[list[int]]]:
    """
    A* 寻路算法

    参数:
        grid: 网格地图，0=可通行，1=障碍物
        init: 起点坐标 [y, x]
        goal: 终点坐标 [y, x]
        cost: 移动代价（通常为1）
        heuristic: 每个格子的启发值矩阵（Manhattan距离或更大值表示障碍惩罚）

    返回:
        (最短路径坐标列表, 方向指令矩阵)

    示例:
        >>> grid = [[0, 1, 0, 0, 0, 0],
        ...        [0, 1, 0, 0, 0, 0],
        ...        [0, 1, 0, 0, 0, 0],
        ...        [0, 1, 0, 0, 1, 0],
        ...        [0, 0, 0, 0, 1, 0]]
        >>> init = [0, 0]
        >>> goal = [len(grid) - 1, len(grid[0]) - 1]
        >>> path, action = search(grid, init, goal, 1, [[0]*6 for _ in range(5)])
        >>> len(path) > 0
        True
    """
    closed = [[0 for _ in range(len(grid[0]))] for _ in range(len(grid))]
    closed[init[0]][init[1]] = 1
    action = [[0 for _ in range(len(grid[0]))] for _ in range(len(grid))]

    x, y = init[0], init[1]
    g = 0
    f = g + heuristic[x][y]  # f = g + h
    cell = [[f, g, x, y]]  # (评估值, 实际代价, 坐标)

    found = False
    resign = False

    while not found and not resign:
        if len(cell) == 0:
            raise ValueError("A* 无法找到解")

        cell.sort()
        cell.reverse()
        next_cell = cell.pop()
        x, y = next_cell[2], next_cell[3]
        g = next_cell[1]

        if x == goal[0] and y == goal[1]:
            found = True
        else:
            # 尝试四个方向
            for i in range(len(DIRECTIONS)):
                x2 = x + DIRECTIONS[i][0]
                y2 = y + DIRECTIONS[i][1]
                if (
                    0 <= x2 < len(grid)
                    and 0 <= y2 < len(grid[0])
                    and closed[x2][y2] == 0
                    and grid[x2][y2] == 0
                ):
                    g2 = g + cost
                    f2 = g2 + heuristic[x2][y2]
                    cell.append([f2, g2, x2, y2])
                    closed[x2][y2] = 1
                    action[x2][y2] = i

    # 回溯路径
    invpath = []
    x, y = goal[0], goal[1]
    invpath.append([x, y])
    while x != init[0] or y != init[1]:
        x2 = x - DIRECTIONS[action[x][y]][0]
        y2 = y - DIRECTIONS[action[x][y]][1]
        x, y = x2, y2
        invpath.append([x, y])

    path = [invpath[len(invpath) - 1 - i] for i in range(len(invpath))]
    return path, action


if __name__ == "__main__":
    grid = [
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],  # 0=通路, 1=障碍
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 0, 0, 0, 1, 0],
    ]
    init = [0, 0]
    goal = [len(grid) - 1, len(grid[0]) - 1]
    cost = 1

    # 启发函数：Manhattan 距离
    heuristic = [[0 for _ in range(len(grid[0]))] for _ in range(len(grid))]
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            heuristic[i][j] = abs(i - goal[0]) + abs(j - goal[1])
            if grid[i][j] == 1:
                heuristic[i][j] = 99  # 障碍物惩罚

    path, action = search(grid, init, goal, cost, heuristic)
    print("路径:")
    for p in path:
        print(p)

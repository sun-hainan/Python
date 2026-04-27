# -*- coding: utf-8 -*-
"""
算法实现：04_图算法 / g_topological_sort

本文件实现 g_topological_sort 相关的算法功能。
"""

from __future__ import annotations


# 穿衣示例：每天早上穿衣的顺序
clothes = {
    0: "内衣",
    1: "裤子",
    2: "腰带",
    3: "外套",
    4: "鞋子",
    5: "袜子",
    6: "衬衫",
    7: "领带",
    8: "手表",
}

# 依赖关系：有向边表示"必须先穿"
# 例如 [1, 4] 表示穿裤子之前必须先穿鞋子
graph = [
    [1, 4],   # 0: 内衣 -> 裤子, 鞋子
    [2, 4],   # 1: 裤子 -> 腰带, 鞋子
    [3],      # 2: 腰带 -> 外套
    [],       # 3: 外套（无后继）
    [],       # 4: 鞋子（无后继）
    [4],      # 5: 袜子 -> 鞋子
    [2, 7],   # 6: 衬衫 -> 腰带, 领带
    [3],      # 7: 领带 -> 外套
    [],       # 8: 手表（无后继）
]

visited = [0 for _ in range(len(graph))]
stack = []


def print_stack(stack: list, items: dict):
    """打印栈内容"""
    order = 1
    while stack:
        current = stack.pop()
        print(f"{order}. {items[current]}")
        order += 1


def depth_first_search(u: int):
    """
    DFS 遍历

    参数:
        u: 当前顶点
    """
    visited[u] = 1
    for v in graph[u]:
        if not visited[v]:
            depth_first_search(v)
    stack.append(u)  # 所有后继访问完毕后入栈


def topological_sort(graph: list, visited: list):
    """
    拓扑排序主函数

    参数:
        graph: 邻接表
        visited: 访问标记数组
    """
    for v in range(len(graph)):
        if not visited[v]:
            depth_first_search(v)


if __name__ == "__main__":
    topological_sort(graph, visited)

    print("拓扑排序结果（穿衣顺序）:")
    print_stack(stack, clothes)

    # 预期顺序：袜子(5) -> 鞋子(4) -> 内衣(0) -> 裤子(1) -> 腰带(2) -> 衬衫(6) -> 领带(7) -> 外套(3) -> 手表(8)

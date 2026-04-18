"""
拓扑排序 (Topological Sort) - 中文注释版
==========================================

问题定义：
    对有向无环图（DAG）的所有顶点进行线性排序，
    使得对于每条有向边 (u, v)，顶点 u 都在 v 之前。

应用场景：
    - 任务调度（先修课程、工程项目）
    - 编译顺序（Makefile 依赖）
    - 碗碗获取顺序
    - 课程表安排

算法思想（DFS + 栈）：
    1. 对图进行 DFS
    2. 当一个顶点的所有邻居都被访问后，将其加入栈
    3. 最后从栈顶弹出元素，得到拓扑排序（逆序）

为什么有效？
    - DFS 保证了一个顶点在所有后继都被访问后才入栈
    - 因此弹出的顺序保证前驱在后面之前

时间复杂度：O(V + E)
空间复杂度：O(V)
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

"""
欧拉路径与欧拉回路 (Eulerian Path & Circuit) - 中文注释版
==========================================

欧拉路径定义：
    一条路径经过图中每条边恰好一次

欧拉回路定义：
    一条欧拉路径，且起点和终点相同（闭合回路）

判断条件（无向图）：
    - 欧拉回路：所有顶点度数为偶数，且图连通
    - 欧拉路径：恰好两个顶点度数为奇数，其余为偶数，且图连通

Hierholzer 算法（求欧拉路径）：
    1. 从满足条件的顶点开始（奇度数顶点或任意顶点）
    2. 沿着边遍历，直到回到起点（形成回路）
    3. 如果还有未遍历的边，将回路切开，从未遍历边的顶点继续
    4. 将新回路合并到原回路中

时间复杂度：O(V + E)
空间复杂度：O(V + E)
"""


def dfs(u, graph, visited_edge, path=None):
    """
    Hierholzer 算法核心：深度优先遍历收集路径

    参数:
        u: 当前顶点
        graph: 邻接表
        visited_edge: 边访问记录矩阵
        path: 累计的路径

    返回:
        从 u 开始的欧拉路径
    """
    path = (path or []) + [u]
    for v in graph[u]:
        if visited_edge[u][v] is False:
            visited_edge[u][v] = visited_edge[v][u] = True
            path = dfs(v, graph, visited_edge, path)
    return path


def check_circuit_or_path(graph, max_node):
    """
    检查图中奇度数顶点的数量

    返回:
        (1, odd_node): 欧拉回路（0个奇度数顶点）
        (2, odd_node): 欧拉路径（2个奇度数顶点）
        (3, -1): 非欧拉图
    """
    odd_degree_nodes = 0
    odd_node = -1

    for i in range(max_node):
        if i not in graph:
            continue
        if len(graph[i]) % 2 == 1:
            odd_degree_nodes += 1
            odd_node = i

    if odd_degree_nodes == 0:
        return 1, odd_node  # 欧拉回路
    if odd_degree_nodes == 2:
        return 2, odd_node  # 欧拉路径
    return 3, odd_node  # 非欧拉图


def check_euler(graph, max_node):
    """
    判断并求解欧拉路径/回路

    参数:
        graph: 邻接表，格式 {顶点: [邻居列表], ...}
        max_node: 最大顶点编号
    """
    visited_edge = [[False for _ in range(max_node + 1)] for _ in range(max_node + 1)]
    check, odd_node = check_circuit_or_path(graph, max_node)

    if check == 3:
        print("此图不是欧拉图，无欧拉路径")
        return

    # 确定起始顶点
    start_node = 1
    if check == 2:
        start_node = odd_node
        print("此图有欧拉路径")
    if check == 1:
        print("此图有欧拉回路")

    path = dfs(start_node, graph, visited_edge)
    print(f"欧拉路径: {path}")


def main():
    # 示例测试
    # g1: 欧拉路径
    g1 = {1: [2, 3, 4], 2: [1, 3], 3: [1, 2], 4: [1, 5], 5: [4]}
    # g2: 欧拉回路
    g2 = {1: [2, 3, 4, 5], 2: [1, 3], 3: [1, 2], 4: [1, 5], 5: [1, 4]}
    # g3: 非欧拉图
    g3 = {1: [2, 3, 4], 2: [1, 3, 4], 3: [1, 2], 4: [1, 2, 5], 5: [4]}
    # g4: 简单三角形（欧拉回路）
    g4 = {1: [2, 3], 2: [1, 3], 3: [1, 2]}
    # g5: 空图
    g5 = {1: [], 2: []}

    print("=== g1 (欧拉路径) ===")
    check_euler(g1, 10)
    print("\n=== g2 (欧拉回路) ===")
    check_euler(g2, 10)
    print("\n=== g4 (欧拉回路) ===")
    check_euler(g4, 10)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / fixed_parameter



本文件实现 fixed_parameter 相关的算法功能。

"""



import random

from typing import List, Set, Tuple





def bounded_search_depth(edges: List[Tuple[int, int]], k: int, n: int) -> bool:

    """

    有界搜索深度算法



    模拟 Vertex Cover 的简单FPT算法



    参数：

        edges: 边列表

        k: 参数（允许的选择数）

        n: 顶点数



    返回：是否存在大小<=k的顶点覆盖

    """

    # 如果没有边，满足

    if not edges:

        return True



    # 如果已经选了k个顶点但还有边，不满足

    if k == 0:

        return len(edges) == 0



    # 随便选一条边

    u, v = edges[0]



    # 分支1：选u

    edges_without_u = [(a, b) for a, b in edges if a != u and b != u]

    if bounded_search_depth(edges_without_u, k - 1, n):

        return True



    # 分支2：选v

    edges_without_v = [(a, b) for a, b in edges if a != v and b != v]

    if bounded_search_depth(edges_without_v, k - 1, n):

        return True



    return False





def fpt_vertex_cover(edges: List[Tuple[int, int]], k: int, n: int) -> bool:

    """

    FPT顶点覆盖算法



    时间复杂度: O(2^k * n)

    """

    return bounded_search_depth(edges, k, n)





def kernelization_vertex_cover(edges: List[Tuple[int, int]], k: int) -> Tuple[List[Tuple[int, int]], int]:

    """

    核化（Kernelization）



    将问题规模缩减到只依赖参数k



    参数：

        edges: 边列表

        k: 参数



    返回：(缩减后的边, 新的参数)

    """

    # 简单核化：如果边数 > k*n，则必定有解

    # 或者：如果某个顶点度 > k，则必须在解中



    n = max(max(u, v) for u, v in edges) + 1 if edges else 0

    reduced_edges = list(edges)

    new_k = k



    # 贪心核化：删除度大于k的顶点（它们必须在覆盖中）

    changed = True

    while changed and new_k > 0:

        changed = False



        # 构建邻接表

        adj = {i: [] for i in range(n)}

        for u, v in reduced_edges:

            if u < n:

                adj[u].append(v)

            if v < n:

                adj[v].append(u)



        # 找度>k的顶点

        for v in range(n):

            if len(adj[v]) > new_k:

                # v必须在覆盖中

                new_k -= 1

                # 删除v及其关联的边

                reduced_edges = [(a, b) for a, b in reduced_edges if a != v and b != v]

                changed = True

                break



    return reduced_edges, new_k





def color_verification(graph: List[List[int]], colors: List[int], k: int) -> bool:

    """

    验证图是否可以用k种颜色着色



    这是着色问题的FPT检查

    """

    n = len(graph)



    for i in range(n):

        used = set()

        for j in graph[i]:

            if colors[j] == colors[i] and i != j:

                return False



    return True





def iterative_deepening_vertex_cover(edges: List[Tuple[int, int]], k: int, n: int) -> bool:

    """

    迭代深化（Iterative Deepening）



    从k=0开始，逐渐增加深度

    """

    for current_k in range(k + 1):

        if fpt_vertex_cover(edges, current_k, n):

            return True

    return False





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 固定参数算法测试 ===\n")



    # 创建简单图

    n = 10

    edges = [

        (0, 1), (0, 2), (1, 3), (2, 3), (3, 4),

        (4, 5), (5, 6), (6, 7), (7, 8), (8, 9),

        (0, 9), (1, 8), (2, 7), (3, 6), (4, 5),

    ]



    print(f"顶点数: {n}, 边数: {len(edges)}")



    # 测试不同k值

    for k in [3, 4, 5, 6]:

        result = fpt_vertex_cover(edges, k, n)

        print(f"Vertex Cover k={k}: {'存在' if result else '不存在'}")



    print()



    # 核化测试

    print("核化演示:")

    reduced, new_k = kernelization_vertex_cover(edges, 5)

    print(f"  原始边数: {len(edges)}")

    print(f"  核化后边数: {len(reduced)}")

    print(f"  新参数: {new_k}")



    print("\n说明：")

    print("  - FPT: O(f(k) * n^c)")

    print("  - 核化: 将问题规模缩减到只依赖k")

    print("  - 如果k很小，即使n很大也能快速求解")


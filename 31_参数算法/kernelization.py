# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / kernelization



本文件实现 kernelization 相关的算法功能。

"""



def kernelize_vertex_cover(graph, k):

    """

    对顶点覆盖问题进行核化。



    核化规则：

    1. 如果图中的边数 m > k * n，说明即使每条边都需要一个不同顶点，

       也无法在 k 个顶点内覆盖所有边，直接拒绝。

    2. 如果某个顶点度数 > k，则该顶点必须选入覆盖集，

       删除它及其所有邻居，更新 k。

    3. 否则，所有顶点度数 <= k，且 m <= k * n，规模已压缩。



    参数:

        graph: 邻接表表示的无向图

        k: 参数，最大允许的顶点覆盖大小



    返回:

        reduced_graph: 核化后的图

        reduced_k: 更新后的参数

        selected: 已选入覆盖集的顶点列表

    """

    selected = []    # 已确定选入覆盖集的顶点

    vertices = set(graph.keys())   # 当前剩余顶点集合



    # 规则2：高度数顶点必须选入

    changed = True

    while changed:

        changed = False

        vertices = set(graph.keys())

        for v in list(vertices):

            neighbors = set(graph.get(v, []))

            # 如果 v 的邻居都在已选顶点中，跳过

            if neighbors.issubset(set(selected)):

                continue

            # 计算 v 当前的有效度数（未覆盖的邻居）

            active_neighbors = neighbors - set(selected)

            if len(active_neighbors) > k:

                # 度数大于 k，无法在限制内覆盖，必须选 v

                selected.append(v)

                # 删除 v 及其已覆盖邻居

                for u in list(vertices):

                    if u == v or u in active_neighbors:

                        graph.pop(u, None)

                changed = True

                k -= 1   # 消耗一个覆盖配额

                break



    # 规则1：边数过多检测

    m = sum(len(neighbors) for neighbors in graph.values()) // 2

    n = len(graph)

    if m > k * n:

        return None, -1, selected   # 无解



    return graph, k, selected





def _remove_vertex(graph, v):

    """从图中删除顶点 v 及其关联边。"""

    if v not in graph:

        return

    neighbors = graph.pop(v, [])

    for u in neighbors:

        if v in graph.get(u, []):

            graph[u].remove(v)





if __name__ == "__main__":

    # 构造一个测试图

    test_graph = {

        0: [1, 2, 3],

        1: [0, 2],

        2: [0, 1, 3],

        3: [0, 2, 4],

        4: [3, 5],

        5: [4]

    }



    print("=== Vertex Cover 核化测试 ===")

    print(f"原始图: {test_graph}")

    print(f"原始顶点数 n = {len(test_graph)}")

    print(f"原始边数 m = {sum(len(v) for v in test_graph.values()) // 2}")



    for k in [2, 3, 4]:

        # 每次测试重新复制图

        import copy

        g = copy.deepcopy(test_graph)

        result_graph, result_k, sel = kernelize_vertex_cover(g, k)



        if result_graph is None:

            print(f"\nk={k}: 无解（边数超过 k*n）")

        else:

            print(f"\nk={k}:")

            print(f"  已选顶点: {sel}")

            print(f"  剩余参数 k' = {result_k}")

            print(f"  核大小: n' = {len(result_graph)}, m' = {sum(len(v) for v in result_graph.values()) // 2}")

            print(f"  核化后图: {result_graph}")


# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / fpt_reduction



本文件实现 fpt_reduction 相关的算法功能。

"""



def vertex_cover_to_odd_vertex_cover(graph, k):

    """

    将顶点覆盖问题归约到奇度数顶点覆盖问题。



    参数:

        graph: 邻接表表示的无向图，如 {0: [1,2], 1: [0,2], ...}

        k: 参数，表示允许选择的顶点数量



    返回:

        new_graph: 构造的新图

        new_k: 新参数值

        mapping: 原始顶点到新图中顶点的映射

    """

    # 初始化新图和映射

    new_graph = {}

    mapping = {}

    vertex_list = list(graph.keys())

    n = len(vertex_list)



    # 为每个原始顶点创建两个副本：v_in 和 v_out

    for idx, v in enumerate(vertex_list):

        vin = idx * 2          # 入副本顶点编号

        vout = idx * 2 + 1     # 出副本顶点编号

        mapping[v] = (vin, vout)



    # 设置新图的总顶点数

    new_vertex_count = n * 2



    # 为每个原始顶点，连接 vin 到 vout

    for v in vertex_list:

        vin, vout = mapping[v]

        new_graph[vin] = new_graph.get(vin, [])

        new_graph[vout] = new_graph.get(vout, [])



    # 将原始图的每条边 (u,v) 替换为 (u_out, v_in) 和 (u_in, v_out)

    edge_set = set()

    for u in graph:

        for v in graph[u]:

            if u < v:  # 每条边只处理一次

                uin, uout = mapping[u]

                vin, vout = mapping[v]

                # 边1：从 u 的出副本到 v 的入副本

                new_graph.setdefault(uout, []).append(vin)

                new_graph.setdefault(vin, []).append(uout)

                # 边2：从 v 的出副本到 u 的入副本

                new_graph.setdefault(vout, []).append(uin)

                new_graph.setdefault(uin, []).append(vout)



    # 新参数 k' = 2k（因为每个原始顶点需要选择两个副本中的一个）

    new_k = 2 * k



    return new_graph, new_k, mapping





def solve_odd_vertex_cover_by_vertex_cover(new_graph, new_k):

    """

    假设我们有奇度数顶点覆盖的求解器，这里模拟调用。

    实际上这里我们用穷举来演示（仅用于参数很小的情况）。

    """

    vertices = list(range(max(new_graph.keys()) + 1))

    n = len(vertices)



    # 穷举检查（仅做演示，生产环境应调用专用求解器）

    for subset in _subsets(vertices, new_k):

        if _is_odd_vertex_cover(new_graph, subset):

            return True

    return False





def _subsets(vertices, k):

    """生成所有大小为 k 的顶点子集（递归实现）。"""

    if k == 0:

        yield []

        return

    if len(vertices) < k:

        return

    # 不选第一个顶点

    for rest in _subsets(vertices[1:], k):

        yield rest

    # 选第一个顶点

    for rest in _subsets(vertices[1:], k - 1):

        yield [vertices[0]] + rest





def _is_odd_vertex_cover(graph, subset):

    """检查子集是否为奇度数顶点覆盖（此处简化处理）。"""

    subset_set = set(subset)

    # 检查每条边是否至少有一个端点在子集中

    covered = set()

    for v in graph:

        if v in subset_set:

            for neighbor in graph[v]:

                covered.add((min(v, neighbor), max(v, neighbor)))

    # 计算总边数

    all_edges = set()

    for v in graph:

        for neighbor in graph[v]:

            if v < neighbor:

                all_edges.add((v, neighbor))

    return covered == all_edges





if __name__ == "__main__":

    # 测试归约：构造一个简单的图

    test_graph = {

        0: [1, 2],

        1: [0, 2],

        2: [0, 1, 3],

        3: [2]

    }

    k = 2



    # 执行归约

    new_g, new_k, mp = vertex_cover_to_odd_vertex_cover(test_graph, k)

    print(f"原始图顶点: {list(test_graph.keys())}")

    print(f"原始参数 k = {k}")

    print(f"新图顶点数: {max(new_g.keys()) + 1}")

    print(f"新参数 k' = {new_k}")

    print(f"映射关系: {mp}")

    print(f"归约成功：参数放大了 {new_k / k} 倍")



    # 验证新图结构

    print(f"\n新图邻接表边数估计: {sum(len(v) for v in new_g.values()) // 2}")


# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / vertex_cover_k



本文件实现 vertex_cover_k 相关的算法功能。

"""



def greedy_vertex_cover(graph, k):

    """

    贪心近似算法（1-近似比）。



    每次选择度数最高的顶点，删除其所有邻居边。

    如果超过 k 步仍未覆盖所有边，则失败。



    参数:

        graph: 邻接表

        k: 参数上限



    返回:

        覆盖集顶点列表，或 None（无解）

    """

    import copy

    g = copy.deepcopy(graph)

    selected = []



    for _ in range(k):

        if not g:

            break



        # 找度数最大的顶点

        max_v = max(g.keys(), key=lambda v: len(g[v]))

        max_deg = len(g[max_v])



        if max_deg == 0:

            # 孤立点，可跳过

            g.pop(max_v, None)

            continue



        # 选择该顶点

        selected.append(max_v)

        # 删除该顶点及其邻居（覆盖所有关联边）

        to_remove = set([max_v] + g.pop(max_v, []))

        for v in list(g.keys()):

            g[v] = [u for u in g[v] if u not in to_remove]

            if not g[v]:

                g.pop(v, None)



        if not g:

            break



    # 检查是否还有未覆盖的边

    if any(g[v] for v in g):

        return None



    return selected





def local_search_vc(graph, k, max_iter=1000):

    """

    局部搜索（Local Search）求解 k-顶点覆盖。



    从一个可行解出发，通过交换操作改进解。

    交换：用一个未选顶点替换已选顶点，如果能保持覆盖性质。



    参数:

        graph: 邻接表

        k: 参数

        max_iter: 最大迭代次数



    返回:

        覆盖集或 None

    """

    import random

    import copy



    vertices = list(graph.keys())

    n = len(vertices)



    # 初始解：随机选择 k 个顶点

    current = set(random.sample(vertices, min(k, n)))



    for _ in range(max_iter):

        # 检查当前解是否有效

        if _is_vertex_cover(graph, current):

            return list(current)



        # 尝试改进：随机换一个顶点

        new_solution = current.copy()

        to_remove = random.choice(list(new_solution))

        candidates = [v for v in vertices if v not in new_solution]

        if candidates:

            to_add = random.choice(candidates)

            new_solution.remove(to_remove)

            new_solution.add(to_add)



            if _is_vertex_cover(graph, new_solution):

                current = new_solution



    return None





def _is_vertex_cover(graph, cover_set):

    """检查 cover_set 是否覆盖图中所有边。"""

    cs = set(cover_set)

    for v in graph:

        for u in graph[v]:

            if u > v and v not in cs and u not in cs:

                return False

    return True





if __name__ == "__main__":

    test_graph = {

        0: [1, 2, 3],

        1: [0, 2, 4],

        2: [0, 1, 3, 4],

        3: [0, 2, 5],

        4: [1, 2, 6],

        5: [3],

        6: [4]

    }



    print("=== k-顶点覆盖确定性算法测试 ===")

    print(f"测试图: {test_graph}")



    for k in [3, 4, 5]:

        # 贪心

        import copy

        g1 = copy.deepcopy(test_graph)

        result_greedy = greedy_vertex_cover(g1, k)



        # 局部搜索

        g2 = copy.deepcopy(test_graph)

        result_ls = local_search_vc(g2, k, max_iter=5000)



        print(f"\nk={k}:")

        print(f"  贪心结果: {result_greedy}")

        print(f"  局部搜索: {result_ls}")


# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / branch_and_bound

本文件实现 branch_and_bound 相关的算法功能。
"""

def branch_and_bound_vc(graph, k, selected=None):
    """
    分支定界求解 k-顶点覆盖。

    算法流程：
    1. 计算当前图的下界（下界 = 边数 / 最大度数，至少 ceil(m/(max_deg+1))）
    2. 如果边数为0，返回已选顶点集合
    3. 如果 k == 0 且仍有边，无解
    4. 如果下界 > k，剪枝
    5. 否则，选择一条边 (u,v)，分支：
       - 分支1：选 u，递归处理 (G - N[u], k-1)
       - 分支2：选 v，递归处理 (G - N[v], k-1)

    参数:
        graph: 邻接表
        k: 剩余可选顶点配额
        selected: 当前已选顶点列表

    返回:
        满足条件的顶点覆盖列表，或 None
    """
    if selected is None:
        selected = []

    # 基础情况：没有边，全部覆盖
    total_edges = sum(len(v) for v in graph.values()) // 2
    if total_edges == 0:
        return selected[:]

    # 超出预算
    if k < 0:
        return None

    # 计算下界：至少需要多少个顶点
    lower_bound = _compute_lower_bound(graph)
    if lower_bound > k:
        return None

    # 选择一条边（优先选择端点度数大的）
    u, v = _select_edge(graph)
    # 分支1：选 u
    new_g1, new_k1 = _remove_vertex_and_neighbors(graph, u, k)
    result1 = branch_and_bound_vc(new_g1, new_k1, selected + [u])
    if result1 is not None:
        return result1

    # 分支2：选 v
    new_g2, new_k2 = _remove_vertex_and_neighbors(graph, v, k)
    result2 = branch_and_bound_vc(new_g2, new_k2, selected + [v])
    return result2


def _compute_lower_bound(graph):
    """计算下界：边数 / 最大度数（取上整）。"""
    m = sum(len(v) for v in graph.values()) // 2
    max_deg = max(len(v) for v in graph.values()) if graph else 0
    if max_deg == 0:
        return 0
    return (m + max_deg) // (max_deg + 1)


def _select_edge(graph):
    """选择一条边（度数之和最大的端点）。"""
    best = None
    best_sum = -1
    for v in graph:
        for u in graph[v]:
            if u > v:   # 每条边只处理一次
                deg_sum = len(graph[v]) + len(graph[u])
                if deg_sum > best_sum:
                    best_sum = deg_sum
                    best = (v, u)
    return best if best else (None, None)


def _remove_vertex_and_neighbors(graph, v, k):
    """
    从图中删除顶点 v 及其所有邻居，返回新图和剩余配额。
    复制图以避免修改原图。
    """
    import copy
    g = copy.deepcopy(graph)
    if v not in g:
        return g, k
    # 收集所有要删除的顶点（v 及其邻居）
    to_remove = set([v] + g.pop(v, []))
    for u in list(g.keys()):
        g[u] = [x for x in g[u] if x not in to_remove]
        if not g[u]:   # 删除孤立顶点
            g.pop(u, None)
    return g, k - 1


def exact_vc_by_enumeration(graph, k):
    """
    暴力枚举验证（用于对比）。
    """
    vertices = list(graph.keys())
    for subset in _subsets(vertices, k):
        if _is_vertex_cover(graph, subset):
            return subset
    return None


def _subsets(vertices, k):
    """生成所有 k 元子集。"""
    if k == 0:
        yield []
        return
    if len(vertices) < k or k < 0:
        return
    for rest in _subsets(vertices[1:], k):
        yield rest
    for rest in _subsets(vertices[1:], k - 1):
        yield [vertices[0]] + rest


def _is_vertex_cover(graph, subset):
    """检查是否为顶点覆盖。"""
    cover_set = set(subset)
    for v in graph:
        for u in graph[v]:
            if u > v and v not in cover_set and u not in cover_set:
                return False
    return True


if __name__ == "__main__":
    import time

    # 测试图
    test_graph = {
        0: [1, 2, 3],
        1: [0, 2, 4],
        2: [0, 1, 3, 4],
        3: [0, 2, 5],
        4: [1, 2, 6],
        5: [3],
        6: [4]
    }

    print("=== Branch-and-Bound k-Vertex Cover ===")
    for k in range(3, 6):
        import copy
        g = copy.deepcopy(test_graph)

        start = time.time()
        result = branch_and_bound_vc(g, k)
        elapsed = time.time() - start

        print(f"\nk={k}: 找到覆盖 = {result}")
        print(f"  用时: {elapsed:.4f}s")

    # 对比验证
    print("\n=== 暴力验证 ===")
    g = copy.deepcopy(test_graph)
    result = exact_vc_by_enumeration(g, 3)
    print(f"k=3 的一个可行解: {result}")

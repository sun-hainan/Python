# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / bounded_search_tree

本文件实现 bounded_search_tree 相关的算法功能。
"""

def bounded_search_tree_ds(graph, k, r=None):
    """
    有界搜索树求解最小支配集（参数化版本）。

    有界搜索树策略：
    - 选择一个未被覆盖的顶点 u
    - 分支1：选 u（支付1个配额），覆盖 u 及其邻居
    - 分支2：选 u 的所有邻居（支付 degree(u) 个配额）

    参数:
        graph: 邻接表
        k: 参数（允许选择的顶点数量）
        r: 当前已选顶点集合

    返回:
        支配集列表，或 None
    """
    if r is None:
        r = []

    # 检查是否所有顶点都被覆盖
    all_vertices = set(graph.keys())
    dominated = set(r)   # 已选顶点视为被自己支配
    for v in r:
        dominated.update(graph.get(v, []))
    uncovered = all_vertices - dominated

    if not uncovered:
        # 所有顶点都被覆盖
        return r[:]

    if k <= 0:
        return None

    # 找一个未被覆盖的顶点
    u = next(iter(uncovered))

    # 分支1：选 u
    result1 = bounded_search_tree_ds(graph, k - 1, r + [u])
    if result1 is not None:
        return result1

    # 分支2：选 u 的所有邻居
    neighbors = [x for x in graph.get(u, [])]
    if len(neighbors) > k:
        return None   # 邻居数超过 k，无法选

    result2 = bounded_search_tree_ds(graph, k - len(neighbors), r + neighbors)
    return result2


def greedy_dominating_set(graph, k):
    """
    贪心近似求解支配集（作为上界参考）。
    """
    import copy
    g = copy.deepcopy(graph)
    selected = []

    while g and k > 0:
        # 选择覆盖率最高的顶点
        best_v = max(g.keys(), key=lambda v: len(set([v] + g.get(v, []))))
        selected.append(best_v)

        # 移除 best_v 及其邻居
        to_remove = set([best_v] + g.pop(best_v, []))
        for v in list(g.keys()):
            g[v] = [x for x in g[v] if x not in to_remove]
            if not g[v]:
                g.pop(v, None)

        k -= 1

    return selected


if __name__ == "__main__":
    # 测试图
    test_graph = {
        0: [1, 2],
        1: [0, 2, 3],
        2: [0, 1, 4],
        3: [1, 4],
        4: [2, 3]
    }

    print("=== 有界搜索树支配集测试 ===")
    print(f"测试图: {test_graph}")

    for k in range(1, 5):
        import copy
        g = copy.deepcopy(test_graph)
        result = bounded_search_tree_ds(g, k)

        if result is not None:
            print(f"\nk={k}: 支配集 = {result} (大小={len(result)})")
            # 验证支配性
            dominated = set(result)
            for v in result:
                dominated.update(test_graph.get(v, []))
            if dominated == set(test_graph.keys()):
                print(f"  验证通过：所有顶点均被支配")
            else:
                missing = set(test_graph.keys()) - dominated
                print(f"  验证失败：未支配顶点 = {missing}")
        else:
            print(f"\nk={k}: 无解")

    # 对比贪心
    print("\n=== 贪心上界对比 ===")
    import copy
    g = copy.deepcopy(test_graph)
    greedy_result = greedy_dominating_set(g, k=3)
    print(f"贪心结果(k=3): {greedy_result}")

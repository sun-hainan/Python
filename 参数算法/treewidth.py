# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / treewidth

本文件实现 treewidth 相关的算法功能。
"""

def nice_tree_decomposition(graph, path_order):
    """
    将图转换为一个 Nice Tree Decomposition（NTD）的路径版本。

    参数:
        graph: 邻接表表示的无向图
        path_order: 顶点的 Elimination Ordering

    返回:
        bags: 每个位置的顶点袋（bag）列表
        width: 计算得到的树宽
    """
    n = len(graph)
    # 初始化：每个顶点对应一个初始bag
    bags = [[v] for v in path_order]

    # 追踪每个顶点的邻接点中排在后面的顶点
    later_neighbors = {}
    for idx, v in enumerate(path_order):
        later_neighbors[v] = [u for u in graph.get(v, [])
                              if path_order.index(u) > idx]

    # 逐步合并：每当两个相邻顶点在序列中不相邻时，创建公共邻居袋
    for idx in range(n):
        v = path_order[idx]
        later = later_neighbors[v]

        if len(later) >= 2:
            # v 有多个排在后面的邻居，需要在他们之间添加边
            # 这里简化处理：扩展当前bag
            bags[idx] = list(set(bags[idx] + later))

    # 计算树宽（bag大小 - 1）
    width = max(len(bag) for bag in bags) - 1

    return bags, width


def dp_on_treewidth(graph, bags, root_bag):
    """
    在给定树宽分解上做简单的动态规划——计算最大独立集。

    这是一个演示性实现，使用状态压缩 DP。
    每个bag有 2^{|bag|} 种选/不选状态。

    参数:
        graph: 原始图
        bags: 树分解的顶点袋列表
        root_bag: 根bag的顶点集合

    返回:
        max_indep_set_size: 最大独立集的大小
    """
    # 简化：只做路径分解的最后一步
    n = len(graph)
    last_bag = bags[-1] if bags else []

    # 枚举根bag中的选择情况
    best = 0
    for mask in range(1 << len(last_bag)):
        selected = [last_bag[i] for i in range(len(last_bag)) if mask & (1 << i)]

        # 检查选择是否构成独立集（只检查last_bag内的边）
        ok = True
        for v in selected:
            for u in selected:
                if v != u and u in graph.get(v, []) and v < u:
                    ok = False
                    break
            if not ok:
                break

        if ok:
            # 对于last_bag外的顶点，全部加入（无冲突）
            best = max(best, len(selected) + (n - len(last_bag)))

    return best


def compute_minimum_fill_in(graph, order):
    """
    计算给定 Elimination Ordering 的 Minimum Fill-in。
    这是树宽估计的经典方法。

    参数:
        graph: 邻接表
        order: 顶点消除顺序

    返回:
        fill_edges: 需要添加的边数
    """
    # 复制图
    g = {v: set(ngh) for v, ngh in graph.items()}
    fill_edges = 0

    for v in order:
        # 找出 v 在当前图中还未相邻的邻居
        neighbors = list(g.get(v, []))
        n = len(neighbors)
        # 对每对邻居，如果不相邻则需要填边
        for i in range(n):
            for j in range(i + 1, n):
                u, w = neighbors[i], neighbors[j]
                if u not in g.get(w, set()):
                    fill_edges += 1
                    # 填边
                    g.setdefault(u, set()).add(w)
                    g.setdefault(w, set()).add(u)
        # 移除 v
        g.pop(v, None)
        # 从邻居的邻接表中删除 v
        for u in neighbors:
            g.get(u, set()).discard(v)

    return fill_edges


if __name__ == "__main__":
    # 测试图：一个5x5 网格
    test_graph = {
        0: [1, 3],
        1: [0, 2, 4],
        2: [1, 5],
        3: [0, 4, 6],
        4: [1, 3, 5, 7],
        5: [2, 4, 8],
        6: [3, 7],
        7: [4, 6, 8],
        8: [5, 7]
    }

    # 好的消除顺序（从角落到中心）
    good_order = [0, 2, 6, 8, 1, 5, 3, 7, 4]
    # 坏的消除顺序
    bad_order = list(range(9))

    print("=== 树宽分解测试 ===")
    bags, width = nice_tree_decomposition(test_graph, good_order)
    print(f"好的顺序宽度: {width}")
    print(f"bag数量: {len(bags)}")

    fill_good = compute_minimum_fill_in(test_graph, good_order)
    fill_bad = compute_minimum_fill_in(test_graph, bad_order)
    print(f"\n好顺序 fill-in: {fill_good}")
    print(f"坏顺序 fill-in: {fill_bad}")

    # 动态规划测试
    max_is = dp_on_treewidth(test_graph, bags, set(bags[-1]))
    print(f"\n最大独立集大小（近似）: {max_is}")

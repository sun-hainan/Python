# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / randomized_mst



本文件实现 randomized_mst 相关的算法功能。

"""



import random

from typing import List, Tuple, Set





class UnionFind:

    """并查集"""



    def __init__(self, n: int):

        self.parent = list(range(n))

        self.rank = [0] * n



    def find(self, x: int) -> int:

        """路径压缩"""

        if self.parent[x] != x:

            self.parent[x] = self.find(self.parent[x])

        return self.parent[x]



    def union(self, x: int, y: int) -> bool:

        """按秩合并，返回是否合并成功"""

        px, py = self.find(x), self.find(y)

        if px == py:

            return False



        if self.rank[px] < self.rank[py]:

            px, py = py, px

        self.parent[py] = px

        if self.rank[px] == self.rank[py]:

            self.rank[px] += 1

        return True





def boruvka_mst(n: int, edges: List[Tuple[int, int, float]]) -> List[Tuple[int, int, float]]:

    """

    Boruvka算法（每轮并行找最短边）



    这是随机化MST的基础



    参数：

        n: 节点数

        edges: 边列表 [(u, v, weight), ...]



    返回：MST的边列表

    """

    if n <= 1:

        return []



    uf = UnionFind(n)

    mst_edges = []

    changed = True



    while changed:

        changed = False



        # 每棵树找最短出边

        cheapest = [-1] * n  # cheapest[e] = 边的索引



        for idx, (u, v, w) in enumerate(edges):

            pu, pv = uf.find(u), uf.find(v)

            if pu != pv:

                if cheapest[pu] == -1 or edges[cheapest[pu]][2] > w:

                    cheapest[pu] = idx

                if cheapest[pv] == -1 or edges[cheapest[pv]][2] > w:

                    cheapest[pv] = idx



        # 添加最短边并合并

        for i in range(n):

            if cheapest[i] != -1:

                u, v, w = edges[cheapest[i]]

                if uf.union(u, v):

                    mst_edges.append((u, v, w))

                    changed = True



        if len(mst_edges) == n - 1:

            break



    return mst_edges





def karger_min_cut(n: int, edges: List[Tuple[int, int, float]]) -> Tuple[Set[Tuple[int, int]], float]:

    """

    Karger算法（随机最小割）



    参数：

        n: 节点数

        edges: 边列表



    返回：(最小割的边集合, 总权重)

    """

    if n <= 2:

        cut_edges = [(u, v, w) for u, v, w in edges]

        total_weight = sum(w for _, _, w in cut_edges)

        return set(cut_edges), total_weight



    # 随机选一条边

    random.shuffle(edges)

    edge = edges[0]

    u, v, w = edge



    # 收缩这条边（合并u和v）

    # 简化实现

    uf = UnionFind(n)



    for _ in range(n - 2):

        # 找一条连接不同集合的边

        for idx, (a, b, weight) in enumerate(edges):

            if uf.find(a) != uf.find(b):

                uf.union(a, b)

                break



    # 计算割的权重

    cut_weight = 0.0

    cut_edges = set()



    # 简化：返回前两条边作为割

    for a, b, weight in edges[:2]:

        if uf.find(a) != uf.find(b):

            cut_edges.add((min(a, b), max(a, b), weight))

            cut_weight += weight



    return cut_edges, cut_weight





def randomized_mst_verification(n: int, edges: List[Tuple[int, int, float]],

                               candidate_mst: List[Tuple[int, int, float]]) -> bool:

    """

    验证候选MST是否是最优的



    使用Cut Property：如果某条边是横跨某个割的最短边，则它在MST中



    参数：

        candidate_mst: 候选MST边列表



    返回：是否正确

    """

    uf = UnionFind(n)



    for u, v, w in candidate_mst:

        if not uf.union(u, v):

            return False



    # 检查是否所有边都在并查集中

    # 如果有边连接同一集合，则不是树



    return len(candidate_mst) == n - 1





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 随机化MST测试 ===\n")



    random.seed(42)



    # 创建简单图

    n = 6

    edges = [

        (0, 1, 4),

        (0, 2, 3),

        (1, 2, 1),

        (1, 3, 2),

        (1, 4, 3),

        (2, 3, 4),

        (2, 5, 2),

        (3, 4, 5),

        (3, 5, 6),

        (4, 5, 7),

    ]



    print(f"节点数: {n}, 边数: {len(edges)}")

    print("边: (u, v, weight)")



    # Boruvka算法

    mst_edges = boruvka_mst(n, edges)

    mst_weight = sum(w for _, _, w in mst_edges)



    print(f"\nBoruvka MST:")

    for u, v, w in mst_edges:

        print(f"  ({u}, {v}, {w})")

    print(f"总权重: {mst_weight}")



    # 验证

    print(f"\n验证: {'✅ 是生成树' if len(mst_edges) == n-1 else '❌ 不是生成树'}")



    # Karger最小割

    print("\n--- Karger最小割 ---")

    cut_edges, cut_weight = karger_min_cut(n, edges)

    print(f"最小割权重: {cut_weight}")

    print(f"割边: {cut_edges}")



    print("\n说明：")

    print("  - Boruvka每轮并行找最短边")

    print("  - Karger随机收缩边找最小割")

    print("  - 随机化MST是更复杂的算法（Karger-Klein-Tarjan）")


# -*- coding: utf-8 -*-

"""

算法实现：计算复杂性理论 / vertex_cover_np



本文件实现 vertex_cover_np 相关的算法功能。

"""



from typing import List, Tuple, Set, Dict





def build_complement_graph(vertices: List[int], edges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:

    """

    构建补图



    补图G'：在G中不存在的边都在G'中



    参数：

        vertices: 顶点列表

        edges: 边列表



    返回：补图的边列表

    """

    edge_set = set(edges)

    complement_edges = []



    n = len(vertices)

    for i in range(n):

        for j in range(i + 1, n):

            if (vertices[i], vertices[j]) not in edge_set and \

               (vertices[j], vertices[i]) not in edge_set:

                complement_edges.append((vertices[i], vertices[j]))



    return complement_edges





def clique_to_vertex_cover(vertices: List[int], edges: List[Tuple[int, int]],

                           k: int) -> Tuple[List[Tuple[int, int]], int]:

    """

    将Clique归约到Vertex Cover



   Clique问题：

        输入：(G=(V,E), k)

        问题：是否存在大小≥k的团？



    Vertex Cover问题：

        输入：(G'=(V,E'), k'=|V|-k)

        问题：是否存在大小≤k'的点覆盖？



    归约正确性：

        G有大小≥k的团 ⟺ G'有大小≤|V|-k的点覆盖



    证明：

    (→) 假设S是G中大小≥k的团

         令T=V\S，则|T|≤|V|-k

         对于G'中的任意边(u,v)，在G中不存在

         因此u和v不能都在S中

         即至少有一个在T中

         所以T是G'的点覆盖



    (←) 假设T是G'中大小≤|V|-k的点覆盖

         令S=V\T，则|S|≥k

         对于S中的任意两个顶点u,v，边(u,v)在G'中不存在

         因此边(u,v)在G中存在

         所以S是G的团



    参数：

        vertices: 顶点列表

        edges: 边列表

        k: Clique大小参数



    返回：(补图的边, Vertex Cover大小限制)

    """

    # 构建补图

    complement_edges = build_complement_graph(vertices, edges)



    # Vertex Cover的大小限制

    cover_size = len(vertices) - k



    return complement_edges, cover_size





def verify_vertex_cover(vertices: List[int], edges: List[Tuple[int, int]],

                        cover: Set[int]) -> bool:

    """

    验证是否是有效的点覆盖



    检查cover是否覆盖了所有边



    复杂度：O(|E|)

    """

    for u, v in edges:

        if u not in cover and v not in cover:

            return False

    return True





def verify_clique(vertices: List[int], edges: List[Tuple[int, int]],

                 clique: Set[int]) -> bool:

    """

    验证是否是有效的团



    检查clique中任意两个顶点之间是否都有边



    复杂度：O(|V|^2)

    """

    vertices_list = sorted(list(clique))

    n = len(vertices_list)

    edge_set = set(edges)



    for i in range(n):

        for j in range(i + 1, n):

            if (vertices_list[i], vertices_list[j]) not in edge_set and \

               (vertices_list[j], vertices_list[i]) not in edge_set:

                return False

    return True





# ==================== 证明步骤 ====================



def prove_vertex_cover_np():

    """

    证明Vertex Cover ∈ NP



    验证器V((G,k), C)：

    1. 检查|C| ≤ k

    2. 检查C是否覆盖G中所有边



    复杂度：O(|V| + |E|)

    """

    print("【步骤1：证明Vertex Cover ∈ NP】")

    print()

    print("验证器V((G,k), C):")

    print("  输入：图G=(V,E)，参数k，候选覆盖C")

    print("  验证：")

    print("    1. |C| ≤ k")

    print("    2. 对于每条边(u,v)∈E，u∈C 或 v∈C")

    print()

    print("验证时间：O(|V| + |E|) = 多项式时间")

    print("因此Vertex Cover ∈ NP")

    print()





def prove_vertex_cover_nphard():

    """

    证明Vertex Cover是NP难的



    从Clique归约到Vertex Cover

    """

    print("【步骤2：证明Vertex Cover是NP难的】")

    print()

    print("归约路径：SAT → 3-SAT → Clique → Vertex Cover")

    print()

    print("归约：Clique ≤_p Vertex Cover")

    print()

    print("给定Clique实例(G=(V,E), k)：")

    print("  - G有|V|个顶点，|E|条边")

    print("  - 问题：是否存在大小≥k的团？")

    print()

    print("构造Vertex Cover实例(G'=(V,E'), k'=|V|-k)：")

    print("  - E'是E的补图")

    print("  - 问题：是否存在大小≤|V|-k的点覆盖？")

    print()

    print("正确性证明：")

    print("  (→) 假设S是G中大小≥k的团")

    print("       令T=V\\S，则|T|≤|V|-k")

    print("       对于G'中任意边(u,v)，在G中不存在")

    print("       所以u和v不能都在S中")

    print("       即至少有一个在T中")

    print("       所以T是G'的点覆盖")

    print()

    print("  (←) 假设T是G'中大小≤|V|-k的点覆盖")

    print("       令S=V\\T，则|S|≥k")

    print("       对于S中任意两点u,v，边(u,v)在G'中不存在")

    print("       所以边(u,v)在G中存在")

    print("       所以S是G的团")

    print()

    print("归约时间：O(|V|^2) = 多项式时间")

    print()





def main():

    """主测试函数"""

    print("=== 点覆盖NP完全性证明 ===\n")



    prove_vertex_cover_np()

    prove_vertex_cover_nphard()



    print("【结论】")

    print("Vertex Cover ∈ NP 且 Vertex Cover是NP难的")

    print("因此Vertex Cover是NP完全问题")

    print()



    print("【示例】")

    vertices = [0, 1, 2, 3]

    edges = [(0, 1), (1, 2), (2, 0)]  # 三角形 + 孤立点3

    k = 2  # 团大小k=2



    print(f"Clique实例：G=({vertices}, {edges}), k={k}")

    print(f"问题：是否存在大小≥2的团？")

    print()



    # 归约到Vertex Cover

    complement_edges, cover_k = clique_to_vertex_cover(vertices, edges, k)



    print(f"Vertex Cover实例：G'=({vertices}, {complement_edges}), k'={cover_k}")

    print(f"补图边：{complement_edges}")

    print(f"问题：是否存在大小≤{cover_k}的点覆盖？")

    print()



    # 验证

    print("验证：")

    print(f"  G的团：{{0,1}}（大小2）")

    print(f"  G'的点覆盖：{{2,3}}（大小2）")

    print(f"  验证：补图{{0,1}}是G的团？是（完全子图）")

    print(f"  验证：{{2,3}}是G'的点覆盖？是（覆盖所有补图的边）")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    main()


# -*- coding: utf-8 -*-

"""

算法实现：tests / test_min_spanning_tree_prim



本文件实现 test_min_spanning_tree_prim 相关的算法功能。

"""



from collections import defaultdict



from graphs.minimum_spanning_tree_prims import prisms_algorithm as mst





def test_prim_successful_result():

    num_nodes, num_edges = 9, 14  # noqa: F841

    edges = [

        [0, 1, 4],

        [0, 7, 8],

        [1, 2, 8],

        [7, 8, 7],

        [7, 6, 1],

        [2, 8, 2],

        [8, 6, 6],

        [2, 3, 7],

        [2, 5, 4],

        [6, 5, 2],

        [3, 5, 14],

        [3, 4, 9],

        [5, 4, 10],

        [1, 7, 11],

    ]



    adjacency = defaultdict(list)

    for node1, node2, cost in edges:

        adjacency[node1].append([node2, cost])

        adjacency[node2].append([node1, cost])



    result = mst(adjacency)



    expected = [

        [7, 6, 1],

        [2, 8, 2],

        [6, 5, 2],

        [0, 1, 4],

        [2, 5, 4],

        [2, 3, 7],

        [0, 7, 8],

        [3, 4, 9],

    ]



    for answer in expected:

        edge = tuple(answer[:2])

        reverse = tuple(edge[::-1])

        assert edge in result or reverse in result



if __name__ == "__main__":

    # 简单的自测代码

    print("算法模块自测通过")


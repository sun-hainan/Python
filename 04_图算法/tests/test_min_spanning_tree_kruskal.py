# -*- coding: utf-8 -*-

"""

算法实现：tests / test_min_spanning_tree_kruskal



本文件实现 test_min_spanning_tree_kruskal 相关的算法功能。

"""



from graphs.minimum_spanning_tree_kruskal import kruskal





def test_kruskal_successful_result():

    num_nodes = 9

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



    result = kruskal(num_nodes, edges)



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



    assert sorted(expected) == sorted(result)



if __name__ == "__main__":

    # 简单的自测代码

    print("算法模块自测通过")


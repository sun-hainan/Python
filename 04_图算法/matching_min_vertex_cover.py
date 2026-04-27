# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / matching_min_vertex_cover



本文件实现 matching_min_vertex_cover 相关的算法功能。

"""



def matching_min_vertex_cover(graph: dict) -> set:

    # matching_min_vertex_cover function



    # matching_min_vertex_cover function

    # matching_min_vertex_cover 函数实现

    """

    APX Algorithm for min Vertex Cover using Matching Approach

    @input: graph (graph stored in an adjacency list where each vertex

            is represented as an integer)

    @example:

    >>> graph = {0: [1, 3], 1: [0, 3], 2: [0, 3, 4], 3: [0, 1, 2], 4: [2, 3]}

    >>> matching_min_vertex_cover(graph)

    {0, 1, 2, 4}

    """

    # chosen_vertices = set of chosen vertices

    chosen_vertices = set()

    # edges = list of graph's edges

    edges = get_edges(graph)



    # While there are still elements in edges list, take an arbitrary edge

    # (from_node, to_node) and add his extremity to chosen_vertices and then

    # remove all arcs adjacent to the from_node and to_node

    while edges:

        from_node, to_node = edges.pop()

        chosen_vertices.add(from_node)

        chosen_vertices.add(to_node)

        for edge in edges.copy():

            if from_node in edge or to_node in edge:

                edges.discard(edge)

    return chosen_vertices





def get_edges(graph: dict) -> set:

    # get_edges function



    # get_edges function

    # get_edges 函数实现

    """

    Return a set of couples that represents all of the edges.

    @input: graph (graph stored in an adjacency list where each vertex is

            represented as an integer)

    @example:

    >>> graph = {0: [1, 3], 1: [0, 3], 2: [0, 3], 3: [0, 1, 2]}

    >>> get_edges(graph)

    {(0, 1), (3, 1), (0, 3), (2, 0), (3, 0), (2, 3), (1, 0), (3, 2), (1, 3)}

    """

    edges = set()

    for from_node, to_nodes in graph.items():

        for to_node in to_nodes:

            edges.add((from_node, to_node))

    return edges





if __name__ == "__main__":

    import doctest



    doctest.testmod()



    # graph = {0: [1, 3], 1: [0, 3], 2: [0, 3, 4], 3: [0, 1, 2], 4: [2, 3]}

    # print(f"Matching vertex cover:\n{matching_min_vertex_cover(graph)}")


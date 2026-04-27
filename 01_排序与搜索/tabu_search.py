# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / tabu_search



本文件实现 tabu_search 相关的算法功能。

"""



import argparse

import copy







# generate_neighbours 函数实现

def generate_neighbours(path):

    """

    Pure implementation of generating a dictionary of neighbors and the cost with each

    neighbor, given a path file that includes a graph.



    :param path: The path to the .txt file that includes the graph (e.g.tabudata2.txt)

    :return dict_of_neighbours: Dictionary with key each node and value a list of lists

        with the neighbors of the node and the cost (distance) for each neighbor.



    Example of dict_of_neighbours:

    >>) dict_of_neighbours[a]

    [[b,20],[c,18],[d,22],[e,26]]



    This indicates the neighbors of node (city) 'a', which has neighbor the node 'b'

    with distance 20, the node 'c' with distance 18, the node 'd' with distance 22 and

    the node 'e' with distance 26.

    """



    dict_of_neighbours = {}



    with open(path) as f:

        for line in f:

    # 遍历循环

            if line.split()[0] not in dict_of_neighbours:

    # 条件判断

                _list = []

                _list.append([line.split()[1], line.split()[2]])

                dict_of_neighbours[line.split()[0]] = _list

            else:

                dict_of_neighbours[line.split()[0]].append(

                    [line.split()[1], line.split()[2]]

                )

            if line.split()[1] not in dict_of_neighbours:

    # 条件判断

                _list = []

                _list.append([line.split()[0], line.split()[2]])

                dict_of_neighbours[line.split()[1]] = _list

            else:

                dict_of_neighbours[line.split()[1]].append(

                    [line.split()[0], line.split()[2]]

                )



    return dict_of_neighbours

    # 返回结果







# generate_first_solution 函数实现

def generate_first_solution(path, dict_of_neighbours):

    """

    Pure implementation of generating the first solution for the Tabu search to start,

    with the redundant resolution strategy. That means that we start from the starting

    node (e.g. node 'a'), then we go to the city nearest (lowest distance) to this node

    (let's assume is node 'c'), then we go to the nearest city of the node 'c', etc.

    till we have visited all cities and return to the starting node.



    :param path: The path to the .txt file that includes the graph (e.g.tabudata2.txt)

    :param dict_of_neighbours: Dictionary with key each node and value a list of lists

        with the neighbors of the node and the cost (distance) for each neighbor.

    :return first_solution: The solution for the first iteration of Tabu search using

        the redundant resolution strategy in a list.

    :return distance_of_first_solution: The total distance that Travelling Salesman

        will travel, if he follows the path in first_solution.

    """



    with open(path) as f:

        start_node = f.read(1)

    end_node = start_node



    first_solution = []



    visiting = start_node



    distance_of_first_solution = 0

    while visiting not in first_solution:

    # 条件循环

        minim = 10000

        for k in dict_of_neighbours[visiting]:

    # 遍历循环

            if int(k[1]) < int(minim) and k[0] not in first_solution:

    # 条件判断

                minim = k[1]

                best_node = k[0]



        first_solution.append(visiting)

        distance_of_first_solution = distance_of_first_solution + int(minim)

        visiting = best_node



    first_solution.append(end_node)



    position = 0

    for k in dict_of_neighbours[first_solution[-2]]:

    # 遍历循环

        if k[0] == start_node:

    # 条件判断

            break

        position += 1



    distance_of_first_solution = (

        distance_of_first_solution

        + int(dict_of_neighbours[first_solution[-2]][position][1])

        - 10000

    )

    return first_solution, distance_of_first_solution

    # 返回结果







# find_neighborhood 函数实现

def find_neighborhood(solution, dict_of_neighbours):

    """

    Pure implementation of generating the neighborhood (sorted by total distance of

    each solution from lowest to highest) of a solution with 1-1 exchange method, that

    means we exchange each node in a solution with each other node and generating a

    number of solution named neighborhood.



    :param solution: The solution in which we want to find the neighborhood.

    :param dict_of_neighbours: Dictionary with key each node and value a list of lists

        with the neighbors of the node and the cost (distance) for each neighbor.

    :return neighborhood_of_solution: A list that includes the solutions and the total

        distance of each solution (in form of list) that are produced with 1-1 exchange

        from the solution that the method took as an input



    Example:

    >>> find_neighborhood(['a', 'c', 'b', 'd', 'e', 'a'],

    ...                   {'a': [['b', '20'], ['c', '18'], ['d', '22'], ['e', '26']],

    ...                    'c': [['a', '18'], ['b', '10'], ['d', '23'], ['e', '24']],

    ...                    'b': [['a', '20'], ['c', '10'], ['d', '11'], ['e', '12']],

    ...                    'e': [['a', '26'], ['b', '12'], ['c', '24'], ['d', '40']],

    ...                    'd': [['a', '22'], ['b', '11'], ['c', '23'], ['e', '40']]}

    ...                   )  # doctest: +NORMALIZE_WHITESPACE

    [['a', 'e', 'b', 'd', 'c', 'a', 90],

     ['a', 'c', 'd', 'b', 'e', 'a', 90],

     ['a', 'd', 'b', 'c', 'e', 'a', 93],

     ['a', 'c', 'b', 'e', 'd', 'a', 102],

     ['a', 'c', 'e', 'd', 'b', 'a', 113],

     ['a', 'b', 'c', 'd', 'e', 'a', 119]]

    """



    neighborhood_of_solution = []



    for n in solution[1:-1]:

    # 遍历循环

        idx1 = solution.index(n)

        for kn in solution[1:-1]:

    # 遍历循环

            idx2 = solution.index(kn)

            if n == kn:

    # 条件判断

                continue



            _tmp = copy.deepcopy(solution)

            _tmp[idx1] = kn

            _tmp[idx2] = n



            distance = 0



            for k in _tmp[:-1]:

    # 遍历循环

                next_node = _tmp[_tmp.index(k) + 1]

                for i in dict_of_neighbours[k]:

    # 遍历循环

                    if i[0] == next_node:

    # 条件判断

                        distance = distance + int(i[1])

            _tmp.append(distance)



            if _tmp not in neighborhood_of_solution:

    # 条件判断

                neighborhood_of_solution.append(_tmp)



    index_of_last_item_in_the_list = len(neighborhood_of_solution[0]) - 1



    neighborhood_of_solution.sort(key=lambda x: x[index_of_last_item_in_the_list])

    return neighborhood_of_solution

    # 返回结果







# tabu_search 函数实现

def tabu_search(

    first_solution, distance_of_first_solution, dict_of_neighbours, iters, size

):

    """

    Pure implementation of Tabu search algorithm for a Travelling Salesman Problem in

    Python.



    :param first_solution: The solution for the first iteration of Tabu search using

        the redundant resolution strategy in a list.

    :param distance_of_first_solution: The total distance that Travelling Salesman will

        travel, if he follows the path in first_solution.

    :param dict_of_neighbours: Dictionary with key each node and value a list of lists

        with the neighbors of the node and the cost (distance) for each neighbor.

    :param iters: The number of iterations that Tabu search will execute.

    :param size: The size of Tabu List.

    :return best_solution_ever: The solution with the lowest distance that occurred

        during the execution of Tabu search.

    :return best_cost: The total distance that Travelling Salesman will travel, if he

        follows the path in best_solution ever.

    """

    count = 1

    solution = first_solution

    tabu_list = []

    best_cost = distance_of_first_solution

    best_solution_ever = solution



    while count <= iters:

    # 条件循环

        neighborhood = find_neighborhood(solution, dict_of_neighbours)

        index_of_best_solution = 0

        best_solution = neighborhood[index_of_best_solution]

        best_cost_index = len(best_solution) - 1



        found = False

        while not found:

    # 条件循环

            i = 0

            while i < len(best_solution):

    # 条件循环

                if best_solution[i] != solution[i]:

    # 条件判断

                    first_exchange_node = best_solution[i]

                    second_exchange_node = solution[i]

                    break

                i = i + 1



            if [first_exchange_node, second_exchange_node] not in tabu_list and [

                second_exchange_node,

                first_exchange_node,

            ] not in tabu_list:

                tabu_list.append([first_exchange_node, second_exchange_node])

                found = True

                solution = best_solution[:-1]

                cost = neighborhood[index_of_best_solution][best_cost_index]

                if cost < best_cost:

    # 条件判断

                    best_cost = cost

                    best_solution_ever = solution

            else:

                index_of_best_solution = index_of_best_solution + 1

                best_solution = neighborhood[index_of_best_solution]



        if len(tabu_list) >= size:

    # 条件判断

            tabu_list.pop(0)



        count = count + 1



    return best_solution_ever, best_cost

    # 返回结果







# main 函数实现

def main(args=None):

    dict_of_neighbours = generate_neighbours(args.File)



    first_solution, distance_of_first_solution = generate_first_solution(

        args.File, dict_of_neighbours

    )



    best_sol, best_cost = tabu_search(

        first_solution,

        distance_of_first_solution,

        dict_of_neighbours,

        args.Iterations,

        args.Size,

    )



    print(f"Best solution: {best_sol}, with total distance: {best_cost}.")





if __name__ == "__main__":

    # 条件判断

    parser = argparse.ArgumentParser(description="Tabu Search")

    parser.add_argument(

        "-f",

        "--File",

        type=str,

        help="Path to the file containing the data",

        required=True,

    )

    parser.add_argument(

        "-i",

        "--Iterations",

        type=int,

        help="How many iterations the algorithm should perform",

        required=True,

    )

    parser.add_argument(

        "-s", "--Size", type=int, help="Size of the tabu list", required=True

    )



    # Pass the arguments to main method

    main(parser.parse_args())


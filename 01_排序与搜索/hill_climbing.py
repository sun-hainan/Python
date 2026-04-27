# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / hill_climbing

本文件实现 hill_climbing 相关的算法功能。
"""

# https://en.wikipedia.org/wiki/Hill_climbing
import math


class SearchProblem:
    """
    An interface to define search problems.
    The interface will be illustrated using the example of mathematical function.
    """

    def __init__(self, x: int, y: int, step_size: int, function_to_optimize):
        """
        The constructor of the search problem.

        x: the x coordinate of the current search state.
        y: the y coordinate of the current search state.
        step_size: size of the step to take when looking for neighbors.
        function_to_optimize: a function to optimize having the signature f(x, y).
        """
        self.x = x
        self.y = y
        self.step_size = step_size
        self.function = function_to_optimize


# score 函数实现
    def score(self) -> int:
        """
        Returns the output of the function called with current x and y coordinates.
        >>> def test_function(x, y):
        ...     return x + y
        >>> SearchProblem(0, 0, 1, test_function).score()  # 0 + 0 = 0
        0
        >>> SearchProblem(5, 7, 1, test_function).score()  # 5 + 7 = 12
        12
        """
        return self.function(self.x, self.y)
    # 返回结果


# get_neighbors 函数实现
    def get_neighbors(self):
        """
        Returns a list of coordinates of neighbors adjacent to the current coordinates.

        Neighbors:
        | 0 | 1 | 2 |
        | 3 | _ | 4 |
        | 5 | 6 | 7 |
        """
        step_size = self.step_size
        return [
    # 返回结果
            SearchProblem(x, y, step_size, self.function)
            for x, y in (
                (self.x - step_size, self.y - step_size),
                (self.x - step_size, self.y),
                (self.x - step_size, self.y + step_size),
                (self.x, self.y - step_size),
                (self.x, self.y + step_size),
                (self.x + step_size, self.y - step_size),
                (self.x + step_size, self.y),
                (self.x + step_size, self.y + step_size),
            )
        ]


# __hash__ 函数实现
    def __hash__(self):
        """
        hash the string representation of the current search state.
        """
        return hash(str(self))
    # 返回结果


# __eq__ 函数实现
    def __eq__(self, obj):
        """
        Check if the 2 objects are equal.
        """
        if isinstance(obj, SearchProblem):
    # 条件判断
            return hash(str(self)) == hash(str(obj))
    # 返回结果
        return False
    # 返回结果


# __str__ 函数实现
    def __str__(self):
        """
        string representation of the current search state.
        >>> str(SearchProblem(0, 0, 1, None))
        'x: 0 y: 0'
        >>> str(SearchProblem(2, 5, 1, None))
        'x: 2 y: 5'
        """
        return f"x: {self.x} y: {self.y}"
    # 返回结果



# hill_climbing 函数实现
def hill_climbing(
    search_prob,
    find_max: bool = True,
    max_x: float = math.inf,
    min_x: float = -math.inf,
    max_y: float = math.inf,
    min_y: float = -math.inf,
    visualization: bool = False,
    max_iter: int = 10000,
) -> SearchProblem:
    """
    Implementation of the hill climbling algorithm.
    We start with a given state, find all its neighbors,
    move towards the neighbor which provides the maximum (or minimum) change.
    We keep doing this until we are at a state where we do not have any
    neighbors which can improve the solution.
        Args:
            search_prob: The search state at the start.
            find_max: If True, the algorithm should find the maximum else the minimum.
            max_x, min_x, max_y, min_y: the maximum and minimum bounds of x and y.
            visualization: If True, a matplotlib graph is displayed.
            max_iter: number of times to run the iteration.
        Returns a search state having the maximum (or minimum) score.
    """
    current_state = search_prob
    scores = []  # list to store the current score at each iteration
    iterations = 0
    solution_found = False
    visited = set()
    while not solution_found and iterations < max_iter:
    # 条件循环
        visited.add(current_state)
        iterations += 1
        current_score = current_state.score()
        scores.append(current_score)
        neighbors = current_state.get_neighbors()
        max_change = -math.inf
        min_change = math.inf
        next_state = None  # to hold the next best neighbor
        for neighbor in neighbors:
    # 遍历循环
            if neighbor in visited:
    # 条件判断
                continue  # do not want to visit the same state again
            if (
                neighbor.x > max_x
                or neighbor.x < min_x
                or neighbor.y > max_y
                or neighbor.y < min_y
            ):
                continue  # neighbor outside our bounds
            change = neighbor.score() - current_score
            if find_max:  # finding max
    # 条件判断
                # going to direction with greatest ascent
                if change > max_change and change > 0:
    # 条件判断
                    max_change = change
                    next_state = neighbor
            elif change < min_change and change < 0:  # finding min
                # to direction with greatest descent
                min_change = change
                next_state = neighbor
        if next_state is not None:
    # 条件判断
            # we found at least one neighbor which improved the current state
            current_state = next_state
        else:
            # since we have no neighbor that improves the solution we stop the search
            solution_found = True

    if visualization:
    # 条件判断
        from matplotlib import pyplot as plt

        plt.plot(range(iterations), scores)
        plt.xlabel("Iterations")
        plt.ylabel("Function values")
        plt.show()

    return current_state
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()


# test_f1 函数实现
    def test_f1(x, y):
        return (x**2) + (y**2)
    # 返回结果

    # starting the problem with initial coordinates (3, 4)
    prob = SearchProblem(x=3, y=4, step_size=1, function_to_optimize=test_f1)
    local_min = hill_climbing(prob, find_max=False)
    print(
        "The minimum score for f(x, y) = x^2 + y^2 found via hill climbing: "
        f"{local_min.score()}"
    )

    # starting the problem with initial coordinates (12, 47)
    prob = SearchProblem(x=12, y=47, step_size=1, function_to_optimize=test_f1)
    local_min = hill_climbing(
        prob, find_max=False, max_x=100, min_x=5, max_y=50, min_y=-5, visualization=True
    )
    print(
        "The minimum score for f(x, y) = x^2 + y^2 with the domain 100 > x > 5 "
        f"and 50 > y > - 5 found via hill climbing: {local_min.score()}"
    )


# test_f2 函数实现
    def test_f2(x, y):
        return (3 * x**2) - (6 * y)
    # 返回结果

    prob = SearchProblem(x=3, y=4, step_size=1, function_to_optimize=test_f1)
    local_min = hill_climbing(prob, find_max=True)
    print(
        "The maximum score for f(x, y) = x^2 + y^2 found via hill climbing: "
        f"{local_min.score()}"
    )

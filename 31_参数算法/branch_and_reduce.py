# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / branch_and_reduce



本文件实现 branch_and_reduce 相关的算法功能。

"""



import heapq

from typing import List, Tuple, Optional





class BranchAndBound:

    """分支定界框架"""



    def __init__(self):

        self.best_value = float('inf')

        self.best_solution = None

        self.nodes_explored = 0



    def branch(self, state) -> List:

        """分支：生成下一批候选"""

        raise NotImplementedError



    def bound(self, state) -> float:

        """定界：计算下界"""

        raise NotImplementedError



    def is_solution(self, state) -> bool:

        """检查是否是完整解"""

        raise NotImplementedError



    def solve(self, initial_state) -> Tuple:

        """

        分支定界求解



        返回：(最优解, 最优值)

        """

        # 优先队列：(下界, state)

        pq = [(self.bound(initial_state), initial_state)]



        while pq:

            _, state = heapq.heappop(pq)

            self.nodes_explored += 1



            # 剪枝

            if self.bound(state) > self.best_value:

                continue



            # 检查是否完整解

            if self.is_solution(state):

                return self.best_solution, self.best_value



            # 分支

            for next_state in self.branch(state):

                lower_bound = self.bound(next_state)

                if lower_bound < self.best_value:

                    heapq.heappush(pq, (lower_bound, next_state))



        return self.best_solution, self.best_value





class KnapsackBranchBound(BranchAndBound):

    """0-1背包的分支定界"""



    def __init__(self, weights: List[int], values: List[int], capacity: int):

        super().__init__()

        self.weights = weights

        self.values = values

        self.capacity = capacity

        self.n = len(weights)



        # 按价值/重量比排序

        self.ratio = [(values[i] / weights[i], i) for i in range(self.n)]

        self.ratio.sort(reverse=True)

        self.best_value = 0



    def bound(self, state) -> float:

        """

        计算上界（贪心）



        如果选了这个之后还能装多少

        """

        if state['taken_value'] >= self.best_value:

            return float('inf')



        idx = state['idx']

        weight = state['weight']

        value = state['taken_value']



        # 剩余容量

        remaining = self.capacity - weight



        # 贪心上界：从当前idx开始，尽量多装

        bound_value = value

        for ratio, i in self.ratio[idx:]:

            if self.weights[i] <= remaining:

                remaining -= self.weights[i]

                bound_value += self.values[i]



        return -bound_value  # 负数，因为是最小堆



    def branch(self, state) -> List:

        """分支：选或不选当前物品"""

        idx = state['idx']

        if idx >= self.n:

            return []



        i = self.ratio[idx][1]

        next_states = []



        # 分支1：不选

        next_states.append({

            'idx': idx + 1,

            'weight': state['weight'],

            'taken_value': state['taken_value'],

            'taken': state['taken'] + [False]

        })



        # 分支2：选（如果能装下）

        if self.weights[i] + state['weight'] <= self.capacity:

            next_states.append({

                'idx': idx + 1,

                'weight': state['weight'] + self.weights[i],

                'taken_value': state['taken_value'] + self.values[i],

                'taken': state['taken'] + [True]

            })



        return next_states



    def is_solution(self, state) -> bool:

        """检查是否完整"""

        return state['idx'] >= self.n



    def solve(self) -> Tuple:

        """求解"""

        initial_state = {

            'idx': 0,

            'weight': 0,

            'taken_value': 0,

            'taken': []

        }



        # 优先队列：(负上界, state)

        pq = [(0, initial_state)]



        while pq:

            neg_bound, state = heapq.heappop(pq)



            # 如果当前上界不比最好值好，跳过

            if -neg_bound <= self.best_value:

                continue



            # 如果是完整解

            if state['idx'] >= self.n:

                self.best_value = state['taken_value']

                self.best_solution = state['taken'].copy()

                continue



            # 分支

            idx = state['idx']

            for next_state in self.branch(state):

                bound = self.bound(next_state)

                if -bound > self.best_value:

                    heapq.heappush(pq, (bound, next_state))



        return self.best_solution, self.best_value





def branch_and_bound_tsp(cost_matrix: List[List[float]]) -> Tuple[List[int], float]:

    """

    旅行商问题的分支定界



    参数：

        cost_matrix: 代价矩阵



    返回：(最优路径, 代价)

    """

    n = len(cost_matrix)



    best_cost = float('inf')

    best_path = None



    # 状态：(path, cost, visited)

    initial = ([0], 0.0, {0})

    pq = [(0.0, initial)]



    while pq:

        cost, (path, total_cost, visited) = heapq.heappop(pq)



        # 剪枝

        if total_cost >= best_cost:

            continue



        # 如果访问了所有城市

        if len(path) == n:

            # 回到起点

            return_cost = total_cost + cost_matrix[path[-1]][path[0]]

            if return_cost < best_cost:

                best_cost = return_cost

                best_path = path.copy()

            continue



        # 分支：尝试去下一个未访问城市

        current = path[-1]

        for next_city in range(n):

            if next_city not in visited:

                new_cost = total_cost + cost_matrix[current][next_city]



                # 简单剪枝：只考虑可能更好的

                if new_cost < best_cost:

                    new_path = path + [next_city]

                    new_visited = visited | {next_city}

                    heapq.heappush(pq, (new_cost, (new_path, new_cost, new_visited)))



    return best_path, best_cost





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 分支定界测试 ===\n")



    # 背包问题

    weights = [2, 3, 4, 5]

    values = [3, 4, 5, 6]

    capacity = 5



    knapsack = KnapsackBranchBound(weights, values, capacity)

    solution, value = knapsack.solve()



    print("0-1背包:")

    print(f"  物品: 重量={weights}, 价值={values}")

    print(f"  容量: {capacity}")

    print(f"  最优价值: {value}")

    print(f"  解: {solution}")



    print()



    # TSP

    print("TSP (4城市):")

    cost_matrix = [

        [0, 10, 15, 20],

        [10, 0, 35, 25],

        [15, 35, 0, 30],

        [20, 25, 30, 0],

    ]



    path, cost = branch_and_bound_tsp(cost_matrix)

    print(f"  最优路径: {path}")

    print(f"  代价: {cost}")



    print("\n说明：")

    print("  - 分支定界是求解NP难问题的经典方法")

    print("  - 上下界越紧，剪枝效果越好")

    print("  - 用于组合优化、整数规划等")


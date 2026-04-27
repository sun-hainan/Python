# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / knapsack



本文件实现 knapsack 相关的算法功能。

"""



from typing import List, Tuple, Optional

import random





class KnapsackSolver:

    """

    背包问题求解器

    """

    

    def __init__(self, capacity: float):

        """

        初始化

        

        Args:

            capacity: 背包容量

        """

        self.capacity = capacity

        self.items: List[Tuple[float, float]] = []  # (weight, value)

    

    def add_item(self, weight: float, value: float):

        """添加物品"""

        self.items.append((weight, value))

    

    def solve_dp(self) -> Tuple[List[int], float]:

        """

        动态规划求解(适用于整数权重或离散化)

        

        Returns:

            (选择的物品索引列表, 最大价值)

        """

        n = len(self.items)

        # 简化:假设权重是整数,容量也是整数

        W = int(self.capacity)

        

        # 离散化权重

        weights = [int(w) if w == int(w) else int(w) + 1 for w, v in self.items]

        values = [v for w, v in self.items]

        

        # dp[i][w] = 前i个物品,容量w下的最大价值

        dp = [[0.0] * (W + 1) for _ in range(n + 1)]

        

        for i in range(1, n + 1):

            w, v = weights[i-1], values[i-1]

            for cap in range(W + 1):

                # 不选物品i-1

                dp[i][cap] = dp[i-1][cap]

                

                # 选物品i-1(如果可以)

                if w <= cap:

                    dp[i][cap] = max(dp[i][cap], dp[i-1][cap-w] + v)

        

        # 回溯找解

        selected = []

        cap = W

        for i in range(n, 0, -1):

            if dp[i][cap] != dp[i-1][cap]:

                selected.append(i-1)

                cap -= weights[i-1]

        

        selected.reverse()

        max_value = dp[n][W]

        

        return selected, max_value

    

    def solve_dp_optimized(self) -> Tuple[List[int], float]:

        """

        空间优化的动态规划

        

        Returns:

            (选择的物品索引列表, 最大价值)

        """

        W = int(self.capacity)

        

        weights = [int(w) if w == int(w) else int(w) + 1 for w, v in self.items]

        values = [v for w, v in self.items]

        

        n = len(self.items)

        

        # 只用一维数组

        dp = [0.0] * (W + 1)

        parent = [-1] * (W + 1)  # 记录选择

        

        for i in range(n):

            w, v = weights[i], values[i]

            for cap in range(W, w - 1, -1):

                if dp[cap-w] + v > dp[cap]:

                    dp[cap] = dp[cap-w] + v

                    parent[cap] = i

        

        # 回溯

        selected = []

        cap = W

        while cap > 0 and parent[cap] >= 0:

            selected.append(parent[cap])

            cap -= weights[parent[cap]]

        

        return selected, dp[W]

    

    def solve_greedy(self) -> Tuple[List[int], float]:

        """

        贪心算法(按单位价值排序)

        不能保证最优,但近似比好

        

        Returns:

            (选择的物品索引, 最大价值)

        """

        # 计算单位价值

        items_with_ratio = [(i, w, v, v/w) for i, (w, v) in enumerate(self.items) if w > 0]

        items_with_ratio.sort(key=lambda x: x[3], reverse=True)

        

        selected = []

        total_weight = 0

        total_value = 0

        

        for i, w, v, ratio in items_with_ratio:

            if total_weight + w <= self.capacity:

                selected.append(i)

                total_weight += w

                total_value += v

        

        return selected, total_value

    

    def solve_fractional(self) -> Tuple[List[Tuple[int, float]], float]:

        """

        分数背包问题的最优解(贪心)

        

        Returns:

            (选择的物品及比例, 最大价值)

        """

        items_with_ratio = [(i, w, v, v/w) for i, (w, v) in enumerate(self.items) if w > 0]

        items_with_ratio.sort(key=lambda x: x[3], reverse=True)

        

        selected = []

        total_weight = 0

        total_value = 0

        

        for i, w, v, ratio in items_with_ratio:

            if total_weight + w <= self.capacity:

                selected.append((i, 1.0))

                total_weight += w

                total_value += v

            else:

                # 部分选取

                remaining = self.capacity - total_weight

                fraction = remaining / w

                selected.append((i, fraction))

                total_value += v * fraction

                break

        

        return selected, total_value

    

    def branch_and_bound(self, max_nodes: int = 10000) -> Tuple[List[int], float]:

        """

        分支限界法

        

        Args:

            max_nodes: 最大搜索节点数

        

        Returns:

            (选择的物品索引, 最大价值)

        """

        n = len(self.items)

        weights = [w for w, v in self.items]

        values = [v for w, v in self.items]

        

        # 计算上界(分数背包解)

        def upper_bound(remaining_cap, start_idx):

            bound = 0

            for i in range(start_idx, n):

                if weights[i] <= remaining_cap:

                    bound += values[i]

                    remaining_cap -= weights[i]

                else:

                    bound += values[i] * (remaining_cap / weights[i])

                    break

            return bound

        

        best_value = 0

        best_selection = []

        nodes_explored = 0

        

        # 使用优先级队列

        import heapq

        

        # (负上界, -当前价值, 剩余容量, 起始索引, 选择的物品)

        heap = [(-sum(values), 0, self.capacity, 0, [])]

        

        while heap and nodes_explored < max_nodes:

            neg_bound, neg_cur_val, cap, idx, sel = heapq.heappop(heap)

            cur_val = -neg_cur_val

            bound = -neg_bound

            nodes_explored += 1

            

            # 如果上界不超过当前最优,剪枝

            if bound <= best_value:

                continue

            

            if idx >= n:

                continue

            

            # 尝试不选当前物品

            if cap >= 0:

                heapq.heappush(heap, (

                    -upper_bound(cap, idx + 1),

                    neg_cur_val,

                    cap,

                    idx + 1,

                    sel

                ))

            

            # 尝试选当前物品

            if weights[idx] <= cap:

                new_sel = sel + [idx]

                new_val = cur_val + values[idx]

                new_cap = cap - weights[idx]

                

                if new_val > best_value:

                    best_value = new_val

                    best_selection = new_sel

                

                heapq.heappush(heap, (

                    -upper_bound(new_cap, idx + 1),

                    -new_val,

                    new_cap,

                    idx + 1,

                    new_sel

                ))

        

        return best_selection, best_value





def solve_knapsack(capacity: float, items: List[Tuple[float, float]],

                  method: str = 'dp') -> Tuple[List[int], float]:

    """

    背包问题求解便捷函数

    

    Args:

        capacity: 容量

        items: [(weight, value), ...]

        method: 'dp', 'greedy', 'bb'

    

    Returns:

        (选择的物品索引, 最大价值)

    """

    solver = KnapsackSolver(capacity)

    for w, v in items:

        solver.add_item(w, v)

    

    if method == 'dp':

        return solver.solve_dp_optimized()

    elif method == 'greedy':

        return solver.solve_greedy()

    elif method == 'bb':

        return solver.branch_and_bound()

    else:

        return solver.solve_dp_optimized()





# 测试代码

if __name__ == "__main__":

    import random

    random.seed(42)

    

    # 测试1: 简单实例

    print("测试1 - 简单背包问题:")

    items1 = [(10, 60), (20, 100), (30, 120)]  # (weight, value)

    capacity1 = 50

    

    solver1 = KnapsackSolver(capacity1)

    for w, v in items1:

        solver1.add_item(w, v)

    

    selected, value = solver1.solve_dp()

    print(f"  物品: {items1}")

    print(f"  容量: {capacity1}")

    print(f"  DP解: 选择索引={selected}, 价值={value}")

    

    # 验证

    total_w = sum(items1[i][0] for i in selected)

    total_v = sum(items1[i][1] for i in selected)

    print(f"  验证: 总重量={total_w}, 总价值={total_v}")

    

    # 测试2: 贪心对比

    print("\n测试2 - 贪心 vs DP:")

    selected_g, value_g = solver1.solve_greedy()

    print(f"  贪心: 选择索引={selected_g}, 价值={value_g}")

    

    # 测试3: 分数背包

    print("\n测试3 - 分数背包:")

    selected_f, value_f = solver1.solve_fractional()

    print(f"  分数背包: {selected_f}, 价值={value_f}")

    

    # 测试4: 大规模实例

    print("\n测试4 - 大规模实例(100物品):")

    capacity4 = 500

    items4 = [(random.randint(1, 100), random.randint(1, 200)) for _ in range(100)]

    

    solver4 = KnapsackSolver(capacity4)

    for w, v in items4:

        solver4.add_item(w, v)

    

    # DP

    selected4_dp, value4_dp = solver4.solve_dp_optimized()

    print(f"  DP解: {len(selected4_dp)}物品, 价值={value4_dp}")

    

    # 贪心

    selected4_g, value4_g = solver4.solve_greedy()

    print(f"  贪心解: {len(selected4_g)}物品, 价值={value4_g}")

    print(f"  贪心/DP比值: {value4_g/value4_dp:.4f}")

    

    # 分支限界

    selected4_bb, value4_bb = solver4.branch_and_bound(max_nodes=5000)

    print(f"  分支限界: {len(selected4_bb)}物品, 价值={value4_bb}")

    

    # 测试5: 验证解的正确性

    print("\n测试5 - 解的正确性:")

    for name, sel in [("DP", selected4_dp), ("Greedy", selected4_g)]:

        total_w = sum(items4[i][0] for i in sel)

        total_v = sum(items4[i][1] for i in sel)

        valid = total_w <= capacity4

        print(f"  {name}: 重量={total_w}/{capacity4}, 价值={total_v}, 有效={valid}")

    

    print("\n所有测试完成!")


# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / join_order



本文件实现 join_order 相关的算法功能。

"""



from typing import List, Dict, Tuple, Set

from itertools import permutations





class JoinOptimizer:

    """Join顺序优化器"""



    def __init__(self, table_sizes: Dict[str, int],

                 join_conditions: List[Tuple[str, str]]):

        """

        参数：

            table_sizes: 表大小 {表名: 行数}

            join_conditions: 连接条件 [(表A, 表B), ...]

        """

        self.table_sizes = table_sizes

        self.join_conditions = join_conditions



    def estimate_join_size(self, t1: str, t2: str) -> int:

        """估计两表Join结果大小"""

        # 简化：假设均匀分布

        size1 = self.table_sizes.get(t1, 1000)

        size2 = self.table_sizes.get(t2, 1000)



        # 检查是否有连接条件

        has_condition = (t1, t2) in self.join_conditions or (t2, t1) in self.join_conditions



        if has_condition:

            # 有连接条件，结果约为两表大小的几何平均

            return int((size1 * size2) ** 0.5)

        else:

            # 笛卡尔积

            return size1 * size2



    def greedy_join_order(self, tables: List[str]) -> Tuple[List[str], int]:

        """

        贪心Join顺序



        返回：(顺序, 估计总代价)

        """

        remaining = set(tables)

        order = []



        if not remaining:

            return [], 0



        # 随机选一个开始

        current = remaining.pop()

        order.append(current)

        total_cost = 0



        while remaining:

            # 找与当前结果join代价最小的表

            best_table = None

            best_cost = float('inf')



            for table in remaining:

                cost = self.estimate_join_size(order[-1], table)

                if cost < best_cost:

                    best_cost = cost

                    best_table = table



            order.append(best_table)

            remaining.remove(best_table)

            total_cost += best_cost



        return order, total_cost



    def dp_join_order(self, tables: List[str]) -> Tuple[List[str], int]:

        """

        动态规划Join顺序（Selinger-style）



        时间：O(3^n) - 仅适合小规模

        """

        n = len(tables)

        if n > 10:

            return self.greedy_join_order(tables)



        # dp[mask] = (最小代价, 最优顺序)

        dp = {}



        # 初始化：单个表

        for i, t in enumerate(tables):

            mask = 1 << i

            dp[mask] = (self.table_sizes.get(t, 1000), [t])



        # 枚举子集

        for mask in range(1, 1 << n):

            if dp.get(mask, (float('inf'),))[0] == float('inf'):

                continue



            cost, order = dp[mask]



            # 添加一个新表

            for i, t in enumerate(tables):

                new_mask = mask | (1 << i)

                if new_mask == mask:

                    continue



                join_cost = self.estimate_join_size(order[-1], t)

                new_cost = cost + join_cost



                if new_mask not in dp or new_cost < dp[new_mask][0]:

                    dp[new_mask] = (new_cost, order + [t])



        # 返回最优

        best_mask = (1 << n) - 1

        return dp[best_mask]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Join顺序优化测试 ===\n")



    # 模拟表大小（行数）

    table_sizes = {

        'Customers': 10000,

        'Orders': 100000,

        'OrderItems': 500000,

        'Products': 50000,

    }



    join_conditions = [

        ('Customers', 'Orders'),

        ('Orders', 'OrderItems'),

        ('OrderItems', 'Products'),

    ]



    optimizer = JoinOptimizer(table_sizes, join_conditions)



    tables = ['Customers', 'Orders', 'OrderItems', 'Products']



    # 贪心

    greedy_order, greedy_cost = optimizer.greedy_join_order(tables)

    print(f"贪心顺序: {' → '.join(greedy_order)}")

    print(f"估计代价: {greedy_cost:,}")



    # DP

    dp_order, dp_cost = optimizer.dp_join_order(tables)

    print(f"\nDP顺序: {' → '.join(dp_order)}")

    print(f"DP代价: {dp_cost:,}")



    print("\n说明：")

    print("  - 不同的Join顺序代价可能差几个数量级")

    print("  - PostgreSQL、MySQL等使用动态规划或贪心")

    print("  - 实际优化器考虑统计信息和索引")


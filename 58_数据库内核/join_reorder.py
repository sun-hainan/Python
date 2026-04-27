# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / join_reorder



本文件实现 join_reorder 相关的算法功能。

"""



import itertools

from dataclasses import dataclass

from typing import List, Dict, Set, Tuple, Optional





@dataclass

class Table:

    """表定义"""

    name: str  # 表名

    rows: int  # 行数

    size: float  # 大小(MB)





@dataclass

class JoinCondition:

    """连接条件"""

    left_table: str  # 左表

    right_table: str  # 右表

    join_column: str  # 连接列





class SelingerOptimizer:

    """

    Selinger动态规划Join优化器

    核心思想：最优N表Join = 最优子集Join + 剩余表

    """



    def __init__(self, tables: List[Table], join_conditions: List[JoinCondition]):

        self.tables = {t.name: t for t in tables}  # 表名->表对象映射

        self.join_conditions = join_conditions  # 连接条件列表

        self.best_plans: Dict[frozenset, 'JoinPlan'] = {}  # 最优计划缓存



    def build_join_graph(self) -> Dict[str, List[str]]:

        """构建连接图，返回每个表的邻居列表"""

        graph = {t.name: [] for t in self.tables}

        for cond in self.join_conditions:

            graph[cond.left_table].append(cond.right_table)

            graph[cond.right_table].append(cond.left_table)

        return graph



    def estimate_join_cost(self, left_plan: 'JoinPlan', right_plan: 'JoinPlan',

                           join_cond: JoinCondition) -> Tuple[float, int]:

        """

        估算Join代价

        返回: (代价, 输出行数)

        使用嵌套循环模型估算

        """

        outer_rows = left_plan.output_rows

        inner_rows = right_plan.output_rows



        # 假设小表作内表构建哈希表

        if inner_rows < outer_rows:

            outer_rows, inner_rows = inner_rows, outer_rows



        # Hash Join代价: 扫描内表 + 扫描外表 + 构建哈希表 + 探测

        io_cost = inner_rows * 0.001 + outer_rows * 0.001

        cpu_cost = (inner_rows + outer_rows) * 0.0001

        cost = io_cost + cpu_cost

        output_rows = int(outer_rows * inner_rows * 0.01)  # 假设连接选择性1%

        return cost, min(output_rows, outer_rows + inner_rows)



    def find_join_condition(self, left_tables: Set[str],

                            right_tables: Set[str]) -> Optional[JoinCondition]:

        """查找两个表集之间的连接条件"""

        for cond in self.join_conditions:

            if (cond.left_table in left_tables and cond.right_table in right_tables) or \

               (cond.left_table in right_tables and cond.right_table in left_tables):

                return cond

        return None



    def enumerate_plans(self, table_set: frozenset) -> 'JoinPlan':

        """

        枚举给定表集的所有可能Join计划

        使用动态规划: 最优K表 = 最优(J表) Join (K-J表)

        """

        if table_set in self.best_plans:

            return self.best_plans[table_set]



        tables = list(table_set)

        if len(tables) == 1:

            # 单表，直接扫描

            table = self.tables[tables[0]]

            plan = JoinPlan(

                tables=list(table_set),

                cost=table.rows * 0.001,

                output_rows=table.rows,

                operator="scan",

                children=[]

            )

            self.best_plans[table_set] = plan

            return plan



        best_plan = None

        best_cost = float('inf')



        # 枚举所有划分方式

        for subset_size in range(1, len(tables) // 2 + 1):

            for subset in itertools.combinations(tables, subset_size):

                left_set = frozenset(subset)

                right_set = table_set - left_set



                # 递归获取子集的最优计划

                left_plan = self.enumerate_plans(left_set)

                right_plan = self.enumerate_plans(right_set)



                # 查找连接条件

                join_cond = self.find_join_condition(left_plan.tables, right_plan.tables)

                if not join_cond:

                    continue



                # 估算代价

                cost, output_rows = self.estimate_join_cost(left_plan, right_plan, join_cond)

                total_cost = left_plan.cost + right_plan.cost + cost



                if total_cost < best_cost:

                    best_cost = total_cost

                    best_plan = JoinPlan(

                        tables=list(table_set),

                        cost=total_cost,

                        output_rows=output_rows,

                        operator="hash_join",

                        children=[left_plan, right_plan],

                        join_cond=join_cond

                    )



        self.best_plans[table_set] = best_plan

        return best_plan



    def optimize(self) -> 'JoinPlan':

        """执行Selinger优化算法"""

        all_tables = frozenset(self.tables.keys())

        return self.enumerate_plans(all_tables)





@dataclass

class JoinPlan:

    """Join执行计划"""

    tables: List[str]  # 涉及的表

    cost: float  # 代价

    output_rows: int  # 输出行数

    operator: str  # 操作类型

    children: List['JoinPlan'] = None  # 子计划

    join_cond: JoinCondition = None  # 连接条件





def print_plan(plan: JoinPlan, indent: int = 0):

    """打印Join计划树"""

    prefix = "  " * indent

    print(f"{prefix}-> {plan.operator} (cost={plan.cost:.4f}, rows={plan.output_rows})")

    if plan.join_cond:

        print(f"{prefix}   join: {plan.join_cond.left_table} = {plan.join_cond.right_table}")

    print(f"{prefix}   tables: {plan.tables}")

    if plan.children:

        for child in plan.children:

            print_plan(child, indent + 1)





if __name__ == "__main__":

    # 测试Selinger Join优化

    tables = [

        Table("R", 1000, 1.0),   # R表，1000行

        Table("S", 500, 0.5),    # S表，500行

        Table("T", 2000, 2.0),   # T表，2000行

        Table("U", 800, 0.8),    # U表，800行

    ]



    # 定义连接条件: R-S, S-T, T-U, R-U

    join_conditions = [

        JoinCondition("R", "S", "id"),

        JoinCondition("S", "T", "id"),

        JoinCondition("T", "U", "id"),

        JoinCondition("R", "U", "id"),

    ]



    optimizer = SelingerOptimizer(tables, join_conditions)

    optimal_plan = optimizer.optimize()



    print("=== Selinger优化最优Join顺序 ===")

    print_plan(optimal_plan)



    # 测试不同表数量的场景

    print("\n=== 3表Join测试 ===")

    tables_3 = [Table("A", 100, 0.1), Table("B", 200, 0.2), Table("C", 150, 0.15)]

    joins_3 = [

        JoinCondition("A", "B", "id"),

        JoinCondition("B", "C", "id"),

    ]

    opt3 = SelingerOptimizer(tables_3, joins_3)

    plan3 = opt3.optimize()

    print_plan(plan3)


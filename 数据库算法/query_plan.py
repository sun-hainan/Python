# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / query_plan



本文件实现 query_plan 相关的算法功能。

"""



import math

from typing import List, Dict, Tuple, Optional, Set, Callable

from collections import defaultdict

from dataclasses import dataclass





@dataclass

class TableStats:

    """表的统计信息"""

    table_name: str

    num_rows: int               # 行数

    num_pages: int               # 页面数

    tuple_size: int             # 元组大小（字节）

    indexes: List[str] = None   # 可用索引列表



    def __post_init__(self):

        if self.indexes is None:

            self.indexes = []





@dataclass

class JoinResult:

    """连接结果"""

    left_rows: int

    right_rows: int

    result_rows: int

    cost: float

    plan_description: str





class QueryPlanOptimizer:

    """查询计划优化器（使用动态规划）"""



    def __init__(self):

        self.table_stats: Dict[str, TableStats] = {}

        self.join_costs: Dict[Tuple[str, str], float] = {}  # 连接代价



    def register_table(self, table_name: str, num_rows: int,

                      tuple_size: int = 100, indexes: List[str] = None):

        """

        注册表统计信息

        

        Args:

            table_name: 表名

            num_rows: 行数

            tuple_size: 元组大小（字节）

            indexes: 可用索引列表

        """

        # 估算页面数（假设页面大小4KB）

        page_size = 4096

        num_pages = max(1, (num_rows * tuple_size) // page_size)

        

        self.table_stats[table_name] = TableStats(

            table_name=table_name,

            num_rows=num_rows,

            num_pages=num_pages,

            tuple_size=tuple_size,

            indexes=indexes or []

        )



    def estimate_scan_cost(self, table_name: str, use_index: bool = False) -> float:

        """

        估算扫描代价

        

        Args:

            table_name: 表名

            use_index: 是否使用索引

            

        Returns:

            扫描代价（页面I/O数）

        """

        stats = self.table_stats.get(table_name)

        if not stats:

            return float('inf')

        

        if use_index:

            # 索引扫描：索引页 + 数据页

            return 1 + stats.num_pages * 0.1  # 简化估算

        else:

            # 全表扫描

            return stats.num_pages



    def estimate_join_cost(self, left_table: str, right_table: str,

                          join_method: str = "hash") -> float:

        """

        估算连接代价

        

        Args:

            left_table: 左表

            right_table: 右表

            join_method: 连接方法 (hash, nested_loop, sort_merge)

            

        Returns:

            连接代价（I/O数）

        """

        left_stats = self.table_stats.get(left_table)

        right_stats = self.table_stats.get(right_table)

        

        if not left_stats or not right_stats:

            return float('inf')

        

        if join_method == "hash":

            # Hash Join：小表build，大表probe

            smaller = min(left_stats.num_pages, right_stats.num_pages)

            larger = max(left_stats.num_pages, right_stats.num_pages)

            return smaller + larger

        

        elif join_method == "nested_loop":

            # NestLoop：外表 * 内表扫描

            outer_cost = left_stats.num_pages

            inner_cost = right_stats.num_pages

            return outer_cost + left_stats.num_rows * inner_cost

        

        elif join_method == "sort_merge":

            # SortMergeJoin：排序 + 合并

            left_sort = left_stats.num_pages * math.log2(left_stats.num_pages)

            right_sort = right_stats.num_pages * math.log2(right_stats.num_pages)

            return left_sort + right_sort + left_stats.num_pages + right_stats.num_pages

        

        return float('inf')



    def optimize(self, tables: List[str]) -> Tuple[float, List[str], str]:

        """

        使用动态规划优化查询计划

        

        Args:

            tables: 涉及的表列表

            

        Returns:

            (最小代价, 最优表顺序, 计划描述)

        """

        if not tables:

            return 0, [], "No tables"

        

        if len(tables) == 1:

            cost = self.estimate_scan_cost(tables[0])

            return cost, tables, f"TableScan({tables[0]})"

        

        # DP状态: {frozenset(tables): (cost, order, description)}

        dp: Dict[frozenset, Tuple[float, List[str], str]] = {}

        

        # 初始化：单个表的代价

        for table in tables:

            cost = self.estimate_scan_cost(table)

            dp[frozenset([table])] = (cost, [table], f"TableScan({table})")

        

        # 逐步增大连接集合

        for size in range(2, len(tables) + 1):

            # 生成所有大小为size的表组合

            for subset in self._generate_subsets(tables, size):

                best_cost = float('inf')

                best_order = None

                best_desc = None

                

                # 枚举所有分割点

                for left_size in range(1, size):

                    left_subsets = self._generate_subsets(list(subset), left_size)

                    

                    for left in left_subsets:

                        right = frozenset(subset - left)

                        

                        if left not in dp or right not in dp:

                            continue

                        

                        left_cost, left_order, left_desc = dp[left]

                        right_cost, right_order, right_desc = dp[right]

                        

                        # 估算连接代价

                        join_cost = self.estimate_join_cost(

                            left_order[-1],  # 简化：假设最后一个是驱动表

                            right_order[-1],

                            "hash"

                        )

                        

                        total_cost = left_cost + right_cost + join_cost

                        

                        if total_cost < best_cost:

                            best_cost = total_cost

                            best_order = left_order + right_order

                            best_desc = f"HashJoin({left_desc}, {right_desc})"

                

                if best_order:

                    dp[subset] = (best_cost, best_order, best_desc)

        

        # 返回最优计划

        best_subset = frozenset(tables)

        if best_subset in dp:

            cost, order, desc = dp[best_subset]

            return cost, order, desc

        

        return float('inf'), [], "No plan found"



    def _generate_subsets(self, tables: List[str], size: int) -> List[frozenset]:

        """生成指定大小的所有子集"""

        if size == 0:

            return [frozenset()]

        

        result = []

        self._combinations(tables, size, 0, frozenset(), result)

        return result



    def _combinations(self, tables: List[str], size: int,

                     start: int, current: frozenset, result: List[frozenset]):

        """生成组合"""

        if len(current) == size:

            result.append(current)

            return

        

        for i in range(start, len(tables)):

            self._combinations(tables, size, i + 1,

                             current | frozenset([tables[i]]), result)



    def enumerate_plans(self, tables: List[str], max_depth: int = 3) -> List[Dict]:

        """

        枚举所有可能的查询计划

        

        Args:

            tables: 表列表

            max_depth: 最大深度

            

        Returns:

            计划列表

        """

        plans = []

        

        def enumerate_rec(current_tables: List[str], depth: int, path: List[str]):

            if depth >= max_depth or len(current_tables) == 1:

                plans.append(path.copy())

                return

            

            for i in range(len(current_tables)):

                for j in range(i + 1, len(current_tables)):

                    left = current_tables[i]

                    right = current_tables[j]

                    

                    # 尝试不同的连接顺序

                    remaining = [t for k, t in enumerate(current_tables)

                               if k != i and k != j]

                    

                    for method in ["hash", "nested_loop", "sort_merge"]:

                        new_path = path + [f"{method}({left},{right})"]

                        enumerate_rec(remaining + [f"({left}x{right})"], depth + 1, new_path)

        

        enumerate_rec(tables, 0, [])

        return plans





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 70)

    print("查询计划优化（动态规划）测试")

    print("=" * 70)



    optimizer = QueryPlanOptimizer()



    # 注册表统计信息

    print("\n--- 注册表统计信息 ---")

    

    optimizer.register_table("orders", num_rows=100000, tuple_size=80)

    optimizer.register_table("customers", num_rows=50000, tuple_size=200)

    optimizer.register_table("products", num_rows=20000, tuple_size=150)

    optimizer.register_table("order_items", num_rows=500000, tuple_size=60)



    for name, stats in optimizer.table_stats.items():

        print(f"  {name}: {stats.num_rows:,} 行, {stats.num_pages:,} 页")



    # 测试单个表的优化

    print("\n--- 单表查询优化 ---")

    cost, order, desc = optimizer.optimize(["customers"])

    print(f"  查询: customers")

    print(f"  最优代价: {cost:.2f} I/O")

    print(f"  计划: {desc}")



    # 测试两表连接

    print("\n--- 两表连接优化 ---")

    cost, order, desc = optimizer.optimize(["orders", "customers"])

    print(f"  查询: orders JOIN customers")

    print(f"  最优顺序: {' -> '.join(order)}")

    print(f"  最小代价: {cost:.2f} I/O")

    print(f"  计划: {desc}")



    # 测试三表连接

    print("\n--- 三表连接优化 ---")

    cost, order, desc = optimizer.optimize(["orders", "customers", "products"])

    print(f"  查询: orders JOIN customers JOIN products")

    print(f"  最优顺序: {' -> '.join(order)}")

    print(f"  最小代价: {cost:.2f} I/O")

    print(f"  计划: {desc}")



    # 测试四表连接

    print("\n--- 四表连接优化 ---")

    cost, order, desc = optimizer.optimize(["orders", "customers", "products", "order_items"])

    print(f"  查询: orders JOIN customers JOIN products JOIN order_items")

    print(f"  最优顺序: {' -> '.join(order)}")

    print(f"  最小代价: {cost:.2f} I/O")

    print(f"  计划: {desc}")



    # 估算不同连接方法的代价

    print("\n--- 不同连接方法代价对比 ---")

    for method in ["hash", "nested_loop", "sort_merge"]:

        cost = optimizer.estimate_join_cost("orders", "customers", method)

        print(f"  orders JOIN customers ({method}): {cost:.2f} I/O")



    # 验证优化效果

    print("\n--- 优化效果验证 ---")

    

    # 手动枚举几种顺序

    orders = [

        ("orders", "customers", "products"),

        ("customers", "orders", "products"),

        ("products", "orders", "customers"),

    ]

    

    for order in orders:

        cost, _, desc = optimizer.optimize(list(order))

        print(f"  顺序 {order}: 代价={cost:.2f}")



    print("\n" + "=" * 70)

    print("复杂度: O(3^n * n) 动态规划，n=表数量")

    print("=" * 70)


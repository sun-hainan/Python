# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / cost_estimation



本文件实现 cost_estimation 相关的算法功能。

"""



import math

from typing import List, Dict, Tuple, Optional, Any

from collections import defaultdict

from dataclasses import dataclass, field





@dataclass

class ColumnStats:

    """列统计信息"""

    column_name: str

    num_distinct: int               # 不同值数量

    null_count: int = 0             # NULL值数量

    min_value: Any = None

    max_value: Any = None

    histogram: Dict[Any, int] = field(default_factory=dict)  # 值 -> 频率



    def get_selectivity_eq(self, value: Any) -> float:

        """等值查询选择率"""

        if self.num_distinct == 0:

            return 1.0

        return 1.0 / self.num_distinct



    def get_selectivity_range(self, low: Any, high: Any) -> float:

        """范围查询选择率"""

        if self.min_value is None or self.max_value is None:

            return 1.0

        

        total_range = self.max_value - self.min_value

        if total_range == 0:

            return 1.0 / self.num_distinct

        

        query_range = high - low

        return min(1.0, query_range / total_range * 1.1)  # 1.1是安全因子





@dataclass

class TableStats:

    """表统计信息"""

    table_name: str

    num_rows: int                   # 总行数

    num_pages: int                  # 总页面数

    tuple_size: int                 # 元组大小

    columns: Dict[str, ColumnStats] = field(default_factory=dict)

    indexes: List['IndexStats'] = field(default_factory=list)



    def estimate_result_size(self, filter_condition: Dict[str, Tuple[str, Any]]) -> int:

        """

        估算过滤后的结果行数

        

        Args:

            filter_condition: {列名: (操作符, 值)}

                             例如: {"age": (">", 30)}

            

        Returns:

            估算的行数

        """

        result = self.num_rows

        

        for col_name, (op, value) in filter_condition.items():

            if col_name not in self.columns:

                continue

            

            col = self.columns[col_name]

            

            if op == "=":

                selectivity = col.get_selectivity_eq(value)

            elif op in (">", "<", ">=", "<="):

                selectivity = col.get_selectivity_range(value, value)

            elif op == "BETWEEN":

                low, high = value

                selectivity = col.get_selectivity_range(low, high)

            elif op == "IN":

                selectivity = len(value) / col.num_distinct if col.num_distinct > 0 else 1.0

            else:

                selectivity = 0.5  # 默认

            

            result *= selectivity

        

        return max(1, int(result))





@dataclass

class IndexStats:

    """索引统计信息"""

    index_name: str

    index_columns: List[str]        # 索引列

    index_type: str                  # 类型: BTree, Hash, etc.

    num_levels: int                 # B树层数

    num_leaf_pages: int             # 叶子页数

    num_entries: int                # 索引条目数

    clustering_factor: float = 1.0   # 聚簇因子（影响随机I/O）



    def estimate_scan_cost(self, num_result_rows: int, is_range: bool = False) -> float:

        """

        估算索引扫描代价

        

        Args:

            num_result_rows: 预计返回的行数

            is_range: 是否是范围扫描

            

        Returns:

            I/O代价

        """

        if is_range:

            # 范围扫描：树遍历 + 叶子页顺序扫描

            return self.num_levels + self.num_leaf_pages * 0.1

        else:

            # 点查询：树遍历 + 随机I/O

            random_io = min(num_result_rows * self.clustering_factor, self.num_leaf_pages)

            return self.num_levels + random_io





class CostEstimator:

    """查询代价估算器"""



    PAGE_SIZE = 4096  # 页面大小4KB

    IO_COST_RANDOM = 1.0   # 随机I/O成本

    IO_COST_SEQ = 0.1     # 顺序I/O成本（相对值）



    def __init__(self):

        self.tables: Dict[str, TableStats] = {}

        self.join_cardinalities: Dict[Tuple[str, str], int] = {}



    def register_table(self, table_name: str, num_rows: int, tuple_size: int):

        """注册表"""

        num_pages = max(1, (num_rows * tuple_size) // self.PAGE_SIZE)

        self.tables[table_name] = TableStats(

            table_name=table_name,

            num_rows=num_rows,

            num_pages=num_pages,

            tuple_size=tuple_size

        )



    def register_column(self, table_name: str, column_name: str,

                      num_distinct: int, min_value: Any = None,

                      max_value: Any = None, histogram: Dict[Any, int] = None):

        """注册列统计"""

        if table_name not in self.tables:

            return

        

        self.tables[table_name].columns[column_name] = ColumnStats(

            column_name=column_name,

            num_distinct=num_distinct,

            min_value=min_value,

            max_value=max_value,

            histogram=histogram or {}

        )



    def register_index(self, table_name: str, index_name: str,

                      columns: List[str], index_type: str = "BTree"):

        """注册索引"""

        if table_name not in self.tables:

            return

        

        # 估算索引大小

        table = self.tables[table_name]

        

        # 简化：假设BTree索引有 log_n(num_rows) 层

        num_levels = max(1, int(math.log2(table.num_rows)))

        num_leaf_pages = max(1, table.num_pages // 10)  # 简化估算

        

        index = IndexStats(

            index_name=index_name,

            index_columns=columns,

            index_type=index_type,

            num_levels=num_levels,

            num_leaf_pages=num_leaf_pages,

            num_entries=table.num_rows

        )

        

        self.tables[table_name].indexes.append(index)



    def estimate_table_scan(self, table_name: str, use_index: bool = False) -> float:

        """估算全表扫描代价"""

        if table_name not in self.tables:

            return float('inf')

        

        table = self.tables[table_name]

        

        if use_index:

            # 索引扫描

            if table.indexes:

                return table.indexes[0].estimate_scan_cost(table.num_rows)

            return table.num_pages

        

        # 全表扫描

        return table.num_pages



    def estimate_index_scan(self, table_name: str, index_name: str,

                           filter_cond: Dict[str, Tuple[str, Any]]) -> Tuple[float, int]:

        """

        估算索引扫描代价

        

        Returns:

            (I/O代价, 估算行数)

        """

        if table_name not in self.tables:

            return float('inf'), 0

        

        table = self.tables[table_name]

        index = None

        

        for idx in table.indexes:

            if idx.index_name == index_name:

                index = idx

                break

        

        if not index:

            return float('inf'), 0

        

        # 估算结果行数

        result_rows = table.estimate_result_size(filter_cond)

        

        # 判断是点查还是范围查

        is_range = any(op in (">", "<", ">=", "<=", "BETWEEN") for op, _ in filter_cond.values())

        

        cost = index.estimate_scan_cost(result_rows, is_range)

        

        return cost, result_rows



    def estimate_join(self, left_table: str, right_table: str,

                     join_condition: Dict[str, str],  # {left_col: right_col}

                     join_type: str = "hash") -> Tuple[float, int]:

        """

        估算连接代价

        

        Returns:

            (I/O代价, 结果行数)

        """

        left = self.tables.get(left_table)

        right = self.tables.get(right_table)

        

        if not left or not right:

            return float('inf'), 0

        

        # 估算结果行数（简化：假设连接列基数相同）

        join_col = list(join_condition.values())[0]

        right_col_stats = right.columns.get(join_col)

        

        if right_col_stats:

            join_selectivity = 1.0 / max(right_col_stats.num_distinct, 1)

        else:

            join_selectivity = 0.1  # 默认

        

        result_rows = int(left.num_rows * right.num_rows * join_selectivity)

        result_rows = max(1, result_rows)

        

        # 估算I/O代价

        if join_type == "hash":

            # Hash Join：小表build，大表probe

            smaller_pages = min(left.num_pages, right.num_pages)

            larger_pages = max(left.num_pages, right.num_pages)

            cost = smaller_pages + larger_pages

        

        elif join_type == "nested_loop":

            # NestLoop

            outer_cost = left.num_pages

            inner_cost = right.num_pages * left.num_rows

            cost = outer_cost + inner_cost

        

        elif join_type == "sort_merge":

            # SortMergeJoin

            left_sort = left.num_pages * math.log2(left.num_pages)

            right_sort = right.num_pages * math.log2(right.num_pages)

            cost = left_sort + right_sort + left.num_pages + right.num_pages

        

        else:

            cost = left.num_pages + right.num_pages

        

        return cost, result_rows



    def select_optimal_plan(self, table_name: str,

                           filter_cond: Dict[str, Tuple[str, Any]]) -> Dict:

        """

        选择最优访问计划

        

        Returns:

            最优计划描述

        """

        if table_name not in self.tables:

            return {"method": "none", "cost": float('inf')}

        

        table = self.tables[table_name]

        

        plans = []

        

        # 全表扫描

        seq_cost = self.estimate_table_scan(table_name, use_index=False)

        result_rows = table.estimate_result_size(filter_cond)

        plans.append({

            "method": "SeqScan",

            "cost": seq_cost,

            "estimated_rows": result_rows

        })

        

        # 索引扫描

        for idx in table.indexes:

            idx_cost, idx_rows = self.estimate_index_scan(

                table_name, idx.index_name, filter_cond

            )

            plans.append({

                "method": f"IndexScan({idx.index_name})",

                "cost": idx_cost,

                "estimated_rows": idx_rows

            })

        

        # 选择代价最小的

        best = min(plans, key=lambda p: p["cost"])

        

        return best





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 70)

    print("查询代价估算测试")

    print("=" * 70)



    estimator = CostEstimator()



    # 设置表统计

    print("\n--- 注册表和索引 ---")

    

    estimator.register_table("orders", num_rows=100000, tuple_size=80)

    estimator.register_column("orders", "order_id", num_distinct=100000, min_value=1, max_value=100000)

    estimator.register_column("orders", "customer_id", num_distinct=5000, min_value=1, max_value=5000)

    estimator.register_column("orders", "order_date", num_distinct=365, min_value=1, max_value=365)

    estimator.register_index("orders", "idx_customer", ["customer_id"], "BTree")

    estimator.register_index("orders", "idx_date", ["order_date"], "BTree")



    estimator.register_table("customers", num_rows=50000, tuple_size=200)

    estimator.register_column("customers", "customer_id", num_distinct=50000, min_value=1, max_value=50000)

    estimator.register_column("customers", "region", num_distinct=10)



    # 全表扫描代价

    print("\n--- 扫描代价估算 ---")

    seq_cost = estimator.estimate_table_scan("orders", use_index=False)

    print(f"  orders 全表扫描: {seq_cost:.2f} I/O ({100000} 行)")



    idx_cost, rows = estimator.estimate_index_scan("orders", "idx_customer", {"customer_id": ("=", 123)})

    print(f"  orders 索引扫描(idx_customer): {idx_cost:.2f} I/O ({rows} 行)")



    # 过滤代价

    print("\n--- 过滤代价估算 ---")

    

    filters = [

        {"customer_id": ("=", 123)},

        {"region": ("=", "NORTH")},

        {"order_date": (">", 300)},

        {"order_date": ("BETWEEN", (100, 200))},

    ]

    

    for f in filters:

        plan = estimator.select_optimal_plan("orders", f)

        print(f"  过滤{f}: 选择 {plan['method']}, 代价={plan['cost']:.2f}, 行数={plan['estimated_rows']}")



    # 连接代价

    print("\n--- 连接代价估算 ---")

    

    join_cost, join_rows = estimator.estimate_join(

        "orders", "customers",

        {"customer_id": "customer_id"},

        "hash"

    )

    print(f"  orders HashJoin customers: {join_cost:.2f} I/O, 约{join_rows:,} 行")



    join_cost, join_rows = estimator.estimate_join(

        "orders", "customers",

        {"customer_id": "customer_id"},

        "nested_loop"

    )

    print(f"  orders NestLoop customers: {join_cost:.2f} I/O, 约{join_rows:,} 行")



    join_cost, join_rows = estimator.estimate_join(

        "orders", "customers",

        {"customer_id": "customer_id"},

        "sort_merge"

    )

    print(f"  orders SortMergeJoin customers: {join_cost:.2f} I/O, 约{join_rows:,} 行")



    # 选择率估算

    print("\n--- 选择率分析 ---")

    

    col = estimator.tables["orders"].columns["customer_id"]

    eq_sel = col.get_selectivity_eq(123)

    print(f"  customer_id=123 选择率: {eq_sel:.6f} (约{1/eq_sel:.0f}行对应1个值)")



    col = estimator.tables["customers"].columns["region"]

    eq_sel = col.get_selectivity_eq("NORTH")

    print(f"  region='NORTH' 选择率: {eq_sel:.6f} (约{1/eq_sel:.0f}个不同值)")



    print("\n" + "=" * 70)

    print("复杂度: O(N) 统计收集, O(1) 单次估算")

    print("=" * 70)


# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / query_cost_model



本文件实现 query_cost_model 相关的算法功能。

"""



import math

from dataclasses import dataclass

from typing import List, Dict, Any





@dataclass

class TableStats:

    """表统计信息"""

    table_name: str  # 表名

    num_rows: int  # 行数

    num_pages: int  # 页面数

    tuple_length: int  # 元组长度(字节)

    index_stats: Dict[str, float]  # 索引 -> 选择性





@dataclass

class PlanNode:

    """查询计划节点"""

    operator: str  # 操作类型：seq_scan/index_scan/nested_loop/hash_join/sort

    cost: float  # 代价

    rows: int  # 输出行数

    children: List['PlanNode'] = None

    info: Dict[str, Any] = None





def seq_scan_cost(table_stats: TableStats, selectivity: float = 1.0) -> PlanNode:

    """

    计算顺序扫描代价

    代价 = 页面数 * 选择性 + CPU处理元组代价

    """

    page_cost = table_stats.num_pages * selectivity  # IO代价

    cpu_cost = table_stats.num_rows * selectivity * 0.01  # CPU代价

    total_cost = page_cost + cpu_cost

    return PlanNode(

        operator="seq_scan",

        cost=total_cost,

        rows=int(table_stats.num_rows * selectivity),

        info={"table": table_stats.table_name}

    )





def index_scan_cost(table_stats: TableStats, index_name: str,

                    selectivity: float, index_selectivity: float) -> PlanNode:

    """

    计算索引扫描代价

    代价 = 索引页IO + 回表IO + CPU代价

    """

    index_pages = 10  # 索引根到叶的深度估算

    index_io = index_pages * index_selectivity  # 索引页访问

    heap_io = table_stats.num_pages * selectivity  # 回表页访问

    cpu_cost = table_stats.num_rows * selectivity * 0.02  # CPU代价

    total_cost = index_io + heap_io + cpu_cost

    return PlanNode(

        operator="index_scan",

        cost=total_cost,

        rows=int(table_stats.num_rows * selectivity),

        info={"table": table_stats.table_name, "index": index_name}

    )





def hash_join_cost(inner_node: PlanNode, outer_node: PlanNode,

                   build_rows: int, probe_rows: int) -> PlanNode:

    """

    计算Hash Join代价

    构建阶段代价 + 探测阶段代价

    """

    build_cost = inner_node.cost  # 构建哈希表代价

    probe_cpu = probe_rows * 0.005  # 探测阶段CPU代价

    probe_cost = outer_node.cost + probe_cpu  # 探测代价

    total_cost = build_cost + probe_cost

    return PlanNode(

        operator="hash_join",

        cost=total_cost,

        rows=build_rows * outer_node.rows // max(build_rows, 1),

        children=[inner_node, outer_node],

        info={"strategy": "hash"}

    )





def nested_loop_join_cost(outer_node: PlanNode, inner_stats: TableStats,

                          outer_rows: int, join_selectivity: float) -> PlanNode:

    """

    计算嵌套循环连接代价

    代价 = 外表代价 + 外表行数 * 内表代价

    """

    outer_cost = outer_node.cost

    inner_scan = seq_scan_cost(inner_stats, 1.0)

    inner_cost_per_row = inner_scan.cost

    inner_cost = outer_rows * inner_cost_per_row * join_selectivity

    total_cost = outer_cost + inner_cost

    return PlanNode(

        operator="nested_loop_join",

        cost=total_cost,

        rows=int(outer_rows * inner_stats.num_rows * join_selectivity),

        children=[outer_node, inner_scan],

        info={"strategy": "nested_loop"}

    )





def sort_cost(base_node: PlanNode, num_rows: int) -> PlanNode:

    """

    计算排序代价

    代价 = 排序CPU代价 + 归并IO代价

    """

    cpu_sort = num_rows * math.log2(num_rows) * 0.001

    pages = num_rows * 100 / 8192  # 假设每页8KB，每行100字节

    io_cost = pages * 2 * 0.5  # 读写各一次

    total_cost = base_node.cost + cpu_sort + io_cost

    return PlanNode(

        operator="sort",

        cost=total_cost,

        rows=num_rows,

        children=[base_node],

        info={"sort_keys": []}

    )





def choose_best_plan(plans: List[PlanNode]) -> PlanNode:

    """选择代价最低的执行计划"""

    return min(plans, key=lambda p: p.cost)





def print_plan(plan: PlanNode, indent: int = 0):

    """打印执行计划"""

    prefix = "  " * indent

    print(f"{prefix}-> {plan.operator} (cost={plan.cost:.2f}, rows={plan.rows})")

    if plan.info:

        for k, v in plan.info.items():

            print(f"{prefix}    {k}={v}")

    if plan.children:

        for child in plan.children:

            print_plan(child, indent + 1)





if __name__ == "__main__":

    # 测试查询代价模型

    orders_stats = TableStats(

        table_name="orders",

        num_rows=100000,

        num_pages=2000,

        tuple_length=80,

        index_stats={"idx_cust": 0.1, "idx_date": 0.05}

    )

    customers_stats = TableStats(

        table_name="customers",

        num_rows=10000,

        num_pages=200,

        tuple_length=200,

        index_stats={"pk_customer_id": 0.0001}

    )



    # 场景1: 全表扫描orders

    seq_plan = seq_scan_cost(orders_stats)

    print("=== 顺序扫描 orders ===")

    print_plan(seq_plan)



    # 场景2: 索引扫描orders(cust_id='C001')

    index_plan = index_scan_cost(orders_stats, "idx_cust", 0.1, 0.01)

    print("\n=== 索引扫描 orders ===")

    print_plan(index_plan)



    # 场景3: Hash Join orders × customers

    orders_scan = seq_scan_cost(orders_stats)

    cust_scan = seq_scan_cost(customers_stats)

    hash_join = hash_join_cost(cust_scan, orders_scan, 10000, 100000)

    print("\n=== Hash Join ===")

    print_plan(hash_join)



    # 场景4: 嵌套循环连接

    nl_join = nested_loop_join_cost(orders_scan, customers_stats, 100000, 0.01)

    print("\n=== 嵌套循环连接 ===")

    print_plan(nl_join)



    # 场景5: 排序

    sorted_plan = sort_cost(seq_plan, 100000)

    print("\n=== 排序 ===")

    print_plan(sorted_plan)



    # 比较多个计划

    print("\n=== 计划选择 ===")

    plans = [seq_plan, index_plan]

    best = choose_best_plan(plans)

    print(f"最优计划: {best.operator}, 代价={best.cost:.2f}")


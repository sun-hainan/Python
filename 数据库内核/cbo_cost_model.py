# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / cbo_cost_model

本文件实现 cbo_cost_model 相关的算法功能。
"""

from typing import List, Dict, Tuple

# 定义表的基础统计信息（示例）
class TableStats:
    def __init__(self, table_name: str, num_rows: int, num_pages: int, 
                 avg_row_width: int, index_info: Dict):
        self.table_name = table_name  # 表名
        self.num_rows = num_rows     # 行数
        self.num_pages = num_pages   # 页数
        self.avg_row_width = avg_row_width  # 平均行宽度（字节）
        self.index_info = index_info  # 索引信息字典

    def __repr__(self):
        return f"TableStats({self.table_name}, rows={self.num_rows}, pages={self.num_pages})"


class CostEstimator:
    """代价估算器：计算不同操作的开销"""
    
    # 机械臂寻道时间常数（毫秒）- 磁盘I/O开销
    SEEK_TIME = 10.0      # 一次寻道时间
    TRANSFER_TIME_PER_PAGE = 0.5  # 每页传输时间（毫秒）
    CPU_TUPLE_COST = 0.01  # 处理每条元组的CPU开销（毫秒）
    
    def __init__(self, page_size: int = 4096):
        self.page_size = page_size  # 页面大小（字节）
    
    def seq_scan_cost(self, table_stats: TableStats) -> float:
        """
        顺序扫描的代价
        = 寻道时间 + 页面传输时间
        = SEEK_TIME + num_pages * TRANSFER_TIME_PER_PAGE
        """
        seek_cost = self.SEEK_TIME
        transfer_cost = table_stats.num_pages * self.TRANSFER_TIME_PER_PAGE
        return seek_cost + transfer_cost
    
    def index_scan_cost(self, table_stats: TableStats, index_name: str, 
                        selectivity: float) -> Tuple[float, int]:
        """
        索引扫描的代价
        返回: (总代价, 访问的页面数)
        selectivity: 选择率（0~1之间）
        """
        if index_name not in table_stats.index_info:
            # 无索引，退化为顺序扫描
            return self.seq_scan_cost(table_stats), table_stats.num_pages
        
        idx_info = table_stats.index_info[index_name]
        index_height = idx_info.get("height", 3)  # B+树高度，默认3层
        index_pages = idx_info.get("pages", 10)   # 索引页面数
        
        # 索引探查代价（树高）+ 数据页访问代价（选择率 * 表页面数）
        probe_cost = index_height * self.SEEK_TIME  # 索引探查
        leaf_traverse_cost = index_pages * self.TRANSFER_TIME_PER_PAGE * selectivity * 0.5
        data_access_cost = table_stats.num_pages * selectivity * self.TRANSFER_TIME_PER_PAGE
        
        total_cost = probe_cost + leaf_traverse_cost + data_access_cost
        pages_accessed = int(index_pages * selectivity + table_stats.num_pages * selectivity)
        
        return total_cost, pages_accessed
    
    def join_cost(self, left_cost: float, right_cost: float, 
                  join_method: str, num_tuples: int) -> float:
        """
        Join操作的代价估算
        left_cost: 左子树的代价
        right_cost: 右子树的代价  
        join_method: join方法（nested_loop/hash_join/sort_merge）
        num_tuples: 连接后的结果元组数
        """
        base_cost = left_cost + right_cost
        
        if join_method == "nested_loop":
            # 嵌套循环连接：外层表全扫描 + 内层表重复扫描
            # 假设左表为外层，右表为内层
            return base_cost + left_cost * right_cost / 1000  # 简化估算
            
        elif join_method == "hash_join":
            # Hash连接：构建阶段 + 探查阶段
            return base_cost + num_tuples * self.CPU_TUPLE_COST * 2
            
        elif join_method == "sort_merge":
            # Sort-merge连接：排序 + 归并
            return base_cost + num_tuples * self.CPU_TUPLE_COST * 3
            
        return base_cost


class PlanNode:
    """执行计划节点"""
    def __init__(self, node_type: str, children: List['PlanNode'], cost: float):
        self.node_type = node_type   # 节点类型：seq_scan/index_scan/join等
        self.children = children      # 子节点列表
        self.cost = cost             # 该节点的代价
        self.info = {}               # 附加信息
    
    def __repr__(self):
        return f"PlanNode({self.node_type}, cost={self.cost:.2f})"


def compare_plans(plans: List[Tuple[str, float]]) -> str:
    """
    比较多个计划，选择代价最低的
    plans: [(plan_description, cost), ...]
    """
    if not plans:
        return ""
    
    best_plan = min(plans, key=lambda x: x[1])
    return f"最优计划: {best_plan[0]}, 代价={best_plan[1]:.2f}ms"


if __name__ == "__main__":
    # 构建示例表统计信息
    orders_table = TableStats(
        table_name="orders",
        num_rows=100000,
        num_pages=5000,
        avg_row_width=120,
        index_info={
            "idx_order_date": {"height": 3, "pages": 50, "type": "btree"},
            "idx_customer_id": {"height": 3, "pages": 40, "type": "btree"}
        }
    )
    
    customers_table = TableStats(
        table_name="customers",
        num_rows=50000,
        num_pages=2000,
        avg_row_width=200,
        index_info={
            "pk_customer_id": {"height": 3, "pages": 30, "type": "btree"}
        }
    )
    
    # 代价估算
    estimator = CostEstimator()
    
    # 方案1：orders顺序扫描
    cost_seq = estimator.seq_scan_cost(orders_table)
    
    # 方案2：orders索引扫描（日期过滤，选择率10%）
    cost_idx, pages = estimator.index_scan_cost(orders_table, "idx_order_date", 0.1)
    
    # 方案3：嵌套循环连接（orders JOIN customers）
    join_cost = estimator.join_cost(cost_idx, 
                                    estimator.seq_scan_cost(customers_table),
                                    "nested_loop", 10000)
    
    # 输出比较结果
    plans = [
        ("顺序扫描orders", cost_seq),
        ("索引扫描orders(idx_order_date)", cost_idx),
        ("Hash Join (orders ⋈ customers)", 
         estimator.join_cost(cost_seq, estimator.seq_scan_cost(customers_table), "hash_join", 10000))
    ]
    
    print("=" * 50)
    print("代价模型估算结果")
    print("=" * 50)
    for desc, cost in plans:
        print(f"  {desc}: {cost:.2f} ms")
    print()
    print(f"推荐计划: {compare_plans(plans)}")

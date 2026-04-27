# -*- coding: utf-8 -*-
"""
算法实现：数据库算法 / query_planner

本文件实现 query_planner 相关的算法功能。
"""

import re
import math
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class JoinMethod(Enum):
    """连接方法"""
    NESTED_LOOP = "nested_loop"
    HASH_JOIN = "hash_join"
    SORT_MERGE = "sort_merge"


class AccessPath(Enum):
    """访问路径"""
    TABLE_SCAN = "table_scan"
    INDEX_SCAN = "index_scan"
    INDEX_ONLY = "index_only"


@dataclass
class TableStats:
    """表统计信息"""
    table_name: str
    n_rows: int
    page_count: int
    column_stats: Dict[str, 'ColumnStats'] = None
    
    def __post_init__(self):
        if self.column_stats is None:
            self.column_stats = {}


@dataclass
class ColumnStats:
    """列统计信息"""
    column_name: str
    n_distinct: int
    min_val: Any = None
    max_val: Any = None
    null_fraction: float = 0.0
    histogram: List[Tuple[Any, float]] = None  # (值, 频率)
    
    def __post_init__(self):
        if self.histogram is None:
            self.histogram = []


@dataclass
class IndexInfo:
    """索引信息"""
    index_name: str
    table_name: str
    columns: List[str]
    unique: bool = False
    selective: bool = True  # 是否高选择性


@dataclass
class PhysicalPlan:
    """物理执行计划"""
    operation: str  # 操作类型
    cost: float  # 代价估计
    rows: int  # 估计行数
    children: List['PhysicalPlan'] = None
    access_path: AccessPath = AccessPath.TABLE_SCAN
    join_method: JoinMethod = None
    extra_info: Dict = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.extra_info is None:
            self.extra_info = {}
    
    def print_plan(self, indent: int = 0) -> str:
        """打印计划"""
        prefix = "  " * indent
        result = f"{prefix}{self.operation} (cost={self.cost:.2f}, rows={self.rows})\n"
        
        for child in self.children:
            result += child.print_plan(indent + 1)
        
        return result


class CostEstimator:
    """
    代价估算器
    
    代价模型：
    - cpu_cost: CPU处理代价
    - io_cost: 磁盘IO代价
    - 总代价 = w_cpu * cpu_cost + w_io * io_cost
    """
    
    def __init__(self, cpu_cost_weight: float = 1.0, io_cost_weight: float = 100.0):
        self.cpu_cost_weight = cpu_cost_weight
        self.io_cost_weight = io_cost_weight
        self.page_size = 4096  # 假设页大小4KB
        self.seq_read_cost = 1.0  # 顺序读一页的CPU代价
        self.rand_read_cost = 10.0  # 随机读一页的CPU代价
    
    def estimate_scan(self, table_stats: TableStats, has_index: bool = False) -> float:
        """估算全表扫描代价"""
        # IO代价：读取所有页
        io_cost = table_stats.page_count * self.seq_read_cost
        
        # CPU代价：处理每一行
        cpu_cost = table_stats.n_rows * 0.1
        
        return self.io_cost_weight * io_cost + self.cpu_cost_weight * cpu_cost
    
    def estimate_index_scan(self, index_stats: IndexInfo, selectivity: float, 
                          table_stats: TableStats) -> float:
        """估算索引扫描代价"""
        # 读取索引页
        index_pages = max(1, index_stats.table_name.__hash__() % 10 + 1)  # 简化估计
        io_cost = index_pages * self.rand_read_cost
        
        # 读取表数据页
        rows_to_read = int(table_stats.n_rows * selectivity)
        pages_to_read = max(1, int(rows_to_read * self.page_size / table_stats.page_count / self.page_size))
        io_cost += pages_to_read * self.rand_read_cost
        
        # CPU代价
        cpu_cost = rows_to_read * 0.1
        
        return self.io_cost_weight * io_cost + self.cpu_cost_weight * cpu_cost
    
    def estimate_join(self, left_plan: PhysicalPlan, right_plan: PhysicalPlan,
                     join_method: JoinMethod) -> float:
        """估算连接代价"""
        # 基础代价：两个子计划的代价
        base_cost = left_plan.cost + right_plan.cost
        
        # 连接处理代价
        if join_method == JoinMethod.NESTED_LOOP:
            # 外层行数 * 内层扫描代价 + 外层扫描代价
            join_cost = left_plan.rows * right_plan.cost + left_plan.cost
        elif join_method == JoinMethod.HASH_JOIN:
            # 构建哈希表 + 探测
            smaller = min(left_plan.rows, right_plan.rows)
            larger = max(left_plan.rows, right_plan.rows)
            build_cost = smaller * 0.01
            probe_cost = larger * 0.01
            join_cost = build_cost + probe_cost
        else:  # SORT_MERGE
            # 排序 + 合并
            sort_cost = left_plan.rows * math.log2(left_plan.rows) * 0.001
            sort_cost += right_plan.rows * math.log2(right_plan.rows) * 0.001
            join_cost = sort_cost + left_plan.rows + right_plan.rows
        
        return base_cost + join_cost


class QueryPlanner:
    """
    查询规划器
    
    简化实现：
    - 假设已解析为表和条件的列表
    - 使用贪心+动态规划选择连接顺序
    """
    
    def __init__(self, stats: Dict[str, TableStats], indexes: Dict[str, List[IndexInfo]]):
        self.stats = stats  # 表统计信息
        self.indexes = indexes  # 索引信息
        self.cost_estimator = CostEstimator()
    
    def create_simple_plan(self, table_name: str, conditions: List[str]) -> PhysicalPlan:
        """
        为单表查询创建计划
        
        参数:
            table_name: 表名
            conditions: WHERE条件列表
        """
        table_stats = self.stats.get(table_name)
        if table_stats is None:
            raise ValueError(f"Unknown table: {table_name}")
        
        # 估算选择率
        selectivity = self._estimate_selectivity(conditions)
        
        # 选择访问路径
        access_path = AccessPath.TABLE_SCAN
        if table_name in self.indexes:
            for idx in self.indexes[table_name]:
                if self._can_use_index(idx, conditions):
                    if selectivity < 0.1:  # 选择率低，使用索引
                        access_path = AccessPath.INDEX_SCAN
                        break
        
        # 估算代价和行数
        if access_path == AccessPath.INDEX_SCAN:
            idx = self.indexes[table_name][0]
            cost = self.cost_estimator.estimate_index_scan(idx, selectivity, table_stats)
        else:
            cost = self.cost_estimator.estimate_scan(table_stats)
        
        rows = int(table_stats.n_rows * selectivity)
        
        return PhysicalPlan(
            operation=f"{access_path.value} on {table_name}",
            cost=cost,
            rows=rows,
            access_path=access_path,
            extra_info={'table': table_name, 'selectivity': selectivity}
        )
    
    def create_join_plan(self, tables: List[str], join_conditions: List[Tuple[str, str]],
                        where_conditions: List[str] = None) -> PhysicalPlan:
        """
        为多表连接创建最优计划
        
        使用动态规划找到最优连接顺序
        """
        if len(tables) == 1:
            return self.create_simple_plan(tables[0], where_conditions or [])
        
        if len(tables) == 2:
            return self._create_two_table_plan(tables[0], tables[1], join_conditions)
        
        # 多表：贪心近似（简化）
        return self._greedy_join_plan(tables, join_conditions)
    
    def _create_two_table_plan(self, t1: str, t2: str, 
                              join_conditions: List[Tuple[str, str]]) -> PhysicalPlan:
        """为两表连接创建最优计划"""
        plan1 = PhysicalPlan(
            operation=f"scan {t1}",
            cost=self.cost_estimator.estimate_scan(self.stats[t1]),
            rows=self.stats[t1].n_rows
        )
        
        plan2 = PhysicalPlan(
            operation=f"scan {t2}",
            cost=self.cost_estimator.estimate_scan(self.stats[t2]),
            rows=self.stats[t2].n_rows
        )
        
        # 选择最优连接方法
        join_methods = [JoinMethod.HASH_JOIN, JoinMethod.NESTED_LOOP, JoinMethod.SORT_MERGE]
        best_method = JoinMethod.HASH_JOIN
        best_cost = float('inf')
        
        for method in join_methods:
            cost = self.cost_estimator.estimate_join(plan1, plan2, method)
            if cost < best_cost:
                best_cost = cost
                best_method = method
        
        return PhysicalPlan(
            operation=f"{best_method.value} join",
            cost=best_cost,
            rows=plan1.rows * plan2.rows * 0.1,  # 简化估计
            children=[plan1, plan2],
            join_method=best_method,
            extra_info={'tables': [t1, t2]}
        )
    
    def _greedy_join_plan(self, tables: List[str],
                         join_conditions: List[Tuple[str, str]]) -> PhysicalPlan:
        """贪心选择最优连接顺序"""
        remaining = set(tables)
        current_plan = None
        current_table = None
        
        while remaining:
            best_next = None
            best_cost = float('inf')
            best_plan = None
            
            for table in remaining:
                # 创建单表计划
                table_plan = PhysicalPlan(
                    operation=f"scan {table}",
                    cost=self.cost_estimator.estimate_scan(self.stats[table]),
                    rows=self.stats[table].n_rows
                )
                
                # 如果有当前计划，估算连接代价
                if current_plan is not None:
                    cost = self.cost_estimator.estimate_join(
                        current_plan, table_plan, JoinMethod.HASH_JOIN
                    )
                    if cost < best_cost:
                        best_cost = cost
                        best_next = table
                        best_plan = table_plan
            
            if best_next is None:
                # 选择第一个表
                best_next = list(remaining)[0]
                best_plan = PhysicalPlan(
                    operation=f"scan {best_next}",
                    cost=self.cost_estimator.estimate_scan(self.stats[best_next]),
                    rows=self.stats[best_next].n_rows
                )
            
            if current_plan is None:
                current_plan = best_plan
            else:
                current_plan = PhysicalPlan(
                    operation="hash_join",
                    cost=best_cost,
                    rows=current_plan.rows * best_plan.rows * 0.1,
                    children=[current_plan, best_plan],
                    join_method=JoinMethod.HASH_JOIN
                )
            
            current_table = best_next
            remaining.remove(best_next)
        
        return current_plan
    
    def _estimate_selectivity(self, conditions: List[str]) -> float:
        """估算条件选择率（简化）"""
        if not conditions:
            return 1.0
        
        # 简化：每个条件减少10%
        return max(0.01, 1.0 - len(conditions) * 0.1)
    
    def _can_use_index(self, index: IndexInfo, conditions: List[str]) -> bool:
        """检查是否可以使用索引"""
        # 简化：检查条件是否涉及索引列
        for cond in conditions:
            for col in index.columns:
                if col in cond.lower():
                    return True
        return False


class SimpleSQLParser:
    """
    简化SQL解析器
    
    支持：SELECT ... FROM ... WHERE ... JOIN ...
    """
    
    def __init__(self):
        self.keywords = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR', 'AS'}
    
    def parse(self, sql: str) -> Dict:
        """
        解析SQL
        
        返回:
            {'tables': [...], 'columns': [...], 'conditions': [...], 'joins': [...]}
        """
        sql_upper = sql.upper()
        
        # 提取SELECT子句
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper, re.IGNORECASE)
        columns = []
        if select_match:
            cols = select_match.group(1)
            columns = [c.strip() for c in cols.split(',')]
            columns = [c for c in columns if c != '*']
        
        # 提取FROM子句
        from_match = re.search(r'FROM\s+(\w+)', sql_upper, re.IGNORECASE)
        tables = []
        if from_match:
            tables.append(from_match.group(1))
        
        # 提取JOIN
        join_pattern = r'JOIN\s+(\w+)'
        for join_match in re.finditer(join_pattern, sql_upper, re.IGNORECASE):
            tables.append(join_match.group(1))
        
        # 提取WHERE条件
        where_match = re.search(r'WHERE\s+(.*?)(?:JOIN|ORDER|GROUP|LIMIT|$)', sql, re.IGNORECASE)
        conditions = []
        if where_match:
            where_clause = where_match.group(1).strip()
            conditions = self._split_conditions(where_clause)
        
        # 提取JOIN条件
        join_conditions = []
        join_pattern = r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        for match in re.finditer(join_pattern, sql):
            join_conditions.append((match.group(1), match.group(3)))
        
        return {
            'columns': columns,
            'tables': tables,
            'conditions': conditions,
            'join_conditions': join_conditions
        }
    
    def _split_conditions(self, where_clause: str) -> List[str]:
        """分割WHERE条件"""
        # 简化：用AND分割
        conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
        return [c.strip() for c in conditions if c.strip()]


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("查询规划器测试")
    print("=" * 50)
    
    # 创建测试统计信息
    stats = {
        'orders': TableStats(
            table_name='orders',
            n_rows=1000000,
            page_count=10000,
            column_stats={
                'order_id': ColumnStats('order_id', 1000000),
                'customer_id': ColumnStats('customer_id', 10000),
                'order_date': ColumnStats('order_date', 365)
            }
        ),
        'customers': TableStats(
            table_name='customers',
            n_rows=10000,
            page_count=100,
            column_stats={
                'customer_id': ColumnStats('customer_id', 10000),
                'name': ColumnStats('name', 10000),
                'segment': ColumnStats('segment', 5)
            }
        ),
        'order_items': TableStats(
            table_name='order_items',
            n_rows=5000000,
            page_count=50000,
            column_stats={
                'order_id': ColumnStats('order_id', 1000000),
                'product_id': ColumnStats('product_id', 50000)
            }
        )
    }
    
    # 创建索引信息
    indexes = {
        'orders': [
            IndexInfo('idx_orders_cust', 'orders', ['customer_id']),
            IndexInfo('pk_orders', 'orders', ['order_id'], unique=True)
        ],
        'customers': [
            IndexInfo('pk_customers', 'customers', ['customer_id'], unique=True)
        ],
        'order_items': [
            IndexInfo('idx_items_order', 'order_items', ['order_id'])
        ]
    }
    
    # 创建查询规划器
    planner = QueryPlanner(stats, indexes)
    
    # 测试SQL解析
    print("\n--- SQL解析测试 ---")
    
    parser = SimpleSQLParser()
    
    sql1 = "SELECT * FROM orders WHERE customer_id = 123"
    parsed1 = parser.parse(sql1)
    print(f"SQL: {sql1}")
    print(f"解析结果: {parsed1}")
    
    sql2 = "SELECT o.order_id, c.name FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.segment = 'VIP'"
    parsed2 = parser.parse(sql2)
    print(f"\nSQL: {sql2}")
    print(f"解析结果: {parsed2}")
    
    # 测试单表查询规划
    print("\n--- 单表查询规划 ---")
    
    plan1 = planner.create_simple_plan('orders', ['customer_id = 123'])
    print(f"查询: SELECT * FROM orders WHERE customer_id = 123")
    print(plan1.print_plan())
    
    # 测试连接查询规划
    print("\n--- 两表连接规划 ---")
    
    plan2 = planner.create_join_plan(
        ['orders', 'customers'],
        [('orders', 'customers')]
    )
    print(f"查询: SELECT * FROM orders o JOIN customers c ON o.customer_id = c.customer_id")
    print(plan2.print_plan())
    
    # 测试三表连接规划
    print("\n--- 三表连接规划 ---")
    
    plan3 = planner.create_join_plan(
        ['order_items', 'orders', 'customers'],
        [('order_items', 'orders'), ('orders', 'customers')]
    )
    print(f"查询: 多表JOIN")
    print(plan3.print_plan())
    
    # 代价对比
    print("\n--- 代价分析 ---")
    
    print(f"全表扫描 orders: {planner.cost_estimator.estimate_scan(stats['orders']):.2f}")
    print(f"索引扫描 orders (customer_id): {planner.cost_estimator.estimate_index_scan(indexes['orders'][0], 0.01, stats['orders']):.2f}")
    print(f"orders JOIN customers (最优): {plan2.cost:.2f}")
    
    # 模拟不同的连接顺序
    print("\n--- 连接顺序影响 ---")
    
    plan_direct = planner._create_two_table_plan('orders', 'customers', [])
    plan_reversed = planner._create_two_table_plan('customers', 'orders', [])
    
    print(f"orders -> customers: {plan_direct.cost:.2f}")
    print(f"customers -> orders: {plan_reversed.cost:.2f}")

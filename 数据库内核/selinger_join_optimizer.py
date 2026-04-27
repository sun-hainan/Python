# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / selinger_join_optimizer

本文件实现 selinger_join_optimizer 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional
from itertools import combinations

# 表信息
class Table:
    def __init__(self, name: str, num_rows: int, num_pages: int):
        self.name = name          # 表名
        self.num_rows = num_rows  # 行数
        self.num_pages = num_pages  # 页数
    
    def __repr__(self):
        return f"{self.name}(rows={self.num_rows}, pages={self.num_pages})"


class JoinState:
    """Join状态：记录当前已连接的表集合及最优计划"""
    def __init__(self, tables: set, cost: float, plan: 'JoinNode'):
        self.tables = tables          # 已连接的表集合
        self.cost = cost              # 当前最小代价
        self.plan = plan              # 最优计划
        self.build_side = None        # build侧（内表）
        self.probe_side = None        # probe侧（外表）
    
    def __repr__(self):
        return f"JoinState({self.tables}, cost={self.cost:.2f})"


class JoinNode:
    """Join执行计划节点"""
    def __init__(self, left, right, join_type: str):
        self.left = left      # 左子节点（表或JoinNode）
        self.right = right    # 右子节点
        self.join_type = join_type  # join类型：nested_loop/hash_merge
        self.build_side = "left"    # 默认左表为build
        self.cost = 0.0       # 代价
    
    def __repr__(self):
        return f"Join({self.left}, {self.right})"


def compute_table_size(table: Table, selectivity: float = 1.0) -> int:
    """计算表的大小（估计行数）"""
    return int(table.num_rows * selectivity)


def estimate_join_cost(left: Table, right: Table, 
                        join_type: str, selectivity: float = 0.1) -> float:
    """
    估算两表Join的代价
    selectivity: 连接条件的选择率
    """
    if join_type == "nested_loop":
        # 嵌套循环：外表全扫描 + 内表重复扫描
        return left.num_pages + left.num_rows * right.num_pages * selectivity
    
    elif join_type == "hash":
        # Hash Join: 扫描两表 + hash计算
        smaller = min(left.num_pages, right.num_pages)
        larger = max(left.num_pages, right.num_pages)
        return larger + smaller * 2
    
    elif join_type == "sort_merge":
        # Sort-Merge: 排序 + 归并
        return (left.num_pages * 2 + right.num_pages * 2 + 
                (left.num_pages + right.num_pages))
    
    return float('inf')


def find_best_build_side(left: Table, right: Table, join_type: str) -> str:
    """
    确定Build侧和Probe侧
    Build侧应该选择较小的表，以便构建hash表
    """
    if join_type != "hash":
        return "left"
    return "left" if left.num_rows <= right.num_rows else "right"


class SelingerOptimizer:
    """
    Selinger风格的Join重排优化器
    使用动态规划寻找最优Join顺序
    """
    
    def __init__(self, tables: List[Table], join_predicates: Dict[Tuple[str,str], float]):
        self.tables = tables                      # 所有要连接的表
        self.join_predicates = join_predicates     # 表间的连接谓词及选择性
        self.dp_table: Dict[frozenset, JoinState] = {}  # 动态规划表
        self.MEMORY_PAGES = 1000                  # 可用的内存页数（用于Hash Join）
    
    def optimize(self) -> JoinNode:
        """主入口：计算最优Join顺序"""
        return self._dp_build()
    
    def _dp_build(self) -> JoinNode:
        """动态规划构建最优计划"""
        n = len(self.tables)
        
        # 初始化：单个表作为叶子节点
        for table in self.tables:
            state = JoinState(
                tables={table.name},
                cost=0.0,  # 扫描单表代价暂不计入
                plan=table
            )
            self.dp_table[frozenset({table.name})] = state
        
        # 逐步构建更大的连接集合
        for size in range(2, n + 1):
            for subset in self._generate_subsets(size):
                best_state = None
                
                # 枚举所有可能的划分方式
                for left_set, right_set in self._split_subset(subset):
                    if not left_set or not right_set:
                        continue
                    
                    # 获取左右子集的最优状态
                    left_state = self.dp_table.get(left_set)
                    right_state = self.dp_table.get(right_set)
                    
                    if not left_state or not right_state:
                        continue
                    
                    # 尝试不同的Join类型
                    for join_type in ["hash", "nested_loop"]:
                        cost = self._compute_join_cost(
                            left_set, right_set, left_state, right_state, join_type
                        )
                        
                        if best_state is None or cost < best_state.cost:
                            # 构造新的Join节点
                            join_node = JoinNode(left_state.plan, right_state.plan, join_type)
                            join_node.build_side = self._choose_build_side(
                                left_set, right_set, join_type
                            )
                            join_node.cost = cost
                            
                            best_state = JoinState(
                                tables=subset,
                                cost=cost,
                                plan=join_node
                            )
                
                if best_state:
                    self.dp_table[subset] = best_state
        
        # 返回完整集合的最优计划
        all_tables = frozenset(t.name for t in self.tables)
        return self.dp_table[all_tables].plan
    
    def _generate_subsets(self, size: int) -> List[frozenset]:
        """生成指定大小的子集"""
        table_names = [t.name for t in self.tables]
        result = []
        
        for combo in combinations(table_names, size):
            result.append(frozenset(combo))
        
        return result
    
    def _split_subset(self, subset: frozenset) -> List[Tuple[frozenset, frozenset]]:
        """将一个集合划分为两个非空子集"""
        result = []
        tables = list(subset)
        n = len(tables)
        
        # 枚举所有划分（不包括空集）
        for i in range(1, n):
            left = frozenset(tables[:i])
            right = frozenset(tables[i:])
            result.append((left, right))
        
        return result
    
    def _compute_join_cost(self, left_set, right_set, 
                          left_state, right_state, join_type) -> float:
        """计算Join的代价"""
        # 获取左右集合中的表对象
        left_tables = [t for t in self.tables if t.name in left_set]
        right_tables = [t for t in self.tables if t.name in right_set]
        
        # 计算子树的代价
        subtree_cost = left_state.cost + right_state.cost
        
        # 计算Join本身的代价
        for lt in left_tables:
            for rt in right_tables:
                pred_key = (lt.name, rt.name)
                selectivity = self.join_predicates.get(pred_key, 0.1)
                
                join_cost = estimate_join_cost(lt, rt, join_type, selectivity)
                subtree_cost += join_cost
        
        return subtree_cost
    
    def _choose_build_side(self, left_set, right_set, join_type: str) -> str:
        """选择Build侧"""
        if join_type != "hash":
            return "left"
        
        # 计算左右两侧的总行数
        left_rows = sum(t.num_rows for t in self.tables if t.name in left_set)
        right_rows = sum(t.num_rows for t in self.tables if t.name in right_set)
        
        return "left" if left_rows <= right_rows else "right"


def print_plan(plan: JoinNode, indent: int = 0):
    """打印执行计划"""
    prefix = "  " * indent
    
    if isinstance(plan, Table):
        print(f"{prefix}Scan {plan.name}")
        return
    
    if isinstance(plan, JoinNode):
        print(f"{prefix}Join ({plan.join_type}):")
        print_plan(plan.left, indent + 1)
        print_plan(plan.right, indent + 1)


if __name__ == "__main__":
    # 定义测试表
    tables = [
        Table("orders", 100000, 5000),
        Table("customers", 50000, 2000),
        Table("order_items", 500000, 15000),
        Table("products", 20000, 1000)
    ]
    
    # 定义连接谓词及选择性
    join_preds = {
        ("orders", "customers"): 0.001,      # orders.customer_id = customers.id
        ("orders", "order_items"): 0.01,      # orders.id = order_items.order_id
        ("order_items", "products"): 0.05,   # order_items.product_id = products.id
        ("customers", "order_items"): 0.02,  # 间接关联
        ("customers", "products"): 0.01
    }
    
    print("=" * 60)
    print("Selinger Join重排优化器")
    print("=" * 60)
    print("\n输入表:")
    for t in tables:
        print(f"  {t}")
    
    print("\n连接谓词及选择性:")
    for (t1, t2), sel in join_preds.items():
        print(f"  {t1} ⋈ {t2}: selectivity={sel}")
    
    # 执行优化
    optimizer = SelingerOptimizer(tables, join_preds)
    optimal_plan = optimizer.optimize()
    
    print("\n最优执行计划:")
    print_plan(optimal_plan)

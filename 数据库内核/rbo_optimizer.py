# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / rbo_optimizer

本文件实现 rbo_optimizer 相关的算法功能。
"""

from typing import List, Dict, Tuple, Any
from enum import IntEnum

# 规则优先级枚举（数字越小优先级越高）
class RulePriority(IntEnum):
    PREDICATE_PUSH_DOWN = 10    # 谓词下推
    PROJECTION_PRUNING = 20     # 投影剪裁
    INDEX_SCAN = 30             # 索引扫描
    JOIN_REORDER = 40           # Join重排
    MATERIALIZE = 50            # 物化中间结果


class RelNode:
    """关系代数节点"""
    def __init__(self, node_type: str):
        self.node_type = node_type  # 类型：scan/join/project/filter
        self.children = []           # 子节点
        self.props = {}              # 节点属性
    
    def __repr__(self):
        return f"RelNode({self.node_type})"


class RBOptimizer:
    """基于规则的优化器"""
    
    def __init__(self):
        self.rules = []  # 规则列表
    
    def add_rule(self, rule_func, priority: RulePriority, rule_name: str):
        """添加优化规则"""
        self.rules.append((priority, rule_func, rule_name))
        self.rules.sort(key=lambda x: x[0])  # 按优先级排序
    
    def optimize(self, plan: RelNode) -> RelNode:
        """对执行计划应用所有规则"""
        current = plan
        for priority, rule_func, rule_name in self.rules:
            new_plan = rule_func(current)
            if new_plan:
                print(f"[RBO] 应用规则: {rule_name} (优先级={priority})")
                current = new_plan
        return current


def rule_predicate_push_down(node: RelNode) -> RelNode:
    """
    规则1：谓词下推
    将Filter操作尽可能下推到叶子节点，减少中间结果大小
    """
    if node.node_type == "filter":
        # 获取过滤条件
        predicate = node.props.get("predicate", {})
        filter_table = predicate.get("table", None)
        
        # 尝试将谓词下推到子节点
        for i, child in enumerate(node.children):
            if child.node_type == "scan" and filter_table:
                if child.props.get("table_name") == filter_table:
                    # 将谓词合并到scan节点
                    existing_pred = child.props.get("predicate", {})
                    child.props["predicate"] = {**existing_pred, **predicate}
                    # 用scan节点替换filter节点
                    return child
    
    # 递归处理子节点
    for i, child in enumerate(node.children):
        new_child = rule_predicate_push_down(child)
        if new_child:
            node.children[i] = new_child
    
    return node


def rule_projection_pruning(node: RelNode) -> RelNode:
    """
    规则2：投影剪裁
    只保留查询中需要的列，减少I/O和内存开销
    """
    required_columns = set()
    
    def collect_columns(n: RelNode):
        if n.node_type == "project":
            required_columns.update(n.props.get("columns", []))
        for child in n.children:
            collect_columns(child)
    
    collect_columns(node)
    
    # 将列信息向下传递，让scan节点只读取需要的列
    def prune_columns(n: RelNode, cols: set):
        if n.node_type == "scan":
            n.props["columns"] = cols if cols else n.props.get("columns", set())
        for child in n.children:
            prune_columns(child, cols)
    
    prune_columns(node, required_columns)
    return node


def rule_index_scan_selection(node: RelNode) -> RelNode:
    """
    规则3：选择索引扫描
    当scan节点有过滤条件且存在可用索引时，选择索引扫描
    """
    if node.node_type == "scan":
        predicate = node.props.get("predicate", {})
        available_indexes = node.props.get("indexes", [])
        
        if predicate and available_indexes:
            # 选择最优索引（简化：选择第一个匹配列的索引）
            for idx in available_indexes:
                idx_columns = idx.get("columns", [])
                for pred_col in predicate.keys():
                    if pred_col in idx_columns:
                        node.props["scan_method"] = "index_scan"
                        node.props["used_index"] = idx["name"]
                        print(f"  → 选择索引扫描: {idx['name']}")
                        return node
    
    # 递归处理子节点
    for i, child in enumerate(node.children):
        node.children[i] = rule_index_scan_selection(child)
    
    return node


def rule_join_reorder(node: RelNode) -> RelNode:
    """
    规则4：Join重排
    根据表大小调整join顺序，小表先join
    """
    if node.node_type == "join":
        left, right = node.children
        
        left_size = left.props.get("est_rows", float('inf'))
        right_size = right.props.get("est_rows", float('inf'))
        
        # 如果左表大于右表，交换顺序（让小表在外层）
        if left_size > right_size:
            node.children = [right, left]
            node.props["swapped"] = True
            print(f"  → Join重排: 交换顺序（左:{left_size} vs 右:{right_size}）")
    
    # 递归处理子节点
    for i, child in enumerate(node.children):
        node.children[i] = rule_join_reorder(child)
    
    return node


def build_sample_plan() -> RelNode:
    """构建示例查询计划"""
    # SELECT * FROM orders o 
    # JOIN customers c ON o.customer_id = c.id 
    # WHERE o.amount > 1000 AND c.region = 'north'
    
    # 叶子节点：scan orders
    scan_orders = RelNode("scan")
    scan_orders.props = {
        "table_name": "orders",
        "predicate": {"amount": (">", 1000)},
        "indexes": [
            {"name": "idx_orders_amount", "columns": ["amount"]},
            {"name": "idx_orders_customer", "columns": ["customer_id"]}
        ],
        "est_rows": 100000,
        "columns": ["id", "customer_id", "amount", "order_date"]
    }
    
    # 叶子节点：scan customers
    scan_customers = RelNode("scan")
    scan_customers.props = {
        "table_name": "customers",
        "predicate": {"region": ("=", "north")},
        "indexes": [
            {"name": "idx_customers_region", "columns": ["region"]}
        ],
        "est_rows": 50000,
        "columns": ["id", "name", "region"]
    }
    
    # Join节点
    join_node = RelNode("join")
    join_node.props = {"type": "inner", "condition": "customer_id=id"}
    join_node.children = [scan_orders, scan_customers]
    
    # Filter节点（顶端）
    filter_node = RelNode("filter")
    filter_node.props = {"predicate": {}}
    filter_node.children = [join_node]
    
    # Project节点
    project_node = RelNode("project")
    project_node.props = {"columns": ["id", "customer_id", "amount", "name", "region"]}
    project_node.children = [filter_node]
    
    return project_node


if __name__ == "__main__":
    # 构建查询计划
    plan = build_sample_plan()
    
    # 创建RBO优化器
    optimizer = RBOptimizer()
    optimizer.add_rule(rule_predicate_push_down, RulePriority.PREDICATE_PUSH_DOWN, "谓词下推")
    optimizer.add_rule(rule_projection_pruning, RulePriority.PROJECTION_PRUNING, "投影剪裁")
    optimizer.add_rule(rule_index_scan_selection, RulePriority.INDEX_SCAN, "索引扫描选择")
    optimizer.add_rule(rule_join_reorder, RulePriority.JOIN_REORDER, "Join重排")
    
    print("=" * 60)
    print("基于规则的优化器（RBO）演示")
    print("=" * 60)
    print("\n原始计划:")
    print(plan)
    
    print("\n开始优化...")
    print("-" * 60)
    
    optimized_plan = optimizer.optimize(plan)
    
    print("-" * 60)
    print("\n优化完成")
    print(f"最终计划类型: {optimized_plan.node_type}")

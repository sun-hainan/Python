# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / bdd

本文件实现 bdd 相关的算法功能。
"""

import numpy as np
from collections import defaultdict
import functools


class BDDNode:
    """
    BDD节点类
    
    属性:
        var: 变量索引（叶子节点为-1）
        low: 变量为0时的子节点ID
        high: 变量为1时的子节点ID
        terminal: 是否为叶子节点
        value: 叶子节点的值（True=1, False=0）
    """
    
    _id_counter = 0
    
    def __init__(self, var=-1, low=None, high=None, terminal=False, value=False):
        self.id = BDDNode._id_counter
        BDDNode._id_counter += 1
        
        self.var = var          # 变量索引
        self.low = low          # low分支（0分支）
        self.high = high        # high分支（1分支）
        self.terminal = terminal  # 是否为叶子节点
        self.value = value      # 叶子节点的值
    
    def __repr__(self):
        if self.terminal:
            return f"Node({self.id}, terminal={self.value})"
        return f"Node({self.id}, var=x{self.var}, low={self.low}, high={self.high})"


class BDD:
    """
    二叉决策图（BDD）类
    
    管理BDD的构建和运算
    使用唯一表（Unique Table）确保共享
    """
    
    def __init__(self, num_vars):
        """
        初始化BDD
        
        参数:
            num_vars: 变量数量
        """
        self.num_vars = num_vars
        self.unique_table = {}  # (var, low, high) -> node_id
        self.nodes = {}        # node_id -> node
        
        # 创建终端节点
        self.terminal_true = self._make_terminal(True)
        self.terminal_false = self._make_terminal(False)
        
        # 缓存已计算的结果
        self.apply_cache = {}
        self.restrict_cache = {}
    
    def _make_terminal(self, value):
        """创建终端节点"""
        node = BDDNode(var=-1, terminal=True, value=value)
        self.nodes[node.id] = node
        return node.id
    
    def _make_node(self, var, low, high):
        """
        创建或获取已存在的节点（唯一性）
        
        参数:
            var: 变量索引
            low: low分支
            high: high分支
        
        返回:
            节点ID
        """
        # 简化规则：low == high 时返回该分支
        if low == high:
            return low
        
        key = (var, low, high)
        if key in self.unique_table:
            return self.unique_table[key]
        
        node = BDDNode(var=var, low=low, high=high)
        self.nodes[node.id] = node
        self.unique_table[key] = node.id
        
        return node.id
    
    def _apply(self, op, u, v):
        """
        递归应用二元操作
        
        参数:
            op: 操作符 ('and', 'or', 'xor', 'imp')
            u, v: 两个BDD的根节点ID
        
        返回:
            结果BDD的根节点ID
        """
        cache_key = (op, u, v)
        if cache_key in self.apply_cache:
            return self.apply_cache[cache_key]
        
        # 获取节点
        node_u = self.nodes[u]
        node_v = self.nodes[v]
        
        # 终端情况
        if node_u.terminal and node_v.terminal:
            if op == 'and':
                result = self.terminal_true.id if (node_u.value and node_v.value) else self.terminal_false.id
            elif op == 'or':
                result = self.terminal_true.id if (node_u.value or node_v.value) else self.terminal_false.id
            elif op == 'xor':
                result = self.terminal_true.id if (node_u.value != node_v.value) else self.terminal_false.id
            elif op == 'imp':
                result = self.terminal_true.id if (not node_u.value or node_v.value) else self.terminal_false.id
            else:
                raise ValueError(f"Unknown op: {op}")
            self.apply_cache[cache_key] = result
            return result
        
        # 递归情况
        if node_u.terminal:
            # u是终端，根据v的结构决定
            if node_u.value:  # u = True
                if op == 'and':
                    result = v
                elif op == 'or':
                    result = self.terminal_true.id
                elif op == 'xor':
                    result = self._apply_not(v)
                elif op == 'imp':
                    result = self.terminal_true.id
            else:  # u = False
                if op == 'and':
                    result = self.terminal_false.id
                elif op == 'or':
                    result = v
                elif op == 'xor':
                    result = v
                elif op == 'imp':
                    result = self.terminal_true.id
        elif node_v.terminal:
            # v是终端
            if node_v.value:  # v = True
                if op == 'and':
                    result = u
                elif op == 'or':
                    result = self.terminal_true.id
                elif op == 'xor':
                    result = self._apply_not(u)
                elif op == 'imp':
                    result = self.terminal_true.id
            else:  # v = False
                if op == 'and':
                    result = self.terminal_false.id
                elif op == 'or':
                    result = u
                elif op == 'xor':
                    result = u
                elif op == 'imp':
                    result = self._apply_not(u)
        else:
            # 两个都是非终端节点
            # 找最小的变量
            if node_u.var < node_v.var:
                var = node_u.var
                low = self._apply(op, node_u.low, v)
                high = self._apply(op, node_u.high, v)
            elif node_u.var > node_v.var:
                var = node_v.var
                low = self._apply(op, u, node_v.low)
                high = self._apply(op, u, node_v.high)
            else:  # node_u.var == node_v.var
                var = node_u.var
                low = self._apply(op, node_u.low, node_v.low)
                high = self._apply(op, node_u.high, node_v.high)
            
            result = self._make_node(var, low, high)
        
        self.apply_cache[cache_key] = result
        return result
    
    def _apply_not(self, u):
        """NOT操作"""
        node = self.nodes[u]
        
        if node.terminal:
            return self.terminal_true.id if not node.value else self.terminal_false.id
        
        # NOT操作会交换low和high分支
        low = self._apply_not(node.low)
        high = self._apply_not(node.high)
        
        return self._make_node(node.var, low, high)
    
    def _restrict(self, u, var, value):
        """
        RESTRICT操作：将变量var限制为value
        
        参数:
            u: BDD根节点
            var: 变量索引
            value: 限制值（True/False）
        
        返回:
            限制后的BDD根节点
        """
        cache_key = (u, var, value)
        if cache_key in self.restrict_cache:
            return self.restrict_cache[cache_key]
        
        node = self.nodes[u]
        
        if node.terminal:
            result = u
        elif node.var < var:
            # 当前变量小于限制变量，递归向下
            low = self._restrict(node.low, var, value)
            high = self._restrict(node.high, var, value)
            result = self._make_node(node.var, low, high)
        elif node.var == var:
            # 当前变量就是限制变量
            if value:
                result = node.high
            else:
                result = node.low
        else:  # node.var > var
            result = u
        
        self.restrict_cache[cache_key] = result
        return result
    
    def var(self, i):
        """
        创建变量x_i的BDD（只取该变量为真）
        
        参数:
            i: 变量索引
        
        返回:
            变量BDD的根节点ID
        """
        # 递归构建变量
        def build_var(i):
            if i == self.num_vars:
                return self.terminal_true.id
            
            low = self.terminal_false.id  # x_i = 0 -> False
            high = build_var(i + 1)       # x_i = 1 -> 继续
            return self._make_node(i, low, high)
        
        return build_var(i)
    
    def and_(self, u, v):
        """AND操作"""
        return self._apply('and', u, v)
    
    def or_(self, u, v):
        """OR操作"""
        return self._apply('or', u, v)
    
    def xor(self, u, v):
        """XOR操作"""
        return self._apply('xor', u, v)
    
    def not_(self, u):
        """NOT操作"""
        return self._apply_not(u)
    
    def imp(self, u, v):
        """蕴含操作 u -> v"""
        return self._apply('imp', u, v)
    
    def restrict(self, u, var, value):
        """限制变量"""
        return self._restrict(u, var, value)
    
    def evaluate(self, u, assignment):
        """
        评估BDD在给定赋值下的值
        
        参数:
            u: BDD根节点
            assignment: 变量赋值列表 [x0, x1, x2, ...]
        
        返回:
            BDD在赋值下的值
        """
        node = self.nodes[u]
        
        while not node.terminal:
            if assignment[node.var]:
                node = self.nodes[node.high]
            else:
                node = self.nodes[node.low]
        
        return node.value
    
    def to_graphviz(self, u):
        """
        转换为Graphviz格式（用于可视化）
        """
        lines = ["digraph BDD {"]
        
        def visit(node_id):
            node = self.nodes[node_id]
            if node.terminal:
                label = "True" if node.value else "False"
                lines.append(f'  n{node_id} [label="{label}", shape=box];')
            else:
                lines.append(f'  n{node_id} [label="x{node.var}"];')
                if node.low is not None:
                    lines.append(f'  n{node_id} -> n{node.low} [style=dashed, label=0];')
                    visit(node.low)
                if node.high is not None:
                    lines.append(f'  n{node_id} -> n{node.high} [label=1];')
                    visit(node.high)
        
        visit(u)
        lines.append("}")
        return "\n".join(lines)


def run_demo():
    """运行BDD演示"""
    print("=" * 60)
    print("BDD（二叉决策图）构建与基本运算")
    print("=" * 60)
    
    # 创建BDD实例（3个变量）
    bdd = BDD(num_vars=3)
    
    # 创建变量
    x0 = bdd.var(0)
    x1 = bdd.var(1)
    x2 = bdd.var(2)
    
    print("\n[基本操作]")
    
    # AND: x0 AND x1
    f_and = bdd.and_(x0, x1)
    print(f"  x0 AND x1:")
    print(f"    评估 [0,0,0] = {bdd.evaluate(f_and, [0,0,0])}")
    print(f"    评估 [1,0,0] = {bdd.evaluate(f_and, [1,0,0])}")
    print(f"    评估 [1,1,0] = {bdd.evaluate(f_and, [1,1,0])}")
    
    # OR: x0 OR x1
    f_or = bdd.or_(x0, x1)
    print(f"  x0 OR x1:")
    print(f"    评估 [0,0,0] = {bdd.or_(x0, x1) and False or bdd.evaluate(f_or, [0,0,0])}")
    print(f"    评估 [0,1,0] = {bdd.evaluate(f_or, [0,1,0])}")
    print(f"    评估 [1,0,0] = {bdd.evaluate(f_or, [1,0,0])}")
    
    # XOR: x0 XOR x1
    f_xor = bdd.xor(x0, x1)
    print(f"  x0 XOR x1:")
    print(f"    评估 [0,0,0] = {bdd.evaluate(f_xor, [0,0,0])}")
    print(f"    评估 [0,1,0] = {bdd.evaluate(f_xor, [0,1,0])}")
    print(f"    评估 [1,0,0] = {bdd.evaluate(f_xor, [1,0,0])}")
    print(f"    评估 [1,1,0] = {bdd.evaluate(f_xor, [1,1,0])}")
    
    # NOT
    f_not = bdd.not_(x0)
    print(f"  NOT x0:")
    print(f"    评估 [0,0,0] = {bdd.evaluate(f_not, [0,0,0])}")
    print(f"    评估 [1,0,0] = {bdd.evaluate(f_not, [1,0,0])}")
    
    # 复合表达式: (x0 AND x1) OR (NOT x0 AND x2)
    f_complex = bdd.or_(bdd.and_(x0, x1), bdd.and_(bdd.not_(x0), x2))
    print(f"\n[复合表达式] (x0 AND x1) OR (NOT x0 AND x2):")
    for assignment in [[0,0,0], [0,0,1], [1,0,0], [1,1,0], [1,1,1]]:
        result = bdd.evaluate(f_complex, assignment)
        print(f"    {assignment} = {result}")
    
    # RESTRICT操作
    print(f"\n[RESTRICT] 限制 x0 = 1:")
    f_restricted = bdd.restrict(f_complex, 0, True)
    for assignment in [[0,0,0], [0,1,0], [1,0,1]]:
        # 重新评估，因为x0被固定
        assignment_with_x0 = [1] + assignment[1:]
        result = bdd.evaluate(f_restricted, assignment)
        print(f"    x0=1, x1={assignment[1]}, x2={assignment[2]} -> {result}")
    
    # 蕴含: x0 -> x1
    f_imp = bdd.imp(x0, x1)
    print(f"\n[蕴含] x0 -> x1:")
    for assignment in [[0,0,0], [0,1,0], [1,0,0], [1,1,0]]:
        result = bdd.evaluate(f_imp, assignment)
        print(f"    {assignment} = {result}")
    
    print("\n" + "=" * 60)
    print("BDD核心概念:")
    print("  1. 二叉决策图: 每个内部节点测试一个变量")
    print("  2. 路径从根到叶子表示一个完整赋值")
    print("  3. 唯一表: 相同子结构共享节点，减少内存")
    print("  4. 简化规则: low==high时返回该分支（消除冗余）")
    print("  5. 有序: 变量按固定顺序测试（OBDD的要求）")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()

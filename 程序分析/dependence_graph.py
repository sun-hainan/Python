# -*- coding: utf-8 -*-
"""
程序依赖图（Dependence Graph）
功能：表示程序中语句间的控制依赖和数据依赖

依赖类型：
1. 控制依赖：语句的执行受某个条件的控制
2. 数据依赖：语句使用了先前语句定义的值

依赖关系：
- 真依赖(RAW)：Read after Write
- 反依赖(WAR)：Write after Read
- 输出依赖(WAW)：Write after Write

作者：Dependence Graph Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class DependenceEdge:
    """依赖边"""
    def __init__(self, src: int, dst: int, dep_type: str, var: str = None):
        self.src = src  # 源语句ID
        self.dst = dst  # 目标语句ID
        self.type = dep_type  # 'flow', 'anti', 'output', 'control'
        self.var = var  # 涉及的变量（数据依赖时）

    def __repr__(self):
        return f"{self.src} →{self.type} {self.dst}"


class DependenceGraph:
    """
    程序依赖图（PDG）
    """

    def __init__(self):
        self.nodes: List[Dict] = []  # 语句列表
        self.edges: List[DependenceEdge] = []
        self.preds: Dict[int, List[DependenceEdge]] = defaultdict(list)
        self.succs: Dict[int, List[DependenceEdge]] = defaultdict(list)

    def add_node(self, stmt: Dict):
        """添加节点"""
        self.nodes.append(stmt)

    def add_edge(self, src: int, dst: int, dep_type: str, var: str = None):
        """添加依赖边"""
        edge = DependenceEdge(src, dst, dep_type, var)
        self.edges.append(edge)
        self.succs[src].append(edge)
        self.preds[dst].append(edge)

    def get_pred_edges(self, node_id: int) -> List[DependenceEdge]:
        """获取前驱依赖边"""
        return self.preds.get(node_id, [])

    def get_succ_edges(self, node_id: int) -> List[DependenceEdge]:
        """获取后继依赖边"""
        return self.succs.get(node_id, [])

    def has_path(self, src: int, dst: int) -> bool:
        """检查是否存在从src到dst的路径"""
        visited = set()
        worklist = [src]
        
        while worklist:
            current = worklist.pop()
            if current == dst:
                return True
            if current in visited:
                continue
            visited.add(current)
            for edge in self.succs.get(current, []):
                worklist.append(edge.dst)
        
        return False


class DependenceAnalyzer:
    """
    依赖分析器
    """

    def __init__(self):
        self.graph = DependenceGraph()

    def analyze(self, stmts: List[Dict]) -> DependenceGraph:
        """
        分析程序语句的依赖关系
        """
        self.graph = DependenceGraph()
        
        for stmt in stmts:
            self.graph.add_node(stmt)
        
        n = len(stmts)
        
        for i in range(n):
            for j in range(i + 1, n):
                self._check_dependency(i, stmts[i], j, stmts[j])
        
        return self.graph

    def _check_dependency(self, i: int, stmt_i: Dict, j: int, stmt_j: Dict):
        """检查stmt_i和stmt_j之间的依赖"""
        # 提取定义和引用
        defs_i = self._extract_defs(stmt_i)
        uses_i = self._extract_uses(stmt_i)
        defs_j = self._extract_defs(stmt_j)
        uses_j = self._extract_uses(stmt_j)
        
        # 真依赖 (RAW): i定义，j使用
        for var in defs_i & uses_j:
            self.graph.add_edge(i, j, 'flow', var)
        
        # 反依赖 (WAR): i使用，j定义
        for var in uses_i & defs_j:
            self.graph.add_edge(i, j, 'anti', var)
        
        # 输出依赖 (WAW): i定义，j定义
        for var in defs_i & defs_j:
            self.graph.add_edge(i, j, 'output', var)
        
        # 控制依赖
        if self._is_control_stmt(stmt_i) and not self._is_control_stmt(stmt_j):
            self.graph.add_edge(i, j, 'control')

    def _extract_defs(self, stmt: Dict) -> Set[str]:
        """提取语句的定义"""
        if stmt.get('type') == 'assign':
            lhs = stmt.get('lhs')
            if lhs:
                return {lhs}
        return set()

    def _extract_uses(self, stmt: Dict) -> Set[str]:
        """提取语句的引用"""
        uses = set()
        self._collect_vars(stmt.get('rhs', {}), uses)
        self._collect_vars(stmt.get('cond', {}), uses)
        return uses

    def _collect_vars(self, expr, uses: Set[str]):
        """收集表达式中的变量"""
        if isinstance(expr, str) and expr.isidentifier():
            uses.add(expr)
        elif isinstance(expr, dict):
            for val in expr.values():
                self._collect_vars(val, uses)
        elif isinstance(expr, list):
            for item in expr:
                self._collect_vars(item, uses)

    def _is_control_stmt(self, stmt: Dict) -> bool:
        """判断是否为控制语句"""
        return stmt.get('type') in ('if', 'while', 'goto')


def example_simple_dep():
    """简单依赖分析"""
    analyzer = DependenceAnalyzer()
    
    stmts = [
        {'type': 'assign', 'lhs': 'x', 'rhs': 10},     # 0
        {'type': 'assign', 'lhs': 'y', 'rhs': 'x'},   # 1: RAW x, WAW x
        {'type': 'assign', 'lhs': 'z', 'rhs': 'y'},   # 2: RAW y, WAR x, WAW y
    ]
    
    graph = analyzer.analyze(stmts)
    
    print("依赖边:")
    for edge in graph.edges:
        print(f"  {edge}")


def example_loop_dep():
    """循环依赖分析"""
    analyzer = DependenceAnalyzer()
    
    # for i = 1 to n:
    #   A[i] = A[i-1] + 1  (语句0)
    stmts = [
        {'type': 'assign', 'lhs': 'A[i]', 'rhs': {'op': '+', 'left': 'A[i-1]', 'right': 1}},
    ]
    
    print("循环依赖分析需要考虑迭代间的依赖")


if __name__ == "__main__":
    print("=" * 50)
    print("程序依赖图 测试")
    print("=" * 50)
    
    example_simple_dep()
    print()
    example_loop_dep()

# -*- coding: utf-8 -*-
"""
指向分析（Points-to Analysis）
功能：分析指针变量指向哪些堆对象或栈变量

与别名分析的关系：
- 别名分析：判断两个指针是否可能指向同一对象
- 指向分析：具体列出指针可能指向的所有对象

算法分类：
1. 收集语义（Inclusion-based）：Andersen-style
2. 等价语义（Equivalence-based）：Steensgaard-style

作者：Points-to Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class HeapObject:
    """堆对象（抽象表示）"""
    def __init__(self, alloc_site: str, offset: int = 0):
        self.alloc_site = alloc_site  # 分配点
        self.offset = offset  # 字段偏移
    
    def __repr__(self):
        return f"heap_{self.alloc_site}"
    
    def __hash__(self):
        return hash((self.alloc_site, self.offset))
    
    def __eq__(self, other):
        return isinstance(other, HeapObject) and self.alloc_site == other.alloc_site


class Var:
    """变量"""
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name


class PointsToGraph:
    """指向图"""
    
    def __init__(self):
        # pts[v] = {v可能指向的对象集合}
        self.pts: Dict[Var, Set[HeapObject]] = defaultdict(set)
        # 所有变量
        self.vars: Set[Var] = set()

    def add_var(self, v: Var):
        self.vars.add(v)

    def add_points_to(self, v: Var, obj: HeapObject):
        self.pts[v].add(obj)

    def get_points_to(self, v: Var) -> Set[HeapObject]:
        return self.pts.get(v, set())

    def merge(self, other: 'PointsToGraph'):
        """合并两个指向图"""
        for v in other.vars:
            self.add_var(v)
            for obj in other.pts.get(v, set()):
                self.pts[v].add(obj)


class AndersenPointsTo:
    """
    Andersen-style指向分析
    
    约束规则：
    1. v = &o → pts(v) ⊇ {o}
    2. v = u → pts(v) ⊇ pts(u)
    3. v = *u → 对所有 o ∈ pts(u)，pts(v) ⊇ pts(o)
    4. *v = u → 对所有 o ∈ pts(v)，pts(o) ⊇ pts(u)
    """

    def __init__(self):
        self.graph = PointsToGraph()
        self.constraints: List[Tuple[str, str, str]] = []  # (lhs, op, rhs)

    def handle_addr(self, v: str, obj: str):
        """v = &obj"""
        self.constraints.append((v, 'addr', obj))

    def handle_copy(self, v: str, u: str):
        """v = u"""
        self.constraints.append((v, 'copy', u))

    def handle_load(self, v: str, u: str):
        """v = *u"""
        self.constraints.append((v, 'load', u))

    def handle_store(self, v: str, u: str):
        """*v = u"""
        self.constraints.append((v, 'store', u))

    def solve(self) -> PointsToGraph:
        """
        使用worklist算法求解
        
        Returns:
            最终的指向图
        """
        # 初始化
        for lhs, op, rhs in self.constraints:
            self.graph.add_var(Var(lhs))
            if op == 'addr':
                self.graph.add_points_to(Var(lhs), HeapObject(rhs))
        
        # Worklist
        worklist = deque(self.constraints)
        processed = set()
        
        while worklist:
            constraint = worklist.popleft()
            lhs, op, rhs = constraint
            
            if op == 'addr':
                new_objs = {HeapObject(rhs)}
            
            elif op == 'copy':
                old_size = len(self.graph.pts.get(Var(lhs), set()))
                self.graph.pts[Var(lhs)] |= self.graph.pts.get(Var(rhs), set())
                new_size = len(self.graph.pts[Var(lhs)])
                if new_size > old_size:
                    for c in self.constraints:
                        if c[1] == 'store' and c[2] == lhs:
                            worklist.append(c)
            
            elif op == 'load':
                # v = *u: pts(v) ⊇ pts(*u)
                for obj in self.graph.get_points_to(Var(rhs)):
                    if isinstance(obj, HeapObject):
                        self.graph.pts[Var(lhs)] |= self.graph.get_points_to(Var(obj.alloc_site))
            
            elif op == 'store':
                # *v = u: pts(*v) ⊇ pts(u)
                for obj in self.graph.get_points_to(Var(lhs)):
                    if isinstance(obj, HeapObject):
                        self.graph.pts[Var(obj.alloc_site)] |= self.graph.pts.get(Var(rhs), set())
        
        return self.graph


class DFSBasedPointsTo:
    """
    基于DFS的指向分析（简化版流敏感分析）
    
    对每个基本块计算IN和OUT状态
    """

    def __init__(self):
        self.blocks: List['BasicBlock'] = []

    def analyze(self, entry_block: 'BasicBlock') -> PointsToGraph:
        """流敏感分析"""
        worklist = deque([entry_block])
        analyzed: Set[str] = set()
        in_state: Dict[str, PointsToGraph] = {}
        
        while worklist:
            block = worklist.popleft()
            block_id = block.label
            
            # 计算IN状态 = 合并所有前驱的OUT
            if block.predecessors:
                in_graph = PointsToGraph()
                for pred in block.predecessors:
                    if pred.label in in_state:
                        in_graph.merge(in_state[pred.label])
                in_state[block_id] = in_graph
            else:
                in_state[block_id] = PointsToGraph()
            
            # 应用块内转换
            out_graph = self._transfer(in_state[block_id], block)
            
            # 若OUT改变，后继加入worklist
            if block_id not in analyzed or out_graph != self.graphs.get(block_id):
                self.graphs[block_id] = out_graph
                analyzed.add(block_id)
                for succ in block.successors:
                    worklist.append(succ)
        
        return self.graphs.get(entry_block.label, PointsToGraph())

    def _transfer(self, in_graph: PointsToGraph, block: 'BasicBlock') -> PointsToGraph:
        """应用转换"""
        out = PointsToGraph()
        out.merge(in_graph)
        # 简化：逐条语句更新out
        for stmt in block.stmts:
            # 应用语句效果
            pass
        return out


class BasicBlock:
    """基本块"""
    def __init__(self, label: str):
        self.label = label
        self.stmts: List = []
        self.predecessors: List['BasicBlock'] = []
        self.successors: List['BasicBlock'] = []


def example_simple_points_to():
    """简单指向分析"""
    analysis = AndersenPointsTo()
    
    # p = &a
    analysis.handle_addr('p', 'a')
    # q = &b
    analysis.handle_addr('q', 'b')
    # r = p  (r指向a)
    analysis.handle_copy('r', 'p')
    # q = r  (q和r都指向a,b的并集)
    analysis.handle_copy('q', 'r')
    
    result = analysis.solve()
    
    print("指向分析结果:")
    for var in ['p', 'q', 'r']:
        pts = result.get_points_to(Var(var))
        print(f"  {var} → {pts}")


def example_heap():
    """堆分配分析"""
    analysis = AndersenPointsTo()
    
    # p = &obj1
    analysis.handle_addr('p', 'obj1')
    # q = p
    analysis.handle_copy('q', 'p')
    # p = &obj2
    analysis.handle_addr('p', 'obj2')
    
    result = analysis.solve()
    
    print("\n堆分配分析:")
    for var in ['p', 'q']:
        pts = result.get_points_to(Var(var))
        print(f"  {var} → {pts}")


def example_alias_detection():
    """基于指向分析的别名检测"""
    analysis = AndersenPointsTo()
    
    # p = &x; q = &y; r = p;
    analysis.handle_addr('p', 'x')
    analysis.handle_addr('q', 'y')
    analysis.handle_copy('r', 'p')
    
    result = analysis.solve()
    
    p_pts = result.get_points_to(Var('p'))
    q_pts = result.get_points_to(Var('q'))
    r_pts = result.get_points_to(Var('r'))
    
    print("\n别名检测:")
    print(f"  p和r可能别名: {bool(p_pts & r_pts)}")
    print(f"  p和q可能别名: {bool(p_pts & q_pts)}")


if __name__ == "__main__":
    print("=" * 50)
    print("指向分析 测试")
    print("=" * 50)
    
    example_simple_points_to()
    print()
    example_heap()
    print()
    example_alias_detection()

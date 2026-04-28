# -*- coding: utf-8 -*-
"""
指针分析/别名分析
功能：确定哪些指针指向同一内存位置

别名分析问题：给定两个指针p和q，判断*p和*q是否可能指向同一对象

算法：
1. Steensgaard算法：基于合并的流不敏感分析（O(n)）
2. Andersen算法：基于约束的流敏感分析（多项式时间）

作者：Pointer Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class Pointer:
    """指针节点"""
    def __init__(self, name: str, is_field: bool = False, field_offset: int = 0):
        self.name = name
        self.is_field = is_field
        self.field_offset = field_offset
    
    def __repr__(self):
        if self.is_field:
            return f"{self.name}.field_{self.field_offset}"
        return self.name
    
    def __hash__(self):
        return hash((self.name, self.is_field, self.field_offset))
    
    def __eq__(self, other):
        return isinstance(other, Pointer) and self.name == other.name


class PointerGraph:
    """指针关系图"""
    
    def __init__(self):
        # 节点集合
        self.nodes: Set[Pointer] = set()
        # 边: pts[ptr] = {可能的指向集合}
        self.pts: Dict[Pointer, Set[Pointer]] = defaultdict(set)
        # 别名对缓存
        self.alias_cache: Dict[Tuple[Pointer, Pointer], Optional[bool]] = {}

    def add_node(self, ptr: Pointer):
        self.nodes.add(ptr)
        if ptr not in self.pts:
            self.pts[ptr] = set()

    def add_points_to(self, ptr: Pointer, target: Pointer):
        """添加 pts(ptr, target)"""
        self.add_node(ptr)
        self.add_node(target)
        self.pts[ptr].add(target)

    def may_alias(self, p: Pointer, q: Pointer) -> bool:
        """
        检查两个指针是否可能别名
        
        简化版本：检查pts集合是否有交集
        """
        if p not in self.pts or q not in self.pts:
            return False
        return bool(self.pts[p] & self.pts[q])

    def must_alias(self, p: Pointer, q: Pointer) -> bool:
        """检查两个指针是否必定别名"""
        if p not in self.pts or q not in self.pts:
            return False
        # 简化：若指向同一唯一对象，则must alias
        p_targets = self.pts[p]
        q_targets = self.pts[q]
        return p_targets == q_targets and len(p_targets) == 1


class SteensgaardAnalysis:
    """
    Steensgaard指针分析（流不敏感，合并语义）
    
    特点：
    - 单次遍历程序
    - 所有赋值语句合并指针等价关系
    - 最坏情况O(n)
    
    核心规则：
    - p = &x → pts(p) ⊆ {x}
    - *p = q → 合并 p 和 q 的指向集合
    - p = q → pts(p) = pts(q)
    """

    def __init__(self):
        self.graph = PointerGraph()
        # 并查集：合并的指针
        self.union_find: Dict[Pointer, Pointer] = {}
        # 指向约束
        self.constraints: List[Tuple[Pointer, Pointer]] = []

    def find(self, ptr: Pointer) -> Pointer:
        """并查集查找"""
        if ptr not in self.union_find:
            self.union_find[ptr] = ptr
            self.graph.add_node(ptr)
        if self.union_find[ptr] != ptr:
            self.union_find[ptr] = self.find(self.union_find[ptr])
        return self.union_find[ptr]

    def union(self, p: Pointer, q: Pointer):
        """并查集合并"""
        rp, rq = self.find(p), self.find(q)
        if rp != rq:
            self.union_find[rq] = rp

    def analyze_assignment(self, lhs: str, rhs: str, kind: str):
        """
        分析赋值语句
        
        Args:
            lhs: 左端
            rhs: 右端
            kind: 'addr', 'copy', 'deref', 'field'
        """
        lhs_ptr = Pointer(lhs)
        rhs_ptr = Pointer(rhs)
        
        if kind == 'addr':
            # p = &x → p指向x
            self.graph.add_points_to(lhs_ptr, rhs_ptr)
        
        elif kind == 'copy':
            # p = q → pts(p) = pts(q)
            self.union(lhs_ptr, rhs_ptr)
            # 合并指向集合
            self.graph.pts[self.find(lhs_ptr)] |= self.graph.pts.get(self.find(rhs_ptr), set())
        
        elif kind == 'deref':
            # *p = q 或 p = *q
            # Steensgaard中，这会导致p和q合并
            self.union(lhs_ptr, rhs_ptr)
        
        elif kind == 'field':
            # p = q.f
            lhs_f = Pointer(lhs, is_field=True, field_offset=0)
            rhs_f = Pointer(rhs, is_field=True, field_offset=0)
            self.union(lhs_f, rhs_f)

    def solve(self):
        """求解指针指向关系"""
        # 传播约束直到不动点
        changed = True
        while changed:
            changed = False
            for ptr, targets in list(self.graph.pts.items()):
                r = self.find(ptr)
                for target in set(targets):
                    rt = self.find(target)
                    if rt not in self.graph.pts[r]:
                        self.graph.pts[r].add(rt)
                        changed = True

    def get_points_to(self, ptr_name: str) -> Set[Pointer]:
        """获取指针的可能指向"""
        ptr = Pointer(ptr_name)
        r = self.find(ptr)
        return self.graph.pts.get(r, set())


class AndersenAnalysis:
    """
    Andersen-style指针分析（流敏感，基于约束）
    
    特点：
    - 对每个程序点维护指向关系
    - 约束传播算法
    - 更精确但更慢
    """

    def __init__(self):
        self.constraints: List[Tuple[Pointer, Pointer]] = []
        self.nodes: Set[Pointer] = set()

    def add_constraint(self, source: Pointer, target: Pointer):
        """添加指向约束 source ⊆ target"""
        self.constraints.append((source, target))
        self.nodes.add(source)
        self.nodes.add(target)

    def solve(self) -> Dict[Pointer, Set[Pointer]]:
        """
        求解约束
        
        使用worklist算法
        """
        pts: Dict[Pointer, Set[Pointer]] = defaultdict(set)
        worklist = deque(self.constraints)
        
        while worklist:
            src, tgt = worklist.popleft()
            
            # 检查是否需要传播
            old_size = len(pts[tgt])
            pts[tgt] |= pts.get(src, set())
            pts[tgt].add(src)  # 自指向
            
            if len(pts[tgt]) > old_size:
                # 有新元素，传播到所有使用tgt作为源的约束
                for s, t in self.constraints:
                    if s == tgt:
                        worklist.append((tgt, t))
        
        return pts


def example_simple_alias():
    """简单别名分析"""
    analysis = SteensgaardAnalysis()
    
    # p = &x
    analysis.analyze_assignment('p', 'x', 'addr')
    # q = p
    analysis.analyze_assignment('q', 'p', 'copy')
    # r = &y
    analysis.analyze_assignment('r', 'y', 'addr')
    
    analysis.solve()
    
    print("Steensgaard分析结果:")
    print(f"  p指向: {analysis.get_points_to('p')}")
    print(f"  q指向: {analysis.get_points_to('q')}")
    print(f"  r指向: {analysis.get_points_to('r')}")
    
    # 检查别名
    p = Pointer('p')
    q = Pointer('q')
    r = Pointer('r')
    
    print(f"  p和q可能别名: {analysis.graph.may_alias(p, q)}")
    print(f"  p和r可能别名: {analysis.graph.may_alias(p, r)}")


def example_complex():
    """复杂示例"""
    analysis = SteensgaardAnalysis()
    
    # a = &x
    analysis.analyze_assignment('a', 'x', 'addr')
    # b = &y
    analysis.analyze_assignment('b', 'y', 'addr')
    # c = a
    analysis.analyze_assignment('c', 'a', 'copy')
    # b = c  (指向y和x的合并)
    analysis.analyze_assignment('b', 'c', 'copy')
    
    analysis.solve()
    
    print("\n复杂示例:")
    print(f"  a指向: {analysis.get_points_to('a')}")
    print(f"  b指向: {analysis.get_points_to('b')}")
    print(f"  c指向: {analysis.get_points_to('c')}")


def example_andersen():
    """Andersen分析示例"""
    analysis = AndersenAnalysis()
    
    a = Pointer('a')
    x = Pointer('x')
    b = Pointer('b')
    y = Pointer('y')
    p = Pointer('p')
    
    # a = &x
    analysis.add_constraint(x, a)
    # b = &y
    analysis.add_constraint(y, b)
    # p = a
    analysis.add_constraint(a, p)
    # p = b
    analysis.add_constraint(b, p)
    
    pts = analysis.solve()
    print("\nAndersen分析:")
    for ptr, targets in pts.items():
        if targets:
            print(f"  pts({ptr}) = {targets}")


if __name__ == "__main__":
    print("=" * 50)
    print("指针别名分析 测试")
    print("=" * 50)
    
    example_simple_alias()
    print()
    example_complex()
    print()
    example_andersen()

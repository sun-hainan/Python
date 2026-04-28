"""
证明搜索策略 (Proof Search Strategies)
======================================
功能：实现不同的证明搜索策略
支持宽度优先、深度优先、最佳优先、归结策略

搜索策略：
1. 宽度优先搜索(BFS)：先扩展所有同一深度的节点
2. 深度优先搜索(DFS)：先沿一条路径深入
3. 最佳优先搜索(Heuristic)：基于启发式函数选择
4. 归结策略：支持多种归结顺序和限制

归结策略：
- 单一归结(Unit Resolution)：至少有一个单文字子句
- 支撑集归结(Support Set)：每次归结至少有一个子句来自支撑集
- 祖先过滤归结(Ancestry Filtering)：禁止对有祖先关系的子句归结
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable, TypeVar
from dataclasses import dataclass, field
from collections import deque
import heapq
import random


T = TypeVar('T')


@dataclass
class Literal:
    """文字"""
    atom: str
    negated: bool = False
    
    def __str__(self):
        return f"¬{self.atom}" if self.negated else self.atom
    
    def complement(self):
        return Literal(self.atom, not self.negated)


@dataclass
class Clause:
    """子句"""
    literals: Set[Literal]
    parent_ids: Tuple[int, int] = field(default_factory=tuple)  # 父子句ID
    id: int = 0
    
    def is_empty(self):
        return len(self.literals) == 0
    
    def is_unit(self):
        return len(self.literals) == 1


@dataclass
class SearchNode:
    """搜索节点"""
    clause: Clause
    depth: int
    heuristic_value: float = 0.0
    
    def __lt__(self, other):
        return self.heuristic_value < other.heuristic_value


class ResolutionProofSearch:
    """
    归结证明搜索
    
    支持多种搜索策略
    """
    
    def __init__(self):
        self.clauses: List[Clause] = []
        self.clause_counter = 0
        self.support_set: Set[int] = set()       # 支撑集
    
    def add_clause(self, clause: Clause) -> int:
        """添加子句，返回子句ID"""
        clause.id = self.clause_counter
        self.clauses.append(clause)
        self.clause_counter += 1
        return clause.id
    
    def resolve(self, c1: Clause, c2: Clause) -> List[Clause]:
        """归结两个子句"""
        results = []
        
        for lit1 in c1.literals:
            for lit2 in c2.literals:
                if lit1.atom == lit2.atom and lit1.negated != lit2.negated:
                    new_literals = set()
                    
                    for lit in c1.literals:
                        if lit != lit1:
                            new_literals.add(lit)
                    
                    for lit in c2.literals:
                        if lit != lit2:
                            new_literals.add(lit)
                    
                    resolvent = Clause(
                        new_literals,
                        parent_ids=(c1.id, c2.id)
                    )
                    results.append(resolvent)
        
        return results
    
    def set_support_set(self, clause_ids: Set[int]):
        """设置支撑集"""
        self.support_set = clause_ids
    
    # -------------------- 搜索策略 --------------------
    
    def bfs_search(self, goal_clause_id: Optional[int] = None) -> Optional[Clause]:
        """
        宽度优先搜索
        
        先扩展浅层节点，保证找到最短证明
        """
        print("[搜索] 宽度优先搜索")
        
        queue = deque([(c.id, c) for c in self.clauses])
        visited = {c.id for c in self.clauses}
        depth_limit = 0
        
        for iteration in range(1000):
            if not queue:
                break
            
            current_id, current_clause = queue.popleft()
            
            # 检查目标
            if current_clause.is_empty():
                print(f"[搜索] ✓ 找到空子句 (深度={current_clause.depth})")
                return current_clause
            
            # 深度限制
            if current_clause.depth >= depth_limit + 5:
                continue
            
            # 归结
            for other_id, other_clause in enumerate(self.clauses):
                if other_id in visited:
                    continue
                
                resolvents = self.resolve(current_clause, other_clause)
                
                for res in resolvents:
                    res.id = self.clause_counter
                    res.depth = current_clause.depth + 1
                    self.clause_counter += 1
                    
                    if res.id not in visited:
                        queue.append((res.id, res))
                        visited.add(res.id)
                        self.add_clause(res)
            
            # 重新排序队列（按深度）
            if iteration % 10 == 0:
                queue = deque(sorted(list(queue), key=lambda x: x[1].depth))
        
        print(f"[搜索] ✗ 未找到证明")
        return None
    
    def dfs_search(
        self,
        max_depth: int = 20,
        current_depth: int = 0,
        visited_ids: Optional[Set[int]] = None
    ) -> Optional[Clause]:
        """
        深度优先搜索
        
        快速深入，可能找到长证明
        """
        if visited_ids is None:
            visited_ids = set()
        
        if current_depth > max_depth:
            return None
        
        for clause in self.clauses:
            if clause.id in visited_ids:
                continue
            
            # 归结
            for other_clause in self.clauses:
                if other_clause.id == clause.id:
                    continue
                
                resolvents = self.resolve(clause, other_clause)
                
                for res in resolvents:
                    if res.is_empty():
                        return res
                    
                    if current_depth < max_depth:
                        visited_ids.add(res.id)
                        self.add_clause(res)
                        
                        # 递归
                        result = self.dfs_search(
                            max_depth, 
                            current_depth + 1,
                            visited_ids
                        )
                        
                        if result and result.is_empty():
                            return result
            
            visited_ids.add(clause.id)
        
        return None
    
    def best_first_search(self) -> Optional[Clause]:
        """
        最佳优先搜索（使用启发式）
        
        启发式：子句中文字数量（越少越好）
        """
        print("[搜索] 最佳优先搜索")
        
        # 初始化优先队列
        pq = []
        for clause in self.clauses:
            node = SearchNode(
                clause=clause,
                depth=0,
                heuristic_value=len(clause.literals)  # 启发式：文字数
            )
            heapq.heappush(pq, node)
        
        visited = set()
        
        for iteration in range(5000):
            if not pq:
                break
            
            node = heapq.heappop(pq)
            
            if node.clause.is_empty():
                print(f"[搜索] ✓ 找到空子句 (迭代={iteration})")
                return node.clause
            
            # 检查是否已处理
            if node.clause.id in visited:
                continue
            visited.add(node.clause.id)
            
            # 归结
            for other_clause in self.clauses:
                if other_clause.id in visited:
                    continue
                
                resolvents = self.resolve(node.clause, other_clause)
                
                for res in resolvents:
                    if res.id not in visited:
                        h = len(res.literals) + res.depth  # 简单启发式
                        new_node = SearchNode(res, res.depth, h)
                        heapq.heappush(pq, new_node)
                        self.add_clause(res)
        
        print(f"[搜索] ✗ 未找到证明")
        return None
    
    def unit_resolution_search(self) -> Optional[Clause]:
        """
        单一归结策略
        
        每次归结至少有一个单位子句（单文字）参与
        """
        print("[搜索] 单一归结搜索")
        
        # 分离单位子句和非单位子句
        unit_clauses = [c for c in self.clauses if c.is_unit()]
        other_clauses = [c for c in self.clauses if not c.is_unit()]
        
        queue = list(unit_clauses)
        visited = {c.id for c in self.clauses}
        
        for iteration in range(1000):
            if not queue:
                break
            
            current = queue.pop(0)
            
            if current.is_empty():
                print(f"[搜索] ✓ 找到空子句")
                return current
            
            # 与所有子句归结
            for other in self.clauses:
                if other.id in visited:
                    continue
                
                resolvents = self.resolve(current, other)
                
                for res in resolvents:
                    if res.is_empty():
                        return res
                    
                    if res.id not in visited:
                        visited.add(res.id)
                        self.add_clause(res)
                        
                        if res.is_unit():
                            queue.append(res)
        
        print(f"[搜索] ✗ 未找到证明")
        return None
    
    def support_set_resolution(self, goal_id: int) -> Optional[Clause]:
        """
        支撑集归结策略
        
        每次归结至少有一个子句来自支撑集
        """
        print("[搜索] 支撑集归结搜索")
        
        # 初始化支撑集
        self.support_set = {goal_id}
        
        queue = deque([self.clauses[goal_id]])
        in_queue = {goal_id}
        
        for iteration in range(1000):
            if not queue:
                break
            
            current = queue.popleft()
            in_queue.remove(current.id)
            
            if current.is_empty():
                print(f"[搜索] ✓ 找到空子句")
                return current
            
            # 与支撑集归结
            for support_id in self.support_set:
                support_clause = self.clauses[support_id]
                resolvents = self.resolve(current, support_clause)
                
                for res in resolvents:
                    if res.is_empty():
                        return res
                    
                    res.id = self.clause_counter
                    self.clause_counter += 1
                    self.add_clause(res)
                    self.support_set.add(res.id)
                    
                    if res.id not in in_queue:
                        queue.append(res)
                        in_queue.add(res.id)
            
            # 与所有子句归结
            for other in self.clauses:
                if other.id == current.id:
                    continue
                
                resolvents = self.resolve(current, other)
                
                for res in resolvents:
                    if res.is_empty():
                        return res
                    
                    if res.id not in self.support_set:
                        self.support_set.add(res.id)
                        res.id = self.clause_counter
                        self.clause_counter += 1
                        self.add_clause(res)
                        queue.append(res)
                        in_queue.add(res.id)
        
        print(f"[搜索] ✗ 未找到证明")
        return None


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("证明搜索策略测试")
    print("=" * 50)
    
    search = ResolutionProofSearch()
    
    # 添加子句
    # p, q, p→r, r→⊥
    clauses = [
        Clause({Literal("p")}),
        Clause({Literal("q")}),
        Clause({Literal("r", negated=True), Literal("p")}),   # ¬r ∨ p
        Clause({Literal("r", negated=True)}),                   # ¬r (目标)
    ]
    
    for c in clauses:
        search.add_clause(c)
    
    print(f"初始子句数: {len(search.clauses)}")
    
    # 测试各种搜索策略
    print("\n--- 深度优先搜索 ---")
    result = search.dfs_search(max_depth=10)
    print(f"结果: {'成功' if result and result.is_empty() else '失败'}")
    
    # 重置
    search2 = ResolutionProofSearch()
    for c in clauses:
        search2.add_clause(c)
    
    print("\n--- 最佳优先搜索 ---")
    result = search2.best_first_search()
    print(f"结果: {'成功' if result and result.is_empty() else '失败'}")
    
    # 重置
    search3 = ResolutionProofSearch()
    for c in clauses:
        search3.add_clause(c)
    
    print("\n--- 单一归结搜索 ---")
    result = search3.unit_resolution_search()
    print(f"结果: {'成功' if result and result.is_empty() else '失败'}")
    
    print("\n✓ 证明搜索策略测试完成")

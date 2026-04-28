"""
时序查询处理 (Temporal Query Processing)
======================================
实现时序知识图谱的查询处理，包括时间范围查询和时序推理查询。

支持的查询类型：
1. 时间点查询: (s, p, o) @ t
2. 时间范围查询: (s, p, o) between [t1, t2]
3. 时序路径查询: 带有时间约束的路径查询
4. 时间推理查询: 基于时序逻辑的查询

参考：
    -渭Temporal Query Language (TQL) Design.
    - TimeTravel SPARQL Extensions.
"""

from typing import List, Dict, Set, Tuple, Optional, Any, Callable
from collections import defaultdict
from enum import Enum


class TemporalOperator(Enum):
    """时序操作符"""
    AT = "AT"           # 在时间点
    BEFORE = "BEFORE"   # 在...之前
    AFTER = "AFTER"     # 在...之后
    BETWEEN = "BETWEEN" # 在...之间
    OVERLAPS = "OVERLAPS"  # 时间重叠
    CONTAINS = "CONTAINS"  # 包含
    STARTS = "STARTS"   # 开始于
    ENDS = "ENDS"       # 结束于


class TemporalQuery:
    """时序查询"""
    def __init__(self, query_type: str, subject: Optional[str] = None,
                 predicate: Optional[str] = None, obj: Optional[str] = None,
                 time_constraint: Any = None, operator: TemporalOperator = TemporalOperator.AT):
        self.query_type = query_type
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.time_constraint = time_constraint
        self.operator = operator
    
    def __str__(self):
        parts = []
        if self.subject:
            parts.append(f"s={self.subject}")
        if self.predicate:
            parts.append(f"p={self.predicate}")
        if self.obj:
            parts.append(f"o={self.obj}")
        if self.time_constraint:
            parts.append(f"t{self.operator.value}={self.time_constraint}")
        return f"TemporalQuery({', '.join(parts)})"


class TemporalQueryEngine:
    """
    时序查询引擎
    
    参数:
        kg: 时序知识图谱
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.query_cache = {}
    
    def execute(self, query: TemporalQuery) -> Set[Tuple]:
        """
        执行时序查询
        
        参数:
            query: 时序查询
        
        返回:
            结果集合
        """
        # 根据操作符分发
        if query.operator == TemporalOperator.AT:
            return self._query_at(query)
        elif query.operator == TemporalOperator.BEFORE:
            return self._query_before(query)
        elif query.operator == TemporalOperator.AFTER:
            return self._query_after(query)
        elif query.operator == TemporalOperator.BETWEEN:
            return self._query_between(query)
        elif query.operator == TemporalOperator.OVERLAPS:
            return self._query_overlaps(query)
        else:
            return set()
    
    def _query_at(self, query: TemporalQuery) -> Set[Tuple]:
        """时间点查询"""
        results = self.kg.query_at_time(query.time_constraint)
        
        # 过滤subject和predicate
        filtered = set()
        for s, p, o in results:
            if query.subject and query.subject != s:
                continue
            if query.predicate and query.predicate != p:
                continue
            if query.obj and query.obj != o:
                continue
            filtered.add((s, p, o))
        
        return filtered
    
    def _query_before(self, query: TemporalQuery) -> Set[Tuple]:
        """时间前查询"""
        results = set()
        t = query.time_constraint
        
        for (s, p, o), intervals in self.kg.triples.items():
            for t_start, t_end in intervals:
                if t_end < t:
                    # 检查过滤条件
                    if query.subject and query.subject != s:
                        continue
                    if query.predicate and query.predicate != p:
                        continue
                    if query.obj and query.obj != o:
                        continue
                    results.add((s, p, o, (t_start, t_end)))
        
        return results
    
    def _query_after(self, query: TemporalQuery) -> Set[Tuple]:
        """时间后查询"""
        results = set()
        t = query.time_constraint
        
        for (s, p, o), intervals in self.kg.triples.items():
            for t_start, t_end in intervals:
                if t_start > t:
                    if query.subject and query.subject != s:
                        continue
                    if query.predicate and query.predicate != p:
                        continue
                    if query.obj and query.obj != o:
                        continue
                    results.add((s, p, o, (t_start, t_end)))
        
        return results
    
    def _query_between(self, query: TemporalQuery) -> Set[Tuple]:
        """时间范围查询"""
        results = set()
        t_start, t_end = query.time_constraint
        
        for (s, p, o), intervals in self.kg.triples.items():
            for interval_start, interval_end in intervals:
                # 重叠检查
                if interval_start <= t_end and interval_end >= t_start:
                    if query.subject and query.subject != s:
                        continue
                    if query.predicate and query.predicate != p:
                        continue
                    if query.obj and query.obj != o:
                        continue
                    results.add((s, p, o, (interval_start, interval_end)))
        
        return results
    
    def _query_overlaps(self, query: TemporalQuery) -> Set[Tuple]:
        """时间重叠查询"""
        results = set()
        
        for (s, p, o), intervals in self.kg.triples.items():
            for t1_start, t1_end in intervals:
                for t2_start, t2_end in query.time_constraint:
                    # 检查重叠
                    if t1_start <= t2_end and t2_start <= t1_end:
                        results.add((s, p, o, (t1_start, t1_end)))
                        break
        
        return results


class TemporalPathQuery:
    """
    时序路径查询
    
    参数:
        kg: 时序知识图谱
        max_length: 最大路径长度
    """
    
    def __init__(self, kg, max_length: int = 3):
        self.kg = kg
        self.max_length = max_length
    
    def find_temporal_paths(self, source: str, target: str,
                           time_constraint: Optional[Tuple[Any, Any]] = None) -> List[List[Tuple]]:
        """
        找从source到target的时序路径
        
        参数:
            source: 起点实体
            target: 终点实体
            time_constraint: 时间约束 (start, end)
        
        返回:
            路径列表，每个路径是 [(s,p,o,t), ...]
        """
        paths = []
        
        def dfs(current: str, target: str, path: List[Tuple], 
               visited: Set[str], time_constraint: Optional[Tuple]):
            if len(path) > self.max_length:
                return
            
            if current == target and path:
                paths.append(path[:])
                return
            
            # 获取邻居
            neighbors = self.kg.get_temporal_neighbors(current)
            
            for neighbor, predicate, time in neighbors:
                if neighbor in visited:
                    continue
                
                # 时间约束检查
                if time_constraint:
                    t_start, t_end = time_constraint
                    if isinstance(time, tuple):
                        time_start, time_end = time
                    else:
                        time_start = time_end = time
                    
                    if not (time_start <= t_end and time_end >= t_start):
                        continue
                
                # 添加到路径
                path.append((current, predicate, neighbor, time))
                visited.add(neighbor)
                
                dfs(neighbor, target, path, visited, time_constraint)
                
                # 回溯
                path.pop()
                visited.remove(neighbor)
        
        dfs(source, target, [], {source}, time_constraint)
        
        return paths
    
    def find_shortest_temporal_path(self, source: str, target: str,
                                   time_constraint: Optional[Tuple] = None) -> Optional[List[Tuple]]:
        """
        找最短时序路径
        
        参数:
            source: 起点
            target: 终点
            time_constraint: 时间约束
        
        返回:
            最短路径或None
        """
        # BFS
        from collections import deque
        
        queue = deque([(source, [(source, None, None, None)])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                return path[1:]  # 去掉起始的dummy
            
            if len(path) > self.max_length:
                continue
            
            neighbors = self.kg.get_temporal_neighbors(current)
            
            for neighbor, predicate, time in neighbors:
                if neighbor not in visited:
                    # 时间约束
                    if time_constraint:
                        t_start, t_end = time_constraint
                        if isinstance(time, tuple):
                            time_start, time_end = time
                        else:
                            time_start = time_end = time
                        
                        if not (time_start <= t_end and time_end >= t_start):
                            continue
                    
                    new_path = path + [(current, predicate, neighbor, time)]
                    queue.append((neighbor, new_path))
                    visited.add(neighbor)
        
        return None


class TemporalAggregationQuery:
    """时序聚合查询"""
    
    def __init__(self, kg):
        self.kg = kg
    
    def count_events_between(self, entity: str, 
                            t_start: Any, t_end: Any,
                            predicate: Optional[str] = None) -> int:
        """
        统计实体在时间范围内的事件数
        
        参数:
            entity: 实体
            t_start: 开始时间
            t_end: 结束时间
            predicate: 可选谓词过滤
        
        返回:
            事件数
        """
        count = 0
        neighbors = self.kg.get_temporal_neighbors(entity)
        
        for neighbor, pred, time in neighbors:
            if isinstance(time, tuple):
                time_start, time_end = time
            else:
                time_start = time_end = time
            
            # 重叠检查
            if time_start <= t_end and time_end >= t_start:
                if predicate and pred != predicate:
                    continue
                count += 1
        
        return count
    
    def find_first_event(self, entity: str, predicate: str) -> Optional[Tuple]:
        """找实体的第一个特定事件"""
        neighbors = self.kg.get_temporal_neighbors(entity)
        
        first = None
        first_time = float('inf')
        
        for neighbor, pred, time in neighbors:
            if pred == predicate:
                if isinstance(time, tuple):
                    t = time[0]
                else:
                    t = time
                
                if t < first_time:
                    first_time = t
                    first = (neighbor, pred, time)
        
        return first
    
    def find_last_event(self, entity: str, predicate: str) -> Optional[Tuple]:
        """找实体的最后一个特定事件"""
        neighbors = self.kg.get_temporal_neighbors(entity)
        
        last = None
        last_time = float('-inf')
        
        for neighbor, pred, time in neighbors:
            if pred == predicate:
                if isinstance(time, tuple):
                    t = time[1]
                else:
                    t = time
                
                if t > last_time:
                    last_time = t
                    last = (neighbor, pred, time)
        
        return last


if __name__ == "__main__":
    print("=== 时序查询处理测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 构建测试TKG
    kg = TemporalKG()
    
    facts = [
        ("Alice", "works_at", "CompanyA", 2018),
        ("Alice", "works_at", "CompanyB", 2020, 2022),
        ("Alice", "married_to", "Bob", 2020),
        ("Bob", "works_at", "CompanyA", 2019),
        ("CompanyA", "located_in", "Paris", 2018),
        ("CompanyB", "located_in", "London", 2020),
        ("Alice", "moved_to", "London", 2020),
    ]
    
    for f in facts:
        if len(f) == 4:
            kg.add_triple(f[0], f[1], f[2], f[3])
        else:
            kg.add_fact(f[0], f[1], f[2], f[3], f[4])
    
    print("时序知识图谱已构建")
    
    # 创建查询引擎
    engine = TemporalQueryEngine(kg)
    
    # 测试时序查询
    print("\n--- 时序查询 ---")
    
    # AT查询
    query1 = TemporalQuery("fact", predicate="works_at",
                           time_constraint=2019, operator=TemporalOperator.AT)
    results1 = engine.execute(query1)
    print(f"\n2019年 works_at 事实: {results1}")
    
    # BETWEEN查询
    query2 = TemporalQuery("fact", subject="Alice",
                           time_constraint=(2019, 2021),
                           operator=TemporalOperator.BETWEEN)
    results2 = engine.execute(query2)
    print(f"\n2019-2021年间 Alice 的事实: {results2}")
    
    # BEFORE查询
    query3 = TemporalQuery("fact", subject="Alice",
                           time_constraint=2020,
                           operator=TemporalOperator.BEFORE)
    results3 = engine.execute(query3)
    print(f"\n2020年前 Alice 的事实: {results3}")
    
    # 时序路径查询
    print("\n--- 时序路径查询 ---")
    path_query = TemporalPathQuery(kg, max_length=3)
    
    paths = path_query.find_temporal_paths("Alice", "London", time_constraint=(2015, 2025))
    print(f"\nAlice到London的时序路径:")
    for path in paths[:3]:
        print(f"  {path}")
    
    # 最短时序路径
    shortest = path_query.find_shortest_temporal_path("Alice", "CompanyA", time_constraint=(2015, 2025))
    print(f"\nAlice到CompanyA的最短路径: {shortest}")
    
    # 聚合查询
    print("\n--- 聚合查询 ---")
    agg_query = TemporalAggregationQuery(kg)
    
    count = agg_query.count_events_between("Alice", 2015, 2025)
    print(f"\nAlice在2015-2025年间的事件数: {count}")
    
    first_works = agg_query.find_first_event("Alice", "works_at")
    print(f"Alice的第一个works_at事件: {first_works}")
    
    last_works = agg_query.find_last_event("Alice", "works_at")
    print(f"Alice的最后一个works_at事件: {last_works}")
    
    print("\n=== 测试完成 ===")

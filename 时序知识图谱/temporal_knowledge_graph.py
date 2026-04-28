"""
时序知识图谱基础 (Temporal Knowledge Graph Foundation)
====================================================
时序知识图谱是带有时间戳边的知识图谱，支持时序查询和推理。

核心概念：
- 时序边 (s, p, o, t)：主语s和宾语o在时间t有谓词p
- 时间窗口查询
- 时序一致性

参考：
    - Costabello, L. et al. (2019). Temporal Knowledge Graphs.
    - Leblay, J. & Chekol, M.W. (2018). Deriving Validity Time in Knowledge Graphs.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta


class TemporalKG:
    """
    时序知识图谱
    
    使用邻接表和时间索引存储时序三元组
    
    参数:
        name: 图谱名称
    """
    
    def __init__(self, name: str = "TKG"):
        self.name = name
        # 三元组存储: (s, p, o) -> [(t_start, t_end), ...]
        self.triples = defaultdict(list)
        # 时间索引: t -> [(s, p, o), ...]
        self.time_index = defaultdict(set)
        # 实体集合
        self.entities = set()
        # 谓词集合
        self.predicates = set()
        # 实体类型: entity -> type
        self.entity_types = {}
        # 时间范围
        self.time_range = (None, None)
    
    def add_fact(self, subject: str, predicate: str, obj: str, 
                time_start: Any, time_end: Optional[Any] = None) -> None:
        """
        添加时序事实
        
        参数:
            subject: 主语实体
            predicate: 谓词
            obj: 宾语实体
            time_start: 开始时间
            time_end: 结束时间（None表示瞬时）
        """
        # 更新实体和谓词集合
        self.entities.add(subject)
        self.entities.add(obj)
        self.predicates.add(predicate)
        
        # 添加时间区间
        if time_end is None:
            time_end = time_start
        
        key = (subject, predicate, obj)
        self.triples[key].append((time_start, time_end))
        self.time_index[time_start].add(key)
        if time_end != time_start:
            self.time_index[time_end].add(key)
        
        # 更新全局时间范围
        if self.time_range[0] is None or time_start < self.time_range[0]:
            self.time_range = (time_start, self.time_range[1])
        if self.time_range[1] is None or time_end > self.time_range[1]:
            self.time_range = (self.time_range[0], time_end)
    
    def add_triple(self, s: str, p: str, o: str, t: Any) -> None:
        """添加瞬时三元组（简写）"""
        self.add_fact(s, p, o, t, t)
    
    def query_at_time(self, time: Any) -> Set[Tuple[str, str, str]]:
        """
        查询指定时间的事实
        
        参数:
            time: 查询时间
        
        返回:
            时间点上的事实集合
        """
        result = set()
        
        for (s, p, o), intervals in self.triples.items():
            for t_start, t_end in intervals:
                if t_start <= time <= t_end:
                    result.add((s, p, o))
                    break
        
        return result
    
    def query_between(self, t_start: Any, t_end: Any) -> Set[Tuple[str, str, str]]:
        """
        查询时间范围内的事实
        
        参数:
            t_start: 开始时间
            t_end: 结束时间
        
        返回:
            时间范围内的事实集合
        """
        result = set()
        
        for (s, p, o), intervals in self.triples.items():
            for interval_start, interval_end in intervals:
                # 检查区间是否与查询区间重叠
                if interval_start <= t_end and interval_end >= t_start:
                    result.add((s, p, o))
                    break
        
        return result
    
    def get_temporal_neighbors(self, entity: str, time: Optional[Any] = None) -> Set[Tuple[str, str, Any]]:
        """
        获取实体的时序邻居
        
        参数:
            entity: 实体
            time: 查询时间（None表示所有时间）
        
        返回:
            (邻居, 谓词, 时间) 元组集合
        """
        neighbors = set()
        
        for (s, p, o), intervals in self.triples.items():
            if s == entity:
                for t_start, t_end in intervals:
                    if time is None or t_start <= time <= t_end:
                        neighbors.add((o, p, t_start))
                        break
            elif o == entity:
                for t_start, t_end in intervals:
                    if time is None or t_start <= time <= t_end:
                        neighbors.add((s, p, t_start))
                        break
        
        return neighbors
    
    def get_validity_time(self, s: str, p: str, o: str) -> List[Tuple[Any, Any]]:
        """
        获取三元组的有效时间
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
        
        返回:
            时间区间列表
        """
        key = (s, p, o)
        return self.triples.get(key, [])
    
    def get_entity_lifespan(self, entity: str) -> Tuple[Any, Any]:
        """
        获取实体的存活时间范围
        
        参数:
            entity: 实体
        
        返回:
            (开始时间, 结束时间)
        """
        intervals = []
        
        for (s, p, o), times in self.triples.items():
            if s == entity or o == entity:
                for t_start, t_end in times:
                    intervals.append((t_start, t_end))
        
        if not intervals:
            return (None, None)
        
        return (min(i[0] for i in intervals), max(i[1] for i in intervals))
    
    def infer_at_time(self, s: str, p: str, o: str, time: Any) -> bool:
        """
        检查给定时间是否可推断该三元组
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
            time: 查询时间
        
        返回:
            是否成立
        """
        key = (s, p, o)
        if key not in self.triples:
            return False
        
        for t_start, t_end in self.triples[key]:
            if t_start <= time <= t_end:
                return True
        
        return False
    
    def statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        返回:
            统计字典
        """
        return {
            "name": self.name,
            "num_entities": len(self.entities),
            "num_predicates": len(self.predicates),
            "num_triples": len(self.triples),
            "time_range": self.time_range,
        }


class TemporalQueryEngine:
    """时序查询引擎"""
    
    def __init__(self, kg: TemporalKG):
        self.kg = kg
    
    def temporal_path_query(self, s: str, t_start: Any, t_end: Any, 
                           max_length: int = 3) -> Set[Tuple[str, ...]]:
        """
        时序路径查询
        
        参数:
            s: 起始实体
            t_start: 查询开始时间
            t_end: 查询结束时间
            max_length: 最大路径长度
        
        返回:
            可达路径集合
        """
        results = set()
        
        def dfs(current: str, time: Any, path: List[str], depth: int):
            if depth > max_length:
                return
            
            path = path + [current]
            
            # 获取当前时间的邻居
            neighbors = self.kg.get_temporal_neighbors(current, time)
            
            for neighbor, predicate, next_time in neighbors:
                if neighbor not in path:  # 避免循环
                    new_path = path + [neighbor]
                    results.add(tuple(new_path))
                    dfs(neighbor, next_time, new_path, depth + 1)
        
        dfs(s, t_start, [], 0)
        return results
    
    def temporal_join(self, p1: str, p2: str, t_constraint: str = "overlap") -> Set[Tuple]:
        """
        时序连接查询
        
        参数:
            p1: 谓词1
            p2: 谓词2
            t_constraint: 时间约束 ("overlap", "before", "after", "equals")
        
        返回:
            连接结果
        """
        results = set()
        
        # 获取两个谓词的三元组
        triples1 = {(s, o, t) for (s, p, o), intervals in self.kg.triples.items() 
                   if p == p1 for t in intervals}
        
        triples2 = {(s, o, t) for (s, p, o), intervals in self.kg.triples.items() 
                   if p == p2 for t in intervals}
        
        for s1, o1, t1 in triples1:
            for s2, o2, t2 in triples2:
                # 基于时间约束连接
                if t_constraint == "overlap":
                    if t1[0] <= t2[1] and t2[0] <= t1[1]:
                        if o1 == s2:
                            results.add((s1, p1, o1, t1, p2, o2, t2))
                elif t_constraint == "before":
                    if t1[1] <= t2[0]:
                        if o1 == s2:
                            results.add((s1, p1, o1, t1, p2, o2, t2))
                elif t_constraint == "equals":
                    if t1 == t2 and o1 == s2:
                        results.add((s1, p1, o1, t1, p2, o2, t2))
        
        return results


if __name__ == "__main__":
    print("=== 时序知识图谱基础测试 ===")
    
    # 创建时序知识图谱
    kg = TemporalKG("HistoryKG")
    
    # 添加历史事件
    events = [
        # 拿破仑的时序事实
        ("Napoleon", "born_in", "Corsica", 1769),
        ("Napoleon", "became_emperor", "France", 1804),
        ("Napoleon", "married", "Marie", 1810),
        ("Napoleon", "died_in", "Saint_Helena", 1821),
        # 法国的时序事实
        ("France", "has_king", "Louis_XVI", 1789),
        ("France", "has_king", "Louis_XVI", 1792, 1792),  # 被废黜
        ("France", "became_republic", "France", 1792),
        ("France", "has_emperor", "Napoleon", 1804),
    ]
    
    for e in events:
        if len(e) == 4:
            kg.add_triple(e[0], e[1], e[2], e[3])
        else:
            kg.add_fact(e[0], e[1], e[2], e[3], e[4])
    
    print("\n图谱统计:")
    stats = kg.statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 查询1800年时的事实
    print("\n\n1800年时的事实:")
    facts_1800 = kg.query_at_time(1800)
    for s, p, o in facts_1800:
        print(f"  {s} --[{p}]--> {o}")
    
    # 查询1790-1815年间的事实
    print("\n\n1790-1815年间关于Napoleon的事实:")
    facts_napoleon = kg.query_between(1790, 1815)
    for s, p, o in facts_napoleon:
        if s == "Napoleon" or o == "Napoleon":
            print(f"  {s} --[{p}]--> {o}")
    
    # 查询实体的生命周期
    print("\n\n实体生命周期:")
    lifespan = kg.get_entity_lifespan("Napoleon")
    print(f"  Napoleon: {lifespan}")
    
    lifespan_france = kg.get_entity_lifespan("France")
    print(f"  France: {lifespan_france}")
    
    # 时序查询引擎
    print("\n\n时序路径查询:")
    engine = TemporalQueryEngine(kg)
    paths = engine.temporal_path_query("Napoleon", 1800, 1815, max_length=2)
    print(f"  从Napoleon出发的路径: {len(paths)} 条")
    for path in list(paths)[:5]:
        print(f"    {path}")
    
    print("\n=== 测试完成 ===")

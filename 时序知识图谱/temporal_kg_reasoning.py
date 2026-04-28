"""
时序知识图谱推理 (Temporal KG Reasoning)
======================================
实现时序知识图谱的推理能力，包括事实时序预测和推理。

任务：
1. 时序预测：预测未来可能发生的事实
2. 时序一致性：检测违反时序约束的事实
3. 时序补全：补全缺失的时序信息

方法：
- 基于规则：时序传递性、反转性
- 基于嵌入：学习时序模式
- 基于路径：挖掘时序推理路径

参考：
    - CETP: Temporal Knowledge Graph Reasoning with Historical Credit Assignment.
    - Temporal-Rule Based Reasoning on TKG.
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from collections import defaultdict
import random


class TemporalRule:
    """时序规则"""
    def __init__(self, name: str, antecedent: Callable, consequent: Callable,
                 confidence: float = 1.0):
        self.name = name
        self.antecedent = antecedent  # 条件函数
        self.consequent = consequent  # 结论函数
        self.confidence = confidence


class TKGReasoner:
    """
    时序知识图谱推理器
    
    参数:
        kg: 时序知识图谱
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.rules = []
        self.rule_matches = defaultdict(int)
    
    def add_rule(self, rule: TemporalRule):
        """添加推理规则"""
        self.rules.append(rule)
    
    def apply_rules(self, s: str, p: str, o: str, t: Any) -> Set[Tuple]:
        """
        应用规则推断新事实
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
            t: 时间
        
        返回:
            推断的事实集合
        """
        inferred = set()
        
        for rule in self.rules:
            if rule.antecedent(s, p, o, t, self.kg):
                results = rule.consequent(s, p, o, t, self.kg)
                for result in results:
                    self.rule_matches[rule.name] += 1
                    inferred.add(result)
        
        return inferred
    
    def predict_future(self, entity: str, predicate: str, 
                      current_time: Any, horizon: int = 1) -> List[Tuple[str, float]]:
        """
        预测未来事实
        
        参数:
            entity: 实体
            predicate: 谓词
            current_time: 当前时间
            horizon: 预测时间范围
        
        返回:
            [(预测实体, 置信度), ...]
        """
        predictions = []
        
        # 获取历史
        history = self.kg.get_temporal_neighbors(entity, current_time)
        predicate_history = [(neighbor, time) for pred, neighbor, time in history 
                           if pred == predicate]
        
        if not predicate_history:
            return []
        
        # 分析历史模式
        neighbors, times = zip(*predicate_history)
        
        # 简化：基于频率和最近邻
        neighbor_counts = defaultdict(int)
        for n in neighbors:
            neighbor_counts[n] += 1
        
        # 得分
        for neighbor, count in neighbor_counts.items():
            # 频率得分
            freq_score = count / len(predicate_history)
            
            # 时间衰减
            latest_time = max(t for n, t in predicate_history if n == neighbor)
            time_diff = current_time - latest_time
            decay_score = 1.0 / (1.0 + time_diff)
            
            score = 0.7 * freq_score + 0.3 * decay_score
            predictions.append((neighbor, score))
        
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions


class TemporalConsistencyChecker:
    """
    时序一致性检查器
    
    检测违反时序约束的事实
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.violations = []
    
    def check_temporal_precedence(self, s: str, p1: str, p2: str) -> bool:
        """
        检查谓词时序优先级
        
        某些谓词必须在另一些谓词之前
        
        参数:
            s: 实体
            p1: 谓词1
            p2: 谓词2
        
        返回:
            是否一致
        """
        # 获取谓词时间
        p1_times = []
        p2_times = []
        
        for neighbor, pred, time in self.kg.get_temporal_neighbors(s):
            if pred == p1:
                p1_times.append(time)
            elif pred == p2:
                p2_times.append(time)
        
        # 检查是否有违例
        for t1 in p1_times:
            for t2 in p2_times:
                if t2 < t1:  # p2发生在p1之前
                    self.violations.append({
                        "type": "precedence",
                        "entity": s,
                        "pred1": p1,
                        "pred2": p2,
                        "time1": t1,
                        "time2": t2
                    })
                    return False
        
        return True
    
    def check_duration_constraints(self, predicate: str, 
                                   min_duration: float, 
                                   max_duration: float) -> List[Dict]:
        """
        检查持续时间约束
        
        参数:
            predicate: 谓词
            min_duration: 最小持续时间
            max_duration: 最大持续时间
        
        返回:
            违规列表
        """
        violations = []
        
        for (s, p, o), intervals in self.kg.triples.items():
            if p != predicate:
                continue
            
            for t_start, t_end in intervals:
                duration = t_end - t_start
                
                if duration < min_duration or duration > max_duration:
                    violations.append({
                        "subject": s,
                        "predicate": p,
                        "object": o,
                        "duration": duration,
                        "valid": min_duration <= duration <= max_duration
                    })
        
        return violations
    
    def check_atemporal_conflicts(self) -> List[Dict]:
        """
        检测时序冲突
        
        例如：实体不能同时在两个地方
        
        返回:
            冲突列表
        """
        conflicts = []
        
        # 检测"在同一时间在两个地方"的冲突
        for entity in self.kg.entities:
            locations = []
            
            for neighbor, pred, time in self.kg.get_temporal_neighbors(entity):
                if pred in ["located_in", "at", "in"]:
                    locations.append((neighbor, time))
            
            # 检查重叠
            for i, (loc1, t1) in enumerate(locations):
                for loc2, t2 in locations[i+1:]:
                    if isinstance(t1, tuple) and isinstance(t2, tuple):
                        # 重叠检查
                        if t1[0] <= t2[1] and t2[0] <= t1[1]:
                            if loc1 != loc2:
                                conflicts.append({
                                    "entity": entity,
                                    "location1": loc1,
                                    "time1": t1,
                                    "location2": loc2,
                                    "time2": t2
                                })
        
        return conflicts


class TemporalImplicationRules:
    """
    时序蕴含规则
    
    参数:
        kg: 时序知识图谱
    """
    
    def __init__(self, kg):
        self.kg = kg
    
    def transitivity_rule(self, s: str, p: str, o1: str, 
                        t1: Any) -> List[Tuple[str, str, Any]]:
        """
        传递性规则
        
        如果 s --p--> o1 at t1 且 o1 --p--> o2 at t2
        则 s --p*--> o2 at max(t1, t2)
        """
        inferred = []
        
        # o1的p关系历史
        o1_history = self.kg.get_temporal_neighbors(o1, None)
        
        for o2, pred2, t2 in o1_history:
            if pred2 == p and o2 != s:
                inferred.append((o1, p, o2, max(t1, t2)))
        
        return inferred
    
    def implication_rule(self, p1: str, p2: str,
                        s: str, o: str, t: Any) -> List[Tuple]:
        """
        蕴含规则
        
        如果 s --p1--> o at t
        则 s --p2--> o at t + Δt
        """
        inferred = []
        
        # 检查是否存在 p1
        times = self.kg.get_validity_time(s, p1, o)
        if times:
            for t1_start, t1_end in times:
                if t1_start <= t <= t1_end:
                    inferred.append((s, p2, o, t + 1))  # 假设Δt=1
                    break
        
        return inferred
    
    def inverse_rule(self, p: str, inv_p: str,
                     s: str, o: str, t: Any) -> List[Tuple]:
        """
        逆规则
        
        如果 s --p--> o at t
        则 o --inv_p--> s at t
        """
        return [(o, inv_p, s, t)]


class TemporalPathReasoning:
    """
    时序路径推理
    
    基于时序路径的推理
    """
    
    def __init__(self, kg):
        self.kg = kg
    
    def find_reasoning_paths(self, s: str, o: str, 
                            max_length: int = 3) -> List[List[Tuple]]:
        """
        找从s到o的推理路径
        
        参数:
            s: 起点
            o: 终点
            max_length: 最大路径长度
        
        返回:
            路径列表
        """
        paths = []
        
        def dfs(current: str, target: str, path: List[Tuple],
               visited: Set[str], depth: int):
            if depth > max_length:
                return
            
            if current == target and path:
                paths.append(path[:])
                return
            
            for neighbor, pred, time in self.kg.get_temporal_neighbors(current):
                if neighbor not in visited:
                    new_path = path + [(current, pred, neighbor, time)]
                    new_visited = visited | {neighbor}
                    dfs(neighbor, target, new_path, new_visited, depth + 1)
        
        dfs(s, o, [], {s}, 0)
        return paths
    
    def score_path(self, path: List[Tuple]) -> float:
        """
        给路径打分
        
        参数:
            path: 推理路径
        
        返回:
            得分
        """
        if not path:
            return 0.0
        
        # 简化的打分函数
        # 考虑：路径长度、时间一致性、关系强度
        
        length_score = 1.0 / (1.0 + len(path))
        
        # 时间一致性：时间应该递增
        time_consistency = 1.0
        for i in range(len(path) - 1):
            t1 = path[i][3]
            t2 = path[i+1][3]
            if t2 < t1:
                time_consistency *= 0.5
        
        return length_score * time_consistency


def infer_temporal_facts(kg, num_inferences: int = 100) -> Set[Tuple]:
    """
    批量时序推理
    
    参数:
        kg: 时序知识图谱
        num_inferences: 最大推理数
    
    返回:
        推理出的事实集合
    """
    reasoner = TKGReasoner(kg)
    
    # 添加默认规则
    rules = [
        TemporalRule(
            name="frequency_prediction",
            antecedent=lambda s, p, o, t, kg: True,
            consequent=lambda s, p, o, t, kg: reasoner.predict_future(s, p, t)
        )
    ]
    
    for rule in rules:
        reasoner.add_rule(rule)
    
    inferred = set()
    
    # 对每个实体进行推理
    for entity in list(kg.entities)[:10]:
        for pred in kg.predicates:
            predictions = reasoner.predict_future(entity, pred, 
                                                 kg.time_range[1] or 2023)
            for pred_entity, score in predictions[:5]:
                inferred.add((entity, pred, pred_entity, score))
    
    return inferred


if __name__ == "__main__":
    print("=== 时序知识图谱推理测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 构建测试TKG
    kg = TemporalKG()
    
    facts = [
        ("Alice", "born_in", "Paris", 1990),
        ("Alice", "graduated_from", "MIT", 2012),
        ("Alice", "joined", "CompanyX", 2013),
        ("Alice", "married_to", "Bob", 2015),
        ("Bob", "works_at", "CompanyY", 2014),
        ("Alice", "moved_to", "NYC", 2013),
        ("CompanyX", "acquired_by", "CompanyZ", 2020),
    ]
    
    for s, p, o, t in facts:
        kg.add_triple(s, p, o, t)
    
    print("TKG已构建")
    
    # 时序推理
    print("\n--- 时序推理 ---")
    reasoner = TKGReasoner(kg)
    
    # 预测Alice的未来关系
    print("\n预测Alice未来可能的工作地点:")
    predictions = reasoner.predict_future("Alice", "works_at", 2020, horizon=5)
    for entity, score in predictions:
        print(f"  {entity}: {score:.4f}")
    
    # 一致性检查
    print("\n--- 时序一致性检查 ---")
    checker = TemporalConsistencyChecker(kg)
    
    # 检查优先级
    is_consistent = checker.check_temporal_precedence("Alice", "born_in", "graduated_from")
    print(f"born_in before graduated_from: {'一致' if is_consistent else '冲突'}")
    
    # 时序蕴含规则
    print("\n--- 时序蕴含规则 ---")
    impl_rules = TemporalImplicationRules(kg)
    
    # 逆规则
    inv = impl_rules.inverse_rule("married_to", "married_to", "Alice", "Bob", 2015)
    print(f"married_to 逆规则: {inv}")
    
    # 路径推理
    print("\n--- 时序路径推理 ---")
    path_reasoner = TemporalPathReasoning(kg)
    
    paths = path_reasoner.find_reasoning_paths("Alice", "CompanyZ", max_length=3)
    print(f"Alice到CompanyZ的推理路径: {len(paths)} 条")
    for path in paths[:3]:
        print(f"  {path}")
    
    # 路径打分
    if paths:
        scores = [(path, path_reasoner.score_path(path)) for path in paths]
        scores.sort(key=lambda x: x[1], reverse=True)
        print(f"\n最高分路径: {scores[0][0]}")
        print(f"得分: {scores[0][1]:.4f}")
    
    print("\n=== 测试完成 ===")

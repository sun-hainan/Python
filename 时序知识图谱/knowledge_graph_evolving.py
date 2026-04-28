"""
知识图谱演变 (Knowledge Graph Evolution)
======================================
模拟和预测知识图谱的演变过程，包括实体和关系的添加、删除、修改。

核心概念：
- 图谱演变：节点和边随时间的动态变化
- 演变模式：反复出现的演变规律
- 趋势预测：基于历史的未来变化预测

参考：
    - RDF Entailment Regimes.
    - Knowledge Graph Evolution and Stability.
"""

from typing import List, Dict, Set, Tuple, Optional, Any, Callable
from collections import defaultdict, Counter
import random


class KGChange:
    """知识图谱变化"""
    def __init__(self, change_type: str, subject: str, predicate: str,
                 obj: str, time: Any, attributes: Optional[Dict] = None):
        self.type = change_type  # "add", "delete", "update"
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.time = time
        self.attributes = attributes or {}
    
    def __str__(self):
        return f"KGChange({self.type}, {self.subject}--{self.predicate}--{self.obj}@{self.time})"


class EvolutionPattern:
    """演变模式"""
    def __init__(self, pattern_id: str):
        self.id = pattern_id
        self.sequence = []  # 变化序列
        self.frequency = 0
        self.avg_duration = 0
    
    def add_change(self, change: KGChange):
        """添加变化"""
        self.sequence.append(change)
        self.frequency += 1
    
    def compute_stats(self):
        """计算统计信息"""
        if len(self.sequence) > 1:
            times = [c.time for c in self.sequence]
            self.avg_duration = sum(abs(times[i+1] - times[i]) 
                                    for i in range(len(times)-1)) / (len(times)-1)


class KnowledgeGraphEvolution:
    """
    知识图谱演变管理器
    
    参数:
        kg: 初始知识图谱
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.change_history = []  # 变化历史
        self.evolution_patterns = []  # 发现的模式
        self.entity_lifecycles = {}  # 实体生命周期
        self.relation_lifecycles = {}  # 关系生命周期
    
    def add_entity(self, entity_id: str, entity_type: str, 
                  birth_time: Any, death_time: Optional[Any] = None):
        """
        添加实体（带生命周期）
        
        参数:
            entity_id: 实体ID
            entity_type: 实体类型
            birth_time: 出生时间
            death_time: 死亡时间（None表示永生）
        """
        self.entity_lifecycles[entity_id] = {
            "type": entity_type,
            "birth": birth_time,
            "death": death_time,
            "active": True
        }
    
    def add_change(self, change_type: str, s: str, p: str, o: str,
                  t: Any, **kwargs):
        """
        记录变化
        
        参数:
            change_type: 变化类型 ("add", "delete", "update")
            s, p, o: 三元组
            t: 时间
        """
        change = KGChange(change_type, s, p, o, t, kwargs)
        self.change_history.append(change)
        
        # 执行实际变化
        if change_type == "add":
            self.kg.add_triple(s, p, o, t)
        elif change_type == "delete":
            # 简化：从triples中移除
            key = (s, p, o)
            if key in self.kg.triples:
                del self.kg.triples[key]
    
    def get_entity_lifecycle(self, entity: str) -> Dict:
        """获取实体的生命周期"""
        return self.entity_lifecycles.get(entity, {})
    
    def get_entity_events(self, entity: str) -> List[KGChange]:
        """获取实体的所有事件"""
        events = []
        for change in self.change_history:
            if change.subject == entity or change.obj == entity:
                events.append(change)
        return events
    
    def compute_growth_rate(self, time_window: int = 1) -> List[float]:
        """
        计算图谱增长率
        
        参数:
            time_window: 时间窗口
        
        返回:
            各时间段的增长率
        """
        if not self.change_history:
            return []
        
        # 按时间排序
        sorted_changes = sorted(self.change_history, key=lambda c: c.time)
        
        # 统计每个时间点的新增边数
        time_counts = Counter()
        for change in sorted_changes:
            if change.type == "add":
                time_counts[change.time] += 1
        
        # 计算增长率
        times = sorted(time_counts.keys())
        rates = []
        
        for i, t in enumerate(times):
            count = time_counts[t]
            if i > 0:
                prev_t = times[i-1]
                time_diff = t - prev_t
                if time_diff > 0:
                    rate = count / time_diff
                    rates.append(rate)
        
        return rates
    
    def detect_entity_patterns(self, entity: str, 
                             pattern_length: int = 3) -> List[KGChange]:
        """
        检测实体的演变模式
        
        参数:
            entity: 实体
            pattern_length: 模式长度
        
        返回:
            发现的模式
        """
        events = self.get_entity_events(entity)
        
        if len(events) < pattern_length:
            return []
        
        # 简化：返回最后pattern_length个事件作为模式
        return events[-pattern_length:]


class EvolutionSimulator:
    """
    演变模拟器
    
    基于历史模式模拟未来演变
    """
    
    def __init__(self, evolution: KnowledgeGraphEvolution):
        self.evolution = evolution
        self.models = {}
    
    def train_model(self, entity_type: str):
        """
        训练演变模型
        
        参数:
            entity_type: 实体类型
        """
        # 收集同类实体的演变历史
        histories = []
        
        for entity, lifecycle in self.evolution.entity_lifecycles.items():
            if lifecycle.get("type") == entity_type:
                events = self.evolution.get_entity_events(entity)
                if events:
                    histories.append(events)
        
        if not histories:
            return
        
        # 简化：统计各谓词的出现频率
        predicate_freq = Counter()
        for history in histories:
            for event in history:
                predicate_freq[event.predicate] += 1
        
        self.models[entity_type] = {
            "predicate_freq": predicate_freq,
            "num_samples": len(histories)
        }
    
    def predict_next_change(self, entity: str, entity_type: str,
                           current_time: Any) -> Optional[KGChange]:
        """
        预测下一个变化
        
        参数:
            entity: 实体
            entity_type: 实体类型
            current_time: 当前时间
        
        返回:
            预测的变化
        """
        if entity_type not in self.models:
            return None
        
        model = self.models[entity_type]
        predicate_freq = model["predicate_freq"]
        
        if not predicate_freq:
            return None
        
        # 基于频率采样下一个谓词
        predicates = list(predicate_freq.keys())
        weights = [predicate_freq[p] for p in predicates]
        total = sum(weights)
        probs = [w / total for w in weights]
        
        # 随机选择
        idx = random.choices(range(len(predicates)), weights=probs)[0]
        predicted_predicate = predicates[idx]
        
        # 简化：假设宾语也是基于频率
        # 实际需要更复杂的模型
        predicted_object = entity + "_related"
        
        return KGChange(
            change_type="add",
            subject=entity,
            predicate=predicted_predicate,
            obj=predicted_object,
            time=current_time + 1
        )
    
    def simulate_evolution(self, entity: str, entity_type: str,
                          num_steps: int = 5,
                          start_time: Any = 2023) -> List[KGChange]:
        """
        模拟演变过程
        
        参数:
            entity: 实体
            entity_type: 实体类型
            num_steps: 模拟步数
            start_time: 开始时间
        
        返回:
            模拟的变化序列
        """
        if entity_type not in self.models:
            self.train_model(entity_type)
        
        changes = []
        current_time = start_time
        
        for _ in range(num_steps):
            change = self.predict_next_change(entity, entity_type, current_time)
            if change:
                changes.append(change)
                current_time = change.time + 1
        
        return changes


class KGStabilityAnalyzer:
    """
    知识图谱稳定性分析器
    
    分析图谱的稳定性和变化趋势
    """
    
    def __init__(self, evolution: KnowledgeGraphEvolution):
        self.evolution = evolution
    
    def compute_stability_score(self, entity: str) -> float:
        """
        计算实体的稳定性得分
        
        参数:
            entity: 实体
        
        返回:
            稳定性得分 (0-1, 越高越稳定)
        """
        events = self.evolution.get_entity_events(entity)
        
        if len(events) <= 1:
            return 1.0
        
        # 基于变化频率计算稳定性
        changes_per_time = len(events)
        
        # 简单：变化越少越稳定
        stability = 1.0 / (1.0 + changes_per_time)
        
        return stability
    
    def compute_graph_stability(self) -> float:
        """
        计算整个图谱的稳定性
        
        返回:
            平均稳定性得分
        """
        if not self.evolution.kg.entities:
            return 0.0
        
        total_stability = sum(
            self.compute_stability_score(e) 
            for e in self.evolution.kg.entities
        )
        
        return total_stability / len(self.evolution.kg.entities)
    
    def predict_stability_trend(self, future_time: Any) -> str:
        """
        预测稳定性趋势
        
        参数:
            future_time: 未来时间点
        
        返回:
            趋势描述 ("increasing", "decreasing", "stable")
        """
        current_stability = self.compute_graph_stability()
        
        # 简化：基于历史变化趋势预测
        growth_rates = self.evolution.compute_growth_rate()
        
        if not growth_rates:
            return "stable"
        
        recent_rates = growth_rates[-3:]  # 最近3个
        avg_recent = sum(recent_rates) / len(recent_rates)
        
        if avg_recent > 0.1:
            return "increasing"  # 变化增加
        elif avg_recent < -0.1:
            return "decreasing"  # 变化减少
        else:
            return "stable"


def analyze_evolution(kg, steps: int = 10) -> Dict[str, Any]:
    """
    分析知识图谱的演变
    
    参数:
        kg: 知识图谱
        steps: 分析步数
    
    返回:
        分析结果
    """
    evolution = KnowledgeGraphEvolution(kg)
    
    # 模拟演变
    for i in range(steps):
        # 随机添加一些边
        entities = list(kg.entities)
        if len(entities) >= 2:
            s, o = random.sample(entities, 2)
            p = random.choice(["related_to", "connected_to", "same_as"])
            evolution.add_change("add", s, p, o, 2020 + i)
    
    # 分析
    stability = KGStabilityAnalyzer(evolution)
    stability_score = stability.compute_graph_stability()
    trend = stability.predict_stability_trend(2030)
    
    return {
        "stability_score": stability_score,
        "trend": trend,
        "num_changes": len(evolution.change_history),
        "growth_rates": evolution.compute_growth_rate()
    }


if __name__ == "__main__":
    print("=== 知识图谱演变测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 创建初始TKG
    kg = TemporalKG("EvolutionKG")
    
    # 添加初始事实
    initial_facts = [
        ("CompanyA", "founded", "2010", 2010),
        ("CompanyA", "hired", "Alice", 2011),
        ("CompanyA", "hired", "Bob", 2012),
        ("Alice", "joined_team", "Engineering", 2011),
        ("Bob", "joined_team", "Sales", 2012),
    ]
    
    for s, p, o, t in initial_facts:
        kg.add_triple(s, p, o, t)
    
    print(f"初始TKG: {len(kg.triples)} 条事实")
    
    # 创建演变管理器
    evolution = KnowledgeGraphEvolution(kg)
    
    # 添加实体生命周期
    evolution.add_entity("CompanyA", "Organization", 2010)
    evolution.add_entity("Alice", "Person", 1985)
    evolution.add_entity("Bob", "Person", 1988)
    
    # 模拟演变
    print("\n模拟演变:")
    for i in range(5):
        entities = list(kg.entities)
        if len(entities) >= 2:
            s, o = random.sample(entities, 2)
            evolution.add_change("add", s, "collaborates_with", o, 2015 + i)
            print(f"  添加: {s} --collaborates_with--> {o} @ {2015+i}")
    
    # 增长率
    print("\n增长分析:")
    growth_rates = evolution.compute_growth_rate()
    print(f"  增长率: {growth_rates}")
    
    # 演变模式检测
    print("\n演变模式检测:")
    for entity in ["CompanyA", "Alice"]:
        pattern = evolution.detect_entity_patterns(entity, pattern_length=3)
        print(f"  {entity} 的模式: {len(pattern)} 个事件")
    
    # 演变模拟
    print("\n演变模拟:")
    simulator = EvolutionSimulator(evolution)
    simulator.train_model("Person")
    
    simulated = simulator.simulate_evolution("Alice", "Person", num_steps=3, start_time=2020)
    for change in simulated:
        print(f"  预测: {change}")
    
    # 稳定性分析
    print("\n稳定性分析:")
    analyzer = KGStabilityAnalyzer(evolution)
    stability_score = analyzer.compute_graph_stability()
    print(f"  图谱稳定性得分: {stability_score:.4f}")
    
    trend = analyzer.predict_stability_trend(2030)
    print(f"  2030年稳定性趋势: {trend}")
    
    print("\n=== 测试完成 ===")

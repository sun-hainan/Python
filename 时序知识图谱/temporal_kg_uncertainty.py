"""
时序知识图谱不确定性建模 (Temporal KG Uncertainty)
================================================
建模时序知识图谱中的不确定性，包括时间不确定性和事实不确定性。

主题：
1. 时间不确定性：事件时间不精确
2. 事实不确定性：事实本身的置信度
3. 概率时序推理：基于概率的时序推断

参考：
    - Probabilistic Temporal Knowledge Graphs.
    - Uncertainty in Knowledge Graphs.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import random
import math


class UncertainTriple:
    """不确定性三元组"""
    def __init__(self, subject: str, predicate: str, obj: str,
                 time_start: Any, time_end: Optional[Any] = None,
                 confidence: float = 1.0, time_uncertainty: float = 0.0):
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.time_start = time_start
        self.time_end = time_end if time_end is not None else time_start
        self.confidence = confidence  # 事实置信度
        self.time_uncertainty = time_uncertainty  # 时间不确定性（标准差）
    
    def __str__(self):
        return (f"({self.subject}--{self.predicate}--{self.obj} @ "
                f"[{self.time_start}, {self.time_end}] "
                f"conf={self.confidence:.2f})")


class TemporalProbabilityDistribution:
    """时间概率分布"""
    
    def __init__(self, mean: float, std: float = 0.0, 
                 distribution_type: str = "normal"):
        self.mean = mean
        self.std = std
        self.type = distribution_type
    
    def sample(self) -> float:
        """从分布中采样"""
        if self.type == "normal":
            return random.gauss(self.mean, self.std)
        elif self.type == "uniform":
            return random.uniform(self.mean - self.std, self.mean + self.std)
        elif self.type == "point":
            return self.mean
        else:
            return self.mean
    
    def probability(self, t: float) -> float:
        """计算时间点t的概率密度"""
        if self.type == "normal":
            if self.std == 0:
                return 1.0 if t == self.mean else 0.0
            # 正态分布概率密度
            coeff = 1.0 / (self.std * math.sqrt(2 * math.pi))
            exp_term = -0.5 * ((t - self.mean) / self.std) ** 2
            return coeff * math.exp(exp_term)
        elif self.type == "uniform":
            if abs(t - self.mean) <= self.std:
                return 1.0 / (2 * self.std)
            return 0.0
        else:
            return 1.0 if t == self.mean else 0.0


class UncertainTemporalKG:
    """
    不确定性时序知识图谱
    
    参数:
        name: 图谱名称
    """
    
    def __init__(self, name: str = "UncertainTKG"):
        self.name = name
        self.uncertain_triples = []  # UncertainTriple列表
        self.entity_confidences = defaultdict(float)  # 实体置信度
    
    def add_uncertain_fact(self, s: str, p: str, o: str,
                          time_start: Any, time_end: Any = None,
                          confidence: float = 1.0,
                          time_std: float = 0.0):
        """
        添加不确定性事实
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
            time_start: 开始时间
            time_end: 结束时间
            confidence: 置信度
            time_std: 时间标准差
        """
        triple = UncertainTriple(s, p, o, time_start, time_end, 
                                 confidence, time_std)
        self.uncertain_triples.append(triple)
        
        # 更新实体置信度
        self.entity_confidences[s] = max(self.entity_confidences[s], confidence)
        self.entity_confidences[o] = max(self.entity_confidences[o], confidence)
    
    def get_confidence(self, s: str, p: str, o: str) -> float:
        """获取三元组的置信度"""
        for triple in self.uncertain_triples:
            if (triple.subject == s and triple.predicate == p 
                and triple.obj == o):
                return triple.confidence
        return 0.0
    
    def get_time_distribution(self, s: str, p: str, o: str) -> Optional[TemporalProbabilityDistribution]:
        """获取时间分布"""
        for triple in self.uncertain_triples:
            if (triple.subject == s and triple.predicate == p 
                and triple.obj == o):
                return TemporalProbabilityDistribution(
                    mean=triple.time_start,
                    std=triple.time_uncertainty,
                    distribution_type="normal" if triple.time_uncertainty > 0 else "point"
                )
        return None
    
    def query_by_confidence(self, threshold: float) -> List[UncertainTriple]:
        """
        查询置信度高于阈值的三元组
        
        参数:
            threshold: 置信度阈值
        
        返回:
            三元组列表
        """
        return [t for t in self.uncertain_triples if t.confidence >= threshold]
    
    def expected_time(self, s: str, p: str, o: str, 
                     num_samples: int = 100) -> float:
        """
        计算期望时间（通过采样）
        
        参数:
            s, p, o: 三元组
            num_samples: 采样次数
        
        返回:
            期望时间
        """
        dist = self.get_time_distribution(s, p, o)
        if dist is None:
            return 0.0
        
        samples = [dist.sample() for _ in range(num_samples)]
        return sum(samples) / num_samples


class ProbabilisticTemporalReasoner:
    """
    概率时序推理器
    
    参数:
        uncertain_kg: 不确定性TKG
    """
    
    def __init__(self, uncertain_kg: UncertainTemporalKG):
        self.kg = uncertain_kg
    
    def infer_confidence(self, s: str, p: str, o: str, t: Any) -> float:
        """
        推断置信度
        
        基于相关事实的置信度
        
        参数:
            s, p, o, t: 查询
        
        返回:
            推断的置信度
        """
        # 方法：基于传递性
        # 如果 A--p1-->B 和 B--p2-->C 存在
        # 则 A--p3-->C 的置信度 = conf(A--p1-->B) * conf(B--p2-->C)
        
        # 简化：直接返回存储的置信度
        return self.kg.get_confidence(s, p, o)
    
    def propagate_confidence(self) -> Dict[str, float]:
        """
        置信度传播
        
        返回:
            更新的实体置信度
        """
        # 多次迭代直到收敛
        max_iterations = 10
        
        for _ in range(max_iterations):
            prev_conf = dict(self.kg.entity_confidences)
            
            # 对每个三元组更新置信度
            for triple in self.kg.uncertain_triples:
                # 主语置信度受所有以它为宾语的fact影响
                for t in self.kg.uncertain_triples:
                    if t.obj == triple.subject:
                        new_conf = t.confidence * self.kg.entity_confidences[t.subject]
                        self.kg.entity_confidences[triple.subject] = max(
                            self.kg.entity_confidences[triple.subject],
                            new_conf
                        )
            
            # 检查收敛
            if prev_conf == self.kg.entity_confidences:
                break
        
        return dict(self.kg.entity_confidences)


class TemporalUncertaintyReasoning:
    """
    时序不确定性推理
    
    处理时间不确定性的推理
    """
    
    def __init__(self, uncertain_kg: UncertainTemporalKG):
        self.kg = uncertain_kg
    
    def temporal_overlap_probability(self, t1: Tuple, t2: Tuple) -> float:
        """
        计算两个时间区间重叠的概率
        
        参数:
            t1: 时间区间1 (start1, end1)
            t2: 时间区间2 (start2, end2)
        
        返回:
            重叠概率
        """
        # 简化为：区间越接近重叠概率越高
        if isinstance(t1[0], TemporalProbabilityDistribution):
            mean1 = t1[0].mean
        else:
            mean1 = (t1[0] + t1[1]) / 2 if isinstance(t1[0], (int, float)) else 0
        
        if isinstance(t2[0], TemporalProbabilityDistribution):
            mean2 = t2[0].mean
        else:
            mean2 = (t2[0] + t2[1]) / 2 if isinstance(t2[0], (int, float)) else 0
        
        # 重叠概率 = 1 / (1 + |mean1 - mean2|)
        return 1.0 / (1.0 + abs(mean1 - mean2))
    
    def infer_temporal_relation(self, s1: str, p1: str, o1: str,
                                s2: str, p2: str, o2: str) -> Dict[str, float]:
        """
        推断两个事实的时序关系
        
        参数:
            事实1: (s1, p1, o1)
            事实2: (s2, p2, o2)
        
        返回:
            各时序关系的概率
        """
        dist1 = self.kg.get_time_distribution(s1, p1, o1)
        dist2 = self.kg.get_time_distribution(s2, p2, o2)
        
        if dist1 is None or dist2 is None:
            return {"UNKNOWN": 1.0}
        
        # 采样计算概率
        num_samples = 1000
        before_count = 0
        after_count = 0
        simultaneous_count = 0
        
        for _ in range(num_samples):
            t1 = dist1.sample()
            t2 = dist2.sample()
            
            if t1 < t2 - 0.5:  # 允许小的容差
                before_count += 1
            elif t2 < t1 - 0.5:
                after_count += 1
            else:
                simultaneous_count += 1
        
        n = num_samples
        return {
            "BEFORE": before_count / n,
            "AFTER": after_count / n,
            "SIMULTANEOUS": simultaneous_count / n,
        }
    
    def predict_time_range(self, s: str, p: str, o: str) -> Tuple[Any, Any]:
        """
        预测时间范围（考虑不确定性）
        
        参数:
            s, p, o: 三元组
        
        返回:
            (预测开始时间, 预测结束时间)
        """
        dist = self.kg.get_time_distribution(s, p, o)
        
        if dist is None:
            return (None, None)
        
        # 95%置信区间
        if dist.type == "normal":
            start = dist.mean - 2 * dist.std
            end = dist.mean + 2 * dist.std
        else:
            start = dist.mean
            end = dist.mean
        
        return (start, end)


class UncertaintyAwareQueryEngine:
    """
    不确定性感知查询引擎
    
    参数:
        uncertain_kg: 不确定性TKG
    """
    
    def __init__(self, uncertain_kg: UncertainTemporalKG):
        self.kg = uncertain_kg
        self.reasoner = ProbabilisticTemporalReasoner(uncertain_kg)
    
    def query_with_confidence_threshold(self, s: str, p: str, o: str,
                                       confidence_threshold: float = 0.5) -> bool:
        """
        带置信度阈值的查询
        
        参数:
            s, p, o: 三元组
            confidence_threshold: 阈值
        
        返回:
            是否满足条件
        """
        conf = self.reasoner.infer_confidence(s, p, o, None)
        return conf >= confidence_threshold
    
    def query_with_time_constraint(self, s: str, p: str, o: str,
                                   t_start: Any, t_end: Any,
                                   probability_threshold: float = 0.5) -> bool:
        """
        带时间约束的查询
        
        参数:
            s, p, o: 三元组
            t_start, t_end: 时间约束
            probability_threshold: 概率阈值
        
        返回:
            是否满足条件
        """
        dist = self.kg.get_time_distribution(s, p, o)
        
        if dist is None:
            return False
        
        # 计算概率
        prob = 0.0
        for t in range(int(t_start), int(t_end) + 1):
            prob += dist.probability(t)
        
        return prob >= probability_threshold
    
    def ranked_query(self, predicate: str, time_constraint: Optional[Tuple] = None,
                    top_k: int = 10) -> List[Tuple[str, float]]:
        """
        排序查询
        
        参数:
            predicate: 谓词
            time_constraint: 时间约束
            top_k: 返回前k个
        
        返回:
            [(宾语, 置信度), ...]
        """
        candidates = []
        
        for triple in self.kg.uncertain_triples:
            if triple.predicate != predicate:
                continue
            
            # 检查时间约束
            if time_constraint:
                t_start, t_end = time_constraint
                if not (t_start <= triple.time_start <= t_end or
                       t_start <= triple.time_end <= t_end):
                    continue
            
            candidates.append((triple.obj, triple.confidence))
        
        # 排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]


def compute_kg_quality_score(uncertain_kg: UncertainTemporalKG) -> Dict[str, float]:
    """
    计算知识图谱质量得分
    
    参数:
        uncertain_kg: 不确定性TKG
    
    返回:
        质量指标
    """
    if not uncertain_kg.uncertain_triples:
        return {"avg_confidence": 0.0, "completeness": 0.0}
    
    # 平均置信度
    confidences = [t.confidence for t in uncertain_kg.uncertain_triples]
    avg_confidence = sum(confidences) / len(confidences)
    
    # 时间完整性（有时间不确定性的比例）
    uncertain_time = sum(1 for t in uncertain_kg.uncertain_triples 
                        if t.time_uncertainty > 0)
    time_completeness = 1.0 - (uncertain_time / len(uncertain_kg.uncertain_triples))
    
    # 实体覆盖率
    all_entities = set()
    for t in uncertain_kg.uncertain_triples:
        all_entities.add(t.subject)
        all_entities.add(t.obj)
    
    entity_confidences = [uncertain_kg.entity_confidences[e] 
                          for e in all_entities]
    avg_entity_conf = sum(entity_confidences) / max(len(entity_confidences), 1)
    
    return {
        "avg_confidence": avg_confidence,
        "time_completeness": time_completeness,
        "entity_confidence": avg_entity_conf,
        "num_triples": len(uncertain_kg.uncertain_triples),
        "num_entities": len(all_entities),
    }


if __name__ == "__main__":
    print("=== 时序知识图谱不确定性建模测试 ===")
    
    # 创建不确定性TKG
    kg = UncertainTemporalKG("UncertainKG")
    
    # 添加不确定性事实
    facts = [
        ("Alice", "born_in", "Paris", 1990, None, 0.95, 1.0),  # 年份有±1不确定性
        ("Alice", "graduated_from", "MIT", 2012, None, 0.90, 0.5),
        ("Alice", "joined", "CompanyX", 2015, None, 0.85, 0.0),  # 精确时间
        ("CompanyX", "founded", "2010", 2010, None, 0.80, 2.0),  # 年份不确定±2年
        ("Alice", "married_to", "Bob", 2018, None, 0.75, 0.0),
    ]
    
    for s, p, o, t_start, t_end, conf, time_std in facts:
        kg.add_uncertain_fact(s, p, o, t_start, t_end, conf, time_std)
    
    print("\n不确定性TKG:")
    for triple in kg.uncertain_triples:
        print(f"  {triple}")
    
    # 置信度查询
    print("\n置信度查询:")
    conf = kg.get_confidence("Alice", "born_in", "Paris")
    print(f"  Alice born_in Paris confidence: {conf:.2f}")
    
    # 时间分布
    print("\n时间分布:")
    dist = kg.get_time_distribution("Alice", "born_in", "Paris")
    if dist:
        samples = [dist.sample() for _ in range(5)]
        print(f"  采样时间: {[f'{s:.1f}' for s in samples]}")
    
    # 期望时间
    print("\n期望时间计算:")
    expected = kg.expected_time("Alice", "born_in", "Paris", num_samples=1000)
    print(f"  期望出生年: {expected:.1f}")
    
    # 概率时序推理
    print("\n概率时序推理:")
    reasoner = ProbabilisticTemporalReasoner(kg)
    propagated = reasoner.propagate_confidence()
    print(f"  传播后实体置信度:")
    for entity, conf in propagated.items():
        print(f"    {entity}: {conf:.3f}")
    
    # 时序不确定性推理
    print("\n时序关系推断:")
    temp_reasoner = TemporalUncertaintyReasoning(kg)
    relations = temp_reasoner.infer_temporal_relation(
        "Alice", "born_in", "Paris",
        "Alice", "graduated_from", "MIT"
    )
    print(f"  Alice出生 vs Alice毕业 的时序关系:")
    for rel, prob in relations.items():
        print(f"    {rel}: {prob:.3f}")
    
    # 不确定性感知查询
    print("\n不确定性感知查询:")
    query_engine = UncertaintyAwareQueryEngine(kg)
    
    result = query_engine.query_with_confidence_threshold(
        "Alice", "born_in", "Paris", confidence_threshold=0.9
    )
    print(f"  置信度>0.9查询: {'满足' if result else '不满足'}")
    
    # 排序查询
    ranked = query_engine.ranked_query("born_in", top_k=3)
    print(f"  born_in 排序查询结果: {ranked}")
    
    # 质量评估
    print("\n知识图谱质量评估:")
    quality = compute_kg_quality_score(kg)
    for metric, value in quality.items():
        if isinstance(value, float):
            print(f"  {metric}: {value:.4f}")
        else:
            print(f"  {metric}: {value}")
    
    print("\n=== 测试完成 ===")

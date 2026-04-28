"""
时序知识图谱富化 (Temporal KG Enrichment)
========================================
实现时序知识图谱的富化，包括时间感知实体表示和时间信息补全。

任务：
1. 时间信息补全：为缺失时间的三元组推断时间
2. 时间感知表示：学习实体的时序嵌入
3. 时序事实推断：推断新的时序事实

参考：
    - TEMP: Temporal Knowledge Graph Embeddings.
    - Time-aware Entity Embeddings for KG Completion.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
import random
import math


class TemporalEntityRepresentation:
    """
    时间感知实体表示
    
    参数:
        embedding_dim: 嵌入维度
        time_dim: 时间嵌入维度
    """
    
    def __init__(self, embedding_dim: int = 64, time_dim: int = 16):
        self.embedding_dim = embedding_dim
        self.time_dim = time_dim
        
        # 实体嵌入
        self.entity_embeddings = {}
        # 时间嵌入
        self.time_embeddings = {}
    
    def initialize_entity(self, entity: str, init_type: str = "random"):
        """初始化实体嵌入"""
        if init_type == "random":
            scale = 0.1
            self.entity_embeddings[entity] = [
                random.gauss(0, scale) for _ in range(self.embedding_dim)
            ]
        elif init_type == "zeros":
            self.entity_embeddings[entity] = [0.0] * self.embedding_dim
    
    def initialize_time(self, time: Any, init_type: str = "random"):
        """初始化时间嵌入"""
        time_key = int(time) if isinstance(time, (int, float)) else hash(time) % 1000
        
        if init_type == "random":
            scale = 0.1
            self.time_embeddings[time_key] = [
                random.gauss(0, scale) for _ in range(self.time_dim)
            ]
        elif init_type == "sinusoidal":
            # 正弦时间编码
            self.time_embeddings[time_key] = self._sinusoidal_encoding(time_key)
    
    def _sinusoidal_encoding(self, time: int, max_time: int = 10000) -> List[float]:
        """正弦时间编码"""
        encoding = []
        
        for i in range(self.time_dim):
            if i % 2 == 0:
                encoding.append(math.sin(time / (max_time ** (2 * i / self.time_dim))))
            else:
                encoding.append(math.cos(time / (max_time ** (2 * i / self.time_dim))))
        
        return encoding
    
    def get_entity_embedding(self, entity: str, time: Optional[Any] = None) -> List[float]:
        """
        获取实体在特定时间的嵌入
        
        参数:
            entity: 实体
            time: 时间（可选）
        
        返回:
            嵌入向量
        """
        if entity not in self.entity_embeddings:
            self.initialize_entity(entity)
        
        base_emb = self.entity_embeddings[entity]
        
        if time is None:
            return base_emb
        
        # 时间感知嵌入
        time_key = int(time) if isinstance(time, (int, float)) else hash(time) % 1000
        
        if time_key not in self.time_embeddings:
            self.initialize_time(time_key)
        
        time_emb = self.time_embeddings[time_key]
        
        # 组合：基础嵌入 + 时间调制
        combined = [
            base_emb[i] * (1.0 + time_emb[i % self.time_dim] * 0.1)
            for i in range(self.embedding_dim)
        ]
        
        return combined


class TemporalFactCompleter:
    """
    时序事实补全器
    
    参数:
        kg: 时序知识图谱
        representations: 实体表示
    """
    
    def __init__(self, kg, representations: TemporalEntityRepresentation):
        self.kg = kg
        self.rep = representations
    
    def infer_missing_time(self, s: str, p: str, o: str) -> Optional[Any]:
        """
        推断缺失的时间
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
        
        返回:
            推断的时间
        """
        # 方法1：基于上下文实体的平均时间
        s_times = []
        o_times = []
        
        # 获取s的邻居时间
        for neighbor, pred, time in self.kg.get_temporal_neighbors(s):
            if pred == p:
                s_times.append(time)
        
        # 获取o的邻居时间
        for neighbor, pred, time in self.kg.get_temporal_neighbors(o):
            if pred == p:
                o_times.append(time)
        
        # 取交集或平均
        all_times = s_times + o_times
        
        if all_times:
            return sum(all_times) / len(all_times)
        
        return None
    
    def infer_missing_entity(self, p: str, o: str, t: Any) -> List[Tuple[str, float]]:
        """
        推断缺失的主语
        
        参数:
            p: 谓词
            o: 宾语
            t: 时间
        
        返回:
            [(实体, 得分), ...]
        """
        scores = []
        
        for entity in self.kg.entities:
            if entity == o:
                continue
            
            # 计算相似度
            emb_s = self.rep.get_entity_embedding(entity, t)
            emb_o = self.rep.get_entity_embedding(o, t)
            
            # 点积相似度
            score = sum(a * b for a, b in zip(emb_s, emb_o))
            scores.append((entity, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:10]
    
    def enrich_with_temporal_context(self) -> int:
        """
        使用时序上下文富化图谱
        
        返回:
            富化的三元组数
        """
        enriched = 0
        
        # 对每个没有时间的三元组推断时间
        for (s, p, o), intervals in self.kg.triples.items():
            if not intervals or intervals[0][0] is None:
                inferred_time = self.infer_missing_time(s, p, o)
                if inferred_time:
                    self.kg.add_triple(s, p, o, inferred_time)
                    enriched += 1
        
        return enriched


class TemporalPatternEnricher:
    """
    时序模式富化
    
    挖掘和推断时序模式
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.patterns = defaultdict(int)
    
    def mine_temporal_patterns(self, min_support: int = 2) -> Dict[str, int]:
        """
        挖掘时序模式
        
        参数:
            min_support: 最小支持度
        
        返回:
            模式字典
        """
        # 谓词语义模式
        predicate_times = defaultdict(list)
        
        for (s, p, o), intervals in self.kg.triples.items():
            for t_start, t_end in intervals:
                predicate_times[p].append((t_start, t_end))
        
        # 分析谓词的时间模式
        for pred, times in predicate_times.items():
            durations = [t_end - t_start for t_start, t_end in times]
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                
                # 模式：持续时间
                if avg_duration < 1:
                    self.patterns[f"{pred}_momentary"] = len(times)
                elif avg_duration < 30:
                    self.patterns[f"{pred}_short_term"] = len(times)
                else:
                    self.patterns[f"{pred}_long_term"] = len(times)
        
        # 过滤
        return {k: v for k, v in self.patterns.items() if v >= min_support}
    
    def apply_temporal_patterns(self, s: str, p: str, o: str, 
                              t_start: Any, t_end: Any) -> List[Tuple]:
        """
        应用时序模式推断新事实
        
        参数:
            s, p, o, t_start, t_end: 三元组及时间
        
        返回:
            推断的事实列表
        """
        inferred = []
        
        # 基于谓词的时间模式推断
        if p in self.patterns:
            for pattern, support in self.patterns.items():
                if pattern.startswith(p):
                    if "momentary" in pattern:
                        # 瞬时事实：只持续一瞬间
                        inferred.append((s, p, o, t_start, t_start))
                    elif "short_term" in pattern:
                        # 短时事实：持续一段时间
                        if t_end - t_start < 1:
                            inferred.append((s, p, o, t_start, t_start + 7))  # 假设7天
                    # long_term 不需要调整
        
        return inferred


class TemporalConsistencyEnricher:
    """
    时序一致性富化
    
    检测和修复时序不一致
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.inconsistencies = []
    
    def detect_inconsistencies(self) -> List[Dict]:
        """
        检测时序不一致
        
        返回:
            不一致列表
        """
        inconsistencies = []
        
        for entity in self.kg.entities:
            # 获取实体的所有关系时间
            relation_times = defaultdict(list)
            
            for neighbor, pred, time in self.kg.get_temporal_neighbors(entity):
                relation_times[pred].append(time)
            
            # 检查某些互斥关系
            for (s, p, o), intervals in self.kg.triples.items():
                if s != entity:
                    continue
                
                # 例如：如果实体同时在不同地方
                if p in ["located_in", "at"]:
                    for t_start, t_end in intervals:
                        # 检查重叠
                        for (s2, p2, o2), intervals2 in self.kg.triples.items():
                            if s2 != entity or p2 != p:
                                continue
                            
                            for t2_start, t2_end in intervals2:
                                if o != o2 and self._overlaps(t_start, t_end, t2_start, t2_end):
                                    inconsistencies.append({
                                        "entity": entity,
                                        "fact1": (s, p, o, t_start, t_end),
                                        "fact2": (s2, p2, o2, t2_start, t2_end),
                                        "type": "spatial_exclusion_violated"
                                    })
        
        self.inconsistencies = inconsistencies
        return inconsistencies
    
    def _overlaps(self, s1: Any, e1: Any, s2: Any, e2: Any) -> bool:
        """检查时间区间是否重叠"""
        return s1 <= e2 and s2 <= e1
    
    def resolve_inconsistencies(self) -> int:
        """
        解决不一致（简化：删除冲突事实）
        
        返回:
            解决的数量
        """
        resolved = 0
        
        for incons in self.inconsistencies:
            # 简化策略：保留时间更早的事实
            fact1_time = incons["fact1"][3]
            fact2_time = incons["fact2"][3]
            
            if fact1_time > fact2_time:
                # 删除fact1
                s, p, o = incons["fact1"][:3]
                if (s, p, o) in self.kg.triples:
                    del self.kg.triples[(s, p, o)]
                    resolved += 1
        
        return resolved


def temporal_enrichment_pipeline(kg) -> Dict[str, Any]:
    """
    时序富化流程
    
    参数:
        kg: 时序知识图谱
    
    返回:
        富化结果
    """
    # 初始化表示
    rep = TemporalEntityRepresentation(embedding_dim=32, time_dim=8)
    
    # 初始化所有实体和时间
    for entity in kg.entities:
        rep.initialize_entity(entity)
    
    for time in range(kg.time_range[0] or 0, (kg.time_range[1] or 2000) + 1):
        rep.initialize_time(time)
    
    # 事实补全
    completer = TemporalFactCompleter(kg, rep)
    enriched_count = completer.enrich_with_temporal_context()
    
    # 模式挖掘
    pattern_enricher = TemporalPatternEnricher(kg)
    patterns = pattern_enricher.mine_temporal_patterns()
    
    # 一致性检测
    consistency_enricher = TemporalConsistencyEnricher(kg)
    inconsistencies = consistency_enricher.detect_inconsistencies()
    
    return {
        "enriched_triples": enriched_count,
        "patterns_discovered": len(patterns),
        "inconsistencies_found": len(inconsistencies),
        "resolved": consistency_enricher.resolve_inconsistencies()
    }


if __name__ == "__main__":
    print("=== 时序知识图谱富化测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 构建测试TKG
    kg = TemporalKG()
    
    facts = [
        ("Alice", "works_at", "CompanyA", 2018),
        ("Alice", "works_at", "CompanyB", 2020, 2022),
        ("Alice", "married_to", "Bob", 2019),
        ("Bob", "works_at", "CompanyA", 2019),
        ("CompanyA", "acquired_by", "CompanyZ", 2021),
        # 缺失时间的三元组
        ("Alice", "visited", "Paris", None),
    ]
    
    for f in facts:
        if len(f) == 4:
            if f[3] is not None:
                kg.add_triple(f[0], f[1], f[2], f[3])
            else:
                # 手动添加无时间的事实
                kg.entities.add(f[0])
                kg.entities.add(f[2])
                kg.predicates.add(f[1])
        else:
            kg.add_fact(f[0], f[1], f[2], f[3], f[4])
    
    print(f"初始TKG: {len(kg.triples)} 条事实")
    
    # 时序富化流程
    print("\n运行时序富化流程...")
    results = temporal_enrichment_pipeline(kg)
    
    print("\n富化结果:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    # 时间感知表示
    print("\n时间感知表示:")
    rep = TemporalEntityRepresentation(embedding_dim=8, time_dim=4)
    
    emb_2018 = rep.get_entity_embedding("Alice", 2018)
    emb_2020 = rep.get_entity_embedding("Alice", 2020)
    emb_none = rep.get_entity_embedding("Alice")
    
    print(f"  Alice@2018: {[f'{x:.3f}' for x in emb_2018]}")
    print(f"  Alice@2020: {[f'{x:.3f}' for x in emb_2020]}")
    print(f"  Alice@none: {[f'{x:.3f}' for x in emb_none]}")
    
    # 时序一致性检测
    print("\n时序一致性检测:")
    consistency = TemporalConsistencyEnricher(kg)
    incons = consistency.detect_inconsistencies()
    print(f"  发现 {len(incons)} 个不一致")
    
    print("\n=== 测试完成 ===")

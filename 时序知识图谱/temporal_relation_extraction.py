"""
时序关系抽取 (Temporal Relation Extraction)
==========================================
从文本中抽取时序关系并构建时序知识图谱。

任务：
1. 实体识别：从文本中识别实体
2. 关系抽取：识别实体间的关系
3. 时间抽取：识别事件时间
4. 时序关系：确定事件的时间顺序

方法：
- 基于规则的方法
- 监督学习方法
- 远程监督方法

参考：
    - Temporal Relation Extraction (ACE TREC).
    - SemEval-2018 Task 6: Information Extraction.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
import re


class Entity:
    """实体"""
    def __init__(self, text: str, entity_type: str, 
                 start_pos: int, end_pos: int):
        self.text = text
        self.type = entity_type
        self.start = start_pos
        self.end = end_pos
    
    def __str__(self):
        return f"Entity({self.text}, {self.type}, {self.start}-{self.end})"


class TimeExpression:
    """时间表达式"""
    def __init__(self, text: str, value: Any, 
                 start_pos: int, end_pos: int):
        self.text = text
        self.value = value  # 标准化后的时间值
        self.start = start_pos
        self.end = end_pos
    
    def __str__(self):
        return f"Time({self.text}, {self.value})"


class TemporalRelation:
    """时序关系类型"""
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    INCLUDES = "INCLUDES"
    IS_INCLUDED = "IS_INCLUDED"
    SIMULTANEOUS = "SIMULTANEOUS"
    OVERLAP = "OVERLAP"


class TemporalRelationExtractor:
    """
    时序关系抽取器
    
    参数:
        use_rules: 是否使用规则
    """
    
    def __init__(self, use_rules: bool = True):
        self.use_rules = use_rules
        self.entity_patterns = self._build_entity_patterns()
        self.time_patterns = self._build_time_patterns()
        self.relation_patterns = self._build_relation_patterns()
    
    def _build_entity_patterns(self) -> Dict[str, re.Pattern]:
        """构建实体识别模式"""
        patterns = {
            "PERSON": re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)\b"),
            "ORGANIZATION": re.compile(r"\b([A-Z][a-z]*(?: Inc|Corp|Ltd)?)\b"),
            "LOCATION": re.compile(r"\b(?:in|at) ([A-Z][a-z]+)\b"),
            "DATE": re.compile(r"\b(\d{4})\b"),
        }
        return patterns
    
    def _build_time_patterns(self) -> List[Tuple[str, re.Pattern]]:
        """构建时间表达式识别模式"""
        patterns = [
            ("YEAR", re.compile(r"\b(19|20)\d{2}\b")),
            ("MONTH_YEAR", re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (19|20)\d{2}\b")),
            ("DATE", re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")),
        ]
        return patterns
    
    def _build_relation_patterns(self) -> Dict[str, re.Pattern]:
        """构建关系抽取模式"""
        patterns = {
            "born_in": re.compile(r"\b(\w+) was born in (\w+) in (\d{4})\b", re.IGNORECASE),
            "founded": re.compile(r"\b(\w+) founded (\w+) in (\d{4})\b", re.IGNORECASE),
            "joined": re.compile(r"\b(\w+) joined (\w+) in (\d{4})\b", re.IGNORECASE),
            "married": re.compile(r"\b(\w+) married (\w+) in (\d{4})\b", re.IGNORECASE),
            "acquired": re.compile(r"\b(\w+) acquired (\w+) in (\d{4})\b", re.IGNORECASE),
            "released": re.compile(r"\b(\w+) released (\w+) in (\d{4})\b", re.IGNORECASE),
        }
        return patterns
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        从文本抽取实体
        
        参数:
            text: 输入文本
        
        返回:
            实体列表
        """
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            for match in pattern.finditer(text):
                entity = Entity(
                    text=match.group(1),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def extract_time_expressions(self, text: str) -> List[TimeExpression]:
        """
        从文本抽取时间表达式
        
        参数:
            text: 输入文本
        
        返回:
            时间表达式列表
        """
        times = []
        
        for time_type, pattern in self.time_patterns:
            for match in pattern.finditer(text):
                if time_type == "YEAR":
                    value = int(match.group(1))
                elif time_type == "MONTH_YEAR":
                    value = match.group(0)
                else:
                    value = match.group(0)
                
                time_expr = TimeExpression(
                    text=match.group(0),
                    value=value,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                times.append(time_expr)
        
        return times
    
    def extract_relations(self, text: str) -> List[Tuple[str, str, str, Any]]:
        """
        从文本抽取关系三元组
        
        参数:
            text: 输入文本
        
        返回:
            (主语, 谓词, 宾语, 时间) 列表
        """
        triplets = []
        
        for relation_type, pattern in self.relation_patterns.items():
            for match in pattern.finditer(text):
                groups = match.groups()
                
                if len(groups) >= 3:
                    s, o, t = groups[0], groups[1], groups[2]
                    time_value = int(t) if t.isdigit() else None
                    
                    triplets.append((s, relation_type, o, time_value))
        
        return triplets
    
    def extract_temporal_relations(self, text: str) -> List[Dict]:
        """
        抽取时序关系（事件之间的时间顺序）
        
        参数:
            text: 输入文本
        
        返回:
            时序关系列表
        """
        temporal_relations = []
        
        # 抽取事件
        events = self.extract_relations(text)
        
        if len(events) < 2:
            return temporal_relations
        
        # 排序
        events_with_time = [(e[0], e[1], e[2], e[3]) for e in events if e[3] is not None]
        events_with_time.sort(key=lambda x: x[3])
        
        # 建立时序关系
        for i in range(len(events_with_time) - 1):
            e1 = events_with_time[i]
            e2 = events_with_time[i + 1]
            
            if e1[3] < e2[3]:
                relation = {
                    "event1": (e1[0], e1[1], e1[2]),
                    "relation": TemporalRelation.BEFORE,
                    "event2": (e2[0], e2[1], e2[2]),
                    "time1": e1[3],
                    "time2": e2[3]
                }
            else:
                relation = {
                    "event1": (e1[0], e1[1], e1[2]),
                    "relation": TemporalRelation.OVERLAP,
                    "event2": (e2[0], e2[1], e2[2]),
                    "time1": e1[3],
                    "time2": e2[3]
                }
            
            temporal_relations.append(relation)
        
        return temporal_relations


class DistantSupervisionExtractor:
    """
    远程监督关系抽取
    
    利用已有知识图谱作为远程监督信号
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.entity_aliases = defaultdict(set)
    
    def build_aliases(self):
        """从KG构建实体别名"""
        for entity in self.kg.entities:
            # 添加实体本身
            self.entity_aliases[entity.lower()].add(entity)
            
            # 添加部分匹配
            parts = entity.split()
            for part in parts:
                if len(part) > 2:
                    self.entity_aliases[part.lower()].add(entity)
    
    def extract_from_text(self, text: str) -> List[Tuple[str, str, str, Optional[int]]]:
        """
        从文本抽取三元组（使用KG监督）
        
        参数:
            text: 输入文本
        
        返回:
            三元组列表
        """
        triplets = []
        
        # 查找KG中实体的提及
        for entity in self.kg.entities:
            if entity.lower() in text.lower():
                # 找到实体提及
                # 查找相关关系
                neighbors = self.kg.get_temporal_neighbors(entity)
                
                for neighbor, pred, time in neighbors:
                    if neighbor.lower() in text.lower():
                        triplets.append((entity, pred, neighbor, time))
        
        return triplets


class TemporalEventDetector:
    """
    时序事件检测
    
    检测文本中的事件并建立时序
    """
    
    def __init__(self):
        self.event_keywords = {
            "founded": 2010,
            "released": 2015,
            "acquired": 2018,
            "merged": 2020,
            "IPO": 2019,
            "launched": 2016,
            "joined": 2012,
            "left": 2018,
            "promoted": 2020,
        }
    
    def detect_events(self, text: str) -> List[Dict]:
        """
        检测事件
        
        参数:
            text: 输入文本
        
        返回:
            事件列表
        """
        events = []
        
        # 基于关键词检测
        text_lower = text.lower()
        
        for keyword, default_year in self.event_keywords.items():
            if keyword in text_lower:
                # 尝试提取时间
                year_match = re.search(r"in (\d{4})", text_lower)
                year = int(year_match.group(1)) if year_match else default_year
                
                # 尝试提取主体
                before_keyword = text_lower[:text_lower.find(keyword)]
                subject_match = re.search(r"(\w+)$", before_keyword)
                subject = subject_match.group(1) if subject_match else "UNKNOWN"
                
                events.append({
                    "subject": subject,
                    "event_type": keyword,
                    "year": year,
                    "text": text
                })
        
        return events
    
    def build_timeline(self, events: List[Dict]) -> List[Dict]:
        """
        构建时间线
        
        参数:
            events: 事件列表
        
        返回:
            按时间排序的事件
        """
        # 排序
        sorted_events = sorted(events, key=lambda x: x.get("year", 0))
        
        # 去重
        seen = set()
        unique_events = []
        
        for event in sorted_events:
            key = (event["subject"], event["event_type"], event["year"])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events


def build_tkg_from_text(texts: List[str]) -> Tuple['TemporalKG', List[Dict]]:
    """
    从文本构建时序知识图谱
    
    参数:
        texts: 文本列表
    
    返回:
        (时序知识图谱, 抽取的元数据)
    """
    from temporal_knowledge_graph import TemporalKG
    
    kg = TemporalKG("ExtractedKG")
    extractor = TemporalRelationExtractor()
    
    all_entities = []
    all_relations = []
    all_temporal_relations = []
    
    for text in texts:
        # 抽取实体
        entities = extractor.extract_entities(text)
        all_entities.extend(entities)
        
        # 抽取关系
        relations = extractor.extract_relations(text)
        for s, p, o, t in relations:
            kg.add_triple(s, p, o, t)
            all_relations.append((s, p, o, t))
        
        # 抽取时序关系
        temp_relations = extractor.extract_temporal_relations(text)
        all_temporal_relations.extend(temp_relations)
    
    metadata = {
        "num_entities": len(all_entities),
        "num_relations": len(all_relations),
        "num_temporal_relations": len(all_temporal_relations),
    }
    
    return kg, metadata


if __name__ == "__main__":
    print("=== 时序关系抽取测试 ===")
    
    # 测试文本
    text1 = """
    Apple was founded in 1976 by Steve Jobs and Steve Wozniak.
    Steve Jobs left Apple in 1985 and returned in 1996.
    Apple released the iPhone in 2007.
    Tim Cook became CEO of Apple in 2011.
    """
    
    text2 = """
    Microsoft acquired LinkedIn in 2016 for $26 billion.
    Amazon was founded by Jeff Bezos in 1994.
    Jeff Bezos became the richest person in 2018.
    """
    
    # 创建抽取器
    extractor = TemporalRelationExtractor()
    
    print("\n--- 实体抽取 ---")
    for text in [text1, text2]:
        entities = extractor.extract_entities(text)
        print(f"文本: {text[:50]}...")
        print(f"  实体: {[str(e) for e in entities[:5]]}")
    
    print("\n--- 时间表达式抽取 ---")
    for text in [text1, text2]:
        times = extractor.extract_time_expressions(text)
        print(f"文本: {text[:50]}...")
        print(f"  时间: {[str(t) for t in times[:5]]}")
    
    print("\n--- 关系抽取 ---")
    for text in [text1, text2]:
        relations = extractor.extract_relations(text)
        print(f"文本: {text[:50]}...")
        print(f"  关系: {relations}")
    
    print("\n--- 时序关系抽取 ---")
    for text in [text1, text2]:
        temp_relations = extractor.extract_temporal_relations(text)
        print(f"文本: {text[:50]}...")
        print(f"  时序关系: {temp_relations[:2]}")
    
    print("\n--- 从多文本构建TKG ---")
    kg, metadata = build_tkg_from_text([text1, text2])
    print(f"构建的TKG统计:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")
    
    # 事件检测
    print("\n--- 时序事件检测 ---")
    detector = TemporalEventDetector()
    events = detector.detect_events(text1)
    print(f"检测到的事件: {events}")
    
    timeline = detector.build_timeline(events)
    print(f"\n时间线:")
    for event in timeline:
        print(f"  {event['year']}: {event['subject']} - {event['event_type']}")
    
    print("\n=== 测试完成 ===")

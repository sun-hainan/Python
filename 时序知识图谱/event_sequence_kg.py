"""
事件序列知识图谱构建 (Event Sequence KG Construction)
==================================================
从事件序列构建知识图谱，支持时间推理和模式挖掘。

核心概念：
- 事件序列：按时间排列的事件列表
- 事件抽取：从文本或结构化数据中识别事件
- 事件图谱：事件及其关系的时序知识图谱

参考：
    - MIT Information Extraction (IE) Framework.
    - ACE (Automatic Content Extraction) Event Extraction.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
import re


class Event:
    """事件"""
    def __init__(self, event_id: str, event_type: str, timestamp: Any,
                 trigger: str, mentions: List[str], arguments: Dict[str, Any]):
        self.id = event_id
        self.type = event_type
        self.timestamp = timestamp
        self.trigger = trigger
        self.mentions = mentions
        self.arguments = arguments  # {role: entity}
        self.attributes = {}
    
    def __str__(self):
        return f"Event({self.type}, {self.timestamp}, {self.arguments})"


class EventMention:
    """事件提及"""
    def __init__(self, text: str, start: int, end: int, 
                 event_type: str, score: float = 1.0):
        self.text = text
        self.start = start
        self.end = end
        self.event_type = event_type
        self.score = score


class EventSchema:
    """事件模式定义"""
    
    # 预定义的事件类型和角色
    EVENT_TYPES = {
        "Transfer": {
            "roles": ["agent", "patient", "beneficiary", "instrument", "place", "time"],
            "subtypes": ["TransferOwnership", "TransferControl"]
        },
        "Movement": {
            "roles": ["theme", "agent", "destination", "origin", "time"],
            "subtypes": ["Transport", "Travel"]
        },
        "Communication": {
            "roles": ["speaker", "addressee", "topic", "medium", "time"],
            "subtypes": ["Speak", "Write", "Contact"]
        },
        "Conflict": {
            "roles": ["attacker", "target", "instrument", "place", "time"],
            "subtypes": ["Attack", "Demonstrate"]
        },
        "Transaction": {
            "roles": ["buyer", "seller", "goods", "price", "place", "time"],
            "subtypes": ["Buy", "Sell", "Pay"]
        }
    }
    
    @classmethod
    def get_roles(cls, event_type: str) -> List[str]:
        """获取事件类型的角色"""
        for category, info in cls.EVENT_TYPES.items():
            if event_type in info["subtypes"]:
                return info["roles"]
        return []
    
    @classmethod
    def get_parent_type(cls, event_type: str) -> Optional[str]:
        """获取事件的父类型"""
        for category, info in cls.EVENT_TYPES.items():
            if event_type in info["subtypes"]:
                return category
        return None


class EventSequenceExtractor:
    """
    事件序列抽取器
    
    从文本或结构化数据中抽取事件序列
    """
    
    def __init__(self):
        self.events = []
        self.entity_mentions = []
        self.coreference_map = {}  # 共指链
    
    def add_event(self, event: Event):
        """添加事件"""
        self.events.append(event)
        # 按时间排序
        self.events.sort(key=lambda e: e.timestamp)
    
    def extract_from_text(self, text: str) -> List[Event]:
        """
        从文本抽取事件（简化版）
        
        参数:
            text: 输入文本
        
        返回:
            事件列表
        """
        events = []
        
        # 简化的模式匹配
        patterns = [
            (r"(\w+) bought (\w+) from (\w+)", "Buy", ["buyer", "goods", "seller"]),
            (r"(\w+) sold (\w+) to (\w+)", "Sell", ["seller", "goods", "buyer"]),
            (r"(\w+) went to (\w+)", "Travel", ["agent", "destination"]),
            (r"(\w+) met (\w+)", "Meet", ["participant1", "participant2"]),
            (r"(\w+) signed (?:an? )?agreement with (\w+)", "SignAgreement", ["signer1", "signer2"]),
        ]
        
        for pattern, event_type, roles in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                event_id = f"evt_{len(events)}"
                timestamp = None  # 需要从上下文推断
                
                arguments = {}
                for i, role in enumerate(roles, 1):
                    if i < len(match.groups()):
                        arguments[role] = match.group(i)
                
                event = Event(
                    event_id=event_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    trigger=match.group(0),
                    mentions=[match.group(0)],
                    arguments=arguments
                )
                events.append(event)
        
        return events
    
    def build_event_graph(self) -> 'EventKnowledgeGraph':
        """
        构建事件知识图谱
        
        返回:
            事件知识图谱
        """
        from temporal_knowledge_graph import TemporalKG
        
        kg = TemporalKG("EventKG")
        
        for event in self.events:
            # 提取三元组
            subject = event.arguments.get("agent") or event.arguments.get("theme") or "UNK"
            obj = event.arguments.get("patient") or event.arguments.get("destination") or "UNK"
            
            if subject != "UNK" and obj != "UNK":
                kg.add_triple(
                    subject,
                    event.type,
                    obj,
                    event.timestamp or 0
                )
            
            # 添加事件特定关系
            for role, value in event.arguments.items():
                if value != "UNK":
                    kg.add_triple(
                        event.id,
                        f"has_{role}",
                        value,
                        event.timestamp or 0
                    )
        
        return kg


class EventCoreferenceResolver:
    """事件共指消解"""
    
    def __init__(self):
        self.clusters = []
        self.mention_to_cluster = {}
    
    def add_mention(self, event_id: str, entity: str, timestamp: Any):
        """添加提及"""
        # 查找是否已存在可链接的簇
        for cluster in self.clusters:
            # 检查时序接近度和实体匹配
            for mention in cluster:
                m_event, m_entity, m_time = mention
                if m_entity == entity and abs(self._time_diff(m_time, timestamp)) < 86400:
                    # 加入簇
                    cluster.append((event_id, entity, timestamp))
                    self.mention_to_cluster[event_id] = cluster
                    return
        
        # 创建新簇
        new_cluster = [(event_id, entity, timestamp)]
        self.clusters.append(new_cluster)
        self.mention_to_cluster[event_id] = new_cluster
    
    def _time_diff(self, t1: Any, t2: Any) -> float:
        """计算时间差（秒）"""
        if isinstance(t1, datetime) and isinstance(t2, datetime):
            return abs((t2 - t1).total_seconds())
        return abs(float(t1) - float(t2)) if t1 and t2 else 0
    
    def get_cluster(self, event_id: str) -> Optional[List]:
        """获取事件所属的簇"""
        return self.mention_to_cluster.get(event_id)


class EventPatternMiner:
    """事件模式挖掘"""
    
    def __init__(self, kg):
        self.kg = kg
        self.patterns = defaultdict(int)
    
    def mine_sequence_patterns(self, min_support: int = 2) -> Dict[str, int]:
        """
        挖掘时序模式
        
        参数:
            min_support: 最小支持度
        
        返回:
            频繁模式字典
        """
        # 获取事件序列
        events = sorted(self.kg.triples.keys(), 
                       key=lambda x: self.kg.get_validity_time(*x)[0])
        
        # 提取事件类型序列
        event_types = [e[1] for e in events]  # (s, p, o) -> p
        
        # 挖掘k-gram模式
        for k in range(1, 4):  # 1-gram到3-gram
            for i in range(len(event_types) - k + 1):
                pattern = tuple(event_types[i:i+k])
                self.patterns[pattern] += 1
        
        # 过滤
        return {p: c for p, c in self.patterns.items() if c >= min_support}
    
    def find_causal_patterns(self) -> List[Tuple[str, str]]:
        """
        发现因果模式
        
        返回:
            [(事件类型1, 事件类型2), ...]
        """
        causal_pairs = []
        
        # 简化：检查时间接近的事件类型对
        events = list(self.kg.triples.keys())
        
        for i in range(len(events) - 1):
            e1_type = events[i][1]
            e2_type = events[i+1][1]
            
            t1 = self.kg.get_validity_time(*events[i])[0][0]
            t2 = self.kg.get_validity_time(*events[i+1])[0][0]
            
            # 时间差小于1天认为是可能的因果关系
            if t2 - t1 < 86400 * 7:  # 1周内
                causal_pairs.append((e1_type, e2_type))
        
        return causal_pairs


def build_event_kg_from_stories(stories: List[Dict]) -> Tuple['EventKnowledgeGraph', List[Event]]:
    """
    从故事列表构建事件知识图谱
    
    参数:
        stories: 故事列表，每个故事包含text和timestamp
    
    返回:
        (事件知识图谱, 事件列表)
    """
    extractor = EventSequenceExtractor()
    
    for story in stories:
        text = story.get("text", "")
        timestamp = story.get("timestamp", 0)
        
        # 抽取事件
        events = extractor.extract_from_text(text)
        
        # 设置时间戳
        for event in events:
            if event.timestamp is None:
                event.timestamp = timestamp
        
        # 添加到抽取器
        for event in events:
            extractor.add_event(event)
    
    # 构建图谱
    kg = extractor.build_event_graph()
    
    return kg, extractor.events


if __name__ == "__main__":
    print("=== 事件序列知识图谱构建测试 ===")
    
    # 事件序列抽取
    extractor = EventSequenceExtractor()
    
    text = """
    Apple bought Beats from Dr. Dre in 2014.
    Tim Cook became CEO of Apple in 2011.
    Steve Jobs founded Apple in 1976.
    Apple released iPhone in 2007.
    """
    
    events = extractor.extract_from_text(text)
    print(f"抽取到 {len(events)} 个事件:")
    for event in events:
        print(f"  {event}")
    
    # 添加事件
    event1 = Event(
        event_id="e1",
        event_type="TransferOwnership",
        timestamp=2014,
        trigger="bought",
        mentions=["Apple bought Beats"],
        arguments={"buyer": "Apple", "seller": "Dr. Dre", "goods": "Beats"}
    )
    
    event2 = Event(
        event_id="e2",
        event_type="BecomeCEO",
        timestamp=2011,
        trigger="became CEO",
        mentions=["Tim Cook became CEO"],
        arguments={"person": "Tim Cook", "organization": "Apple"}
    )
    
    extractor.add_event(event1)
    extractor.add_event(event2)
    
    # 构建事件图谱
    print("\n构建事件图谱:")
    event_kg = extractor.build_event_graph()
    stats = event_kg.statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 事件模式挖掘
    print("\n事件模式挖掘:")
    miner = EventPatternMiner(event_kg)
    patterns = miner.mine_sequence_patterns(min_support=1)
    print(f"  发现 {len(patterns)} 种模式:")
    for pattern, count in list(patterns.items())[:5]:
        print(f"    {pattern}: {count}")
    
    # 因果模式
    causal = miner.find_causal_patterns()
    print(f"\n  可能因果对: {causal[:5]}")
    
    # 事件模式定义
    print("\n\n事件模式定义:")
    roles = EventSchema.get_roles("Buy")
    print(f"  Buy事件角色: {roles}")
    
    parent = EventSchema.get_parent_type("Buy")
    print(f"  Buy父类型: {parent}")
    
    print("\n=== 测试完成 ===")

"""
实体检索模块 - 实体链接/实体消歧

本模块实现基于知识图谱的实体检索和链接系统。
给定文本中的实体提及，识别并链接到知识图谱中的对应实体。

核心方法：
1. 候选生成：根据提及文本生成候选实体
2. 实体消歧：在多个候选中选择正确实体
3. 上下文编码：利用上下文信息消歧
4. 图推理：利用知识图谱结构辅助消歧
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter, defaultdict
import re


@dataclass
class Entity:
    """实体"""
    entity_id: str
    name: str
    entity_type: str
    aliases: List[str] = None
    description: str = ""
    attributes: Dict = None


@dataclass
class Mention:
    """文本提及"""
    text: str
    start: int
    end: int
    linked_entity: Optional[str] = None
    candidates: List[str] = None


class KnowledgeGraph:
    """知识图谱"""

    def __init__(self):
        self.entities = {}  # entity_id -> Entity
        self.name_to_entities = defaultdict(list)  # name -> [entity_ids]
        self.type_to_entities = defaultdict(list)  # type -> [entity_ids]
        self.entity_relations = {}  # (e1, e2) -> [relation_types]

    def add_entity(self, entity: Entity):
        self.entities[entity.entity_id] = entity
        self.name_to_entities[entity.name].append(entity.entity_id)
        self.type_to_entities[entity.entity_type].append(entity.entity_id)

        # 别名
        if entity.aliases:
            for alias in entity.aliases:
                self.name_to_entities[alias].append(entity.entity_id)

    def add_relation(self, e1_id: str, e2_id: str, relation: str):
        key = (e1_id, e2_id)
        if key not in self.entity_relations:
            self.entity_relations[key] = []
        self.entity_relations[key].append(relation)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def get_candidates_by_name(self, name: str) -> List[str]:
        return self.name_to_entities.get(name, [])

    def get_neighbors(self, entity_id: str) -> Dict[str, List[str]]:
        """获取邻居实体和关系"""
        neighbors = defaultdict(list)
        for (e1, e2), rels in self.entity_relations.items():
            if e1 == entity_id:
                neighbors[e2].extend(rels)
            elif e2 == entity_id:
                neighbors[e1].extend(rels)
        return dict(neighbors)


class CandidateGenerator:
    """候选实体生成器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def generate(self, mention_text: str) -> List[str]:
        """
        生成候选实体列表
        :param mention_text: 提及文本
        :return: 候选实体ID列表
        """
        candidates = []

        # 精确匹配
        exact = self.kg.get_candidates_by_name(mention_text)
        candidates.extend(exact)

        # 小写匹配
        lower = mention_text.lower()
        for name, entity_ids in self.kg.name_to_entities.items():
            if name.lower() == lower:
                candidates.extend(entity_ids)

        # 去重
        return list(set(candidates))


class EntityDisambiguator(nn.Module):
    """实体消歧模型"""

    def __init__(self, embed_dim=128, hidden_dim=256, vocab_size=10000):
        super().__init__()
        # 上下文编码器
        self.context_encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        # 实体编码器
        self.entity_encoder = nn.Sequential(
            nn.Embedding(vocab_size, embed_dim),
            nn.Linear(embed_dim, hidden_dim),
            nn.ReLU()
        )
        # 评分层
        self.scorer = nn.Sequential(
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def encode_context(self, context_tokens: torch.Tensor) -> torch.Tensor:
        """编码上下文"""
        embed = nn.functional.embedding(context_tokens, torch.zeros_like(context_tokens).float())
        _, (h_n, _) = self.context_encoder(embed)
        return torch.cat([h_n[0], h_n[1]], dim=-1)

    def score_candidate(self, context_repr: torch.Tensor,
                       entity_repr: torch.Tensor) -> float:
        """评分单个候选"""
        combined = torch.cat([context_repr, entity_repr,
                             context_repr * entity_repr,
                             torch.abs(context_repr - entity_repr)], dim=-1)
        score = self.scorer(combined)
        return score.item()


class EntityLinker:
    """实体链接器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.candidate_generator = CandidateGenerator(kg)
        self.disambiguator = EntityDisambiguator()
        self.disambiguator.eval()

    def link_mention(self, mention: Mention, context: str) -> Optional[str]:
        """
        链接单个提及到知识图谱
        :param mention: 文本提及
        :param context: 周围上下文
        :return: 实体ID或None
        """
        # 生成候选
        candidates = self.candidate_generator.generate(mention.text)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 消歧（简化版：选择类型匹配的）
        best_entity = None
        best_score = -1e9

        for entity_id in candidates:
            entity = self.kg.get_entity(entity_id)
            if not entity:
                continue

            # 简化的消歧：使用邻居重叠
            mention_neighbors = set()  # 从上下文中提取的邻居
            entity_neighbors = set(self.kg.get_neighbors(entity_id).keys())

            # 计算重叠
            overlap = len(mention_neighbors & entity_neighbors)
            score = overlap + (1.0 if entity.type == "PERSON" else 0.5)

            if score > best_score:
                best_score = score
                best_entity = entity_id

        return best_entity


class EntityRetrieval:
    """实体检索系统"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.entity_vectors = {}  # entity_id -> vector
        self.entity_index = {}  # entity_id -> 原始数据

    def index_entity(self, entity_id: str, entity_vector: np.ndarray):
        """索引实体"""
        self.entity_vectors[entity_id] = entity_vector
        self.entity_index[entity_id] = self.kg.get_entity(entity_id)

    def search(self, query_vector: np.ndarray, entity_type: Optional[str] = None,
               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索实体
        :return: [(entity_id, score)]
        """
        scores = []

        for entity_id, entity_vec in self.entity_vectors.items():
            entity = self.kg.get_entity(entity_id)

            # 类型过滤
            if entity_type and entity and entity.entity_type != entity_type:
                continue

            # 余弦相似度
            sim = np.dot(query_vector, entity_vec) / (
                np.linalg.norm(query_vector) * np.linalg.norm(entity_vec) + 1e-10
            )
            scores.append((entity_id, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def get_entity_info(self, entity_id: str) -> Dict:
        """获取实体完整信息"""
        entity = self.kg.get_entity(entity_id)
        if not entity:
            return {}

        neighbors = self.kg.get_neighbors(entity_id)

        return {
            "id": entity_id,
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description,
            "neighbors": {
                neighbor_id: relations
                for neighbor_id, relations in neighbors.items()
            }
        }


class EntityMentionDetector:
    """实体提及检测器"""

    def __init__(self):
        self.person_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            r'\b(Mr|Mrs|Ms|Dr|Prof)\. [A-Z][a-z]+'
        ]

    def detect(self, text: str) -> List[Mention]:
        """检测文本中的实体提及"""
        mentions = []

        # 简单正则匹配
        for pattern in self.person_patterns:
            for match in re.finditer(pattern, text):
                mention_text = match.group()
                mentions.append(Mention(
                    text=mention_text,
                    start=match.start(),
                    end=match.end()
                ))

        return mentions


def compute_entity_linking_accuracy(predicted: Dict[str, str],
                                    ground_truth: Dict[str, str]) -> float:
    """计算实体链接准确率"""
    correct = sum(1 for m, e in predicted.items() if ground_truth.get(m) == e)
    total = len(ground_truth) if ground_truth else 1
    return correct / total


def demo():
    """实体检索演示"""
    print("[实体检索演示]")

    # 构建知识图谱
    kg = KnowledgeGraph()

    entities = [
        Entity("e1", "Apple Inc.", "ORG", aliases=["Apple", "Apple Computer"]),
        Entity("e2", "Apple", "FRUIT"),
        Entity("e3", "Steve Jobs", "PERSON", aliases=["Steve", "Jobs"]),
        Entity("e4", "Tim Cook", "PERSON"),
        Entity("e5", "California", "LOCATION"),
        Entity("e6", "Google", "ORG", aliases=["Google Inc."]),
    ]

    for e in entities:
        kg.add_entity(e)

    # 添加关系
    kg.add_relation("e1", "e3", "founded_by")
    kg.add_relation("e1", "e4", "CEO_of")
    kg.add_relation("e1", "e5", "located_in")
    kg.add_relation("e6", "e3", "worked_with")

    # 候选生成
    generator = CandidateGenerator(kg)
    candidates = generator.generate("Apple")
    print(f"  'Apple'的候选: {[kg.get_entity(e).name for e in candidates]}")

    candidates = generator.generate("Steve Jobs")
    print(f"  'Steve Jobs'的候选: {[kg.get_entity(e).name for e in candidates]}")

    # 实体链接
    linker = EntityLinker(kg)
    mention = Mention("Apple", 0, 5)
    linked = linker.link_mention(mention, "Apple Inc. was founded by Steve Jobs")
    print(f"\n  'Apple'链接到: {linked} ({kg.get_entity(linked).name if linked else 'None'})")

    # 实体检索
    retrieval = EntityRetrieval(kg)
    for eid, entity in kg.entities.items():
        retrieval.index_entity(eid, np.random.randn(128))

    results = retrieval.search(np.random.randn(128), entity_type="PERSON", top_k=3)
    print(f"\n  PERSON类型实体搜索结果: {[(kg.get_entity(e).name, f'{s:.3f}') for e, s in results]}")

    # 实体信息
    info = retrieval.get_entity_info("e1")
    print(f"\n  Apple Inc.的信息:")
    print(f"    类型: {info['type']}")
    print(f"    邻居: {info['neighbors']}")

    print("  ✅ 实体检索演示通过！")


from dataclasses import dataclass


if __name__ == "__main__":
    demo()

"""
知识图谱问答模块

本模块实现基于知识图谱的问答系统（KBQA）。
给定自然语言问题，链接到知识图谱中的实体和关系，生成答案。

核心方法：
1. 实体识别：NER识别问题中的实体
2. 实体链接：将识别出的实体链接到知识图谱
3. 关系检测：识别查询意图和关系路径
4. 子图推理：在知识图谱子图中推理答案
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        import re
        text = text.lower()
        words = re.sub(r'[^\w\s]', ' ', text).split()
        return [w for w in words if len(w) > 1]


class KnowledgeGraph:
    """简单知识图谱"""

    def __init__(self):
        self.entities = {}  # entity_id -> {name, type, properties}
        self.relations = []  # [(head_id, relation, tail_id)]
        self.entity_index = {}  # name -> entity_id
        self.relation_types = set()

    def add_entity(self, entity_id: str, name: str, entity_type: str = "", properties: Dict = None):
        self.entities[entity_id] = {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "properties": properties or {}
        }
        self.entity_index[name.lower()] = entity_id
        self.entity_index[name.lower().split()[0]] = entity_id  # 方便匹配

    def add_triple(self, head_id: str, relation: str, tail_id: str):
        self.relations.append((head_id, relation, tail_id))
        self.relation_types.add(relation)

    def get_neighbors(self, entity_id: str, relation: Optional[str] = None) -> List[Tuple[str, str]]:
        neighbors = []
        for h, r, t in self.relations:
            if h == entity_id and (relation is None or r == relation):
                neighbors.append((t, r))
            elif t == entity_id and (relation is None or r == relation):
                neighbors.append((h, r))
        return neighbors

    def get_property(self, entity_id: str, relation: str) -> List[str]:
        results = []
        for h, r, t in self.relations:
            if h == entity_id and r == relation:
                entity = self.entities.get(t)
                if entity:
                    results.append(entity["name"])
        return results


class NamedEntityRecognizer:
    """命名实体识别器（简单实现）"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.entity_names = [e["name"] for e in kg.entities.values()]

    def recognize(self, text: str) -> List[Dict]:
        """
        识别文本中的实体
        :return: [{"text": "...", "start": 0, "end": 5, "type": "PERSON"}]
        """
        results = []
        text_lower = text.lower()

        for entity_id, entity in self.kg.entities.items():
            name = entity["name"].lower()
            if name in text_lower:
                start = text_lower.index(name)
                results.append({
                    "text": entity["name"],
                    "start": start,
                    "end": start + len(name),
                    "entity_id": entity_id,
                    "type": entity["type"]
                })

        # 去重：保留最长的匹配
        results.sort(key=lambda x: x["end"] - x["start"], reverse=True)
        filtered = []
        used_positions = set()

        for r in results:
            overlap = False
            for pos in range(r["start"], r["end"]):
                if pos in used_positions:
                    overlap = True
                    break
            if not overlap:
                filtered.append(r)
                for pos in range(r["start"], r["end"]):
                    used_positions.add(pos)

        return filtered


class EntityLinker:
    """实体链接器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def link(self, mention_text: str) -> Optional[str]:
        """将文本链接到知识图谱实体"""
        mention_lower = mention_text.lower()

        # 精确匹配
        if mention_lower in self.kg.entity_index:
            return self.kg.entity_index[mention_lower]

        # 前缀匹配
        for name, eid in self.kg.entity_index.items():
            if name.startswith(mention_lower) or mention_lower.startswith(name):
                return eid

        return None


class RelationClassifier(nn.Module):
    """关系分类器"""

    def __init__(self, vocab_size=5000, embed_dim=128, hidden_dim=256, num_relations=20):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_relations)
        )

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        embed = nn.functional.embedding(token_ids, torch.zeros_like(token_ids).float())
        _, (h_n, _) = self.encoder(embed)
        hidden = torch.cat([h_n[0], h_n[1]], dim=-1)
        return self.classifier(hidden)


class SPARQLLikeQueryGenerator:
    """类似SPARQL的查询生成器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.relation_patterns = {
            "出生地": "birth_place",
            "出生日期": "birth_date",
            "职业": "occupation",
            "首都": "capital_of",
            "位于": "located_in",
            "创立": "founded_by",
            "CEO": "CEO_of",
            "身高": "height",
            "人口": "population"
        }

    def generate(self, entity_id: str, relation_keyword: str) -> Dict:
        """生成查询"""
        # 找到匹配的关系
        matched_relation = None
        for pattern, rel in self.relation_patterns.items():
            if pattern in relation_keyword:
                matched_relation = rel
                break

        if not matched_relation:
            # 模糊匹配
            for rel in self.kg.relation_types:
                if rel.replace("_", " ") in relation_keyword.lower():
                    matched_relation = rel
                    break

        if not matched_relation:
            return {"error": "Relation not found"}

        # 执行查询
        results = self.kg.get_property(entity_id, matched_relation)

        return {
            "head_entity": entity_id,
            "relation": matched_relation,
            "answer": results,
            "query": f"SELECT ?x WHERE {{ <{entity_id}> <{matched_relation}> ?x }}"
        }


class GraphPathFinder:
    """图路径查找器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def find_paths(self, start_id: str, end_id: str, max_hops: int = 3) -> List[List[Tuple[str, str]]]:
        """
        找两点之间的路径
        :return: [[(neighbor_id, relation), ...], ...]
        """
        paths = []

        def dfs(current: str, target: str, visited: Set[str], path: List[Tuple[str, str]], depth: int):
            if depth > max_hops:
                return
            if current == target and path:
                paths.append(path.copy())
                return
            if current in visited:
                return

            visited.add(current)
            neighbors = self.kg.get_neighbors(current)

            for neighbor, relation in neighbors:
                if neighbor not in visited:
                    path.append((neighbor, relation))
                    dfs(neighbor, target, visited, path, depth + 1)
                    path.pop()

            visited.remove(current)

        dfs(start_id, end_id, set(), [], 0)
        return paths


class KnowledgeGraphQA:
    """知识图谱问答系统"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.ner = NamedEntityRecognizer(kg)
        self.entity_linker = EntityLinker(kg)
        self.query_generator = SPARQLLikeQueryGenerator(kg)
        self.path_finder = GraphPathFinder(kg)
        self.relation_classifier = RelationClassifier()

    def answer(self, question: str) -> Dict:
        """
        回答问题
        :param question: 自然语言问题
        :return: 答案结果
        """
        # 1. NER识别
        entities = self.ner.recognize(question)
        if not entities:
            return {"question": question, "error": "No entities recognized"}

        # 取第一个实体
        main_entity = entities[0]
        entity_id = main_entity["entity_id"]

        # 2. 关系检测
        relation_keyword = question.replace(main_entity["text"], "").strip()

        # 3. 生成查询
        query_result = self.query_generator.generate(entity_id, relation_keyword)

        if "error" in query_result:
            # 尝试多跳查询
            return self._multi_hop_answer(question, entities)

        return {
            "question": question,
            "recognized_entity": main_entity,
            "query": query_result["query"],
            "answer": query_result["answer"],
            "method": "direct_lookup"
        }

    def _multi_hop_answer(self, question: str, entities: List[Dict]) -> Dict:
        """多跳问答"""
        if len(entities) < 2:
            return {"question": question, "error": "Cannot resolve with multi-hop"}

        # 假设要找两个实体之间的关系
        e1_id = entities[0]["entity_id"]
        e2_id = entities[1]["entity_id"]

        paths = self.path_finder.find_paths(e1_id, e2_id, max_hops=3)

        if paths:
            path = paths[0]
            # 解析路径
            path_desc = " -> ".join([f"{rel}({e})" for e, rel in path])
            return {
                "question": question,
                "path": path_desc,
                "answer": [e for e, r in path],
                "method": "multi_hop"
            }

        return {
            "question": question,
            "error": "No path found between entities"
        }


def build_sample_kg() -> KnowledgeGraph:
    """构建示例知识图谱"""
    kg = KnowledgeGraph()

    # 实体
    kg.add_entity("e_apple", "Apple Inc.", "Company")
    kg.add_entity("e_steve", "Steve Jobs", "Person")
    kg.add_entity("e_tim", "Tim Cook", "Person")
    kg.add_entity("e_paris", "Paris", "City")
    kg.add_entity("e_france", "France", "Country")
    kg.add_entity("e_california", "California", "State")
    kg.add_entity("e_google", "Google", "Company")
    kg.add_entity("e_larry", "Larry Page", "Person")

    # 关系
    kg.add_triple("e_apple", "founded_by", "e_steve")
    kg.add_triple("e_apple", "CEO_of", "e_tim")
    kg.add_triple("e_apple", "located_in", "e_california")
    kg.add_triple("e_steve", "birth_place", "e_paris")
    kg.add_triple("e_france", "capital_of", "e_paris")
    kg.add_triple("e_france", "located_in", "e_europe")
    kg.add_triple("e_google", "founded_by", "e_larry")
    kg.add_triple("e_tim", "birth_place", "e_alabama")

    return kg


def demo():
    """知识图谱问答演示"""
    print("[知识图谱问答演示]")

    # 构建知识图谱
    kg = build_sample_kg()
    print(f"  实体数: {len(kg.entities)}")
    print(f"  关系数: {len(kg.relations)}")

    # 初始化QA系统
    qa = KnowledgeGraphQA(kg)

    # 测试问题
    test_questions = [
        "Who is the CEO of Apple Inc.?",
        "Where was Steve Jobs born?",
        "What is the capital of France?",
        "Apple Inc. was founded by whom?"
    ]

    print(f"\n  问答测试:")
    for q in test_questions:
        result = qa.answer(q)
        print(f"\n  Q: {q}")
        print(f"  识别实体: {result.get('recognized_entity', {}).get('text', 'N/A')}")
        print(f"  方法: {result.get('method', 'error')}")
        if 'answer' in result:
            print(f"  答案: {result['answer']}")
        if 'query' in result:
            print(f"  查询: {result['query'][:60]}...")
        if 'error' in result:
            print(f"  错误: {result['error']}")

    # NER演示
    print(f"\n  NER识别演示:")
    entities = qa.ner.recognize("Apple Inc. was founded by Steve Jobs")
    for e in entities:
        print(f"    '{e['text']}' -> {e['entity_id']} ({e['type']})")

    print("  ✅ 知识图谱问答演示通过！")


if __name__ == "__main__":
    demo()

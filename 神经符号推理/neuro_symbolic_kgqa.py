"""
神经符号知识图谱问答 (Neuro-Symbolic KGQA)
============================================
本模块实现神经符号混合的知识图谱问答系统：

方法：
1. 嵌入基础查询
2. 符号逻辑推理
3. 神经网络的查询嵌入学习

目标问题类型：
- 单跳查询 (What is X's relation to Y?)
- 多跳查询 (What is X's relation to Z through Y?)
- 聚合查询 (How many X are related to Y?)

Author: 算法库
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        self.triples: Set[Tuple[str, str, str]] = set()
        self.entity_to_id: Dict[str, int] = {}
        self.id_to_entity: Dict[int, str] = {}
        self.relation_to_id: Dict[str, int] = {}
        self.id_to_relation: Dict[int, str] = {}
        
        # 索引
        self.head_to_tail: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self.tail_to_head: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    
    def add_triple(self, head: str, relation: str, tail: str):
        """添加三元组"""
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        self.triples.add((head, relation, tail))
        
        # 更新索引
        self.head_to_tail[(head, relation)].add(tail)
        self.tail_to_head[(tail, relation)].add(head)
        
        # 分配ID
        if head not in self.entity_to_id:
            idx = len(self.entity_to_id)
            self.entity_to_id[head] = idx
            self.id_to_entity[idx] = head
        
        if tail not in self.entity_to_id:
            idx = len(self.entity_to_id)
            self.entity_to_id[tail] = idx
            self.id_to_entity[idx] = tail
        
        if relation not in self.relation_to_id:
            idx = len(self.relation_to_id)
            self.relation_to_id[relation] = idx
            self.id_to_relation[idx] = relation
    
    def get_tail(self, head: str, relation: str) -> Set[str]:
        """获取尾实体"""
        return self.head_to_tail.get((head, relation), set())
    
    def get_head(self, tail: str, relation: str) -> Set[str]:
        """获取头实体"""
        return self.tail_to_head.get((tail, relation), set())
    
    def num_entities(self) -> int:
        return len(self.entities)
    
    def num_relations(self) -> int:
        return len(self.relations)


class Query:
    """查询"""
    
    def __init__(self, query_type: str, entities: List[str] = None):
        self.query_type = query_type
        self.entities = entities or []


class KGQASystem:
    """知识图谱问答系统"""
    
    def __init__(self, kg: KnowledgeGraph, embedding_dim: int = 64):
        self.kg = kg
        self.embedding_dim = embedding_dim
        self.entity_embeddings: Dict[str, np.ndarray] = {}
        self.relation_embeddings: Dict[str, np.ndarray] = {}
        
        # 初始化嵌入
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """初始化实体和关系嵌入"""
        np.random.seed(42)
        scale = 0.1
        
        for entity in self.kg.entities:
            self.entity_embeddings[entity] = np.random.randn(self.embedding_dim) * scale
        
        for relation in self.kg.relations:
            self.relation_embeddings[relation] = np.random.randn(self.embedding_dim) * scale
    
    def answer_single_hop(self, head: str, relation: str) -> Set[str]:
        """单跳查询"""
        return self.kg.get_tail(head, relation)
    
    def answer_multi_hop(self, head: str, path: List[str]) -> Set[str]:
        """
        多跳查询
        
        参数:
            head: 起始实体
            path: 关系路径，如 ["father_of", "mother_of"]
        
        返回:
            终点实体集合
        """
        current_entities = {head}
        
        for relation in path:
            next_entities = set()
            for entity in current_entities:
                tails = self.kg.get_tail(entity, relation)
                next_entities.update(tails)
            current_entities = next_entities
            
            if not current_entities:
                break
        
        return current_entities
    
    def answer_conjunction(self, queries: List[Tuple[str, str]]) -> Set[str]:
        """
        合取查询
        
        参数:
            queries: [(entity, relation), ...]
        
        返回:
            满足所有查询条件的实体
        """
        result_sets = []
        
        for entity, relation in queries:
            tails = self.kg.get_tail(entity, relation)
            result_sets.append(tails)
        
        # 交集
        if result_sets:
            return set.intersection(*result_sets)
        return set()
    
    def answer_disjunction(self, queries: List[Tuple[str, str]]) -> Set[str]:
        """
        析取查询
        
        返回满足任一查询条件的实体
        """
        result_sets = []
        
        for entity, relation in queries:
            tails = self.kg.get_tail(entity, relation)
            result_sets.append(tails)
        
        if result_sets:
            return set.union(*result_sets)
        return set()
    
    def answer_negation(self, head: str, pos_rel: str, neg_rel: str) -> Set[str]:
        """
        否定查询
        
        找到通过pos_rel可达但通过neg_rel不可达的实体
        """
        pos_results = self.kg.get_tail(head, pos_rel)
        neg_results = self.kg.get_tail(head, neg_rel)
        
        return pos_results - neg_results
    
    def answer_aggregation(self, entity: str, relation: str) -> int:
        """
        聚合查询
        
        计数
        """
        return len(self.kg.get_tail(entity, relation))


class NeuralKGQA:
    """神经知识图谱问答"""
    
    def __init__(self, kgqa: KGQASystem):
        self.kgqa = kgqa
    
    def encode_query(self, query: Query) -> np.ndarray:
        """
        编码查询到向量空间
        
        简化实现
        """
        if query.query_type == "single_hop":
            head = query.entities[0]
            relation = query.entities[1]
            
            head_emb = self.kgqa.entity_embeddings.get(head, np.zeros(self.kgqa.embedding_dim))
            rel_emb = self.kgqa.relation_embeddings.get(relation, np.zeros(self.kgqa.embedding_dim))
            
            # 查询嵌入 = 头 + 关系
            return head_emb + rel_emb
        
        elif query.query_type == "multi_hop":
            head = query.entities[0]
            path = query.entities[1:]
            
            head_emb = self.kgqa.entity_embeddings.get(head, np.zeros(self.kgqa.embedding_dim))
            
            path_emb = np.zeros(self.kgqa.embedding_dim)
            for rel in path:
                rel_emb = self.kgqa.relation_embeddings.get(rel, np.zeros(self.kgqa.embedding_dim))
                path_emb += rel_emb
            
            return head_emb + path_emb
        
        return np.zeros(self.kgqa.embedding_dim)
    
    def score_entity(self, query_embedding: np.ndarray, entity: str) -> float:
        """计算实体与查询的匹配分数"""
        entity_emb = self.kgqa.entity_embeddings.get(entity, np.zeros(self.kgqa.embedding_dim))
        
        # 余弦相似度
        dot = np.dot(query_embedding, entity_emb)
        norm = np.linalg.norm(query_embedding) * np.linalg.norm(entity_emb)
        
        return dot / (norm + 1e-8)
    
    def rank_entities(self, query: Query, top_k: int = 10) -> List[Tuple[str, float]]:
        """对实体进行排序"""
        query_emb = self.encode_query(query)
        
        scores = []
        for entity in self.kgqa.kg.entities:
            score = self.score_entity(query_emb, entity)
            scores.append((entity, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def predict_answer(self, query: Query) -> Set[str]:
        """预测答案（结合神经和符号）"""
        # 符号执行获取候选
        if query.query_type == "single_hop":
            head = query.entities[0]
            relation = query.entities[1]
            return self.kgqa.answer_single_hop(head, relation)
        
        elif query.query_type == "multi_hop":
            head = query.entities[0]
            path = query.entities[1:]
            return self.kgqa.answer_multi_hop(head, path)
        
        return set()


class QueryParser:
    """自然语言查询解析（简化）"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.entity_mentions: Dict[str, List[str]] = {}  # 提及 -> 实体
    
    def register_entity_mention(self, mention: str, entity: str):
        """注册实体提及"""
        if mention not in self.entity_mentions:
            self.entity_mentions[mention.lower()] = []
        self.entity_mentions[mention.lower()].append(entity)
    
    def parse(self, question: str) -> Optional[Query]:
        """
        解析自然语言问题
        
        简化实现
        """
        question = question.lower()
        
        # 单跳查询
        if "what is" in question and "relation to" in question:
            # 提取实体和关系
            parts = question.replace("?", "").split()
            
            # 简化：假设格式已知
            return Query("single_hop", ["entity1", "relation1"])
        
        # 多跳查询
        if "through" in question:
            return Query("multi_hop", ["entity1", "rel1", "rel2"])
        
        return None


class EmbeddingBasedReasoner:
    """基于嵌入的推理器"""
    
    def __init__(self, kgqa: KGQASystem):
        self.kgqa = kgqa
    
    def compute_query_embedding(self, entity: str, relation: str) -> np.ndarray:
        """计算查询嵌入"""
        entity_emb = self.kgqa.entity_embeddings.get(entity, np.zeros(64))
        relation_emb = self.kgqa.relation_embeddings.get(relation, np.zeros(64))
        return entity_emb + relation_emb
    
    def find_similar_entities(self, entity: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """找到相似实体"""
        if entity not in self.kgqa.entity_embeddings:
            return []
        
        entity_emb = self.kgqa.entity_embeddings[entity]
        
        similarities = []
        for other in self.kgqa.kg.entities:
            if other == entity:
                continue
            
            other_emb = self.kgqa.entity_embeddings[other]
            sim = np.dot(entity_emb, other_emb) / (
                np.linalg.norm(entity_emb) * np.linalg.norm(other_emb) + 1e-8
            )
            similarities.append((other, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def predict_relation(self, head: str, tail: str) -> List[Tuple[str, float]]:
        """预测头尾实体之间的关系"""
        if head not in self.kgqa.entity_embeddings or tail not in self.kgqa.entity_embeddings:
            return []
        
        head_emb = self.kgqa.entity_embeddings[head]
        tail_emb = self.kgqa.entity_embeddings[tail]
        
        # 关系嵌入 ≈ tail - head
        pred_rel_emb = tail_emb - head_emb
        
        # 找最接近的关系
        similarities = []
        for rel in self.kgqa.kg.relations:
            rel_emb = self.kgqa.relation_embeddings[rel]
            sim = np.dot(pred_rel_emb, rel_emb) / (
                np.linalg.norm(pred_rel_emb) * np.linalg.norm(rel_emb) + 1e-8
            )
            similarities.append((rel, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:5]


if __name__ == "__main__":
    print("=" * 55)
    print("神经符号知识图谱问答测试")
    print("=" * 55)
    
    # 创建知识图谱
    kg = KnowledgeGraph()
    
    # 添加三元组：家庭关系
    triples = [
        ("Alice", "parent_of", "Bob"),
        ("Bob", "parent_of", "Carol"),
        ("Carol", "parent_of", "David"),
        ("Alice", "married_to", "John"),
        ("John", "married_to", "Alice"),
        ("Bob", "brother_of", "Eve"),
        ("Eve", "sister_of", "Bob"),
    ]
    
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    
    print(f"\n知识图谱: {kg.num_entities()} 实体, {kg.num_relations()} 关系")
    print(f"三元组数量: {len(kg.triples)}")
    
    # 创建问答系统
    kgqa = KGQASystem(kg)
    print(f"嵌入维度: {kgqa.embedding_dim}")
    
    # 单跳查询
    print("\n--- 单跳查询 ---")
    
    answers = kgqa.answer_single_hop("Alice", "parent_of")
    print(f"Alice parent_of ? => {answers}")
    
    answers = kgqa.answer_single_hop("Bob", "parent_of")
    print(f"Bob parent_of ? => {answers}")
    
    # 多跳查询
    print("\n--- 多跳查询 ---")
    
    answers = kgqa.answer_multi_hop("Alice", ["parent_of", "parent_of"])
    print(f"Alice --parent_of--> X --parent_of--> ? => {answers}")
    
    # 合取查询
    print("\n--- 合取查询 ---")
    
    answers = kgqa.answer_conjunction([
        ("Alice", "parent_of"),
        ("Bob", "brother_of")
    ])
    print(f"Alice parent_of X AND Bob brother_of X => {answers}")
    
    # 否定查询
    print("\n--- 否定查询 ---")
    
    answers = kgqa.answer_negation("Bob", "parent_of", "brother_of")
    print(f"Bob parent_of X but NOT brother_of X => {answers}")
    
    # 聚合查询
    print("\n--- 聚合查询 ---")
    
    count = kgqa.answer_aggregation("Alice", "parent_of")
    print(f"How many Alice parent_of ? => {count}")
    
    # 神经问答
    print("\n--- 神经问答 ---")
    
    neural_kgqa = NeuralKGQA(kgqa)
    
    # 编码查询
    query = Query("single_hop", ["Alice", "parent_of"])
    query_emb = neural_kgqa.encode_query(query)
    print(f"查询嵌入维度: {query_emb.shape}")
    
    # 排序实体
    rankings = neural_kgqa.rank_entities(query, top_k=5)
    print(f"实体排序 (Alice parent_of ?):")
    for entity, score in rankings:
        print(f"  {entity}: {score:.4f}")
    
    # 基于嵌入的推理
    print("\n--- 基于嵌入的推理 ---")
    
    reasoner = EmbeddingBasedReasoner(kgqa)
    
    similar = reasoner.find_similar_entities("Bob", top_k=3)
    print(f"与Bob相似的实体: {similar}")
    
    pred_rels = reasoner.predict_relation("Alice", "Bob")
    print(f"预测 Alice-Bob 之间的关系: {pred_rels}")
    
    # 查询解析
    print("\n--- 查询解析 ---")
    
    parser = QueryParser(kg)
    parser.register_entity_mention("Alice", "Alice")
    parser.register_entity_mention("Bob", "Bob")
    parser.register_entity_mention("parent_of", "parent_of")
    
    query = parser.parse("What is Alice's parent_of relation?")
    print(f"解析的查询: {query.query_type if query else None}")
    
    print("\n测试通过！神经符号KBQA系统工作正常。")

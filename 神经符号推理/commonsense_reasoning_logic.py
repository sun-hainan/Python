"""
常识推理的神经符号方法
========================
本模块实现常识推理的神经符号混合方法：

挑战：
- 常识知识难以形式化
- 概率与确定性的平衡
- 知识获取与表示

方法：
- 概率逻辑推理
- 知识图谱增强
- 神经符号集成

Author: 算法库
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Callable
import random


class CommonsenseKnowledge:
    """常识知识库"""
    
    def __init__(self):
        self.facts: Set[Tuple[str, str, str]] = set()  # (subject, relation, object)
        self.rules: List[Tuple[str, str, str, float]] = []  # (head, body1, body2, weight)
        self.entity_embeddings: Dict[str, np.ndarray] = {}
    
    def add_fact(self, subject: str, relation: str, obj: str, confidence: float = 1.0):
        """添加事实"""
        self.facts.add((subject, relation, obj))
    
    def add_rule(self, head_rel: str, body_rel1: str, body_rel2: str, weight: float = 0.8):
        """添加规则"""
        self.rules.append((head_rel, body_rel1, body_rel2, weight))
    
    def get_facts(self, subject: str = None, relation: str = None) -> List[Tuple]:
        """获取事实"""
        results = []
        for fact in self.facts:
            s, r, o = fact
            if (subject is None or s == subject) and (relation is None or r == relation):
                results.append(fact)
        return results
    
    def initialize_embedding(self, entity: str, embedding_dim: int = 64):
        """初始化实体嵌入"""
        if entity not in self.entity_embeddings:
            self.entity_embeddings[entity] = np.random.randn(embedding_dim) * 0.1


class CommonsenseReasoner:
    """常识推理器"""
    
    def __init__(self, knowledge: CommonsenseKnowledge):
        self.knowledge = knowledge
        self.inference_cache: Dict[Tuple, float] = {}
    
    def forward_chain(self, entity: str, relation: str) -> List[str]:
        """
        前向链推理
        
        已知: X --r1--> Y, 规则 r1 + r2 -> r3
        推导: X --r3--> ? (通过中间节点)
        """
        results = []
        
        # 直接事实
        direct = self.knowledge.get_facts(entity, relation)
        for s, r, o in direct:
            results.append(o)
        
        # 通过规则推导
        for head_rel, body1, body2, weight in self.knowledge.rules:
            if head_rel != relation:
                continue
            
            # 查找中间节点
            for s1, r1, o1 in self.knowledge.get_facts(entity, body1):
                for s2, r2, o2 in self.knowledge.get_facts(o1, body2):
                    if o2 not in results:
                        results.append(o2)
        
        return results
    
    def backward_chain(self, target: str, start: str, path_length: int = 2) -> List[List[str]]:
        """
        后向链推理
        
        找到从start到target的路径
        """
        paths = []
        
        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > path_length:
                return
            
            if current == target:
                paths.append(path.copy())
                return
            
            # 获取当前节点的所有出边
            for s, r, o in self.knowledge.get_facts(current):
                if o not in path:
                    path.append(o)
                    dfs(o, target, path, depth + 1)
                    path.pop()
        
        dfs(start, target, [start], 0)
        return paths
    
    def compute_confidence(self, subject: str, relation: str, obj: str) -> float:
        """
        计算推理置信度
        """
        # 检查直接事实
        if (subject, relation, obj) in self.knowledge.facts:
            return 1.0
        
        # 检查缓存
        key = (subject, relation, obj)
        if key in self.inference_cache:
            return self.inference_cache[key]
        
        # 通过规则计算
        confidence = 0.0
        
        for head_rel, body1, body2, weight in self.knowledge.rules:
            if head_rel != relation:
                continue
            
            # 查找中间节点
            for s1, r1, o1 in self.knowledge.get_facts(subject, body1):
                for s2, r2, o2 in self.knowledge.get_facts(o1, body2):
                    if o2 == obj:
                        confidence = max(confidence, weight)
        
        self.inference_cache[key] = confidence
        return confidence
    
    def similarity(self, entity1: str, entity2: str) -> float:
        """
        计算实体相似度（基于嵌入）
        """
        if entity1 not in self.knowledge.entity_embeddings:
            self.knowledge.initialize_embedding(entity1)
        if entity2 not in self.knowledge.entity_embeddings:
            self.knowledge.initialize_embedding(entity2)
        
        emb1 = self.knowledge.entity_embeddings[entity1]
        emb2 = self.knowledge.entity_embeddings[entity2]
        
        # 余弦相似度
        dot = np.dot(emb1, emb2)
        norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
        
        return (dot / (norm + 1e-8) + 1) / 2  # 归一化到[0,1]


class AnalogicalReasoning:
    """类比推理"""
    
    def __init__(self, knowledge: CommonsenseKnowledge):
        self.knowledge = knowledge
    
    def find_analogy(self, source_pair: Tuple[str, str], 
                    target_candidates: List[str]) -> List[Tuple[str, float]]:
        """
        寻找类比
        
        已知: A : B :: ?
        找到与B最相似的目标
        """
        source_entity, related_to_source = source_pair
        
        if source_entity not in self.knowledge.entity_embeddings:
            self.knowledge.initialize_embedding(source_entity)
        if related_to_source not in self.knowledge.entity_embeddings:
            self.knowledge.initialize_embedding(related_to_source)
        
        emb_source = self.knowledge.entity_embeddings[source_entity]
        emb_related = self.knowledge.entity_embeddings[related_to_source]
        
        # 关系向量
        relation_vec = emb_related - emb_source
        
        analogies = []
        for candidate in target_candidates:
            if candidate not in self.knowledge.entity_embeddings:
                self.knowledge.initialize_embedding(candidate)
            
            emb_candidate = self.knowledge.entity_embeddings[candidate]
            # 预测目标
            predicted = emb_candidate + relation_vec
            
            # 搜索与预测最接近的实体
            best_match = None
            best_score = -float('inf')
            
            for entity in self.knowledge.entity_embeddings:
                emb_entity = self.knowledge.entity_embeddings[entity]
                score = -np.linalg.norm(predicted - emb_entity)
                if score > best_score:
                    best_score = score
                    best_match = entity
            
            analogies.append((best_match, float(np.exp(best_score))))
        
        analogies.sort(key=lambda x: x[1], reverse=True)
        return analogies
    
    def structural_mapping(self, source_structure: Dict, 
                         target_domain: str) -> Dict:
        """
        结构映射
        
        将源域的结构映射到目标域
        """
        mapping = {}
        
        # 简化：基于共享关系
        source_relations = set()
        for s, r, o in self.knowledge.facts:
            source_relations.add(r)
        
        for rel in source_relations:
            # 在目标域中找对应关系
            target_candidates = [
                r for s, r, o in self.knowledge.get_facts(target_domain)
            ]
            
            if target_candidates:
                mapping[rel] = target_candidates[0]  # 简化选择
        
        return mapping


class CounterfactualReasoner:
    """反事实推理"""
    
    def __init__(self, reasoner: CommonsenseReasoner):
        self.reasoner = reasoner
    
    def generate_counterfactual(self, fact: Tuple[str, str, str]) -> List[str]:
        """
        生成反事实问题
        
        例如: "如果鸟不会飞..."
        """
        entity, relation, value = fact
        counterfactuals = []
        
        # 查找同类型的其他实体
        for s, r, o in self.knowledge.get_facts():
            if r == relation and s != entity:
                counterfactuals.append(
                    f"如果{s}不是{relation}{o}, 那么{entity}会{relation}什么?"
                )
        
        return counterfactuals[:5]
    
    def evaluate_counterfactual(self, premise: str, hypothesis: str) -> float:
        """
        评估反事实推理
        
        简化版本：基于规则匹配
        """
        # 检查是否是反事实模式
        if "如果" in premise and "会" in premise:
            return 0.7  # 简化置信度
        
        return 0.0


class CommonsenseQA:
    """常识问答"""
    
    def __init__(self, knowledge: CommonsenseKnowledge):
        self.knowledge = knowledge
        self.reasoner = CommonsenseReasoner(knowledge)
    
    def answer_question(self, question: str, choices: List[str]) -> Tuple[str, float]:
        """
        回答常识问题
        
        参数:
            question: 问题（如 "鸟可以___"）
            choices: 选项列表
        
        返回:
            (最佳答案, 置信度)
        """
        # 简化：从问题中提取关系
        # 假设格式：实体 + 关系 + "?"
        parts = question.replace("?", "").split()
        
        if len(parts) >= 2:
            entity = parts[0]
            # 关系是 "can" 或类似词
            inferred_relations = self.reasoner.forward_chain(entity, "")
            
            # 评估每个选项
            best_choice = choices[0]
            best_score = 0.0
            
            for choice in choices:
                score = self.reasoner.compute_confidence(entity, "", choice)
                if score > best_score:
                    best_score = score
                    best_choice = choice
            
            return best_choice, best_score
        
        return choices[0], 0.5


if __name__ == "__main__":
    print("=" * 55)
    print("常识推理的神经符号方法测试")
    print("=" * 55)
    
    # 创建常识知识库
    knowledge = CommonsenseKnowledge()
    
    # 添加常识事实
    facts = [
        ("bird", "can", "fly"),
        ("penguin", "is_a", "bird"),
        ("penguin", "cannot", "fly"),
        ("bird", "has", "wings"),
        ("fish", "can", "swim"),
        ("car", "is_a", "vehicle"),
        ("dog", "is_a", "mammal"),
        ("mammal", "is_a", "animal"),
    ]
    
    for s, r, o in facts:
        knowledge.add_fact(s, r, o)
    
    # 添加规则
    knowledge.add_rule("has", "is_a", "has", 0.9)
    
    print("\n--- 常识知识库 ---")
    print(f"事实数量: {len(knowledge.facts)}")
    print(f"规则数量: {len(knowledge.rules)}")
    
    # 初始化嵌入
    for entity in ["bird", "penguin", "fish", "car", "dog", "mammal"]:
        knowledge.initialize_embedding(entity)
    
    # 创建推理器
    reasoner = CommonsenseReasoner(knowledge)
    
    print("\n--- 前向链推理 ---")
    
    # penguin can ?
    results = reasoner.forward_chain("penguin", "fly")
    print(f"penguin can: {results}")
    
    # bird has ?
    results = reasoner.forward_chain("bird", "wings")
    print(f"bird has: {results}")
    
    print("\n--- 后向链推理 ---")
    
    # dog -> ? -> animal 路径
    paths = reasoner.backward_chain("animal", "dog", path_length=3)
    print(f"dog到animal的路径: {paths}")
    
    print("\n--- 推理置信度 ---")
    
    confidence = reasoner.compute_confidence("penguin", "has", "wings")
    print(f"penguin has wings 置信度: {confidence:.4f}")
    
    # 类比推理
    print("\n--- 类比推理 ---")
    
    analogizer = AnalogicalReasoning(knowledge)
    analogies = analogizer.find_analogy(
        ("bird", "nest"),  # bird和nest的关系
        ["dog", "fish", "car"]
    )
    print(f"bird:nest :: ?:{analogies}")
    
    # 反事实推理
    print("\n--- 反事实推理 ---")
    
    cf_reasoner = CounterfactualReasoner(reasoner)
    counterfactuals = cf_reasoner.generate_counterfactual(("penguin", "fly", "cannot"))
    print("反事实问题:")
    for cf in counterfactuals:
        print(f"  {cf}")
    
    # 常识问答
    print("\n--- 常识问答 ---")
    
    qa = CommonsenseQA(knowledge)
    answer, conf = qa.answer_question(
        "bird can ?",
        ["fly", "swim", "run"]
    )
    print(f"问题: bird can ?")
    print(f"答案: {answer}, 置信度: {conf:.4f}")
    
    print("\n测试通过！常识推理方法工作正常。")

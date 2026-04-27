# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / fuzzy_kg

本文件实现 fuzzy_kg 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict


class FuzzyTriple:
    """模糊三元组"""
    
    def __init__(self, head: str, relation: str, tail: str, confidence: float = 1.0):
        self.head = head
        self.relation = relation
        self.tail = tail
        self.confidence = max(0.0, min(1.0, confidence))  # 限制在[0,1]
    
    def __repr__(self):
        return f"({self.head}, {self.relation}, {self.tail}, cf={self.confidence:.2f})"


class FuzzyKnowledgeGraph:
    """模糊知识图谱"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        self.triples: List[FuzzyTriple] = []
        
        # 索引
        self.head_index: Dict[str, List[FuzzyTriple]] = defaultdict(list)
        self.relation_index: Dict[str, List[FuzzyTriple]] = defaultdict(list)
        self.triple_dict: Dict[Tuple[str, str, str], float] = {}
    
    def add_triple(self, head: str, relation: str, tail: str, confidence: float = 1.0):
        """添加模糊三元组"""
        fuzzy_triple = FuzzyTriple(head, relation, tail, confidence)
        
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        self.triples.append(fuzzy_triple)
        
        self.head_index[head].append(fuzzy_triple)
        self.relation_index[relation].append(fuzzy_triple)
        self.triple_dict[(head, relation, tail)] = confidence
    
    def get_confidence(self, head: str, relation: str, tail: str) -> float:
        """获取三元组的置信度"""
        return self.triple_dict.get((head, relation, tail), 0.0)
    
    def get_neighbors(self, entity: str) -> List[Tuple[str, str, float]]:
        """获取实体的邻居三元组"""
        neighbors = []
        for triple in self.head_index.get(entity, []):
            neighbors.append((triple.relation, triple.tail, triple.confidence))
        return neighbors


class FuzzyReasoning:
    """模糊推理引擎"""
    
    def __init__(self, fkg: FuzzyKnowledgeGraph):
        self.fkg = fkg
    
    def t_norm(self, x: float, y: float, t_type: str = 'min') -> float:
        """
        T-范数（与运算）
        
        常见T-范数：
        - min: 最小值
        - product: 乘积
        - Lukasiewicz: max(0, x + y - 1)
        """
        if t_type == 'min':
            return min(x, y)
        elif t_type == 'product':
            return x * y
        elif t_type == 'lukasiewicz':
            return max(0.0, x + y - 1)
        else:
            return min(x, y)
    
    def t_conorm(self, x: float, y: float, s_type: str = 'max') -> float:
        """
        T-余范数（或运算）
        
        常见T-余范数：
        - max: 最大值
        - probabilistic: x + y - xy
        """
        if s_type == 'max':
            return max(x, y)
        elif s_type == 'probabilistic':
            return x + y - x * y
        else:
            return max(x, y)
    
    def combine_confidence(self, confidences: List[float], 
                         method: str = 'min') -> float:
        """
        组合多个置信度
        
        方法:
        - min: 最小值
        - max: 最大值
        - average: 平均值
        - product: 乘积
        """
        if not confidences:
            return 0.0
        
        if method == 'min':
            return min(confidences)
        elif method == 'max':
            return max(confidences)
        elif method == 'average':
            return np.mean(confidences)
        elif method == 'product':
            result = 1.0
            for c in confidences:
                result *= c
            return result
        else:
            return min(confidences)
    
    def path_inference(self, start: str, end: str, 
                     max_depth: int = 3,
                     t_norm: str = 'min') -> float:
        """
        路径推理
        
        通过多条路径从start推理到end的置信度
        
        参数:
            start: 起始实体
            end: 目标实体
            max_depth: 最大路径深度
            t_norm: T-范数类型
        
        返回:
            推理置信度
        """
        from collections import deque
        
        queue = deque([(start, 1.0, [])])
        visited = {start}
        
        paths = []
        path_confidences = []
        
        while queue:
            current, current_conf, path = queue.popleft()
            
            if current == end and len(path) > 0:
                paths.append(path)
                path_confidences.append(current_conf)
                continue
            
            if len(path) >= max_depth:
                continue
            
            for relation, neighbor, confidence in self.fkg.get_neighbors(current):
                if neighbor not in visited or len(path) < 2:
                    new_conf = self.t_norm(current_conf, confidence, t_norm)
                    visited.add(neighbor)
                    queue.append((neighbor, new_conf, path + [relation]))
        
        if not path_confidences:
            return 0.0
        
        # 使用T-余范数组合多条路径的置信度
        result = path_confidences[0]
        for conf in path_confidences[1:]:
            result = self.t_conorm(result, conf, s_type='probabilistic')
        
        return result
    
    def forward_chain(self, start: str, relations: List[str]) -> Dict[str, float]:
        """
        前向链式推理
        
        参数:
            start: 起始实体
            relations: 关系序列
        
        返回:
            可能的尾实体及其置信度
        """
        current = start
        current_conf = 1.0
        results = {start: 1.0}
        
        for relation in relations:
            next_entities = {}
            
            for h, r, t, cf in self.fkg.triples:
                if h == current and r == relation:
                    new_conf = self.t_norm(current_conf, cf)
                    next_entities[t] = max(next_entities.get(t, 0.0), new_conf)
            
            if not next_entities:
                return {}
            
            current_conf = self.combine_confidence(list(next_entities.values()))
            current = list(next_entities.keys())[0]  # 简化：取第一个
            results[current] = current_conf
        
        return results
    
    def backward_chain(self, target: str, relations: List[str]) -> Dict[str, float]:
        """
        后向链式推理
        
        参数:
            target: 目标实体
            relations: 关系序列（逆序）
        
        返回:
            可能的起始实体及其置信度
        """
        current = target
        current_conf = 1.0
        results = {target: 1.0}
        
        # 逆序关系
        for relation in reversed(relations):
            prev_entities = {}
            
            for h, r, t, cf in self.fkg.triples:
                if t == current and r == relation:
                    new_conf = self.t_norm(current_conf, cf)
                    prev_entities[h] = max(prev_entities.get(h, 0.0), new_conf)
            
            if not prev_entities:
                return {}
            
            current_conf = self.combine_confidence(list(prev_entities.values()))
            current = list(prev_entities.keys())[0]
            results[current] = current_conf
        
        return results


class FuzzyQueryEngine:
    """模糊查询引擎"""
    
    def __init__(self, fkg: FuzzyKnowledgeGraph):
        self.fkg = fkg
        self.reasoner = FuzzyReasoning(fkg)
    
    def query_and(self, entity1: str, entity2: str, relation: str) -> float:
        """
        查询 AND: 两个实体通过某关系的置信度
        """
        conf1 = self.fkg.get_confidence(entity1, relation, entity2)
        conf2 = self.fkg.get_confidence(entity2, relation, entity1)  # 考虑双向
        
        return self.reasoner.t_norm(conf1, conf2)
    
    def query_or(self, entity1: str, entity2: str, relation: str) -> float:
        """
        查询 OR: 任一方向存在的关系置信度
        """
        conf1 = self.fkg.get_confidence(entity1, relation, entity2)
        conf2 = self.fkg.get_confidence(entity2, relation, entity1)
        
        return self.reasoner.t_conorm(conf1, conf2)
    
    def query_path(self, start: str, path: List[str]) -> float:
        """
        路径查询
        """
        current = start
        confidences = []
        
        for relation in path:
            found = False
            for h, r, t, cf in self.fkg.triples:
                if h == current and r == relation:
                    confidences.append(cf)
                    current = t
                    found = True
                    break
            
            if not found:
                return 0.0
        
        return self.reasoner.combine_confidence(confidences)
    
    def query_exist(self, entity: str, relation: str, target: str) -> float:
        """
        存在性查询：是否存在该关系
        """
        return self.fkg.get_confidence(entity, relation, target)
    
    def query_similar(self, entity: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        相似实体查询：基于共享邻居
        """
        neighbors1 = set((r, t) for r, t, c in self.fkg.get_neighbors(entity))
        
        similarities = []
        for other_entity in self.fkg.entities:
            if other_entity == entity:
                continue
            
            neighbors2 = set((r, t) for r, t, c in self.fkg.get_neighbors(other_entity))
            
            # Jaccard相似度
            intersection = neighbors1 & neighbors2
            union = neighbors1 | neighbors2
            
            if union:
                similarity = len(intersection) / len(union)
                similarities.append((other_entity, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("模糊知识图谱概率推理测试")
    print("=" * 50)
    
    # 创建模糊知识图谱
    fkg = FuzzyKnowledgeGraph()
    
    # 添加模糊三元组
    fuzzy_triples = [
        ("猫", "是", "动物", 0.95),
        ("狗", "是", "动物", 0.90),
        ("动物", "能", "移动", 0.80),
        ("猫", "能", "抓老鼠", 0.85),
        ("狗", "能", "看家", 0.90),
        ("动物", "有", "生命", 0.70),
        ("猫", "住在", "家", 0.75),
        ("狗", "住在", "家", 0.80),
        ("家", "位于", "城市", 0.60),
        ("城市", "位于", "国家", 0.70),
    ]
    
    for h, r, t, cf in fuzzy_triples:
        fkg.add_triple(h, r, t, cf)
    
    print(f"\n模糊KG: {len(fkg.entities)} 实体, {len(fkg.relations)} 关系, {len(fkg.triples)} 三元组")
    
    # 模糊推理
    print("\n--- 模糊推理 ---")
    reasoner = FuzzyReasoning(fkg)
    
    # 路径推理
    path_conf = reasoner.path_inference("猫", "国家", max_depth=4)
    print(f"猫 -> 国家的路径置信度: {path_conf:.4f}")
    
    # AND查询
    print("\n--- AND查询 ---")
    query_engine = FuzzyQueryEngine(fkg)
    
    and_conf = query_engine.query_and("猫", "狗", "是")
    print(f"猫 AND 狗 是[某种东西]的置信度: {and_conf:.4f}")
    
    # OR查询
    print("\n--- OR查询 ---")
    or_conf = query_engine.query_or("猫", "狗", "能")
    print(f"猫 OR 狗 能[做某事]的置信度: {or_conf:.4f}")
    
    # 相似实体
    print("\n--- 相似实体 ---")
    similar = query_engine.query_similar("猫", top_k=3)
    print(f"与猫相似的实体: {similar}")
    
    # T-范数测试
    print("\n--- T-范数测试 ---")
    print(f"min(0.8, 0.6) = {reasoner.t_norm(0.8, 0.6, 'min'):.4f}")
    print(f"product(0.8, 0.6) = {reasoner.t_norm(0.8, 0.6, 'product'):.4f}")
    print(f"Lukasiewicz(0.8, 0.6) = {reasoner.t_norm(0.8, 0.6, 'lukasiewicz'):.4f}")
    
    # T-余范数测试
    print("\n--- T-余范数测试 ---")
    print(f"max(0.8, 0.6) = {reasoner.t_conorm(0.8, 0.6, 'max'):.4f}")
    print(f"probabilistic(0.8, 0.6) = {reasoner.t_conorm(0.8, 0.6, 'probabilistic'):.4f}")
    
    # 置信度组合
    print("\n--- 置信度组合 ---")
    confs = [0.9, 0.8, 0.7, 0.6]
    print(f"组合方式: {confs}")
    print(f"min: {reasoner.combine_confidence(confs, 'min'):.4f}")
    print(f"max: {reasoner.combine_confidence(confs, 'max'):.4f}")
    print(f"average: {reasoner.combine_confidence(confs, 'average'):.4f}")
    print(f"product: {reasoner.combine_confidence(confs, 'product'):.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")

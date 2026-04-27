# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / amie_rule_mining

本文件实现 amie_rule_mining 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict, deque


class KnowledgeGraph:
    """知识图谱（复用path_ranking中的定义）"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        self.triples: List[Tuple[str, str, str]] = []
        self.triple_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.reverse_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    def add_triple(self, head: str, relation: str, tail: str):
        """添加三元组"""
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        self.triples.append((head, relation, tail))
        self.triple_index[head].append((relation, tail))
        self.reverse_index[tail].append((relation, head))
    
    def get_neighbors(self, entity: str) -> List[Tuple[str, str]]:
        """获取实体的所有邻居"""
        return self.triple_index.get(entity, [])
    
    def get_tail_entities(self, head: str, relation: str) -> Set[str]:
        """获取头实体通过某关系的尾实体集合"""
        tails = set()
        for rel, tail in self.triple_index.get(head, []):
            if rel == relation:
                tails.add(tail)
        return tails


class AMIERule:
    """关联规则"""
    
    def __init__(self, body_relations: List[Tuple[str, str]], 
                 head_relation: str,
                 head_variable: Optional[str] = None):
        """
        参数:
            body_relations: 规则体的关系列表 [(relation, var_type), ...]
                          var_type: 'v' 表示变量, 'c' 表示常量
            head_relation: 规则头的谓词
            head_variable: 规则头的变量名
        """
        self.body_relations = body_relations
        self.head_relation = head_relation
        self.head_variable = head_variable or 'y'
        
        # 统计指标
        self.head_coverage = 0.0      # 头覆盖度
        self.confidence = 0.0         # 置信度
        self.positive_examples = 0   # 正例数量
        self.total_body_support = 0  # 规则体支持数
    
    def __str__(self):
        """打印规则"""
        body_str = ", ".join([f"?x{ri} -> {rel}" if var == 'v' else f"{const} -> {rel}" 
                             for ri, (rel, var) in enumerate(self.body_relations)])
        return f"{self.head_relation}(?{self.head_variable}) :- {body_str}"


class AMIE:
    """
    AMIE关联规则挖掘算法
    
    参数:
        kg: 知识图谱
        min_support: 最小支持度
        min_confidence: 最小置信度
    """
    
    def __init__(self, kg: KnowledgeGraph, min_support: float = 0.001,
                 min_confidence: float = 0.5):
        self.kg = kg
        self.min_support = min_support
        self.min_confidence = min_confidence
        
        # 挖掘出的规则
        self.rules: List[AMIERule] = []
    
    def mine_rules(self, max_body_length: int = 3) -> List[AMIERule]:
        """
        挖掘关联规则
        
        参数:
            max_body_length: 规则体最大长度
        
        返回:
            挖掘出的规则列表
        """
        rules = []
        
        # 对每个关系挖掘规则
        for relation in self.kg.relations:
            # 初始化：挖掘单关系规则 (head :- body)
            initial_rules = self._mine_initial_rules(relation)
            
            for rule in initial_rules:
                # 评估规则
                self._evaluate_rule(rule)
                
                if rule.confidence >= self.min_confidence:
                    rules.append(rule)
                
                # 扩展规则
                for extended_rule in self._extend_rule(rule, max_body_length):
                    self._evaluate_rule(extended_rule)
                    
                    if extended_rule.confidence >= self.min_confidence:
                        rules.append(extended_rule)
        
        # 按置信度排序
        rules.sort(key=lambda r: r.confidence, reverse=True)
        
        self.rules = rules
        return rules[:100]  # 返回前100条规则
    
    def _mine_initial_rules(self, relation: str) -> List[AMIERule]:
        """挖掘初始规则（单关系规则）"""
        rules = []
        
        # 找到该关系的所有实例
        instances = []
        for head, rel, tail in self.kg.triples:
            if rel == relation:
                instances.append((head, tail))
        
        n_total = len(instances)
        
        if n_total == 0:
            return rules
        
        # 创建规则: head(x, y) :- body(z)
        # 这里简化：只挖掘 head(x) :- relation(x, y) 这类形式
        
        return [AMIERule([], relation)]
    
    def _extend_rule(self, rule: AMIERule, max_length: int) -> List[AMIERule]:
        """扩展规则（添加新的关系原子）"""
        if len(rule.body_relations) >= max_length:
            return []
        
        extended_rules = []
        
        # 尝试添加一个新的关系原子
        for relation in self.kg.relations:
            # 添加到规则体
            new_body = rule.body_relations + [(relation, 'v')]
            new_rule = AMIERule(new_body, rule.head_relation, rule.head_variable)
            
            # 这里需要处理变量链接，简化处理
            extended_rules.append(new_rule)
        
        return extended_rules
    
    def _evaluate_rule(self, rule: AMIERule):
        """评估规则的统计指标"""
        # 简化实现：计算覆盖度和置信度
        
        if len(rule.body_relations) == 0:
            # 无条件规则：只统计头关系
            count_head = sum(1 for h, r, t in self.kg.triples if r == rule.head_relation)
            count_total = len(self.kg.triples)
            
            rule.head_coverage = count_head / count_total if count_total > 0 else 0
            rule.confidence = rule.head_coverage
            rule.positive_examples = count_head
            rule.total_body_support = count_total
        else:
            # 有条件规则（简化）
            # 假设规则体中的关系都存在
            count_body = len(self.kg.triples) // 10  # 简化估计
            count_head_body = count_body // 2  # 简化估计
            
            rule.total_body_support = count_body
            rule.positive_examples = count_head_body
            rule.head_coverage = count_head_body / len(self.kg.triples) if len(self.kg.triples) > 0 else 0
            rule.confidence = count_head_body / count_body if count_body > 0 else 0
    
    def print_rules(self, top_k: int = 20):
        """打印规则"""
        print(f"共挖掘 {len(self.rules)} 条规则")
        print(f"最小支持度: {self.min_support}, 最小置信度: {self.min_confidence}")
        print("\nTop规则:")
        
        for i, rule in enumerate(self.rules[:top_k]):
            print(f"{i+1}. {rule}")
            print(f"   置信度: {rule.confidence:.4f}, 覆盖度: {rule.head_coverage:.4f}")


def compute_rule_confidence(kg: KnowledgeGraph, rule: AMIERule) -> float:
    """
    计算规则置信度
    
    置信度 = 规则体和规则头同时成立的次数 / 规则体成立的次数
    """
    if len(rule.body_relations) == 0:
        return 0.0
    
    # 简化的置信度计算
    # 假设规则形式: H(x, y) :- B1(z1), B2(z2), ...
    
    # 找到头部关系的所有实例
    head_count = sum(1 for h, r, t in kg.triples if r == rule.head_relation)
    
    # 估计规则体成立的次数
    body_count = head_count // 2  # 简化估计
    
    if body_count == 0:
        return 0.0
    
    return head_count / (body_count * 2)  # 简化


def mine_confidence_rules(kg: KnowledgeGraph, relation: str,
                         min_confidence: float = 0.5) -> List[Tuple[List[str], float]]:
    """
    挖掘某关系的置信规则
    
    返回:
        [(关系列表, 置信度), ...]
    """
    rules = []
    
    # 单关系规则
    head_count = sum(1 for h, r, t in kg.triples if r == relation)
    total_count = len(kg.triples)
    
    confidence = head_count / total_count if total_count > 0 else 0
    rules.append(([relation], confidence))
    
    # 尝试添加前缀规则
    for prefix_rel in kg.relations:
        if prefix_rel != relation:
            # 添加前缀后的规则置信度（简化）
            rules.append(([prefix_rel, relation], confidence * 0.8))
    
    rules.sort(key=lambda x: x[1], reverse=True)
    
    return [r for r in rules if r[1] >= min_confidence]


class AMIEPlus:
    """
    AMIE+算法（改进版）
    
    使用支持度剪枝和优化
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        
        # 统计信息
        self.relation_counts: Dict[str, int] = {}
        self.entity_counts: Dict[str, int] = {}
        
        self._compute_statistics()
    
    def _compute_statistics(self):
        """计算统计信息"""
        for h, r, t in self.kg.triples:
            self.relation_counts[r] = self.relation_counts.get(r, 0) + 1
            self.entity_counts[h] = self.entity_counts.get(h, 0) + 1
            self.entity_counts[t] = self.entity_counts.get(t, 0) + 1
    
    def support(self, predicate: str) -> float:
        """计算谓词的支持度"""
        count = self.relation_counts.get(predicate, 0)
        return count / len(self.kg.triples) if len(self.kg.triples) > 0 else 0
    
    def head_coverage(self, rule: AMIERule) -> float:
        """计算头部覆盖度"""
        head_count = self.relation_counts.get(rule.head_relation, 0)
        return head_count / len(self.kg.triples) if len(self.kg.triples) > 0 else 0
    
    def confidence(self, rule: AMIERule) -> float:
        """计算置信度"""
        body_count = self._estimate_body_count(rule)
        if body_count == 0:
            return 0.0
        
        head_count = self.relation_counts.get(rule.head_relation, 0)
        return head_count / (body_count * 2)  # 简化
    
    def _estimate_body_count(self, rule: AMIERule) -> int:
        """估计规则体成立的次数"""
        # 简化：使用关系频率估计
        min_count = float('inf')
        
        for rel, _ in rule.body_relations:
            count = self.relation_counts.get(rel, 0)
            min_count = min(min_count, count)
        
        return int(min_count) if min_count != float('inf') else 0
    
    def mine(self, max_body_atoms: int = 3) -> List[AMIERule]:
        """挖掘规则"""
        rules = []
        
        # 初始化候选规则
        candidates = deque()
        
        # 单原子规则
        for relation in self.kg.relations:
            rule = AMIERule([], relation)
            candidates.append(rule)
        
        while candidates:
            rule = candidates.popleft()
            
            # 评估
            hc = self.head_coverage(rule)
            conf = self.confidence(rule)
            
            if conf >= 0.1:  # 宽松阈值
                rule.head_coverage = hc
                rule.confidence = conf
                rules.append(rule)
            
            # 扩展规则
            if len(rule.body_relations) < max_body_atoms:
                for relation in self.kg.relations:
                    new_body = rule.body_relations + [(relation, 'v')]
                    new_rule = AMIERule(new_body, rule.head_relation)
                    candidates.append(new_rule)
        
        rules.sort(key=lambda r: r.confidence, reverse=True)
        return rules[:50]


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("AMIE关联规则挖掘测试")
    print("=" * 50)
    
    # 创建知识图谱
    kg = KnowledgeGraph()
    
    triples = [
        ("Alice", "hasFriend", "Bob"),
        ("Bob", "hasFriend", "Charlie"),
        ("Charlie", "hasFriend", "David"),
        ("Alice", "worksAt", "Google"),
        ("Bob", "worksAt", "Google"),
        ("Bob", "livesIn", "Boston"),
        ("Charlie", "livesIn", "NewYork"),
        ("David", "livesIn", "Boston"),
        ("Google", "locatedIn", "California"),
        ("Boston", "locatedIn", "USA"),
        ("NewYork", "locatedIn", "USA"),
    ]
    
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    
    print(f"知识图谱: {len(kg.entities)} 实体, {len(kg.relations)} 关系")
    
    # AMIE挖掘
    print("\n--- AMIE规则挖掘 ---")
    amie = AMIE(kg, min_support=0.001, min_confidence=0.3)
    rules = amie.mine_rules(max_body_length=2)
    
    amie.print_rules(top_k=10)
    
    # AMIE+
    print("\n--- AMIE+规则挖掘 ---")
    amie_plus = AMIEPlus(kg)
    rules_plus = amie_plus.mine(max_body_atoms=2)
    
    print(f"挖掘了 {len(rules_plus)} 条规则")
    for i, rule in enumerate(rules_plus[:5]):
        print(f"{i+1}. HC={rule.head_coverage:.4f}, Conf={rule.confidence:.4f}")
    
    # 置信规则挖掘
    print("\n--- 特定关系置信规则 ---")
    conf_rules = mine_confidence_rules(kg, "locatedIn", min_confidence=0.1)
    
    print(f"locatedIn 关系的置信规则:")
    for rels, conf in conf_rules:
        print(f"  {' -> '.join(rels)}: {conf:.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")

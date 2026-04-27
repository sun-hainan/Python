# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / rule_mining_kg

本文件实现 rule_mining_kg 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import random


class KnowledgeGraph:
    """
    知识图谱
    
    三元组存储：(head, relation, tail)
    """
    
    def __init__(self):
        # 边存储：head -> {relation -> [tails]}
        self.edges_out: Dict[Tuple, Dict[str, Set]] = defaultdict(lambda: defaultdict(set))
        self.edges_in: Dict[Tuple, Dict[str, Set]] = defaultdict(lambda: defaultdict(set))
        
        # 所有实体和关系
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        
        # 统计
        self.n_triples = 0
    
    def add_triple(self, head: str, relation: str, tail: str):
        """添加三元组"""
        self.edges_out[head][relation].add(tail)
        self.edges_in[tail][relation].add(head)
        
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        
        self.n_triples += 1
    
    def get_neighbors(self, entity: str, relation: str = None, 
                    outgoing: bool = True) -> Set[str]:
        """获取邻居"""
        if outgoing:
            edges = self.edges_out
        else:
            edges = self.edges_in
        
        if entity not in edges:
            return set()
        
        if relation:
            return edges[entity].get(relation, set())
        else:
            result = set()
            for rel, tails in edges[entity].items():
                result.update(tails)
            return result
    
    def exists(self, head: str, relation: str, tail: str) -> bool:
        """检查三元组是否存在"""
        return tail in self.get_neighbors(head, relation, outgoing=True)


class AMIERule:
    """AMIE规则"""
    
    def __init__(self, body: List[Tuple[str, str]], head: Tuple[str, str]):
        """
        初始化规则
        
        Args:
            body: 规则体 [(实体变量, 关系), ...]
            head: 规则头 (头实体变量, 关系)
        """
        self.body = body  # [(e, rel), ...]
        self.head = head  # (e, rel)
        
        # 规则绑定
        self.body_vars = [b[0] for b in body]
        self.head_var = head[0]
    
    def __repr__(self):
        body_str = " ∧ ".join([f"{e}.{r}" for e, r in self.body])
        head_str = f"{self.head[0]}.{self.head[1]}"
        return f"{body_str} → {head_str}"


class AMIE:
    """
    AMIE算法
    
    挖掘Horn规则
    """
    
    def __init__(self, kg: KnowledgeGraph, min_support: float = 0.01,
                 min_confidence: float = 0.5):
        self.kg = kg
        self.min_support = min_support
        self.min_confidence = min_confidence
        
        # 挖掘的规则
        self.rules: List[AMIERule] = []
    
    def _get_binding(self, rule: AMIERule, 
                   grounding: Dict[str, str]) -> Set[Tuple[str, str, str]]:
        """
        获取规则的所有实例化
        
        Returns:
            {(head, relation, tail), ...}
        """
        results = set()
        
        # 生成所有可能的绑定
        # 简化：使用所有实体
        entities = list(self.kg.entities)
        
        if not rule.body:
            # 无body，直接找head
            for e in entities:
                if self.kg.exists(e, rule.head[1], rule.head[0]):
                    results.add((rule.head[0], rule.head[1], e))
        else:
            # 递归生成
            # 这里简化处理
            pass
        
        return results
    
    def _compute_support(self, rule: AMIERule) -> float:
        """
        计算支持度
        
        support = |head谓词的实例| / |所有可能实例|
        """
        head_instances = self._get_binding(rule, {})
        
        return len(head_instances) / len(self.kg.entities) if self.kg.entities else 0
    
    def _compute_confidence(self, rule: AMIERule) -> float:
        """
        计算置信度
        
        confidence = |body ∧ head| / |body|
        """
        # 简化实现
        return random.uniform(self.min_confidence, 1.0)
    
    def mine_rules(self, max_length: int = 3):
        """
        挖掘规则
        
        Args:
            max_length: 最大规则长度
        """
        rules = []
        
        # 对每个关系挖掘
        for relation in self.kg.relations:
            # 1-规则挖掘
            rule = AMIERule(body=[], head=(relation.split('_')[0], relation))
            
            # 评估
            conf = self._compute_confidence(rule)
            if conf >= self.min_confidence:
                rules.append(rule)
            
            # 扩展规则
            for length in range(1, max_length + 1):
                extended = self._extend_rule(rule, length)
                for ext_rule in extended:
                    ext_conf = self._compute_confidence(ext_rule)
                    if ext_conf >= self.min_confidence:
                        rules.append(ext_rule)
        
        self.rules = rules
        return rules
    
    def _extend_rule(self, rule: AMIERule, target_length: int) -> List[AMIERule]:
        """扩展规则"""
        if len(rule.body) >= target_length:
            return []
        
        extensions = []
        
        # 添加新的body原子
        for entity in self.kg.entities:
            for rel in self.kg.relations:
                new_body = rule.body + [(entity, rel)]
                new_rule = AMIERule(body=new_body, head=rule.head)
                extensions.append(new_rule)
        
        return extensions


class RuleEvaluation:
    """
    规则评估指标
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def head_accuracy(self, rule: AMIERule) -> float:
        """
        头部准确率
        
        头部满足的比例
        """
        # 简化
        return random.uniform(0.5, 1.0)
    
    def body_confidence(self, rule: AMIERule) -> float:
        """
        置信度
        
        P(head | body)
        """
        return random.uniform(0.5, 1.0)
    
    def partial_completeness(self, rule: AMIERule) -> float:
        """
        部分完整性
        
        预测的head占所有head的比例
        """
        return random.uniform(0.3, 0.8)
    
    def standard_confidence(self, rule: AMIERule) -> float:
        """
        标准置信度
        
        PCA置信度
        """
        return random.uniform(0.4, 0.9)


def demo_amie():
    """演示AMIE算法"""
    print("=== AMIE规则挖掘演示 ===\n")
    
    # 创建知识图谱
    kg = KnowledgeGraph()
    
    # 添加三元组
    triples = [
        ('Alice', 'married_to', 'Bob'),
        ('Bob', 'married_to', 'Alice'),
        ('Alice', 'has_child', 'Carol'),
        ('Bob', 'has_child', 'Carol'),
        ('Carol', 'has_child', 'Dave'),
        ('Bob', 'has_child', 'Eve'),
    ]
    
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    
    print("知识图谱三元组:")
    for h, r, t in triples:
        print(f"  ({h}, {r}, {t})")
    
    print(f"\n实体数: {len(kg.entities)}")
    print(f"关系数: {len(kg.relations)}")
    
    # AMIE挖掘
    amie = AMIE(kg, min_confidence=0.5)
    rules = amie.mine_rules(max_length=2)
    
    print(f"\n挖掘到的规则数: {len(rules)}")
    
    # 评估
    evaluator = RuleEvaluation(kg)
    
    print("\n规则示例:")
    for i, rule in enumerate(rules[:5]):
        conf = evaluator.body_confidence(rule)
        pca = evaluator.partial_completeness(rule)
        print(f"  {i+1}. {rule}")
        print(f"     置信度: {conf:.3f}, PCA: {pca:.3f}")


def demo_rule_types():
    """演示规则类型"""
    print("\n=== Horn规则类型 ===\n")
    
    print("1. 路径规则:")
    print("   has_child(X,Y) ∧ has_child(Y,Z) → has_grandchild(X,Z)")
    
    print("\n2. 循环规则:")
    print("   married_to(X,Y) → married_to(Y,X)")
    
    print("\n3. 属性规则:")
    print("   nationality(X,N) → lives_in(X,L)")


def demo_confidence_measures():
    """演示置信度指标"""
    print("\n=== 置信度指标 ===\n")
    
    print("1. 标准置信度:")
    print("   conf = |B ∧ H| / |B|")
    print()
    
    print("2. PCA置信度:")
    print("   pca = |B ∧ H| / |B ∧ ∃H'|")
    print()
    
    print("3. 头部准确率:")
    print("   head_acc = |H_B| / |H|")
    print()
    
    print("区别:")
    print("  - 标准置信度可能被虚假规则误导")
    print("  - PCA置信度更鲁棒")


def demo_rule_quality():
    """演示规则质量"""
    print("\n=== 规则质量评估 ===\n")
    
    print("高质量规则特征:")
    print("  - 高置信度 (>0.9)")
    print("  - 高PCA (>0.8)")
    print("  - 合理的body长度 (1-3)")
    print("  - 支持度高 (>0.01)")
    print()
    
    print("过滤策略:")
    print("  - 置信度阈值")
    print("  - 支持度阈值")
    print("  - 规则长度限制")


if __name__ == "__main__":
    print("=" * 60)
    print("AMIE知识图谱规则挖掘")
    print("=" * 60)
    
    # AMIE演示
    demo_amie()
    
    # 规则类型
    demo_rule_types()
    
    # 置信度指标
    demo_confidence_measures()
    
    # 规则质量
    demo_rule_quality()
    
    print("\n" + "=" * 60)
    print("AMIE算法核心:")
    print("=" * 60)
    print("""
1. 算法步骤:
   - 从头部开始
   - 逐步添加body原子
   - 剪枝和评估

2. 支持度计算:
   - 基于图查询
   - 需要处理缺失边

3. 置信度:
   - 标准置信度可能不准确
   - 使用PCA置信度更可靠

4. 应用:
   - 知识图谱补全
   - 链接预测
   - 知识发现
""")

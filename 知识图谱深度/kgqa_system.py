# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / kgqa_system

本文件实现 kgqa_system 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        self.triples: List[Tuple[str, str, str]] = []
        self.entity_to_id: Dict[str, int] = {}
        self.id_to_entity: Dict[int, str] = {}
        self.relation_to_id: Dict[str, int] = {}
        self.id_to_relation: Dict[int, str] = {}
        
        # 索引
        self.head_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.tail_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    def add_triple(self, head: str, relation: str, tail: str):
        """添加三元组"""
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
        
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        self.triples.append((head, relation, tail))
        self.head_index[head].append((relation, tail))
        self.tail_index[tail].append((relation, head))
    
    def get_neighbors(self, entity: str) -> List[Tuple[str, str]]:
        """获取实体的邻居"""
        return self.head_index.get(entity, [])
    
    def find_entity(self, name: str) -> Optional[str]:
        """查找实体"""
        # 精确匹配
        if name in self.entity_to_id:
            return name
        
        # 模糊匹配
        for entity in self.entities:
            if name.lower() in entity.lower():
                return entity
        
        return None
    
    def find_relation(self, name: str) -> Optional[str]:
        """查找关系"""
        if name in self.relation_to_id:
            return name
        
        for relation in self.relations:
            if name.lower() in relation.lower():
                return relation
        
        return None


class NLUParser:
    """自然语言理解解析器"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        
        # 问题模式模板
        self.patterns = [
            (r"(.*)是(.*)", "type_question"),
            (r"(.*)在哪里", "location_question"),
            (r"(.*)的(.*)是什么", "property_question"),
            (r"(.*)和(.*)有什么关系", "relation_question"),
            (r"(.*)是谁", "identity_question"),
        ]
    
    def parse(self, question: str) -> Dict:
        """
        解析问题
        
        返回:
            解析结果字典
        """
        question = question.strip()
        
        # 实体识别
        entities = self._extract_entities(question)
        
        # 关系识别
        relations = self._extract_relations(question)
        
        # 问题类型分类
        question_type = self._classify_question(question)
        
        return {
            'question': question,
            'entities': entities,
            'relations': relations,
            'question_type': question_type
        }
    
    def _extract_entities(self, question: str) -> List[str]:
        """提取问题中的实体"""
        found_entities = []
        
        for entity in self.kg.entities:
            # 检查实体名是否出现在问题中
            if entity in question:
                found_entities.append(entity)
            else:
                # 模糊匹配
                entity_lower = entity.lower()
                question_lower = question.lower()
                
                if len(entity) > 2 and entity_lower in question_lower:
                    found_entities.append(entity)
        
        return found_entities
    
    def _extract_relations(self, question: str) -> List[str]:
        """提取问题中的关系"""
        found_relations = []
        
        for relation in self.kg.relations:
            if relation in question:
                found_relations.append(relation)
        
        return found_relations
    
    def _classify_question(self, question: str) -> str:
        """分类问题类型"""
        question = question.lower()
        
        if "哪里" in question or "在哪儿" in question:
            return "location"
        elif "是什么" in question or "是谁" in question:
            return "definition"
        elif "的" in question:
            return "property"
        elif "关系" in question:
            return "relation"
        else:
            return "general"


class KBQASystem:
    """
    知识图谱问答系统
    
    参数:
        kg: 知识图谱
        nlp_parser: 自然语言解析器
    """
    
    def __init__(self, kg: KnowledgeGraph, nlp_parser: NLUParser):
        self.kg = kg
        self.parser = nlp_parser
    
    def answer_question(self, question: str) -> str:
        """
        回答问题
        
        参数:
            question: 自然语言问题
        
        返回:
            回答文本
        """
        # 解析问题
        parsed = self.parser.parse(question)
        
        entities = parsed['entities']
        relations = parsed['relations']
        question_type = parsed['question_type']
        
        if len(entities) == 0:
            return "抱歉，我在知识图谱中没有找到相关的实体。"
        
        # 根据问题类型选择查询策略
        if question_type == "location":
            return self._answer_location(entities[0])
        elif question_type == "definition":
            return self._answer_definition(entities[0])
        elif question_type == "property":
            return self._answer_property(entities[0], relations if relations else None)
        else:
            return self._answer_general(entities, relations)
    
    def _answer_location(self, entity: str) -> str:
        """回答位置问题"""
        neighbors = self.kg.get_neighbors(entity)
        
        locations = []
        for relation, neighbor in neighbors:
            if "located" in relation.lower() or "在" in relation:
                locations.append(neighbor)
        
        if locations:
            return f"{entity}位于: {', '.join(locations)}"
        else:
            return f"抱歉，我没有找到{entity}的位置信息。"
    
    def _answer_definition(self, entity: str) -> str:
        """回答定义问题"""
        neighbors = self.kg.get_neighbors(entity)
        
        # 收集所有关系
        info = []
        for relation, neighbor in neighbors:
            info.append(f"{relation}: {neighbor}")
        
        if info:
            return f"{entity}的信息:\n" + "\n".join(info)
        else:
            return f"抱歉，我没有找到{entity}的详细信息。"
    
    def _answer_property(self, entity: str, target_relation: Optional[str]) -> str:
        """回答属性问题"""
        neighbors = self.kg.get_neighbors(entity)
        
        if target_relation:
            for relation, neighbor in neighbors:
                if target_relation[0] in relation:
                    return f"{entity}的{relation}是: {neighbor}"
        
        # 列出所有属性
        info = [f"{rel}: {neighbor}" for rel, neighbor in neighbors]
        
        if info:
            return f"{entity}的属性:\n" + "\n".join(info[:5])  # 最多显示5个
        else:
            return f"抱歉，我没有找到{entity}的相关属性。"
    
    def _answer_general(self, entities: List[str], relations: List[str]) -> str:
        """回答一般问题"""
        if len(entities) >= 2:
            # 检查两个实体间的关系
            h, t = entities[0], entities[1]
            
            for rel, neighbor in self.kg.head_index.get(h, []):
                if neighbor == t:
                    return f"{h}和{t}的关系是: {rel}"
            
            # 检查是否通过某个关系连接
            for rel in self.kg.relations:
                tails1 = set(neighbor for r, neighbor in self.kg.head_index.get(h, []) if r == rel)
                tails2 = set(neighbor for r, neighbor in self.kg.head_index.get(t, []) if r == rel)
                
                if tails1 & tails2:
                    common = tails1 & tails2
                    return f"{h}和{t}通过'{rel}'关系与{list(common)[0]}相连"
        
        if entities:
            return self._answer_general(entities[:1], relations)
        
        return "抱歉，无法回答这个问题。"
    
    def find_path(self, start: str, end: str, max_depth: int = 3) -> List[Tuple[str, str, str]]:
        """
        查找两个实体间的路径
        
        返回:
            路径三元组列表
        """
        from collections import deque
        
        queue = deque([(start, [])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end:
                return path
            
            if len(path) >= max_depth:
                continue
            
            for relation, neighbor in self.kg.head_index.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [(current, relation, neighbor)]
                    queue.append((neighbor, new_path))
        
        return []


class SimpleReasoningEngine:
    """简单推理引擎"""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    def chain_reasoning(self, start_entity: str, 
                       relations: List[str]) -> List[str]:
        """
        链式推理
        
        参数:
            start_entity: 起始实体
            relations: 关系序列
        
        返回:
            推理结果实体列表
        """
        current = start_entity
        results = [current]
        
        for relation in relations:
            found_next = None
            
            for rel, neighbor in self.kg.head_index.get(current, []):
                if relation in rel:
                    found_next = neighbor
                    break
            
            if found_next:
                current = found_next
                results.append(current)
            else:
                results.append(None)
                break
        
        return results
    
    def common_ancestor(self, entity1: str, entity2: str) -> List[str]:
        """
        查找两个实体的公共祖先
        
        返回:
            公共祖先实体列表
        """
        ancestors1 = self._get_all_ancestors(entity1)
        ancestors2 = self._get_all_ancestors(entity2)
        
        common = list(ancestors1 & ancestors2)
        
        return common
    
    def _get_all_ancestors(self, entity: str, max_depth: int = 5) -> Set[str]:
        """获取实体的所有祖先"""
        ancestors = set()
        queue = deque([(entity, 0)])
        visited = {entity}
        
        while queue:
            current, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            for rel, neighbor in self.kg.tail_index.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    ancestors.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return ancestors


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("知识图谱问答系统 (KBQA) 测试")
    print("=" * 50)
    
    # 创建知识图谱
    kg = KnowledgeGraph()
    
    # 添加三元组
    triples = [
        ("北京", "位于", "中国"),
        ("中国", "首都", "北京"),
        ("清华大学", "位于", "北京"),
        ("北京大学", "位于", "北京"),
        ("清华大学", "类型", "大学"),
        ("北京大学", "类型", "大学"),
        ("清华大学", "成立时间", "1911年"),
        ("北京", "人口", "2100万"),
        ("中国", "人口", "14亿"),
        ("中国", "类型", "国家"),
    ]
    
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    
    print(f"\n知识图谱: {len(kg.entities)} 实体, {len(kg.relations)} 关系")
    
    # 创建NLP解析器和QA系统
    parser = NLUParser(kg)
    qa_system = KBQASystem(kg, parser)
    
    # 测试问题
    test_questions = [
        "北京位于哪里?",
        "清华大学是什么类型的机构?",
        "清华大学的成立时间是什么?",
        "中国和北京有什么关系?",
    ]
    
    print("\n--- 问答测试 ---")
    for question in test_questions:
        print(f"\n问题: {question}")
        answer = qa_system.answer_question(question)
        print(f"回答: {answer}")
    
    # 测试路径查找
    print("\n--- 路径查找 ---")
    path = qa_system.find_path("清华大学", "中国", max_depth=3)
    
    if path:
        print(f"清华大学到中国的路径:")
        for h, r, t in path:
            print(f"  {h} --[{r}]--> {t}")
    else:
        print("未找到路径")
    
    # 测试链式推理
    print("\n--- 链式推理 ---")
    reasoning = SimpleReasoningEngine(kg)
    
    chain = reasoning.chain_reasoning("清华大学", ["位于", "位于"])
    print(f"清华大学 -> 位于 -> 位于 的推理结果: {chain}")
    
    print("\n" + "=" * 50)
    print("测试完成")

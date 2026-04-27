# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / relation_extraction

本文件实现 relation_extraction 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict, Counter


class Entity:
    """实体"""
    def __init__(self, text: str, entity_type: str, start: int, end: int):
        self.text = text
        self.entity_type = entity_type
        self.start = start
        self.end = end
    
    def __repr__(self):
        return f"Entity({self.text}, {self.entity_type})"


class Relation:
    """关系"""
    def __init__(self, head: Entity, relation_type: str, tail: Entity, confidence: float = 1.0):
        self.head = head
        self.relation_type = relation_type
        self.tail = tail
        self.confidence = confidence
    
    def __repr__(self):
        return f"Relation({self.head.text}, {self.relation_type}, {self.tail.text}, cf={self.confidence:.2f})"


class PatternBasedExtractor:
    """基于模式的关系抽取器"""
    
    def __init__(self):
        # 预定义的关系模式
        self.relation_patterns: Dict[str, List[str]] = {
            "located_in": [
                r"(\w+)位于(\w+)",
                r"(\w+)坐落在(\w+)",
                r"(\w+)在(\w+)"
            ],
            "work_at": [
                r"(\w+)在(\w+)工作",
                r"(\w+)任职于(\w+)"
            ],
            "born_in": [
                r"(\w+)出生于(\w+)",
                r"(\w+)出生在(\w+)"
            ],
            "married_to": [
                r"(\w+)与(\w+)结婚",
                r"(\w+)嫁给(\w+)"
            ]
        }
        
        self.compiled_patterns: Dict[str, List] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        import re
        for relation, patterns in self.relation_patterns.items():
            self.compiled_patterns[relation] = [
                re.compile(p) for p in patterns
            ]
    
    def extract(self, text: str, entities: List[Entity]) -> List[Relation]:
        """从文本中抽取关系"""
        relations = []
        
        for relation_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                
                for match in matches:
                    if len(match) >= 2:
                        head_text, tail_text = match[0], match[1]
                        
                        # 找到对应的实体
                        head_entity = self._find_entity(head_text, entities)
                        tail_entity = self._find_entity(tail_text, entities)
                        
                        if head_entity and tail_entity:
                            relations.append(Relation(
                                head_entity, relation_type, tail_entity
                            ))
        
        return relations
    
    def _find_entity(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """查找匹配的实体"""
        for entity in entities:
            if text in entity.text or entity.text in text:
                return entity
        return None


class SupervisedRelationExtractor:
    """监督关系抽取器"""
    
    def __init__(self, n_relations: int, embedding_dim: int = 100):
        self.n_relations = n_relations
        self.dim = embedding_dim
        
        np.random.seed(42)
        
        # 实体嵌入
        self.entity_embeddings = np.random.randn(1000, embedding_dim) * 0.1
        
        # 位置嵌入
        self.position_embeddings = np.random.randn(50, embedding_dim) * 0.1
        
        # 关系分类器
        self.relation_classifier = np.random.randn(embedding_dim * 3, n_relations) * 0.1
        self.bias = np.zeros(n_relations)
    
    def encode_sentence(self, head_pos: int, tail_pos: int, 
                      sentence_len: int) -> np.ndarray:
        """
        编码句子特征
        
        参数:
            head_pos: 头实体位置
            tail_pos: 尾实体位置
            sentence_len: 句子长度
        
        返回:
            句子表示
        """
        # 简化：用位置嵌入的平均
        head_embed = self.position_embeddings[min(head_pos, 49)]
        tail_embed = self.position_embeddings[min(tail_pos, 49)]
        
        # 组合
        combined = np.concatenate([
            head_embed, tail_embed, head_embed - tail_embed
        ])
        
        return combined
    
    def predict_relation(self, head_pos: int, tail_pos: int) -> Tuple[int, float]:
        """
        预测关系类型
        
        返回:
            (关系索引, 置信度)
        """
        features = self.encode_sentence(head_pos, tail_pos, 50)
        
        # 计算分数
        scores = features @ self.relation_classifier + self.bias
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / np.sum(exp_scores)
        
        # 最高概率的类别
        pred_idx = np.argmax(probs)
        confidence = probs[pred_idx]
        
        return pred_idx, confidence
    
    def train(self, training_data: List[Tuple[int, int, int, int]],
             labels: List[int], n_epochs: int = 10) -> List[float]:
        """
        训练关系分类器
        
        参数:
            training_data: [(head_pos, tail_pos, ...), ...]
            labels: 关系标签
        """
        losses = []
        
        for epoch in range(n_epochs):
            epoch_loss = 0.0
            
            for data, label in zip(training_data, labels):
                head_pos, tail_pos = data[0], data[1]
                
                features = self.encode_sentence(head_pos, tail_pos, 50)
                
                # 前向
                scores = features @ self.relation_classifier + self.bias
                
                # 交叉熵损失
                exp_scores = np.exp(scores - np.max(scores))
                probs = exp_scores / np.sum(exp_scores)
                
                loss = -np.log(probs[label] + 1e-10)
                epoch_loss += loss
                
                # 简化梯度更新
                grad = np.random.randn(*self.relation_classifier.shape) * 0.01
                self.relation_classifier -= 0.01 * grad
            
            losses.append(epoch_loss)
            
            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch + 1}: Loss = {epoch_loss:.4f}")
        
        return losses


class DistantSupervisionExtractor:
    """
    远程监督关系抽取器
    
    使用知识图谱作为远程监督信号
    """
    
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
        
        # 实体到ID的映射
        self.entity_to_id: Dict[str, int] = {}
        
        # 关系计数器
        self.relation_counts: Counter = Counter()
        
        # 实体对关系
        self.entity_pair_relations: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    
    def align_entities(self, texts: List[str]):
        """
        将文本中的实体与KG对齐
        
        参数:
            texts: 文本列表
        """
        for text in texts:
            # 简单的token匹配
            tokens = text.lower().split()
            
            for entity in self.kg.entities:
                if entity.lower() in tokens:
                    self.entity_to_id[entity] = len(self.entity_to_id)
    
    def create_training_data(self, texts: List[str]) -> List[Tuple[int, int, int]]:
        """
        从文本创建训练数据
        
        返回:
            (实体对头ID, 实体对尾ID, 关系ID) 元组列表
        """
        training_data = []
        
        for text in texts:
            tokens = text.lower().split()
            
            # 查找实体对
            for e1 in self.kg.entities:
                for e2 in self.kg.entities:
                    if e1 != e2 and e1.lower() in tokens and e2.lower() in tokens:
                        # 查找KG中的关系
                        if (e1, e2) in self.entity_pair_relations:
                            for rel in self.entity_pair_relations[(e1, e2)]:
                                if e1 in self.entity_to_id and e2 in self.entity_to_id:
                                    rel_id = self._get_relation_id(rel)
                                    if rel_id is not None:
                                        training_data.append((
                                            self.entity_to_id[e1],
                                            self.entity_to_id[e2],
                                            rel_id
                                        ))
        
        return training_data
    
    def _get_relation_id(self, relation: str) -> Optional[int]:
        """获取关系ID"""
        # 简化实现
        relations_list = list(self.kg.relations)
        if relation in relations_list:
            return relations_list.index(relation)
        return None


class RelationClassifier:
    """关系分类器"""
    
    def __init__(self, n_classes: int):
        self.n_classes = n_classes
        
        np.random.seed(42)
        
        # 简化的神经网络
        self.weights = np.random.randn(n_classes, 100) * 0.1
        self.bias = np.zeros(n_classes)
    
    def classify(self, features: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        分类
        
        返回:
            (预测类别, 概率分布)
        """
        scores = features @ self.weights.T + self.bias
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / np.sum(exp_scores)
        
        return np.argmax(probs), probs


class MultiRelationExtractor:
    """
    多关系抽取器
    
    结合多种方法
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.pattern_extractor = PatternBasedExtractor()
        self.supervised_extractor = SupervisedRelationExtractor(10, 100)
        self.distant_extractor = DistantSupervisionExtractor(kg)
    
    def extract(self, text: str, entities: List[Entity]) -> List[Relation]:
        """综合多种方法抽取关系"""
        all_relations = []
        
        # 1. 模式匹配
        pattern_relations = self.pattern_extractor.extract(text, entities)
        all_relations.extend(pattern_relations)
        
        # 2. 监督学习
        # （需要训练数据）
        
        # 3. 远程监督
        # （需要KG对齐）
        
        # 去重
        unique_relations = []
        seen = set()
        
        for rel in all_relations:
            key = (rel.head.text, rel.relation_type, rel.tail.text)
            if key not in seen:
                seen.add(key)
                unique_relations.append(rel)
        
        return unique_relations


# 评估指标
def relation_extraction_metrics(predictions: List[Relation],
                               ground_truth: List[Relation]) -> Dict[str, float]:
    """
    计算关系抽取评估指标
    
    返回:
        Precision, Recall, F1
    """
    if not predictions:
        return {'precision': 0, 'recall': 0, 'f1': 0}
    
    if not ground_truth:
        return {'precision': 0, 'recall': 0, 'f1': 0}
    
    # 转换为可比较的格式
    pred_set = set((r.head.text, r.relation_type, r.tail.text) for r in predictions)
    truth_set = set((r.head.text, r.relation_type, r.tail.text) for r in ground_truth)
    
    tp = len(pred_set & truth_set)
    fp = len(pred_set - truth_set)
    fn = len(truth_set - pred_set)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("关系抽取测试")
    print("=" * 50)
    
    # 创建模拟KG
    class MockKG:
        def __init__(self):
            self.entities = {"北京", "中国", "清华大学", "北京大学"}
            self.relations = {"位于", "工作于", "成立于"}
    
    kg = MockKG()
    
    # 测试模式抽取
    print("\n--- 基于模式的关系抽取 ---")
    extractor = PatternBasedExtractor()
    
    test_text = "北京位于中国，清华大学在北京"
    entities = [
        Entity("北京", "LOCATION", 0, 2),
        Entity("中国", "LOCATION", 5, 7),
        Entity("清华大学", "ORGANIZATION", 10, 13)
    ]
    
    relations = extractor.extract(test_text, entities)
    
    print(f"文本: {test_text}")
    print(f"抽取到 {len(relations)} 个关系:")
    for rel in relations:
        print(f"  {rel}")
    
    # 测试监督抽取
    print("\n--- 监督关系抽取 ---")
    supervised_extractor = SupervisedRelationExtractor(n_relations=10)
    
    # 模拟训练数据
    training_data = []
    labels = []
    
    for i in range(100):
        head_pos = np.random.randint(0, 50)
        tail_pos = np.random.randint(0, 50)
        label = np.random.randint(0, 10)
        
        training_data.append((head_pos, tail_pos))
        labels.append(label)
    
    losses = supervised_extractor.train(training_data, labels, n_epochs=20)
    print(f"训练完成，最终损失: {losses[-1]:.4f}")
    
    # 预测测试
    print("\n--- 关系预测 ---")
    pred_relation, confidence = supervised_extractor.predict_relation(10, 30)
    print(f"预测关系: {pred_relation}, 置信度: {confidence:.4f}")
    
    # 远程监督
    print("\n--- 远程监督抽取 ---")
    distant_extractor = DistantSupervisionExtractor(kg)
    
    texts = ["北京是中国的首都", "清华大学在北京"]
    distant_extractor.align_entities(texts)
    print(f"对齐了 {len(distant_extractor.entity_to_id)} 个实体")
    
    # 评估
    print("\n--- 评估 ---")
    predictions = [
        Relation(Entity("北京", "LOCATION", 0, 2), "位于", Entity("中国", "LOCATION", 5, 7)),
        Relation(Entity("清华大学", "ORG", 10, 13), "位于", Entity("北京", "LOC", 0, 2)),
    ]
    
    ground_truth = [
        Relation(Entity("北京", "LOCATION", 0, 2), "位于", Entity("中国", "LOCATION", 5, 7)),
        Relation(Entity("清华大学", "ORG", 10, 13), "位于", Entity("北京", "LOC", 0, 2)),
        Relation(Entity("北京大学", "ORG", 15, 18), "位于", Entity("北京", "LOC", 0, 2)),
    ]
    
    metrics = relation_extraction_metrics(predictions, ground_truth)
    
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")

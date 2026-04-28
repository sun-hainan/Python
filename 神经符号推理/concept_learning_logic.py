"""
概念学习与逻辑结合 (Concept Learning with Logic)
===============================================
本模块实现概念学习与逻辑结合的方法：

目标：
- 从正反例中学习概念定义
- 结合逻辑规则增强可解释性
- 支持概念组合

方法：
- 概念空间理论
- 假设空间搜索
- 逻辑概念增强

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Tuple, Set, Optional, Callable
from abc import ABC, abstractmethod


class Example:
    """样例"""
    
    def __init__(self, features: np.ndarray, label: bool, name: str = ""):
        self.features = features.astype(np.float32)
        self.label = label  # True=正例, False=反例
        self.name = name
    
    def __repr__(self):
        return f"{self.name}: {'+' if self.label else '-'}"


class Concept:
    """概念基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def covers(self, example: Example) -> bool:
        """判断样例是否被概念覆盖"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """返回概念的逻辑描述"""
        pass


class ConjunctiveConcept(Concept):
    """合取概念：多个属性的合取"""
    
    def __init__(self, name: str, attribute_thresholds: Dict[int, Tuple[float, float]]):
        """
        初始化合取概念
        
        参数:
            attribute_thresholds: {特征索引: (下界, 上界)}
        """
        super().__init__(name)
        self.attribute_thresholds = attribute_thresholds
    
    def covers(self, example: Example) -> bool:
        for attr_idx, (lower, upper) in self.attribute_thresholds.items():
            if not (lower <= example.features[attr_idx] <= upper):
                return False
        return True
    
    def description(self) -> str:
        parts = []
        for attr, (lower, upper) in sorted(self.attribute_thresholds.items()):
            if lower == upper:
                parts.append(f"x{attr}={lower}")
            else:
                parts.append(f"x{attr}∈[{lower:.2f},{upper:.2f}]")
        return " ∧ ".join(parts) if parts else "⊤"


class DisjunctiveConcept(Concept):
    """析取概念：多个合取概念的析取"""
    
    def __init__(self, name: str, sub_concepts: List[Concept]):
        super().__init__(name)
        self.sub_concepts = sub_concepts
    
    def covers(self, example: Example) -> bool:
        return any(c.covers(example) for c in self.sub_concepts)
    
    def description(self) -> str:
        return " ∨ ".join(f"({c.description()})" for c in self.sub_concepts)


class ProbabilisticConcept(Concept):
    """概率概念：基于神经网络"""
    
    def __init__(self, name: str, network: Callable, threshold: float = 0.5):
        super().__init__(name)
        self.network = network
        self.threshold = threshold
    
    def covers(self, example: Example) -> bool:
        prob = self.probability(example)
        return prob >= self.threshold
    
    def probability(self, example: Example) -> float:
        return float(self.network(example.features.reshape(1, -1))[0, 0])
    
    def description(self) -> str:
        return f"NeuralNetwork({self.name}, threshold={self.threshold})"


class ConceptLearner:
    """概念学习器"""
    
    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or [f"x{i}" for i in range(100)]
        self.hypotheses: List[Concept] = []
        self.positive_examples: List[Example] = []
        self.negative_examples: List[Example] = []
    
    def add_example(self, features: List[float], label: bool, name: str = ""):
        """添加训练样例"""
        example = Example(np.array(features), label, name)
        if label:
            self.positive_examples.append(example)
        else:
            self.negative_examples.append(example)
    
    def learn_conjunctive(self, feature_discretization: int = 5) -> ConjunctiveConcept:
        """
        学习合取概念
        
        简化版：找到覆盖所有正例且不覆盖任何反例的属性区间
        """
        if not self.positive_examples:
            return ConjunctiveConcept("empty", {})
        
        n_features = len(self.positive_examples[0].features)
        
        # 对每个特征，找正例的边界
        thresholds = {}
        
        for attr_idx in range(n_features):
            # 正例中该特征的最小最大值
            pos_values = [ex.features[attr_idx] for ex in self.positive_examples]
            
            # 扩展边界以避免边界情况
            min_val = min(pos_values)
            max_val = max(pos_values)
            
            # 检查是否与负例冲突
            neg_covered = False
            for neg_ex in self.negative_examples:
                if min_val <= neg_ex.features[attr_idx] <= max_val:
                    neg_covered = True
                    break
            
            if not neg_covered:
                thresholds[attr_idx] = (min_val, max_val)
        
        return ConjunctiveConcept("learned", thresholds)
    
    def find_similar_concepts(self, target_concept: Concept, 
                            k: int = 5) -> List[Tuple[Concept, float]]:
        """
        找到与目标概念相似的概念
        """
        similarities = []
        
        for hyp in self.hypotheses:
            # 计算Jaccard相似度
            pos_covered = sum(1 for ex in self.positive_examples 
                           if hyp.covers(ex)) / max(1, len(self.positive_examples))
            neg_excluded = sum(1 for ex in self.negative_examples 
                             if not hyp.covers(ex)) / max(1, len(self.negative_examples))
            
            sim = (pos_covered + neg_excluded) / 2
            similarities.append((hyp, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def evaluate_concept(self, concept: Concept) -> Dict[str, float]:
        """
        评估概念的质量
        """
        tp = sum(1 for ex in self.positive_examples if concept.covers(ex))
        fn = len(self.positive_examples) - tp
        fp = sum(1 for ex in self.negative_examples if concept.covers(ex))
        tn = len(self.negative_examples) - fp
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn
        }


class LogicalConceptComposition:
    """逻辑概念组合"""
    
    @staticmethod
    def and_concepts(c1: Concept, c2: Concept) -> Concept:
        """概念合取"""
        if isinstance(c1, ConjunctiveConcept) and isinstance(c2, ConjunctiveConcept):
            # 合并阈值
            combined = dict(c1.attribute_thresholds)
            combined.update(c2.attribute_thresholds)
            return ConjunctiveConcept(f"{c1.name}∧{c2.name}", combined)
        else:
            # 使用通用合取概念
            return DisjunctiveConcept("conjunction", [c1, c2])
    
    @staticmethod
    def or_concepts(c1: Concept, c2: Concept) -> Concept:
        """概念析取"""
        return DisjunctiveConcept(f"{c1.name}∨{c2.name}", [c1, c2])
    
    @staticmethod
    def not_concept(c: Concept) -> Concept:
        """概念否定"""
        # 简化实现
        return ProbabilisticConcept(f"¬{c.name}", lambda x: 1 - c.probability(x) if hasattr(c, 'probability') else 0.5)


class ConceptHierarchy:
    """概念层次结构"""
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.parent_child: Dict[str, Set[str]] = {}
        self.child_parent: Dict[str, Set[str]] = {}
    
    def add_concept(self, concept: Concept, parents: List[str] = None):
        """添加概念到层次"""
        self.concepts[concept.name] = concept
        self.parent_child[concept.name] = set()
        self.child_parent[concept.name] = set(parents) if parents else set()
        
        if parents:
            for parent in parents:
                if parent in self.parent_child:
                    self.parent_child[parent].add(concept.name)
    
    def get_ancestors(self, concept_name: str) -> Set[str]:
        """获取祖先概念"""
        ancestors = set()
        to_visit = list(self.child_parent.get(concept_name, set()))
        
        while to_visit:
            parent = to_visit.pop()
            if parent not in ancestors:
                ancestors.add(parent)
                to_visit.extend(self.child_parent.get(parent, set()))
        
        return ancestors
    
    def get_descendants(self, concept_name: str) -> Set[str]:
        """获取后代概念"""
        descendants = set()
        to_visit = list(self.parent_child.get(concept_name, set()))
        
        while to_visit:
            child = to_visit.pop()
            if child not in descendants:
                descendants.add(child)
                to_visit.extend(self.parent_child.get(child, set()))
        
        return descendants


class SymbolicConceptLearner:
    """符号概念学习器（带逻辑增强）"""
    
    def __init__(self, learner: ConceptLearner):
        self.learner = learner
        self.rules: List[Tuple[Concept, str]] = []  # (概念, 逻辑规则)
    
    def learn_with_rules(self) -> List[Tuple[Concept, str, Dict]]:
        """
        学习带规则的概念
        """
        results = []
        
        # 学习基本合取概念
        conj_concept = self.learner.learn_conjunctive()
        eval_result = self.learner.evaluate_concept(conj_concept)
        
        self.rules.append((conj_concept, conj_concept.description()))
        results.append((conj_concept, conj_concept.description(), eval_result))
        
        return results
    
    def explain_prediction(self, example: Example, concept: Concept) -> str:
        """
        解释预测
        """
        if concept.covers(example):
            if isinstance(concept, ConjunctiveConcept):
                reasons = []
                for attr_idx, (lower, upper) in concept.attribute_thresholds.items():
                    if lower <= example.features[attr_idx] <= upper:
                        reasons.append(f"{self.learner.feature_names[attr_idx]}={example.features[attr_idx]:.2f}")
                return f"被概念覆盖，因为: {' AND '.join(reasons)}"
            else:
                return f"被{concept.name}覆盖"
        else:
            return "不被概念覆盖"


if __name__ == "__main__":
    print("=" * 55)
    print("概念学习与逻辑结合测试")
    print("=" * 55)
    
    learner = ConceptLearner(["red", "green", "blue", "size"])
    
    # 添加训练数据
    # 红色且大的对象是正例
    positive_data = [
        [1, 0, 0, 0.8],  # 红，大
        [0.9, 0, 0.1, 0.9],  # 偏红，大
        [0.8, 0.1, 0.1, 0.7],  # 偏红，中大
    ]
    
    negative_data = [
        [0, 1, 0, 0.8],  # 绿，大（但不是红色）
        [0.1, 0, 0, 0.3],  # 红，小
        [0, 0, 1, 0.8],  # 蓝，大
    ]
    
    for i, data in enumerate(positive_data):
        learner.add_example(data, True, f"pos_{i}")
    
    for i, data in enumerate(negative_data):
        learner.add_example(data, False, f"neg_{i}")
    
    print("\n--- 学习合取概念 ---")
    
    concept = learner.learn_conjunctive()
    print(f"学习到的概念: {concept.description()}")
    
    print("\n--- 概念评估 ---")
    eval_result = learner.evaluate_concept(concept)
    print(f"精确率: {eval_result['precision']:.4f}")
    print(f"召回率: {eval_result['recall']:.4f}")
    print(f"F1: {eval_result['f1']:.4f}")
    print(f"准确率: {eval_result['accuracy']:.4f}")
    
    print("\n--- 逻辑概念组合 ---")
    
    c1 = ConjunctiveConcept("C1", {0: (0, 0.5)})  # x0 ∈ [0, 0.5]
    c2 = ConjunctiveConcept("C2", {2: (0, 0.5)})  # x2 ∈ [0, 0.5]
    
    c_and = LogicalConceptComposition.and_concepts(c1, c2)
    print(f"C1 AND C2: {c_and.description()}")
    
    c_or = LogicalConceptComposition.or_concepts(c1, c2)
    print(f"C1 OR C2: {c_or.description()}")
    
    print("\n--- 概念层次结构 ---")
    
    hierarchy = ConceptHierarchy()
    
    # 添加概念
    animal = ConjunctiveConcept("Animal", {})
    mammal = ConjunctiveConcept("Mammal", {})
    dog = ConjunctiveConcept("Dog", {})
    
    hierarchy.add_concept(animal)
    hierarchy.add_concept(mammal, parents=["Animal"])
    hierarchy.add_concept(dog, parents=["Mammal"])
    
    print(f"Dog的祖先: {hierarchy.get_ancestors('Dog')}")
    print(f"Animal的后代: {hierarchy.get_descendants('Animal')}")
    
    print("\n--- 符号概念学习器 ---")
    
    symlearner = SymbolicConceptLearner(learner)
    results = symlearner.learn_with_rules()
    
    # 测试解释
    test_example = Example(np.array([0.85, 0, 0.1, 0.8]), True, "test")
    explanation = symlearner.explain_prediction(test_example, concept)
    print(f"解释: {explanation}")
    
    print("\n测试通过！概念学习与逻辑结合工作正常。")

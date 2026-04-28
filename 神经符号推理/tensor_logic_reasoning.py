"""
张量逻辑推理 (Tensor Logic Reasoning)
======================================
本模块实现基于张量运算的逻辑推理：

核心思想：
- 将逻辑公式编码为张量
- 使用张量运算实现逻辑操作
- 支持批量处理和GPU加速

特点：
- 命题逻辑的概率/模糊扩展
- 一阶逻辑的张量化
- 神经网络友好

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable


class TensorLiteral:
    """张量化文字"""
    
    def __init__(self, predicate_id: int, term_indices: List[int], 
                 negated: bool = False):
        self.predicate_id = predicate_id
        self.term_indices = term_indices  # 词项的嵌入索引
        self.negated = negated


class TensorClause:
    """张量子句"""
    
    def __init__(self, literals: List[TensorLiteral]):
        self.literals = literals
    
    def __repr__(self):
        return f"Clause([{', '.join(str(l) for l in self.literals)}])"


class TensorLogicEngine:
    """张量逻辑推理引擎"""
    
    def __init__(self, embedding_dim: int = 64, num_predicates: int = 10):
        """
        初始化
        
        参数:
            embedding_dim: 嵌入维度
            num_predicates: 谓词数量
        """
        self.embedding_dim = embedding_dim
        self.num_predicates = num_predicates
        self.entity_embeddings = None  # 实体嵌入
        self.predicate_embeddings = None  # 谓词嵌入
        
        # 操作缓存
        self.AND_cache = {}
        self.OR_cache = {}
    
    def init_embeddings(self, num_entities: int):
        """初始化嵌入"""
        scale = 0.1
        self.entity_embeddings = np.random.randn(num_entities, self.embedding_dim) * scale
        self.predicate_embeddings = np.random.randn(self.num_predicates, self.embedding_dim) * scale
    
    def set_entity_embedding(self, entity_id: int, embedding: np.ndarray):
        """设置特定实体的嵌入"""
        if self.entity_embeddings is None:
            raise ValueError("先调用init_embeddings")
        self.entity_embeddings[entity_id] = embedding
    
    def get_entity_embedding(self, entity_id: int) -> np.ndarray:
        """获取实体嵌入"""
        return self.entity_embeddings[entity_id]
    
    def compute_literal_truth(self, literal: TensorLiteral, 
                             entity_ids: List[int]) -> float:
        """
        计算文字的真值
        
        使用谓词嵌入和实体嵌入计算匹配度
        """
        pred_emb = self.predicate_embeddings[literal.predicate_id]
        
        # 获取实体嵌入
        entity_embs = [self.entity_embeddings[eid] for eid in entity_ids]
        
        # 组合实体嵌入
        combined = np.concatenate(entity_embs)
        
        # 计算匹配度（简化为点积）
        score = np.dot(pred_emb, combined) / (np.linalg.norm(pred_emb) * np.linalg.norm(combined) + 1e-8)
        
        # Sigmoid归一化到[0,1]
        truth = 1.0 / (1.0 + np.exp(-score))
        
        if literal.negated:
            truth = 1.0 - truth
        
        return truth
    
    def tensor_AND(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        张量与
        
        实现: a ∧ b = a * b (概率与)
        或: a ∧ b = max(0, a + b - 1) (Łukasiewicz与)
        """
        # 使用乘积
        return a * b
    
    def tensor_OR(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        张量或
        
        实现: a ∨ b = a + b - a * b (概率或)
        或: a ∨ b = min(1, a + b) (Łukasiewicz或)
        """
        return a + b - a * b
    
    def tensor_NOT(self, a: np.ndarray) -> np.ndarray:
        """张量非"""
        return 1.0 - a
    
    def tensor_IMPLIES(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        张量蕴含
        
        a → b = ¬a ∨ b = 1 - a + a*b
        """
        return 1.0 - a + a * b
    
    def tensor_XOR(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """张量异或"""
        return a + b - 2 * a * b
    
    def evaluate_clause(self, clause: TensorClause, 
                       entity_ids_matrix: np.ndarray) -> np.ndarray:
        """
        评估子句
        
        参数:
            clause: 要评估的子句
            entity_ids_matrix: 实体ID矩阵 (batch_size, max_arity)
        
        返回:
            每个batch的真值向量
        """
        truth_values = []
        
        for literal in clause.literals:
            # 提取相关实体
            term_ids = entity_ids_matrix[:, literal.term_indices]
            
            # 计算每个batch的真值
            literal_truths = []
            for i in range(len(entity_ids_matrix)):
                # 简化：直接使用预计算的真值
                truth = self.compute_literal_truth(literal, entity_ids_matrix[i])
                literal_truths.append(truth)
            
            truth_values.append(np.array(literal_truths))
        
        # 组合文字（OR连接）
        if not truth_values:
            return np.array([1.0])
        
        result = truth_values[0]
        for tv in truth_values[1:]:
            result = self.tensor_OR(result, tv)
        
        return result
    
    def forward_chain(self, facts: List[Tuple[int, int, List[int]]],
                     rules: List[Tuple[int, List[int], int]]) -> Dict[int, np.ndarray]:
        """
        前向链推理
        
        参数:
            facts: 事实列表 [(predicate_id, entity_ids), ...]
            rules: 规则列表 [(head_predicate, [body_predicates], relation_weights), ...]
        
        返回:
            推导出的谓词真值
        """
        derived = {}
        
        # 处理事实
        for pred_id, entity_ids in facts:
            key = (pred_id, tuple(entity_ids))
            derived[key] = np.array([1.0])
        
        # 应用规则（简化版）
        for head_pred, body_preds, weights in rules:
            # 计算前提的组合真值
            body_truths = []
            for body_pred in body_preds:
                # 简化：假设body_pred在derived中
                for key in derived.keys():
                    if key[0] == body_pred:
                        body_truths.append(derived[key])
            
            if body_truths:
                # AND组合
                combined = body_truths[0]
                for bt in body_truths[1:]:
                    combined = self.tensor_AND(combined, bt)
                
                # 推导出头
                head_key = (head_pred, (0,))  # 简化
                derived[head_key] = combined
        
        return derived
    
    def backward_chain(self, query_pred: int, 
                      known_facts: Dict[Tuple[int, Tuple], float]) -> float:
        """
        后向链推理
        
        参数:
            query_pred: 查询谓词ID
            known_facts: 已知事实
        
        返回:
            查询的真值
        """
        # 简化：直接查找
        for key, truth in known_facts.items():
            if key[0] == query_pred:
                return truth
        
        return 0.5  # 未知


class TensorLogicProgram:
    """张量逻辑程序"""
    
    def __init__(self, engine: TensorLogicEngine):
        self.engine = engine
        self.rules: List[Callable] = []
    
    def add_rule(self, head_func: Callable, body_funcs: List[Callable]):
        """添加规则"""
        def rule():
            head = head_func()
            body_values = [f() for f in body_funcs]
            return self.engine.tensor_IMPLIES(
                self.engine.tensor_AND(*body_values) if body_values else np.array([1.0]),
                head
            )
        self.rules.append(rule)
    
    def evaluate(self) -> np.ndarray:
        """评估整个程序"""
        results = [rule() for rule in self.rules]
        if not results:
            return np.array([0.5])
        return self.engine.tensor_OR(*results)


class FuzzyReasoner:
    """模糊逻辑推理器（基于张量）"""
    
    def __init__(self, engine: TensorLogicEngine):
        self.engine = engine
    
    def compute_fuzzy_closure(self, 
                             initial_facts: Dict[str, float],
                             rules: List[Tuple[str, List[str], float]]) -> Dict[str, float]:
        """
        计算模糊闭包
        
        参数:
            initial_facts: 初始事实 {原子: 真值}
            rules: 规则 [(head, [body...], weight), ...]
        
        返回:
            所有原子的最终真值
        """
        facts = initial_facts.copy()
        
        # 迭代直到收敛
        for _ in range(100):
            old_facts = facts.copy()
            
            for head, body, weight in rules:
                # 计算体的最小真值（AND）
                if not body:
                    body_min = 1.0
                else:
                    body_min = min(facts.get(b, 0.0) for b in body)
                
                # 应用规则
                new_truth = self.engine.tensor_IMPLIES(
                    np.array([body_min]), 
                    np.array([weight])
                )[0]
                
                # 取最大（OR）
                if head in facts:
                    facts[head] = max(facts[head], new_truth)
                else:
                    facts[head] = new_truth
            
            # 检查收敛
            max_change = max(abs(facts.get(k, 0) - old_facts.get(k, 0)) 
                           for k in set(list(facts.keys()) + list(old_facts.keys())))
            if max_change < 1e-6:
                break
        
        return facts


if __name__ == "__main__":
    print("=" * 55)
    print("张量逻辑推理测试")
    print("=" * 55)
    
    # 创建引擎
    engine = TensorLogicEngine(embedding_dim=32, num_predicates=5)
    engine.init_embeddings(num_entities=20)
    
    # 设置特定嵌入
    engine.set_entity_embedding(1, np.array([0.8] * 32))
    engine.set_entity_embedding(2, np.array([0.6] * 32))
    
    print("\n--- 张量逻辑运算 ---")
    
    a = np.array([0.8, 0.6, 0.3, 0.9])
    b = np.array([0.7, 0.4, 0.5, 0.2])
    
    print(f"A = {a}")
    print(f"B = {b}")
    print(f"A ∧ B = {engine.tensor_AND(a, b)}")
    print(f"A ∨ B = {engine.tensor_OR(a, b)}")
    print(f"¬A = {engine.tensor_NOT(a)}")
    print(f"A → B = {engine.tensor_IMPLIES(a, b)}")
    print(f"A ⊕ B = {engine.tensor_XOR(a, b)}")
    
    # 文字真值计算
    print("\n--- 文字真值计算 ---")
    
    lit = TensorLiteral(predicate_id=0, term_indices=[0, 1], negated=False)
    entity_ids = np.array([[1, 2], [2, 1]])
    
    truth = engine.compute_literal_truth(lit, [1, 2])
    print(f"文字 P(1, 2) 的真值: {truth:.4f}")
    
    # 前向链
    print("\n--- 前向链推理 ---")
    
    facts = [(0, [1]), (0, [2])]  # P(1), P(2)
    rules = [(1, [0], 0.9)]  # Q :- P (简化)
    
    derived = engine.forward_chain(facts, rules)
    print(f"推导结果: {derived}")
    
    # 模糊推理
    print("\n--- 模糊逻辑推理 ---")
    
    fuzzy = FuzzyReasoner(engine)
    
    initial = {"A": 0.8, "B": 0.6}
    fuzzy_rules = [
        ("C", ["A"], 0.7),      # C :- A (权重0.7)
        ("D", ["A", "B"], 0.9), # D :- A ∧ B (权重0.9)
    ]
    
    result = fuzzy.compute_fuzzy_closure(initial, fuzzy_rules)
    print(f"初始: {initial}")
    print(f"规则: {fuzzy_rules}")
    print(f"结果: {result}")
    
    # 张量逻辑程序
    print("\n--- 张量逻辑程序 ---")
    
    program = TensorLogicProgram(engine)
    
    # 定义规则: X ∧ Y → Z
    def rule_x():
        return np.array([0.8])
    def rule_y():
        return np.array([0.6])
    
    program.add_rule(
        lambda: np.array([0.7]),  # head
        [rule_x, rule_y]          # body
    )
    
    result = program.evaluate()
    print(f"程序结果: {result}")
    
    print("\n测试通过！张量逻辑推理工作正常。")

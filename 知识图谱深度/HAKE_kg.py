# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / HAKE_kg

本文件实现 HAKE_kg 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional


class HAKEModel:
    """
    HAKE模型
    
    嵌入表示:
    - 实体: e = (e_mod, e_phase) ∈ C^d × R^d
    - 关系: r = (r_mod, r_phase) ∈ R^d × R^d
    
    评分函数:
    score(h, r, t) = d_mod + d_phase
    
    其中:
    d_mod = ||h_mod * r_mod - t_mod||_2^2
    d_phase = ||sin((h_phase + r_phase - t_phase) / 2)||_1
    """
    
    def __init__(self, n_entities: int, n_relations: int, 
                 embedding_dim: int = 100):
        self.n_entities = n_entities
        self.n_relations = n_relations
        self.dim = embedding_dim
        
        np.random.seed(42)
        
        # 模态嵌入（半径方向）
        self.entity_mod = np.random.randn(n_entities, embedding_dim) * 0.1
        self.relation_mod = np.random.randn(n_relations, embedding_dim) * 0.1
        
        # 相位嵌入
        self.entity_phase = np.random.randn(n_entities, embedding_dim) * 0.1
        self.relation_phase = np.random.randn(n_relations, embedding_dim) * 0.1
        
        # 可学习参数
        self.w_mod = np.ones(embedding_dim)
        self.w_phase = np.ones(embedding_dim)
        self.w_gamma = 1.0  # 权衡参数
    
    def _mod_distance(self, h_mod: np.ndarray, r_mod: np.ndarray, 
                      t_mod: np.ndarray) -> np.ndarray:
        """模态距离"""
        h_r = h_mod * r_mod
        diff = h_r - t_mod
        return np.sum(diff ** 2, axis=-1)
    
    def _phase_distance(self, h_phase: np.ndarray, r_phase: np.ndarray,
                       t_phase: np.ndarray) -> np.ndarray:
        """相位距离（使用sin）"""
        combined = (h_phase + r_phase - t_phase) / 2
        sin_val = np.sin(combined)
        return np.sum(np.abs(sin_val), axis=-1)
    
    def score(self, head_idx: int, relation_idx: int, tail_idx: int) -> float:
        """
        计算三元组分数
        """
        h_mod = self.entity_mod[head_idx]
        r_mod = self.relation_mod[relation_idx]
        t_mod = self.entity_mod[tail_idx]
        
        h_phase = self.entity_phase[head_idx]
        r_phase = self.relation_phase[relation_idx]
        t_phase = self.entity_phase[tail_idx]
        
        d_mod = self._mod_distance(h_mod, r_mod, t_mod)
        d_phase = self._phase_distance(h_phase, r_phase, t_phase)
        
        # 加权求和
        score = self.w_gamma * d_mod + d_phase
        
        # HAKE假设分数越低越好
        return -float(score)
    
    def predict_tail(self, head_idx: int, relation_idx: int,
                    top_k: int = 10) -> List[Tuple[int, float]]:
        """预测尾实体"""
        h_mod = self.entity_mod[head_idx]
        r_mod = self.relation_mod[relation_idx]
        h_phase = self.entity_phase[head_idx]
        r_phase = self.relation_phase[relation_idx]
        
        scores = []
        
        for tail_idx in range(self.n_entities):
            t_mod = self.entity_mod[tail_idx]
            t_phase = self.entity_phase[tail_idx]
            
            d_mod = self._mod_distance(h_mod, r_mod, t_mod)
            d_phase = self._phase_distance(h_phase, r_phase, t_phase)
            
            score = -float(self.w_gamma * d_mod + d_phase)
            scores.append((tail_idx, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HAKEOptimizer:
    """HAKE优化器"""
    
    def __init__(self, model: HAKEModel, learning_rate: float = 0.0005,
                 margin: float = 6.0):
        self.model = model
        self.lr = learning_rate
        self.margin = margin
    
    def train_step(self, pos_triples: List[Tuple[int, int, int]],
                  neg_triples: List[Tuple[int, int, int]]) -> float:
        """单步训练"""
        total_loss = 0.0
        
        for (h, r, t), (h_n, r_n, t_n) in zip(pos_triples, neg_triples):
            pos_score = self.model.score(h, r, t)
            neg_score = self.model.score(h_n, r_n, t_n)
            
            loss = max(0, self.margin - pos_score + neg_score)
            total_loss += loss
            
            if loss > 0:
                # 简化的梯度更新
                self._update_model(h, r, t, h_n, r_n, t_n)
        
        return total_loss
    
    def _update_model(self, h: int, r: int, t: int,
                     h_n: int, r_n: int, t_n: int):
        """更新模型参数"""
        lr = self.lr
        
        # 简化：直接更新
        # 实际需要计算梯度
        for emb in [self.model.entity_mod, self.model.entity_phase,
                   self.model.relation_mod, self.model.relation_phase]:
            noise = np.random.randn(*emb.shape) * 0.001
            if h < emb.shape[0]:
                emb[h] -= lr * noise[h]
            if t < emb.shape[0]:
                emb[t] -= lr * noise[t]


def hierarchical_score_analysis(model: HAKEModel, relation_idx: int) -> dict:
    """
    分析关系的层级属性
    
    返回:
        关系的关系模态和相位
    """
    r_mod = model.relation_mod[relation_idx]
    r_phase = model.relation_phase[relation_idx]
    
    return {
        'relation_idx': relation_idx,
        'mod_mean': np.mean(r_mod),
        'mod_std': np.std(r_mod),
        'mod_range': np.max(r_mod) - np.min(r_mod),
        'phase_mean': np.mean(r_phase),
        'phase_std': np.std(r_phase),
        'phase_range': np.max(r_phase) - np.min(r_phase)
    }


class HAKEWithConstraints:
    """
    带约束的HAKE
    
    强制语义关系和本体关系分开
    """
    
    def __init__(self, n_entities: int, n_relations: int,
                 embedding_dim: int = 100,
                 semantic_dim: int = 50,
                 ontological_dim: int = 50):
        self.model = HAKEModel(n_entities, n_relations, embedding_dim)
        
        # 分离语义和本体维度
        self.semantic_dim = semantic_dim
        self.ontological_dim = ontological_dim
        
        # 语义层：相位
        # 本体层：模态
    
    def constrain_embeddings(self):
        """
        强制约束嵌入
        """
        # 语义维度应该有更大的相位变化
        self.model.entity_phase[:, :self.semantic_dim] = \
            np.clip(self.model.entity_phase[:, :self.semantic_dim], -np.pi, np.pi)
        
        # 本体维度应该有更大的模态变化
        entity_norms = np.linalg.norm(
            self.model.entity_mod[:, self.ontological_dim:], 
            axis=1, keepdims=True
        )
        self.model.entity_mod[:, self.ontological_dim:] = \
            self.model.entity_mod[:, self.ontological_dim:] / (entity_norms + 1e-10)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("HAKE层级感知知识嵌入测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 模拟数据
    n_entities = 1000
    n_relations = 50
    
    # 创建模型
    print("\n--- 初始化HAKE ---")
    model = HAKEModel(n_entities, n_relations, embedding_dim=100)
    print(f"嵌入维度: {model.dim}")
    
    # 训练模拟
    print("\n--- 模拟训练 ---")
    n_triples = 5000
    triples = [
        (np.random.randint(n_entities),
         np.random.randint(n_relations),
         np.random.randint(n_entities))
        for _ in range(n_triples)
    ]
    
    optimizer = HAKEOptimizer(model)
    
    for epoch in range(5):
        pos_batch = triples[:100]
        neg_batch = [
            (h, r, np.random.randint(n_entities))
            for h, r, t in pos_batch
        ]
        
        loss = optimizer.train_step(pos_batch, neg_batch)
        
        if (epoch + 1) % 2 == 0:
            print(f"Epoch {epoch + 1}: Loss = {loss:.4f}")
    
    # 评估
    print("\n--- 预测评估 ---")
    test_triple = (0, 5, 100)
    score = model.score(*test_triple)
    print(f"测试三元组 {test_triple} 的分数: {score:.4f}")
    
    # 预测尾实体
    predictions = model.predict_tail(0, 5, top_k=5)
    print(f"实体(0, 5)的预测尾实体: {predictions}")
    
    # 层级分析
    print("\n--- 关系层级分析 ---")
    for r in range(5):
        analysis = hierarchical_score_analysis(model, r)
        print(f"关系 {r}: mod_range={analysis['mod_range']:.3f}, "
              f"phase_range={analysis['phase_range']:.3f}")
    
    print("\n" + "=" * 50)
    print("测试完成")

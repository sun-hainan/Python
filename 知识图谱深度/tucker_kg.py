# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / tucker_kg

本文件实现 tucker_kg 相关的算法功能。
"""

import numpy as np
from typing import Tuple, List, Optional
from collections import defaultdict


class TuckERModel:
    """
    TuckER模型
    
    参数:
        n_entities: 实体数量
        n_relations: 关系数量
        embedding_dim: 实体嵌入维度
        relation_dim: 关系嵌入维度（核心张量维度）
        rank: 张量分解的秩
    """
    
    def __init__(self, n_entities: int, n_relations: int,
                 embedding_dim: int = 100,
                 relation_dim: int = 30,
                 rank: Optional[int] = None):
        self.n_entities = n_entities
        self.n_relations = n_relations
        self.embedding_dim = embedding_dim
        self.relation_dim = relation_dim
        self.rank = rank or relation_dim
        
        # 初始化参数
        np.random.seed(42)
        
        # 实体嵌入矩阵
        self.entity_embeddings = np.random.randn(n_entities, embedding_dim) * 0.1
        # 关系嵌入矩阵
        self.relation_embeddings = np.random.randn(n_relations, relation_dim) * 0.1
        
        # 核心张量 W ∈ R^{d_r × d_e × d_e}
        core_shape = (relation_dim, embedding_dim, embedding_dim)
        self.core_tensor = np.random.randn(*core_shape) * 0.1
        
        # 关系特定的变换矩阵
        self.relation_transforms = np.random.randn(n_relations, embedding_dim, embedding_dim) * 0.01
    
    def score(self, head_idx: int, relation_idx: int, tail_idx: int) -> float:
        """
        计算三元组的分数
        
        参数:
            head_idx: 头实体索引
            relation_idx: 关系索引
            tail_idx: 尾实体索引
        
        返回:
            分数（越高越可能为真）
        """
        # 获取嵌入
        head_emb = self.entity_embeddings[head_idx]
        tail_emb = self.entity_embeddings[tail_idx]
        rel_emb = self.relation_embeddings[relation_idx]
        
        # 计算分数
        # 简化版本：使用双线性变换
        W_r = self.relation_transforms[relation_idx]
        
        score = head_emb @ W_r @ tail_emb
        
        return float(score)
    
    def predict_tail(self, head_idx: int, relation_idx: int, 
                    top_k: int = 10) -> List[Tuple[int, float]]:
        """
        预测尾实体
        
        返回:
            [(tail_idx, score), ...]
        """
        head_emb = self.entity_embeddings[head_idx]
        rel_emb = self.relation_embeddings[relation_idx]
        W_r = self.relation_transforms[relation_idx]
        
        scores = head_emb @ W_r @ self.entity_embeddings.T
        
        # 获取top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(idx, scores[idx]) for idx in top_indices]
    
    def predict_head(self, relation_idx: int, tail_idx: int,
                    top_k: int = 10) -> List[Tuple[int, float]]:
        """预测头实体"""
        tail_emb = self.entity_embeddings[tail_idx]
        rel_emb = self.relation_embeddings[relation_idx]
        W_r = self.relation_transforms[relation_idx]
        
        scores = (self.entity_embeddings @ W_r) @ tail_emb
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(idx, scores[idx]) for idx in top_indices]
    
    def predict_relation(self, head_idx: int, tail_idx: int,
                        top_k: int = 10) -> List[Tuple[int, float]]:
        """预测关系"""
        head_emb = self.entity_embeddings[head_idx]
        tail_emb = self.entity_embeddings[tail_idx]
        
        scores = np.zeros(self.n_relations)
        
        for r in range(self.n_relations):
            W_r = self.relation_transforms[r]
            scores[r] = head_emb @ W_r @ tail_emb
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(idx, scores[idx]) for idx in top_indices]


class TuckERTrainer:
    """TuckER训练器"""
    
    def __init__(self, model: TuckERModel, learning_rate: float = 0.001):
        self.model = model
        self.lr = learning_rate
        
        # Adam优化器状态
        self.m_entity = [np.zeros_like(e) for e in [model.entity_embeddings]]
        self.v_entity = [np.zeros_like(e) for e in [model.entity_embeddings]]
        self.m_relation = [np.zeros_like(r) for r in [model.relation_embeddings]]
        self.v_relation = [np.zeros_like(r) for r in [model.relation_embeddings]]
        self.m_core = [np.zeros_like(c) for c in [model.core_tensor]]
        self.v_core = [np.zeros_like(c) for c in [model.core_tensor]]
    
    def train_epoch(self, triples: List[Tuple[int, int, int]], 
                   batch_size: int = 256,
                   margin: float = 1.0) -> float:
        """
        训练一个epoch
        
        参数:
            triples: 三元组列表 (head, relation, tail)
            batch_size: 批大小
            margin: 对比损失间隔
        
        返回:
            总损失
        """
        total_loss = 0.0
        n_batches = (len(triples) + batch_size - 1) // batch_size
        
        np.random.shuffle(triples)
        
        for batch_idx in range(n_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(triples))
            
            batch = triples[batch_start:batch_end]
            
            # 生成负例
            pos_scores = []
            neg_scores = []
            
            for h, r, t in batch:
                pos_score = self.model.score(h, r, t)
                pos_scores.append(pos_score)
                
                # 替换头或尾生成负例
                if np.random.random() < 0.5:
                    # 替换头
                    neg_h = np.random.randint(self.model.n_entities)
                    while neg_h == h:
                        neg_h = np.random.randint(self.model.n_entities)
                    neg_score = self.model.score(neg_h, r, t)
                else:
                    # 替换尾
                    neg_t = np.random.randint(self.model.n_entities)
                    while neg_t == t:
                        neg_t = np.random.randint(self.model.n_entities)
                    neg_score = self.model.score(h, r, neg_t)
                
                neg_scores.append(neg_score)
            
            # 计算对比损失
            pos_scores = np.array(pos_scores)
            neg_scores = np.array(neg_scores)
            
            # max(0, margin - pos + neg)
            losses = np.maximum(0, margin - pos_scores + neg_scores)
            batch_loss = np.sum(losses)
            total_loss += batch_loss
            
            # 梯度更新（简化）
            self._update_parameters(batch, pos_scores, neg_scores)
        
        return total_loss
    
    def _update_parameters(self, batch: List[Tuple[int, int, int]],
                          pos_scores: np.ndarray, neg_scores: np.ndarray):
        """更新参数（简化版梯度下降）"""
        lr = self.lr
        
        for i, (h, r, t) in enumerate(batch):
            if pos_scores[i] - neg_scores[i] < -0.1:  # 满足间隔
                continue
            
            # 梯度
            grad_pos = 1.0
            grad_neg = -1.0
            
            # 更新实体嵌入（简化）
            head_emb = self.model.entity_embeddings[h]
            tail_emb = self.model.entity_embeddings[t]
            W_r = self.model.relation_transforms[r]
            
            # d_loss/d_score
            d_pos = grad_pos
            d_neg = grad_neg
            
            # 简化梯度
            grad_W = np.outer(head_emb, tail_emb)
            grad_head = W_r @ tail_emb
            grad_tail = head_emb @ W_r
            
            # 更新
            self.model.entity_embeddings[h] -= lr * d_pos * grad_head
            self.model.entity_embeddings[t] -= lr * d_pos * grad_tail
            self.model.relation_transforms[r] -= lr * (d_pos - d_neg) * grad_W


def evaluate_link_prediction(model: TuckERModel, 
                             test_triples: List[Tuple[int, int, int]],
                             filter_triples: Optional[List[Tuple[int, int, int]]] = None) -> dict:
    """
    评估链接预测
    
    返回:
        MRR, Hits@1, Hits@10
    """
    mr = 0.0
    hits_at_1 = 0.0
    hits_at_10 = 0.0
    n = len(test_triples)
    
    for h, r, t in test_triples:
        # 预测尾实体
        predictions = model.predict_tail(h, r, top_k=model.n_entities)
        
        # 过滤已存在的三元组
        if filter_triples:
            predictions = [(idx, score) for idx, score in predictions 
                         if (h, r, idx) not in filter_triples]
        
        # 计算排名
        rank = 1
        for idx, score in predictions:
            if idx == t:
                break
            rank += 1
        
        mr += rank
        if rank == 1:
            hits_at_1 += 1
        if rank <= 10:
            hits_at_10 += 1
    
    return {
        'MRR': mr / n,
        'Hits@1': hits_at_1 / n,
        'Hits@10': hits_at_10 / n
    }


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("TuckER张量分解测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 模拟数据
    n_entities = 100
    n_relations = 20
    n_triples = 500
    
    # 生成三元组
    triples = []
    for _ in range(n_triples):
        h = np.random.randint(n_entities)
        r = np.random.randint(n_relations)
        t = np.random.randint(n_entities)
        triples.append((h, r, t))
    
    print(f"\n数据: {n_entities} 实体, {n_relations} 关系, {n_triples} 三元组")
    
    # 创建模型
    print("\n--- 初始化TuckER模型 ---")
    model = TuckERModel(
        n_entities=n_entities,
        n_relations=n_relations,
        embedding_dim=50,
        relation_dim=20
    )
    print(f"模型参数: 实体嵌入 {n_entities}x{model.embedding_dim}, "
          f"关系嵌入 {n_relations}x{model.relation_dim}")
    
    # 训练
    print("\n--- 训练 ---")
    trainer = TuckERTrainer(model, learning_rate=0.01)
    
    for epoch in range(10):
        loss = trainer.train_epoch(triples, batch_size=64, margin=1.0)
        
        if (epoch + 1) % 2 == 0:
            print(f"Epoch {epoch + 1}: Loss = {loss:.4f}")
    
    # 链接预测评估
    print("\n--- 链接预测评估 ---")
    test_triples = triples[:50]
    metrics = evaluate_link_prediction(model, test_triples)
    
    print(f"MRR: {metrics['MRR']:.4f}")
    print(f"Hits@1: {metrics['Hits@1']:.4f}")
    print(f"Hits@10: {metrics['Hits@10']:.4f}")
    
    # 示例预测
    print("\n--- 示例预测 ---")
    h, r, t = triples[0]
    print(f"三元组: ({h}, {r}, {t})")
    print(f"原始分数: {model.score(h, r, t):.4f}")
    
    # 预测尾实体
    top_tails = model.predict_tail(h, r, top_k=5)
    print(f"预测尾实体 (top-5): {top_tails}")
    
    # 预测关系
    top_relations = model.predict_relation(h, t, top_k=5)
    print(f"预测关系 (top-5): {top_relations}")
    
    print("\n" + "=" * 50)
    print("测试完成")

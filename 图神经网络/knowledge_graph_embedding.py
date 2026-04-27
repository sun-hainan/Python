# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / knowledge_graph_embedding

本文件实现 knowledge_graph_embedding 相关的算法功能。
"""

import numpy as np


# ============================
# TransE
# ============================

class TransE:
    """
    TransE模型（Translating Embeddings）
    
    核心思想：h + r ≈ t
    距离函数：d(h + r, t) = ||h + r - t||_2
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, num_entities, num_relations, embedding_dim=64):
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        # Xavier初始化
        self.entity_embeddings = np.random.randn(num_entities, embedding_dim) * np.sqrt(2.0 / embedding_dim)
        self.relation_embeddings = np.random.randn(num_relations, embedding_dim) * np.sqrt(2.0 / embedding_dim)
        
        # 归一化实体嵌入
        self._normalize_embeddings()
    
    def _normalize_embeddings(self):
        """归一化实体嵌入"""
        norms = np.linalg.norm(self.entity_embeddings, axis=1, keepdims=True)
        self.entity_embeddings = self.entity_embeddings / (norms + 1e-8)
    
    def score(self, head, relation, tail):
        """
        计算三元组的得分
        
        参数:
            head: 头实体嵌入
            relation: 关系嵌入
            tail: 尾实体嵌入
        返回:
            score: 得分（越小越好）
        """
        # TransE: h + r ≈ t
        # 得分 = ||h + r - t||_2
        score = np.sum((head + relation - tail) ** 2, axis=-1)
        return score
    
    def forward(self, heads, relations, tails, mode='head_prediction'):
        """
        前馈传播
        
        参数:
            heads: 头实体索引 (batch_size,)
            relations: 关系索引 (batch_size,)
            tails: 尾实体索引 (batch_size,)
            mode: 'head_prediction' 或 'tail_prediction'
        返回:
            scores: 得分 (batch_size,)
        """
        h = self.entity_embeddings[heads]
        r = self.relation_embeddings[relations]
        t = self.entity_embeddings[tails]
        
        if mode == 'head_prediction':
            # 预测头实体：t - r ≈ h
            return self.score(t - r, np.zeros_like(r), h)
        else:
            # 预测尾实体：h + r ≈ t
            return self.score(h, r, t)
    
    def get_embeddings(self, entity_ids=None):
        """获取实体嵌入"""
        if entity_ids is None:
            return self.entity_embeddings
        return self.entity_embeddings[entity_ids]


# ============================
# TransR
# ============================

class TransR:
    """
    TransR模型
    
    核心思想：在关系特定空间中，h_r + r ≈ t_r
    其中 h_r = M_r * h, t_r = M_r * t
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        entity_dim: 实体嵌入维度
        relation_dim: 关系嵌入维度
    """
    
    def __init__(self, num_entities, num_relations, entity_dim=64, relation_dim=64):
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.entity_dim = entity_dim
        self.relation_dim = relation_dim
        
        # 实体嵌入
        self.entity_embeddings = np.random.randn(num_entities, entity_dim) * np.sqrt(2.0 / entity_dim)
        
        # 关系嵌入和投影矩阵
        self.relation_embeddings = np.random.randn(num_relations, relation_dim) * np.sqrt(2.0 / relation_dim)
        self.projection_matrices = np.random.randn(num_relations, entity_dim, relation_dim) * 0.01
    
    def project(self, entities, relation_ids):
        """
        将实体投影到关系特定空间
        
        参数:
            entities: 实体嵌入 (batch, entity_dim)
            relation_ids: 关系索引 (batch,)
        返回:
            projected: 投影后的嵌入 (batch, relation_dim)
        """
        # 获取每个样本对应的投影矩阵
        projected = []
        for i, rel_id in enumerate(relation_ids):
            M = self.projection_matrices[rel_id]
            h = entities[i]
            projected.append(h @ M)
        
        return np.array(projected)
    
    def score(self, head, relation, tail):
        """计算得分"""
        # 投影
        h_r = self.project(head, np.arange(len(head)))
        t_r = self.project(tail, np.arange(len(tail)))
        
        # TransE-like score in relation space
        score = np.sum((h_r + relation - t_r) ** 2, axis=-1)
        return score


# ============================
# DistMult
# ============================

class DistMult:
    """
    DistMult模型（双线性因子分解）
    
    核心思想：h^T * M_r * t ≈ score
    当M_r是对角矩阵时，简化为 h * r * t（逐元素乘积）
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, num_entities, num_relations, embedding_dim=64):
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        # 实体嵌入
        self.entity_embeddings = np.random.randn(num_entities, embedding_dim) * np.sqrt(2.0 / embedding_dim)
        
        # 关系嵌入（作为对角矩阵）
        self.relation_embeddings = np.random.randn(num_relations, embedding_dim) * np.sqrt(2.0 / embedding_dim)
    
    def score(self, head, relation, tail):
        """
        计算三元组得分
        score = Σ_i h_i * r_i * t_i
        """
        # 逐元素乘积
        score = head * relation * tail
        return np.sum(score, axis=-1)
    
    def forward(self, heads, relations, tails):
        """前馈传播"""
        h = self.entity_embeddings[heads]
        r = self.relation_embeddings[relations]
        t = self.entity_embeddings[tails]
        
        return self.score(h, r, t)


# ============================
# RotatE
# ============================

class RotatE:
    """
    RotatE模型（旋转嵌入）
    
    核心思想：在复数空间中，头实体通过关系的旋转映射到尾实体
    t = h ∘ r（∘表示哈达玛积/逐元素复数乘法）
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        embedding_dim: 嵌入维度（必须是偶数）
    """
    
    def __init__(self, num_entities, num_relations, embedding_dim=64):
        assert embedding_dim % 2 == 0, "embedding_dim must be even"
        
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        # 实体嵌入（作为复数）
        self.entity_embeddings = np.random.randn(num_entities, embedding_dim) * 0.01
        
        # 关系嵌入（相位角）
        self.relation_embeddings = np.random.randn(num_relations, embedding_dim // 2) * 0.01
    
    def _get_rotation_matrix(self, relation_ids):
        """
        获取旋转矩阵（由关系相位角定义）
        
        参数:
            relation_ids: 关系索引
        返回:
            rotations: 旋转相位 (num_samples, embedding_dim)
        """
        phases = self.relation_embeddings[relation_ids]
        
        # 扩展为完整维度
        rotations = np.concatenate([np.cos(phases), np.sin(phases)], axis=1)
        
        return rotations
    
    def score(self, head, relation_ids, tail):
        """计算得分"""
        # 获取旋转相位
        rotations = self._get_rotation_matrix(relation_ids)
        
        # 旋转：h ∘ r
        rotated_head = head * rotations
        
        # 距离
        score = np.sum((rotated_head - tail) ** 2, axis=-1)
        return score
    
    def forward(self, heads, relations, tails):
        """前馈传播"""
        h = self.entity_embeddings[heads]
        t = self.entity_embeddings[tails]
        
        return self.score(h, relations, t)


# ============================
# ComplEx
# ============================

class ComplEx:
    """
    ComplEx模型（复数嵌入）
    
    核心思想：在复数空间中学习嵌入
    score = Re(Σ_i h_i * r_i * conj(t_i))
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, num_entities, num_relations, embedding_dim=64):
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        # 实部和虚部
        self.entity_embeddings_real = np.random.randn(num_entities, embedding_dim) * 0.01
        self.entity_embeddings_imag = np.random.randn(num_entities, embedding_dim) * 0.01
        self.relation_embeddings_real = np.random.randn(num_relations, embedding_dim) * 0.01
        self.relation_embeddings_imag = np.random.randn(num_relations, embedding_dim) * 0.01
    
    def score(self, head, relation, tail):
        """
        计算得分
        score = Re(Σ h_i * r_i * conj(t_i))
        = Re(Σ (h_real + i*h_imag) * (r_real + i*r_imag) * (t_real - i*t_imag))
        """
        # 复数乘积的实部
        # Re(h * r * conj(t)) = h_real*r_real*t_real + h_imag*r_imag*t_real 
        #                     + h_real*r_imag*t_imag - h_imag*r_real*t_imag
        
        h_r = head
        r = relation
        t = tail
        
        score = (h_r[:, :self.embedding_dim//2] * r[:, :self.embedding_dim//2] * t[:, :self.embedding_dim//2] +
                 h_r[:, self.embedding_dim//2:] * r[:, self.embedding_dim//2:] * t[:, :self.embedding_dim//2] +
                 h_r[:, :self.embedding_dim//2] * r[:, self.embedding_dim//2:] * t[:, self.embedding_dim//2:] -
                 h_r[:, self.embedding_dim//2:] * r[:, :self.embedding_dim//2] * t[:, self.embedding_dim//2:])
        
        return np.sum(score, axis=-1)
    
    def forward(self, heads, relations, tails):
        """前馈传播"""
        h = np.concatenate([self.entity_embeddings_real[heads], self.entity_embeddings_imag[heads]], axis=1)
        r = np.concatenate([self.relation_embeddings_real[relations], self.relation_embeddings_imag[relations]], axis=1)
        t = np.concatenate([self.entity_embeddings_real[tails], self.entity_embeddings_imag[tails]], axis=1)
        
        return self.score(h, r, t)


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 60)
    print("知识图谱嵌入模型测试")
    print("=" * 60)
    
    num_entities = 100
    num_relations = 20
    embedding_dim = 32
    
    # 创建模型
    models = {
        'TransE': TransE(num_entities, num_relations, embedding_dim),
        'TransR': TransR(num_entities, num_relations, embedding_dim, embedding_dim),
        'DistMult': DistMult(num_entities, num_relations, embedding_dim),
        'RotatE': RotatE(num_entities, num_relations, embedding_dim * 2),
        'ComplEx': ComplEx(num_entities, num_relations, embedding_dim),
    }
    
    # 创建测试三元组
    batch_size = 16
    head_ids = np.random.randint(0, num_entities, batch_size)
    relation_ids = np.random.randint(0, num_relations, batch_size)
    tail_ids = np.random.randint(0, num_entities, batch_size)
    
    print(f"\n测试三元组数量: {batch_size}")
    print(f"头实体范围: [{head_ids.min()}, {head_ids.max()}]")
    print(f"关系范围: [{relation_ids.min()}, {relation_ids.max()}]")
    print(f"尾实体范围: [{tail_ids.min()}, {tail_ids.max()}]")
    
    # 测试1：各模型得分
    print("\n--- 各模型得分对比 ---")
    print(f"{'模型':>12} | {'得分均值':>12} | {'得分标准差':>12} | {'最小值':>12}")
    print("-" * 55)
    
    for name, model in models.items():
        if name == 'TransE':
            scores = model.forward(head_ids, relation_ids, tail_ids)
        elif name == 'RotatE':
            scores = model.forward(head_ids, relation_ids, tail_ids)
        elif name == 'DistMult':
            scores = model.forward(head_ids, relation_ids, tail_ids)
        elif name == 'ComplEx':
            scores = model.forward(head_ids, relation_ids, tail_ids)
        else:
            # TransR
            h = model.entity_embeddings[head_ids]
            r = model.relation_embeddings[relation_ids]
            t = model.entity_embeddings[tail_ids]
            scores = model.score(h, r, t)
        
        print(f"{name:>12} | {scores.mean():12.4f} | {scores.std():12.4f} | {scores.min():12.4f}")
    
    # 测试2：TransE的翻译特性
    print("\n--- TransE翻译特性测试 ---")
    transe = models['TransE']
    
    h = transe.entity_embeddings[head_ids[0]]
    r = transe.relation_embeddings[relation_ids[0]]
    t = transe.entity_embeddings[tail_ids[0]]
    
    h_plus_r = h + r
    
    print(f"头实体嵌入: {h[:5].round(3)}")
    print(f"关系嵌入: {r[:5].round(3)}")
    print(f"头+关系: {h_plus_r[:5].round(3)}")
    print(f"尾实体嵌入: {t[:5].round(3)}")
    print(f"距离 ||h+r-t||: {np.linalg.norm(h_plus_r - t):.4f}")
    
    # 测试3：RotatE的旋转特性
    print("\n--- RotatE旋转特性测试 ---")
    rotate = models['RotatE']
    
    h = rotate.entity_embeddings[head_ids[0]]
    phases = rotate.relation_embeddings[relation_ids[0]]
    
    rotated = np.concatenate([np.cos(phases), np.sin(phases)], axis=0) * h
    
    print(f"原始嵌入: {h[:5].round(3)}")
    print(f"旋转相位: {phases[:3].round(3)}")
    print(f"旋转后: {rotated[:5].round(3)}")
    
    # 测试4：预测能力测试
    print("\n--- 预测能力模拟测试 ---")
    
    # 创建一些正确三元组和错误三元组
    correct_triples = [(0, 0, 1), (1, 1, 2), (2, 2, 3), (3, 3, 4)]
    wrong_triples = [(0, 0, 99), (1, 1, 98), (2, 2, 97), (3, 3, 96)]
    
    print(f"{'模型':>12} | {'正确三元组得分':>18} | {'错误三元组得分':>18}")
    print("-" * 55)
    
    for name, model in models.items():
        correct_scores = []
        wrong_scores = []
        
        for h, r, t in correct_triples:
            if name == 'TransE':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'RotatE':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'DistMult':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'ComplEx':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            else:
                h_e = model.entity_embeddings[h:h+1]
                r_e = model.relation_embeddings[r:r+1]
                t_e = model.entity_embeddings[t:t+1]
                score = model.score(h_e, r_e, t_e)[0]
            correct_scores.append(score)
        
        for h, r, t in wrong_triples:
            if name == 'TransE':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'RotatE':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'DistMult':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            elif name == 'ComplEx':
                score = model.forward(np.array([h]), np.array([r]), np.array([t]))[0]
            else:
                h_e = model.entity_embeddings[h:h+1]
                r_e = model.relation_embeddings[r:r+1]
                t_e = model.entity_embeddings[t:t+1]
                score = model.score(h_e, r_e, t_e)[0]
            wrong_scores.append(score)
        
        print(f"{name:>12} | {np.mean(correct_scores):18.4f} | {np.mean(wrong_scores):18.4f}")
    
    # 测试5：嵌入维度对得分分布的影响
    print("\n--- 嵌入维度对得分分布的影响 ---")
    
    for dim in [16, 32, 64, 128]:
        model = TransE(num_entities, num_relations, dim)
        scores = model.forward(head_ids, relation_ids, tail_ids)
        print(f"  TransE(dim={dim:3d}): 均值={scores.mean():.4f}, 标准差={scores.std():.4f}")
    
    print("\n知识图谱嵌入模型测试完成！")

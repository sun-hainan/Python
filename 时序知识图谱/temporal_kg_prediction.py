"""
时序知识图谱预测 (Temporal KG Prediction - TAE/TNT)
================================================
实现时序知识图谱的预测任务：给定(s, p, ?, t)或(?, p, o, t)，预测缺失实体。

TAE (Temporal Attribute Encoder): 基于时间感知的编码器
TNT (Temporal Neighbors Transformer): 基于邻居时序信息的Transformer

参考：
    - Liu, Y. et al. (2022). Temporal Knowledge Graph Forecasting.
    - Wu, S. et al. (2023). TNT: Temporal Neighbor-aware Transformer.
"""

from typing import List, Dict, Set, Tuple, Optional
import random
import math


class TemporalEntity:
    """时序实体"""
    def __init__(self, id: str, history: List[Tuple[str, int]]):
        self.id = id
        self.history = history  # [(relation, time), ...]
        self.type = None


class TemporalKnowledgeGraph:
    """时序知识图谱（预测用）"""
    def __init__(self):
        self.entities = {}  # id -> TemporalEntity
        self.triples = []  # [(s, p, o, t), ...]
        self.entity_history = {}  # entity_id -> [(p, o, t), ...]
    
    def add_triple(self, s: str, p: str, o: str, t: int):
        """添加三元组"""
        self.triples.append((s, p, o, t))
        
        if s not in self.entity_history:
            self.entity_history[s] = []
        self.entity_history[s].append((p, o, t))
        
        if o not in self.entity_history:
            self.entity_history[o] = []
        self.entity_history[o].append((p, s, t))  # 反向
    
    def get_history(self, entity: str, before_t: Optional[int] = None) -> List[Tuple]:
        """获取实体的历史"""
        history = self.entity_history.get(entity, [])
        if before_t is not None:
            history = [(p, o, t) for p, o, t in history if t <= before_t]
        return history
    
    def get_neighbors(self, entity: str, time: int, hops: int = 1) -> Set[str]:
        """获取邻居实体"""
        neighbors = set()
        history = self.get_history(entity, time)
        
        for p, o, t in history:
            if t <= time:
                neighbors.add(o)
        
        return neighbors


class TAEPredictor:
    """
    TAE (Temporal Attribute Encoder) 预测器
    
    基于实体历史和时间编码的预测模型
    
    参数:
        embedding_dim: 嵌入维度
        num_heads: 注意力头数
    """
    
    def __init__(self, embedding_dim: int = 64, num_heads: int = 4):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        
        # 初始化
        self.entity_embeddings = {}
        self.relation_embeddings = {}
        self.time_embeddings = {}
    
    def _init_embeddings(self, kg: TemporalKnowledgeGraph):
        """初始化嵌入"""
        scale = 0.1
        
        for entity in kg.entity_history.keys():
            if entity not in self.entity_embeddings:
                self.entity_embeddings[entity] = [
                    random.gauss(0, scale) for _ in range(self.embedding_dim)
                ]
        
        for triple in kg.triples:
            s, p, o, t = triple
            if p not in self.relation_embeddings:
                self.relation_embeddings[p] = [
                    random.gauss(0, scale) for _ in range(self.embedding_dim)
                ]
            if t not in self.time_embeddings:
                self.time_embeddings[t] = [
                    random.gauss(0, scale) for _ in range(self.embedding_dim)
                ]
    
    def encode_temporal(self, entity: str, time: int) -> List[float]:
        """
        时间感知编码
        
        参数:
            entity: 实体ID
            time: 时间戳
        
        返回:
            编码向量
        """
        # 获取基础嵌入
        base_emb = self.entity_embeddings.get(entity, 
            [0.0] * self.embedding_dim)
        
        # 获取时间嵌入
        time_emb = self.time_embeddings.get(time,
            [0.0] * self.embedding_dim)
        
        # 获取历史聚合
        history = self.get_temporal_history(entity, time)
        history_emb = self._aggregate_history(history)
        
        # 组合
        alpha1, alpha2 = 0.4, 0.3
        encoded = [
            base_emb[i] * alpha1 + time_emb[i] * (1 - alpha1) * 0.5 + history_emb[i] * alpha2
            for i in range(self.embedding_dim)
        ]
        
        return encoded
    
    def get_temporal_history(self, entity: str, time: int) -> List[Tuple]:
        """获取时序历史"""
        if entity not in self.entity_embeddings:
            return []
        
        history = []
        entity_history = self.entity_history.get(entity, [])
        for p, o, t in entity_history:
            if t < time:
                history.append((p, o, t))
        
        return history
    
    def _aggregate_history(self, history: List[Tuple]) -> List[float]:
        """聚合历史信息"""
        if not history:
            return [0.0] * self.embedding_dim
        
        aggregated = [0.0] * self.embedding_dim
        
        for p, o, t in history:
            # 关系嵌入
            r_emb = self.relation_embeddings.get(p, [0.0] * self.embedding_dim)
            # 邻居嵌入
            o_emb = self.entity_embeddings.get(o, [0.0] * self.embedding_dim)
            
            for i in range(self.embedding_dim):
                aggregated[i] += r_emb[i] + o_emb[i]
        
        # 平均
        n = len(history)
        aggregated = [x / n for x in aggregated]
        
        return aggregated
    
    def entity_history(self, entity: str) -> List[Tuple]:
        """获取实体的历史"""
        return self.entity_history.get(entity, [])
    
    def score(self, s: str, p: str, o: str, t: int) -> float:
        """
        计算三元组得分
        
        参数:
            s: 主语
            p: 关系
            o: 宾语
            t: 时间
        
        返回:
            得分
        """
        s_enc = self.encode_temporal(s, t)
        o_enc = self.encode_temporal(o, t)
        p_emb = self.relation_embeddings.get(p, [0.0] * self.embedding_dim)
        
        # s + p - o 的负L2距离
        diff = [s_enc[i] + p_emb[i] - o_enc[i] for i in range(self.embedding_dim)]
        score = -math.sqrt(sum(d * d for d in diff))
        
        return score
    
    def predict_tail(self, s: str, p: str, t: int, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        预测尾实体
        
        参数:
            s: 主语
            p: 关系
            t: 时间
            top_k: 返回前k个
        
        返回:
            [(实体, 得分), ...]
        """
        scores = []
        for o in self.entity_embeddings.keys():
            if o != s:
                score = self.score(s, p, o, t)
                scores.append((o, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def predict_head(self, p: str, o: str, t: int, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        预测头实体
        
        参数:
            p: 关系
            o: 宾语
            t: 时间
            top_k: 返回前k个
        
        返回:
            [(实体, 得分), ...]
        """
        scores = []
        for s in self.entity_embeddings.keys():
            if s != o:
                score = self.score(s, p, o, t)
                scores.append((s, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class TNTPredictor:
    """
    TNT (Temporal Neighbors Transformer) 预测器
    
    基于邻居时序信息和Transformer的预测模型
    
    参数:
        embedding_dim: 嵌入维度
        num_layers: Transformer层数
    """
    
    def __init__(self, embedding_dim: int = 64, num_layers: int = 2):
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.entity_embeddings = {}
        self.relation_embeddings = {}
        self.time_embeddings = {}
    
    def _multihead_attention(self, queries: List[List[float]], 
                             keys: List[List[float]],
                             values: List[List[float]],
                             num_heads: int = 4) -> List[List[float]]:
        """
        多头注意力机制
        
        参数:
            queries: 查询向量
            keys: 键向量
            values: 值向量
            num_heads: 头数
        
        返回:
            注意力输出
        """
        dim_per_head = self.embedding_dim // num_heads
        outputs = []
        
        for q in queries:
            # 分头
            q_heads = [q[i*dim_per_head:(i+1)*dim_per_head] for i in range(num_heads)]
            
            # 计算注意力
            attn_scores = []
            for k in keys:
                k_heads = [k[i*dim_per_head:(i+1)*dim_per_head] for i in range(num_heads)]
                scores = []
                for qh, kh in zip(q_heads, k_heads):
                    score = sum(qh[i] * kh[i] for i in range(dim_per_head))
                    scores.append(score)
                attn_scores.append(sum(scores) / num_heads)
            
            # softmax
            max_score = max(attn_scores)
            exp_scores = [math.exp(s - max_score) for s in attn_scores]
            total = sum(exp_scores)
            weights = [e / total for e in exp_scores]
            
            # 加权求和
            output = [0.0] * self.embedding_dim
            for w, v in zip(weights, values):
                for i, vi in enumerate(v):
                    output[i] += w * vi
            
            outputs.append(output)
        
        return outputs
    
    def get_temporal_neighbors(self, entity: str, time: int) -> List[Tuple]:
        """获取时序邻居"""
        return []  # 需要TKG数据
    
    def score(self, s: str, p: str, o: str, t: int, 
              neighbor_k: int = 5) -> float:
        """
        TNT得分函数
        
        参数:
            s: 主语
            p: 关系
            o: 宾语
            t: 时间
            neighbor_k: 考虑的邻居数量
        
        返回:
            得分
        """
        # 获取编码
        s_enc = self.entity_embeddings.get(s, [0.0] * self.embedding_dim)
        o_enc = self.entity_embeddings.get(o, [0.0] * self.embedding_dim)
        p_enc = self.relation_embeddings.get(p, [0.0] * self.embedding_dim)
        t_enc = self.time_embeddings.get(t, [0.0] * self.embedding_dim)
        
        # 邻居聚合（简化）
        # s_neighbors = self._aggregate_neighbors(s, t, neighbor_k)
        # o_neighbors = self._aggregate_neighbors(o, t, neighbor_k)
        
        # 组合
        s_combined = [s_enc[i] + p_enc[i] + t_enc[i] * 0.3 for i in range(self.embedding_dim)]
        o_combined = [o_enc[i] - t_enc[i] * 0.3 for i in range(self.embedding_dim)]
        
        # 点积
        score = sum(s_combined[i] * o_combined[i] for i in range(self.embedding_dim))
        
        return score
    
    def _aggregate_neighbors(self, entity: str, time: int, k: int) -> List[float]:
        """聚合邻居信息"""
        return [0.0] * self.embedding_dim


def evaluate_prediction(predictor, test_triples: List[Tuple], 
                       metric: str = "MRR") -> Dict[str, float]:
    """
    评估预测性能
    
    参数:
        predictor: 预测器
        test_triples: 测试三元组
        metric: 评估指标 ("MRR", "Hit@K", "MR")
    
    返回:
        评估结果
    """
    ranks = []
    
    for s, p, o, t in test_triples:
        # 预测尾实体
        predictions = predictor.predict_tail(s, p, t, top_k=100)
        
        # 找真实宾语的位置
        rank = None
        for i, (pred_o, _) in enumerate(predictions):
            if pred_o == o:
                rank = i + 1
                break
        
        if rank is not None:
            ranks.append(rank)
        else:
            ranks.append(len(predictions) + 1)
    
    # 计算指标
    mrr = sum(1 / r for r in ranks) / len(ranks)
    hit10 = sum(1 for r in ranks if r <= 10) / len(ranks)
    hit1 = sum(1 for r in ranks if r <= 1) / len(ranks)
    mr = sum(ranks) / len(ranks)
    
    return {
        "MRR": mrr,
        "Hit@10": hit10,
        "Hit@1": hit1,
        "MR": mr
    }


if __name__ == "__main__":
    print("=== 时序知识图谱预测测试 ===")
    
    # 构建时序知识图谱
    kg = TemporalKnowledgeGraph()
    
    # 添加训练数据
    train_triples = [
        ("Alice", "visits", "Paris", 2020),
        ("Alice", "visits", "London", 2021),
        ("Bob", "visits", "Paris", 2020),
        ("Bob", "visits", "Tokyo", 2021),
        ("Charlie", "visits", "Paris", 2021),
    ]
    
    for s, p, o, t in train_triples:
        kg.add_triple(s, p, o, t)
    
    print(f"构建TKG: {len(kg.triples)} 条三元组")
    
    # 训练TAE预测器
    print("\n训练TAE预测器:")
    predictor = TAEPredictor(embedding_dim=32, num_heads=2)
    predictor._init_embeddings(kg)
    
    # 预测
    print("\n预测 Alice 在 2022 年 visits 哪里:")
    predictions = predictor.predict_tail("Alice", "visits", 2022, top_k=3)
    for entity, score in predictions:
        print(f"  {entity}: {score:.4f}")
    
    print("\n预测 谁 visits Paris 在 2021:")
    predictions = predictor.predict_head("visits", "Paris", 2021, top_k=3)
    for entity, score in predictions:
        print(f"  {entity}: {score:.4f}")
    
    # 测试评估
    print("\n\n评估预测性能:")
    test_triples = [
        ("Alice", "visits", "London", 2021),
        ("Bob", "visits", "Tokyo", 2021),
    ]
    
    metrics = evaluate_prediction(predictor, test_triples)
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n=== 测试完成 ===")

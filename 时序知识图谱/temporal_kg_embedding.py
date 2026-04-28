"""
时序知识图谱嵌入 (Temporal KG Embedding - TComplEx/TeLM)
=====================================================
实现时序知识图谱的嵌入表示学习。

TComplEx: 使用复数向量表示实体和关系，引入时间维度
TeLM: 使用线性时间插值的多关系嵌入

参考：
    - Lacroix, T. et al. (2020). TComplEx: Temporal Complex Knowledge Graph Embeddings.
    - Wu, J. et al. (2022). TeLM: Temporal Knowledge Graph Embeddings.
"""

from typing import List, Dict, Set, Tuple
import random
import math


class TKGEmbedding:
    """
    时序知识图谱嵌入基类
    
    参数:
        num_entities: 实体数量
        num_relations: 关系数量
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, num_entities: int, num_relations: int, embedding_dim: int = 64):
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        
        # 初始化嵌入
        scale = 0.1
        self.entity_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(num_entities)
        ]
        self.relation_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(num_relations)
        ]
        
        # 时间嵌入
        self.time_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(1000)  # 假设最多1000个时间戳
        ]
    
    def score(self, s: int, p: int, o: int, t: int) -> float:
        """
        计算三元组(s, p, o)在时间t的得分
        
        参数:
            s: 主语实体ID
            p: 关系ID
            o: 宾语实体ID
            t: 时间戳ID
        
        返回:
            得分（越高越可能成立）
        """
        raise NotImplementedError
    
    def predict(self, s: int, p: int, t: int, k: int = 5) -> List[Tuple[int, float]]:
        """
        预测在时间t给定(s,p)的宾语
        
        参数:
            s: 主语ID
            p: 关系ID
            t: 时间ID
            k: 返回前k个
        
        返回:
            [(实体ID, 得分), ...]
        """
        scores = []
        for o in range(self.num_entities):
            if o != s:  # 排除自环
                score = self.score(s, p, o, t)
                scores.append((o, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
    
    def train_step(self, positive_samples: List[Tuple], 
                   negative_samples: List[Tuple], 
                   margin: float = 1.0) -> float:
        """
        单步训练（使用margin-based ranking loss）
        
        参数:
            positive_samples: 正样本列表
            negative_samples: 负样本列表
            margin: 间隔参数
        
        返回:
            损失值
        """
        loss = 0.0
        
        for pos, neg in zip(positive_samples, negative_samples):
            s, p, o, t = pos
            s_neg, p_neg, o_neg, t_neg = neg
            
            pos_score = self.score(s, p, o, t)
            neg_score = self.score(s_neg, p_neg, o_neg, t_neg)
            
            # hinge loss
            loss += max(0, margin - pos_score + neg_score)
        
        return loss


class TComplEx(TKGEmbedding):
    """
    TComplEx: 时序复数嵌入
    
    使用复数向量表示，允许非对称的时间关系
    
    得分函数: Re(<s, r, t, ō>)
    其中t是时间嵌入，ō是o的共轭
    """
    
    def __init__(self, num_entities: int, num_relations: int, embedding_dim: int = 64):
        super().__init__(num_entities, num_relations, embedding_dim)
        
        # 复数用实数对表示: [real, imag, real, imag, ...]
        dim = embedding_dim // 2
        
        # 重新初始化为复数形式
        scale = 0.1
        self.entity_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(num_entities)
        ]
        self.relation_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(num_relations)
        ]
        self.time_embeddings = [
            [random.gauss(0, scale) for _ in range(embedding_dim)]
            for _ in range(1000)
        ]
    
    def _complex_multiply(self, a: List[float], b: List[float]) -> List[float]:
        """复数乘法 a * b"""
        dim = len(a) // 2
        result = [0.0] * len(a)
        
        for i in range(dim):
            # a_real = a[2*i], a_imag = a[2*i+1]
            # b_real = b[2*i], b_imag = b[2*i+1]
            result[2*i] += a[2*i] * b[2*i] - a[2*i+1] * b[2*i+1]
            result[2*i+1] += a[2*i] * b[2*i+1] + a[2*i+1] * b[2*i]
        
        return result
    
    def _complex_conj(self, a: List[float]) -> List[float]:
        """复数共轭"""
        result = a[:]
        dim = len(a) // 2
        for i in range(dim):
            result[2*i+1] = -result[2*i+1]
        return result
    
    def _dot_product(self, a: List[float], b: List[float]) -> float:
        """点积"""
        return sum(a_i * b_i for a_i, b_i in zip(a, b))
    
    def score(self, s: int, p: int, o: int, t: int) -> float:
        """
        TComplEx得分函数
        
        score = Re(<s, r ⊗ t, ō>)
        
        参数:
            s: 主语嵌入
            p: 关系嵌入
            o: 宾语嵌入
            t: 时间嵌入
        
        返回:
            得分
        """
        s_emb = self.entity_embeddings[s]
        r_emb = self.relation_embeddings[p]
        o_emb = self.entity_embeddings[o]
        t_emb = self.time_embeddings[t] if t < len(self.time_embeddings) else [0.0] * self.embedding_dim
        
        # 计算 r ⊗ t (关系与时间的哈达玛积)
        rt = self._complex_multiply(r_emb, t_emb)
        
        # 计算 <s, rt, ō> (三方点积)
        # = sum(s_i * rt_i * conj(o)_i)
        o_conj = self._complex_conj(o_emb)
        
        product = [s_emb[i] * rt[i] * o_conj[i] for i in range(self.embedding_dim)]
        score = sum(product)
        
        return score


class TeLM(TKGEmbedding):
    """
    TeLM: Temporal Linear Model
    
    使用线性时间插值学习时序知识图谱嵌入
    
    核心思想: 实体的嵌入随时间线性变化
    e(t) = (1 - α(t)) * e_prev + α(t) * e_next
    
    参数:
        alpha: 时间插值系数
    """
    
    def __init__(self, num_entities: int, num_relations: int, 
                 embedding_dim: int = 64, alpha: float = 0.5):
        super().__init__(num_entities, num_relations, embedding_dim)
        self.alpha = alpha
        
        # 存储每个时间点的实体嵌入
        self.entity_time_embeddings = {}  # (entity_id, time_id) -> embedding
    
    def get_entity_embedding(self, entity_id: int, time_id: int) -> List[float]:
        """
        获取实体在特定时间的嵌入
        
        参数:
            entity_id: 实体ID
            time_id: 时间ID
        
        返回:
            嵌入向量
        """
        # 检查缓存
        if (entity_id, time_id) in self.entity_time_embeddings:
            return self.entity_time_embeddings[(entity_id, time_id)]
        
        # 线性插值
        base_emb = self.entity_embeddings[entity_id]
        time_emb = self.time_embeddings[time_id] if time_id < len(self.time_embeddings) else [0.0] * self.embedding_dim
        
        # e(t) = (1 - α) * e_entity + α * e_time
        result = [
            (1 - self.alpha) * base_emb[i] + self.alpha * time_emb[i]
            for i in range(self.embedding_dim)
        ]
        
        self.entity_time_embeddings[(entity_id, time_id)] = result
        return result
    
    def score(self, s: int, p: int, o: int, t: int) -> float:
        """
        TeLM得分函数
        
        score = -||e_s(t) + r_p - e_o(t)||
        
        参数:
            s: 主语ID
            p: 关系ID
            o: 宾语ID
            t: 时间ID
        
        返回:
            得分（距离的负数，越大越好）
        """
        s_emb = self.get_entity_embedding(s, t)
        o_emb = self.get_entity_embedding(o, t)
        r_emb = self.relation_embeddings[p]
        
        # 计算 s + r - o
        diff = [s_emb[i] + r_emb[i] - o_emb[i] for i in range(self.embedding_dim)]
        
        # L2距离
        distance = math.sqrt(sum(d * d for d in diff))
        
        return -distance  # 负距离作为得分


def generate_negative_samples(kg, num_samples: int) -> List[Tuple]:
    """
    生成负样本（随机替换头或尾）
    
    参数:
        kg: 知识图谱
        num_samples: 样本数量
    
    返回:
        负样本列表
    """
    negatives = []
    triples = list(kg.triples.keys())
    
    for _ in range(num_samples):
        if not triples:
            break
        
        s, p, o = random.choice(triples)
        t = random.choice(list(kg.triples[(s, p, o)]))[0]
        
        # 随机替换头或尾
        if random.random() < 0.5:
            # 替换头
            new_s = random.choice(list(kg.entities))
            while new_s == s:
                new_s = random.choice(list(kg.entities))
            s = new_s
        else:
            # 替换尾
            new_o = random.choice(list(kg.entities))
            while new_o == o:
                new_o = random.choice(list(kg.entities))
            o = new_o
        
        negatives.append((s, p, o, t))
    
    return negatives


def train_tkg_embedding(kg, model_class="TComplEx", 
                        epochs: int = 100, 
                        batch_size: int = 32,
                        learning_rate: float = 0.01) -> TKGEmbedding:
    """
    训练时序知识图谱嵌入模型
    
    参数:
        kg: 知识图谱
        model_class: 模型类型 ("TComplEx" 或 "TeLM")
        epochs: 训练轮数
        batch_size: 批大小
        learning_rate: 学习率
    
    返回:
        训练好的模型
    """
    # 获取实体和关系数量
    num_entities = len(kg.entities)
    num_relations = len(kg.predicates)
    
    # 创建模型
    if model_class == "TComplEx":
        model = TComplEx(num_entities, num_relations)
    else:
        model = TeLM(num_entities, num_relations)
    
    # 准备训练数据
    triples = list(kg.triples.keys())
    times = {}
    for i, (s, p, o) in enumerate(triples):
        intervals = kg.triples[(s, p, o)]
        times[(s, p, o)] = intervals[0][0] % 1000  # 归一化到0-999
    
    # 实体和关系ID映射
    entity_to_id = {e: i for i, e in enumerate(kg.entities)}
    relation_to_id = {r: i for i, r in enumerate(kg.predicates)}
    
    # 训练循环
    for epoch in range(epochs):
        total_loss = 0.0
        num_batches = 0
        
        # 随机打乱数据
        random.shuffle(triples)
        
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i+batch_size]
            
            # 准备正负样本
            pos_samples = []
            neg_samples = []
            
            for s, p, o in batch:
                t = times[(s, p, o)]
                s_id = entity_to_id.get(s, 0)
                p_id = relation_to_id.get(p, 0)
                o_id = entity_to_id.get(o, 0)
                t_id = t % 1000
                
                pos_samples.append((s_id, p_id, o_id, t_id))
                
                # 生成负样本
                if random.random() < 0.5:
                    s_neg = random.randint(0, num_entities - 1)
                    neg_samples.append((s_neg, p_id, o_id, t_id))
                else:
                    o_neg = random.randint(0, num_entities - 1)
                    neg_samples.append((s_id, p_id, o_neg, t_id))
            
            # 计算损失
            loss = model.train_step(pos_samples, neg_samples)
            total_loss += loss
            num_batches += 1
            
            # 简化：不做实际梯度更新（需要PyTorch等框架）
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}: avg_loss = {total_loss / max(num_batches, 1):.4f}")
    
    return model


if __name__ == "__main__":
    print("=== 时序知识图谱嵌入测试 ===")
    
    # 创建测试数据
    from temporal_knowledge_graph import TemporalKG
    
    kg = TemporalKG()
    kg.add_triple("Alice", "knows", "Bob", 2020)
    kg.add_triple("Bob", "knows", "Charlie", 2020)
    kg.add_triple("Alice", "knows", "Bob", 2021)
    kg.add_triple("Bob", "knows", "Charlie", 2021)
    kg.add_triple("Alice", "knows", "Charlie", 2021)
    
    # 准备ID映射
    entities = list(kg.entities)
    relations = list(kg.predicates)
    entity_to_id = {e: i for i, e in enumerate(entities)}
    relation_to_id = {r: i for i, r in enumerate(relations)}
    
    # 创建TComplEx模型
    print("\nTComplEx模型:")
    tcomplex = TComplEx(len(entities), len(relations), embedding_dim=16)
    
    # 计算得分
    s = entity_to_id["Alice"]
    p = relation_to_id["knows"]
    o = entity_to_id["Bob"]
    t = 2020
    
    score = tcomplex.score(s, p, o, t)
    print(f"  score(Alice, knows, Bob, 2020) = {score:.4f}")
    
    # 预测
    print("\n预测 Alice 在 2020 年 knows 谁:")
    predictions = tcomplex.predict(s, p, t, k=3)
    for pred_o, pred_score in predictions:
        print(f"  {entities[pred_o]}: {pred_score:.4f}")
    
    # 创建TeLM模型
    print("\n\nTeLM模型:")
    telm = TeLM(len(entities), len(relations), embedding_dim=16)
    
    score_telm = telm.score(s, p, o, t)
    print(f"  score(Alice, knows, Bob, 2020) = {score_telm:.4f}")
    
    print("\n=== 测试完成 ===")

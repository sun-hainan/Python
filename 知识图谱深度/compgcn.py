# -*- coding: utf-8 -*-

"""

算法实现：知识图谱深度 / compgcn



本文件实现 compgcn 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional





class GraphConvolution:

    """图卷积层"""

    

    def __init__(self, in_dim: int, out_dim: int):

        self.W = np.random.randn(in_dim, out_dim) * 0.1

        self.bias = np.zeros(out_dim)

    

    def forward(self, node_embeddings: np.ndarray,

                adjacency: np.ndarray) -> np.ndarray:

        """

        前向传播

        

        参数:

            node_embeddings: 节点嵌入 (n_nodes, in_dim)

            adjacency: 邻接矩阵 (n_nodes, n_nodes)

        

        返回:

            更新后的嵌入 (n_nodes, out_dim)

        """

        # 聚合邻居信息

        aggregated = adjacency @ node_embeddings

        

        # 线性变换

        output = aggregated @ self.W + self.bias

        

        # ReLU激活

        output = np.maximum(output, 0)

        

        return output





class CompositionFunction:

    """组合函数"""

    

    @staticmethod

    def sub(e1: np.ndarray, e2: np.ndarray) -> np.ndarray:

        """减法组合: e1 - e2"""

        return e1 - e2

    

    @staticmethod

    def mul(e1: np.ndarray, e2: np.ndarray) -> np.ndarray:

        """乘法组合: e1 * e2"""

        return e1 * e2

    

    @staticmethod

    def corr(e1: np.ndarray, e2: np.ndarray) -> np.ndarray:

        """相关组合: e1 + e2 - e1 * e2"""

        return e1 + e2 - e1 * e2

    

    @staticmethod

    def circular_correlation(e1: np.ndarray, e2: np.ndarray) -> np.ndarray:

        """循环相关（用于RotatE风格）"""

        d = len(e1)

        result = np.zeros(d)

        

        for k in range(d):

            for j in range(d):

                result[k] += e1[j] * e2[(j - k) % d]

        

        return result





class CompGCNLayer:

    """

    CompGCN层

    

    参数:

        in_dim: 输入维度

        out_dim: 输出维度

        composition: 组合函数类型

        n_relations: 关系数量

    """

    

    def __init__(self, in_dim: int, out_dim: int,

                 composition: str = 'sub',

                 n_relations: int = 10):

        self.composition = composition

        self.n_relations = n_relations

        

        # 节点变换

        self.W_s = np.random.randn(in_dim, out_dim) * 0.1  # 主语变换

        self.W_r = np.random.randn(in_dim, out_dim) * 0.1  # 关系变换

        self.W_o = np.random.randn(in_dim, out_dim) * 0.1  # 宾语变换

        

        # 关系嵌入

        self.relation_embeddings = np.random.randn(n_relations, out_dim) * 0.1

    

    def _compose(self, e1: np.ndarray, e2: np.ndarray) -> np.ndarray:

        """执行组合"""

        if self.composition == 'sub':

            return CompositionFunction.sub(e1, e2)

        elif self.composition == 'mul':

            return CompositionFunction.mul(e1, e2)

        elif self.composition == 'corr':

            return CompositionFunction.corr(e1, e2)

        else:

            return CompositionFunction.sub(e1, e2)

    

    def forward(self, head_embeddings: np.ndarray,

               tail_embeddings: np.ndarray,

               relation_indices: np.ndarray,

               edge_weights: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:

        """

        前向传播

        

        参数:

            head_embeddings: 头实体嵌入 (n_edges, in_dim)

            tail_embeddings: 尾实体嵌入 (n_edges, in_dim)

            relation_indices: 关系索引 (n_edges,)

            edge_weights: 边权重（可选）

        

        返回:

            (更新的头嵌入, 更新后的尾嵌入)

        """

        n_edges = len(head_embeddings)

        

        # 组合头尾实体

        composed = np.zeros((n_edges, head_embeddings.shape[1]))

        for i in range(n_edges):

            h = head_embeddings[i]

            t = tail_embeddings[i]

            composed[i] = self._compose(h, t)

        

        # 应用关系变换

        relation_emb = self.relation_embeddings[relation_indices]

        composed = composed @ self.W_r + relation_emb

        

        # 如果有权重

        if edge_weights is not None:

            composed = composed * edge_weights[:, np.newaxis]

        

        # 聚合（简化：平均）

        if len(composed) > 0:

            aggregated = np.mean(composed, axis=0)

        else:

            aggregated = np.zeros(head_embeddings.shape[1])

        

        # 更新嵌入

        updated_head = head_embeddings @ self.W_s + aggregated

        updated_tail = tail_embeddings @ self.W_o + aggregated

        

        return updated_head, updated_tail





class CompGCNModel:

    """

    CompGCN模型

    

    用于知识图谱补全

    """

    

    def __init__(self, n_entities: int, n_relations: int,

                 embedding_dim: int = 100,

                 n_layers: int = 2,

                 composition: str = 'sub'):

        self.n_entities = n_entities

        self.n_relations = n_relations

        self.embedding_dim = embedding_dim

        self.n_layers = n_layers

        

        np.random.seed(42)

        

        # 实体嵌入

        self.entity_embeddings = np.random.randn(n_entities, embedding_dim) * 0.1

        

        # 关系嵌入

        self.relation_embeddings = np.random.randn(n_relations, embedding_dim) * 0.1

        

        # GCN层

        self.gcn_layers = []

        for _ in range(n_layers):

            self.gcn_layers.append(

                CompGCNLayer(embedding_dim, embedding_dim, composition, n_relations)

            )

        

        # 评分函数

        self.score_func = 'distmult'  # 或 'transE', 'rotate'

    

    def score(self, head_idx: int, relation_idx: int, tail_idx: int) -> float:

        """计算三元组分数"""

        h = self.entity_embeddings[head_idx]

        r = self.relation_embeddings[relation_idx]

        t = self.entity_embeddings[tail_idx]

        

        if self.score_func == 'distmult':

            # DistMult: <h, r, t>

            return float(np.sum(h * r * t))

        elif self.score_func == 'transE':

            # TransE: -||h + r - t||

            return -float(np.linalg.norm(h + r - t))

        else:

            return float(np.sum(h * r * t))

    

    def predict(self, head_idx: int, relation_idx: int,

               top_k: int = 10) -> List[Tuple[int, float]]:

        """预测尾实体"""

        h = self.entity_embeddings[head_idx]

        r = self.relation_embeddings[relation_idx]

        

        # 计算所有尾实体的分数

        scores = []

        for tail_idx in range(self.n_entities):

            t = self.entity_embeddings[tail_idx]

            

            if self.score_func == 'distmult':

                score = np.sum(h * r * t)

            else:

                score = -np.linalg.norm(h + r - t)

            

            scores.append((tail_idx, float(score)))

        

        scores.sort(key=lambda x: x[1], reverse=True)

        

        return scores[:top_k]





class CompGCNTrainer:

    """CompGCN训练器"""

    

    def __init__(self, model: CompGCNModel, learning_rate: float = 0.001):

        self.model = model

        self.lr = learning_rate

    

    def train_step(self, triples: List[Tuple[int, int, int]],

                  negative_samples: int = 5,

                  margin: float = 2.0) -> float:

        """单步训练"""

        total_loss = 0.0

        

        for h, r, t in triples:

            # 正例分数

            pos_score = self.model.score(h, r, t)

            

            # 负例

            for _ in range(negative_samples):

                # 替换尾实体

                neg_t = np.random.randint(self.model.n_entities)

                while neg_t == t:

                    neg_t = np.random.randint(self.model.n_entities)

                

                neg_score = self.model.score(h, r, neg_t)

                

                loss = max(0, margin - pos_score + neg_score)

                total_loss += loss

                

                if loss > 0:

                    self._update_embeddings(h, r, t, neg_t)

        

        return total_loss

    

    def _update_embeddings(self, h: int, r: int, t: int, neg_t: int):

        """更新嵌入（简化）"""

        lr = self.lr

        

        # 随机梯度

        for embeddings in [self.model.entity_embeddings, self.model.relation_embeddings]:

            noise = np.random.randn(*embeddings.shape) * 0.001

            embeddings -= lr * noise





def build_adjacency_from_triples(triples: List[Tuple[int, int, int]],

                                n_entities: int) -> np.ndarray:

    """

    从三元组构建邻接矩阵

    """

    adj = np.zeros((n_entities, n_entities))

    

    for h, r, t in triples:

        adj[h, t] += 1

    

    # 添加自环

    adj += np.eye(n_entities)

    

    # 对称化

    adj = (adj + adj.T) / 2

    

    # 归一化

    degrees = np.sum(adj, axis=1, keepdims=True)

    degrees = np.maximum(degrees, 1)

    adj = adj / degrees

    

    return adj





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("CompGCN 图神经网络知识图谱补全测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 模拟数据

    n_entities = 1000

    n_relations = 50

    n_triples = 5000

    

    triples = []

    for _ in range(n_triples):

        h = np.random.randint(n_entities)

        r = np.random.randint(n_relations)

        t = np.random.randint(n_entities)

        triples.append((h, r, t))

    

    print(f"\n数据: {n_entities} 实体, {n_relations} 关系, {n_triples} 三元组")

    

    # 创建模型

    print("\n--- 初始化CompGCN ---")

    model = CompGCNModel(n_entities, n_relations, 

                         embedding_dim=100, n_layers=2)

    print(f"模型: {n_layers}层, 嵌入维度 {model.embedding_dim}")

    

    # 构建邻接矩阵

    adj = build_adjacency_from_triples(triples, n_entities)

    print(f"邻接矩阵形状: {adj.shape}")

    

    # 训练

    print("\n--- 训练 ---")

    trainer = CompGCNTrainer(model, learning_rate=0.001)

    

    train_triples = triples[:4000]

    test_triples = triples[4000:]

    

    for epoch in range(5):

        loss = trainer.train_step(train_triples[:100], negative_samples=3)

        if (epoch + 1) % 2 == 0:

            print(f"Epoch {epoch + 1}: Loss = {loss:.4f}")

    

    # 评估

    print("\n--- 评估 ---")

    test_sample = test_triples[:10]

    

    total_score = 0

    for h, r, t in test_sample:

        score = model.score(h, r, t)

        total_score += score

    

    avg_score = total_score / len(test_sample)

    print(f"测试集平均分数: {avg_score:.4f}")

    

    # 预测示例

    print("\n--- 预测示例 ---")

    h, r, _ = test_triples[0]

    print(f"查询: head={h}, relation={r}")

    

    predictions = model.predict(h, r, top_k=5)

    print(f"预测top-5: {predictions}")

    

    print("\n" + "=" * 50)

    print("测试完成")


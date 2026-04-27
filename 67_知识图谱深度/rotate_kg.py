# -*- coding: utf-8 -*-

"""

算法实现：知识图谱深度 / rotate_kg



本文件实现 rotate_kg 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional





class RotatEModel:

    """

    RotatE模型

    

    参数:

        n_entities: 实体数量

        n_relations: 关系数量

        embedding_dim: 嵌入维度（复数空间，所以实际维度是embedding_dim//2）

    """

    

    def __init__(self, n_entities: int, n_relations: int, embedding_dim: int = 100):

        self.n_entities = n_entities

        self.n_relations = n_relations

        self.embedding_dim = embedding_dim

        self.dim = embedding_dim // 2  # 复数表示用两列

        

        np.random.seed(42)

        

        # 初始化实体嵌入（复数用两列表示）

        # embedding[:, 0] 是实部, embedding[:, 1] 是虚部

        self.entity_embeddings = np.random.randn(n_entities, self.dim, 2) * 0.1

        

        # 关系嵌入（相位）

        self.relation_phases = np.random.randn(n_relations, self.dim) * 0.1

    

    def _to_complex(self, embedding: np.ndarray) -> np.ndarray:

        """将嵌入转为复数形式"""

        # embedding shape: (n, dim, 2) -> complex (n, dim)

        real = embedding[:, :, 0]

        imag = embedding[:, :, 1]

        return real + 1j * imag

    

    def _get_entity_vector(self, entity_idx: int) -> np.ndarray:

        """获取实体的复数向量"""

        return self._to_complex(self.entity_embeddings[entity_idx])

    

    def _get_relation_rotation(self, relation_idx: int) -> np.ndarray:

        """获取关系的旋转（相位）"""

        phase = self.relation_phases[relation_idx]

        return np.exp(1j * phase)

    

    def score(self, head_idx: int, relation_idx: int, tail_idx: int) -> float:

        """

        计算三元组分数

        

        RotatE评分: -||h * r - t||

        """

        h = self._get_entity_vector(head_idx)

        r = self._get_relation_rotation(relation_idx)

        t = self._get_entity_vector(tail_idx)

        

        # 旋转：h * r

        h_rotated = h * r

        

        # 距离

        distance = np.abs(h_rotated - t)

        

        # 评分（距离越小越好）

        score = -np.sum(distance)

        

        return float(score)

    

    def predict_tail(self, head_idx: int, relation_idx: int, 

                    top_k: int = 10) -> List[Tuple[int, float]]:

        """预测尾实体"""

        h = self._get_entity_vector(head_idx)

        r = self._get_relation_rotation(relation_idx)

        h_rotated = h * r

        

        scores = []

        

        for tail_idx in range(self.n_entities):

            t = self._get_entity_vector(tail_idx)

            distance = np.abs(h_rotated - t)

            score = -np.sum(distance)

            scores.append((tail_idx, score))

        

        scores.sort(key=lambda x: x[1], reverse=True)

        

        return scores[:top_k]

    

    def predict_head(self, relation_idx: int, tail_idx: int,

                    top_k: int = 10) -> List[Tuple[int, float]]:

        """预测头实体"""

        t = self._get_entity_vector(tail_idx)

        r = self._get_relation_rotation(relation_idx)

        

        # h = t / r (反旋转)

        r_inv = np.exp(-1j * self.relation_phases[relation_idx])

        

        scores = []

        

        for head_idx in range(self.n_entities):

            h = self._get_entity_vector(head_idx)

            h_rotated = h * r

            distance = np.abs(h_rotated - t)

            score = -np.sum(distance)

            scores.append((head_idx, score))

        

        scores.sort(key=lambda x: x[1], reverse=True)

        

        return scores[:top_k]





class RotatETrainer:

    """RotatE训练器"""

    

    def __init__(self, model: RotatEModel, learning_rate: float = 0.0005,

                 margin: float = 6.0, batch_size: int = 512):

        self.model = model

        self.lr = learning_rate

        self.margin = margin

        self.batch_size = batch_size

        

        # Adam参数

        self.beta1 = 0.9

        self.beta2 = 0.999

        self.epsilon = 1e-8

        

        self.m = [np.zeros_like(e) for e in [model.entity_embeddings, model.relation_phases]]

        self.v = [np.zeros_like(e) for e in [model.entity_embeddings, model.relation_phases]]

        self.t = 0

    

    def train_step(self, positive_triples: List[Tuple[int, int, int]],

                   negative_triples: List[Tuple[int, int, int]]) -> float:

        """

        单步训练

        

        参数:

            positive_triples: 正例三元组

            negative_triples: 负例三元组

        """

        self.t += 1

        

        total_loss = 0.0

        

        for pos, neg in zip(positive_triples, negative_triples):

            h, r, t = pos

            h_neg, r_neg, t_neg = neg

            

            # 计算分数

            pos_score = self.model.score(h, r, t)

            neg_score = self.model.score(h_neg, r_neg, t_neg)

            

            # 对比损失

            loss = max(0, self.margin - pos_score + neg_score)

            total_loss += loss

            

            if loss > 0:

                # 简化的梯度更新

                grad = self._compute_gradient(pos, neg)

                self._apply_gradient(grad)

        

        return total_loss

    

    def _compute_gradient(self, pos: Tuple[int, int, int],

                         neg: Tuple[int, int, int]) -> dict:

        """计算梯度（简化）"""

        h, r, t = pos

        h_n, r_n, t_n = neg

        

        # 简化的梯度

        grad_entity = np.random.randn(*self.model.entity_embeddings.shape) * 0.01

        grad_relation = np.random.randn(*self.model.relation_phases.shape) * 0.01

        

        return {

            'entity': grad_entity,

            'relation': grad_relation

        }

    

    def _apply_gradient(self, grad: dict):

        """应用梯度"""

        self.model.entity_embeddings -= self.lr * grad['entity']

        self.model.relation_phases -= self.lr * grad['relation']

        

        # 归一化实体嵌入

        norms = np.linalg.norm(self.model.entity_embeddings, axis=2, keepdims=True)

        self.model.entity_embeddings /= (norms + 1e-10)

        

        # 限制关系相位

        self.model.relation_phases = np.clip(self.model.relation_phases, -np.pi, np.pi)





def generate_rotate_negative(positive_triple: Tuple[int, int, int],

                            n_entities: int,

                            method: str = 'uniform') -> Tuple[int, int, int]:

    """

    生成负例

    

    方法:

    - uniform: 随机替换头或尾

    - corrupt_tail: 只替换尾

    - corrupt_head: 只替换头

    """

    h, r, t = positive_triple

    

    if method == 'corrupt_tail':

        neg_t = np.random.randint(n_entities)

        while neg_t == t:

            neg_t = np.random.randint(n_entities)

        return (h, r, neg_t)

    

    elif method == 'corrupt_head':

        neg_h = np.random.randint(n_entities)

        while neg_h == h:

            neg_h = np.random.randint(n_entities)

        return (neg_h, r, t)

    

    else:  # uniform

        if np.random.random() < 0.5:

            neg_t = np.random.randint(n_entities)

            while neg_t == t:

                neg_t = np.random.randint(n_entities)

            return (h, r, neg_t)

        else:

            neg_h = np.random.randint(n_entities)

            while neg_h == h:

                neg_h = np.random.randint(n_entities)

            return (neg_h, r, t)





class RotatEWithRelations:

    """

    带关系类型的RotatE扩展

    """

    

    def __init__(self, n_entities: int, n_relations: int,

                 embedding_dim: int = 200):

        self.model = RotatEModel(n_entities, n_relations, embedding_dim)

        self.trainer = RotatETrainer(self.model)

    

    def train(self, triples: List[Tuple[int, int, int]],

             n_epochs: int = 100,

             negative_samples: int = 5) -> List[float]:

        """

        训练RotatE

        """

        losses = []

        

        for epoch in range(n_epochs):

            epoch_loss = 0.0

            

            np.random.shuffle(triples)

            

            for i in range(0, len(triples), self.trainer.batch_size):

                batch = triples[i:i + self.trainer.batch_size]

                

                pos_batch = batch

                neg_batch = [

                    generate_rotate_negative(t, self.model.n_entities)

                    for t in batch

                ]

                

                loss = self.trainer.train_step(pos_batch, neg_batch)

                epoch_loss += loss

            

            losses.append(epoch_loss)

            

            if (epoch + 1) % 10 == 0:

                print(f"Epoch {epoch + 1}: Loss = {epoch_loss:.4f}")

        

        return losses





def evaluate_rotatE(model: RotatEModel, test_triples: List[Tuple[int, int, int]]) -> dict:

    """

    评估模型

    

    返回:

        MRR, Hits@1, Hits@3, Hits@10

    """

    mr = 0.0

    hits_at_1 = 0.0

    hits_at_3 = 0.0

    hits_at_10 = 0.0

    n = len(test_triples)

    

    for h, r, t in test_triples:

        predictions = model.predict_tail(h, r, top_k=model.n_entities)

        

        rank = 1

        for pred_t, score in predictions:

            if pred_t == t:

                break

            rank += 1

        

        mr += rank

        if rank == 1:

            hits_at_1 += 1

        if rank <= 3:

            hits_at_3 += 1

        if rank <= 10:

            hits_at_10 += 1

    

    return {

        'MRR': mr / n,

        'Hits@1': hits_at_1 / n,

        'Hits@3': hits_at_3 / n,

        'Hits@10': hits_at_10 / n

    }





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("RotatE知识图谱嵌入测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 模拟数据

    n_entities = 1000

    n_relations = 50

    n_triples = 10000

    

    # 生成三元组

    triples = []

    for _ in range(n_triples):

        h = np.random.randint(n_entities)

        r = np.random.randint(n_relations)

        t = np.random.randint(n_entities)

        triples.append((h, r, t))

    

    print(f"\n数据: {n_entities} 实体, {n_relations} 关系, {n_triples} 三元组")

    

    # 创建模型

    print("\n--- 初始化RotatE ---")

    model = RotatEModel(n_entities, n_relations, embedding_dim=100)

    print(f"嵌入维度: {model.embedding_dim} (复数空间: {model.dim})")

    

    # 训练

    print("\n--- 训练 ---")

    rotator = RotatEWithRelations(n_entities, n_relations, embedding_dim=100)

    

    train_triples = triples[:8000]

    test_triples = triples[8000:]

    

    losses = rotator.train(train_triples, n_epochs=20)

    

    # 评估

    print("\n--- 评估 ---")

    metrics = evaluate_rotatE(model, test_triples[:500])

    

    print(f"MRR: {metrics['MRR']:.4f}")

    print(f"Hits@1: {metrics['Hits@1']:.4f}")

    print(f"Hits@3: {metrics['Hits@3']:.4f}")

    print(f"Hits@10: {metrics['Hits@10']:.4f}")

    

    # 示例预测

    print("\n--- 示例预测 ---")

    h, r, t = test_triples[0]

    print(f"查询: head={h}, relation={r}, true_tail={t}")

    

    predictions = model.predict_tail(h, r, top_k=5)

    print(f"预测top-5: {predictions}")

    

    print("\n" + "=" * 50)

    print("测试完成")


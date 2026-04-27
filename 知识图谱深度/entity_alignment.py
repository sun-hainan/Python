# -*- coding: utf-8 -*-

"""

算法实现：知识图谱深度 / entity_alignment



本文件实现 entity_alignment 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Set, Optional

from collections import defaultdict





class KnowledgeGraph:

    """知识图谱"""

    

    def __init__(self, name: str = "KG"):

        self.name = name

        self.entities: Set[str] = set()

        self.relations: Set[str] = set()

        self.triples: List[Tuple[str, str, str]] = []

        self.entity_embeddings: Dict[str, np.ndarray] = {}

        self.relation_embeddings: Dict[str, np.ndarray] = {}

    

    def add_triple(self, head: str, relation: str, tail: str):

        """添加三元组"""

        self.entities.add(head)

        self.entities.add(tail)

        self.relations.add(relation)

        self.triples.append((head, relation, tail))

    

    def get_neighbors(self, entity: str) -> List[Tuple[str, str]]:

        """获取邻居"""

        neighbors = []

        for h, r, t in self.triples:

            if h == entity:

                neighbors.append((r, t))

            elif t == entity:

                neighbors.append((r, h))

        return neighbors





class AlignmentBootstrap:

    """对齐引导器"""

    

    def __init__(self, kg1: KnowledgeGraph, kg2: KnowledgeGraph):

        self.kg1 = kg1

        self.kg2 = kg2

        

        # 对齐种子

        self.seed_alignments: List[Tuple[str, str]] = []

        

        # 已学习的对齐

        self.learned_alignments: Set[Tuple[str, str]] = set()

        

        # 实体映射

        self.entity_mapping: Dict[str, str] = {}

    

    def add_seed_alignment(self, e1: str, e2: str):

        """添加种子对齐"""

        self.seed_alignments.append((e1, e2))

        self.learned_alignments.add((e1, e2))

        self.entity_mapping[e1] = e2

    

    def get_entity_vector(self, entity: str, embeddings: Dict[str, np.ndarray]) -> np.ndarray:

        """获取实体向量"""

        return embeddings.get(entity, np.zeros(100))  # 假设嵌入维度100

    

    def compute_alignment_score(self, e1: str, e2: str,

                               emb1: Dict[str, np.ndarray],

                               emb2: Dict[str, np.ndarray]) -> float:

        """计算对齐分数"""

        v1 = self.get_entity_vector(e1, emb1)

        v2 = self.get_entity_vector(e2, emb2)

        

        return -np.linalg.norm(v1 - v2)  # 距离越小越好

    

    def find_new_alignments(self, embeddings1: Dict[str, np.ndarray],

                            embeddings2: Dict[str, np.ndarray],

                            top_k: int = 5) -> List[Tuple[str, str]]:

        """基于当前嵌入找到新的对齐"""

        new_alignments = []

        

        for e1 in self.kg1.entities:

            if e1 in self.entity_mapping:

                continue

            

            candidates = []

            for e2 in self.kg2.entities:

                if e2 in self.entity_mapping.values():

                    continue

                

                score = self.compute_alignment_score(e1, e2, embeddings1, embeddings2)

                candidates.append((e2, score))

            

            # 按分数排序

            candidates.sort(key=lambda x: x[1], reverse=True)

            

            # 取top-k

            for e2, score in candidates[:top_k]:

                new_alignments.append((e1, e2))

        

        return new_alignments





class IPTransE:

    """

    IPTransE模型

    

    参数:

        embedding_dim: 嵌入维度

        learning_rate: 学习率

        margin: 间隔

        n_iterations: 迭代次数

    """

    

    def __init__(self, embedding_dim: int = 100,

                 learning_rate: float = 0.01,

                 margin: float = 1.0,

                 n_iterations: int = 100):

        self.embedding_dim = embedding_dim

        self.lr = learning_rate

        self.margin = margin

        self.n_iterations = n_iterations

        

        self.kg1_embeddings: Dict[str, np.ndarray] = {}

        self.kg2_embeddings: Dict[str, np.ndarray] = {}

        self.relation_embeddings: Dict[str, np.ndarray] = {}

    

    def _init_embeddings(self, kg1: KnowledgeGraph, kg2: KnowledgeGraph):

        """初始化嵌入"""

        np.random.seed(42)

        

        for entity in kg1.entities:

            self.kg1_embeddings[entity] = np.random.randn(self.embedding_dim) * 0.1

        

        for entity in kg2.entities:

            self.kg2_embeddings[entity] = np.random.randn(self.embedding_dim) * 0.1

        

        for relation in kg1.relations | kg2.relations:

            self.relation_embeddings[relation] = np.random.randn(self.embedding_dim) * 0.1

    

    def _transE_score(self, head: np.ndarray, relation: str, tail: np.ndarray) -> float:

        """TransE评分函数"""

        r = self.relation_embeddings.get(relation, np.zeros(self.embedding_dim))

        return -np.linalg.norm(head + r - tail)

    

    def _train_transE(self, triples: List[Tuple[str, str, str]],

                     embeddings: Dict[str, np.ndarray],

                     is_kg1: bool) -> float:

        """训练TransE"""

        total_loss = 0.0

        

        np.random.shuffle(triples)

        

        for h, r, t in triples[:100]:  # 简化：每epoch只使用100个三元组

            head_emb = embeddings.get(h, np.zeros(self.embedding_dim))

            tail_emb = embeddings.get(t, np.zeros(self.embedding_dim))

            rel_emb = self.relation_embeddings.get(r, np.zeros(self.embedding_dim))

            

            pos_score = self._transE_score(head_emb, r, tail_emb)

            

            # 生成负例

            neg_tail = list(embeddings.keys())[np.random.randint(len(embeddings))]

            while neg_tail == t:

                neg_tail = list(embeddings.keys())[np.random.randint(len(embeddings))]

            

            neg_emb = embeddings[neg_tail]

            neg_score = self._transE_score(head_emb, r, neg_emb)

            

            # 损失

            loss = max(0, self.margin - pos_score + neg_score)

            total_loss += loss

            

            if loss > 0:

                # 梯度

                grad_pos = (head_emb + rel_emb - tail_emb) / np.linalg.norm(head_emb + rel_emb - tail_emb + 1e-10)

                grad_neg = (head_emb + rel_emb - neg_emb) / np.linalg.norm(head_emb + rel_emb - neg_emb + 1e-10)

                

                # 更新

                if is_kg1:

                    self.kg1_embeddings[h] -= self.lr * grad_pos

                    self.kg1_embeddings[t] += self.lr * grad_pos

                else:

                    self.kg2_embeddings[h] -= self.lr * grad_pos

                    self.kg2_embeddings[t] += self.lr * grad_pos

        

        return total_loss

    

    def train(self, kg1: KnowledgeGraph, kg2: KnowledgeGraph,

             seed_alignments: List[Tuple[str, str]]) -> Dict[str, str]:

        """

        训练IPTransE

        

        参数:

            kg1, kg2: 两个知识图谱

            seed_alignments: 种子对齐

        

        返回:

            学习到的对齐映射

        """

        self._init_embeddings(kg1, kg2)

        

        current_alignments = set(seed_alignments)

        

        for iteration in range(self.n_iterations):

            # 1. 训练TransE

            loss1 = self._train_transE(kg1.triples, self.kg1_embeddings, True)

            loss2 = self._train_transE(kg2.triples, self.kg2_embeddings, False)

            

            # 2. 对齐传播

            new_alignments = self._alignment_propagation(

                kg1, kg2, current_alignments, iterations=3

            )

            

            current_alignments.update(new_alignments)

            

            if (iteration + 1) % 10 == 0:

                print(f"迭代 {iteration + 1}: 当前对齐数 = {len(current_alignments)}")

        

        return {e1: e2 for e1, e2 in current_alignments}

    

    def _alignment_propagation(self, kg1: KnowledgeGraph, kg2: KnowledgeGraph,

                             current_alignments: Set[Tuple[str, str]],

                             iterations: int = 3) -> Set[Tuple[str, str]]:

        """对齐传播"""

        new_alignments = set()

        

        for iteration in range(iterations):

            temp_alignments = set(current_alignments)

            

            for e1 in kg1.entities:

                if any(a[0] == e1 for a in temp_alignments):

                    continue

                

                # 基于结构相似性找候选

                e1_neighbors = set(kg1.get_neighbors(e1))

                

                best_candidate = None

                best_score = -1

                

                for e2 in kg2.entities:

                    if any(a[1] == e2 for a in temp_alignments):

                        continue

                    

                    e2_neighbors = set(kg2.get_neighbors(e2))

                    

                    # 结构相似度

                    if len(e1_neighbors) > 0 and len(e2_neighbors) > 0:

                        common = len(e1_neighbors & e2_neighbors)

                        structure_score = common / len(e1_neighbors | e2_neighbors)

                        

                        # 嵌入相似度

                        emb_score = -np.linalg.norm(

                            self.kg1_embeddings.get(e1, np.zeros(self.embedding_dim)) -

                            self.kg2_embeddings.get(e2, np.zeros(self.embedding_dim))

                        )

                        

                        combined_score = 0.5 * structure_score + 0.5 * emb_score

                        

                        if combined_score > best_score:

                            best_score = combined_score

                            best_candidate = e2

                

                if best_candidate and best_score > 0.3:  # 阈值

                    temp_alignments.add((e1, best_candidate))

                    new_alignments.add((e1, best_candidate))

            

            current_alignments.update(new_alignments)

        

        return new_alignments





def compute_alignment_metrics(predicted_alignments: Dict[str, str],

                            ground_truth: Dict[str, str]) -> dict:

    """

    计算对齐评估指标

    

    返回:

        Precision, Recall, F1, Hits@1

    """

    n_predicted = len(predicted_alignments)

    n_ground_truth = len(ground_truth)

    

    if n_predicted == 0:

        return {'precision': 0, 'recall': 0, 'f1': 0, 'hits@1': 0}

    

    # 计算正确匹配数

    correct = sum(1 for e1, e2 in predicted_alignments.items() 

                 if ground_truth.get(e1) == e2)

    

    # 计算Hits@1

    hits_at_1 = sum(1 for e1, e2 in predicted_alignments.items()

                   if ground_truth.get(e1) == e2 and 

                   list(predicted_alignments.keys()).index(e1) == 0)

    

    precision = correct / n_predicted

    recall = correct / n_ground_truth if n_ground_truth > 0 else 0

    f1 = 2 * precision * recall / (precision + recall + 1e-10)

    hits_at_1_score = hits_at_1 / n_predicted

    

    return {

        'precision': precision,

        'recall': recall,

        'f1': f1,

        'hits@1': hits_at_1_score

    }





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("IPTransE实体对齐测试")

    print("=" * 50)

    

    # 创建两个知识图谱

    kg1 = KnowledgeGraph("KG1")

    kg2 = KnowledgeGraph("KG2")

    

    # KG1三元组

    kg1_triples = [

        ("Alice", "friendOf", "Bob"),

        ("Bob", "friendOf", "Charlie"),

        ("Alice", "worksAt", "Google"),

        ("Bob", "worksAt", "Google"),

        ("Google", "locatedIn", "California"),

    ]

    

    # KG2三元组（部分实体对应）

    kg2_triples = [

        ("Alice_2", "friendOf", "Bob_2"),

        ("Bob_2", "friendOf", "Charlie_2"),

        ("Alice_2", "employedBy", "Google_2"),

        ("Google_2", "in", "California_2"),

    ]

    

    for h, r, t in kg1_triples:

        kg1.add_triple(h, r, t)

    

    for h, r, t in kg2_triples:

        kg2.add_triple(h, r, t)

    

    print(f"KG1: {len(kg1.entities)} 实体, {len(kg1.triples)} 三元组")

    print(f"KG2: {len(kg2.entities)} 实体, {len(kg2.triples)} 三元组")

    

    # 种子对齐

    seed_alignments = [

        ("Alice", "Alice_2"),

        ("Bob", "Bob_2"),

    ]

    

    print(f"\n种子对齐: {len(seed_alignments)} 对")

    

    # 训练IPTransE

    print("\n--- 训练IPTransE ---")

    model = IPTransE(embedding_dim=50, n_iterations=50)

    

    learned_alignments = model.train(kg1, kg2, seed_alignments)

    

    print(f"学习到的对齐: {len(learned_alignments)} 对")

    

    # 显示学习到的对齐

    print("\n学习到的对齐:")

    for e1, e2 in learned_alignments.items():

        print(f"  {e1} <-> {e2}")

    

    # 评估（使用部分ground truth）

    ground_truth = {

        "Alice": "Alice_2",

        "Bob": "Bob_2",

        "Charlie": "Charlie_2",

        "Google": "Google_2",

    }

    

    predicted_alignment = {"Alice": "Alice_2", "Bob": "Bob_2"}  # 简化预测

    metrics = compute_alignment_metrics(predicted_alignment, ground_truth)

    

    print(f"\n评估指标:")

    print(f"  Precision: {metrics['precision']:.4f}")

    print(f"  Recall: {metrics['recall']:.4f}")

    print(f"  F1: {metrics['f1']:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


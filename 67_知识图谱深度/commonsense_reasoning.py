# -*- coding: utf-8 -*-

"""

算法实现：知识图谱深度 / commonsense_reasoning



本文件实现 commonsense_reasoning 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Set, Optional

from collections import defaultdict, deque





class Concept:

    """概念"""

    

    def __init__(self, name: str, lang: str = "en"):

        self.name = name

        self.lang = lang

        self.embeddings: Optional[np.ndarray] = None

    

    def __hash__(self):

        return hash(self.name)

    

    def __eq__(self, other):

        return self.name == other.name





class ConceptRelation:

    """概念间的关系"""

    

    def __init__(self, start: Concept, relation_type: str, end: Concept, weight: float = 1.0):

        self.start = start

        self.relation_type = relation_type

        self.end = end

        self.weight = weight





class ConceptNet:

    """

    简化的ConceptNet实现

    

    参数:

        concepts: 概念集合

        relations: 关系列表

    """

    

    def __init__(self):

        self.concepts: Dict[str, Concept] = {}

        self.relations: List[ConceptRelation] = []

        

        # 关系类型索引

        self.relation_index: Dict[str, List[int]] = defaultdict(list)

        

        # 概念邻居索引

        self.neighbor_index: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)

        

        # ConceptNet常见关系类型

        self.RELATION_TYPES = {

            "IsA": "isa",           # 上位词

            "PartOf": "partof",     # 部分

            "HasA": "hasa",         # 拥有属性

            "UsedFor": "usedfor",   # 用途

            "CapableOf": "capable", # 能做

            "AtLocation": "atlocation",  # 位于

            "SimilarTo": "similar", # 相似

            "Antonym": "antonym",   # 反义

            "DerivedFrom": "derived", # 派生

            "RelatedTo": "related", # 相关

            "Causes": "causes",      # 导致

            "Desires": "desires",   # 期望

        }

    

    def add_concept(self, concept_name: str, lang: str = "en") -> Concept:

        """添加概念"""

        if concept_name not in self.concepts:

            self.concepts[concept_name] = Concept(concept_name, lang)

        return self.concepts[concept_name]

    

    def add_relation(self, start_name: str, relation_type: str,

                   end_name: str, weight: float = 1.0):

        """添加关系"""

        start = self.add_concept(start_name)

        end = self.add_concept(end_name)

        

        relation = ConceptRelation(start, relation_type, end, weight)

        self.relations.append(relation)

        

        self.relation_index[relation_type].append(len(self.relations) - 1)

        self.neighbor_index[start_name].append((relation_type, end_name, weight))

        self.neighbor_index[end_name].append((relation_type, start_name, weight))

    

    def get_relations(self, concept_name: str) -> List[Tuple[str, str, float]]:

        """获取概念的所有关系"""

        return self.neighbor_index.get(concept_name, [])

    

    def find_path(self, start: str, end: str, max_depth: int = 3) -> List[List[str]]:

        """查找两概念间的路径"""

        if start not in self.concepts or end not in self.concepts:

            return []

        

        queue = deque([(start, [start])])

        visited = {start}

        paths = []

        

        while queue:

            current, path = queue.popleft()

            

            if current == end:

                paths.append(path)

                continue

            

            if len(path) >= max_depth:

                continue

            

            for rel_type, neighbor, weight in self.neighbor_index.get(current, []):

                if neighbor not in visited:

                    visited.add(neighbor)

                    queue.append((neighbor, path + [neighbor]))

        

        return paths

    

    def get_related_concepts(self, concept: str, 

                            relation_type: Optional[str] = None,

                            top_k: int = 10) -> List[Tuple[str, float]]:

        """获取相关概念"""

        neighbors = self.neighbor_index.get(concept, [])

        

        if relation_type:

            filtered = [(n, w) for rt, n, w in neighbors if rt == relation_type]

            neighbors = filtered

        

        # 按权重排序

        neighbors.sort(key=lambda x: x[1], reverse=True)

        

        return neighbors[:top_k]





class CommonsenseReasoner:

    """

    常识推理器

    

    参数:

        conceptnet: ConceptNet实例

    """

    

    def __init__(self, conceptnet: ConceptNet):

        self.conceptnet = conceptnet

    

    def is_a_chain(self, concept1: str, concept2: str) -> bool:

        """检查是否是IsA链"""

        paths = self.conceptnet.find_path(concept1, concept2, max_depth=5)

        

        for path in paths:

            # 检查路径上的关系是否都是IsA

            for i in range(len(path) - 1):

                neighbors = self.conceptnet.get_relations(path[i])

                found_isa = False

                for rel, neighbor, _ in neighbors:

                    if neighbor == path[i + 1] and rel in ["IsA", "isa"]:

                        found_isa = True

                        break

                if not found_isa:

                    break

            else:

                return True

        

        return False

    

    def analogy(self, A: str, B: str, C: str) -> List[str]:

        """

        类比推理：A相对于B类似于C相对于?

        

        返回:

            候选答案列表

        """

        # A和B的关系

        A_relations = set(self.conceptnet.get_relations(A))

        

        candidates = []

        

        for rel, D, weight in self.conceptnet.get_relations(C):

            # 检查A和B之间是否有相同关系

            if (rel, D, weight) in A_relations:

                candidates.append(D)

        

        return candidates

    

    def property_transfer(self, source: str, target: str) -> List[Tuple[str, float]]:

        """

        属性迁移

        

        将source的属性迁移到target

        """

        # 获取source的属性

        source_props = []

        for rel, neighbor, weight in self.conceptnet.get_relations(source):

            if rel in ["HasA", "UsedFor", "CapableOf", "AtLocation"]:

                source_props.append((rel, neighbor, weight))

        

        # 检查target是否有相同的属性

        target_props = set(self.conceptnet.get_relations(target))

        

        transferred = []

        for rel, prop, weight in source_props:

            if (rel, prop, weight) not in target_props:

                transferred.append((prop, weight))

        

        transferred.sort(key=lambda x: x[1], reverse=True)

        

        return transferred

    

    def similarity(self, concept1: str, concept2: str) -> float:

        """

        计算两个概念的相似度

        

        使用邻居重叠度

        """

        neighbors1 = set(n for r, n, w in self.conceptnet.get_relations(concept1))

        neighbors2 = set(n for r, n, w in self.conceptnet.get_relations(concept2))

        

        if len(neighbors1) == 0 or len(neighbors2) == 0:

            return 0.0

        

        # Jaccard相似度

        intersection = neighbors1 & neighbors2

        union = neighbors1 | neighbors2

        

        return len(intersection) / len(union) if len(union) > 0 else 0.0

    

    def most_specific_common_concept(self, concept1: str, concept2: str) -> List[str]:

        """

        找最具体的公共概念

        

        例如：狗和金鱼的最具体公共概念可能是"动物"

        """

        # 获取两个概念的祖先路径

        def get_ancestors(concept, visited=None):

            if visited is None:

                visited = set()

            

            if concept in visited:

                return visited

            

            visited.add(concept)

            

            for rel, neighbor, _ in self.conceptnet.get_relations(concept):

                if rel in ["IsA", "isa", "partof"]:

                    get_ancestors(neighbor, visited)

            

            return visited

        

        ancestors1 = get_ancestors(concept1)

        ancestors2 = get_ancestors(concept2)

        

        common = list(ancestors1 & ancestors2)

        

        # 找最深层的公共概念（最简单的）

        return common





class EmbeddingReasoner:

    """基于嵌入的常识推理"""

    

    def __init__(self, n_concepts: int, embedding_dim: int = 100):

        self.n_concepts = n_concepts

        self.dim = embedding_dim

        

        np.random.seed(42)

        

        # 概念嵌入

        self.concept_embeddings = np.random.randn(n_concepts, embedding_dim) * 0.1

        

        # 关系嵌入

        self.relation_embeddings = np.random.randn(20, embedding_dim) * 0.1

    

    def compute_similarity(self, idx1: int, idx2: int) -> float:

        """计算概念相似度"""

        e1 = self.concept_embeddings[idx1]

        e2 = self.concept_embeddings[idx2]

        

        # 余弦相似度

        dot = np.dot(e1, e2)

        norm1 = np.linalg.norm(e1)

        norm2 = np.linalg.norm(e2)

        

        return dot / (norm1 * norm2 + 1e-10)

    

    def relation_score(self, head_idx: int, rel_idx: int, tail_idx: int) -> float:

        """计算关系三元组分数"""

        h = self.concept_embeddings[head_idx]

        r = self.relation_embeddings[rel_idx]

        t = self.concept_embeddings[tail_idx]

        

        # TransE风格

        return -float(np.linalg.norm(h + r - t))

    

    def predict_tail(self, head_idx: int, rel_idx: int,

                    top_k: int = 10) -> List[Tuple[int, float]]:

        """预测尾实体"""

        h = self.concept_embeddings[head_idx]

        r = self.relation_embeddings[rel_idx]

        

        target = h + r

        

        scores = []

        for i in range(self.n_concepts):

            e = self.concept_embeddings[i]

            score = -np.linalg.norm(target - e)

            scores.append((i, float(score)))

        

        scores.sort(key=lambda x: x[1], reverse=True)

        

        return scores[:top_k]





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("常识推理 - ConceptNet测试")

    print("=" * 50)

    

    # 创建ConceptNet

    cn = ConceptNet()

    

    # 添加常识知识

    commonsense_data = [

        ("狗", "IsA", "动物", 1.0),

        ("猫", "IsA", "动物", 1.0),

        ("金鱼", "IsA", "动物", 1.0),

        ("动物", "IsA", "生物", 1.0),

        ("植物", "IsA", "生物", 1.0),

        ("狗", "CapableOf", "奔跑", 0.9),

        ("猫", "CapableOf", "奔跑", 0.9),

        ("鸟", "CapableOf", "飞翔", 0.8),

        ("鱼", "CapableOf", "游泳", 0.9),

        ("狗", "HasA", "四条腿", 1.0),

        ("猫", "HasA", "四条腿", 1.0),

        ("鸟", "HasA", "翅膀", 1.0),

        ("狗", "AtLocation", "家", 0.7),

        ("猫", "AtLocation", "家", 0.7),

        ("鱼", "AtLocation", "水", 1.0),

        ("奔跑", "UsedFor", "移动", 0.8),

        ("飞翔", "UsedFor", "移动", 0.8),

    ]

    

    for start, rel, end, weight in commonsense_data:

        cn.add_relation(start, rel, end, weight)

    

    print(f"\nConceptNet: {len(cn.concepts)} 概念, {len(cn.relations)} 关系")

    

    # 常识推理

    reasoner = CommonsenseReasoner(cn)

    

    # 查找路径

    print("\n--- 路径查找 ---")

    paths = cn.find_path("狗", "生物", max_depth=5)

    print(f"狗到生物的路径: {paths}")

    

    # IsA链检查

    print("\n--- IsA链检查 ---")

    is_chain = reasoner.is_a_chain("狗", "生物")

    print(f"狗是生物的IsA链: {is_chain}")

    

    # 类比推理

    print("\n--- 类比推理 ---")

    analogies = reasoner.analogy("狗", "奔跑", "鸟")

    print(f"狗:奔跑 :: 鸟:? = {analogies}")

    

    # 属性迁移

    print("\n--- 属性迁移 ---")

    transferred = reasoner.property_transfer("狗", "猫")

    print(f"狗到猫的属性迁移: {transferred}")

    

    # 最具体公共概念

    print("\n--- 最具体公共概念 ---")

    common = reasoner.most_specific_common_concept("狗", "金鱼")

    print(f"狗和金鱼的最具体公共概念: {common}")

    

    # 基于嵌入的推理

    print("\n--- 基于嵌入的推理 ---")

    embed_reasoner = EmbeddingReasoner(len(cn.concepts), embedding_dim=50)

    

    sim = embed_reasoner.compute_similarity(0, 1)  # 假设索引

    print(f"概念0和1的相似度: {sim:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


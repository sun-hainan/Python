# -*- coding: utf-8 -*-

"""

算法实现：知识图谱深度 / temporal_kg



本文件实现 temporal_kg 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Set, Optional

from collections import defaultdict





class TemporalKnowledgeGraph:

    """时序知识图谱"""

    

    def __init__(self):

        self.entities: Set[str] = set()

        self.relations: Set[str] = set()

        self.triples: List[Tuple[str, str, str, str]] = []  # (h, r, t, start_time, end_time)

        

        # 索引

        self.time_index: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)

        self.entity_time_index: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

        self.head_index: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)

    

    def add_triple(self, head: str, relation: str, tail: str,

                  start_time: str = "0", end_time: str = "+inf"):

        """添加时序三元组"""

        self.entities.add(head)

        self.entities.add(tail)

        self.relations.add(relation)

        

        triple = (head, relation, tail, start_time, end_time)

        self.triples.append(triple)

        

        # 索引

        self.time_index[start_time].append((head, relation, tail))

        self.entity_time_index[head][start_time].append((relation, tail))

        self.head_index[head].append((relation, tail, start_time, end_time))

    

    def get_temporal_neighbors(self, entity: str, 

                               time_range: Tuple[Optional[str], Optional[str]] = (None, None)) -> List[Tuple[str, str, str]]:

        """获取某时间范围内的邻居"""

        neighbors = []

        

        for rel, tail, start, end in self.head_index.get(entity, []):

            # 检查时间范围

            if start is not None and time_range[0] is not None:

                if start > time_range[0]:

                    continue

            if end is not None and time_range[1] is not None:

                if end < time_range[1]:

                    continue

            

            neighbors.append((rel, tail))

        

        return neighbors

    

    def find_temporal_facts(self, head: Optional[str] = None,

                           relation: Optional[str] = None,

                           tail: Optional[str] = None,

                           start_time: Optional[str] = None,

                           end_time: Optional[str] = None) -> List[Tuple]:

        """查询时序事实"""

        results = []

        

        for triple in self.triples:

            h, r, t, s, e = triple

            

            if head is not None and h != head:

                continue

            if relation is not None and r != relation:

                continue

            if tail is not None and t != tail:

                continue

            if start_time is not None and s > start_time:

                continue

            if end_time is not None and e < end_time:

                continue

            

            results.append(triple)

        

        return results





class TemporalEmbedding:

    """时序嵌入模型"""

    

    def __init__(self, n_entities: int, n_relations: int,

                 embedding_dim: int = 100):

        self.n_entities = n_entities

        self.n_relations = n_relations

        self.dim = embedding_dim

        

        np.random.seed(42)

        

        # 实体嵌入

        self.entity_embeddings = np.random.randn(n_entities, embedding_dim) * 0.1

        

        # 关系嵌入

        self.relation_embeddings = np.random.randn(n_relations, embedding_dim) * 0.1

        

        # 时间嵌入

        self.time_embeddings = np.random.randn(1000, embedding_dim) * 0.1  # 假设时间戳数量

    

    def score(self, head_idx: int, relation_idx: int, tail_idx: int,

             time_idx: int) -> float:

        """计算时序三元组分数"""

        h = self.entity_embeddings[head_idx]

        r = self.relation_embeddings[relation_idx]

        t = self.entity_embeddings[tail_idx]

        time_emb = self.time_embeddings[min(time_idx, len(self.time_embeddings) - 1)]

        

        # 时序TransE: h + r + time ≈ t

        score = -np.linalg.norm(h + r + time_emb - t)

        

        return float(score)

    

    def temporal_distance(self, head_idx: int, relation_idx: int, tail_idx: int,

                         time1_idx: int, time2_idx: int) -> float:

        """计算两个时序三元组的时间距离"""

        score1 = self.score(head_idx, relation_idx, tail_idx, time1_idx)

        score2 = self.score(head_idx, relation_idx, tail_idx, time2_idx)

        

        return abs(score1 - score2)





class TemporalReasoning:

    """时序推理"""

    

    def __init__(self, tkg: TemporalKnowledgeGraph):

        self.tkg = tkg

    

    def find_sequence(self, entity: str, relation: str,

                     start_time: str, end_time: str) -> List[Tuple[str, str]]:

        """

        查找实体的时序关系链

        

        返回:

            [(时间, 实体), ...]

        """

        facts = self.tkg.find_temporal_facts(head=entity, relation=relation)

        

        # 过滤时间范围

        sequence = []

        for h, r, t, s, e in facts:

            if s >= start_time and e <= end_time:

                sequence.append((s, t))

        

        # 按时间排序

        sequence.sort(key=lambda x: x[0])

        

        return sequence

    

    def evolve_between(self, entity1: str, entity2: str) -> List[Tuple[str, str, str]]:

        """

        查找两实体间的演化路径

        

        返回:

            [(关系, 中间实体, 时间), ...]

        """

        # BFS查找

        from collections import deque

        

        queue = deque([(entity1, [], None)])

        visited = {entity1}

        

        while queue:

            current, path, last_time = queue.popleft()

            

            if current == entity2:

                return path

            

            for rel, neighbor, start, end in self.tkg.head_index.get(current, []):

                if neighbor not in visited:

                    visited.add(neighbor)

                    new_path = path + [(rel, neighbor, start)]

                    queue.append((neighbor, new_path, end))

        

        return []

    

    def temporal_patterns(self, entity: str) -> Dict[str, List[Tuple[str, str]]]:

        """

        分析实体的时序模式

        

        返回:

            关系 -> [(时间, 尾实体)] 映射

        """

        patterns = defaultdict(list)

        

        facts = self.tkg.find_temporal_facts(head=entity)

        

        for h, r, t, s, e in facts:

            patterns[r].append((s, t))

        

        # 排序

        for rel in patterns:

            patterns[rel].sort(key=lambda x: x[0])

        

        return dict(patterns)





class TKGCompleter:

    """时序知识图谱补全"""

    

    def __init__(self, tkg: TemporalKnowledgeGraph):

        self.tkg = tkg

    

    def predict_next(self, entity: str, relation: str,

                    current_time: str) -> List[Tuple[str, float]]:

        """

        预测下一个尾实体

        

        返回:

            [(尾实体, 分数), ...]

        """

        neighbors = self.tkg.get_temporal_neighbors(entity)

        

        candidates = []

        for rel, tail in neighbors:

            if rel == relation:

                # 找到该关系的历史

                facts = self.tkg.find_temporal_facts(head=entity, relation=relation, tail=tail)

                

                if facts:

                    # 使用最后一个已知时间来推断

                    last_time = max(s for h, r, t, s, e in facts if s <= current_time)

                    candidates.append((tail, float(last_time)))

        

        candidates.sort(key=lambda x: x[1], reverse=True)

        

        return candidates

    

    def fill_gaps(self, entity: str, relation: str,

                 start_time: str, end_time: str) -> List[str]:

        """

        填补时序间隙

        

        返回:

            估计的尾实体列表

        """

        # 获取已知的时间序列

        sequence = self.tkg.find_temporal_facts(head=entity, relation=relation)

        sequence = [(s, t) for h, r, t, s, e in sequence if s >= start_time and e <= end_time]

        sequence.sort()

        

        if len(sequence) < 2:

            return []

        

        # 分析模式

        # 简化：假设相同的尾实体会重复出现

        tail_counts = defaultdict(int)

        for s, t in sequence:

            tail_counts[t] += 1

        

        # 返回最常见的尾实体

        sorted_tails = sorted(tail_counts.items(), key=lambda x: x[1], reverse=True)

        

        return [t for t, c in sorted_tails]





def temporal_accuracy(predicted_time: str, actual_time: str) -> float:

    """

    计算时序预测准确度

    """

    try:

        pred = float(predicted_time)

        actual = float(actual_time)

        

        error = abs(pred - actual)

        

        if error <= 1:

            return 1.0

        elif error <= 10:

            return 0.8

        elif error <= 100:

            return 0.5

        else:

            return 0.0

    except:

        return 0.0





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("时序知识图谱测试")

    print("=" * 50)

    

    # 创建时序知识图谱

    tkg = TemporalKnowledgeGraph()

    

    # 添加时序三元组

    timeline_data = [

        ("Alice", "worked_at", "Google", "2010", "2015"),

        ("Alice", "worked_at", "Microsoft", "2015", "2020"),

        ("Alice", "worked_at", "Apple", "2020", "2023"),

        ("Bob", "worked_at", "Google", "2012", "2018"),

        ("Charlie", "worked_at", "Microsoft", "2018", "2023"),

    ]

    

    for h, r, t, s, e in timeline_data:

        tkg.add_triple(h, r, t, s, e)

    

    print(f"\n时序KG: {len(tkg.entities)} 实体, {len(tkg.relations)} 关系, {len(tkg.triples)} 时序三元组")

    

    # 时序查询

    print("\n--- 时序查询 ---")

    

    # 查询某时间范围的邻居

    neighbors = tkg.get_temporal_neighbors("Alice", ("2014", "2016"))

    print(f"Alice在2014-2016年的邻居: {neighbors}")

    

    # 查询特定事实

    facts = tkg.find_temporal_facts(head="Alice", relation="worked_at")

    print(f"\nAlice的work经历:")

    for h, r, t, s, e in facts:

        print(f"  {h} --[{r}]--> {t}, 时间: {s} - {e}")

    

    # 时序推理

    print("\n--- 时序推理 ---")

    reasoning = TemporalReasoning(tkg)

    

    # 序列查找

    sequence = reasoning.find_sequence("Alice", "worked_at", "2010", "2025")

    print(f"Alice的work序列: {sequence}")

    

    # 时序模式

    patterns = reasoning.temporal_patterns("Alice")

    print(f"\nAlice的时序模式:")

    for rel, seq in patterns.items():

        print(f"  {rel}: {seq}")

    

    # 预测下一个

    print("\n--- 时序预测 ---")

    completer = TKGCompleter(tkg)

    

    next_entities = completer.predict_next("Alice", "worked_at", "2023")

    print(f"预测Alice在2023年后的work: {next_entities}")

    

    # 时序嵌入测试

    print("\n--- 时序嵌入 ---")

    n_entities = len(tkg.entities)

    n_relations = len(tkg.relations)

    

    embed_model = TemporalEmbedding(n_entities, n_relations, embedding_dim=50)

    

    # 计算分数

    score = embed_model.score(0, 0, 1, 50)

    print(f"时序三元组分数: {score:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")


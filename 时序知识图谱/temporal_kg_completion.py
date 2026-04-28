"""
时序知识图谱补全 (Temporal KG Completion)
=========================================
实现时序知识图谱补全方法，包括基于路径和基于嵌入的方法。

任务：给定(s, p, ?, t)或(?, p, o, t)，预测缺失实体或关系。

方法：
1. 基于路径的方法：挖掘时序路径模式
2. 基于嵌入的方法：使用TComplEx等模型
3. 混合方法：结合路径和嵌入

参考：
    - Dasgupta, S.S. et al. (2018). HyTE: Hyperplane-based Temporally aware KG.
    - Jiang, T. et al. (2016). Temporal Knowledge Base Completion.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import random


class TemporalPath:
    """时序路径"""
    def __init__(self, relations: List[str], times: List[int]):
        self.relations = relations
        self.times = times
    
    def __str__(self):
        parts = []
        for r, t in zip(self.relations, self.times):
            parts.append(f"{r}@{t}")
        return " -> ".join(parts)


class TKGCompletion:
    """
    时序知识图谱补全器
    
    参数:
        kg: 时序知识图谱
        method: 补全方法 ("path", "embedding", "hybrid")
    """
    
    def __init__(self, kg, method: str = "hybrid"):
        self.kg = kg
        self.method = method
        
        # 路径索引
        self.path_patterns = defaultdict(int)
        self.path_votes = defaultdict(lambda: defaultdict(int))
    
    def mine_temporal_paths(self, max_length: int = 3, min_support: int = 2):
        """
        挖掘时序路径模式
        
        参数:
            max_length: 最大路径长度
            min_support: 最小支持度
        """
        # 对每个实体作为起点
        for entity in self.kg.entities:
            # BFS探索路径
            self._dfs_mine_paths(
                current_entity=entity,
                path_relations=[],
                path_entities=[entity],
                path_times=[],
                max_length=max_length
            )
        
        # 过滤低频模式
        self.path_patterns = {
            k: v for k, v in self.path_patterns.items()
            if v >= min_support
        }
    
    def _dfs_mine_paths(self, current_entity: str, 
                       path_relations: List[str],
                       path_entities: List[str],
                       path_times: List[int],
                       max_length: int):
        """DFS挖掘路径"""
        if len(path_relations) >= max_length:
            return
        
        # 获取当前实体的历史
        history = self.kg.get_temporal_neighbors(current_entity)
        
        for neighbor, relation, time in history:
            if neighbor not in path_entities:  # 避免循环
                # 添加到路径
                new_relations = path_relations + [relation]
                new_entities = path_entities + [neighbor]
                new_times = path_times + [time]
                
                # 记录路径模式
                key = tuple(new_relations)
                self.path_patterns[key] += 1
                
                # 递归
                self._dfs_mine_paths(
                    neighbor, new_relations, new_entities, new_times, max_length
                )
    
    def predict_by_path(self, s: str, p: str, t: int, 
                       top_k: int = 5) -> List[Tuple[str, float]]:
        """
        基于路径预测尾实体
        
        参数:
            s: 主语
            p: 目标关系
            t: 时间
            top_k: 返回前k个
        
        返回:
            [(实体, 得分), ...]
        """
        scores = defaultdict(float)
        
        # 获取s在t之前的历史
        history = self.kg.get_temporal_neighbors(s, t)
        
        # 探索两步路径: s -r1-> x -p-> ?
        for r1, x, t1 in history:
            if t1 >= t:
                continue
            
            # 从x出发的路径
            x_history = self.kg.get_temporal_neighbors(x, t)
            for r2, y, t2 in x_history:
                if t2 <= t and r2 == p:
                    # 找到 s -r1-> x -p-> y
                    pattern = (r1, p)
                    pattern_key = str(pattern)
                    
                    # 投票
                    self.path_votes[pattern][y] += 1
        
        # 排序
        result = [(y, count) for y, count in self.path_votes.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result[:top_k]
    
    def predict_by_embedding(self, s: str, p: str, t: int,
                            top_k: int = 5) -> List[Tuple[str, float]]:
        """
        基于嵌入预测（简化版本）
        
        参数:
            s: 主语
            p: 关系
            t: 时间
            top_k: 返回前k个
        
        返回:
            [(实体, 得分), ...]
        """
        # 简化实现：基于共现频率
        cooccurrence = defaultdict(int)
        
        # 获取s的历史
        s_history = self.kg.get_temporal_neighbors(s, t)
        
        for r1, neighbor, t1 in s_history:
            if t1 < t:
                # 获取neighbor的历史
                n_history = self.kg.get_temporal_neighbors(neighbor, t)
                for r2, y, t2 in n_history:
                    if t2 <= t and r2 == p:
                        cooccurrence[y] += 1
        
        # 添加基于时间接近度的分数
        for r1, neighbor, t1 in s_history:
            if t1 < t:
                # 与s在t1时刻直接相连的实体
                pass
        
        result = [(y, score) for y, score in cooccurrence.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result[:top_k]
    
    def predict_hybrid(self, s: str, p: str, t: int,
                      top_k: int = 5) -> List[Tuple[str, float]]:
        """
        混合预测（路径+嵌入）
        
        参数:
            s: 主语
            p: 关系
            t: 时间
            top_k: 返回前k个
        
        返回:
            [(实体, 得分), ...]
        """
        path_scores = dict(self.predict_by_path(s, p, t, top_k * 2))
        embed_scores = dict(self.predict_by_embedding(s, p, t, top_k * 2))
        
        # 归一化
        all_entities = set(path_scores.keys()) | set(embed_scores.keys())
        
        max_path = max(path_scores.values()) if path_scores else 1
        max_embed = max(embed_scores.values()) if embed_scores else 1
        
        hybrid_scores = []
        for entity in all_entities:
            path_score = path_scores.get(entity, 0) / max_path
            embed_score = embed_scores.get(entity, 0) / max_embed
            hybrid = 0.5 * path_score + 0.5 * embed_score
            hybrid_scores.append((entity, hybrid))
        
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores[:top_k]


class TKGPathRanking:
    """
    时序路径排序模型
    
    参数:
        kg: 时序知识图谱
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.path_scores = {}
    
    def extract_paths(self, s: str, o: str, max_length: int = 2) -> List[TemporalPath]:
        """
        提取s和o之间的时序路径
        
        参数:
            s: 起点
            o: 终点
            max_length: 最大路径长度
        
        返回:
            时序路径列表
        """
        paths = []
        
        # BFS
        queue = [(s, [], [])]
        
        while queue:
            current, relations, times = queue.pop(0)
            
            if len(relations) > max_length:
                continue
            
            if current == o and relations:
                paths.append(TemporalPath(relations, times))
                continue
            
            # 获取邻居
            neighbors = self.kg.get_temporal_neighbors(current)
            
            for neighbor, relation, time in neighbors:
                if neighbor not in [s] or len(relations) > 0:
                    new_relations = relations + [relation]
                    new_times = times + [time]
                    queue.append((neighbor, new_relations, new_times))
        
        return paths
    
    def compute_path_features(self, s: str, o: str) -> Dict[str, float]:
        """
        计算路径特征
        
        参数:
            s: 主语
            o: 宾语
        
        返回:
            特征字典
        """
        paths = self.extract_paths(s, o)
        
        features = {
            "num_paths": len(paths),
            "avg_length": sum(len(p.relations) for p in paths) / max(len(paths), 1),
            "min_length": min((len(p.relations) for p in paths), default=0),
            "max_length": max((len(p.relations) for p in paths), default=0),
        }
        
        # 关系类型特征
        relation_counts = defaultdict(int)
        for path in paths:
            for r in path.relations:
                relation_counts[r] += 1
        features["relation_diversity"] = len(relation_counts)
        
        return features
    
    def predict_link(self, s: str, p: str, o: str, t: int) -> float:
        """
        预测链接存在概率
        
        参数:
            s: 主语
            p: 谓词
            o: 宾语
            t: 时间
        
        返回:
            概率分数
        """
        # 提取相关路径
        paths = self.extract_paths(s, o, max_length=2)
        
        # 筛选与目标关系相关的路径
        relevant_paths = [p for p in paths if p.relations[-1] == p]
        
        if not relevant_paths:
            return 0.0
        
        # 简单打分
        score = len(relevant_paths) / max(len(paths), 1)
        
        return score


def temporal_kgc_train_test_split(kg, test_ratio: float = 0.2,
                                 seed: int = 42) -> Tuple[List, List]:
    """
    时序KG补全数据集划分
    
    参数:
        kg: 时序知识图谱
        test_ratio: 测试集比例
        seed: 随机种子
    
    返回:
        (训练集, 测试集)
    """
    random.seed(seed)
    
    triples = list(kg.triples.keys())
    random.shuffle(triples)
    
    split_idx = int(len(triples) * (1 - test_ratio))
    
    train = triples[:split_idx]
    test = triples[split_idx:]
    
    return train, test


def evaluate_tkg_completion(completion: TKGCompletion, 
                           test_triples: List[Tuple],
                           task: str = "tail") -> Dict[str, float]:
    """
    评估时序KG补全性能
    
    参数:
        completion: 补全器
        test_triples: 测试三元组
        task: "tail" 或 "head"
    
    返回:
        评估指标
    """
    ranks = []
    
    for triple in test_triples:
        if len(triple) == 4:
            s, p, o, t = triple
        else:
            continue
        
        if task == "tail":
            predictions = completion.predict_hybrid(s, p, t, top_k=50)
            # 找真实o的位置
            for i, (pred_o, _) in enumerate(predictions):
                if pred_o == o:
                    ranks.append(i + 1)
                    break
            else:
                ranks.append(len(predictions) + 1)
    
    if not ranks:
        return {}
    
    # 计算指标
    mrr = sum(1 / r for r in ranks) / len(ranks)
    hit10 = sum(1 for r in ranks if r <= 10) / len(ranks)
    hit1 = sum(1 for r in ranks if r <= 1) / len(ranks)
    
    return {
        "MRR": mrr,
        "Hit@10": hit10,
        "Hit@1": hit1
    }


if __name__ == "__main__":
    print("=== 时序知识图谱补全测试 ===")
    
    from temporal_knowledge_graph import TemporalKG
    
    # 构建测试TKG
    kg = TemporalKG()
    
    facts = [
        ("Alice", "works_at", "CompanyA", 2018),
        ("CompanyA", "located_in", "Paris", 2018),
        ("Alice", "works_at", "CompanyB", 2021),
        ("CompanyB", "located_in", "London", 2021),
        ("Bob", "works_at", "CompanyA", 2019),
        ("Bob", "married_to", "Alice", 2020),
        ("Alice", "lives_in", "Paris", 2018),
        ("Alice", "moved_to", "London", 2021),
    ]
    
    for s, p, o, t in facts:
        kg.add_triple(s, p, o, t)
    
    print(f"TKG: {len(kg.triples)} 条事实")
    
    # 创建补全器
    completion = TKGCompletion(kg, method="hybrid")
    completion.mine_temporal_paths(max_length=3, min_support=1)
    
    print(f"\n挖掘到 {len(completion.path_patterns)} 种路径模式")
    
    # 预测
    print("\n预测 Alice 在 2021 年 works_at 哪里:")
    predictions = completion.predict_hybrid("Alice", "works_at", 2021, top_k=5)
    for entity, score in predictions:
        print(f"  {entity}: {score:.4f}")
    
    # 路径排序
    print("\n路径排序测试:")
    pr = TKGPathRanking(kg)
    
    features = pr.compute_path_features("Alice", "Paris")
    print(f"  Alice -> Paris 的路径特征: {features}")
    
    features2 = pr.compute_path_features("Alice", "London")
    print(f"  Alice -> London 的路径特征: {features2}")
    
    # 评估
    print("\n\n评估性能:")
    test_data = [
        ("Alice", "works_at", "CompanyB", 2021),
        ("Bob", "works_at", "CompanyA", 2019),
    ]
    
    metrics = evaluate_tkg_completion(completion, test_data)
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n=== 测试完成 ===")

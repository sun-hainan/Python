# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / path_ranking

本文件实现 path_ranking 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict
from scipy.sparse import csr_matrix, lil_matrix


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        self.triples: List[Tuple[str, str, str]] = []
        
        # 邻接表：head -> (relation, tail)
        self.triple_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        # 反向：tail -> (relation, head)
        self.reverse_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    def add_triple(self, head: str, relation: str, tail: str):
        """添加三元组"""
        self.entities.add(head)
        self.entities.add(tail)
        self.relations.add(relation)
        
        self.triples.append((head, relation, tail))
        self.triple_index[head].append((relation, tail))
        self.reverse_index[tail].append((relation, head))
    
    def get_neighbors(self, entity: str, relation: Optional[str] = None) -> List[Tuple[str, str]]:
        """获取实体的邻居"""
        if relation:
            return [(rel, tail) for rel, tail in self.triple_index[entity] if rel == relation]
        return self.triple_index[entity]
    
    def get_path(self, start: str, relation: str, end: str, max_depth: int = 3) -> List[List[str]]:
        """
        查找从start到end的指定关系路径
        
        返回:
            路径列表，每条路径是关系序列
        """
        paths = []
        
        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current == target and len(path) > 0:
                paths.append(path.copy())
                return
            
            for rel, neighbor in self.triple_index[current]:
                if rel == relation or relation is None:
                    path.append(rel)
                    dfs(neighbor, target, path, depth + 1)
                    path.pop()
        
        dfs(start, end, [], 0)
        return paths


class PathRankingAlgorithm:
    """
    路径排序算法
    
    参数:
        kg: 知识图谱
        max_path_length: 最大路径长度
    """
    
    def __init__(self, kg: KnowledgeGraph, max_path_length: int = 3):
        self.kg = kg
        self.max_path_length = max_path_length
        
        # 路径类型权重
        self.path_weights: Dict[str, float] = {}
        
        # 特征矩阵
        self.features: Dict[Tuple[str, str], List[float]] = {}
    
    def extract_path_features(self, head: str, tail: str) -> List[float]:
        """
        提取从头到尾的路径特征
        
        参数:
            head: 头实体
            tail: 尾实体
        
        返回:
            路径特征向量
        """
        features = []
        
        # 收集所有从head到tail的路径
        paths = self._find_all_paths(head, tail, self.max_path_length)
        
        # 统计每种关系类型的路径数
        path_type_counts = defaultdict(int)
        for path in paths:
            path_type = tuple(path)
            path_type_counts[path_type] += 1
        
        # 返回特征
        all_path_types = list(set(tuple(p) for p in paths))
        for path_type in all_path_types:
            features.append(path_type_counts.get(path_type, 0))
        
        return features if features else [0] * 10
    
    def _find_all_paths(self, start: str, end: str, max_depth: int) -> List[List[str]]:
        """BFS查找所有路径"""
        paths = []
        queue = [(start, [])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current == end and len(path) > 0:
                paths.append(path)
                continue
            
            for relation, neighbor in self.kg.triple_index[current]:
                queue.append((neighbor, path + [relation]))
        
        return paths
    
    def _build_feature_matrix(self, relation_to_predict: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建训练特征矩阵
        
        参数:
            relation_to_predict: 要预测的关系
        
        返回:
            (特征矩阵, 标签向量)
        """
        # 收集正例（该关系存在的三元组）
        positive_examples = []
        for head, rel, tail in self.kg.triples:
            if rel == relation_to_predict:
                positive_examples.append((head, tail))
        
        if len(positive_examples) == 0:
            return np.array([]), np.array([])
        
        # 收集负例（随机选择的非正例）
        negative_examples = []
        all_entities = list(self.kg.entities)
        
        while len(negative_examples) < len(positive_examples):
            head, tail = np.random.choice(all_entities, 2, replace=False)
            if (head, tail) not in positive_examples:
                negative_examples.append((head, tail))
        
        # 构建特征
        all_examples = positive_examples + negative_examples
        labels = np.array([1] * len(positive_examples) + [0] * len(negative_examples))
        
        # 提取特征
        features_list = []
        for head, tail in all_examples:
            features_list.append(self.extract_path_features(head, tail))
        
        # 填充到相同长度
        max_features = max(len(f) for f in features_list) if features_list else 10
        for i in range(len(features_list)):
            while len(features_list[i]) < max_features:
                features_list[i].append(0)
        
        features_matrix = np.array(features_list)
        
        return features_matrix, labels
    
    def train(self, relation: str):
        """
        训练路径权重
        
        参数:
            relation: 要预测的关系
        """
        X, y = self._build_feature_matrix(relation)
        
        if len(X) == 0:
            print(f"没有训练数据 for relation: {relation}")
            return
        
        # 使用逻辑回归（简化版）
        # 实际实现可以使用更复杂的方法
        self._train_logistic_regression(X, y)
    
    def _train_logistic_regression(self, X: np.ndarray, y: np.ndarray, 
                                   learning_rate: float = 0.1,
                                   n_iterations: int = 100):
        """简化版逻辑回归训练"""
        n_features = X.shape[1]
        
        # 初始化权重
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        
        # 归一化特征
        X_norm = X / (np.sum(X, axis=1, keepdims=True) + 1e-10)
        
        # 梯度下降
        for _ in range(n_iterations):
            # 前向传播
            z = X_norm @ self.weights + self.bias
            predictions = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
            
            # 梯度
            error = y - predictions
            dw = X_norm.T @ error / len(y)
            db = np.mean(error)
            
            # 更新
            self.weights += learning_rate * dw
            self.bias += learning_rate * db
    
    def predict(self, head: str, tail: str) -> float:
        """
        预测两个实体间存在关系的概率
        
        参数:
            head: 头实体
            tail: 尾实体
        
        返回:
            概率值 [0, 1]
        """
        if not hasattr(self, 'weights'):
            return 0.0
        
        features = self.extract_path_features(head, tail)
        
        # 归一化
        features = np.array(features) / (np.sum(features) + 1e-10)
        
        # 预测
        z = features @ self.weights + self.bias
        prob = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
        
        return float(prob)


class PRAWithRelationTypes:
    """
    带关系类型的PRA扩展
    """
    
    def __init__(self, kg: KnowledgeGraph, max_path_length: int = 3):
        self.kg = kg
        self.max_path_length = max_path_length
        
        # 路径类型到索引的映射
        self.path_type_to_idx: Dict[Tuple[str, ...], int] = {}
        
        # 训练好的模型
        self.models: Dict[str, Tuple[np.ndarray, float]] = {}
    
    def build_path_vocabulary(self, max_paths: int = 1000):
        """构建路径类型词汇表"""
        path_types = set()
        
        # 收集所有路径类型
        for head, rel, tail in self.kg.triples:
            paths = self._collect_paths(head, tail, self.max_path_length)
            for path in paths:
                path_types.add(tuple(path))
        
        # 限制词汇表大小
        path_types = list(path_types)[:max_paths]
        
        # 创建映射
        for i, path_type in enumerate(path_types):
            self.path_type_to_idx[path_type] = i
    
    def _collect_paths(self, start: str, end: str, max_depth: int) -> List[Tuple[str, ...]]:
        """收集路径"""
        paths = []
        
        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current == end and len(path) > 0:
                paths.append(tuple(path))
                return
            
            for rel, neighbor in self.kg.triple_index[current]:
                path.append(rel)
                dfs(neighbor, path, depth + 1)
                path.pop()
        
        dfs(start, [], 0)
        return paths
    
    def get_path_features(self, head: str, tail: str) -> np.ndarray:
        """获取路径特征向量"""
        n_paths = len(self.path_type_to_idx)
        features = np.zeros(n_paths)
        
        paths = self._collect_paths(head, tail, self.max_path_length)
        
        for path in paths:
            if path in self.path_type_to_idx:
                features[self.path_type_to_idx[path]] += 1
        
        return features


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("路径排序算法 (PRA) 测试")
    print("=" * 50)
    
    # 创建知识图谱
    kg = KnowledgeGraph()
    
    # 添加三元组
    triples = [
        ("John", "study_at", "MIT"),
        ("John", "live_in", "Boston"),
        ("MIT", "located_in", "Massachusetts"),
        ("Massachusetts", "located_in", "USA"),
        ("Bob", "study_at", "Harvard"),
        ("Bob", "live_in", "Boston"),
        ("Harvard", "located_in", "Massachusetts"),
        ("Alice", "work_at", "Google"),
        ("Alice", "live_in", "California"),
        ("Google", "located_in", "California"),
        ("California", "located_in", "USA"),
    ]
    
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    
    print(f"图谱: {len(kg.entities)} 个实体, {len(kg.relations)} 个关系, {len(kg.triples)} 条边")
    
    # PRA模型
    pra = PathRankingAlgorithm(kg, max_path_length=3)
    
    # 训练
    print("\n--- 训练PRA模型 ---")
    pra.train("live_in")
    print("训练完成")
    
    # 预测
    print("\n--- 预测 ---")
    test_cases = [
        ("John", "Boston"),
        ("Bob", "California"),
        ("Alice", "USA")
    ]
    
    for head, tail in test_cases:
        prob = pra.predict(head, tail)
        features = pra.extract_path_features(head, tail)
        print(f"({head}, ?, {tail}): 概率={prob:.4f}, 特征长度={len(features)}")
    
    # 带关系类型的PRA
    print("\n--- 带关系类型的PRA ---")
    pra_typed = PRAWithRelationTypes(kg, max_path_length=3)
    pra_typed.build_path_vocabulary(max_paths=100)
    print(f"路径词汇表大小: {len(pra_typed.path_type_to_idx)}")
    
    features = pra_typed.get_path_features("John", "USA")
    print(f"John -> USA 的路径特征: 非零元素={np.sum(features > 0)}")
    
    print("\n" + "=" * 50)
    print("测试完成")

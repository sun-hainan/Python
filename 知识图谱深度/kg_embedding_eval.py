# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / kg_embedding_eval

本文件实现 kg_embedding_eval 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict


def mean_reciprocal_rank(predictions: List[List[int]], ground_truth: List[int]) -> float:
    """
    计算MRR
    
    参数:
        predictions: 预测列表，每个元素是按排名排序的候选列表
        ground_truth: 真实答案列表
    
    返回:
        MRR分数
    """
    reciprocal_ranks = []
    
    for pred, truth in zip(predictions, ground_truth):
        for rank, candidate in enumerate(pred, 1):
            if candidate == truth:
                reciprocal_ranks.append(1.0 / rank)
                break
        else:
            reciprocal_ranks.append(0.0)
    
    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0


def hits_at_k(predictions: List[List[int]], ground_truth: List[int], k: int) -> float:
    """
    计算Hits@K
    
    参数:
        predictions: 预测列表
        ground_truth: 真实答案
        k: K值
    
    返回:
        Hits@K分数
    """
    hits = 0
    
    for pred, truth in zip(predictions, ground_truth):
        if truth in pred[:k]:
            hits += 1
    
    return hits / len(ground_truth) if ground_truth else 0.0


def mean_rank(predictions: List[List[int]], ground_truth: List[int]) -> float:
    """
    计算MR
    
    参数:
        predictions: 预测列表
        ground_truth: 真实答案
    
    返回:
        MR分数
    """
    ranks = []
    
    for pred, truth in enumerate(predictions, ground_truth):
        for rank, candidate in enumerate(pred, 1):
            if candidate == truth:
                ranks.append(rank)
                break
        else:
            ranks.append(len(pred) + 1)  # 如果未找到，排名为最后
    
    return np.mean(ranks) if ranks else 0.0


def precision_at_k(predictions: List[List[int]], ground_truth: List[int], k: int) -> float:
    """
    计算Precision@K
    
    参数:
        predictions: 预测列表
        ground_truth: 真实答案列表（可能包含多个）
        k: K值
    
    返回:
        Precision@K分数
    """
    precisions = []
    
    for pred, truth in zip(predictions, ground_truth):
        if isinstance(truth, list):
            hits = len(set(pred[:k]) & set(truth))
            precision = hits / k
        else:
            precision = 1.0 if truth in pred[:k] else 0.0
        
        precisions.append(precision)
    
    return np.mean(precisions) if precisions else 0.0


class LinkPredictionEvaluator:
    """
    链接预测评估器
    
    参数:
        model: 嵌入模型（有predict_tail方法）
        kg: 知识图谱
    """
    
    def __init__(self, model, kg):
        self.model = model
        self.kg = kg
    
    def evaluate_link_prediction(self, test_triples: List[Tuple[int, int, int]],
                               filtered: bool = True) -> Dict[str, float]:
        """
        评估链接预测
        
        参数:
            test_triples: 测试三元组列表
            filtered: 是否使用过滤评估（排除已存在的三元组）
        
        返回:
            评估指标字典
        """
        predictions = []
        ground_truth = []
        
        for h, r, t in test_triples:
            # 预测尾实体
            pred_tails = self.model.predict_tail(h, r, top_k=self.model.n_entities)
            
            if filtered:
                # 过滤已存在的三元组
                filtered_tails = []
                existing = set()
                
                for triple in self.kg.triples:
                    existing.add((triple[0], triple[1], triple[2]))
                
                for tail_idx, score in pred_tails:
                    if (h, r, tail_idx) not in existing:
                        filtered_tails.append(tail_idx)
                    if len(filtered_tails) >= len(pred_tails):
                        break
                
                pred_tails_filtered = filtered_tails if filtered_tails else [t for t, _ in pred_tails]
            else:
                pred_tails_filtered = [t for t, _ in pred_tails]
            
            predictions.append(pred_tails_filtered)
            ground_truth.append(t)
        
        return {
            'MRR': mean_reciprocal_rank(predictions, ground_truth),
            'MR': mean_rank(predictions, ground_truth),
            'Hits@1': hits_at_k(predictions, ground_truth, k=1),
            'Hits@3': hits_at_k(predictions, ground_truth, k=3),
            'Hits@10': hits_at_k(predictions, ground_truth, k=10),
            'P@1': precision_at_k(predictions, ground_truth, k=1),
            'P@5': precision_at_k(predictions, ground_truth, k=5),
        }


class TripleClassificationEvaluator:
    """
    三元组分类评估器
    
    评估三元组是否有效（正例/负例）
    """
    
    def __init__(self, model):
        self.model = model
    
    def evaluate_classification(self, 
                               positive_triples: List[Tuple[int, int, int]],
                               negative_triples: List[Tuple[int, int, int]],
                               threshold: Optional[float] = None) -> Dict[str, float]:
        """
        评估三元组分类
        
        返回:
            准确率、精确率、召回率、F1
        """
        # 计算所有三元组的分数
        pos_scores = []
        for h, r, t in positive_triples:
            score = self.model.score(h, r, t)
            pos_scores.append(score)
        
        neg_scores = []
        for h, r, t in negative_triples:
            score = self.model.score(h, r, t)
            neg_scores.append(score)
        
        # 确定阈值
        if threshold is None:
            all_scores = pos_scores + neg_scores
            threshold = np.median(all_scores)
        
        # 分类
        pos_predicted = sum(1 for s in pos_scores if s > threshold)
        neg_predicted = sum(1 for s in neg_scores if s > threshold)
        
        tp = pos_predicted
        fp = neg_predicted
        fn = len(pos_scores) - pos_predicted
        
        accuracy = (tp + (len(neg_scores) - neg_predicted)) / (len(pos_scores) + len(neg_scores))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall + 1e-10)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'threshold': threshold
        }
    
    def find_optimal_threshold(self,
                              positive_triples: List[Tuple[int, int, int]],
                              negative_triples: List[Tuple[int, int, int]]) -> float:
        """
        找到最优分类阈值
        """
        all_scores = []
        labels = []
        
        for h, r, t in positive_triples:
            all_scores.append(self.model.score(h, r, t))
            labels.append(1)
        
        for h, r, t in negative_triples:
            all_scores.append(self.model.score(h, r, t))
            labels.append(0)
        
        all_scores = np.array(all_scores)
        labels = np.array(labels)
        
        best_f1 = 0.0
        best_threshold = 0.0
        
        for threshold in np.linspace(np.min(all_scores), np.max(all_scores), 100):
            predictions = (all_scores > threshold).astype(int)
            
            tp = np.sum((predictions == 1) & (labels == 1))
            fp = np.sum((predictions == 1) & (labels == 0))
            fn = np.sum((predictions == 0) & (labels == 1))
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall + 1e-10)
            
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        return best_threshold


class RankingEvaluator:
    """排名评估器"""
    
    def __init__(self):
        self.results = defaultdict(list)
    
    def add_result(self, metric_name: str, value: float):
        """添加评估结果"""
        self.results[metric_name].append(value)
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """获取汇总统计"""
        summary = {}
        
        for metric, values in self.results.items():
            summary[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values)
            }
        
        return summary


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("知识图谱嵌入评估测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 模拟预测结果
    print("\n--- 模拟评估 ---")
    
    # 模拟预测列表（每个预测是按分数排序的候选列表）
    predictions = [
        [1, 2, 3, 4, 5],
        [2, 1, 3, 4, 5],
        [1, 3, 2, 4, 5],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
    ]
    
    ground_truth = [1, 2, 3, 1, 3]
    
    mrr = mean_reciprocal_rank(predictions, ground_truth)
    mr = mean_rank(predictions, ground_truth)
    hits1 = hits_at_k(predictions, ground_truth, k=1)
    hits3 = hits_at_k(predictions, ground_truth, k=3)
    hits10 = hits_at_k(predictions, ground_truth, k=10)
    
    print(f"MRR: {mrr:.4f}")
    print(f"MR: {mr:.4f}")
    print(f"Hits@1: {hits1:.4f}")
    print(f"Hits@3: {hits3:.4f}")
    print(f"Hits@10: {hits10:.4f}")
    
    # 三元组分类评估
    print("\n--- 三元组分类评估 ---")
    
    # 模拟分数
    pos_scores = np.array([0.9, 0.8, 0.85, 0.7, 0.95])
    neg_scores = np.array([0.2, 0.3, 0.15, 0.4, 0.1])
    
    all_scores = np.concatenate([pos_scores, neg_scores])
    threshold = 0.5
    
    pos_predicted = np.sum(pos_scores > threshold)
    neg_predicted = np.sum(neg_scores > threshold)
    
    tp = pos_predicted
    fp = len(neg_scores) - neg_predicted
    fn = len(pos_scores) - pos_predicted
    tn = neg_predicted
    
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    
    print(f"阈值: {threshold}")
    print(f"准确率: {accuracy:.4f}")
    print(f"精确率: {precision:.4f}")
    print(f"召回率: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    
    # 综合评估
    print("\n--- 综合评估 ---")
    
    evaluator = RankingEvaluator()
    
    for i in range(5):
        evaluator.add_result('MRR', 0.3 + np.random.rand() * 0.5)
        evaluator.add_result('Hits@10', 0.4 + np.random.rand() * 0.4)
        evaluator.add_result('F1', 0.6 + np.random.rand() * 0.3)
    
    summary = evaluator.get_summary()
    
    for metric, stats in summary.items():
        print(f"\n{metric}:")
        for stat_name, stat_value in stats.items():
            print(f"  {stat_name}: {stat_value:.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")

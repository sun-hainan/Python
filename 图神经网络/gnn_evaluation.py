# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gnn_evaluation

本文件实现 gnn_evaluation 相关的算法功能。
"""

import numpy as np


def accuracy(y_true, y_pred):
    """分类准确率"""
    return np.mean(y_true == y_pred)


def precision(y_true, y_pred, average='binary'):
    """精确率"""
    if average == 'binary':
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0
    else:
        # 多分类
        classes = np.unique(y_true)
        precisions = []
        for c in classes:
            tp = np.sum((y_true == c) & (y_pred == c))
            fp = np.sum((y_true != c) & (y_pred == c))
            if tp + fp > 0:
                precisions.append(tp / (tp + fp))
        return np.mean(precisions) if precisions else 0.0


def recall(y_true, y_pred, average='binary'):
    """召回率"""
    if average == 'binary':
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0
    else:
        classes = np.unique(y_true)
        recalls = []
        for c in classes:
            tp = np.sum((y_true == c) & (y_pred == c))
            fn = np.sum((y_true == c) & (y_pred != c))
            if tp + fn > 0:
                recalls.append(tp / (tp + fn))
        return np.mean(recalls) if recalls else 0.0


def f1_score(y_true, y_pred, average='binary'):
    """F1分数"""
    p = precision(y_true, y_pred, average)
    r = recall(y_true, y_pred, average)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def confusion_matrix(y_true, y_pred):
    """混淆矩阵"""
    classes = np.unique(np.concatenate([y_true, y_pred]))
    n = len(classes)
    cm = np.zeros((n, n))
    
    for i, c1 in enumerate(classes):
        for j, c2 in enumerate(classes):
            cm[i, j] = np.sum((y_true == c1) & (y_pred == c2))
    
    return cm, classes


def roc_auc_score(y_true, y_scores):
    """
    ROC AUC分数
    
    参数:
        y_true: 真实标签 (0或1)
        y_scores: 预测分数（概率）
    """
    # 按分数排序
    indices = np.argsort(y_scores)[::-1]
    y_true_sorted = y_true[indices]
    
    # 计算AUC
    n_positive = np.sum(y_true)
    n_negative = len(y_true) - n_positive
    
    if n_positive == 0 or n_negative == 0:
        return 0.0
    
    # 计算曲线下面积
    tpr_accum = 0.0
    fpr_prev = 0.0
    
    for i in range(len(y_scores)):
        if y_true_sorted[i] == 1:
            tpr_accum += 1
        else:
            # 每遇到一个负样本，计算当前TPR和FPR
            pass
    
    # 简化实现
    thresholds = np.linspace(0, 1, 100)
    tprs = []
    fprs = []
    
    for thresh in thresholds:
        y_pred_binary = (y_scores >= thresh).astype(int)
        tp = np.sum((y_true == 1) & (y_pred_binary == 1))
        fp = np.sum((y_true == 0) & (y_pred_binary == 1))
        tn = np.sum((y_true == 0) & (y_pred_binary == 0))
        fn = np.sum((y_true == 1) & (y_pred_binary == 0))
        
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        tprs.append(tpr)
        fprs.append(fpr)
    
    # 计算AUC（梯形法则）
    auc = 0.0
    for i in range(1, len(thresholds)):
        auc += (fprs[i-1] - fprs[i]) * (tprs[i-1] + tprs[i]) / 2
    
    return 1 - auc  # 修正方向


def average_precision(y_true, y_scores):
    """
    平均精确率（AP）
    """
    thresholds = np.linspace(0, 1, 100)
    aps = []
    
    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)
        
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        
        if tp + fp > 0:
            aps.append(tp / (tp + fp))
        else:
            aps.append(0)
    
    return np.mean(aps)


def ranking_metrics(positive_scores, negative_scores):
    """
    边预测的排名指标
    
    参数:
        positive_scores: 正样本（真实边）的预测分数
        negative_scores: 负样本（虚假边）的预测分数
    """
    all_scores = np.concatenate([positive_scores, negative_scores])
    labels = np.concatenate([np.ones(len(positive_scores)), np.zeros(len(negative_scores))])
    
    # AUC
    auc = roc_auc_score(labels, all_scores)
    
    # AP
    ap = average_precision(labels, all_scores)
    
    # MRR (Mean Reciprocal Rank)
    ranks = []
    for i in range(len(positive_scores)):
        pos_score = positive_scores[i]
        rank = 1 + np.sum(negative_scores > pos_score)
        ranks.append(1.0 / rank)
    mrr = np.mean(ranks)
    
    # Hits@K
    hits_at_1 = np.mean(positive_scores > np.percentile(negative_scores, 99))
    hits_at_10 = np.mean(positive_scores > np.percentile(negative_scores, 90))
    
    return {
        'auc': auc,
        'ap': ap,
        'mrr': mrr,
        'hits@1': hits_at_1,
        'hits@10': hits_at_10
    }


class EvaluationMetrics:
    """评估指标计算器"""
    
    def __init__(self, task='classification'):
        self.task = task
        self.reset()
    
    def reset(self):
        """重置缓存"""
        self.y_true = []
        self.y_pred = []
        self.y_scores = []
    
    def update(self, y_true, y_pred=None, y_score=None):
        """添加预测结果"""
        self.y_true.extend(y_true if isinstance(y_true, list) else y_true.tolist())
        if y_pred is not None:
            self.y_pred.extend(y_pred if isinstance(y_pred, list) else y_pred.tolist())
        if y_score is not None:
            self.y_scores.extend(y_score if isinstance(y_score, list) else y_score.tolist())
    
    def compute(self):
        """计算所有指标"""
        y_true = np.array(self.y_true)
        
        results = {}
        
        if self.y_pred:
            y_pred = np.array(self.y_pred)
            results['accuracy'] = accuracy(y_true, y_pred)
            results['precision'] = precision(y_true, y_pred)
            results['recall'] = recall(y_true, y_pred)
            results['f1'] = f1_score(y_true, y_pred)
            
            cm, classes = confusion_matrix(y_true, y_pred)
            results['confusion_matrix'] = cm
            results['classes'] = classes
        
        if self.y_scores:
            y_scores = np.array(self.y_scores)
            results['auc'] = roc_auc_score(y_true, y_scores)
            results['ap'] = average_precision(y_true, y_scores)
        
        return results


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("GNN评估指标测试")
    print("=" * 55)
    
    # 测试分类指标
    print("\n--- 分类指标 ---")
    y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 0, 1, 1, 0, 1, 0])
    
    print(f"真实标签: {y_true}")
    print(f"预测标签: {y_pred}")
    print(f"Accuracy: {accuracy(y_true, y_pred):.4f}")
    print(f"Precision: {precision(y_true, y_pred):.4f}")
    print(f"Recall: {recall(y_true, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_true, y_pred):.4f}")
    
    # 混淆矩阵
    cm, classes = confusion_matrix(y_true, y_pred)
    print(f"\n混淆矩阵:")
    print(f"         Pred0  Pred1")
    for i, c in enumerate(classes):
        print(f"True{c}: {cm[i].astype(int)}")
    
    # 测试ROC AUC
    print("\n--- ROC AUC ---")
    y_true_binary = np.array([0, 0, 0, 1, 1, 1, 1, 0, 0, 1])
    y_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.6, 0.9, 0.4, 0.5, 0.85])
    
    auc = roc_auc_score(y_true_binary, y_scores)
    ap = average_precision(y_true_binary, y_scores)
    
    print(f"真实标签: {y_true_binary}")
    print(f"预测分数: {y_scores.round(2)}")
    print(f"AUC: {auc:.4f}")
    print(f"AP: {ap:.4f}")
    
    # 测试边预测指标
    print("\n--- 边预测排名指标 ---")
    pos_scores = np.array([0.9, 0.8, 0.7, 0.85, 0.75, 0.6, 0.95, 0.7])
    neg_scores = np.array([0.1, 0.2, 0.3, 0.15, 0.25, 0.35, 0.05, 0.4, 0.3, 0.45])
    
    ranks = ranking_metrics(pos_scores, neg_scores)
    
    print(f"正样本分数: {pos_scores.round(2)}")
    print(f"负样本分数: {neg_scores.round(2)}")
    print(f"AUC: {ranks['auc']:.4f}")
    print(f"AP: {ranks['ap']:.4f}")
    print(f"MRR: {ranks['mrr']:.4f}")
    print(f"Hits@1: {ranks['hits@1']:.4f}")
    print(f"Hits@10: {ranks['hits@10']:.4f}")
    
    # 测试EvaluationMetrics类
    print("\n--- EvaluationMetrics类 ---")
    evaluator = EvaluationMetrics()
    
    for i in range(10):
        y_t = np.random.randint(0, 2, 5)
        y_p = np.random.randint(0, 2, 5)
        y_s = np.random.rand(5)
        evaluator.update(y_t, y_p, y_s)
    
    results = evaluator.compute()
    print("聚合结果:")
    for k, v in results.items():
        if k != 'confusion_matrix' and k != 'classes':
            print(f"  {k}: {v:.4f}")
    
    # 多分类测试
    print("\n--- 多分类指标 ---")
    y_true_multi = np.array([0, 1, 2, 2, 1, 0, 2, 0, 1, 2])
    y_pred_multi = np.array([0, 1, 1, 2, 1, 0, 2, 0, 2, 2])
    
    print(f"真实标签: {y_true_multi}")
    print(f"预测标签: {y_pred_multi}")
    print(f"Accuracy: {accuracy(y_true_multi, y_pred_multi):.4f}")
    print(f"Macro Precision: {precision(y_true_multi, y_pred_multi, average='macro'):.4f}")
    print(f"Macro Recall: {recall(y_true_multi, y_pred_multi, average='macro'):.4f}")
    
    # 类别不平衡测试
    print("\n--- 类别不平衡测试 ---")
    y_true_imbalanced = np.array([0]*90 + [1]*10)
    y_pred_random = np.random.randint(0, 2, 100)
    
    print(f"类别分布: 0={90}, 1={10}")
    print(f"随机预测准确率: {accuracy(y_true_imbalanced, y_pred_random):.4f}")
    print(f"随机预测F1: {f1_score(y_true_imbalanced, y_pred_random):.4f}")
    
    print("\n评估指标测试完成！")

# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / loss_functions

本文件实现 loss_functions 相关的算法功能。
"""

import numpy as np


def mean_squared_error(y_pred, y_true):
    """MSE损失"""
    return np.mean((y_pred - y_true) ** 2)


def mean_absolute_error(y_pred, y_true):
    """MAE损失"""
    return np.mean(np.abs(y_pred - y_true))


def huber_loss(y_pred, y_true, delta=1.0):
    """
    Huber损失：结合MSE和MAE的优点
    delta: 切换点
    """
    error = y_pred - y_true
    abs_error = np.abs(error)
    
    # L2损失区域
    quadratic = 0.5 * error ** 2
    
    # L1损失区域
    linear = delta * abs_error - 0.5 * delta ** 2
    
    return np.mean(np.where(abs_error <= delta, quadratic, linear))


def binary_cross_entropy(y_pred, y_true, eps=1e-8):
    """
    二分类交叉熵损失
    """
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def softmax_cross_entropy(logits, labels):
    """
    多分类交叉熵损失（带Softmax）
    """
    # 数值稳定的Softmax
    logits_shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_shifted)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    # 交叉熵
    eps = 1e-8
    ce = -np.sum(labels * np.log(probs + eps), axis=-1)
    return np.mean(ce)


def sparse_softmax_cross_entropy(logits, labels):
    """
    稀疏多分类交叉熵（标签是整数索引）
    """
    # 数值稳定的Softmax
    logits_shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_shifted)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    # 获取正确类别的概率
    batch_size = logits.shape[0]
    correct_log_probs = -np.log(probs[np.arange(batch_size), labels] + 1e-8)
    
    return np.mean(correct_log_probs)


def focal_loss(logits, labels, gamma=2.0, alpha=0.25):
    """
    Focal Loss：用于处理类别不平衡
    """
    # Softmax
    probs = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = probs / np.sum(probs, axis=-1, keepdims=True)
    
    # 获取目标类别的概率
    batch_size = logits.shape[0]
    p_t = probs[np.arange(batch_size), labels]
    
    # Focal weight
    focal_weight = (1 - p_t) ** gamma
    
    # Alpha weighting
    alpha_t = alpha * np.ones_like(labels)
    alpha_t[labels == 0] = 1 - alpha
    
    # Focal loss
    loss = -alpha_t * focal_weight * np.log(p_t + 1e-8)
    
    return np.mean(loss)


def triplet_loss(anchor, positive, negative, margin=1.0):
    """
    Triplet Loss：用于度量学习
    d(a, p) - d(a, n) + margin
    """
    d_ap = np.sum((anchor - positive) ** 2, axis=-1)
    d_an = np.sum((anchor - negative) ** 2, axis=-1)
    
    loss = np.maximum(0, d_ap - d_an + margin)
    return np.mean(loss)


def contrastive_loss(embeddings1, embeddings2, labels, margin=1.0):
    """
    对比损失：相同类别拉近，不同类别推开
    """
    # 计算相似度
    similarities = np.sum(embeddings1 * embeddings2, axis=-1)
    
    # 正样本对：最大化相似度
    # 负样本对：最小化相似度（到margin以下）
    loss = labels * (1 - similarities) ** 2 + (1 - labels) * np.maximum(0, similarities - margin) ** 2
    
    return np.mean(loss)


def center_loss(features, labels, centers):
    """
    Center Loss：让同一类别的特征靠近类中心
    """
    batch_size = features.shape[0]
    
    loss = 0.0
    for i in range(batch_size):
        label = labels[i]
        center = centers[label]
        loss += np.sum((features[i] - center) ** 2)
    
    return loss / batch_size


class LossFunction:
    """损失函数包装类"""
    
    def __init__(self, name='mse'):
        self.name = name
    
    def __call__(self, y_pred, y_true, **kwargs):
        if self.name == 'mse':
            return mean_squared_error(y_pred, y_true)
        elif self.name == 'mae':
            return mean_absolute_error(y_pred, y_true)
        elif self.name == 'huber':
            return huber_loss(y_pred, y_true, kwargs.get('delta', 1.0))
        elif self.name == 'bce':
            return binary_cross_entropy(y_pred, y_true)
        elif self.name == 'cross_entropy':
            return softmax_cross_entropy(y_pred, y_true)
        elif self.name == 'focal':
            return focal_loss(y_pred, y_true, kwargs.get('gamma', 2.0))
        else:
            raise ValueError(f"Unknown loss: {self.name}")


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("损失函数测试")
    print("=" * 55)
    
    # 回归损失测试
    print("\n--- 回归损失测试 ---")
    y_pred = np.array([1.0, 2.0, 3.0, 4.0])
    y_true = np.array([1.5, 2.5, 2.5, 4.5])
    
    print(f"预测值: {y_pred}")
    print(f"真实值: {y_true}")
    print(f"MSE: {mean_squared_error(y_pred, y_true):.4f}")
    print(f"MAE: {mean_absolute_error(y_pred, y_true):.4f}")
    print(f"Huber: {huber_loss(y_pred, y_true):.4f}")
    
    # 分类损失测试
    print("\n--- 分类损失测试 ---")
    logits = np.array([
        [2.0, 1.0, 0.5],
        [0.5, 2.0, 1.0],
        [1.0, 0.5, 2.0]
    ])
    labels = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ])
    sparse_labels = np.array([0, 1, 2])
    
    print(f"Logits:\n{logits}")
    print(f"Labels (one-hot):\n{labels}")
    print(f"Cross Entropy: {softmax_cross_entropy(logits, labels):.4f}")
    print(f"Sparse Cross Entropy: {sparse_softmax_cross_entropy(logits, sparse_labels):.4f}")
    print(f"Focal Loss: {focal_loss(logits, sparse_labels):.4f}")
    
    # Triplet Loss测试
    print("\n--- Triplet Loss测试 ---")
    anchor = np.array([[1.0, 2.0], [3.0, 4.0]])
    positive = np.array([[1.1, 2.1], [3.1, 4.1]])
    negative = np.array([[5.0, 6.0], [7.0, 8.0]])
    
    loss = triplet_loss(anchor, positive, negative, margin=1.0)
    print(f"Triplet Loss: {loss:.4f}")
    
    # 困难样本测试
    print("\n--- 困难Triplet样本 ---")
    # 困难负样本：很接近锚点
    hard_negative = np.array([[1.2, 2.2], [3.2, 4.2]])
    
    loss_easy = triplet_loss(anchor, positive, negative, margin=0.5)
    loss_hard = triplet_loss(anchor, positive, hard_negative, margin=0.5)
    
    print(f"简单负样本 Loss: {loss_easy:.4f}")
    print(f"困难负样本 Loss: {loss_hard:.4f}")
    print("困难负样本会产生更大的损失")
    
    # Focal Loss测试
    print("\n--- Focal Loss测试 ---")
    # 模拟类别不平衡
    imbalanced_logits = np.array([
        [5.0, 0.5, 0.3],
        [0.2, 0.3, 0.1],
        [0.1, 0.1, 0.05]
    ])
    imbalanced_labels = np.array([0, 1, 2])
    
    ce_loss = sparse_softmax_cross_entropy(imbalanced_logits, imbalanced_labels)
    focal_loss_val = focal_loss(imbalanced_logits, imbalanced_labels, gamma=2.0)
    
    print(f"标准Cross Entropy: {ce_loss:.4f}")
    print(f"Focal Loss (γ=2): {focal_loss_val:.4f}")
    print("Focal Loss降低了简单样本的权重")
    
    # 对比损失测试
    print("\n--- 对比损失测试 ---")
    emb1 = np.random.randn(10, 8)
    emb2 = np.random.randn(10, 8)
    same_labels = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    
    loss_contrastive = contrastive_loss(emb1, emb2, same_labels)
    print(f"对比损失: {loss_contrastive:.4f}")
    
    # LRScheduler with Loss监控
    print("\n--- 损失曲线模拟 ---")
    epochs = 50
    losses = []
    
    for epoch in range(epochs):
        # 模拟损失下降
        loss = 1.0 / (1 + epoch / 10) + np.random.randn() * 0.05
        losses.append(max(0.01, loss))
    
    print(f"初始损失: {losses[0]:.4f}")
    print(f"最终损失: {losses[-1]:.4f}")
    print(f"损失下降: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")
    
    print("\n损失函数测试完成！")

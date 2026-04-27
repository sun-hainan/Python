# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / model_pruning

本文件实现 model_pruning 相关的算法功能。
"""

import numpy as np


# ============================
# 幅度剪枝
# ============================

def magnitude_prune(weights, sparsity):
    """
    幅度剪枝：移除绝对值最小的权重
    
    参数:
        weights: 权重矩阵
        sparsity: 剪枝比例（0-1之间），如0.5表示剪掉50%的权重
    返回:
        mask: 保留位置为True，剪掉位置为False
    """
    threshold = np.percentile(np.abs(weights), sparsity * 100)
    mask = np.abs(weights) > threshold
    return mask


def apply_pruning_mask(weights, mask):
    """将剪枝掩码应用到权重"""
    return weights * mask


class MagnitudePruner:
    """
    幅度剪枝器
    
    参数:
        sparsity: 剪枝比例（每次剪掉多少比例的权重）
        gradual: 是否渐进式剪枝（默认True）
    """
    
    def __init__(self, sparsity=0.5, gradual=True):
        self.sparsity = sparsity
        self.gradual = gradual
        self.current_sparsity = 0.0
        self.masks = {}
    
    def step(self, model, epoch=None, total_epochs=None):
        """
        执行一步剪枝
        
        参数:
            model: 包含weights的模型（需有state_dict方法）
            epoch: 当前epoch（用于渐进式剪枝）
            total_epochs: 总epoch数
        """
        if self.gradual and epoch is not None and total_epochs is not None:
            # 渐进式剪枝：从0逐渐增加到目标sparsity
            self.current_sparsity = self.sparsity * (epoch / total_epochs)
        else:
            self.current_sparsity = self.sparsity
        
        for name, param in model.items():
            if 'weight' in name:
                # 对每层独立计算阈值
                threshold = np.percentile(
                    np.abs(param), 
                    self.current_sparsity * 100
                )
                mask = np.abs(param) > threshold
                self.masks[name] = mask


# ============================
# 结构化剪枝
# ============================

def prune_channels_by_l1(weights, channel_axis=0, sparsity=0.5):
    """
    按L1范数剪枝通道/神经元
    
    参数:
        weights: 权重张量 (out_channels, in_channels, kH, kW) 或 (out_features, in_features)
        channel_axis: 通道所在的轴
        sparsity: 剪枝比例
    返回:
        mask: 保留的通道掩码
    """
    if channel_axis == 0:
        # 计算每个输出通道的L1范数
        channel_norms = np.sum(np.abs(weights), axis=(1, 2, 3)) if weights.ndim == 4 \
                       else np.sum(np.abs(weights), axis=1)
    else:
        channel_norms = np.sum(np.abs(weights), axis=(0, 2, 3)) if weights.ndim == 4 \
                       else np.sum(np.abs(weights), axis=0)
    
    threshold = np.percentile(channel_norms, sparsity * 100)
    mask = channel_norms > threshold
    return mask


def structured_prune_weights(weights, mask):
    """
    应用结构化剪枝掩码
    
    参数:
        weights: 权重 (out_channels, in_channels, kH, kW)
        mask: 通道掩码
    返回:
        pruned_weights: 剪枝后的权重
    """
    if weights.ndim == 4:
        return weights[mask, :, :, :]
    elif weights.ndim == 2:
        return weights[mask, :]
    return weights


class StructuredPruner:
    """
    结构化剪枝器（按通道/神经元组剪枝）
    
    参数:
        sparsity: 剪枝比例
        criterion: 剪枝准则 ('l1', 'l2', 'taylor')
    """
    
    def __init__(self, sparsity=0.5, criterion='l1'):
        self.sparsity = sparsity
        self.criterion = criterion
        self.masks = {}
    
    def compute_channel_importance(self, weights, criterion='l1'):
        """
        计算每个通道的重要性分数
        
        参数:
            weights: 权重张量
            criterion: 重要性准则
        返回:
            importance: 每个通道的重要性分数
        """
        if criterion == 'l1':
            # L1范数：衡量通道的平均激活强度
            importance = np.sum(np.abs(weights), axis=tuple(range(1, weights.ndim)))
        elif criterion == 'l2':
            # L2范数
            importance = np.sqrt(np.sum(weights ** 2, axis=tuple(range(1, weights.ndim))))
        elif criterion == 'l1_mean':
            # 平均L1范数（考虑通道内权重数量）
            importance = np.mean(np.abs(weights), axis=tuple(range(1, weights.ndim)))
        else:
            raise ValueError(f"Unknown criterion: {criterion}")
        
        return importance
    
    def prune(self, weights, sparsity=None):
        """
        执行结构化剪枝
        
        参数:
            weights: 权重张量
            sparsity: 剪枝比例（可选，覆盖默认值）
        返回:
            pruned_weights: 剪枝后的权重
            mask: 保留通道的掩码
        """
        if sparsity is None:
            sparsity = self.sparsity
        
        importance = self.compute_channel_importance(weights, self.criterion)
        threshold = np.percentile(importance, sparsity * 100)
        mask = importance > threshold
        
        if weights.ndim == 4:
            pruned = weights[mask, :, :, :]
        elif weights.ndim == 2:
            pruned = weights[mask, :]
        else:
            pruned = weights[mask] if mask.ndim == 1 else weights
        
        return pruned, mask


# ============================
# 迭代式剪枝与微调
# ============================

class IterativePruner:
    """
    迭代式剪枝：多次剪枝-微调循环
    
    参数:
        pruner: 基础剪枝器
        prune_epochs: 总剪枝epoch数
        prune_ratio_per_iter: 每次迭代的剪枝比例
    """
    
    def __init__(self, pruner, prune_epochs=10, prune_ratio_per_iter=0.1):
        self.pruner = pruner
        self.prune_epochs = prune_epochs
        self.prune_ratio_per_iter = prune_ratio_per_iter
    
    def simulate_pruning_iterations(self, weights, iterations=5):
        """
        模拟多次迭代剪枝的过程
        
        参数:
            weights: 初始权重
            iterations: 迭代次数
        返回:
            final_weights: 最终剪枝后的权重
            history: 每次迭代后的非零比例
        """
        current_weights = weights.copy()
        history = [1.0]  # 初始非零比例
        
        for i in range(iterations):
            # 计算当前迭代的目标稀疏度
            target_sparsity = 1 - (1 - self.prune_ratio_per_iter) ** (i + 1)
            current_sparsity = target_sparsity - (1 - history[-1])
            
            if current_sparsity > 0:
                mask = magnitude_prune(current_weights, current_sparsity)
                current_weights = current_weights * mask
            
            nonzero_ratio = np.sum(mask) / mask.size
            history.append(nonzero_ratio)
            print(f"  迭代 {i+1}: 稀疏度={1-nonzero_ratio:.2%}, 非零权重数={np.sum(mask)}")
        
        return current_weights, history


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("模型剪枝测试")
    print("=" * 55)
    
    # 测试1：幅度剪枝
    print("\n--- 幅度剪枝测试 ---")
    weights = np.random.randn(512, 512) * 0.1
    original_count = weights.size
    
    for sparsity in [0.3, 0.5, 0.7, 0.9]:
        mask = magnitude_prune(weights, sparsity)
        pruned_count = np.sum(mask)
        print(f"  稀疏度{sparsity:.0%}: 保留{pruned_count}/{original_count} ({pruned_count/original_count:.1%})")
    
    # 测试2：结构化剪枝
    print("\n--- 结构化剪枝（通道剪枝）测试 ---")
    # 模拟CNN权重: (out_channels=32, in_channels=16, kH=3, kW=3)
    conv_weights = np.random.randn(32, 16, 3, 3) * 0.05
    
    for sparsity in [0.25, 0.5]:
        pruned, mask = StructuredPruner(sparsity=sparsity).prune(conv_weights)
        print(f"  稀疏度{sparsity:.0%}: 输出通道 32 -> {pruned.shape[0]}")
    
    # 测试3：迭代式剪枝
    print("\n--- 迭代式剪枝测试 ---")
    weights_large = np.random.randn(100, 100) * 0.01
    
    pruner = IterativePruner(
        MagnitudePruner(sparsity=0.8),
        prune_epochs=10,
        prune_ratio_per_iter=0.2
    )
    
    print("模拟5次迭代剪枝:")
    final_weights, history = pruner.simulate_pruning_iterations(weights_large, iterations=5)
    
    # 测试4：剪枝后权重分布
    print("\n--- 剪枝后权重分布分析 ---")
    mask = magnitude_prune(weights, 0.5)
    remaining = weights[mask]
    
    print(f"原始权重: 均值={weights.mean():.4f}, 标准差={weights.std():.4f}")
    print(f"剪枝后权重: 均值={remaining.mean():.4f}, 标准差={remaining.std():.4f}")
    print(f"被剪枝权重均值: {weights[~mask].mean():.4f}")
    
    # 测试5：不同剪枝准则对比
    print("\n--- 不同剪枝准则对比 ---")
    conv_weights_test = np.random.randn(64, 32, 3, 3)
    
    for criterion in ['l1', 'l2', 'l1_mean']:
        pruner = StructuredPruner(sparsity=0.3, criterion=criterion)
        importance = pruner.compute_channel_importance(conv_weights_test, criterion)
        print(f"  {criterion}: 通道重要性范围=[{importance.min():.4f}, {importance.max():.4f}]")
    
    print("\n模型剪枝测试完成！")

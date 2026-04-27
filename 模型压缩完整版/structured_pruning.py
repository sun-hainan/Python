# -*- coding: utf-8 -*-
"""
算法实现：模型压缩完整版 / structured_pruning

本文件实现 structured_pruning 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import copy


class ChannelPruner:
    """
    通道剪枝器

    移除不重要的卷积通道
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def compute_channel_importance(self, dataloader, num_batches=50):
        """
        计算通道重要性

        使用L1范数或梯度作为重要性指标

        参数:
            dataloader: 数据加载器
            num_batches: 评估的批次数

        返回:
            importance_dict: {layer_name: importance_scores}
        """
        self.model.eval()
        importance = {}

        # 收集每层的批归一化缩放因子
        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                # 使用BN的gamma作为通道重要性
                importance[name] = module.weight.data.abs().cpu().numpy()

        return importance

    def prune_channels(self, importance_dict, prune_ratio=0.3):
        """
        根据重要性剪枝通道

        参数:
            importance_dict: 通道重要性字典
            prune_ratio: 剪枝比例
        """
        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                if name not in importance_dict:
                    continue

                imp = importance_dict[name]
                threshold = np.percentile(imp, prune_ratio * 100)

                # 创建mask
                mask = torch.from_numpy(imp > threshold).float().to(self.device)

                # 应用mask到BN参数
                module.weight.data *= mask
                module.bias.data *= mask

    def get_pruned_model(self):
        """创建剪枝后的模型（需要重建）"""
        # 简化：返回带有mask的模型
        return self.model


class NeuronPruner:
    """
    神经元剪枝器

    移除不重要的神经元（全连接层）
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def compute_neuron_importance(self, dataloader, num_batches=50):
        """
        计算神经元重要性

        使用激活值或梯度
        """
        self.model.eval()
        neuron_activations = {}

        hooks = []

        def hook_fn(name):
            def hook(module, input, output):
                if isinstance(output, torch.Tensor):
                    # 使用激活的L1范数
                    acts = output.detach()
                    importance = acts.abs().mean(dim=(0, 2, 3) if acts.dim() == 4 else 0)
                    if name not in neuron_activations:
                        neuron_activations[name] = []
                    neuron_activations[name].append(importance)
            return hook

        # 注册hook
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                handle = module.register_forward_hook(hook_fn(name))
                hooks.append(handle)

        # 收集激活
        with torch.no_grad():
            for i, (images, _) in enumerate(dataloader):
                if i >= num_batches:
                    break
                self.model(images.to(self.device))

        # 移除hook
        for h in hooks:
            h.remove()

        # 计算平均重要性
        importance_dict = {}
        for name, acts in neuron_activations.items():
            stacked = torch.stack(acts, dim=0)
            importance_dict[name] = stacked.mean(dim=0).cpu().numpy()

        return importance_dict

    def prune_neurons(self, importance_dict, prune_ratio=0.3):
        """
        剪枝神经元
        """
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                if name not in importance_dict:
                    continue

                imp = importance_dict[name]
                threshold = np.percentile(imp, prune_ratio * 100)

                mask = torch.from_numpy(imp > threshold).float().to(self.device)

                # 应用mask
                module.weight.data *= mask.view(-1, 1)
                if module.bias is not None:
                    module.bias.data *= mask


class LayerPruner:
    """
    层级剪枝器

    移除整个层（如整个卷积层）
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def compute_layer_importance(self, dataloader):
        """
        计算层级重要性

        使用泰勒展开估计
        """
        self.model.train()
        layer_importance = {}

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                module.weight.requires_grad = True

        hooks = []
        gradients = {}

        def hook_fn(name):
            def hook(module, grad_input, grad_output):
                gradients[name] = grad_output[0].detach()
            return hook

        # 注册hook
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                handle = module.register_full_backward_hook(hook_fn(name))
                hooks.append(handle)

        # 计算梯度
        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            outputs = self.model(images)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

        # 移除hook
        for h in hooks:
            h.remove()

        # 计算重要性
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                weight = module.weight.data
                grad = gradients.get(name)

                if grad is not None:
                    # 泰勒重要性：|weight * gradient|
                    importance = (weight * grad).abs().mean().item()
                    layer_importance[name] = importance

        return layer_importance

    def remove_layers(self, layer_importance, prune_ratio=0.2):
        """
        移除不重要的层
        """
        # 简化实现
        sorted_layers = sorted(layer_importance.items(), key=lambda x: x[1])

        num_remove = int(len(sorted_layers) * prune_ratio)

        for name, _ in sorted_layers[:num_remove]:
            print(f"移除层: {name}")


class StructuredPruner:
    """
    结构化剪枝统一接口

    支持多种结构化剪枝策略
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.pruning_masks = {}

    def magnitude_based_pruning(self, sparsity=0.5):
        """
        基于幅度的剪枝
        """
        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                # 使用gamma作为重要性
                gamma = module.weight.data.abs()
                threshold = torch.quantile(gamma, sparsity)

                mask = (gamma > threshold).float()
                self.pruning_masks[name] = mask

                module.weight.data *= mask
                module.bias.data *= mask

    def gradient_based_pruning(self, dataloader, sparsity=0.5):
        """
        基于梯度的剪枝
        """
        self.model.train()

        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                module.weight.requires_grad = True

        # 收集梯度
        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            outputs = self.model(images)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

        # 基于梯度剪枝
        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                grad = module.weight.grad
                if grad is not None:
                    importance = grad.abs()
                    threshold = torch.quantile(importance, sparsity)

                    mask = (importance > threshold).float()
                    self.pruning_masks[name] = mask

                    module.weight.data *= mask
                    module.bias.data *= mask

    def random_pruning(self, sparsity=0.5):
        """
        随机剪枝（作为基线）
        """
        for name, module in self.model.named_modules():
            if isinstance(module, nn.BatchNorm2d):
                mask = (torch.rand_like(module.weight.data) > sparsity).float()
                self.pruning_masks[name] = mask

                module.weight.data *= mask
                module.bias.data *= mask

    def apply_masks(self):
        """应用保存的mask"""
        for name, mask in self.pruning_masks.items():
            for n, module in self.model.named_modules():
                if n == name and isinstance(module, nn.BatchNorm2d):
                    module.weight.data *= mask
                    module.bias.data *= mask

    def restore_weights(self, original_state_dict):
        """恢复原始权重"""
        self.model.load_state_dict(original_state_dict)


class PruningScheduler:
    """
    渐进式剪枝调度

    逐步增加剪枝率
    """

    def __init__(self, model, initial_ratio=0.1, final_ratio=0.7, steps=100):
        self.model = model
        self.initial_ratio = initial_ratio
        self.final_ratio = final_ratio
        self.steps = steps

    def get_sparsity(self, step):
        """获取当前步的剪枝率"""
        # 线性调度
        ratio = self.initial_ratio + (self.final_ratio - self.initial_ratio) * step / self.steps
        return min(ratio, self.final_ratio)

    def step(self, step, dataloader):
        """执行一步剪枝"""
        sparsity = self.get_sparsity(step)
        pruner = StructuredPruner(self.model)

        if step % 10 == 0:
            pruner.magnitude_based_pruning(sparsity=sparsity)


if __name__ == "__main__":
    # 定义简单模型
    class SimpleCNN(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
            self.bn1 = nn.BatchNorm2d(32)
            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
            self.bn2 = nn.BatchNorm2d(64)
            self.fc1 = nn.Linear(64 * 7 * 7, 128)
            self.fc2 = nn.Linear(128, num_classes)

        def forward(self, x):
            x = F.relu(self.bn1(F.max_pool2d(self.conv1(x), 2)))
            x = F.relu(self.bn2(F.max_pool2d(self.conv2(x), 2)))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    device = torch.device("cpu")
    model = SimpleCNN(num_classes=10).to(device)

    # 虚拟数据
    class DummyDataset:
        def __init__(self, size=10):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                images = torch.rand(32, 1, 28, 28)
                labels = torch.randint(0, 10, (32,))
                yield images, labels

    print("=" * 50)
    print("结构化剪枝测试")
    print("=" * 50)

    # 通道剪枝
    print("\n--- 通道剪枝 ---")
    channel_pruner = ChannelPruner(model, device)
    importance = channel_pruner.compute_channel_importance(DummyDataset(10), num_batches=5)

    for name, imp in list(importance.items())[:3]:
        print(f"{name}: 通道数={len(imp)}, 重要性范围=[{imp.min():.4f}, {imp.max():.4f}]")

    channel_pruner.prune_channels(importance, prune_ratio=0.3)

    # 结构化剪枝
    print("\n--- 结构化剪枝 ---")
    model2 = SimpleCNN(num_classes=10).to(device)
    structured_pruner = StructuredPruner(model2, device)

    # 幅度剪枝
    structured_pruner.magnitude_based_pruning(sparsity=0.5)
    print("幅度剪枝完成")

    # 随机剪枝
    structured_pruner.random_pruning(sparsity=0.3)
    print("随机剪枝完成")

    # 剪枝调度器
    print("\n--- 剪枝调度器 ---")
    scheduler = PruningScheduler(model, initial_ratio=0.1, final_ratio=0.7, steps=100)

    for step in [0, 25, 50, 75, 100]:
        sparsity = scheduler.get_sparsity(step)
        print(f"Step {step}: sparsity={sparsity:.2%}")

    print("\n测试完成！")

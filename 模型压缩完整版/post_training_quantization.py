# -*- coding: utf-8 -*-
"""
算法实现：模型压缩完整版 / post_training_quantization

本文件实现 post_training_quantization 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.stats import norm


class PostTrainingQuantization:
    """
    后训练量化基类
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()

    def quantize_weights(self, num_bits=8):
        """
        量化模型权重

        参数:
            num_bits: 量化位数
        """
        n_levels = 2 ** num_bits

        for name, param in self.model.named_parameters():
            if 'weight' not in name:
                continue

            weight = param.data.cpu().numpy()
            w_min, w_max = weight.min(), weight.max()

            # 均匀量化
            scale = (w_max - w_min) / (n_levels - 1)
            quantized = torch.round((param.data - w_min) / scale) * scale + w_min

            param.data.copy_(quantized)

    def quantize_activations(self, images, num_bits=8):
        """
        量化激活值

        需要通过模型获取激活值范围
        """
        hooks = []
        activation_ranges = {}

        def hook_fn(name):
            def hook(module, input, output):
                if isinstance(output, torch.Tensor):
                    activation_ranges[name] = {
                        'min': output.detach().min(),
                        'max': output.detach().max()
                    }
            return hook

        # 注册hook
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.ReLU, nn.Conv2d, nn.Linear)):
                hooks.append(module.register_forward_hook(hook_fn(name)))

        # 运行一次前向传播
        with torch.no_grad():
            self.model(images)

        # 移除hook
        for h in hooks:
            h.remove()

        return activation_ranges


class DynamicQuantization:
    """
    动态量化

    在推理时动态量化权重，使用更细粒度的统计信息
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def compute_scale_zp(self, tensor, num_bits=8):
        """
        计算量化的scale和zero_point

        参数:
            tensor: 待量化张量
            num_bits: 位数

        返回:
            scale: 缩放因子
            zero_point: 零点
        """
        qmin, qmax = 0, 2 ** num_bits - 1

        min_val = tensor.min().item()
        max_val = tensor.max().item()

        # 避免除零
        if max_val == min_val:
            return 1.0, 0

        scale = (max_val - min_val) / (qmax - qmin)
        zero_point = qmin - min_val / scale

        return scale, zero_point

    def quantize_tensor(self, tensor, num_bits=8, scale=None, zero_point=None):
        """
        量化单个张量

        参数:
            tensor: 输入张量
            num_bits: 位数
            scale: 缩放因子
            zero_point: 零点
        """
        if scale is None or zero_point is None:
            scale, zero_point = self.compute_scale_zp(tensor, num_bits)

        qmin, qmax = 0, 2 ** num_bits - 1
        quantized = torch.round(tensor / scale + zero_point)
        quantized = torch.clamp(quantized, qmin, qmax)

        return quantized, scale, zero_point

    def dequantize_tensor(self, quantized, scale, zero_point):
        """
        反量化

        参数:
            quantized: 量化后的张量
            scale: 缩放因子
            zero_point: 零点
        """
        return scale * (quantized - zero_point)

    def dynamic_quantize_model(self, num_bits=8):
        """
        对整个模型应用动态量化
        """
        quantized_state_dict = {}

        for name, param in self.model.state_dict().items():
            if 'weight' in name:
                quantized, scale, zero_point = self.quantize_tensor(param, num_bits)
                quantized_state_dict[name] = {
                    'quantized': quantized,
                    'scale': scale,
                    'zero_point': zero_point
                }
            else:
                quantized_state_dict[name] = param

        return quantized_state_dict


class CalibrationQuantization:
    """
    校准量化

    使用少量校准数据来确定量化参数
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.calibration_data = []
        self.hooks = []

    def collect_statistics(self, dataloader, num_batches=100):
        """
        收集激活值统计信息

        参数:
            dataloader: 数据加载器
            num_batches: 收集的批次数
        """
        self.model.eval()
        activation_stats = {}

        def hook_fn(name):
            def hook(module, input, output):
                if isinstance(output, torch.Tensor):
                    if name not in activation_stats:
                        activation_stats[name] = {'min': [], 'max': [], 'hist': []}
                    activation_stats[name]['min'].append(output.detach().min().item())
                    activation_stats[name]['max'].append(output.detach().max().item())
            return hook

        # 注册hook
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.ReLU, nn.Conv2d, nn.Linear)):
                self.hooks.append(module.register_forward_hook(hook_fn(name)))

        # 收集数据
        with torch.no_grad():
            for i, (images, _) in enumerate(dataloader):
                if i >= num_batches:
                    break
                self.model(images.to(self.device))

        # 移除hook
        for h in self.hooks:
            h.remove()

        # 计算百分位数
        self.activation_stats = {}
        for name, stats in activation_stats.items():
            all_min = min(stats['min'])
            all_max = max(stats['max'])
            # 使用0.01和0.99百分位数
            self.activation_stats[name] = {
                'min': np.percentile(stats['min'], 1),
                'max': np.percentile(stats['max'], 99)
            }

        return self.activation_stats

    def apply_quantization(self, num_bits=8):
        """
        应用量化
        """
        n_levels = 2 ** num_bits

        for name, param in self.model.named_parameters():
            if 'weight' not in name:
                continue

            weight = param.data.cpu().numpy()
            w_min, w_max = weight.min(), weight.max()

            scale = (w_max - w_min) / (n_levels - 1)
            quantized = torch.round((param.data - w_min) / scale) * scale + w_min

            param.data.copy_(quantized)


class MixedPrecisionQuantization:
    """
    混合精度量化

    为不同层分配不同的量化位数
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def analyze_layer_importance(self, dataloader):
        """
        分析每层的重要性

        基于梯度或激活敏感度
        """
        self.model.train()
        layer_importance = {}

        for name, param in self.model.named_parameters():
            if 'weight' not in name:
                continue

            param.requires_grad = True
            total_grad = 0.0
            count = 0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                self.model.zero_grad()
                loss.backward()

                total_grad += param.grad.abs().mean().item()
                count += 1

                if count >= 10:
                    break

            layer_importance[name] = total_grad / count

        # 归一化
        max_imp = max(layer_importance.values())
        for name in layer_importance:
            layer_importance[name] /= max_imp

        return layer_importance

    def assign_bit_widths(self, layer_importance, total_bits):
        """
        分配位宽

        参数:
            layer_importance: 层重要性分数
            total_bits: 可用的总比特数
        """
        num_layers = len(layer_importance)
        avg_bits = total_bits / num_layers

        bit_assignments = {}

        for name, importance in layer_importance.items():
            # 重要性高的层分配更多比特
            bits = max(4, min(16, int(avg_bits * importance * 2)))
            bit_assignments[name] = bits

        return bit_assignments


if __name__ == "__main__":
    # 定义简单模型
    class SimpleCNN(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
            self.fc1 = nn.Linear(64 * 7 * 7, 128)
            self.fc2 = nn.Linear(128, num_classes)

        def forward(self, x):
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            x = F.relu(F.max_pool2d(self.conv2(x), 2))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    device = torch.device("cpu")
    model = SimpleCNN(num_classes=10).to(device)

    # 虚拟数据
    class DummyDataset:
        def __init__(self, size=20):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                images = torch.rand(32, 1, 28, 28)
                labels = torch.randint(0, 10, (32,))
                yield images, labels

    print("=" * 50)
    print("后训练量化（PTQ）测试")
    print("=" * 50)

    # 动态量化
    print("\n--- 动态量化 ---")
    dyn_quantizer = DynamicQuantization(model, device)

    test_weight = torch.randn(64, 32)
    scale, zero_point = dyn_quantizer.compute_scale_zp(test_weight, num_bits=8)
    print(f"Scale: {scale:.6f}, Zero Point: {zero_point:.6f}")

    quantized, s, z = dyn_quantizer.quantize_tensor(test_weight, num_bits=8)
    dequantized = dyn_quantizer.dequantize_tensor(quantized, s, z)

    error = (test_weight - dequantized).abs().mean()
    print(f"量化误差: {error:.6f}")

    # 校准量化
    print("\n--- 校准量化 ---")
    cal_quantizer = CalibrationQuantization(model, device)
    stats = cal_quantizer.collect_statistics(DummyDataset(20), num_batches=10)

    print(f"收集到 {len(stats)} 层的激活统计")

    # 混合精度量化
    print("\n--- 混合精度量化 ---")
    mixed_quantizer = MixedPrecisionQuantization(model, device)
    importance = mixed_quantizer.analyze_layer_importance(DummyDataset(20))

    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("层重要性排名:")
    for name, imp in sorted_imp[:5]:
        print(f"  {name}: {imp:.4f}")

    bit_assignments = mixed_quantizer.assign_bit_widths(importance, total_bits=128)
    print("\n位宽分配:")
    for name, bits in list(bit_assignments.items())[:5]:
        print(f"  {name}: {bits} bits")

    print("\n测试完成！")

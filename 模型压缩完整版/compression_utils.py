# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / compression_utils



本文件实现 compression_utils 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

from typing import Dict, List, Tuple





class CompressionUtils:

    """

    模型压缩工具类

    """



    @staticmethod

    def count_parameters(model):

        """统计参数量"""

        return sum(p.numel() for p in model.parameters())



    @staticmethod

    def count_flops(model, input_shape=(1, 1, 32, 32)):

        """估算FLOPs"""

        total = 0

        for m in model.modules():

            if isinstance(m, nn.Conv2d):

                h, w = input_shape[2], input_shape[3]

                out_h = (h + 2 * m.padding[0] - m.kernel_size[0]) // m.stride[0] + 1

                out_w = (w + 2 * m.padding[1] - m.kernel_size[1]) // m.stride[1] + 1

                total += m.in_channels * m.out_channels * m.kernel_size[0] * m.kernel_size[1] * out_h * out_w

                input_shape = (1, m.out_channels, out_h, out_w)

        return total



    @staticmethod

    def compute_sparsity(model):

        """计算稀疏度"""

        total = 0

        zero = 0



        for p in model.parameters():

            if p.dim() > 1:

                total += p.numel()

                zero += (p == 0).sum().item()



        return zero / total if total > 0 else 0



    @staticmethod

    def get_model_size_kb(model):

        """获取模型大小（KB）"""

        import pickle

        size = len(pickle.dumps(model.state_dict()))

        return size / 1024





class PruningScheduler:

    """

    剪枝调度器



    支持多种调度策略

    """



    def __init__(self, initial_sparsity=0.0, final_sparsity=0.7, schedule_type='linear'):

        self.initial = initial_sparsity

        self.final = final_sparsity

        self.schedule_type = schedule_type



    def get_sparsity(self, epoch, total_epochs):

        """获取当前稀疏度"""

        progress = epoch / total_epochs



        if self.schedule_type == 'linear':

            return self.initial + (self.final - self.initial) * progress

        elif self.schedule_type == 'exponential':

            return self.initial * (self.final / self.initial) ** progress

        elif self.schedule_type == 'cosine':

            return self.initial + (self.final - self.initial) * (1 - np.cos(np.pi * progress)) / 2

        else:

            return self.final





class QuantizationConfig:

    """

    量化配置

    """



    def __init__(self, num_bits=8, scheme='symmetric'):

        self.num_bits = num_bits

        self.scheme = scheme  # 'symmetric' or 'asymmetric'



    def compute_scale_zero(self, tensor):

        """计算量化的scale和zero_point"""

        if self.scheme == 'symmetric':

            scale = tensor.abs().max() / (2 ** (self.num_bits - 1) - 1)

            zero_point = 0

        else:

            min_val = tensor.min()

            max_val = tensor.max()

            scale = (max_val - min_val) / (2 ** self.num_bits - 1)

            zero_point = -min_val / scale



        return scale, zero_point



    def quantize(self, tensor):

        """量化张量"""

        scale, zero_point = self.compute_scale_zero(tensor)

        quantized = torch.round(tensor / scale + zero_point)

        quantized = torch.clamp(quantized, 0, 2 ** self.num_bits - 1)

        return quantized * scale - zero_point





class KnowledgeDistillationLoss:

    """

    知识蒸馏损失函数集合

    """



    @staticmethod

    def kl_div_loss(student_logits, teacher_logits, temperature=4.0, alpha=0.5):

        """KL散度蒸馏损失"""

        student_soft = F.log_softmax(student_logits / temperature, dim=1)

        teacher_soft = F.softmax(teacher_logits / temperature, dim=1)



        kl_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * (temperature ** 2)



        hard_loss = F.cross_entropy(student_logits, torch.argmax(teacher_logits, dim=1))



        return alpha * hard_loss + (1 - alpha) * kl_loss



    @staticmethod

    def attention_transfer_loss(student_features, teacher_features):

        """注意力迁移损失"""

        student_attention = F.normalize(student_features.sum(dim=-1), p=2, dim=-1)

        teacher_attention = F.normalize(teacher_features.sum(dim=-1), p=2, dim=-1)



        return F.mse_loss(student_attention, teacher_attention)





class CompressionPipeline:

    """

    压缩流水线



    按顺序执行多种压缩操作

    """



    def __init__(self, model):

        self.model = model

        self.steps = []



    def add_step(self, name, func):

        """添加压缩步骤"""

        self.steps.append((name, func))



    def execute(self):

        """执行流水线"""

        results = {}



        for name, func in self.steps:

            self.model = func(self.model)

            results[name] = {

                'params': CompressionUtils.count_parameters(self.model),

                'flops': CompressionUtils.count_flops(self.model),

                'size_kb': CompressionUtils.get_model_size_kb(self.model)

            }



        return results





if __name__ == "__main__":

    class SimpleCNN(nn.Module):

        def __init__(self):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, 10)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    model = SimpleCNN()



    print("=" * 50)

    print("模型压缩工具箱测试")

    print("=" * 50)



    print(f"\n原始模型:")

    print(f"  参数量: {CompressionUtils.count_parameters(model):,}")

    print(f"  FLOPs: {CompressionUtils.count_flops(model):,}")

    print(f"  大小: {CompressionUtils.get_model_size_kb(model):.2f} KB")



    # 剪枝调度器

    print("\n--- 剪枝调度器 ---")

    scheduler = PruningScheduler(0.0, 0.7, 'cosine')



    for epoch in [0, 25, 50, 75, 100]:

        sparsity = scheduler.get_sparsity(epoch, 100)

        print(f"  Epoch {epoch}: sparsity={sparsity:.2%}")



    # 量化

    print("\n--- 量化 ---")

    config = QuantizationConfig(num_bits=8)

    test_weight = torch.randn(64, 32)

    quantized = config.quantize(test_weight)

    print(f"量化后形状: {quantized.shape}")



    # 压缩流水线

    print("\n--- 压缩流水线 ---")

    pipeline = CompressionPipeline(model)

    pipeline.add_step('placeholder', lambda m: m)

    results = pipeline.execute()

    print(f"压缩步骤结果: {results}")



    print("\n测试完成！")


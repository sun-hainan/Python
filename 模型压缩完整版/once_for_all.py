# -*- coding: utf-8 -*-
"""
算法实现：模型压缩完整版 / once_for_all

本文件实现 once_for_all 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple


class ElasticConv2d(nn.Module):
    """
    弹性卷积层

    支持不同的通道数
    """

    def __init__(self, max_in_channels, max_out_channels, kernel_size, stride=1, padding=0):
        super().__init__()
        self.max_in_channels = max_in_channels
        self.max_out_channels = max_out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding

        # 最大通道数的权重
        self.weight = nn.Parameter(
            torch.randn(max_out_channels, max_in_channels, kernel_size, kernel_size)
        )
        self.bias = nn.Parameter(torch.zeros(max_out_channels))

    def forward(self, x, out_channels=None, in_channels=None):
        """
        可变通道数的前向传播

        参数:
            out_channels: 输出通道数
            in_channels: 输入通道数
        """
        if out_channels is None:
            out_channels = self.max_out_channels
        if in_channels is None:
            in_channels = self.max_in_channels

        # 切片
        w = self.weight[:out_channels, :in_channels, :, :]
        b = self.bias[:out_channels]

        return F.conv2d(x, w, b, stride=self.stride, padding=self.padding)

    def get_params(self, out_channels, in_channels):
        """获取指定通道数的参数量"""
        return out_channels * in_channels * self.kernel_size * self.kernel_size


class ElasticLinear(nn.Module):
    """
    弹性全连接层
    """

    def __init__(self, max_in_features, max_out_features):
        super().__init__()
        self.max_in_features = max_in_features
        self.max_out_features = max_out_features

        self.weight = nn.Parameter(
            torch.randn(max_out_features, max_in_features)
        )
        self.bias = nn.Parameter(torch.zeros(max_out_features))

    def forward(self, x, out_features=None, in_features=None):
        if out_features is None:
            out_features = self.max_out_features
        if in_features is None:
            in_features = self.max_in_features

        w = self.weight[:out_features, :in_features]
        b = self.bias[:out_features]

        return F.linear(x, w, b)


class OFABlock(nn.Module):
    """
    Once-For-All Block

    支持不同的深度（跳过某些层）和宽度（不同通道数）
    """

    def __init__(self, max_in_channels, max_out_channels, kernel_size=3, stride=1):
        super().__init__()
        self.max_in_channels = max_in_channels
        self.max_out_channels = max_out_channels
        self.stride = stride

        # 深度可分离卷积
        self.depth_conv = ElasticConv2d(
            max_in_channels, max_in_channels, kernel_size, stride, padding=kernel_size // 2
        )
        self.point_conv = ElasticConv2d(
            max_in_channels, max_out_channels, 1
        )

        self.bn1 = nn.BatchNorm2d(max_in_channels)
        self.bn2 = nn.BatchNorm2d(max_out_channels)

        # 残差连接（仅当通道数匹配且stride=1时）
        self.use_residual = (max_in_channels == max_out_channels) and (stride == 1)

    def forward(self, x, depth=True, width_mult=1.0):
        """
        可配置深度和宽度的前向传播

        参数:
            depth: 是否执行此块（False则跳过）
            width_mult: 宽度缩放因子
        """
        if not depth:
            return x

        in_ch = max(8, int(self.max_in_channels * width_mult))
        out_ch = max(8, int(self.max_out_channels * width_mult))

        out = self.bn1(self.depth_conv(x, in_channels=in_ch, out_channels=in_ch))
        out = F.relu6(out)
        out = self.bn2(self.point_conv(out, in_channels=in_ch, out_channels=out_ch))

        if self.use_residual and width_mult == 1.0:
            return x + out
        else:
            return out


class OnceForAllNetwork(nn.Module):
    """
    Once-For-All网络

    训练一个超网，支持多种配置
    """

    def __init__(self, num_classes=10, depth_list=[2, 3, 4],
                 width_list=[0.65, 0.8, 1.0], resolution_list=[32, 28, 24]):
        super().__init__()

        self.depth_list = depth_list
        self.width_list = width_list
        self.resolution_list = resolution_list

        # 初始卷积
        self.stem = ElasticConv2d(3, 32, 3, stride=1, padding=1)

        # 阶段配置
        self.stages = nn.ModuleList([
            # (max_channels, num_blocks)
            (64, 2),
            (128, 2),
            (256, 3),
            (512, 2),
        ])

        self.blocks = nn.ModuleList()
        for max_ch, num_blocks in self.stages:
            stage_blocks = nn.ModuleList()
            for i in range(max(depth_list)):
                block = OFABlock(max_ch, max_ch, kernel_size=3, stride=2 if i == 0 and max_ch > 32 else 1)
                stage_blocks.append(block)
            self.blocks.append(stage_blocks)

        # 分类器
        self.classifier = ElasticLinear(512, num_classes)

        self._initialize_weights()

    def forward(self, x, depth=None, width_mult=1.0):
        """
        前向传播

        参数:
            depth: 每个阶段的深度（层数）
            width_mult: 通道宽度缩放因子
        """
        if depth is None:
            depth = [max(self.depth_list)] * len(self.blocks)

        # 初始层
        out = self.stem(x, out_channels=32)

        # 逐阶段处理
        for stage_idx, stage in enumerate(self.blocks):
            num_blocks = depth[stage_idx]

            for block_idx in range(max(self.depth_list)):
                if block_idx < num_blocks:
                    out = stage[block_idx](out, depth=True, width_mult=width_mult)
                else:
                    out = stage[block_idx](out, depth=False, width_mult=width_mult)

        # 全局池化和分类
        out = F.adaptive_avg_pool2d(out, 1)
        out = out.view(out.size(0), -1)
        out = self.classifier(out, out_features=10)

        return out

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)


class OFATrainer:
    """
    OFA训练器

    训练超网，支持不同的子网配置
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def train_step(self, images, labels, depth=None, width_mult=1.0):
        """一步训练"""
        outputs = self.model(images, depth=depth, width_mult=width_mult)
        loss = F.cross_entropy(outputs, labels)

        return loss

    def train_epoch(self, dataloader, depth_schedule=None, width_schedule=None):
        """
        训练一个epoch

        每次迭代随机选择不同的子网配置
        """
        total_loss = 0.0
        num_batches = 0

        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            # 随机选择配置
            depth = [np.random.choice(self.model.depth_list) for _ in range(len(self.model.blocks))]
            width_mult = np.random.choice(self.model.width_list)

            loss = self.train_step(images, labels, depth=depth, width_mult=width_mult)

            total_loss += loss.item()
            num_batches += 1

        return total_loss / num_batches

    def knowledge_distill(self, teacher_model, dataloader, alpha=0.5, temperature=4.0):
        """
        知识蒸馏训练OFA

        从大型模型蒸馏知识到超网
        """
        total_loss = 0.0

        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            # 随机选择子网配置
            depth = [np.random.choice(self.model.depth_list) for _ in range(len(self.model.blocks))]
            width_mult = np.random.choice(self.model.width_list)

            # 学生输出
            student_outputs = self.model(images, depth=depth, width_mult=width_mult)

            # 教师输出
            with torch.no_grad():
                teacher_outputs = teacher_model(images)

            # 蒸馏损失
            student_soft = F.log_softmax(student_outputs / temperature, dim=1)
            teacher_soft = F.softmax(teacher_outputs / temperature, dim=1)
            kl_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * (temperature ** 2)

            # 硬标签损失
            hard_loss = F.cross_entropy(student_outputs, labels)

            loss = alpha * hard_loss + (1 - alpha) * kl_loss

            total_loss += loss.item()

        return total_loss


class SubNetExtractor:
    """
    子网提取器

    从训练好的OFA超网中提取满足特定约束的子网
    """

    def __init__(self, ofa_model):
        self.ofa_model = ofa_model

    def extract(self, depth, width_mult):
        """
        提取子网

        参数:
            depth: 每层深度列表
            width_mult: 宽度缩放因子

        返回:
            subnet: 提取的子网（状态字典）
        """
        subnet = {}

        # 复制超网权重
        for name, param in self.ofa_model.named_parameters():
            subnet[name] = param.data.clone()

        return subnet

    def count_params(self, depth, width_mult):
        """计算子网参数量"""
        total = 0

        for name, module in self.ofa_model.named_modules():
            if isinstance(module, (ElasticConv2d, ElasticLinear)):
                in_ch = int(module.max_in_channels * width_mult)
                out_ch = int(module.max_out_channels * width_mult)

                if isinstance(module, ElasticConv2d):
                    total += out_ch * in_ch * module.kernel_size * module.kernel_size
                else:
                    total += out_ch * in_ch

        return total


def ofa_search_and_deploy():
    """OFA搜索和部署流程"""
    device = torch.device("cpu")

    print("=" * 50)
    print("Once-For-All网络")
    print("=" * 50)

    # 创建OFA网络
    ofa = OnceForAllNetwork(num_classes=10)

    # 统计超网大小
    total_params = sum(p.numel() for p in ofa.parameters())
    print(f"超网参数量: {total_params:,}")

    # 提取器
    extractor = SubNetExtractor(ofa)

    # 不同的子网配置
    configs = [
        ([2, 2, 3, 2], 1.0),
        ([4, 4, 4, 4], 1.0),
        ([2, 2, 2, 2], 0.65),
        ([4, 3, 2, 2], 0.8),
    ]

    print("\n子网参数量:")
    for depth, width_mult in configs:
        params = extractor.count_params(depth, width_mult)
        print(f"  depth={depth}, width={width_mult}: {params:,} params ({params / 1e6:.2f}M)")

    # 测试前向传播
    print("\n前向传播测试:")
    test_input = torch.rand(2, 3, 32, 32).to(device)

    for depth, width_mult in configs[:2]:
        output = ofa(test_input, depth=depth, width_mult=width_mult)
        print(f"  depth={depth}, width={width_mult}: output shape={output.shape}")

    return ofa


if __name__ == "__main__":
    ofa_search_and_deploy()
    print("\n测试完成！")

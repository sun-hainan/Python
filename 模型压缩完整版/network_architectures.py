# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / network_architectures



本文件实现 network_architectures 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class ResidualBlock(nn.Module):

    """

    标准残差块



    y = F(x) + x

    其中F是学习到的残差映射

    """



    def __init__(self, in_channels, out_channels, stride=1):

        super().__init__()



        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False)

        self.bn1 = nn.BatchNorm2d(out_channels)

        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False)

        self.bn2 = nn.BatchNorm2d(out_channels)



        # 下采样残差（当维度不匹配时）

        if stride != 1 or in_channels != out_channels:

            self.shortcut = nn.Sequential(

                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),

                nn.BatchNorm2d(out_channels)

            )

        else:

            self.shortcut = nn.Identity()



    def forward(self, x):

        identity = self.shortcut(x)



        out = F.relu(self.bn1(self.conv1(x)))

        out = self.bn2(self.conv2(out))



        out += identity

        out = F.relu(out)



        return out





class BottleneckBlock(nn.Module):

    """

    Bottleneck残差块



    1x1 -> 3x3 -> 1x1

    减少3x3卷积的计算量

    """



    def __init__(self, in_channels, out_channels, stride=1, expansion=4):

        super().__init__()

        mid_channels = out_channels // expansion



        self.conv1 = nn.Conv2d(in_channels, mid_channels, 1, bias=False)

        self.bn1 = nn.BatchNorm2d(mid_channels)



        self.conv2 = nn.Conv2d(mid_channels, mid_channels, 3, stride=stride, padding=1, bias=False)

        self.bn2 = nn.BatchNorm2d(mid_channels)



        self.conv3 = nn.Conv2d(mid_channels, out_channels, 1, bias=False)

        self.bn3 = nn.BatchNorm2d(out_channels)



        if stride != 1 or in_channels != out_channels:

            self.shortcut = nn.Sequential(

                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),

                nn.BatchNorm2d(out_channels)

            )

        else:

            self.shortcut = nn.Identity()



    def forward(self, x):

        identity = self.shortcut(x)



        out = F.relu(self.bn1(self.conv1(x)))

        out = F.relu(self.bn2(self.conv2(out)))

        out = self.bn3(self.conv3(out))



        out += identity

        out = F.relu(out)



        return out





class ResNet(nn.Module):

    """

    ResNet主干网络



    使用残差连接的经典架构

    """



    def __init__(self, num_classes=10, block_type='bottleneck', layers=[3, 4, 6, 3]):

        super().__init__()



        # 初始卷积

        self.stem = nn.Sequential(

            nn.Conv2d(1, 64, 7, stride=2, padding=3, bias=False),

            nn.BatchNorm2d(64),

            nn.ReLU(inplace=True),

            nn.MaxPool2d(3, stride=2, padding=1)

        )



        # 残差阶段

        if block_type == 'bottleneck':

            block = BottleneckBlock

            channels = [256, 512, 1024, 2048]

        else:

            block = ResidualBlock

            channels = [64, 128, 256, 512]



        self.stage1 = self._make_stage(64, channels[0], layers[0], block, stride=1)

        self.stage2 = self._make_stage(channels[0], channels[1], layers[1], block, stride=2)

        self.stage3 = self._make_stage(channels[1], channels[2], layers[2], block, stride=2)

        self.stage4 = self._make_stage(channels[2], channels[3], layers[3], block, stride=2)



        # 分类器

        self.classifier = nn.Sequential(

            nn.AdaptiveAvgPool2d(1),

            nn.Flatten(),

            nn.Linear(channels[3], num_classes)

        )



        self._initialize_weights()



    def _make_stage(self, in_channels, out_channels, num_blocks, block, stride):

        strides = [stride] + [1] * (num_blocks - 1)

        blocks = []



        for s in strides:

            blocks.append(block(in_channels, out_channels, s))

            in_channels = out_channels



        return nn.Sequential(*blocks)



    def forward(self, x):

        x = self.stem(x)

        x = self.stage1(x)

        x = self.stage2(x)

        x = self.stage3(x)

        x = self.stage4(x)

        x = self.classifier(x)



        return x



    def _initialize_weights(self):

        for m in self.modules():

            if isinstance(m, nn.Conv2d):

                nn.init.kaiming_normal_(m.weight, mode='fan_out')

            elif isinstance(m, nn.BatchNorm2d):

                nn.init.ones_(m.weight)

                nn.init.zeros_(m.bias)





class DenseLayer(nn.Module):

    """

    DenseNet的稠密层



    每个层接收所有前面层的特征图作为输入

    """



    def __init__(self, in_channels, growth_rate):

        super().__init__()

        self.bn1 = nn.BatchNorm2d(in_channels)

        self.conv1 = nn.Conv2d(in_channels, 4 * growth_rate, 1, bias=False)

        self.bn2 = nn.BatchNorm2d(4 * growth_rate)

        self.conv2 = nn.Conv2d(4 * growth_rate, growth_rate, 3, padding=1, bias=False)



    def forward(self, x):

        # 拼接所有输入特征

        if isinstance(x, list):

            x = torch.cat(x, dim=1)



        out = self.conv1(F.relu(self.bn1(x)))

        out = self.conv2(F.relu(self.bn2(out)))



        return out





class TransitionBlock(nn.Module):

    """

    DenseNet的过渡层



    用于减少特征图数量和尺寸

    """



    def __init__(self, in_channels, out_channels):

        super().__init__()

        self.bn = nn.BatchNorm2d(in_channels)

        self.conv = nn.Conv2d(in_channels, out_channels, 1, bias=False)

        self.pool = nn.AvgPool2d(2, stride=2)



    def forward(self, x):

        if isinstance(x, list):

            x = torch.cat(x, dim=1)



        out = self.conv(F.relu(self.bn(x)))

        out = self.pool(out)



        return out





class DenseBlock(nn.Module):

    """

    稠密块



    包含多个稠密层，每层输出添加到特征列表中

    """



    def __init__(self, in_channels, num_layers, growth_rate):

        super().__init__()

        self.layers = nn.ModuleList()



        for i in range(num_layers):

            layer = DenseLayer(in_channels + i * growth_rate, growth_rate)

            self.layers.append(layer)



    def forward(self, x):

        features = [x]



        for layer in self.layers:

            new_feature = layer(features)

            features.append(new_feature)



        return torch.cat(features, dim=1)





class DenseNet(nn.Module):

    """

    DenseNet



    使用稠密连接模式的神经网络

    每个层直接连接所有前面的层

    """



    def __init__(self, num_classes=10, growth_rate=32, block_config=(6, 12, 24, 16)):

        super().__init__()



        # 初始卷积

        self.stem = nn.Sequential(

            nn.Conv2d(1, 64, 7, stride=2, padding=3, bias=False),

            nn.BatchNorm2d(64),

            nn.ReLU(inplace=True),

            nn.MaxPool2d(3, stride=2, padding=1)

        )



        # 稠密块和过渡层

        num_features = 64

        self.dense_blocks = nn.ModuleList()

        self.transitions = nn.ModuleList()



        for i, num_layers in enumerate(block_config):

            # 稠密块

            block = DenseBlock(num_features, num_layers, growth_rate)

            self.dense_blocks.append(block)

            num_features = num_features + num_layers * growth_rate



            # 过渡层（除了最后一个稠密块）

            if i < len(block_config) - 1:

                out_features = num_features // 2

                trans = TransitionBlock(num_features, out_features)

                self.transitions.append(trans)

                num_features = out_features

            else:

                self.transitions.append(nn.Identity())



        # 最终归一化和分类器

        self.final_bn = nn.BatchNorm2d(num_features)

        self.classifier = nn.Sequential(

            nn.AdaptiveAvgPool2d(1),

            nn.Flatten(),

            nn.Linear(num_features, num_classes)

        )



        self._initialize_weights()



    def forward(self, x):

        x = self.stem(x)



        for block, trans in zip(self.dense_blocks, self.transitions):

            x = block(x)

            x = trans(x)



        x = F.relu(self.final_bn(x))

        x = self.classifier(x)



        return x



    def _initialize_weights(self):

        for m in self.modules():

            if isinstance(m, nn.Conv2d):

                nn.init.kaiming_normal_(m.weight, mode='fan_out')

            elif isinstance(m, nn.BatchNorm2d):

                nn.init.ones_(m.weight)

                nn.init.zeros_(m.bias)





class SEBlock(nn.Module):

    """

    Squeeze-and-Excitation Block



    通道注意力机制

    """



    def __init__(self, channels, reduction=16):

        super().__init__()

        self.squeeze = nn.AdaptiveAvgPool2d(1)

        self.excitation = nn.Sequential(

            nn.Linear(channels, channels // reduction, bias=False),

            nn.ReLU(inplace=True),

            nn.Linear(channels // reduction, channels, bias=False),

            nn.Sigmoid()

        )



    def forward(self, x):

        b, c, _, _ = x.shape

        y = self.squeeze(x).view(b, c)

        y = self.excitation(y).view(b, c, 1, 1)

        return x * y





class SEResidualBlock(nn.Module):

    """

    SE残差块



    将SE机制集成到残差块中

    """



    def __init__(self, in_channels, out_channels, stride=1, reduction=16):

        super().__init__()



        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False)

        self.bn1 = nn.BatchNorm2d(out_channels)

        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False)

        self.bn2 = nn.BatchNorm2d(out_channels)



        self.se = SEBlock(out_channels, reduction)



        if stride != 1 or in_channels != out_channels:

            self.shortcut = nn.Sequential(

                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),

                nn.BatchNorm2d(out_channels)

            )

        else:

            self.shortcut = nn.Identity()



    def forward(self, x):

        identity = self.shortcut(x)



        out = F.relu(self.bn1(self.conv1(x)))

        out = self.bn2(self.conv2(out))

        out = self.se(out)



        out += identity

        out = F.relu(out)



        return out





class EfficientNetBlock(nn.Module):

    """

    EfficientNet的基础块



    深度可分离卷积 + SE + 残差连接

    """



    def __init__(self, in_channels, out_channels, stride=1, expand_ratio=6, reduction=4):

        super().__init__()

        mid_channels = in_channels * expand_ratio

        self.use_residual = (stride == 1 and in_channels == out_channels)



        # Pointwise + Depthwise + SE

        self.conv1 = nn.Conv2d(in_channels, mid_channels, 1, bias=False)

        self.bn1 = nn.BatchNorm2d(mid_channels)



        self.dwconv = nn.Conv2d(mid_channels, mid_channels, 3, stride=stride,

                                padding=1, groups=mid_channels, bias=False)

        self.bn2 = nn.BatchNorm2d(mid_channels)



        self.se = SEBlock(mid_channels, reduction)



        self.conv2 = nn.Conv2d(mid_channels, out_channels, 1, bias=False)

        self.bn3 = nn.BatchNorm2d(out_channels)



    def forward(self, x):

        identity = x



        out = F.relu(self.bn1(self.conv1(x)))

        out = F.relu(self.bn2(self.dwconv(out)))

        out = self.se(out)

        out = self.bn3(self.conv2(out))



        if self.use_residual:

            out = out + identity



        return out





def count_parameters(model):

    """计算参数量"""

    return sum(p.numel() for p in model.parameters())





def compute_flops(model, input_shape=(1, 1, 32, 32)):

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





if __name__ == "__main__":

    print("=" * 50)

    print("神经网络架构设计测试")

    print("=" * 50)



    device = torch.device("cpu")

    input_shape = (1, 1, 32, 32)



    # ResNet

    print("\n--- ResNet ---")

    resnet = ResNet(num_classes=10, block_type='basic', layers=[2, 2, 2, 2])

    params = count_parameters(resnet)

    print(f"参数量: {params:,} ({params / 1e6:.2f}M)")

    print(f"FLOPs: {compute_flops(resnet, input_shape):,}")



    # DenseNet

    print("\n--- DenseNet ---")

    densenet = DenseNet(num_classes=10, growth_rate=24, block_config=(4, 8, 16, 8))

    params = count_parameters(densenet)

    print(f"参数量: {params:,} ({params / 1e6:.2f}M)")

    print(f"FLOPs: {compute_flops(densenet, input_shape):,}")



    # 测试前向传播

    print("\n--- 前向传播测试 ---")

    test_input = torch.rand(2, 1, 32, 32).to(device)



    for name, model in [("ResNet", resnet), ("DenseNet", densenet)]:

        model.eval()

        with torch.no_grad():

            output = model(test_input)

            print(f"{name}: output shape={output.shape}")



    # SE Block

    print("\n--- SE Block ---")

    se = SEBlock(channels=64)

    test_feat = torch.rand(2, 64, 8, 8)

    se_out = se(test_feat)

    print(f"SE输入形状: {test_feat.shape}, 输出形状: {se_out.shape}")



    # EfficientNet块

    print("\n--- EfficientNet Block ---")

    eff_block = EfficientNetBlock(32, 64, stride=1)

    test_input = torch.rand(2, 32, 16, 16)

    output = eff_block(test_input)

    print(f"EfficientNet输入: {test_input.shape}, 输出: {output.shape}")



    print("\n测试完成！")


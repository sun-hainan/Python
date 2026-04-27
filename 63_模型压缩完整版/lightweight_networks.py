# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / lightweight_networks



本文件实现 lightweight_networks 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class DepthwiseSeparableConv(nn.Module):

    """

    深度可分离卷积（Depthwise Separable Convolution）



    将标准卷积分解为：

    1. 深度卷积（逐通道）：每个通道独立卷积

    2. 逐点卷积（1x1）：混合通道信息



    计算量：DK * DK * M * D_out + M * N * D_out

    标准卷积：DK * DK * M * N * D_out

    加速比：1/N + 1/(DK^2)

    """



    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):

        super().__init__()

        self.depthwise = nn.Conv2d(

            in_channels, in_channels, kernel_size,

            stride=stride, padding=padding, groups=in_channels  # 深度卷积

        )

        self.pointwise = nn.Conv2d(

            in_channels, out_channels, kernel_size=1  # 逐点卷积

        )



    def forward(self, x):

        x = self.depthwise(x)

        x = self.pointwise(x)

        return x





class MobileNetV1Block(nn.Module):

    """

    MobileNetV1的基本模块

    """



    def __init__(self, in_channels, out_channels, stride=1):

        super().__init__()

        self.conv = DepthwiseSeparableConv(in_channels, out_channels, stride=stride)

        self.bn1 = nn.BatchNorm2d(out_channels)

        self.relu = nn.ReLU(inplace=True)



        # 如果 stride=1 且通道不变，不需要残差连接

        self.use_residual = stride == 1 and in_channels == out_channels



    def forward(self, x):

        out = self.relu(self.bn1(self.conv(x)))



        if self.use_residual:

            return x + out

        else:

            return out





class MobileNetV1(nn.Module):

    """

    MobileNetV1



    第一个大规模商用的轻量化网络

    使用深度可分离卷积替代标准卷积

    """



    def __init__(self, num_classes=10, width_mult=1.0):

        super().__init__()

        self.width_mult = width_mult



        # 初始卷积

        self.initial = nn.Sequential(

            nn.Conv2d(1, int(32 * width_mult), kernel_size=3, stride=2, padding=1),

            nn.BatchNorm2d(int(32 * width_mult)),

            nn.ReLU(inplace=True)

        )



        # MobileNet块

        self.features = nn.Sequential(

            MobileNetV1Block(int(32 * width_mult), int(64 * width_mult)),

            MobileNetV1Block(int(64 * width_mult), int(128 * width_mult), stride=2),

            MobileNetV1Block(int(128 * width_mult), int(128 * width_mult)),

            MobileNetV1Block(int(128 * width_mult), int(256 * width_mult), stride=2),

            MobileNetV1Block(int(256 * width_mult), int(256 * width_mult)),

            MobileNetV1Block(int(256 * width_mult), int(512 * width_mult), stride=2),

            MobileNetV1Block(int(512 * width_mult), int(512 * width_mult)),

            MobileNetV1Block(int(512 * width_mult), int(512 * width_mult)),

            MobileNetV1Block(int(512 * width_mult), int(512 * width_mult)),

            MobileNetV1Block(int(512 * width_mult), int(512 * width_mult)),

            MobileNetV1Block(int(512 * width_mult), int(1024 * width_mult), stride=2),

            MobileNetV1Block(int(1024 * width_mult), int(1024 * width_mult)),

        )



        # 全局池化和分类器

        self.avgpool = nn.AdaptiveAvgPool2d(1)

        self.classifier = nn.Sequential(

            nn.Dropout(0.2),

            nn.Linear(int(1024 * width_mult), num_classes)

        )



    def forward(self, x):

        x = self.initial(x)

        x = self.features(x)

        x = self.avgpool(x)

        x = x.view(x.size(0), -1)

        x = self.classifier(x)

        return x





class FireModule(nn.Module):

    """

    SqueezeNet的Fire模块



    包含squeeze层（压缩）和expand层（扩展）

    squeeze: 1x1卷积减少通道数

    expand: 1x1 + 3x3卷积混合

    """



    def __init__(self, in_channels, squeeze_channels, expand_channels):

        super().__init__()

        self.squeeze = nn.Conv2d(in_channels, squeeze_channels, kernel_size=1)

        self.squeeze_bn = nn.BatchNorm2d(squeeze_channels)

        self.squeeze_relu = nn.ReLU(inplace=True)



        self.expand_1x1 = nn.Conv2d(squeeze_channels, expand_channels, kernel_size=1)

        self.expand_3x3 = nn.Conv2d(squeeze_channels, expand_channels, kernel_size=3, padding=1)



        self.expand_bn = nn.BatchNorm2d(expand_channels * 2)

        self.expand_relu = nn.ReLU(inplace=True)



    def forward(self, x):

        x = self.squeeze_relu(self.squeeze_bn(self.squeeze(x)))



        expand_1x1 = self.expand_1x1(x)

        expand_3x3 = self.expand_3x3(x)



        # 拼接两个分支

        x = torch.cat([expand_1x1, expand_3x3], dim=1)

        x = self.expand_relu(self.expand_bn(x))



        return x





class SqueezeNet(nn.Module):

    """

    SqueezeNet



    使用Fire模块和延迟下采样实现高效

    参数量比AlexNet少50倍，达到类似准确率

    """



    def __init__(self, num_classes=10):

        super().__init__()

        self.initial = nn.Sequential(

            nn.Conv2d(1, 96, kernel_size=7, stride=2, padding=3),

            nn.BatchNorm2d(96),

            nn.ReLU(inplace=True),

            nn.MaxPool2d(kernel_size=3, stride=2, ceil_mode=True)

        )



        self.fire2 = FireModule(96, 16, 64)

        self.fire3 = FireModule(128, 32, 128)

        self.fire4 = FireModule(256, 32, 128)

        self.fire5 = FireModule(256, 48, 192)

        self.fire6 = FireModule(384, 48, 192)

        self.fire7 = FireModule(384, 64, 256)

        self.fire8 = FireModule(512, 64, 256)



        self.final_conv = nn.Conv2d(512, num_classes, kernel_size=1)

        self.avgpool = nn.AdaptiveAvgPool2d(1)



    def forward(self, x):

        x = self.initial(x)



        x = self.fire2(x)

        x = self.fire3(x)

        x = self.fire4(x)

        x = self.fire5(x)

        x = self.fire6(x)

        x = self.fire7(x)

        x = self.fire8(x)



        x = self.final_conv(x)

        x = self.avgpool(x)

        x = x.view(x.size(0), -1)



        return x





class ChannelShuffle(nn.Module):

    """

    通道重排（Channel Shuffle）



    将通道分成组并重排，增强组间信息流动

    """



    def __init__(self, num_groups, num_channels):

        super().__init__()

        self.num_groups = num_groups

        self.num_channels = num_channels



        # 确保通道数可以被组数整除

        assert num_channels % num_groups == 0



    def forward(self, x):

        B, C, H, W = x.shape

        channels_per_group = C // self.num_groups



        # reshape: [B, C, H, W] -> [B, num_groups, channels_per_group, H, W]

        x = x.view(B, self.num_groups, channels_per_group, H, W)

        # transpose: 交换组和通道维度

        x = x.transpose(1, 2)

        # flatten: [B, C, H, W]

        x = x.contiguous().view(B, C, H, W)



        return x





class ShuffleNetUnit(nn.Module):

    """

    ShuffleNet的基本单元

    """



    def __init__(self, in_channels, out_channels, stride=1, num_groups=3):

        super().__init__()

        self.num_groups = num_groups

        self.stride = stride



        # 压缩通道

        mid_channels = out_channels // 4 if out_channels > 24 else out_channels



        # GConv1: 1x1卷积（分组） + BN + ReLU

        self.gconv1 = nn.Conv2d(in_channels, mid_channels, kernel_size=1, groups=num_groups)

        self.bn1 = nn.BatchNorm2d(mid_channels)

        self.relu = nn.ReLU(inplace=True)



        # 通道重排

        self.channel_shuffle = ChannelShuffle(num_groups, mid_channels)



        # DWConv: 深度卷积

        self.dwconv = nn.Conv2d(mid_channels, mid_channels, kernel_size=3,

                               stride=stride, padding=1, groups=mid_channels)

        self.dwconv_bn = nn.BatchNorm2d(mid_channels)



        # GConv2: 1x1卷积（分组）

        self.gconv2 = nn.Conv2d(mid_channels, out_channels, kernel_size=1, groups=num_groups)

        self.bn2 = nn.BatchNorm2d(out_channels)



        # 残差连接（如果stride=1）

        self.use_residual = stride == 1 and in_channels == out_channels



    def forward(self, x):

        residual = x



        x = self.relu(self.bn1(self.gconv1(x)))

        x = self.channel_shuffle(x)

        x = self.dwconv_bn(self.dwconv(x))

        x = self.bn2(self.gconv2(x))



        if self.use_residual:

            x = x + residual

        else:

            # 下采样时对残差也做下采样

            residual = F.avg_pool2d(residual, kernel_size=3, stride=self.stride, padding=1)

            x = torch.cat([x, residual], dim=1)



        x = self.relu(x)

        return x





class ShuffleNet(nn.Module):

    """

    ShuffleNet



    使用通道重排和分组卷积实现高效

    适合移动端部署

    """



    def __init__(self, num_classes=10, num_groups=3, width_mult=1.0):

        super().__init__()

        self.num_groups = num_groups



        # 初始层

        self.initial = nn.Sequential(

            nn.Conv2d(1, int(24 * width_mult), kernel_size=3, stride=2, padding=1),

            nn.BatchNorm2d(int(24 * width_mult)),

            nn.ReLU(inplace=True),

            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        )



        # Stage定义: (out_channels, num_blocks, stride)

        stages = [

            (int(240 * width_mult), 4, 2),

            (int(480 * width_mult), 8, 2),

            (int(960 * width_mult), 4, 2)

        ]



        layers = []

        in_channels = int(24 * width_mult)



        for out_channels, num_blocks, stride in stages:

            layers.append(ShuffleNetUnit(in_channels, out_channels, stride, num_groups))

            in_channels = out_channels



            for _ in range(num_blocks - 1):

                layers.append(ShuffleNetUnit(in_channels, out_channels, 1, num_groups))



        self.features = nn.Sequential(*layers)

        self.avgpool = nn.AdaptiveAvgPool2d(1)



        self.classifier = nn.Linear(int(960 * width_mult), num_classes)



    def forward(self, x):

        x = self.initial(x)

        x = self.features(x)

        x = self.avgpool(x)

        x = x.view(x.size(0), -1)

        x = self.classifier(x)

        return x





def count_parameters(model):

    """计算模型参数量"""

    return sum(p.numel() for p in model.parameters())





def compute_flops(module, input_shape):

    """估算FLOPs（简化版）"""

    total = 0

    for name, m in module.named_modules():

        if isinstance(m, nn.Conv2d):

            h, w = input_shape[2], input_shape[3]

            out_h = (h + 2 * m.padding[0] - m.kernel_size[0]) // m.stride[0] + 1

            out_w = (w + 2 * m.padding[1] - m.kernel_size[1]) // m.stride[1] + 1

            flops = m.in_channels * m.out_channels * m.kernel_size[0] * m.kernel_size[1] * out_h * out_w

            total += flops

            input_shape = (1, m.out_channels, out_h, out_w)

        elif isinstance(m, nn.Linear):

            total += m.in_features * m.out_features

            input_shape = (1, m.out_features)

    return total





if __name__ == "__main__":

    print("=" * 50)

    print("轻量化网络测试")

    print("=" * 50)



    device = torch.device("cpu")

    input_shape = (1, 1, 28, 28)



    # MobileNetV1

    print("\n--- MobileNetV1 ---")

    mobilenet = MobileNetV1(num_classes=10, width_mult=0.5).to(device)

    params = count_parameters(mobilenet)

    print(f"参数量: {params:,} ({params / 1e6:.2f}M)")

    print(f"FLOPs估算: {compute_flops(mobilenet, input_shape):,}")



    # SqueezeNet

    print("\n--- SqueezeNet ---")

    squeezenet = SqueezeNet(num_classes=10).to(device)

    params = count_parameters(squeezenet)

    print(f"参数量: {params:,} ({params / 1e6:.2f}M)")

    print(f"FLOPs估算: {compute_flops(squeezenet, input_shape):,}")



    # ShuffleNet

    print("\n--- ShuffleNet ---")

    shufflenet = ShuffleNet(num_classes=10, num_groups=3, width_mult=0.5).to(device)

    params = count_parameters(shufflenet)

    print(f"参数量: {params:,} ({params / 1e6:.2f}M)")

    print(f"FLOPs估算: {compute_flops(shufflenet, input_shape):,}")



    # 对比标准CNN

    print("\n--- 标准CNN对比 ---")

    class StandardCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.conv3 = nn.Conv2d(64, 128, 3, padding=1)

            self.conv4 = nn.Conv2d(128, 256, 3, padding=1)

            self.fc1 = nn.Linear(256 * 1 * 1, 256)

            self.fc2 = nn.Linear(256, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = F.relu(F.max_pool2d(self.conv3(x), 2))

            x = F.relu(F.max_pool2d(self.conv4(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    standard = StandardCNN(num_classes=10).to(device)

    params = count_parameters(standard)

    print(f"标准CNN参数量: {params:,} ({params / 1e6:.2f}M)")



    # 前向传播测试

    print("\n--- 前向传播测试 ---")

    test_input = torch.rand(4, 1, 28, 28).to(device)



    for name, model in [("MobileNet", mobilenet), ("SqueezeNet", squeezenet),

                        ("ShuffleNet", shufflenet), ("StandardCNN", standard)]:

        model.eval()

        with torch.no_grad():

            output = model(test_input)

            print(f"{name}: output shape={output.shape}")



    print("\n测试完成！")


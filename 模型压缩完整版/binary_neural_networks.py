# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / binary_neural_networks



本文件实现 binary_neural_networks 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class BinarySign(torch.autograd.Function):

    """

    二值化符号函数



    前向：sign(x) -> {-1, +1}

    反向：Straight-Through Estimator (STE)

    """



    @staticmethod

    def forward(ctx, input, threshold=0.0):

        """前向：二值化"""

        return torch.sign(input - threshold)



    @staticmethod

    def backward(ctx, grad_output):

        """反向：STE"""

        # 截断梯度

        grad_input = grad_output.clone()

        grad_input[input.abs() > 1.0] = 0

        return grad_input, None





class BinaryWeight(torch.autograd.Function):

    """

    二值化权重函数



    将权重二值化，但保持梯度的精确传递

    """



    @staticmethod

    def forward(ctx, weight):

        """前向：二值化权重"""

        return torch.sign(weight)



    @staticmethod

    def backward(ctx, grad_output):

        """反向：裁剪后的梯度"""

        return grad_output





class BinaryConv2d(nn.Module):

    """

    二值化卷积层



    权重和激活都是二值的

    """



    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0):

        super().__init__()

        self.in_channels = in_channels

        self.out_channels = out_channels

        self.kernel_size = kernel_size

        self.stride = stride

        self.padding = padding



        # 浮点权重

        self.weight = nn.Parameter(torch.randn(out_channels, in_channels, kernel_size, kernel_size))

        # 学习缩放因子

        self.alpha = nn.Parameter(torch.ones(1))



        self._initialize_weights()



    def _initialize_weights(self):

        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')



    def forward(self, x):

        # 二值化权重

        binary_weight = torch.sign(self.weight)



        # 二值化激活（简化：使用sign）

        binary_x = torch.sign(x)



        # XNOR卷积：使用位运算模拟

        # 实际实现中需要popcount和位操作

        output = F.conv2d(binary_x, binary_weight, stride=self.stride, padding=self.padding)



        # 应用缩放因子

        output = output * self.alpha



        return output





class BinaryLinear(nn.Module):

    """

    二值化全连接层

    """



    def __init__(self, in_features, out_features):

        super().__init__()

        self.in_features = in_features

        self.out_features = out_features



        self.weight = nn.Parameter(torch.randn(out_features, in_features))

        self.alpha = nn.Parameter(torch.ones(1))



        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')



    def forward(self, x):

        # 二值化

        binary_weight = torch.sign(self.weight)

        binary_x = torch.sign(x)



        # XNOR矩阵乘法

        output = F.linear(binary_x, binary_weight)



        return output * self.alpha





class StraightThroughEstimator(nn.Module):

    """

    使用STE的近似二值化



    前向用sign，反向用恒等

    """



    def __init__(self):

        super().__init__()



    def forward(self, x):

        # STE: forward = sign, backward = identity

        return BinarySign.apply(x, 0.0)





class BatchNormBinary(nn.Module):

    """

    二值化批归一化



    在二值化卷积之间使用

    """



    def __init__(self, num_features, momentum=0.1):

        super().__init__()

        self.bn = nn.BatchNorm2d(num_features, momentum=momentum)



    def forward(self, x):

        return self.bn(x)





class BinarizedNeuralNetwork(nn.Module):

    """

    完整的二值化神经网络



    结合XNOR-Net的思想，使用缩放因子

    """



    def __init__(self, num_classes=10):

        super().__init__()



        self.features = nn.Sequential(

            # Block 1

            nn.Conv2d(1, 32, kernel_size=3, padding=1),

            nn.BatchNorm2d(32),

            StraightThroughEstimator(),

            BinaryConv2d(32, 32, kernel_size=3, padding=1),

            nn.MaxPool2d(2),



            # Block 2

            nn.BatchNorm2d(32),

            StraightThroughEstimator(),

            BinaryConv2d(32, 64, kernel_size=3, padding=1),

            nn.MaxPool2d(2),



            # Block 3

            nn.BatchNorm2d(64),

            StraightThroughEstimator(),

            BinaryConv2d(64, 128, kernel_size=3, padding=1),

        )



        self.avgpool = nn.AdaptiveAvgPool2d(1)



        self.classifier = nn.Sequential(

            nn.Linear(128, num_classes)

        )



    def forward(self, x):

        x = self.features(x)

        x = self.avgpool(x)

        x = x.view(x.size(0), -1)

        x = self.classifier(x)

        return x





class XNORNetBlock(nn.Module):

    """

    XNOR-Net的基本模块



    包含：

    1. 二值化权重

    2. 二值化激活

    3. 缩放因子

    """



    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):

        super().__init__()



        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride=stride, padding=padding)



        # 缩放因子

        self.alpha = nn.Parameter(torch.ones(1))



    def compute_binary_weight(self):

        """计算二值化权重及缩放因子"""

        E = torch.abs(self.conv.weight).mean(dim=(1, 2, 3), keepdim=True)

        binary_weight = torch.sign(self.conv.weight)

        self.alpha.data = E.squeeze()

        return binary_weight



    def forward(self, x):

        binary_weight = self.compute_binary_weight()

        binary_input = torch.sign(x)



        # XNOR卷积

        output = F.conv2d(binary_input, binary_weight, stride=self.conv.stride, padding=self.conv.padding)



        return output * self.alpha





class DoReFaQuantization(nn.Module):

    """

    DoReFa-Net量化



    使用不同的位宽量化权重、激活和梯度

    """



    def __init__(self, num_bits=1):

        super().__init__()

        self.num_bits = num_bits



    def forward(self, x):

        if self.num_bits == 1:

            # 二值化

            return torch.sign(x)

        else:

            # 多位量化

            # 映射到[0, 1]

            x_clamped = torch.clamp(x, 0, 1)

            # 量化

            scale = 2 ** self.num_bits - 1

            x_quantized = torch.round(x_clamped * scale) / scale

            return x_quantized





class BNNTrainer:

    """

    二值化网络训练器

    """



    def __init__(self, model, device='cpu', lr=0.01):

        self.model = model

        self.device = device

        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)



    def train_step(self, images, labels):

        """训练步骤"""

        self.model.train()



        # 前向传播

        outputs = self.model(images)

        loss = F.cross_entropy(outputs, labels)



        # 反向传播

        self.optimizer.zero_grad()

        loss.backward()

        self.optimizer.step()



        return loss.item()



    def evaluate(self, images, labels):

        """评估"""

        self.model.eval()

        with torch.no_grad():

            outputs = self.model(images)

            preds = torch.argmax(outputs, dim=1)

            acc = (preds == labels).float().mean()



        return acc.item()





class StraightThroughGradientEstimator:

    """

    梯度截断的STE



    避免过大的梯度导致训练不稳定

    """



    def __init__(self, clip_value=1.0):

        self.clip_value = clip_value



    def __call__(self, x):

        # STE with gradient clipping

        return BinarySign.apply(x, 0.0)





def binarize_weights(weight, method='sign'):

    """

    将权重二值化



    参数:

        weight: 浮点权重

        method: 二值化方法 ('sign', 'stochastic')

    """

    if method == 'sign':

        return torch.sign(weight)

    elif method == 'stochastic':

        # 随机二值化

        p = (weight - weight.min()) / (weight.max() - weight.min() + 1e-8)

        mask = torch.bernoulli(p)

        return mask * 2 - 1

    else:

        raise ValueError(f"Unknown method: {method}")





def compute_bnn_compression_ratio(model):

    """

    计算二值化网络的压缩比



    假设浮点32位 -> 二值1位

    """

    total_params = 0

    binary_params = 0



    for name, module in model.named_modules():

        if isinstance(module, (BinaryConv2d, BinaryLinear)):

            total_params += module.weight.numel() * 32  # 浮点位

            binary_params += module.weight.numel() * 1  # 二值位



    return total_params / binary_params if binary_params > 0 else 1.0





if __name__ == "__main__":

    print("=" * 50)

    print("神经网络二值化（BNN/XNOR-Net）测试")

    print("=" * 50)



    device = torch.device("cpu")



    # 创建二值化网络

    bnn = BinarizedNeuralNetwork(num_classes=10).to(device)



    # 统计参数量

    total_params = sum(p.numel() for p in bnn.parameters())

    binary_params = 0

    for m in bnn.modules():

        if isinstance(m, (BinaryConv2d, BinaryLinear)):

            binary_params += m.weight.numel()



    print(f"\n--- 参数量统计 ---")

    print(f"总参数量: {total_params:,}")

    print(f"二值化参数: {binary_params:,}")

    print(f"压缩比: {total_params / binary_params:.2f}x")



    # 测试前向传播

    print("\n--- 前向传播测试 ---")

    test_input = torch.rand(4, 1, 28, 28).to(device)

    test_labels = torch.randint(0, 10, (4,)).to(device)



    # 训练几步

    trainer = BNNTrainer(bnn, device, lr=0.001)



    for epoch in range(5):

        loss = trainer.train_step(test_input, test_labels)

        if (epoch + 1) % 2 == 0:

            acc = trainer.evaluate(test_input, test_labels)

            print(f"Epoch {epoch + 1}: Loss={loss:.4f}, Acc={acc:.2%}")



    # 测试XNOR-Net块

    print("\n--- XNOR-Net块测试 ---")

    xnor_block = XNORNetBlock(1, 32).to(device)

    test_input = torch.randn(2, 1, 8, 8)

    output = xnor_block(test_input)

    print(f"输入形状: {test_input.shape}")

    print(f"输出形状: {output.shape}")

    print(f"缩放因子alpha: {xnor_block.alpha.item():.4f}")



    # DoReFa量化

    print("\n--- DoReFa量化 ---")

    for num_bits in [1, 2, 4, 8]:

        quant = DoReFaQuantization(num_bits=num_bits)

        test_data = torch.rand(4, 8) * 2 - 1  # [-1, 1]

        quantized = quant(test_data)

        unique_vals = len(quantized.unique())

        print(f"  {num_bits}位量化: 唯一值数={unique_vals}")



    # 权重二值化方法对比

    print("\n--- 权重二值化方法对比 ---")

    weight = torch.randn(32, 32)



    binary_sign = binarize_weights(weight, method='sign')

    binary_stoch = binarize_weights(weight, method='stochastic')



    print(f"Sign方法唯一值: {binary_sign.unique().tolist()}")

    print(f"Stochastic方法唯一值: {binary_stoch.unique().tolist()}")



    print("\n测试完成！")


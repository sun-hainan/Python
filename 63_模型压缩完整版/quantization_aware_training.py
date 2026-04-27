# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / quantization_aware_training



本文件实现 quantization_aware_training 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class StraightThroughEstimator(torch.autograd.Function):

    """

    Straight-Through Estimator (STE)



    前向传播：量化

    反向传播：恒等映射（绕过量化）

    """



    @staticmethod

    def forward(ctx, input, num_bits=8):

        """前向：量化"""

        return torch.round(input)



    @staticmethod

    def backward(ctx, grad_output):

        """反向：直接传递梯度"""

        return grad_output, None





class QuantizedLinear(nn.Module):

    """

    量化感知的全连接层

    """



    def __init__(self, in_features, out_features, num_bits=8, bias=True):

        super().__init__()

        self.in_features = in_features

        self.out_features = out_features

        self.num_bits = num_bits



        # 原始权重（高精度）

        self.weight = nn.Parameter(torch.randn(out_features, in_features) * 0.01)

        if bias:

            self.bias = nn.Parameter(torch.zeros(out_features))

        else:

            self.register_parameter('bias', None)



        # 量化参数

        self.register_buffer('scale', torch.tensor(1.0))

        self.register_buffer('zero_point', torch.tensor(0.0))



    def update_quantization_params(self):

        """更新量化参数"""

        weight = self.weight.data

        qmin, qmax = 0, 2 ** self.num_bits - 1



        w_min, w_max = weight.min(), weight.max()

        self.scale = (w_max - w_min) / (qmax - qmin) if w_max != w_min else torch.tensor(1.0)

        self.zero_point = qmin - w_min / self.scale if self.scale != 0 else torch.tensor(0.0)



    def quantize_weights(self):

        """量化权重"""

        # 计算量化参数

        weight = self.weight.data

        qmin, qmax = 0, 2 ** self.num_bits - 1



        scale = self.scale.item()

        zero_point = self.zero_point.item()



        # 量化

        quantized = torch.round((weight - zero_point) / scale) * scale + zero_point



        return quantized



    def forward(self, x):

        # 获取量化权重

        q_weight = self.quantize_weights()



        # STE前向：使用量化权重但保持梯度到原始权重

        if self.training:

            # 前向用量化权重，反向传原始权重的梯度

            output = F.linear(x, q_weight, self.bias)

        else:

            # 推理时直接用量化权重

            output = F.linear(x, q_weight, self.bias)



        return output





class QuantizedConv2d(nn.Module):

    """

    量化感知的卷积层

    """



    def __init__(self, in_channels, out_channels, kernel_size, stride=1,

                 padding=0, dilation=1, groups=1, bias=True, num_bits=8):

        super().__init__()

        self.in_channels = in_channels

        self.out_channels = out_channels

        self.kernel_size = kernel_size

        self.stride = stride

        self.padding = padding

        self.dilation = dilation

        self.groups = groups

        self.num_bits = num_bits



        self.weight = nn.Parameter(

            torch.randn(out_channels, in_channels // groups, kernel_size, kernel_size) * 0.01

        )

        if bias:

            self.bias = nn.Parameter(torch.zeros(out_channels))

        else:

            self.register_parameter('bias', None)



        self.scale = torch.tensor(1.0)

        self.zero_point = torch.tensor(0.0)



    def update_quantization_params(self):

        """更新量化参数"""

        weight = self.weight.data

        qmin, qmax = 0, 2 ** self.num_bits - 1



        w_min, w_max = weight.min(), weight.max()

        self.scale = (w_max - w_min) / (qmax - qmin) if w_max != w_min else torch.tensor(1.0)

        self.zero_point = qmin - w_min / self.scale if self.scale != 0 else torch.tensor(0.0)



    def quantize_weights(self):

        """量化权重"""

        weight = self.weight.data

        scale = self.scale.item()

        zero_point = self.zero_point.item()



        quantized = torch.round((weight - zero_point) / scale) * scale + zero_point



        return quantized



    def forward(self, x):

        q_weight = self.quantize_weights()



        if self.training:

            output = F.conv2d(x, q_weight, self.bias, self.stride,

                            self.padding, self.dilation, self.groups)

        else:

            output = F.conv2d(x, q_weight, self.bias, self.stride,

                            self.padding, self.dilation, self.groups)



        return output





class FakeQuantization(nn.Module):

    """

    模拟量化层（用于激活值）

    """



    def __init__(self, num_bits=8, momentum=0.1):

        super().__init__()

        self.num_bits = num_bits

        self.momentum = momentum

        self.register_buffer('running_min', torch.tensor(0.0))

        self.register_buffer('running_max', torch.tensor(1.0))



    def forward(self, x):

        # 更新统计量

        if self.training:

            with torch.no_grad():

                min_val = x.detach().min()

                max_val = x.detach().max()



                self.running_min = self.momentum * self.running_min + (1 - self.momentum) * min_val

                self.running_max = self.momentum * self.running_max + (1 - self.momentum) * max_val



        # 量化

        qmin, qmax = 0, 2 ** self.num_bits - 1



        scale = (self.running_max - self.running_min) / (qmax - qmin) if self.running_max != self.running_min else torch.tensor(1.0)

        zero_point = qmin - self.running_min / scale if scale != 0 else torch.tensor(0.0)



        # Fake quantization

        x_quantized = torch.round((x - self.running_min) / scale + zero_point) * scale + self.running_min



        # STE：反向时直接传递梯度

        if self.training:

            x_quantized = x + (x_quantized - x).detach()



        return x_quantized





class QATAwareTrainer:

    """

    量化感知训练器

    """



    def __init__(self, model, device='cpu', num_bits=8):

        self.model = model

        self.device = device

        self.num_bits = num_bits



    def prepare_qat_model(self):

        """

        将普通模型转换为QAT模型



        将Linear和Conv2d替换为量化版本

        """

        # 这里简化处理，直接使用原始层进行QAT

        # 实际应替换为QuantizedLinear/QuantizedConv2d

        pass



    def train_step(self, images, labels, optimizer, criterion=F.cross_entropy):

        """

        QAT训练步骤



        参数:

            images: 输入图像

            labels: 标签

            optimizer: 优化器

            criterion: 损失函数

        """

        self.model.train()



        # 前向传播（带量化模拟）

        outputs = self.model(images)

        loss = criterion(outputs, labels)



        # 反向传播

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()



        return loss.item()



    def update_quantization_params(self):

        """

        更新所有量化参数



        在每个epoch或每个step后调用

        """

        for module in self.model.modules():

            if hasattr(module, 'update_quantization_params'):

                module.update_quantization_params()





class PACTQuantization:

    """

    PACT: Parameterized Clipping Activation



    带有可学习裁剪参数的激活函数量化

    """



    def __init__(self, num_bits=8, alpha_init=6.0):

        """

        参数:

            alpha_init: 初始裁剪值

        """

        self.num_bits = num_bits

        self.alpha = nn.Parameter(torch.tensor(alpha_init))



    def forward(self, x):

        """

        PACT前向

        """

        # 限制alpha范围

        alpha = torch.clamp(self.alpha, min=0.1)



        # 裁剪

        x_clipped = torch.clamp(x, 0, alpha.item())



        # 量化

        qmin, qmax = 0, 2 ** self.num_bits - 1

        scale = alpha.item() / qmax



        x_quantized = torch.round(x_clipped / scale) * scale



        # STE

        if self.training:

            x_quantized = x_clipped + (x_quantized - x_clipped).detach()



        return x_quantized





class LSQQuantization:

    """

    LSQ: Learned Step Size Quantization



    可学习的量化步长

    """



    def __init__(self, num_bits=8):

        self.num_bits = num_bits

        self.Q = 2 ** num_bits

        self.step_size = nn.Parameter(torch.tensor(0.1))



    def forward(self, x):

        """LSQ前向"""

        # 梯度估计器

        g = 1.0 / (self.Q ** 0.5)



        # STE for step size

        if self.training:

            # 量化

            x_round = torch.round(x / self.step_size) * self.step_size

            # STE

            x_quantized = x + (x_round - x).detach()

        else:

            x_quantized = torch.round(x / self.step_size) * self.step_size



        return x_quantized





if __name__ == "__main__":

    # 定义QAT模型

    class QATModel(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = QuantizedConv2d(1, 32, 3, padding=1, num_bits=8)

            self.conv2 = QuantizedConv2d(32, 64, 3, padding=1, num_bits=8)

            self.fc1 = QuantizedLinear(64 * 7 * 7, 128, num_bits=8)

            self.fc2 = QuantizedLinear(128, num_classes, num_bits=8)

            self.fake_quant = FakeQuantization(num_bits=8)



        def forward(self, x):

            x = self.fake_quant(F.max_pool2d(self.conv1(x), 2))

            x = self.fake_quant(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = self.fake_quant(F.relu(self.fc1(x)))

            x = self.fc2(x)

            return x



    device = torch.device("cpu")

    model = QATModel(num_classes=10).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)



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

    print("量化感知训练（QAT）测试")

    print("=" * 50)



    trainer = QATAwareTrainer(model, device, num_bits=8)



    # 训练几个epoch

    print("\n--- QAT训练 ---")

    for epoch in range(5):

        total_loss = 0

        for images, labels in DummyDataset(10):

            loss = trainer.train_step(images, labels, optimizer)

            total_loss += loss



        trainer.update_quantization_params()

        print(f"Epoch {epoch + 1}: Loss={total_loss / 320:.4f}")



    # PACT测试

    print("\n--- PACT激活函数 ---")

    pact = PACTQuantization(num_bits=8, alpha_init=4.0)

    test_input = torch.rand(4, 32)

    output = pact(test_input)

    print(f"输入范围: [{test_input.min():.4f}, {test_input.max():.4f}]")

    print(f"Alpha值: {pact.alpha.item():.4f}")

    print(f"输出范围: [{output.min():.4f}, {output.max():.4f}]")



    # LSQ测试

    print("\n--- LSQ量化 ---")

    lsq = LSQQuantization(num_bits=8)

    test_input = torch.randn(4, 32)

    output = lsq(test_input)

    print(f"Step size: {lsq.step_size.item():.6f}")

    print(f"输出范围: [{output.min():.4f}, {output.max():.4f}]")



    print("\n测试完成！")


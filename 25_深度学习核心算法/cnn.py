# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / cnn

本文件实现 cnn 相关的算法功能。
"""

import numpy as np


def im2col(image, kernel_size, stride=1, padding=0):
    """
    将图像转换为列形式（用于高效卷积）
    
    参数:
        image: (batch, channels, height, width)
        kernel_size: 卷积核大小
        stride: 步长
        padding: 填充
    返回:
        cols: 转换后的列 (out_h * out_w, kernel_h * kernel_w * channels * batch)
    """
    batch, channels, height, width = image.shape
    kh, kw = kernel_size, kernel_size
    
    # 填充
    if padding > 0:
        image = np.pad(image, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
    
    # 输出尺寸
    out_h = (height + 2 * padding - kh) // stride + 1
    out_w = (width + 2 * padding - kw) // stride + 1
    
    # 提取补丁
    cols = np.zeros((out_h * out_w * batch, kh * kw * channels))
    
    for b in range(batch):
        for oh in range(out_h):
            for ow in range(out_w):
                h_start = oh * stride
                w_start = ow * stride
                
                patch = image[b, :, h_start:h_start+kh, w_start:w_start+kw]
                row_idx = b * out_h * out_w + oh * out_w + ow
                cols[row_idx] = patch.flatten()
    
    return cols


def col2im(cols, image_shape, kernel_size, stride=1, padding=0):
    """
    将列形式转换回图像
    """
    batch, channels, height, width = image_shape
    kh, kw = kernel_size, kernel_size
    
    out_h = (height + 2 * padding - kh) // stride + 1
    out_w = (width + 2 * padding - kw) // stride + 1
    
    image = np.zeros((batch, channels, height + 2 * padding, width + 2 * padding))
    
    for b in range(batch):
        for oh in range(out_h):
            for ow in range(out_w):
                h_start = oh * stride
                w_start = ow * stride
                
                row_idx = b * out_h * out_w + oh * out_w + ow
                patch = cols[row_idx].reshape(channels, kh, kw)
                
                image[b, :, h_start:h_start+kh, w_start:w_start+kw] += patch
    
    # 移除填充
    if padding > 0:
        image = image[:, :, padding:-padding, padding:-padding]
    
    return image


class Conv2d:
    """
    2D卷积层
    
    参数:
        in_channels: 输入通道数
        out_channels: 输出通道数
        kernel_size: 卷积核大小
        stride: 步长
        padding: 填充
    """
    
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        
        # He初始化
        self.weight = np.random.randn(out_channels, in_channels, kernel_size, kernel_size) * np.sqrt(2.0 / (in_channels * kernel_size * kernel_size))
        self.bias = np.zeros(out_channels)
    
    def forward(self, x):
        """
        前馈传播
        
        参数:
            x: 输入 (batch, in_channels, height, width)
        返回:
            output: 输出 (batch, out_channels, out_h, out_w)
        """
        batch, in_c, in_h, in_w = x.shape
        
        # 计算输出尺寸
        out_h = (in_h + 2 * self.padding - self.kernel_size) // self.stride + 1
        out_w = (in_w + 2 * self.padding - self.kernel_size) // self.stride + 1
        
        # 使用im2col加速
        cols = im2col(x, self.kernel_size, self.stride, self.padding)
        
        # 重塑权重
        W_col = self.weight.reshape(self.out_channels, -1)
        
        # 计算输出
        out_flat = W_col @ cols.T + self.bias.reshape(-1, 1)
        output = out_flat.reshape(batch, out_h, out_w, self.out_channels).transpose(0, 3, 1, 2)
        
        return output
    
    def __call__(self, x):
        return self.forward(x)


class MaxPool2d:
    """
    2D最大池化层
    """
    
    def __init__(self, kernel_size=2, stride=2):
        self.kernel_size = kernel_size
        self.stride = stride
    
    def forward(self, x):
        batch, channels, height, width = x.shape
        
        out_h = (height - self.kernel_size) // self.stride + 1
        out_w = (width - self.kernel_size) // self.stride + 1
        
        output = np.zeros((batch, channels, out_h, out_w))
        
        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * self.stride
                        w_start = ow * self.stride
                        
                        patch = x[b, c, h_start:h_start+self.kernel_size, w_start:w_start+self.kernel_size]
                        output[b, c, oh, ow] = np.max(patch)
        
        return output


class AvgPool2d:
    """2D平均池化层"""
    
    def __init__(self, kernel_size=2, stride=2):
        self.kernel_size = kernel_size
        self.stride = stride
    
    def forward(self, x):
        batch, channels, height, width = x.shape
        
        out_h = (height - self.kernel_size) // self.stride + 1
        out_w = (width - self.kernel_size) // self.stride + 1
        
        output = np.zeros((batch, channels, out_h, out_w))
        
        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * self.stride
                        w_start = ow * self.stride
                        
                        patch = x[b, c, h_start:h_start+self.kernel_size, w_start:w_start+self.kernel_size]
                        output[b, c, oh, ow] = np.mean(patch)
        
        return output


class BatchNorm2d:
    """2D批量归一化"""
    
    def __init__(self, num_channels, momentum=0.9):
        self.num_channels = num_channels
        self.momentum = momentum
        
        self.gamma = np.ones(num_channels)
        self.beta = np.zeros(num_channels)
        
        self.running_mean = np.zeros(num_channels)
        self.running_var = np.ones(num_channels)
        self.training = True
    
    def forward(self, x):
        """x: (batch, channels, height, width)"""
        if self.training:
            mean = np.mean(x, axis=(0, 2, 3))
            var = np.var(x, axis=(0, 2, 3))
            
            self.running_mean = self.momentum * self.running_mean + (1 - self.momentum) * mean
            self.running_var = self.momentum * self.running_var + (1 - self.momentum) * var * (x.shape[0] / (x.shape[0] - 1))
        else:
            mean = self.running_mean
            var = self.running_var
        
        x_norm = (x - mean.reshape(1, -1, 1, 1)) / np.sqrt(var.reshape(1, -1, 1, 1) + 1e-5)
        
        return self.gamma.reshape(1, -1, 1, 1) * x_norm + self.beta.reshape(1, -1, 1, 1)


class Flatten:
    """展平层"""
    def forward(self, x):
        return x.reshape(x.shape[0], -1)


class LeNet5:
    """
    LeNet-5简化版
    
    架构: Conv -> Pool -> Conv -> Pool -> FC -> FC
    """
    
    def __init__(self, num_classes=10):
        self.conv1 = Conv2d(1, 6, kernel_size=5, stride=1, padding=2)
        self.pool1 = AvgPool2d(kernel_size=2, stride=2)
        
        self.conv2 = Conv2d(6, 16, kernel_size=5, stride=1, padding=0)
        self.pool2 = AvgPool2d(kernel_size=2, stride=2)
        
        self.flatten = Flatten()
        self.fc1 = np.random.randn(16 * 5 * 5, 120) * np.sqrt(2.0 / (16 * 5 * 5))
        self.fc2 = np.random.randn(120, 84) * np.sqrt(2.0 / 120)
        self.fc3 = np.random.randn(84, num_classes) * np.sqrt(2.0 / 84)
        
        self.relu = lambda x: np.maximum(0, x)
    
    def forward(self, x):
        # Conv1
        x = self.relu(self.conv1(x))
        # Pool1
        x = self.pool1(x)
        # Conv2
        x = self.relu(self.conv2(x))
        # Pool2
        x = self.pool2(x)
        # Flatten
        x = self.flatten.forward(x)
        # FC1
        x = self.relu(x @ self.fc1)
        # FC2
        x = self.relu(x @ self.fc2)
        # FC3
        x = x @ self.fc3
        
        return x


class SimpleAlexNet:
    """
    AlexNet简化版
    
    架构: Conv -> Norm -> Pool -> Conv -> Conv -> Pool -> Conv -> Conv -> Conv -> Pool -> FC -> FC -> FC
    """
    
    def __init__(self, num_classes=1000):
        self.features = [
            Conv2d(3, 96, kernel_size=11, stride=4, padding=3),
            lambda x: np.maximum(0, x),  # ReLU
            lambda x: x[:, :, ::2, ::2],  # MaxPool简化
            Conv2d(96, 256, kernel_size=5, stride=1, padding=2),
            lambda x: np.maximum(0, x),
            lambda x: x[:, :, ::2, ::2],
            Conv2d(256, 384, kernel_size=3, stride=1, padding=1),
            lambda x: np.maximum(0, x),
            Conv2d(384, 384, kernel_size=3, stride=1, padding=1),
            lambda x: np.maximum(0, x),
            Conv2d(384, 256, kernel_size=3, stride=1, padding=1),
            lambda x: np.maximum(0, x),
            lambda x: x[:, :, ::2, ::2],
        ]
        
        self.flatten = Flatten()
        
        self.fc1 = np.random.randn(256 * 6 * 6, 4096) * 0.01
        self.fc2 = np.random.randn(4096, 4096) * 0.01
        self.fc3 = np.random.randn(4096, num_classes) * 0.01
    
    def forward(self, x):
        for layer in self.features:
            x = layer(x)
        
        x = self.flatten.forward(x)
        x = np.maximum(0, x @ self.fc1)
        x = np.maximum(0, x @ self.fc2)
        x = x @ self.fc3
        
        return x


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("卷积神经网络（CNN）测试")
    print("=" * 55)
    
    # 测试卷积层
    print("\n--- 卷积层测试 ---")
    conv = Conv2d(3, 16, kernel_size=3, stride=1, padding=1)
    
    x = np.random.randn(4, 3, 32, 32)
    y = conv(x)
    
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {y.shape}")
    print(f"卷积核形状: {conv.weight.shape}")
    print(f"参数量: {conv.weight.size + conv.bias.size}")
    
    # 测试池化层
    print("\n--- 池化层测试 ---")
    maxpool = MaxPool2d(kernel_size=2, stride=2)
    avgpool = AvgPool2d(kernel_size=2, stride=2)
    
    x = np.random.randn(2, 8, 16, 16)
    
    y_max = maxpool(x)
    y_avg = avgpool(x)
    
    print(f"MaxPool: {x.shape} -> {y_max.shape}")
    print(f"AvgPool: {x.shape} -> {y_avg.shape}")
    
    # 测试BatchNorm
    print("\n--- BatchNorm2d测试 ---")
    bn = BatchNorm2d(num_channels=8)
    
    x = np.random.randn(4, 8, 8, 8)
    y = bn.forward(x)
    
    print(f"输入均值: {x.mean():.4f}, 输出均值: {y.mean():.4f}")
    print(f"输入方差: {x.var():.4f}, 输出方差: {y.var():.4f}")
    
    # 测试LeNet-5
    print("\n--- LeNet-5测试 ---")
    lenet = LeNet5(num_classes=10)
    
    x = np.random.randn(2, 1, 28, 28)
    y = lenet(x)
    
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {y.shape}")
    print(f"输出 logits 范围: [{y.min():.4f}, {y.max():.4f}]")
    
    # 测试AlexNet简化版
    print("\n--- AlexNet简化版测试 ---")
    alexnet = SimpleAlexNet(num_classes=1000)
    
    x = np.random.randn(2, 3, 224, 224)
    y = alexnet(x)
    
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {y.shape}")
    
    # 参数统计
    print("\n--- 参数统计 ---")
    lenet_params = (
        lenet.conv1.weight.size + lenet.conv1.bias.size +
        lenet.conv2.weight.size + lenet.conv2.bias.size +
        lenet.fc1.size + lenet.fc2.size + lenet.fc3.size
    )
    print(f"LeNet-5 参数量: {lenet_params:,}")
    
    # 卷积感受野分析
    print("\n--- 感受野分析 ---")
    print("LeNet-5:")
    print(f"  Conv1 (5x5): 感受野 = 5")
    print(f"  Pool1 (2x2, s=2): 感受野 = 6")
    print(f"  Conv2 (5x5): 感受野 = 10")
    print(f"  Pool2 (2x2, s=2): 感受野 = 12")
    
    # 特征图大小计算
    print("\n--- 特征图大小计算 ---")
    print("LeNet-5 各层特征图:")
    
    h, w = 32, 32
    layers = [
        ("Input", h, w),
        ("Conv1(5x5,p=2)", (h + 4 - 5) + 1, (w + 4 - 5) + 1),
        ("Pool1(2x2,s=2)", (h - 2) // 2 + 1, (w - 2) // 2 + 1),
        ("Conv2(5x5)", (h - 5) // 2 + 1, (w - 5) // 2 + 1),
        ("Pool2(2x2,s=2)", ((h - 5) // 2 - 2) // 2 + 1, ((w - 5) // 2 - 2) // 2 + 1),
    ]
    
    for name, h_out, w_out in layers:
        print(f"  {name}: {h_out}x{w_out}")
    
    # 训练模拟
    print("\n--- 训练模拟 ---")
    x_train = np.random.randn(100, 1, 28, 28)
    y_train = np.random.randint(0, 10, 100)
    
    print(f"训练样本数: {len(x_train)}")
    print(f"类别数: {len(np.unique(y_train))}")
    
    # 前向传播计算量估算
    print("\n--- 计算量估算 ---")
    print("卷积层计算量（FLOPs）= 2 * 输出点数 * 卷积核参数")
    
    batch = 1
    out_h, out_w = 28, 28
    out_c = 6
    kh, kw = 5, 5
    
    flops = 2 * batch * out_h * out_w * out_c * kh * kw * 1
    print(f"LeNet Conv1 FLOPs: {flops:,}")
    
    print("\nCNN测试完成！")

# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / nn_components



本文件实现 nn_components 相关的算法功能。

"""



import numpy as np





class DenseLayer:

    """全连接层"""

    def __init__(self, in_features, out_features):

        self.W = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)

        self.b = np.zeros(out_features)

    

    def forward(self, x):

        return x @ self.W + self.b

    

    def __call__(self, x):

        return self.forward(x)





class Conv2d:

    """简化2D卷积层"""

    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):

        self.kh, self.kw = kernel_size, kernel_size

        self.stride = stride

        self.padding = padding

        

        self.W = np.random.randn(out_channels, in_channels, self.kh, self.kw) * 0.01

        self.b = np.zeros(out_channels)

    

    def forward(self, x):

        """x: (batch, channels, height, width)"""

        batch, C, H, W = x.shape

        out_C, _, kh, kw = self.W.shape

        

        # 填充

        if self.padding > 0:

            x = np.pad(x, ((0, 0), (0, 0), (self.padding, self.padding), (self.padding, self.padding)))

        

        # 计算输出尺寸

        out_H = (H + 2 * self.padding - kh) // self.stride + 1

        out_W = (W + 2 * self.padding - kw) // self.stride + 1

        

        output = np.zeros((batch, out_C, out_H, out_W))

        

        for i in range(batch):

            for oc in range(out_C):

                for oh in range(out_H):

                    for ow in range(out_W):

                        h_start = oh * self.stride

                        w_start = ow * self.stride

                        

                        patch = x[i, :, h_start:h_start+kh, w_start:w_start+kw]

                        output[i, oc, oh, ow] = np.sum(patch * self.W[oc]) + self.b[oc]

        

        return output

    

    def __call__(self, x):

        return self.forward(x)





class MaxPool2d:

    """最大池化层"""

    def __init__(self, kernel_size=2, stride=2):

        self.kh = self.kw = kernel_size

        self.stride = stride

    

    def forward(self, x):

        """x: (batch, channels, height, width)"""

        batch, C, H, W = x.shape

        

        out_H = (H - self.kh) // self.stride + 1

        out_W = (W - self.kw) // self.stride + 1

        

        output = np.zeros((batch, C, out_H, out_W))

        

        for i in range(batch):

            for c in range(C):

                for oh in range(out_H):

                    for ow in range(out_W):

                        h_start = oh * self.stride

                        w_start = ow * self.stride

                        

                        patch = x[i, c, h_start:h_start+self.kh, w_start:w_start+self.kw]

                        output[i, c, oh, ow] = np.max(patch)

        

        return output





class AvgPool2d:

    """平均池化层"""

    def __init__(self, kernel_size=2, stride=2):

        self.kh = self.kw = kernel_size

        self.stride = stride

    

    def forward(self, x):

        batch, C, H, W = x.shape

        

        out_H = (H - self.kh) // self.stride + 1

        out_W = (W - self.kw) // self.stride + 1

        

        output = np.zeros((batch, C, out_H, out_W))

        

        for i in range(batch):

            for c in range(C):

                for oh in range(out_H):

                    for ow in range(out_W):

                        h_start = oh * self.stride

                        w_start = ow * self.stride

                        

                        patch = x[i, c, h_start:h_start+self.kh, w_start:w_start+self.kw]

                        output[i, c, oh, ow] = np.mean(patch)

        

        return output





class BatchNorm2d:

    """2D批量归一化"""

    def __init__(self, num_features, momentum=0.9, eps=1e-5):

        self.num_features = num_features

        self.momentum = momentum

        self.eps = eps

        

        self.gamma = np.ones(num_features)

        self.beta = np.zeros(num_features)

        

        self.running_mean = np.zeros(num_features)

        self.running_var = np.ones(num_features)

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

        

        # 归一化

        x_norm = (x - mean.reshape(1, -1, 1, 1)) / np.sqrt(var.reshape(1, -1, 1, 1) + self.eps)

        

        return self.gamma.reshape(1, -1, 1, 1) * x_norm + self.beta.reshape(1, -1, 1, 1)





class ResidualBlock:

    """残差块"""

    def __init__(self, channels):

        self.conv1 = Conv2d(channels, channels, 3, 1, 1)

        self.bn1 = BatchNorm2d(channels)

        self.conv2 = Conv2d(channels, channels, 3, 1, 1)

        self.bn2 = BatchNorm2d(channels)

        self.relu = lambda x: np.maximum(0, x)

    

    def forward(self, x):

        residual = x

        

        out = self.relu(self.bn1.forward(self.conv1(x)))

        out = self.bn2.forward(self.conv2(out))

        

        return self.relu(out + residual)





class SimpleMLP:

    """简单多层感知机"""

    def __init__(self, layer_dims):

        self.layers = []

        for i in range(len(layer_dims) - 1):

            self.layers.append(DenseLayer(layer_dims[i], layer_dims[i+1]))

        self.relu = lambda x: np.maximum(0, x)

    

    def forward(self, x):

        for i, layer in enumerate(self.layers):

            x = layer(x)

            if i < len(self.layers) - 1:

                x = self.relu(x)

        return x





class SimpleCNN:

    """简单CNN"""

    def __init__(self):

        self.conv1 = Conv2d(1, 8, 3, 1, 1)

        self.bn1 = BatchNorm2d(8)

        self.pool1 = MaxPool2d(2, 2)

        self.conv2 = Conv2d(8, 16, 3, 1, 1)

        self.bn2 = BatchNorm2d(16)

        self.pool2 = AvgPool2d(2, 2)

        self.flatten = lambda x: x.reshape(x.shape[0], -1)

        self.fc = DenseLayer(16 * 7 * 7, 10)

        self.relu = lambda x: np.maximum(0, x)

    

    def forward(self, x):

        x = self.relu(self.bn1.forward(self.conv1(x)))

        x = self.pool1(x)

        x = self.relu(self.bn2.forward(self.conv2(x)))

        x = self.pool2(x)

        x = self.flatten(x)

        x = self.fc(x)

        return x





if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("神经网络基础组件测试")

    print("=" * 55)

    

    # 测试全连接层

    print("\n--- 全连接层 ---")

    dense = DenseLayer(10, 5)

    x = np.random.randn(4, 10)

    y = dense(x)

    print(f"输入: {x.shape} -> 输出: {y.shape}")

    

    # 测试卷积层

    print("\n--- 卷积层 ---")

    conv = Conv2d(3, 16, kernel_size=3, stride=1, padding=1)

    x = np.random.randn(2, 3, 8, 8)

    y = conv(x)

    print(f"输入: {x.shape} -> 输出: {y.shape}")

    

    # 测试池化

    print("\n--- 池化层 ---")

    maxpool = MaxPool2d(2, 2)

    x = np.random.randn(2, 8, 16, 16)

    y = maxpool(x)

    print(f"MaxPool: {x.shape} -> {y.shape}")

    

    avgpool = AvgPool2d(2, 2)

    y = avgpool(x)

    print(f"AvgPool: {x.shape} -> {y.shape}")

    

    # 测试BatchNorm

    print("\n--- BatchNorm2d ---")

    bn = BatchNorm2d(8)

    x = np.random.randn(4, 8, 8, 8)

    y = bn.forward(x)

    print(f"输入均值: {x.mean():.4f}, 方差: {x.var():.4f}")

    print(f"输出均值: {y.mean():.4f}, 方差: {y.var():.4f}")

    

    # 测试残差块

    print("\n--- 残差块 ---")

    resblock = ResidualBlock(16)

    x = np.random.randn(2, 16, 8, 8)

    y = resblock.forward(x)

    print(f"输入: {x.shape} -> 输出: {y.shape}")

    

    # 测试MLP

    print("\n--- MLP ---")

    mlp = SimpleMLP([784, 256, 128, 10])

    x = np.random.randn(16, 784)

    y = mlp.forward(x)

    print(f"MLP: {x.shape} -> {y.shape}")

    

    # 测试CNN

    print("\n--- CNN ---")

    cnn = SimpleCNN()

    x = np.random.randn(4, 1, 28, 28)

    y = cnn.forward(x)

    print(f"CNN: {x.shape} -> {y.shape}")

    

    # 参数统计

    print("\n--- 参数量统计 ---")

    total_params = 0

    

    for layer in mlp.layers:

        params = layer.W.size + layer.b.size

        total_params += params

        print(f"  Dense: {params}")

    

    print(f"MLP总参数: {total_params}")

    

    # 残差连接效果

    print("\n--- 残差连接效果 ---")

    x = np.random.randn(2, 16, 4, 4)

    

    # 普通块

    conv_block = Conv2d(16, 16, 3, 1, 1)

    output = np.maximum(0, conv_block(conv_block(x)))

    

    # 残差块

    res_output = resblock.forward(x)

    

    print(f"普通块输出范数: {np.linalg.norm(output):.4f}")

    print(f"残差块输出范数: {np.linalg.norm(res_output):.4f}")

    print(f"残差连接保留了更多信息")

    

    print("\n神经网络基础组件测试完成！")


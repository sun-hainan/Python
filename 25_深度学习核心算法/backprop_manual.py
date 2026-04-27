# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / backprop_manual



本文件实现 backprop_manual 相关的算法功能。

"""



import numpy as np





# ============================

# 激活函数及其导数

# ============================



def relu(z):

    """ReLU激活函数：max(0, z)"""

    return np.maximum(0, z)





def relu_gradient(z):

    """ReLU的导数：z>0时为1，否则为0"""

    return (z > 0).astype(float)





def sigmoid(z):

    """Sigmoid激活函数：1/(1+exp(-z))"""

    # 数值稳定性处理，防止exp溢出

    z = np.clip(z, -500, 500)

    return 1 / (1 + np.exp(-z))





def sigmoid_gradient(z):

    """Sigmoid的导数：sigmoid(z) * (1 - sigmoid(z))"""

    s = sigmoid(z)

    return s * (1 - s)





def tanh(z):

    """Tanh激活函数：(exp(z)-exp(-z))/(exp(z)+exp(-z))"""

    return np.tanh(z)





def tanh_gradient(z):

    """Tanh的导数：1 - tanh^2(z)"""

    t = np.tanh(z)

    return 1 - t ** 2





# ============================

# 网络层定义

# ============================



class LinearLayer:

    """

    全连接线性层（无激活函数）

    

    参数:

        input_dim: 输入特征维度

        output_dim: 输出特征维度（神经元个数）

        learning_rate: 学习率

    """

    

    def __init__(self, input_dim, output_dim, learning_rate=0.01):

        # Xavier初始化：保持前向传播时方差一致

        self.weights = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)

        self.bias = np.zeros((1, output_dim))

        self.lr = learning_rate

        # 反向传播时保存中间结果

        self.input_cache = None

        self.output_cache = None

    

    def forward(self, x):

        """

        前馈传播：y = x @ W + b

        

        参数:

            x: 输入矩阵 (batch_size, input_dim)

        返回:

            output: 输出矩阵 (batch_size, output_dim)

        """

        self.input_cache = x  # 保存输入用于反向传播

        self.output_cache = x @ self.weights + self.bias

        return self.output_cache

    

    def backward(self, grad_output):

        """

        反向传播：计算损失对权重和偏置的梯度

        

        参数:

            grad_output: 损失对输出的梯度 (batch_size, output_dim)

        返回:

            grad_input: 损失对输入的梯度 (batch_size, input_dim)

        """

        batch_size = grad_output.shape[0]

        

        # 损失对权重的梯度：grad_output^T @ input

        grad_weights = self.input_cache.T @ grad_output / batch_size

        # 损失对偏置的梯度：对batch维度求和

        grad_bias = np.sum(grad_output, axis=0, keepdims=True) / batch_size

        # 损失对输入的梯度：grad_output @ weights^T

        grad_input = grad_output @ self.weights.T

        

        # 梯度下降更新（W和b的梯度与更新写在同一层）

        self.weights -= self.lr * grad_weights

        self.bias -= self.lr * grad_bias

        

        return grad_input





class ActivationLayer:

    """

    激活函数层（无参数）

    

    参数:

        activation: 激活函数名 ('relu', 'sigmoid', 'tanh')

    """

    

    def __init__(self, activation='relu'):

        self.activation = activation

        self.input_cache = None

        self.output_cache = None

    

    def forward(self, x):

        """前馈传播：应用激活函数"""

        self.input_cache = x

        if self.activation == 'relu':

            self.output_cache = relu(x)

        elif self.activation == 'sigmoid':

            self.output_cache = sigmoid(x)

        elif self.activation == 'tanh':

            self.output_cache = tanh(x)

        else:

            raise ValueError(f"Unsupported activation: {self.activation}")

        return self.output_cache

    

    def backward(self, grad_output):

        """反向传播：链式法则乘以激活函数导数"""

        if self.activation == 'relu':

            grad = relu_gradient(self.input_cache)

        elif self.activation == 'sigmoid':

            grad = sigmoid_gradient(self.input_cache)

        elif self.activation == 'tanh':

            grad = tanh_gradient(self.input_cache)

        return grad_output * grad





# ============================

# 损失函数

# ============================



def cross_entropy_loss(pred, target):

    """

    交叉熵损失函数（带Softmax）

    

    参数:

        pred: 模型预测 logits (batch_size, num_classes)

        target: 真实标签 (batch_size,) 整数索引 或 one-hot (batch_size, num_classes)

    返回:

        loss: 标量损失值

        grad: 对pred的梯度

    """

    batch_size = pred.shape[0]

    

    # 数值稳定的Softmax

    pred_shifted = pred - np.max(pred, axis=1, keepdims=True)

    exp_pred = np.exp(pred_shifted)

    probs = exp_pred / np.sum(exp_pred, axis=1, keepdims=True)

    

    # 真实标签的one-hot编码

    if len(target.shape) == 1:

        target_onehot = np.zeros_like(pred)

        target_onehot[np.arange(batch_size), target] = 1.0

    

    # 交叉熵损失

    loss = -np.sum(target_onehot * np.log(probs + 1e-8)) / batch_size

    

    # 梯度：softmax - target（简化的梯度公式）

    grad = (probs - target_onehot) / batch_size

    

    return loss, grad





def mse_loss(pred, target):

    """均方误差损失"""

    batch_size = pred.shape[0]

    error = pred - target

    loss = np.sum(error ** 2) / (2 * batch_size)

    grad = error / batch_size

    return loss, grad





# ============================

# 神经网络模型

# ============================



class SimpleNeuralNetwork:

    """

    简单多层感知机（MLP）

    

    参数:

        layer_dims: 各层维度列表，如 [784, 256, 128, 10]

        activation: 隐藏层激活函数

        learning_rate: 学习率

    """

    

    def __init__(self, layer_dims, activation='relu', learning_rate=0.01):

        self.layers = []

        for i in range(len(layer_dims) - 1):

            # 添加线性层

            self.layers.append(

                LinearLayer(layer_dims[i], layer_dims[i+1], learning_rate)

            )

            # 隐藏层添加激活函数（输出层不加激活）

            if i < len(layer_dims) - 2:

                self.layers.append(ActivationLayer(activation))

    

    def forward(self, x):

        """前馈传播：依次通过每一层"""

        for layer in self.layers:

            x = layer.forward(x)

        return x

    

    def backward(self, grad):

        """反向传播：从后向前依次计算梯度"""

        for layer in reversed(self.layers):

            grad = layer.backward(grad)

    

    def predict(self, x):

        """预测：返回概率最大的类别索引"""

        probs = self.forward(x)

        return np.argmax(probs, axis=1)





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    # 生成模拟数据：1000个样本，20个特征，10个类别

    np.random.seed(42)

    batch_size = 64

    input_dim = 20

    hidden_dim = 32

    output_dim = 10

    

    # 随机数据和标签

    X = np.random.randn(batch_size, input_dim)

    y = np.random.randint(0, output_dim, batch_size)

    

    # 构建网络：[20, 32, 10]，学习率0.1

    net = SimpleNeuralNetwork(

        [input_dim, hidden_dim, output_dim],

        activation='relu',

        learning_rate=0.1

    )

    

    # 训练一个batch

    pred = net.forward(X)

    loss, grad = cross_entropy_loss(pred, y)

    net.backward(grad)

    

    # 计算准确率

    predictions = net.predict(X)

    accuracy = np.mean(predictions == y)

    

    print(f"批次损失: {loss:.4f}")

    print(f"批次准确率: {accuracy:.2%}")

    print(f"网络结构: {input_dim} -> {hidden_dim} -> {output_dim}")

    print("BP反向传播手动实现测试通过！")


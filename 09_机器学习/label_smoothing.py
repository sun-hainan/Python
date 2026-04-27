# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / label_smoothing



本文件实现 label_smoothing 相关的算法功能。

"""



import numpy as np





def smooth_labels(y, epsilon=0.1):

    """

    标签平滑



    参数:

        y: One-hot编码标签 (n_samples, n_classes)

        epsilon: 平滑因子



    返回:

        y_smoothed: 平滑后的标签

    """

    n_classes = y.shape[1]

    return (1 - epsilon) * y + epsilon / n_classes





class LabelSmoothingLoss:

    """

    标签平滑损失函数



    等价于：

        L = -Σ y_smooth * log(y_pred)

          = -(1-ε) * Σ y_onehot * log(y_pred) - ε/K * Σ log(y_pred)

          = (1-ε) * CE + ε * H(y_pred, uniform)

    """



    def __init__(self, n_classes, epsilon=0.1):

        self.n_classes = n_classes

        self.epsilon = epsilon



    def __call__(self, y_pred, y_true):

        """

        计算标签平滑交叉熵损失



        参数:

            y_pred: 模型预测 (n_samples, n_classes) 概率

            y_true: 原始标签 (n_samples, n_classes) one-hot或平滑后



        返回:

            loss: 损失值

        """

        # 如果输入是one-hot，转换为平滑标签

        if np.sum(y_true[0]) == 1:

            y_smoothed = smooth_labels(y_true, self.epsilon)

        else:

            y_smoothed = y_true



        # 交叉熵

        eps = 1e-10

        loss = -np.mean(np.sum(y_smoothed * np.log(y_pred + eps), axis=1))



        return loss



    def grad(self, y_pred, y_true):

        """

        计算梯度



        ∂L/∂z_i = (1-ε) * (softmax_i - y_i)

        """

        if np.sum(y_true[0]) == 1:

            y_smoothed = smooth_labels(y_true, self.epsilon)

        else:

            y_smoothed = y_true



        # Softmax梯度

        grad = y_pred - y_smoothed

        return grad





class LabelSmoothingClassifier:

    """

    带标签平滑的分类器示例



    参数:

        layer_dims: 网络结构 [input, hidden1, ..., output]

        smoothing_epsilon: 平滑因子

        lr: 学习率

    """



    def __init__(self, layer_dims, smoothing_epsilon=0.1, lr=0.01):

        self.smoothing_epsilon = smoothing_epsilon

        self.lr = lr

        self.n_classes = layer_dims[-1]



        # 初始化网络

        self.weights = []

        self.biases = []

        for i in range(len(layer_dims) - 1):

            fan_in = layer_dims[i]

            fan_out = layer_dims[i + 1]

            W = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)

            b = np.zeros(fan_out)

            self.weights.append(W)

            self.biases.append(b)



    def _softmax(self, X):

        """Softmax函数"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def _forward(self, X):

        """前向传播"""

        H = X

        for i, (W, b) in enumerate(zip(self.weights, self.biases)):

            Z = H @ W + b

            if i < len(self.weights) - 1:

                H = np.maximum(0, Z)  # ReLU

            else:

                H = self._softmax(Z)

        return H



    def fit(self, X, y, epochs=100, batch_size=32):

        """

        训练模型



        参数:

            X: 输入数据 (n_samples, n_features)

            y: 标签 (n_samples, n_classes) one-hot

            epochs: 训练轮数

            batch_size: 批量大小

        """

        n_samples = X.shape[0]

        criterion = LabelSmoothingLoss(self.n_classes, self.smoothing_epsilon)



        for epoch in range(epochs):

            indices = np.random.permutation(n_samples)

            epoch_loss = 0.0



            for start in range(0, n_samples, batch_size):

                end = min(start + batch_size, n_samples)

                batch_X = X[indices[start:end]]

                batch_y = y[indices[start:end]]



                # 前向传播

                y_pred = self._forward(batch_X)



                # 计算损失（标签平滑）

                loss = criterion(y_pred, batch_y)

                epoch_loss += loss * (end - start)



                # 反向传播（简化）

                grad = criterion.grad(y_pred, batch_y)

                m = batch_X.shape[0]



                # 更新

                for i in range(len(self.weights) - 1, -1, -1):

                    if i > 0:

                        dH = grad @ self.weights[i].T

                        dZ = dH * (self.weights[i] @ self.weights[i].T > 0).astype(float)

                    else:

                        dZ = grad



                    dW = batch_X.T @ dZ if i == 0 else None

                    if dW is not None:

                        self.weights[i] -= self.lr * dW / m

                        self.biases[i] -= self.lr * np.sum(dZ, axis=0) / m



            if (epoch + 1) % 20 == 0:

                preds = np.argmax(self._forward(X), axis=1)

                labels = np.argmax(y, axis=1)

                acc = np.mean(preds == labels)

                print(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / n_samples:.4f}, Acc: {acc:.4f}")



    def predict(self, X):

        """预测"""

        return np.argmax(self._forward(X), axis=1)





def test_label_smoothing():

    """测试标签平滑"""

    np.random.seed(42)



    print("=" * 60)

    print("标签平滑测试")

    print("=" * 60)



    # 生成模拟数据

    n_samples = 300

    n_features = 20

    n_classes = 3



    X = np.random.randn(n_samples, n_features)

    # 创建类别结构

    for i in range(n_classes):

        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)

        X[mask] += np.array([1, 2, 0])[i]



    y = np.zeros((n_samples, n_classes))

    labels = np.zeros(n_samples, dtype=int)

    for i in range(n_classes):

        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)

        y[mask, i] = 1

        labels[mask] = i



    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)



    # 测试平滑效果

    print("\n1. 标签平滑转换示例:")

    y_original = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    y_smoothed = smooth_labels(y_original, epsilon=0.1)

    print(f"原始标签:\n{y_original}")

    print(f"平滑后 (ε=0.1):\n{y_smoothed}")



    # 对比训练效果

    print("\n2. 对比有/无标签平滑:")



    print("\n  无标签平滑:")

    model_no_smooth = LabelSmoothingClassifier([n_features, 32, n_classes], smoothing_epsilon=0.0, lr=0.1)

    model_no_smooth.fit(X, y, epochs=100, batch_size=32)



    print("\n  有标签平滑 (ε=0.1):")

    model_smooth = LabelSmoothingClassifier([n_features, 32, n_classes], smoothing_epsilon=0.1, lr=0.1)

    model_smooth.fit(X, y, epochs=100, batch_size=32)



    # 检查预测置信度

    print("\n3. 预测置信度对比:")

    y_pred_no_smooth = model_no_smooth._forward(X[:10])

    y_pred_smooth = model_smooth._forward(X[:10])



    print(f"  无平滑 - 预测置信度: {np.max(y_pred_no_smooth, axis=1)}")

    print(f"  有平滑 - 预测置信度: {np.max(y_pred_smooth, axis=1)}")

    print(f"  无平滑 - 平均置信度: {np.mean(np.max(y_pred_no_smooth, axis=1)):.4f}")

    print(f"  有平滑 - 平均置信度: {np.mean(np.max(y_pred_smooth, axis=1)):.4f}")





if __name__ == "__main__":

    test_label_smoothing()


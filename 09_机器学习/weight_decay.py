# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / weight_decay



本文件实现 weight_decay 相关的算法功能。

"""



import numpy as np





class WeightDecayOptimizer:

    """

    带权重衰减的优化器（简化版SGD）



    参数:

        lr: 学习率

        weight_decay: 权重衰减系数λ

    """



    def __init__(self, lr=0.01, weight_decay=0.01):

        self.lr = lr

        self.weight_decay = weight_decay



    def step(self, weights, grads):

        """

        单步参数更新



        参数:

            weights: 权重列表

            grads: 梯度列表



        返回:

            新的权重列表

        """

        new_weights = []

        for W in weights:

            # L2正则化梯度: 2 * λ * W

            grad_decay = 2 * self.weight_decay * W

            # 梯度更新（含权重衰减）

            W_new = W - self.lr * (grads[W] + grad_decay)

            new_weights.append(W_new)

        return new_weights





class L1L2Regularization:

    """

    L1/L2正则化比较



    L1: λ * ||W||₁  -> 产生稀疏权重（特征选择）

    L2: λ * ||W||²  -> 权重衰减

    Elastic Net: λ₁ * ||W||₁ + λ₂ * ||W||²

    """



    def __init__(self, l1_lambda=0.01, l2_lambda=0.01):

        self.l1_lambda = l1_lambda

        self.l2_lambda = l2_lambda



    def l1_penalty(self, W):

        """L1正则化项 = λ * Σ|W|"""

        return self.l1_lambda * np.sum(np.abs(W))



    def l2_penalty(self, W):

        """L2正则化项 = λ * ΣW²"""

        return self.l2_lambda * np.sum(W ** 2)



    def elastic_net_penalty(self, W):

        """Elastic Net = L1 + L2"""

        return self.l1_penalty(W) + self.l2_penalty(W)



    def l1_grad(self, W):

        """L1梯度: λ * sign(W)"""

        return self.l1_lambda * np.sign(W)



    def l2_grad(self, W):

        """L2梯度: 2 * λ * W"""

        return 2 * self.l2_lambda * W



    def elastic_net_grad(self, W):

        """Elastic Net梯度"""

        return self.l1_grad(W) + self.l2_grad(W)





class NeuralNetworkWithWeightDecay:

    """

    带权重衰减的简单神经网络



    参数:

        layer_dims: 各层维度

        weight_decay: 权重衰减系数

        lr: 学习率

    """



    def __init__(self, layer_dims, weight_decay=0.01, lr=0.01):

        self.layer_dims = layer_dims

        self.weight_decay = weight_decay

        self.lr = lr

        self.n_layers = len(layer_dims) - 1



        # Xavier初始化

        self.weights = []

        self.biases = []

        for i in range(self.n_layers):

            fan_in = layer_dims[i]

            fan_out = layer_dims[i + 1]

            W = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)

            b = np.zeros(fan_out)

            self.weights.append(W)

            self.biases.append(b)



    def _relu(self, X):

        """ReLU激活"""

        return np.maximum(0, X)



    def _relu_grad(self, Z):

        """ReLU梯度"""

        return (Z > 0).astype(float)



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def _cross_entropy(self, y_pred, y_true):

        """交叉熵损失"""

        eps = 1e-10

        return -np.mean(y_true * np.log(y_pred + eps))



    def _forward(self, X):

        """前向传播"""

        caches = [(X, None)]

        H = X



        for i, (W, b) in enumerate(zip(self.weights, self.biases)):

            Z = H @ W + b

            caches.append((Z, H))



            if i < self.n_layers - 1:

                H = self._relu(Z)

            else:

                H = self._softmax(Z)



        return H, caches



    def _backward(self, y_pred, y_true, caches):

        """反向传播"""

        m = y_pred.shape[0]

        grads = {'W': {}, 'b': {}}



        # 输出层梯度（交叉熵+softmax）

        dZ = y_pred - y_true



        for i in range(self.n_layers - 1, -1, -1):

            Z, H = caches[i + 1]



            dW = H.T @ dZ / m

            db = np.sum(dZ, axis=0) / m



            # 保存梯度

            grads['W'][i] = dW

            grads['b'][i] = db



            # 传递梯度

            if i > 0:

                dH = dZ @ self.weights[i].T

                dZ = dH * self._relu_grad(Z)



        return grads



    def _compute_loss_with_decay(self, y_pred, y_true):

        """计算带权重衰减的损失"""

        # 交叉熵损失

        ce_loss = self._cross_entropy(y_pred, y_true)



        # L2正则化损失

        l2_loss = 0.0

        for W in self.weights:

            l2_loss += np.sum(W ** 2)

        l2_loss = 0.5 * self.weight_decay * l2_loss



        return ce_loss + l2_loss



    def fit(self, X, y, epochs=100, batch_size=32):

        """

        训练网络



        参数:

            X: 输入数据 (n_samples, n_features)

            y: 标签 (n_samples, n_classes) one-hot

            epochs: 训练轮数

            batch_size: 批量大小

        """

        n_samples = X.shape[0]



        for epoch in range(epochs):

            indices = np.random.permutation(n_samples)

            epoch_loss = 0.0



            for start in range(0, n_samples, batch_size):

                end = min(start + batch_size, n_samples)

                batch_X = X[indices[start:end]]

                batch_y = y[indices[start:end]]



                # 前向传播

                y_pred, caches = self._forward(batch_X)



                # 计算损失（含权重衰减）

                loss = self._compute_loss_with_decay(y_pred, batch_y)

                epoch_loss += loss * (end - start)



                # 反向传播

                grads = self._backward(y_pred, batch_y, caches)



                # 更新权重（添加权重衰减梯度）

                for i in range(self.n_layers):

                    W_grad = grads['W'][i]

                    b_grad = grads['b'][i]



                    # 权重衰减：添加L2正则化梯度

                    W_grad += self.weight_decay * self.weights[i]



                    self.weights[i] -= self.lr * W_grad

                    self.biases[i] -= self.lr * b_grad



            if (epoch + 1) % 20 == 0:

                # 计算准确率

                y_pred_train, _ = self._forward(X)

                predictions = np.argmax(y_pred_train, axis=1)

                labels = np.argmax(y, axis=1)

                accuracy = np.mean(predictions == labels)



                print(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / n_samples:.4f}, "

                      f"Acc: {accuracy:.4f}")



    def predict(self, X):

        """预测"""

        y_pred, _ = self._forward(X)

        return np.argmax(y_pred, axis=1)





def compare_with_without_decay():

    """

    对比有/无权重衰减的效果

    """

    np.random.seed(42)



    # 生成模拟数据（容易过拟合）

    n_samples = 200

    n_features = 50

    n_classes = 3



    X = np.random.randn(n_samples, n_features)

    # 创建结构化噪声

    for i in range(n_samples):

        X[i, :10] += np.random.randn(10) * 5



    y = np.zeros((n_samples, n_classes))

    labels = np.random.randint(0, n_classes, n_samples)

    for i in range(n_samples):

        y[i, labels[i]] = 1.0



    print("=" * 60)

    print("权重衰减效果对比")

    print("=" * 60)



    # 无权重衰减

    print("\n1. 无权重衰减:")

    model_no_decay = NeuralNetworkWithWeightDecay(

        [n_features, 64, 32, n_classes],

        weight_decay=0.0,

        lr=0.1

    )

    model_no_decay.fit(X, y, epochs=100, batch_size=32)



    # 有权重衰减

    print("\n2. 有权重衰减 (λ=0.01):")

    model_with_decay = NeuralNetworkWithWeightDecay(

        [n_features, 64, 32, n_classes],

        weight_decay=0.01,

        lr=0.1

    )

    model_with_decay.fit(X, y, epochs=100, batch_size=32)



    # 对比权重范数

    print("\n3. 权重范数对比:")

    for name, model in [("无衰减", model_no_decay), ("有衰减", model_with_decay)]:

        total_norm = sum(np.sum(W ** 2) for W in model.weights) ** 0.5

        print(f"  {name}: 总权重范数 = {total_norm:.4f}")





if __name__ == "__main__":

    compare_with_without_decay()


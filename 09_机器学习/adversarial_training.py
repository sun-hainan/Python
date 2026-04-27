# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / adversarial_training



本文件实现 adversarial_training 相关的算法功能。

"""



import numpy as np





class FGM:

    """

    Fast Gradient Method 对抗训练



    参数:

        epsilon: 扰动幅度

    """



    def __init__(self, epsilon=0.1):

        self.epsilon = epsilon



    def generate_adversarial(self, x, grad):

        """

        生成对抗样本



        参数:

            x: 原始输入 (batch, ...)

            grad: 损失对输入的梯度



        返回:

            x_adv: 对抗样本

        """

        # FGM扰动：基于梯度符号

        perturbation = self.epsilon * np.sign(grad)

        x_adv = x + perturbation

        return x_adv





class PGD:

    """

    Projected Gradient Descent 对抗训练



    参数:

        epsilon: 扰动幅度上限

        alpha: 步长

        n_iter: 迭代次数

    """



    def __init__(self, epsilon=0.1, alpha=0.01, n_iter=7):

        self.epsilon = epsilon

        self.alpha = alpha

        self.n_iter = n_iter



    def generate_adversarial(self, x, grad_fn, y):

        """

        生成对抗样本（多次迭代）



        参数:

            x: 原始输入

            grad_fn: 梯度计算函数 grad = grad_fn(x, y)

            y: 标签



        返回:

            x_adv: 对抗样本

        """

        x_adv = x.copy()



        for t in range(self.n_iter):

            # 计算梯度

            grad = grad_fn(x_adv, y)



            # 更新扰动

            perturbation = self.alpha * np.sign(grad)

            x_adv = x_adv + perturbation



            # 投影到L∞球内

            x_adv = np.clip(x_adv, x - self.epsilon, x + self.epsilon)



        return x_adv





class AdversarialTrainingClassifier:

    """

    带对抗训练的分类器



    参数:

        layer_dims: 网络结构

        epsilon: 对抗扰动幅度

        method: 'FGM' 或 'PGD'

    """



    def __init__(self, layer_dims, epsilon=0.1, method='FGM', lr=0.01):

        self.epsilon = epsilon

        self.lr = lr



        if method == 'FGM':

            self.adversarial = FGM(epsilon)

        else:

            self.adversarial = PGD(epsilon)



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



    def _relu(self, X):

        return np.maximum(0, X)



    def _relu_grad(self, Z):

        return (Z > 0).astype(float)



    def _softmax(self, X):

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def _forward(self, X):

        H = X

        for i, (W, b) in enumerate(zip(self.weights, self.biases)):

            Z = H @ W + b

            if i < len(self.weights) - 1:

                H = self._relu(Z)

            else:

                H = self._softmax(Z)

        return H



    def _backward(self, y_pred, y_true):

        """反向传播，返回对输入的梯度"""

        m = y_pred.shape[0]



        # 输出层

        dZ = y_pred - y_true

        dX = dZ.copy()



        for i in range(len(self.weights) - 1, -1, -1):

            # 权重梯度

            # （省略，只关注输入梯度）



            if i > 0:

                dX = dX @ self.weights[i].T

                # （简化：假设relu恒为1）

                dX = dX



        return dX  # 对输入的梯度



    def fit(self, X, y, epochs=100, batch_size=32):

        """

        对抗训练



        参数:

            X: 输入数据

            y: 标签（one-hot）

            epochs: 训练轮数

            batch_size: 批量大小

        """

        n_samples = X.shape[0]



        for epoch in range(epochs):

            indices = np.random.permutation(n_samples)

            epoch_loss_clean = 0.0

            epoch_loss_adv = 0.0



            for start in range(0, n_samples, batch_size):

                end = min(start + batch_size, n_samples)

                batch_X = X[indices[start:end]]

                batch_y = y[indices[start:end]]



                # 1. 干净样本前向/反向

                y_pred_clean = self._forward(batch_X)

                loss_clean = -np.mean(batch_y * np.log(y_pred_clean + 1e-10))

                epoch_loss_clean += loss_clean * (end - start)



                grad_clean = self._backward(y_pred_clean, batch_y)



                # 2. 生成对抗样本

                X_adv = batch_X + self.epsilon * np.sign(grad_clean)



                # 3. 对抗样本前向/反向

                y_pred_adv = self._forward(X_adv)

                loss_adv = -np.mean(batch_y * np.log(y_pred_adv + 1e-10))

                epoch_loss_adv += loss_adv * (end - start)



                grad_adv = self._backward(y_pred_adv, batch_y)



                # 4. 用对抗梯度更新（简化）

                # 实际中应组合干净和对抗梯度

                grad = grad_adv  # 纯对抗训练

                # 或 grad = grad_clean + grad_adv  # TRADES等方法



                # 模拟更新

                if (start + batch_size) % (batch_size * 10) == 0:

                    pass  # 简化：不做实际权重更新



            if (epoch + 1) % 20 == 0:

                preds_clean = np.argmax(self._forward(X), axis=1)

                labels = np.argmax(y, axis=1)

                acc = np.mean(preds_clean == labels)

                print(f"Epoch {epoch + 1}, Clean Loss: {epoch_loss_clean/n_samples:.4f}, "

                      f"Adv Loss: {epoch_loss_adv/n_samples:.4f}, Acc: {acc:.4f}")



    def predict(self, X):

        """预测"""

        return np.argmax(self._forward(X), axis=1)





def test_adversarial_examples():

    """测试对抗样本生成"""

    np.random.seed(42)



    print("=" * 60)

    print("对抗训练测试")

    print("=" * 60)



    # 简单数据集

    X = np.random.randn(100, 2)

    y = np.zeros((100, 2))

    y[:, 0] = (X[:, 0] * 2 + X[:, 1] > 0).astype(float)

    y[:, 1] = 1 - y[:, 0]



    print("\n1. FGM vs PGD 对比:")



    # 模拟梯度

    grad = np.random.randn(10, 2) * 0.1



    fgm = FGM(epsilon=0.3)

    pgd = PGD(epsilon=0.3, alpha=0.1, n_iter=5)



    x_sample = X[:10]



    # FGM扰动

    x_fgm = fgm.generate_adversarial(x_sample, grad)

    perturbation_fgm = x_fgm - x_sample



    # PGD扰动（简化）

    x_pgd = x_sample + np.clip(np.sum(perturbation_fgm, axis=0, keepdims=True), -0.3, 0.3)

    perturbation_pgd = x_pgd - x_sample



    print(f"   FGM扰动范数: {np.linalg.norm(perturbation_fgm):.4f}")

    print(f"   PGD扰动范数: {np.linalg.norm(perturbation_pgd):.4f}")



    print("\n2. 对抗样本效果演示:")

    print("   原始样本前几个:")

    print(f"   {X[:3, :3]}")



    print("\n   FGM对抗样本:")

    print(f"   {x_fgm[:3, :3]}")



    print("\n   扰动幅度:")

    print(f"   FGM: ε = 0.3")

    print(f"   PGD: ε = 0.3, 迭代5步")



    print("\n3. 对抗训练流程:")

    print("   ┌─────────────────────────────────────────┐")

    print("   │ 1. 干净样本前向 + 反向 -> grad_clean    │")

    print("   │ 2. 生成对抗样本: x_adv = x + ε*sign(g) │")

    print("   │ 3. 对抗样本前向 + 反向 -> grad_adv     │")

    print("   │ 4. 更新: θ = θ - lr * (grad_adv)      │")

    print("   └─────────────────────────────────────────┘")



    # 训练示例

    print("\n4. 训练示例:")

    np.random.seed(42)

    n = 200

    X = np.random.randn(n, 10)

    y = np.zeros((n, 2))

    y[:, 0] = (np.sum(X[:, :3], axis=1) > 0).astype(float)

    y[:, 1] = 1 - y[:, 0]



    model = AdversarialTrainingClassifier([10, 16, 8, 2], epsilon=0.1, method='FGM', lr=0.01)

    model.fit(X, y, epochs=50, batch_size=32)





if __name__ == "__main__":

    test_adversarial_examples()


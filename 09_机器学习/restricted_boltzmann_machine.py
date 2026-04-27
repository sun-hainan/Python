# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / restricted_boltzmann_machine



本文件实现 restricted_boltzmann_machine 相关的算法功能。

"""



import numpy as np





class RestrictedBoltzmannMachine:

    """

    受限玻尔兹曼机实现



    参数:

        n_visible: 可见层单元数

        n_hidden: 隐藏层单元数

        learning_rate: 学习率

        n_iterations: 训练迭代次数

        k: CD-k中的k值（Gibbs采样步数）

    """



    def __init__(self, n_visible, n_hidden, learning_rate=0.01, n_iterations=1000, k=1):

        self.n_visible = n_visible

        self.n_hidden = n_hidden

        self.lr = learning_rate

        self.n_iterations = n_iterations

        self.k = k



        # 初始化权重（ Xavier初始化）

        self.W = np.random.randn(n_visible, n_hidden) * np.sqrt(2.0 / (n_visible + n_hidden))

        # 可见层偏置

        self.b_v = np.zeros(n_visible)

        # 隐藏层偏置

        self.b_h = np.zeros(n_hidden)



    def _sigmoid(self, X):

        """Sigmoid激活函数"""

        return 1.0 / (1.0 + np.exp(-np.clip(X, -500, 500)))



    def _sample(self, probs):

        """从概率分布采样（伯努利分布）"""

        return (np.random.rand(*probs.shape) < probs).astype(float)



    def _gibbs_step(self, v_sample):

        """

        Gibbs采样一步

        v -> h -> v

        """

        # 从可见层采样隐藏层

        h_activation = self.b_h + v_sample @ self.W

        h_probs = self._sigmoid(h_activation)

        h_sample = self._sample(h_probs)



        # 从隐藏层采样可见层

        v_activation = self.b_v + h_sample @ self.W.T

        v_probs = self._sigmoid(v_activation)

        v_sample = self._sample(v_probs)



        return v_sample, h_probs, h_sample



    def _contrastive_divergence(self, v0):

        """

        对比散度算法（CD-k）



        参数:

            v0: 原始可见层数据



        返回:

            positive_grad: 正相位关联

            negative_v: 负相位可见层

        """

        # 正相位：从数据计算隐藏层概率

        h0_probs = self._sigmoid(self.b_h + v0 @ self.W)

        h0_sample = self._sample(h0_probs)

        positive_grad = v0.T @ h0_probs  # <v₀ h₀>



        # 负相位：k步Gibbs采样

        vk = v0.copy()

        for _ in range(self.k):

            vk, hk_probs, hk_sample = self._gibbs_step(vk)



        # 负相位关联

        negative_grad = vk.T @ hk_probs  # <vₖ hₖ>



        return positive_grad, negative_grad, vk



    def fit(self, X):

        """

        训练RBM



        参数:

            X: 训练数据 (n_samples, n_visible)，二值数据[0,1]

        """

        n_samples = X.shape[0]



        for iteration in range(self.n_iterations):

            # 随机选择一个样本批次（实际用mini-batch）

            for i in range(n_samples):

                v0 = X[i:i + 1]  # 保持2D形状



                # 对比散度

                pos_grad, neg_grad, vk = self._contrastive_divergence(v0)



                # 更新权重和偏置

                self.W += self.lr * (pos_grad - neg_grad) / n_samples

                self.b_h += self.lr * (np.mean(v0 @ self.W, axis=0) - np.mean(vk @ self.W, axis=0))

                self.b_v += self.lr * (np.mean(v0, axis=0) - np.mean(vk, axis=0))



            if (iteration + 1) % 200 == 0:

                # 计算重构误差

                h = self._sigmoid(self.b_h + v0 @ self.W)

                v_reconstructed = self._sigmoid(self.b_v + h @ self.W.T)

                error = np.mean((v_reconstructed - v0) ** 2)

                print(f"Iteration {iteration + 1}/{self.n_iterations}, Error: {error:.6f}")



    def transform(self, X):

        """

        将可见层转换为隐藏层表示



        参数:

            X: 可见层数据



        返回:

            h: 隐藏层激活概率

        """

        return self._sigmoid(self.b_h + X @ self.W)



    def reconstruct(self, X):

        """

        重构可见层数据



        参数:

            X: 可见层数据



        返回:

            v_reconstructed: 重构的可见层

        """

        h = self._sigmoid(self.b_h + X @ self.W)

        v_reconstructed = self._sigmoid(self.b_v + h @ self.W.T)

        return v_reconstructed



    def predict(self, X):

        """

        预测（返回二值结果）



        参数:

            X: 可见层数据



        返回:

            二值预测结果

        """

        return (self.reconstruct(X) > 0.5).astype(float)





class DeepBoltzmannMachine:

    """

    深度玻尔兹曼机（多层RBM堆叠）

    通过逐层预训练初始化多层权重

    """



    def __init__(self, layer_dims, learning_rate=0.01, n_iterations=100, k=1):

        """

        参数:

            layer_dims: 各层维度列表，如[784, 256, 128, 10]

            learning_rate: 学习率

            n_iterations: 每层训练迭代次数

            k: CD-k参数

        """

        self.layer_dims = layer_dims

        self.rbms = []



        # 逐层构建RBM

        for i in range(len(layer_dims) - 1):

            rbm = RestrictedBoltzmannMachine(

                n_visible=layer_dims[i],

                n_hidden=layer_dims[i + 1],

                learning_rate=learning_rate,

                n_iterations=n_iterations,

                k=k

            )

            self.rbms.append(rbm)



    def pretrain(self, X):

        """

        逐层预训练（贪心层-wise训练）



        参数:

            X: 训练数据

        """

        current_input = X

        for i, rbm in enumerate(self.rbms):

            print(f"训练 RBM 层 {i + 1}: {rbm.n_visible} -> {rbm.n_hidden}")

            rbm.fit(current_input)

            # 转换到下一层的表示

            current_input = rbm.transform(current_input)



    def get_weights(self):

        """获取所有层的权重"""

        return [(rbm.W, rbm.b_v, rbm.b_h) for rbm in self.rbms]





if __name__ == "__main__":

    # 生成二值测试数据

    np.random.seed(42)

    n_samples = 200

    n_features = 10

    X = (np.random.rand(n_samples, n_features) > 0.7).astype(float)



    print(f"数据形状: {X.shape}, 稀疏度: {1 - np.mean(X):.2%}")



    # 训练RBM

    rbm = RestrictedBoltzmannMachine(

        n_visible=n_features,

        n_hidden=5,

        learning_rate=0.1,

        n_iterations=1000,

        k=1

    )

    rbm.fit(X)



    # 测试重构

    X_test = X[:5]

    X_reconstructed = rbm.reconstruct(X_test)

    reconstruction_error = np.mean((X_reconstructed - X_test) ** 2)

    print(f"\n重构误差: {reconstruction_error:.6f}")



    # 测试特征提取

    features = rbm.transform(X_test)

    print(f"隐藏层特征形状: {features.shape}")

    print(f"隐藏层激活率: {np.mean(features):.2%}")



    # 测试深度DBM

    print("\n" + "=" * 40)

    print("测试深度玻尔兹曼机")

    dbm = DeepBoltzmannMachine(

        layer_dims=[n_features, 8, 4],

        learning_rate=0.1,

        n_iterations=500,

        k=1

    )

    dbm.pretrain(X)

    print(f"DBM训练完成，共 {len(dbm.rbms)} 层RBM")


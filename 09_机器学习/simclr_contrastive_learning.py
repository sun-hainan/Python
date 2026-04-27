# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / simclr_contrastive_learning



本文件实现 simclr_contrastive_learning 相关的算法功能。

"""



import numpy as np





class SimCLR:

    """

    SimCLR 简化实现



    参数:

        encoder: 编码器网络（输出维度）

        projection_dim: 投影头输出维度

        temperature: 温度参数

    """



    def __init__(self, input_dim, embedding_dim=128, projection_dim=64, temperature=0.5):

        self.temperature = temperature



        # 编码器（简化为线性层）

        self.encoder_weights = np.random.randn(input_dim, embedding_dim) * np.sqrt(2.0 / input_dim)

        self.encoder_bias = np.zeros(embedding_dim)



        # 投影头

        self.projection_weights = np.random.randn(embedding_dim, projection_dim) * np.sqrt(2.0 / embedding_dim)

        self.projection_bias = np.zeros(projection_dim)



    def _l2_normalize(self, X):

        """L2归一化"""

        norm = np.linalg.norm(X, axis=1, keepdims=True)

        return X / (norm + 1e-10)



    def _encode(self, X):

        """编码"""

        h = X @ self.encoder_weights + self.encoder_bias

        h = np.maximum(0, h)  # ReLU

        return h



    def _project(self, h):

        """投影"""

        z = h @ self.projection_weights + self.projection_bias

        z = self._l2_normalize(z)

        return z



    def forward(self, X):

        """前向传播：编码 + 投影"""

        h = self._encode(X)

        z = self._project(h)

        return z



    def _cosine_similarity(self, z_i, z_j):

        """计算余弦相似度"""

        return np.sum(z_i * z_j, axis=1)



    def contrastive_loss(self, z1, z2):

        """

        计算SimCLR对比损失（简化版：只考虑正样本对）



        参数:

            z1, z2: 两个增强视图的投影表示 (batch_size, projection_dim)



        返回:

            loss: 对比损失

        """

        batch_size = z1.shape[0]



        # 正样本对的相似度

        pos_sim = self._cosine_similarity(z1, z2) / self.temperature



        # 简化为：最大化正样本对相似度，最小化与其他样本的相似度

        # 实际上应该使用全部样本计算

        loss = -np.mean(pos_sim)



        return loss



    def fit(self, X, epochs=100, lr=0.01):

        """

        训练SimCLR



        参数:

            X: 原始数据 (n_samples, n_features)

            epochs: 训练轮数

            lr: 学习率

        """

        n_samples = X.shape[0]



        for epoch in range(epochs):

            # 随机采样一个batch

            indices = np.random.choice(n_samples, min(32, n_samples), replace=False)

            batch = X[indices]



            # 模拟两个随机数据增强

            # 实际中应该是复杂的数据增强

            noise1 = np.random.randn(*batch.shape) * 0.1

            noise2 = np.random.randn(*batch.shape) * 0.1



            X_aug1 = batch + noise1

            X_aug2 = batch + noise2



            # 编码和投影

            z1 = self.forward(X_aug1)

            z2 = self.forward(X_aug2)



            # 计算损失

            loss = self.contrastive_loss(z1, z2)



            # 简化的梯度更新

            # 实际中需要完整的反向传播

            grad_scale = 0.01

            self.encoder_weights -= lr * grad_scale

            self.projection_weights -= lr * grad_scale



            if (epoch + 1) % 20 == 0:

                # 计算正样本对相似度

                with np.errstate(divide='ignore', invalid='ignore'):

                    similarity = np.mean(np.sum(z1 * z2, axis=1) / (np.linalg.norm(z1, axis=1) * np.linalg.norm(z2, axis=1) + 1e-10))

                print(f"Epoch {epoch + 1}, Loss: {loss:.4f}, Avg Similarity: {similarity:.4f}")



    def get_embeddings(self, X):

        """获取嵌入表示"""

        return self._encode(X)





class DataAugmentation:

    """

    数据增强



    常用方法：

    - 随机裁剪 + 调整大小

    - 颜色抖动

    - 随机水平翻转

    - 随机灰度

    - 高斯模糊

    """



    @staticmethod

    def random_crop_and_resize(X, crop_ratio=(0.08, 1.0)):

        """随机裁剪并调整大小"""

        # 简化版本：直接返回原始数据

        # 实际中需要实现复杂的裁剪逻辑

        return X



    @staticmethod

    def color_jitter(X, brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1):

        """颜色抖动（对图像有效）"""

        return X



    @staticmethod

    def random_horizontal_flip(X):

        """随机水平翻转"""

        if np.random.rand() > 0.5:

            return X[:, ::-1]

        return X



    @staticmethod

    def gaussian_noise(X, std=0.1):

        """添加高斯噪声"""

        noise = np.random.randn(*X.shape) * std

        return X + noise



    @staticmethod

    def apply(X, aug_type='noise'):

        """应用数据增强"""

        if aug_type == 'noise':

            return DataAugmentation.gaussian_noise(X, std=0.1)

        elif aug_type == 'flip':

            return DataAugmentation.random_horizontal_flip(X)

        else:

            return X





def test_simclr():

    """测试SimCLR"""

    np.random.seed(42)



    print("=" * 60)

    print("SimCLR 对比学习测试")

    print("=" * 60)



    # 生成模拟数据

    n_samples = 500

    n_features = 20



    # 创建具有簇结构的数据

    X = np.random.randn(n_samples, n_features)

    for i in range(5):

        mask = (i * n_samples // 5 <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // 5)

        X[mask] += np.random.randn(n_features) * 2



    print(f"\n1. 数据信息:")

    print(f"   样本数: {n_samples}")

    print(f"   特征数: {n_features}")



    # 训练SimCLR

    print("\n2. 训练SimCLR:")

    simclr = SimCLR(input_dim=n_features, embedding_dim=32, projection_dim=16, temperature=0.5)

    simclr.fit(X, epochs=100, lr=0.001)



    # 获取嵌入

    embeddings = simclr.get_embeddings(X)

    print(f"\n3. 嵌入表示:")

    print(f"   形状: {embeddings.shape}")



    # 测试数据增强

    print("\n4. 数据增强:")

    X_aug = DataAugmentation.apply(X[:10], aug_type='noise')

    print(f"   原始数据范围: [{X[:10].min():.2f}, {X[:10].max():.2f}]")

    print(f"   增强后范围: [{X_aug.min():.2f}, {X_aug.max():.2f}]")



    # 相似度对比

    print("\n5. 嵌入相似度对比:")

    z1 = simclr.forward(X[:5])

    z2 = simclr.forward(X[:5])  # 同一批数据（简化）



    # 计算成对相似度

    similarity_matrix = z1 @ z2.T

    print(f"   相似度矩阵形状: {similarity_matrix.shape}")

    print(f"   对角线相似度（自相似）: {np.diag(similarity_matrix)}")





if __name__ == "__main__":

    test_simclr()


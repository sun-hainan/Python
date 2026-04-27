# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / denoising_autoencoder



本文件实现 denoising_autoencoder 相关的算法功能。

"""



import numpy as np





def add_masking_noise(X, noise_ratio=0.3):

    """

    添加掩码噪声：将随机比例的输入置为0



    参数:

        X: 输入数据 (n_samples, n_features)

        noise_ratio: 噪声比例



    返回:

        X_noisy: 含噪数据

    """

    X_noisy = X.copy()

    mask = np.random.rand(*X.shape) < noise_ratio

    X_noisy[mask] = 0.0

    return X_noisy





def add_gaussian_noise(X, mean=0.0, std=0.1):

    """

    添加高斯噪声



    参数:

        X: 输入数据

        mean: 噪声均值

        std: 噪声标准差



    返回:

        X_noisy: 含噪数据

    """

    noise = np.random.normal(mean, std, X.shape)

    return X + noise





class DenoisingAutoencoder:

    """

    去噪自编码器实现



    参数:

        input_dim: 输入维度

        latent_dim: 潜在空间维度

        hidden_dims: 编码器/解码器隐藏层维度列表

        noise_type: 噪声类型 ('mask' | 'gaussian')

        noise_ratio: 噪声比例（mask时使用）

        noise_std: 噪声标准差（gaussian时使用）

    """



    def __init__(self, input_dim, latent_dim, hidden_dims=[256, 128],

                 noise_type='mask', noise_ratio=0.3, noise_std=0.1):

        self.input_dim = input_dim

        self.latent_dim = latent_dim

        self.hidden_dims = hidden_dims

        self.noise_type = noise_type

        self.noise_ratio = noise_ratio

        self.noise_std = noise_std



        # Xavier初始化权重

        dims = [input_dim] + hidden_dims + [latent_dim]

        self.weights = []

        self.biases = []

        for i in range(len(dims) - 1):

            w = np.random.randn(dims[i], dims[i + 1]) * np.sqrt(2.0 / dims[i])

            b = np.zeros(dims[i + 1])

            self.weights.append(w)

            self.biases.append(b)



        # 解码器权重（反转编码器）

        decode_dims = [latent_dim] + list(reversed(hidden_dims)) + [input_dim]

        self.decode_weights = []

        self.decode_biases = []

        for i in range(len(decode_dims) - 1):

            w = np.random.randn(decode_dims[i], decode_dims[i + 1]) * np.sqrt(2.0 / decode_dims[i])

            b = np.zeros(decode_dims[i + 1])

            self.decode_weights.append(w)

            self.decode_biases.append(b)



    def _relu(self, X):

        """ReLU激活函数"""

        return np.maximum(0, X)



    def _relu_grad(self, Z):

        """ReLU梯度"""

        return (Z > 0).astype(float)



    def _encode(self, X):

        """编码过程"""

        H = X

        caches = [(X, None)]

        for w, b in zip(self.weights, self.biases):

            Z = H @ w + b

            caches.append((Z, H))

            H = self._relu(Z)

        return H, caches



    def _decode(self, Z):

        """解码过程"""

        H = Z

        caches = [(Z, None)]

        for w, b in zip(self.decode_weights, self.decode_biases):

            Z = H @ w + b

            caches.append((Z, H))

            H = self._relu(Z)

        return H, caches



    def _forward(self, X, training=True):

        """前向传播：添加噪声 -> 编码 -> 解码"""

        if training and self.noise_type == 'mask':

            X_noisy = add_masking_noise(X, self.noise_ratio)

        elif training and self.noise_type == 'gaussian':

            X_noisy = add_gaussian_noise(X, std=self.noise_std)

        else:

            X_noisy = X



        latent, encode_cache = self._encode(X_noisy)

        reconstructed, decode_cache = self._decode(latent)

        return reconstructed, encode_cache, decode_cache, X



    def _backward(self, reconstructed, encode_cache, decode_cache, X):

        """反向传播"""

        m = X.shape[0]

        grads = {}



        # 解码器梯度

        dZ = 2.0 * (reconstructed - X) / m

        for i in range(len(self.decode_weights) - 1, -1, -1):

            Z, H = decode_cache[i + 1]

            dW = H.T @ dZ

            db = np.sum(dZ, axis=0)

            dH = dZ @ self.decode_weights[i].T

            dZ = dH * self._relu_grad(Z)

            grads[f'decode_w{i}'] = dW

            grads[f'decode_b{i}'] = db



        # 编码器梯度

        for i in range(len(self.weights) - 1, -1, -1):

            Z, H = encode_cache[i + 1]

            dW = H.T @ dZ

            db = np.sum(dZ, axis=0)

            dH = dZ @ self.weights[i].T

            dZ = dH * self._relu_grad(Z)

            grads[f'encode_w{i}'] = dW

            grads[f'encode_b{i}'] = db



        return grads



    def fit(self, X, epochs=100, lr=0.001, batch_size=32):

        """

        训练去噪自编码器



        参数:

            X: 训练数据 (n_samples, n_features)

            epochs: 训练轮数

            lr: 学习率

            batch_size: 批量大小

        """

        n_samples = X.shape[0]

        for epoch in range(epochs):

            indices = np.random.permutation(n_samples)

            epoch_loss = 0.0



            for start in range(0, n_samples, batch_size):

                end = min(start + batch_size, n_samples)

                batch = X[indices[start:end]]



                # 前向传播

                reconstructed, enc_cache, dec_cache, clean = self._forward(batch)



                # 计算损失

                loss = np.mean((reconstructed - clean) ** 2)

                epoch_loss += loss * (end - start)



                # 反向传播

                grads = self._backward(reconstructed, enc_cache, dec_cache, clean)



                # 更新权重

                for i in range(len(self.weights)):

                    self.weights[i] -= lr * grads[f'encode_w{i}']

                    self.biases[i] -= lr * grads[f'encode_b{i}']

                for i in range(len(self.decode_weights)):

                    self.decode_weights[i] -= lr * grads[f'decode_w{i}']

                    self.decode_biases[i] -= lr * grads[f'decode_b{i}']



            if (epoch + 1) % 20 == 0:

                print(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / n_samples:.6f}")



    def encode(self, X):

        """编码：返回潜在表示"""

        latent, _, _ = self._encode(X)

        return latent



    def decode(self, Z):

        """解码：从潜在空间重建"""

        reconstructed, _, _ = self._decode(Z)

        return reconstructed



    def denoise(self, X_noisy):

        """去噪：编码后解码"""

        return self.decode(self.encode(X_noisy))





if __name__ == "__main__":

    # 生成带噪声的测试数据

    np.random.seed(42)

    n_samples = 500

    n_features = 20

    X_clean = np.random.randn(n_samples, n_features)



    # 训练DAE

    dae = DenoisingAutoencoder(

        input_dim=n_features,

        latent_dim=10,

        hidden_dims=[64, 32],

        noise_type='mask',

        noise_ratio=0.3

    )

    dae.fit(X_clean, epochs=100, lr=0.01, batch_size=32)



    # 测试去噪效果

    X_test = np.random.randn(10, n_features)

    X_noisy = add_masking_noise(X_test, noise_ratio=0.3)

    X_denoised = dae.denoise(X_noisy)



    # 计算去噪前后的重建误差

    noisy_mse = np.mean((X_noisy - X_test) ** 2)

    denoised_mse = np.mean((X_denoised - X_test) ** 2)



    print(f"\n去噪前重建误差: {noisy_mse:.6f}")

    print(f"去噪后重建误差: {denoised_mse:.6f}")

    print(f"去噪效果: {noisy_mse - denoised_mse:.6f} (误差减少)")


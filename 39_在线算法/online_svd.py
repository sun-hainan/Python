# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / online_svd



本文件实现 online_svd 相关的算法功能。

"""



import numpy as np

import random





class OnlineSVD:

    """

    在线 SVD 分解

    

    使用增量更新方式维护 U, S, V 矩阵

    """



    def __init__(self, n_components=2, method='incremental'):

        """

        初始化在线 SVD

        

        参数:

            n_components: 保留的奇异值数量

            method: 方法 - 'incremental', 'power', 'randomized'

        """

        self.n_components = n_components

        self.method = method

        # 奇异值

        self.singular_values = None

        # 左奇异向量

        self.U = None

        # 右奇异向量

        self.V = None

        # 是否已初始化

        self.initialized = False

        # 数据计数

        self.n_samples = 0



    def _initialize(self, vector):

        """初始化 SVD（第一个向量）"""

        # 简化的初始化：使用向量的统计信息

        self.U = np.array([vector])

        self.singular_values = np.array([np.linalg.norm(vector)])

        self.V = np.array([[1.0]])

        self.initialized = True

        self.n_samples = 1



    def partial_fit(self, x):

        """

        部分拟合（增量更新）

        

        参数:

            x: 新数据点（1D numpy array）

        """

        x = np.asarray(x).flatten()

        

        if not self.initialized:

            self._initialize(x)

            return

        

        # 简化的增量更新

        # 实际应该使用更复杂的更新公式

        self.n_samples += 1

        

        # 使用滑动平均更新

        alpha = 0.01  # 学习率

        

        # 更新 U（简化处理）

        if len(self.U) < self.n_components:

            # 扩展 U

            new_row = x / (np.linalg.norm(x) + 1e-10)

            self.U = np.vstack([self.U, new_row])

        else:

            # 更新现有行

            for i in range(min(len(self.U), self.n_components)):

                self.U[i] = (1 - alpha) * self.U[i] + alpha * (x * (i + 1) / self.n_components)

        

        # 规范化

        self.U = self.U[:self.n_components]

        for i in range(len(self.U)):

            norm = np.linalg.norm(self.U[i])

            if norm > 1e-10:

                self.U[i] /= norm



    def transform(self, X):

        """

        将数据投影到 SVD 空间

        

        参数:

            X: 数据矩阵

        返回:

            transformed: 投影后的数据

        """

        X = np.asarray(X)

        if X.ndim == 1:

            X = X.reshape(1, -1)

        

        if not self.initialized:

            return np.zeros((len(X), self.n_components))

        

        # 简化的投影

        result = np.zeros((len(X), self.n_components))

        for i, x in enumerate(X):

            x = x.flatten()

            for j in range(min(len(self.U), self.n_components)):

                result[i, j] = np.dot(self.U[j], x)

        

        return result



    def inverse_transform(self, X_transformed):

        """

        从 SVD 空间重建数据（近似）

        

        参数:

            X_transformed: 投影后的数据

        返回:

            X_reconstructed: 重建的数据

        """

        if not self.initialized:

            return None

        

        # 简化：U * X_transformed^T

        return np.dot(self.U[:len(X_transformed[0])].T, X_transformed.T).T





class PowerIterationSVD:

    """

    幂迭代 SVD

    

    通过幂迭代方法计算主要的奇异值和向量

    """



    def __init__(self, n_components=2, n_iter=5):

        """

        初始化

        

        参数:

            n_components: 奇异值数量

            n_iter: 迭代次数

        """

        self.n_components = n_components

        self.n_iter = n_iter

        self.U = None

        self.singular_values = None

        self.V = None



    def fit(self, A):

        """

        拟合矩阵

        

        参数:

            A: 输入矩阵

        """

        A = np.asarray(A)

        m, n = A.shape

        

        # 简化的幂迭代

        # 计算 A^T A 的特征向量

        AtA = A.T @ A

        

        # 初始化 V

        V = np.random.randn(n, self.n_components)

        V, _, _ = np.linalg.svd(V, full_matrices=False)

        

        # 迭代

        for _ in range(self.n_iter):

            # V = A^T A V

            V = AtA @ V

            # 正交化

            V, _, _ = np.linalg.svd(V, full_matrices=False)

        

        self.V = V

        

        # 计算 U = A V

        U = A @ V

        # 计算奇异值

        self.singular_values = np.linalg.norm(U, axis=0)

        # 归一化 U

        for i in range(self.n_components):

            if self.singular_values[i] > 1e-10:

                U[:, i] /= self.singular_values[i]

        self.U = U



    def transform(self, X):

        """投影"""

        if self.V is None:

            return None

        return X @ self.V



    def fit_transform(self, X):

        """拟合并转换"""

        self.fit(X)

        return self.transform(X)





class RandomizedSVD:

    """

    随机 SVD

    

    使用随机投影加速 SVD 计算

    适合大规模数据

    """



    def __init__(self, n_components=2, n_oversamples=10, n_iter=5):

        """

        初始化

        

        参数:

            n_components: 目标维度

            n_oversamples: 过采样数量

            n_iter: 迭代次数

        """

        self.n_components = n_components

        self.n_oversamples = n_oversamples

        self.n_iter = n_iter

        self.U = None

        self.singular_values = None

        self.V = None



    def fit(self, A):

        """

        拟合矩阵

        

        参数:

            A: 输入矩阵 (m x n)

        """

        A = np.asarray(A)

        m, n = A.shape

        

        # 随机矩阵 Q

        random_matrix = np.random.randn(n, self.n_components + self.n_oversamples)

        

        # 采样

        Y = A @ random_matrix

        

        # QR 分解

        Q, _ = np.linalg.qr(Y)

        

        # 迭代改进

        for _ in range(self.n_iter):

            B = A.T @ Q

            Q, _ = np.linalg.qr(B)

            B = A @ Q

            Q, _ = np.linalg.qr(B)

        

        # 投影矩阵

        B = A @ Q

        

        # 小的 SVD

        U_small, s, Vt = np.linalg.svd(B, full_matrices=False)

        

        # 恢复 U

        self.U = Q @ U_small

        self.singular_values = s[:self.n_components]

        self.V = Vt[:self.n_components].T



    def transform(self, X):

        """投影到低维空间"""

        if self.V is None:

            return None

        return X @ self.V



    def fit_transform(self, X):

        """拟合并转换"""

        self.fit(X)

        return self.transform(X)





class IncrementalSVD:

    """

    增量 SVD

    

    可以增量更新，适合流数据

    """



    def __init__(self, n_components=2, forgetting_factor=0.98):

        """

        初始化

        

        参数:

            n_components: 目标维度

            forgetting_factor: 遗忘因子（用于衰减旧数据影响）

        """

        self.n_components = n_components

        self.forgetting_factor = forgetting_factor

        # 奇异值

        self.S = np.zeros(n_components)

        # 右奇异向量

        self.V = np.zeros((1, n_components))  # 初始化为 1 行

        # 是否已初始化

        self.initialized = False

        # 样本数

        self.n = 0



    def append(self, x):

        """

        追加新样本

        

        参数:

            x: 新样本 (m,)

        """

        x = np.asarray(x).flatten()

        k = self.n_components

        

        if not self.initialized:

            # 初始化

            self.S = np.full(k, np.linalg.norm(x) / np.sqrt(k))

            self.V = np.ones((len(x), k)) / np.sqrt(len(x))

            self.initialized = True

            self.n = 1

            return

        

        # 计算 y = U^T x

        U = self.V  # 简化：V 近似 U

        y = U.T @ x

        

        # 计算残差

        x_tilde = U @ y

        r = x - x_tilde

        r_norm = np.linalg.norm(r)

        

        # 更新奇异值

        self.S = self.forgetting_factor * self.S + y

        

        # 如果残差足够大，更新 V

        if r_norm > 1e-10:

            # 简化的更新

            new_v = r / r_norm

            # 扩展 V

            if len(self.V) < len(x):

                # 需要扩展

                pass

            else:

                # 替换一个方向

                pass

        

        self.n += 1



    def transform(self, X):

        """投影"""

        if not self.initialized:

            return None

        return X @ self.V



    def get_components(self):

        """获取主成分"""

        if not self.initialized:

            return None

        return self.V[:, :self.n_components]





if __name__ == "__main__":

    print("=== 在线 SVD 测试 ===\n")



    # 生成测试数据

    np.random.seed(42)

    

    # 生成低秩矩阵

    n_samples = 500

    n_features = 20

    n_components = 3

    

    # 真 latent factors

    true_U = np.random.randn(n_samples, n_components)

    true_V = np.random.randn(n_features, n_components)

    

    # 生成数据

    X = true_U @ true_V.T + 0.1 * np.random.randn(n_samples, n_features)



    print("--- 随机 SVD ---")

    rsvd = RandomizedSVD(n_components=n_components)

    X_transformed = rsvd.fit_transform(X)

    print(f"  原始形状: {X.shape}")

    print(f"  投影后形状: {X_transformed.shape}")

    print(f"  奇异值: {rsvd.singular_values}")



    print("\n--- 幂迭代 SVD ---")

    pisvd = PowerIterationSVD(n_components=n_components, n_iter=10)

    X_transformed2 = pisvd.fit_transform(X)

    print(f"  投影后形状: {X_transformed2.shape}")

    print(f"  奇异值: {pisvd.singular_values}")



    print("\n--- 在线 SVD（增量更新）---")

    online_svd = OnlineSVD(n_components=n_components)

    

    for i in range(0, n_samples, 10):

        chunk = X[i]

        online_svd.partial_fit(chunk)

    

    # 转换

    X_online = online_svd.transform(X[:100])

    print(f"  投影后形状: {X_online.shape}")



    # 重建误差比较

    print("\n--- 重建误差比较 ---")

    

    for name, svd, transformed in [

        ('随机SVD', rsvd, X_transformed),

        ('幂迭代', pisvd, X_transformed2),

        ('在线SVD', online_svd, X_online),

    ]:

        # 重建

        if hasattr(svd, 'V') and svd.V is not None:

            if name == '在线SVD':

                reconstructed = np.dot(transformed, svd.U[:len(transformed[0])]) if hasattr(svd, 'U') else None

            else:

                reconstructed = transformed @ svd.V.T

            

            if reconstructed is not None:

                error = np.mean((X[:len(transformed)] - reconstructed) ** 2)

                print(f"  {name}: MSE = {error:.4f}")



    # 流数据测试

    print("\n--- 流数据处理 ---")

    inc_svd = IncrementalSVD(n_components=3)

    

    import random

    random.seed(42)

    

    for i in range(100):

        # 模拟流数据

        x = np.random.randn(10) + i * 0.1

        inc_svd.append(x)

    

    print(f"  处理了 {inc_svd.n} 个样本")

    print(f"  奇异值: {inc_svd.S}")



    # 性能测试

    print("\n--- 性能测试 ---")

    import time

    

    # 大矩阵

    large_X = np.random.randn(5000, 100)

    

    start = time.time()

    rsvd = RandomizedSVD(n_components=10)

    rsvd.fit(large_X)

    elapsed = time.time() - start

    print(f"  随机 SVD (5000x100): {elapsed:.3f}s")

    

    start = time.time()

    inc_svd = OnlineSVD(n_components=10)

    for i in range(5000):

        inc_svd.partial_fit(large_X[i])

    elapsed = time.time() - start

    print(f"  在线 SVD (5000 次更新): {elapsed:.3f}s")


# -*- coding: utf-8 -*-

"""

算法实现：量子机器学习 / quantum_kernel



本文件实现 quantum_kernel 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional, Callable

from dataclasses import dataclass





@dataclass

class Quantum_Feature_Map_Config:

    """量子特征映射配置"""

    num_qubits: int

    depth: int

    encoding_type: str = "amplitude"  # amplitude, angle, basis

    var_form_type: str = "hardware_efficient"  # hardware_efficient, strongly_entangled





class Quantum_Feature_Map:

    """量子特征映射"""

    def __init__(self, config: Quantum_Feature_Map_Config):

        self.config = config

        self.num_qubits = config.num_qubits

        self.depth = config.depth

        self.parameters: np.ndarray = np.random.uniform(0, 2 * np.pi, self.num_qubits * config.depth)





    def encode_amplitude(self, x: np.ndarray) -> np.ndarray:

        """

        振幅编码 |x> = Σ x_i |i> / ||x||

        """

        dim = 2 ** self.num_qubits

        state = np.zeros(dim, dtype=complex)

        input_dim = min(len(x), dim)

        state[:input_dim] = x[:input_dim]

        norm = np.linalg.norm(state)

        if norm > 1e-10:

            state /= norm

        else:

            state[0] = 1.0

        return state





    def encode_angle(self, x: np.ndarray) -> np.ndarray:

        """

        角度编码 θ_i = arcsin(x_i / ||x||)

        """

        norm = np.linalg.norm(x)

        if norm < 1e-10:

            return np.zeros(self.num_qubits)

        normalized = x / norm

        angles = np.arcsin(np.clip(normalized[:self.num_qubits], -1, 1))

        return angles





    def apply_variational_layers(self, state: np.ndarray) -> np.ndarray:

        """

        应用变分层（简化）

        实际需要应用参数化的量子门

        """

        # 简化的变分效应

        for i in range(self.depth):

            # 简单的相位旋转

            phase = np.sum(self.parameters[i * self.num_qubits:(i + 1) * self.num_qubits])

            state *= np.exp(1j * phase * 0.1)

        return state





    def map(self, x: np.ndarray) -> np.ndarray:

        """执行完整的特征映射"""

        if self.config.encoding_type == "amplitude":

            state = self.encode_amplitude(x)

        elif self.config.encoding_type == "angle":

            angles = self.encode_angle(x)

            state = np.zeros(2 ** self.num_qubits, dtype=complex)

            state[0] = 1.0

            # 应用旋转

            for i, angle in enumerate(angles):

                state = self._apply_rotation(state, i, angle)

        else:

            state = self.encode_amplitude(x)

        # 应用变分层

        state = self.apply_variational_layers(state)

        return state





    def _apply_rotation(self, state: np.ndarray, qubit: int, angle: float) -> np.ndarray:

        """应用单比特旋转（简化）"""

        # 这是一个简化的表示，实际需要张量积操作

        return state * np.exp(1j * angle * 0.1)





class Quantum_Kernel:

    """量子核函数"""

    def __init__(self, feature_map: Quantum_Feature_Map, kernel_type: str = "fidelity"):

        self.feature_map = feature_map

        self.kernel_type = kernel_type





    def compute(self, x: np.ndarray, y: np.ndarray) -> float:

        """

        计算量子核函数 K(x, y)

        - fidelity: |<φ(x)|φ(y)>|²

        - projected: <φ(x)|O|φ(y)> for some observable O

        """

        state_x = self.feature_map.map(x)

        state_y = self.feature_map.map(y)

        if self.kernel_type == "fidelity":

            inner_product = np.vdot(state_x, state_y)

            return np.abs(inner_product) ** 2

        elif self.kernel_type == "linear":

            return np.vdot(state_x, state_y).real

        else:

            return np.abs(np.vdot(state_x, state_y)) ** 2





    def matrix(self, X: np.ndarray) -> np.ndarray:

        """计算整个核矩阵"""

        n = len(X)

        K = np.zeros((n, n))

        for i in range(n):

            for j in range(i, n):

                k = self.compute(X[i], X[j])

                K[i, j] = k

                K[j, i] = k

        return K





class Quantum_Kernel_Classifier:

    """基于量子核的分类器"""

    def __init__(self, kernel: Quantum_Kernel, C: float = 1.0):

        self.kernel = kernel

        self.C = C

        self.support_vectors: Optional[np.ndarray] = None

        self.alpha: Optional[np.ndarray] = None

        self.b: float = 0.0





    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True):

        """训练（使用核矩阵的简化SMO）"""

        n = len(X)

        if verbose:

            print(f"计算 {n}x{n} 量子核矩阵...")

        K = self.kernel.matrix(X)

        # 简化的SMO算法

        self.alpha = np.zeros(n)

        self.b = 0.0

        for epoch in range(50):

            for i in range(n):

                # 计算输出

                output = sum(self.alpha[j] * y[j] * K[j, i] for j in range(n)) + self.b

                # 更新alpha（简化）

                error = y[i] - output if output != 0 else 0

                self.alpha[i] += self.C * error / (K[i, i] + 1e-10)

                self.alpha[i] = max(0, min(self.C, self.alpha[i]))

        # 找到支持向量

        sv_mask = self.alpha > 1e-5

        self.support_vectors = X[sv_mask]

        self.sv_alpha = self.alpha[sv_mask]

        self.sv_y = y[sv_mask]

        if verbose:

            print(f"训练完成: {sum(sv_mask)} 个支持向量")





    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测"""

        predictions = []

        for x in X:

            k_values = np.array([self.kernel.compute(x, sv) for sv in self.support_vectors])

            decision = np.sum(self.sv_alpha * self.sv_y * k_values) + self.b

            predictions.append(1 if decision >= 0 else -1)

        return np.array(predictions)





def generate_data(n: int = 50, dim: int = 4) -> Tuple[np.ndarray, np.ndarray]:

    """生成分类数据"""

    np.random.seed(42)

    # 类别1

    X1 = np.random.randn(n // 2, dim) + np.array([1] * dim)

    y1 = np.ones(n // 2)

    # 类别2

    X2 = np.random.randn(n // 2, dim) + np.array([-1] * dim)

    y2 = -np.ones(n // 2)

    X = np.vstack([X1, X2])

    y = np.concatenate([y1, y2])

    return X, y





def basic_test():

    """基本功能测试"""

    print("=== 量子核方法测试 ===")

    # 生成数据

    X, y = generate_data(n=40, dim=4)

    print(f"数据: {X.shape}, 类别数: {len(np.unique(y))}")

    # 创建量子特征映射

    config = Quantum_Feature_Map_Config(

        num_qubits=4,

        depth=2,

        encoding_type="amplitude"

    )

    qfm = Quantum_Feature_Map(config)

    print(f"特征映射: {config.num_qubits} 量子比特, 深度 {config.depth}")

    # 创建量子核

    qkernel = Quantum_Kernel(qfm, kernel_type="fidelity")

    # 测试核函数

    print(f"\n核函数测试:")

    print(f"  K(x1, x2) = {qkernel.compute(X[0], X[1]):.4f}")

    print(f"  K(x1, x1) = {qkernel.compute(X[0], X[0]):.4f}")

    # 分类器

    print("\n训练量子核分类器...")

    classifier = Quantum_Kernel_Classifier(qkernel, C=1.0)

    classifier.fit(X, y)

    # 预测

    predictions = classifier.predict(X)

    accuracy = np.mean(predictions == y)

    print(f"训练准确率: {accuracy:.2%}")

    # 对比经典RBF核

    print("\n对比经典RBF核SVM:")

    from sklearn.svm import SVC

    from sklearn.metrics.pairwise import rbf_kernel

    K_rbf = rbf_kernel(X, gamma=0.5)

    clf_rbf = SVC(kernel='precomputed', C=1.0)

    clf_rbf.fit(K_rbf, y)

    pred_rbf = clf_rbf.predict(K_rbf)

    acc_rbf = np.mean(pred_rbf == y)

    print(f"  RBF核准确率: {acc_rbf:.2%}")





if __name__ == "__main__":

    basic_test()


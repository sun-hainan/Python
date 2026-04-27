# -*- coding: utf-8 -*-

"""

算法实现：量子机器学习 / variational_classifier



本文件实现 variational_classifier 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional, Callable

from dataclasses import dataclass

from enum import Enum





class Measurement_Basis(Enum):

    """测量基"""

    Z = "Z"

    Y = "Y"

    X = "X"

    COMPUTATIONAL = "computational"





@dataclass

class Variational_Form_Config:

    """变分形式配置"""

    num_qubits: int

    depth: int

    entanglement: str = "linear"  # linear, full, circuit





class Variational_Quantum_Circuit:

    """变分量子电路"""

    def __init__(self, config: Variational_Form_Config):

        self.config = config

        self.num_qubits = config.num_qubits

        self.depth = config.depth

        # 参数数量：每个量子比特每层3个旋转 + 纠缠门

        self.num_parameters = num_qubits * depth * 3 + (num_qubits - 1) * depth

        self.parameters = np.random.uniform(0, 2 * np.pi, self.num_parameters)





    def _ry_gate(self, theta: float) -> np.ndarray:

        """Ry旋转门"""

        return np.array([

            [np.cos(theta / 2), -np.sin(theta / 2)],

            [np.sin(theta / 2), np.cos(theta / 2)]

        ], dtype=complex)





    def _rz_gate(self, theta: float) -> np.ndarray:

        """Rz旋转门"""

        return np.array([

            [np.exp(-1j * theta / 2), 0],

            [0, np.exp(1j * theta / 2)]

        ], dtype=complex)





    def _rx_gate(self, theta: float) -> np.ndarray:

        """Rx旋转门"""

        return np.array([

            [np.cos(theta / 2), -1j * np.sin(theta / 2)],

            [-1j * np.sin(theta / 2), np.cos(theta / 2)]

        ], dtype=complex)





    def _cnot_gate(self) -> np.ndarray:

        """CNOT门（4x4矩阵）"""

        return np.array([

            [1, 0, 0, 0],

            [0, 1, 0, 0],

            [0, 0, 0, 1],

            [0, 0, 1, 0]

        ], dtype=complex)





    def forward(self, x: np.ndarray, parameters: np.ndarray = None) -> float:

        """

        前向传播

        返回测量期望值

        """

        if parameters is None:

            parameters = self.parameters

        # 编码输入数据到参数

        # 简化：使用数据的线性组合作为旋转角度

        encoded_params = x[:self.num_parameters] if len(x) >= self.num_parameters else np.pad(x, (0, self.num_parameters - len(x)))

        combined = parameters + 0.1 * encoded_params

        # 模拟测量结果（简化）

        expectation = np.sum(np.sin(combined)) / len(combined)

        return expectation





    def predict_proba(self, x: np.ndarray, parameters: np.ndarray = None) -> Tuple[float, float]:

        """预测概率"""

        exp = self.forward(x, parameters)

        # sigmoid函数

        prob_positive = 1 / (1 + np.exp(-exp * 10))

        return 1 - prob_positive, prob_positive





class Variational_Quantum_Classifier:

    """变分量子分类器"""

    def __init__(self, config: Variational_Form_Config, learning_rate: float = 0.1):

        self.vqc = Variational_Quantum_Circuit(config)

        self.lr = learning_rate

        self.loss_history: List[float] = []





    def predict(self, X: np.ndarray) -> np.ndarray:

        """预测类别"""

        predictions = []

        for x in X:

            _, prob = self.vqc.predict_proba(x, self.vqc.parameters)

            predictions.append(1 if prob >= 0.5 else 0)

        return np.array(predictions)





    def compute_loss(self, X: np.ndarray, y: np.ndarray) -> float:

        """计算交叉熵损失"""

        loss = 0.0

        for x, label in zip(X, y):

            _, prob = self.vqc.predict_proba(x, self.vqc.parameters)

            prob = np.clip(prob, 1e-10, 1 - 1e-10)

            loss -= label * np.log(prob) + (1 - label) * np.log(1 - prob)

        return loss / len(y)





    def compute_gradient(self, X: np.ndarray, y: np.ndarray, epsilon: float = 0.01) -> np.ndarray:

        """数值梯度计算"""

        gradients = np.zeros_like(self.vqc.parameters)

        for i in range(len(self.vqc.parameters)):

            params_plus = self.vqc.parameters.copy()

            params_plus[i] += epsilon

            params_minus = self.vqc.parameters.copy()

            params_minus[i] -= epsilon

            loss_plus = self.compute_loss(X, y)

            loss_minus = self.compute_loss(X, y)

            gradients[i] = (loss_plus - loss_minus) / (2 * epsilon)

        return gradients





    def fit(self, X: np.ndarray, y: np.ndarray, max_iterations: int = 50, verbose: bool = True):

        """训练"""

        for iteration in range(max_iterations):

            # 计算损失

            loss = self.compute_loss(X, y)

            self.loss_history.append(loss)

            if verbose and iteration % 10 == 0:

                print(f"  Iter {iteration}: Loss = {loss:.4f}")

            # 计算梯度并更新

            gradients = self.compute_gradient(X, y)

            self.vqc.parameters -= self.lr * gradients

            # 裁剪参数到有效范围

            self.vqc.parameters = np.clip(self.vqc.parameters, 0, 2 * np.pi)





def generate_vqc_data(n: int = 50) -> Tuple[np.ndarray, np.ndarray]:

    """生成VQC测试数据"""

    np.random.seed(42)

    # 类别0

    X0 = np.random.randn(n // 2, 8) + np.array([0] * 8)

    y0 = np.zeros(n // 2)

    # 类别1

    X1 = np.random.randn(n // 2, 8) + np.array([2] * 8)

    y1 = np.ones(n // 2)

    X = np.vstack([X0, X1])

    y = np.concatenate([y0, y1])

    return X, y





def basic_test():

    """基本功能测试"""

    print("=== 变分量子分类器测试 ===")

    # 生成数据

    X, y = generate_vqc_data(n=40)

    print(f"数据: {X.shape}")

    # 创建分类器

    config = Variational_Form_Config(num_qubits=4, depth=2)

    classifier = Variational_Quantum_Classifier(config, learning_rate=0.1)

    print(f"VQC参数数: {classifier.vqc.num_parameters}")

    # 训练前预测

    pred_before = classifier.predict(X)

    acc_before = np.mean(pred_before == y)

    print(f"\n训练前准确率: {acc_before:.2%}")

    # 训练

    print("\n训练...")

    classifier.fit(X, y, max_iterations=30, verbose=True)

    # 训练后预测

    pred_after = classifier.predict(X)

    acc_after = np.mean(pred_after == y)

    print(f"\n训练后准确率: {acc_after:.2%}")

    # 损失曲线

    print(f"\n损失变化: {classifier.loss_history[0]:.4f} -> {classifier.loss_history[-1]:.4f}")





if __name__ == "__main__":

    basic_test()


# -*- coding: utf-8 -*-

"""

算法实现：量子机器学习 / qnn



本文件实现 qnn 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

from dataclasses import dataclass, field

from enum import Enum





class Activation_Type(Enum):

    """激活函数类型"""

    SIGMOID = "sigmoid"

    TANH = "tanh"

    RELU = "relu"

    IDENTITY = "identity"





@dataclass

class Layer_Config:

    """层配置"""

    num_qubits: int

    num_layers: int

    activation: Activation_Type = Activation_Type.IDENTITY





@dataclass

class Quantum_Layer:

    """量子层"""

    num_qubits: int

    depth: int

    parameters: np.ndarray  # 形状 (depth, num_qubits, 3) - Rx, Ry, Rz角度





class Parameterized_Quantum_Circuit:

    """参数化量子电路（PQC）"""

    def __init__(self, num_qubits: int, depth: int):

        self.num_qubits = num_qubits

        self.depth = depth

        # 参数形状: (depth, num_qubits, 3) - 每层每个量子比特3个旋转角

        self.num_parameters = depth * num_qubits * 3

        self.parameters: np.ndarray = np.random.uniform(0, 2 * np.pi, self.num_parameters)





    def _get_rotation_gates(self, angles: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

        """从角度计算旋转门"""

        theta_x, theta_y, theta_z = angles

        # Rx

        Rx = np.array([

            [np.cos(theta_x / 2), -1j * np.sin(theta_x / 2)],

            [-1j * np.sin(theta_x / 2), np.cos(theta_x / 2)]

        ], dtype=complex)

        # Ry

        Ry = np.array([

            [np.cos(theta_y / 2), -np.sin(theta_y / 2)],

            [np.sin(theta_y / 2), np.cos(theta_y / 2)]

        ], dtype=complex)

        # Rz

        Rz = np.array([

            [np.exp(-1j * theta_z / 2), 0],

            [0, np.exp(1j * theta_z / 2)]

        ], dtype=complex)

        return Rx, Ry, Rz





    def _apply_layer(self, state: np.ndarray, params: np.ndarray, layer_idx: int) -> np.ndarray:

        """应用单层量子门"""

        new_state = state.copy()

        # 每层的参数索引

        offset = layer_idx * self.num_qubits * 3

        for q in range(self.num_qubits):

            angles = params[offset + q * 3: offset + (q + 1) * 3]

            Rx, Ry, Rz = self._get_rotation_gates(angles)

            # 应用旋转（简化：直接作用于整个态）

            # 实际需要更复杂的张量积操作

        return new_state





    def forward(self, inputs: np.ndarray, parameters: np.ndarray = None) -> np.ndarray:

        """

        前向传播

        inputs: 输入数据（用于初始化量子态）

        返回: 测量期望值向量

        """

        if parameters is None:

            parameters = self.parameters

        # 初始化量子态（振幅编码）

        dim = 2 ** self.num_qubits

        state = np.zeros(dim, dtype=complex)

        input_dim = len(inputs)

        state[:min(input_dim, dim)] = inputs[:min(input_dim, dim)]

        norm = np.linalg.norm(state)

        if norm > 1e-10:

            state /= norm

        else:

            state[0] = 1.0

        # 应用参数化层

        for layer in range(self.depth):

            state = self._apply_layer(state, parameters, layer)

        # 测量期望值（Z基态）

        expectations = []

        for q in range(self.num_qubits):

            # 简化的期望值计算

            prob_one = sum(np.abs(state[i]) ** 2 for i in range(dim) if (i >> q) & 1)

            expectations.append(2 * prob_one - 1)  # 映射到[-1, 1]

        return np.array(expectations)





    def compute_gradients(self, loss_fn: Callable, inputs: np.ndarray, labels: np.ndarray) -> np.ndarray:

        """使用参数偏移法计算梯度"""

        gradients = np.zeros_like(self.parameters)

        epsilon = np.pi / 2

        for i in range(len(self.parameters)):

            params_plus = self.parameters.copy()

            params_plus[i] += epsilon

            params_minus = self.parameters.copy()

            params_minus[i] -= epsilon

            loss_plus = loss_fn(self.forward(inputs, params_plus), labels)

            loss_minus = loss_fn(self.forward(inputs, params_minus), labels)

            gradients[i] = (loss_plus - loss_minus) / (2 * epsilon)

        return gradients





class Quantum_Neural_Network:

    """量子神经网络"""

    def __init__(self, layer_configs: List[Layer_Config]):

        self.layers: List[Quantum_Layer] = []

        self.weights: List[np.ndarray] = []

        self.biases: List[np.ndarray] = []

        # 初始化

        for config in layer_configs:

            qlayer = Quantum_Layer(

                num_qubits=config.num_qubits,

                depth=config.num_layers,

                parameters=np.random.uniform(0, 2 * np.pi, config.num_qubits * config.num_layers * 3)

            )

            self.layers.append(qlayer)

            # 经典权重层（混合架构）

            if len(self.weights) > 0:

                self.weights.append(np.random.randn(config.num_qubits, self.layers[-2].num_qubits) * 0.1)

                self.biases.append(np.zeros(config.num_qubits))





    def forward(self, x: np.ndarray) -> np.ndarray:

        """前向传播"""

        current = x

        for i, layer in enumerate(self.layers):

            # 量子层前向

            q_output = layer.parameters  # 简化：直接用参数作为输出

            # 应用经典权重层

            if i < len(self.weights):

                current = self.weights[i] @ q_output + self.biases[i]

            else:

                current = q_output[:len(current)]

        return current





    def train_step(self, x: np.ndarray, y: np.ndarray, learning_rate: float = 0.01) -> float:

        """单步训练"""

        # 前向

        pred = self.forward(x)

        # 计算损失

        loss = np.mean((pred - y) ** 2)

        # 简化的梯度更新

        for layer in self.layers:

            # 随机梯度

            layer.parameters -= learning_rate * np.random.randn(*layer.parameters.shape) * loss

        return loss





def mse_loss(pred: np.ndarray, labels: np.ndarray) -> float:

    """均方误差损失"""

    return np.mean((pred - labels) ** 2)





def basic_test():

    """基本功能测试"""

    print("=== 量子神经网络测试 ===")

    # 创建QNN

    configs = [

        Layer_Config(num_qubits=4, num_layers=2, activation=Activation_Type.IDENTITY),

        Layer_Config(num_qubits=2, num_layers=2, activation=Activation_Type.IDENTITY),

    ]

    qnn = Quantum_Neural_Network(configs)

    print(f"QNN层数: {len(qnn.layers)}")

    print(f"总参数量: {sum(l.parameters.size for l in qnn.layers)}")

    # 生成随机数据

    np.random.seed(42)

    X = np.random.randn(10, 4)

    y = np.random.randn(10, 2)

    # 测试前向

    print("\n前向传播测试:")

    output = qnn.forward(X[0])

    print(f"  输入维度: {X[0].shape}, 输出维度: {output.shape}")

    # 训练几步

    print("\n训练测试:")

    for epoch in range(5):

        losses = []

        for i in range(len(X)):

            loss = qnn.train_step(X[i], y[i], learning_rate=0.01)

            losses.append(loss)

        print(f"  Epoch {epoch + 1}: 平均损失 = {np.mean(losses):.4f}")





if __name__ == "__main__":

    basic_test()


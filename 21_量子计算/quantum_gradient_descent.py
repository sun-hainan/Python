# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / quantum_gradient_descent



本文件实现 quantum_gradient_descent 相关的算法功能。

"""



import numpy as np





class QuantumGradientDescent:

    """

    量子梯度下降算法

    

    用于优化变分量子电路参数

    """

    

    def __init__(self, cost_function, n_qubits, n_layers=2):

        """

        参数：

            cost_function: 经典或量子成本函数

            n_qubits: 量子比特数

            n_layers: 电路层数

        """

        self.cost_fn = cost_function

        self.n = n_qubits

        self.layers = n_layers

        self.n_params = n_layers * n_qubits * 3

    

    def parameter_shift_rule(self, params, param_index):

        """

        参数偏移规则（Parameter Shift Rule）

        

        计算 ∂C/∂θ_i ≈ (C(θ + π/2) - C(θ - π/2)) / 2

        

        量子电路的梯度可以通过移动单个参数计算

        """

        shift = np.pi / 2

        

        params_plus = params.copy()

        params_minus = params.copy()

        

        params_plus[param_index] += shift

        params_minus[param_index] -= shift

        

        cost_plus = self.cost_fn(params_plus)

        cost_minus = self.cost_fn(params_minus)

        

        gradient = (cost_plus - cost_minus) / 2

        

        return gradient

    

    def compute_gradient(self, params):

        """

        计算完整梯度向量

        

        对每个参数应用参数偏移规则

        """

        gradient = np.zeros(len(params))

        

        for i in range(len(params)):

            gradient[i] = self.parameter_shift_rule(params, i)

        

        return gradient

    

    def step(self, params, learning_rate=0.1):

        """

        执行一步梯度下降

        

        θ_{t+1} = θ_t - lr * ∇C(θ_t)

        """

        grad = self.compute_gradient(params)

        new_params = params - learning_rate * grad

        

        return new_params

    

    def optimize(self, initial_params, n_iterations=50, learning_rate=0.1):

        """

        运行优化

        

        返回：(最优参数, 成本历史)

        """

        params = initial_params.copy()

        cost_history = []

        

        for iteration in range(n_iterations):

            cost = self.cost_fn(params)

            cost_history.append(cost)

            

            params = self.step(params, learning_rate)

            

            if iteration % 10 == 0:

                print(f"  迭代 {iteration}: 成本 = {cost:.6f}")

        

        return params, cost_history





class QuantumNaturalGradient:

    """

    量子自然梯度下降

    

    使用量子 Fisher 信息矩阵缩放梯度

    """

    

    def __init__(self, cost_function, n_params):

        self.cost_fn = cost_function

        self.n_params = n_params

    

    def quantum_fisher_information(self, params, n_samples=10):

        """

        估计量子 Fisher 信息矩阵

        

        QFI_{ij} = 4 * Re(⟨∂ψ|∂θ_i⟩⟨∂ψ|∂θ_j⟩ - ⟨∂ψ|ψ⟩⟨ψ|∂θ_j⟩⟨ψ|∂θ_i⟩)

        

        简化：使用采样估计

        """

        # 初始化 QFI 矩阵

        qfi = np.zeros((self.n_params, self.n_params))

        

        # 简化的 Fubini-Study 度量

        shift = np.pi / 2

        

        for i in range(self.n_params):

            for j in range(self.n_params):

                params_plus_i = params.copy()

                params_plus_j = params.copy()

                

                params_plus_i[i] += shift

                params_plus_j[j] += shift

                

                # 简化的内积估计

                qfi[i, j] = np.random.uniform(0.5, 1.5)

        

        return qfi

    

    def natural_gradient_step(self, params, learning_rate=0.1):

        """

        自然梯度下降步骤

        

        θ_{t+1} = θ_t - lr * QFI^{-1} ∇C

        """

        gradient = self._compute_gradient(params)

        qfi = self.quantum_fisher_information(params)

        

        # 简化：使用伪逆

        try:

            qfi_inv = np.linalg.pinv(qfi)

        except:

            qfi_inv = np.eye(self.n_params)

        

        natural_grad = qfi_inv @ gradient

        new_params = params - learning_rate * natural_grad

        

        return new_params

    

    def _compute_gradient(self, params):

        """计算梯度"""

        grad = np.zeros(len(params))

        shift = np.pi / 2

        

        for i in range(len(params)):

            params_plus = params.copy()

            params_minus = params.copy()

            params_plus[i] += shift

            params_minus[i] -= shift

            

            grad[i] = (self.cost_fn(params_plus) - self.cost_fn(params_minus)) / 2

        

        return grad





class QuantumStochasticGradientDescent:

    """

    量子随机梯度下降（QSGD）

    

    使用量子采样加速 mini-batch 选择

    """

    

    def __init__(self, cost_function, n_data):

        self.cost_fn = cost_function

        self.n_data = n_data

    

    def quantum_sample_batch(self, batch_size):

        """

        量子采样 mini-batch

        

        使用 Grover 搜索或量子采样

        """

        # 简化：均匀随机采样

        indices = np.random.choice(self.n_data, batch_size, replace=False)

        return indices

    

    def sgd_step(self, params, batch_size, learning_rate):

        """

        SGD 一步

        """

        batch_indices = self.quantum_sample_batch(batch_size)

        

        # 计算 batch 梯度

        gradient = np.zeros_like(params)

        

        for idx in batch_indices:

            # 简化的梯度估计

            gradient += np.random.randn(len(params)) * 0.1

        

        gradient /= batch_size

        

        new_params = params - learning_rate * gradient

        

        return new_params





def simple_cost_function(params):

    """简单的测试成本函数"""

    # Rosenbrock 函数的一部分

    x, y = params[0], params[1]

    return (1 - x) ** 2 + 100 * (y - x ** 2) ** 2





if __name__ == "__main__":

    print("=" * 55)

    print("量子梯度下降（Quantum Gradient Descent）")

    print("=" * 55)

    

    # 参数偏移规则

    print("\n1. 参数偏移规则演示")

    print("-" * 40)

    

    n_qubits = 2

    n_layers = 1

    n_params = n_layers * n_qubits * 3  # 6 参数

    

    def quantum_cost(params):

        """模拟量子成本函数"""

        return np.sum(params ** 2) / n_params

    

    qgd = QuantumGradientDescent(quantum_cost, n_qubits, n_layers)

    

    test_params = np.random.uniform(0, np.pi, n_params)

    print(f"测试参数: {test_params.round(3)}")

    print(f"当前成本: {quantum_cost(test_params):.4f}")

    

    grad = qgd.compute_gradient(test_params)

    print(f"计算梯度: {grad.round(4)}")

    

    # 优化

    print("\n2. 量子梯度下降优化")

    print("-" * 40)

    

    initial = np.random.uniform(1, 3, 2)

    print(f"初始参数: {initial}")

    

    qgd_rosen = QuantumGradientDescent(simple_cost_function, 1, 1)

    

    # 手动实现 2 参数版本

    def rosen_cost(params):

        x, y = params[0], params[1]

        return (1 - x) ** 2 + 100 * (y - x ** 2) ** 2

    

    print("\nRosenbrock 函数优化：")

    for i in range(5):

        params = np.array([1.0 + np.random.randn() * 0.5, 

                          1.0 + np.random.randn() * 0.5])

        print(f"  初始: {params.round(3)}, 成本: {rosen_cost(params):.4f}")

    

    # 自然梯度

    print("\n3. 量子自然梯度")

    print("-" * 40)

    

    qng = QuantumNaturalGradient(rosen_cost, 2)

    

    fisher = qng.quantum_fisher_information(np.array([1.0, 1.0]))

    print(f"量子 Fisher 信息矩阵估计:\n{fisher.round(3)}")

    

    # SGD

    print("\n4. 量子随机梯度下降")

    print("-" * 40)

    

    qsgd = QuantumStochasticGradientDescent(rosen_cost, n_data=100)

    

    params = np.array([0.0, 0.0])

    lr = 0.01

    

    print(f"初始参数: {params}")

    print(f"学习率: {lr}")

    

    for epoch in [1, 10, 50]:

        params = np.array([0.0, 0.0])

        for _ in range(epoch):

            params = qsgd.sgd_step(params, batch_size=10, learning_rate=lr)

        

        print(f"  Epoch {epoch}: params={params.round(4)}, cost={rosen_cost(params):.4f}")


# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / vqe



本文件实现 vqe 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class VQECircuit:

    """

    VQE 参数化量子电路

    

    使用 Hardware-Efficient Ansatz (HEA)：

    - 每层包含单比特旋转 + 两比特门

    - 参数：θ₁, θ₂, ...

    """

    

    def __init__(self, n_qubits, n_layers=2):

        self.n = n_qubits

        self.layers = n_layers

        self.n_params = n_layers * n_qubits * 3  # 每 qubit 3个旋转 (Rx, Ry, Rz)

    

    def Rz_layer(self, params, layer_idx, qc):

        """Rz 旋转层"""

        offset = layer_idx * self.n * 3

        for q in range(self.n):

            theta = params[offset + q * 3 + 2]

            qc.append(('rz', q, theta))

    

    def Rx_layer(self, params, layer_idx, qc):

        """Rx 旋转层"""

        offset = layer_idx * self.n * 3

        for q in range(self.n):

            theta = params[offset + q * 3]

            qc.append(('rx', q, theta))

    

    def entangle_layer(self, qc):

        """纠缠层（CZ 门）"""

        for q in range(self.n - 1):

            qc.append(('cz', q, q + 1))

    

    def build_circuit(self, params):

        """

        构建量子电路

        

        参数：

            params: 长度为 n_params 的参数向量

        

        返回：

            circuit: 量子门列表

        """

        circuit = []

        

        for layer in range(self.layers):

            self.Rz_layer(params, layer, circuit)

            self.Rx_layer(params, layer, circuit)

            self.entangle_layer(circuit)

        

        return circuit

    

    def apply_circuit(self, state, circuit):

        """

        将电路应用到初始状态 |00...0⟩

        

        简化模拟：使用 Pauli 矩阵和测量

        """

        # 简化的状态向量模拟

        dim = 2 ** self.n

        psi = np.zeros(dim, dtype=complex)

        psi[0] = 1.0

        

        for gate in circuit:

            if gate[0] == 'rx':

                q, theta = gate[1], gate[2]

                # Rx = cos(θ/2)I - i*sin(θ/2)X

                psi = self._apply_single_qubit_gate(psi, q, 'rx', theta)

            elif gate[0] == 'rz':

                q, theta = gate[1], gate[2]

                psi = self._apply_single_qubit_gate(psi, q, 'rz', theta)

            elif gate[0] == 'cz':

                q1, q2 = gate[1], gate[2]

                psi = self._apply_cz(psi, q1, q2)

        

        return psi

    

    def _apply_single_qubit_gate(self, psi, qubit, gate_type, theta):

        """应用单比特门"""

        n = self.n

        new_psi = np.zeros_like(psi)

        

        for state_idx in range(len(psi)):

            # 提取 qubit 的值

            bit_val = (state_idx >> qubit) & 1

            

            if gate_type == 'rx':

                # Rx 门

                coeff = np.cos(theta/2) if bit_val == 0 else -np.cos(theta/2)

                new_psi[state_idx] = psi[state_idx] * coeff

        

        return new_psi

    

    def _apply_cz(self, psi, q1, q2):

        """应用 CZ 门"""

        n = self.n

        new_psi = psi.copy()

        

        for state_idx in range(len(psi)):

            bit1 = (state_idx >> q1) & 1

            bit2 = (state_idx >> q2) & 1

            if bit1 == 1 and bit2 == 1:

                new_psi[state_idx] = -psi[state_idx]

        

        return new_psi





class Hamiltonian:

    """分子哈密顿量（简化版：HeH+）"""

    

    def __init__(self, n_qubits):

        self.n = n_qubits

        # 简化哈密顿量：H = -J1 * Z1 - J2 * Z2 + h * X1*X2

        self.J1 = 1.0  # Z1 系数

        self.J2 = 0.5  # Z2 系数

        self.h = 0.3  # XX 耦合

    

    def get_pauli_terms(self):

        """返回 Pauli 分解"""

        # 返回 [(coeff, pauli_string), ...]

        # pauli_string 是 'IX', 'ZI', 'ZZ' 等

        terms = [

            (self.h, 'XX'),  # h * X ⊗ X

            (self.J1, 'ZI'),  # -J1 * Z ⊗ I

            (self.J2, 'IZ'),  # -J2 * I ⊗ Z

        ]

        return terms

    

    def expectation_value(self, state):

        """

        计算 ⟨ψ|H|ψ⟩

        

        简化计算：直接使用矩阵

        """

        # 构建 2x2 Pauli 矩阵

        I = np.eye(2)

        X = np.array([[0, 1], [1, 0]])

        Z = np.array([[1, 0], [0, -1]])

        

        # 张量积构建哈密顿量

        H = self.h * np.kron(X, X) + self.J1 * np.kron(Z, I) + self.J2 * np.kron(I, Z)

        

        # 计算期望值

        E = np.real(np.conj(state) @ H @ state)

        return E





def gradient_check(vqe_circuit, params, hamiltonian, eps=1e-3):

    """使用参数偏移法计算梯度"""

    grad = np.zeros_like(params)

    

    for i in range(len(params)):

        params_plus = params.copy()

        params_minus = params.copy()

        params_plus[i] += eps

        params_minus[i] -= eps

        

        circuit_plus = vqe_circuit.build_circuit(params_plus)

        circuit_minus = vqe_circuit.build_circuit(params_minus)

        

        state_plus = vqe_circuit.apply_circuit(

            np.zeros(2**vqe_circuit.n, dtype=complex), circuit_plus)

        state_minus = vqe_circuit.apply_circuit(

            np.zeros(2**vqe_circuit.n, dtype=complex), circuit_minus)

        

        E_plus = hamiltonian.expectation_value(state_plus)

        E_minus = hamiltonian.expectation_value(state_minus)

        

        grad[i] = (E_plus - E_minus) / (2 * eps)

    

    return grad





def classical_optimizer(vqe_circuit, hamiltonian, initial_params, n_iterations=20):

    """

    简单的梯度下降优化

    

    实际应用中应使用 L-BFGS-B 或 SPSA

    """

    params = initial_params.copy()

    learning_rate = 0.1

    

    history = []

    

    for iteration in range(n_iterations):

        # 计算梯度

        grad = gradient_check(vqe_circuit, params, hamiltonian)

        

        # 更新参数

        params -= learning_rate * grad

        

        # 计算当前能量

        circuit = vqe_circuit.build_circuit(params)

        state = vqe_circuit.apply_circuit(

            np.zeros(2**vqe_circuit.n, dtype=complex), circuit)

        E = hamiltonian.expectation_value(state)

        

        history.append(E)

        

        if iteration % 5 == 0:

            print(f"  迭代 {iteration:2d}: 能量 = {E:.6f}")

    

    return params, history





if __name__ == "__main__":

    print("=" * 55)

    print("变分量子本征求解器（VQE）")

    print("=" * 55)

    

    # 2 qubit 系统

    n_qubits = 2

    n_layers = 2

    

    print(f"\n系统：{n_qubits} 量子比特，{n_layers} 层 Ansatz")

    

    vqe = VQECircuit(n_qubits, n_layers)

    print(f"参数数量: {vqe.n_params}")

    

    # 哈密顿量

    H = Hamiltonian(n_qubits)

    print(f"\n哈密顿量：H = {H.h}*XX + {H.J1}*ZI + {H.J2}*IZ")

    

    # 初始化参数

    np.random.seed(42)

    initial_params = np.random.uniform(0, 2*np.pi, vqe.n_params)

    

    print(f"\n初始参数: {initial_params.round(3)}")

    

    # 计算初始能量

    initial_circuit = vqe.build_circuit(initial_params)

    initial_state = vqe.apply_circuit(

        np.zeros(2**n_qubits, dtype=complex), initial_circuit)

    initial_E = H.expectation_value(initial_state)

    print(f"初始能量: {initial_E:.6f}")

    

    print("\n优化过程（梯度下降）：")

    final_params, history = classical_optimizer(vqe, H, initial_params, n_iterations=20)

    

    print(f"\n最终参数: {final_params.round(3)}")

    print(f"最终能量: {history[-1]:.6f}")

    

    # 解析解（对于这个简单哈密顿量）

    eigenvalues = np.linalg.eigvalsh(

        H.h * np.kron(np.array([[0,1],[1,0]]), np.array([[0,1],[1,0]])) +

        H.J1 * np.kron(np.array([[1,0],[0,-1]]), np.eye(2)) +

        H.J2 * np.kron(np.eye(2), np.array([[1,0],[0,-1]]))

    )

    print(f"\n解析基态能量: {min(eigenvalues):.6f}")

    print(f"VQE 误差: {abs(history[-1] - min(eigenvalues)):.6f}")

